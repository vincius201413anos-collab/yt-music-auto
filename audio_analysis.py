"""
audio_analysis.py — Elite Audio Analysis Engine v2.1 GRAVE REAL + ALIAS KICKS
=====================================================
NOVO v2.0:
- Detecção de snare / caixa (200-8000 Hz)
- Detecção de hi-hat / chimbal (8000 Hz+)
- Seções musicais: intro, buildup, drop, calm, outro
- Intensidade por beat: weak / medium / strong
- Perfil da música: aggressive / medium / chill
- Curva de energia normalizada
- Expressões FFmpeg: zoom, shake, flash com section modulation
- Loop seamless: expressões baseadas em sin/cos cíclicos
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("audio_analysis")

try:
    import numpy as np
    import librosa
    LIBROSA_OK = True
except ImportError:
    LIBROSA_OK = False
    logger.warning("librosa não disponível — análise limitada.")

try:
    from scipy.signal import butter, lfilter
    from scipy.ndimage import uniform_filter1d
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False
    logger.warning("scipy não disponível — filtros de frequência desativados.")

DEBUG_DIR  = Path("debug")
HOP_LENGTH = 512
FRAME_LEN  = 2048


def _clean_audio(y):
    """
    Corrige NaN/inf e normaliza o áudio.
    Isso evita o erro: Audio buffer is not finite everywhere.
    """
    if not LIBROSA_OK:
        return y

    try:
        y = np.asarray(y, dtype=np.float32)
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

        peak = float(np.max(np.abs(y))) if y.size else 0.0
        if peak > 1e-9:
            y = y / peak

        return y
    except Exception:
        return y


# ══════════════════════════════════════════════════════════════════
# FILTROS DE FREQUÊNCIA
# ══════════════════════════════════════════════════════════════════

def _bandpass(y, sr: int, lowcut: float, highcut: float):
    if not SCIPY_OK:
        return y
    nyq  = sr / 2.0
    low  = max(lowcut / nyq, 0.001)
    high = min(highcut / nyq, 0.999)
    if low >= high:
        return y
    try:
        b, a = butter(4, [low, high], btype="band")
        return lfilter(b, a, y)
    except Exception:
        return y


def _highpass(y, sr: int, lowcut: float):
    if not SCIPY_OK:
        return y
    nyq = sr / 2.0
    low = min(lowcut / nyq, 0.99)
    try:
        b, a = butter(4, low, btype="high")
        return lfilter(b, a, y)
    except Exception:
        return y


# ══════════════════════════════════════════════════════════════════
# DETECÇÃO DE INSTRUMENTOS
# ══════════════════════════════════════════════════════════════════

def detect_bass_hits(y, sr: int) -> list:
    """
    Kicks / 808 / sub-bass: 20-220 Hz.
    Versão corrigida:
    - limpa NaN/inf
    - reforça grave
    - detecta kick mais agressivo
    - fallback nos beats se não achar bass suficiente
    """
    if not LIBROSA_OK:
        return []

    try:
        y = _clean_audio(y)

        # Faixa mais larga pra phonk/trap: pega kick + 808
        y_b = _bandpass(y, sr, 20.0, 220.0)
        y_b = _clean_audio(y_b)

        env = librosa.onset.onset_strength(
            y=y_b,
            sr=sr,
            hop_length=HOP_LENGTH,
            aggregate=np.median,
        )

        env = np.nan_to_num(env, nan=0.0, posinf=0.0, neginf=0.0)

        if len(env) == 0 or float(np.max(env)) <= 1e-9:
            bpm, beats = detect_beats(y, sr)
            return [float(t) for t in beats[:90]]

        frames = librosa.onset.onset_detect(
            onset_envelope=env,
            sr=sr,
            hop_length=HOP_LENGTH,
            backtrack=True,
            pre_max=2,
            post_max=2,
            pre_avg=4,
            post_avg=6,
            delta=0.055,
            wait=3,
        )

        times = [float(t) for t in librosa.frames_to_time(frames, sr=sr, hop_length=HOP_LENGTH)]

        # Fallback inteligente: se a música é phonk/trap e achou pouco grave,
        # usa os beats como "bass proxy" pra logo não ficar morto.
        if len(times) < 8:
            bpm, beats = detect_beats(y, sr)
            if beats:
                return [float(t) for t in beats[:110]]

        return times

    except Exception as e:
        logger.warning(f"detect_bass_hits: {e}")
        try:
            bpm, beats = detect_beats(_clean_audio(y), sr)
            return [float(t) for t in beats[:90]]
        except Exception:
            return []


def detect_snare_hits(y, sr: int) -> list:
    """Snare / caixa: 200-8000 Hz — flash rápido na tela."""
    if not LIBROSA_OK:
        return []
    try:
        y = _clean_audio(y)
        y_m = _bandpass(y, sr, 200.0, 8000.0)
        env = librosa.onset.onset_strength(y=y_m, sr=sr, hop_length=HOP_LENGTH)
        frames = librosa.onset.onset_detect(
            onset_envelope=env, sr=sr, hop_length=HOP_LENGTH,
            backtrack=True, pre_max=1, post_max=1,
            pre_avg=2, post_avg=3, delta=0.10, wait=8,
        )
        return [float(t) for t in librosa.frames_to_time(frames, sr=sr, hop_length=HOP_LENGTH)]
    except Exception as e:
        logger.warning(f"detect_snare_hits: {e}")
        return []


def detect_hihat_hits(y, sr: int) -> list:
    """Hi-hat / chimbal: 8000 Hz+ — micro-jitter sutil."""
    if not LIBROSA_OK:
        return []
    try:
        y = _clean_audio(y)
        y_h = _highpass(y, sr, 8000.0)
        env = librosa.onset.onset_strength(y=y_h, sr=sr, hop_length=256)
        frames = librosa.onset.onset_detect(
            onset_envelope=env, sr=sr, hop_length=256,
            backtrack=False, pre_max=1, post_max=1,
            pre_avg=2, post_avg=2, delta=0.15, wait=4,
        )
        return [float(t) for t in librosa.frames_to_time(frames, sr=sr, hop_length=256)]
    except Exception as e:
        logger.warning(f"detect_hihat_hits: {e}")
        return []


def detect_beats(y, sr: int) -> tuple:
    """BPM e timestamps de todos os beats."""
    if not LIBROSA_OK:
        return 120.0, []
    try:
        y = _clean_audio(y)
        tempo, frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP_LENGTH)
        bpm = float(np.ravel(tempo)[0]) if hasattr(tempo, "__len__") else float(tempo)
        times = [float(t) for t in librosa.frames_to_time(frames, sr=sr, hop_length=HOP_LENGTH)]
        return bpm, times
    except Exception as e:
        logger.warning(f"detect_beats: {e}")
        return 120.0, []


def detect_drop(y, sr: int, duration: float) -> Optional[float]:
    """Localiza o drop: pico de energia entre 20%-80% da música."""
    if not LIBROSA_OK:
        return None
    try:
        y = _clean_audio(y)
        rms = librosa.feature.rms(y=y, frame_length=FRAME_LEN, hop_length=HOP_LENGTH)[0]
        smooth = uniform_filter1d(rms.astype(float), size=60) if SCIPY_OK else rms.astype(float)
        total = len(smooth)
        s, e  = int(total * 0.20), int(total * 0.80)
        zone  = smooth[s:e]
        if len(zone) == 0:
            return None
        peak = int(np.argmax(zone)) + s
        # Recua até onde a energia sobe (início do drop real)
        lookback = int(0.5 * sr / HOP_LENGTH)
        for i in range(peak, max(s, peak - lookback), -1):
            if smooth[i] < smooth[peak] * 0.70:
                peak = i
                break
        return float(librosa.frames_to_time(peak, sr=sr, hop_length=HOP_LENGTH))
    except Exception as e:
        logger.warning(f"detect_drop: {e}")
        return None


def detect_sections(y, sr: int, duration: float, drop_time: Optional[float]) -> dict:
    """
    Segmenta a música em: intro, buildup, drop, calm, outro.
    Usado para modular a intensidade dos efeitos por seção.
    """
    intro_end    = min(duration * 0.14, 18.0)
    outro_start  = max(duration * 0.82, duration - 18.0)

    if drop_time is not None:
        buildup_s = intro_end
        buildup_e = max(drop_time - 2.0, intro_end + 2.0)
        drop_s    = drop_time
        drop_e    = min(drop_time + 22.0, outro_start - 2.0)
        calm_s    = drop_e
        calm_e    = outro_start
    else:
        mid       = duration / 2.0
        buildup_s = intro_end
        buildup_e = mid * 0.80
        drop_s    = mid
        drop_e    = min(mid + duration * 0.22, outro_start - 2.0)
        calm_s    = drop_e
        calm_e    = outro_start

    return {
        "intro_end":     intro_end,
        "buildup_start": buildup_s,
        "buildup_end":   buildup_e,
        "drop_start":    drop_s,
        "drop_end":      drop_e,
        "calm_start":    calm_s,
        "calm_end":      calm_e,
        "outro_start":   outro_start,
    }


def classify_beat_intensities(beats: list, y, sr: int) -> list:
    """Classifica cada beat como 'weak', 'medium' ou 'strong' pela energia RMS local."""
    if not LIBROSA_OK or not beats:
        return ["medium"] * len(beats)
    try:
        y = _clean_audio(y)
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        energies = []
        for t in beats:
            f = min(librosa.time_to_frames(t, sr=sr, hop_length=HOP_LENGTH), len(rms) - 1)
            energies.append(float(rms[f]))
        p33 = float(np.percentile(energies, 33))
        p66 = float(np.percentile(energies, 66))
        return ["weak" if e < p33 else "strong" if e >= p66 else "medium" for e in energies]
    except Exception as e:
        logger.warning(f"classify_beat_intensities: {e}")
        return ["medium"] * len(beats)


def classify_song_profile(y, sr: int, bpm: float) -> str:
    """
    Classifica a música como 'aggressive', 'medium' ou 'chill'.
    Controla a intensidade GERAL de todos os efeitos visuais.
    """
    if not LIBROSA_OK:
        return "medium"
    try:
        y = _clean_audio(y)
        rms     = librosa.feature.rms(y=y)[0]
        zcr     = librosa.feature.zero_crossing_rate(y)[0]
        onset   = librosa.onset.onset_strength(y=y, sr=sr)
        stft    = np.abs(librosa.stft(y))
        freqs   = librosa.fft_frequencies(sr=sr)
        total_e = float(np.mean(stft)) + 1e-9
        sub_m   = (freqs >= 20) & (freqs <= 80)
        sub_bass = float(np.mean(stft[sub_m])) / total_e if np.any(sub_m) else 0.0

        avg_energy = float(np.mean(rms))
        avg_zcr    = float(np.mean(zcr))
        avg_onset  = float(np.mean(onset))

        score = 0.0
        if bpm > 145:    score += 2.5
        elif bpm > 125:  score += 1.5
        elif bpm > 110:  score += 0.8

        if avg_energy > 0.12:   score += 2.5
        elif avg_energy > 0.07: score += 1.5
        elif avg_energy > 0.04: score += 0.6

        if avg_zcr > 0.12:   score += 1.2
        elif avg_zcr > 0.07: score += 0.6

        if sub_bass > 0.07:   score += 1.2
        elif sub_bass > 0.04: score += 0.6

        if avg_onset > 2.5:   score += 1.0
        elif avg_onset > 1.5: score += 0.4

        if score >= 5.5: return "aggressive"
        if score >= 2.5: return "medium"
        return "chill"
    except Exception as e:
        logger.warning(f"classify_song_profile: {e}")
        return "medium"


def compute_energy_curve(y, sr: int, n_points: int = 100) -> list:
    """Curva de energia normalizada com n_points amostras (0.0 a 1.0)."""
    if not LIBROSA_OK:
        return [0.5] * n_points
    try:
        y = _clean_audio(y)
        rms  = librosa.feature.rms(y=y, frame_length=FRAME_LEN, hop_length=HOP_LENGTH)[0]
        idx  = np.linspace(0, len(rms) - 1, n_points).astype(int)
        curve = rms[idx].astype(float)
        mn, mx = curve.min(), curve.max()
        if mx > mn:
            curve = (curve - mn) / (mx - mn)
        return curve.tolist()
    except Exception as e:
        logger.warning(f"compute_energy_curve: {e}")
        return [0.5] * n_points


# ══════════════════════════════════════════════════════════════════
# ANÁLISE COMPLETA
# ══════════════════════════════════════════════════════════════════

def full_analysis(audio_path: str) -> dict:
    """
    Análise completa. Retorna:
        bpm, beats, bass_hits, snare_hits, hihat_hits,
        drop_time, sections, beat_intensities, song_profile,
        energy_curve, duration
    """
    result = {
        "bpm":              120.0,
        "beats":            [],
        "bass_hits":        [],
        "kicks":            [],  # alias compatível com video_generator/Remotion
        "snare_hits":       [],
        "hihat_hits":       [],
        "drop_time":        None,
        "sections":         {},
        "beat_intensities": [],
        "song_profile":     "medium",
        "energy_curve":     [],
        "duration":         0.0,
    }
    if not LIBROSA_OK:
        return result
    try:
        logger.info(f"  [analysis] Carregando: {Path(audio_path).name}")
        y, sr    = librosa.load(audio_path, mono=True)
        y = _clean_audio(y)
        duration = float(librosa.get_duration(y=y, sr=sr))
        result["duration"] = duration

        bpm, beats = detect_beats(y, sr)
        result["bpm"]   = round(bpm, 1)
        result["beats"] = beats

        bass_hits = detect_bass_hits(y, sr)
        result["bass_hits"] = bass_hits
        result["kicks"] = bass_hits  # alias para qualquer parte antiga do bot que leia "kicks"
        result["snare_hits"] = detect_snare_hits(y, sr)
        result["hihat_hits"] = detect_hihat_hits(y, sr)

        drop = detect_drop(y, sr, duration)
        result["drop_time"] = drop
        result["sections"]  = detect_sections(y, sr, duration, drop)
        result["beat_intensities"] = classify_beat_intensities(beats, y, sr)
        result["song_profile"]     = classify_song_profile(y, sr, bpm)
        result["energy_curve"]     = compute_energy_curve(y, sr)

        drop_s = f"{drop:.2f}s" if drop else "não detectado"
        logger.info(
            f"  [analysis] ✓ BPM={bpm:.1f} | beats={len(beats)} | "
            f"kicks={len(result['bass_hits'])} | snares={len(result['snare_hits'])} | "
            f"hihats={len(result['hihat_hits'])} | drop={drop_s} | "
            f"perfil={result['song_profile']}"
        )
    except Exception as e:
        logger.error(f"full_analysis falhou: {e}", exc_info=True)
    return result


def crop_analysis(analysis: dict, start: float, duration: float) -> dict:
    """Recorta a análise para a janela [start, start+duration]."""
    end = start + duration

    def _crop(times: list) -> list:
        return [round(t - start, 4) for t in times if start <= t < end]

    beats_orig = analysis.get("beats", [])
    ints_orig  = analysis.get("beat_intensities", [])
    crop_beats, crop_ints = [], []
    for i, t in enumerate(beats_orig):
        if start <= t < end:
            crop_beats.append(round(t - start, 4))
            crop_ints.append(ints_orig[i] if i < len(ints_orig) else "medium")

    drop_raw  = analysis.get("drop_time")
    drop_crop = round(drop_raw - start, 4) if (drop_raw is not None and start <= drop_raw < end) else None

    # Ajusta seções
    sec = analysis.get("sections", {})
    sec_keys = ["intro_end", "buildup_start", "buildup_end",
                "drop_start", "drop_end", "calm_start", "calm_end", "outro_start"]
    new_sec = {k: max(0.0, round(sec[k] - start, 4)) for k in sec_keys if k in sec}

    cropped_bass_hits = _crop(analysis.get("bass_hits") or analysis.get("kicks", []))

    return {
        **analysis,
        "beats":            crop_beats,
        "bass_hits":        cropped_bass_hits,
        "kicks":            cropped_bass_hits,  # alias compatível
        "snare_hits":       _crop(analysis.get("snare_hits", [])),
        "hihat_hits":       _crop(analysis.get("hihat_hits", [])),
        "beat_intensities": crop_ints,
        "drop_time":        drop_crop,
        "sections":         new_sec,
        "duration":         duration,
    }


def find_best_window(audio_path: str, target_dur: int) -> tuple:
    """Encontra a janela ideal: começa antes do drop e captura o pico de energia."""
    if not LIBROSA_OK:
        return 0.0, float(target_dur)
    try:
        y, sr = librosa.load(audio_path, mono=True, duration=300)
        y = _clean_audio(y)
        total = float(librosa.get_duration(y=y, sr=sr))
        if total <= target_dur:
            return 0.0, total
        drop = detect_drop(y, sr, total)
        if drop is not None:
            ideal = max(0.0, drop - target_dur * 0.22)
            ideal = min(ideal, total - target_dur)
            return round(ideal, 2), float(target_dur)
        # Sem drop: janela de maior energia em 10%-80%
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        wf  = int(target_dur * sr / HOP_LENGTH)
        min_f = int(len(rms) * 0.10)
        max_f = max(min_f + 1, int(len(rms) * 0.80) - wf)
        best_f, best_e = min_f, -1.0
        for f in range(min_f, max_f, max(1, wf // 20)):
            e = float(np.mean(rms[f:f + wf]))
            if e > best_e:
                best_e, best_f = e, f
        return round(float(librosa.frames_to_time(best_f, sr=sr, hop_length=HOP_LENGTH)), 2), float(target_dur)
    except Exception as e:
        logger.warning(f"find_best_window: {e}")
        return 0.0, float(target_dur)


# ══════════════════════════════════════════════════════════════════
# CONSTRUTORES DE EXPRESSÕES FFMPEG
# ══════════════════════════════════════════════════════════════════

def build_flash_expression(
    analysis: dict,
    base_brightness: float,
    beat_flash: float,
    bass_flash: float,
    drop_flash: float,
) -> str:
    """
    Expressão FFmpeg para brilho beat-reactive.
    Inclui: beat (por intensidade) + kick + snare + drop.
    """
    beats      = analysis.get("beats", [])
    bass_hits  = analysis.get("bass_hits") or analysis.get("kicks", [])
    snare_hits = analysis.get("snare_hits", [])
    drop_time  = analysis.get("drop_time")
    intensities = analysis.get("beat_intensities", [])

    parts = [str(round(base_brightness, 4))]

    # Beat (intensidade variável)
    intensity_map = {"weak": 0.50, "medium": 1.00, "strong": 1.65}
    for i, t in enumerate(beats[:60]):
        lvl = intensities[i] if i < len(intensities) else "medium"
        s   = beat_flash * intensity_map.get(lvl, 1.0)
        parts.append(f"{s:.4f}*max(0,1-abs(t-{t:.4f})/0.08)")

    # Kick / bass
    for t in bass_hits[:55]:
        parts.append(f"{bass_flash:.4f}*max(0,1-abs(t-{t:.4f})/0.06)")

    # Snare → flash rápido e brilhante
    snare_str = bass_flash * 0.82
    for t in snare_hits[:50]:
        parts.append(f"{snare_str:.4f}*max(0,1-abs(t-{t:.4f})/0.05)")

    # Drop
    if drop_time is not None:
        parts.append(f"{drop_flash:.4f}*max(0,1-abs(t-{drop_time:.4f})/0.28)")

    return f"({'+'.join(parts)})"


def build_shake_expression(
    analysis: dict,
    max_shake_x: float,
    max_shake_y: float,
    style: str = "default",
) -> tuple:
    """
    Expressões (x, y) de shake com:
    - Bass: forte impulso
    - Hi-hat: micro-jitter rápido e sutil
    - Drop: mega-shake
    """
    bass_hits  = analysis.get("bass_hits") or analysis.get("kicks", [])
    hihat_hits = analysis.get("hihat_hits", [])
    drop_time  = analysis.get("drop_time")
    profile    = analysis.get("song_profile", "medium")

    heavy = style in {"phonk", "metal", "rock", "trap", "electronic", "funk"}
    pm    = {"aggressive": 1.7, "medium": 1.0, "chill": 0.45}.get(profile, 1.0)
    mult  = (1.5 if heavy else 1.0) * pm

    bx = f"(sin(t*2.9)*{max_shake_x*0.70*mult:.3f}+sin(t*5.2)*{max_shake_x*0.30*mult:.3f})"
    by = f"(cos(t*2.6)*{max_shake_y*0.70*mult:.3f}+cos(t*4.8)*{max_shake_y*0.30*mult:.3f})"

    # Bass boost
    if bass_hits:
        bass_boost = "+".join([
            f"1.8*max(0,1-abs(t-{t:.4f})/0.12)" for t in bass_hits[:55]
        ])
        bx = f"({bx})*(1+{bass_boost})"
        by = f"({by})*(1+{bass_boost})"

    # Hi-hat micro-jitter (pequeno, rápido, sutil)
    if hihat_hits:
        jx = "+".join([
            f"1.6*sin({(i*17+7):.1f})*max(0,1-abs(t-{t:.4f})/0.04)"
            for i, t in enumerate(hihat_hits[:65])
        ])
        jy = "+".join([
            f"1.3*cos({(i*13+5):.1f})*max(0,1-abs(t-{t:.4f})/0.04)"
            for i, t in enumerate(hihat_hits[:65])
        ])
        bx = f"({bx}+({jx}))"
        by = f"({by}+({jy}))"

    # Drop mega-shake
    if drop_time is not None:
        dm_val = 4.2 if heavy else 2.8
        dm = f"(1+{dm_val}*max(0,1-abs(t-{drop_time:.4f})/0.25))"
        bx = f"({bx})*{dm}"
        by = f"({by})*{dm}"

    # Hook gate (suaviza os primeiros 0.08s)
    gate = "if(lt(t,0.08),0.02,1.0)"
    return f"({bx})*{gate}", f"({by})*{gate}"


def build_zoom_expression(
    analysis: dict,
    total_frames: int,
    base_speed: float,
    pulse_strength: float,
    max_zoom: float,
    fps: int,
) -> str:
    """
    Expressão de zoom com:
    - Base cíclica (loop seamless)
    - Section modulation (intro sutil → buildup crescente → drop máximo)
    - Beat, bass e drop pulses
    - Drift multi-axis orgânico
    - Profile-based scaling
    """
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits") or analysis.get("kicks", [])
    drop_time = analysis.get("drop_time")
    sections  = analysis.get("sections", {})
    duration  = analysis.get("duration", total_frames / fps)
    intensities = analysis.get("beat_intensities", [])
    profile   = analysis.get("song_profile", "medium")

    pm = {"aggressive": 1.5, "medium": 1.0, "chill": 0.55}.get(profile, 1.0)

    # Base cíclica — loop seamless
    speed = base_speed * pm
    base  = f"(1.0+{speed:.4f}*(0.5-0.5*cos(2*PI*on/{total_frames})))"

    # Drift senoidal multi-axis
    ps   = pulse_strength * pm
    drift = (
        f"({ps*0.55:.4f}*sin(on*0.062+0.2)*cos(on*0.031)+"
        f"{ps*0.28:.4f}*sin(on*0.118+1.4))"
    )

    # Beat pulses com intensidade variável
    imap = {"weak": 0.003, "medium": 0.005, "strong": 0.009}
    bp   = [
        f"{imap.get(intensities[i] if i < len(intensities) else 'medium', 0.005) * pm:.4f}"
        f"*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.08*fps))})"
        for i, b in enumerate(beats[:70])
    ]
    beat_pulse = f"({'+'.join(bp)})" if bp else "0"

    # Bass punch
    bsp = [
        f"{0.018*pm:.4f}*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.06*fps))})"
        for b in bass_hits[:60]
    ]
    bass_pulse = f"({'+'.join(bsp)})" if bsp else "0"

    # Drop punch
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({0.14*pm:.4f}*max(0,1-abs(on-{df})/{max(1,int(0.05*fps))})+"
            f"{0.055*pm:.4f}*max(0,({int(0.4*fps)}-abs(on-{df+int(0.1*fps)}))/{int(0.4*fps)}))"
        )

    # Section modulator
    sec_mod = _section_zoom_mod(sections, fps)

    full = f"({base}+{drift}+{beat_pulse}+{bass_pulse}+{drop_expr})*{sec_mod}"
    return f"min(max({full},1.0),{max_zoom+0.16:.3f})"


def _section_zoom_mod(sections: dict, fps: int) -> str:
    """
    Multiplicador de zoom por seção:
    intro=0.50, buildup ramp 0.50→1.00, drop=1.00, calm=0.65, outro=0.45
    """
    ie  = sections.get("intro_end", 10.0)
    bs  = sections.get("buildup_start", 10.0)
    be  = sections.get("buildup_end", 30.0)
    ds  = sections.get("drop_start", 30.0)
    de  = sections.get("drop_end", 50.0)
    cs  = sections.get("calm_start", 50.0)
    ce  = sections.get("calm_end", 70.0)
    os_ = sections.get("outro_start", 70.0)

    ie_f  = int(ie  * fps)
    bs_f  = int(bs  * fps)
    be_f  = int(be  * fps)
    ds_f  = int(ds  * fps)
    de_f  = int(de  * fps)
    cs_f  = int(cs  * fps)
    ce_f  = int(ce  * fps)
    os_f  = int(os_ * fps)
    rng   = max(be_f - bs_f, 1)

    return (
        f"if(lte(on,{ie_f}),0.50,"
        f"if(between(on,{bs_f},{be_f}),"
        f"0.50+(on-{bs_f})*0.50/{rng},"
        f"if(between(on,{ds_f},{de_f}),1.00,"
        f"if(between(on,{cs_f},{ce_f}),0.65,"
        f"if(gte(on,{os_f}),0.45,0.80)))))"
    )



def build_remotion_audio_data(analysis: dict, rms: list | None = None) -> dict:
    """
    Monta JSON compatível com o Composition.tsx do Remotion.
    Mantém os nomes:
    - rms / audio_data
    - beats
    - bass_hits
    - kicks
    - bpm
    - drop_time
    """
    bass_hits = analysis.get("bass_hits") or analysis.get("kicks") or []
    beats = analysis.get("beats") or []

    return {
        "rms": rms or analysis.get("rms") or analysis.get("audio_data") or analysis.get("energy_curve") or [],
        "audio_data": rms or analysis.get("audio_data") or analysis.get("rms") or analysis.get("energy_curve") or [],
        "beats": beats,
        "bass_hits": bass_hits,
        "kicks": bass_hits,
        "snare_hits": analysis.get("snare_hits", []),
        "hihat_hits": analysis.get("hihat_hits", []),
        "bpm": analysis.get("bpm", 120.0),
        "drop_time": analysis.get("drop_time"),
        "duration": analysis.get("duration", 0.0),
        "song_profile": analysis.get("song_profile", "medium"),
    }

def save_debug(data: dict, path: Optional[str] = None) -> None:
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        out  = path or str(DEBUG_DIR / f"analysis_{int(time.time())}.json")
        safe = {k: v for k, v in data.items()
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))}
        with open(out, "w", encoding="utf-8") as f:
            json.dump(safe, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"save_debug: {e}")
