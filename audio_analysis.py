"""
audio_analysis.py — Elite Audio Engine v4.0 HYPNOTIC EDITION
=============================================================
NOVIDADES v4.0:
- Detecção separada: Kick / Snare / Hi-hat / Bass
- Classificação de intensidade de beat (fraco / médio / forte)
- Detecção de seções: intro / build-up / drop / calm / outro
- Score de energia por frame para graduar efeitos
- BPM grid para sincronização perfeita de loop
- Fingerprint de energia para escolha automática de perfil
- Perfil automático de edição: zoom / shake / flash / logo / loop
- Expressões prontas para logo pulsando, hi-hat jitter e rotação suave
- Randomização controlada por música para evitar vídeos repetidos
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
import random
from pathlib import Path
from typing import Optional

logger = logging.getLogger("audio_analysis")

try:
    import numpy as np
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa não encontrado — usando ffmpeg fallback.")

SR          = 22_050
HOP         = 256
MIN_BEAT_GAP = 0.10
MIN_BASS_GAP = 0.12
MIN_DROP_GAP = 2.0
MAX_BEATS    = 500
MAX_BASS     = 250
MAX_SNARE    = 200
MAX_HIHAT    = 400


# ═══════════════════════════════════════════════════════════════════
# LIBROSA ENGINE
# ═══════════════════════════════════════════════════════════════════

def _load(path: str):
    return librosa.load(path, sr=SR, mono=True)


def _detect_beats(y, sr) -> tuple[list[float], float]:
    _, y_perc = librosa.effects.hpss(y, margin=6.0)
    tempo, beat_frames = librosa.beat.beat_track(
        y=y_perc, sr=sr, hop_length=HOP, trim=False,
        units="frames", tightness=120,
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP)
    onset_env = librosa.onset.onset_strength(
        y=y_perc, sr=sr, hop_length=HOP,
        aggregate=np.median, fmax=8000,
    )
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=HOP,
        backtrack=True, pre_max=2, post_max=2,
        pre_avg=3, post_avg=3, delta=0.05, wait=3,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP)
    combined = sorted(set(
        [round(float(t), 4) for t in beat_times] +
        [round(float(t), 4) for t in onset_times]
    ))
    filtered = []
    for t in combined:
        if not filtered or (t - filtered[-1]) >= MIN_BEAT_GAP:
            filtered.append(t)
    bpm = float(tempo) if np.isscalar(tempo) else float(np.atleast_1d(tempo)[0])
    return filtered[:MAX_BEATS], bpm


def _detect_kick(y, sr) -> list[float]:
    """Sub-bass 40-100Hz = kick fundamental"""
    D = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    kick_mask = (freqs >= 40) & (freqs <= 100)
    mid_mask  = (freqs >= 100) & (freqs <= 250)
    energy = D[kick_mask].sum(0) * 0.65 + D[mid_mask].sum(0) * 0.35
    max_e = energy.max()
    if max_e < 1e-8:
        return []
    norm = energy / max_e
    smooth = np.convolve(norm, np.ones(3) / 3, mode="same")
    times = librosa.frames_to_time(np.arange(len(smooth)), sr=sr, hop_length=HOP)
    window = int(sr / HOP * 2.0)
    thresh_g = float(smooth.mean()) + 0.6 * float(smooth.std())
    hits = []
    for i in range(4, len(smooth) - 4):
        local = smooth[max(0, i - window):i]
        thresh = max(thresh_g, float(local.mean()) * 1.4)
        is_peak = (
            smooth[i] > smooth[i-1] and smooth[i] > smooth[i+1]
            and smooth[i] > smooth[i-2] and smooth[i] > thresh
            and smooth[i] > 0.35
        )
        if is_peak and i >= 2:
            if smooth[i] - smooth[i-2] < 0.08:
                continue
        if is_peak:
            t = float(times[i])
            if not hits or (t - hits[-1]) >= MIN_BASS_GAP:
                hits.append(round(t, 4))
    return hits[:MAX_BASS]


def _detect_snare(y, sr) -> list[float]:
    """150-350Hz + componente noise = snare"""
    D = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    snare_mask = (freqs >= 150) & (freqs <= 350)
    noise_mask  = (freqs >= 1000) & (freqs <= 8000)
    energy = D[snare_mask].sum(0) * 0.55 + D[noise_mask].sum(0) * 0.45
    norm = energy / (energy.max() + 1e-8)
    smooth = np.convolve(norm, np.ones(3) / 3, mode="same")
    times = librosa.frames_to_time(np.arange(len(smooth)), sr=sr, hop_length=HOP)
    thresh = float(smooth.mean()) + 0.8 * float(smooth.std())
    hits = []
    for i in range(3, len(smooth) - 3):
        if (smooth[i] > smooth[i-1] and smooth[i] > smooth[i+1]
                and smooth[i] > thresh and smooth[i] > 0.40):
            t = float(times[i])
            if not hits or (t - hits[-1]) >= 0.15:
                hits.append(round(t, 4))
    return hits[:MAX_SNARE]


def _detect_hihat(y, sr) -> list[float]:
    """7kHz+ = hi-hat"""
    D = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    mask = freqs >= 7000
    energy = D[mask].sum(0)
    norm = energy / (energy.max() + 1e-8)
    smooth = np.convolve(norm, np.ones(2) / 2, mode="same")
    times = librosa.frames_to_time(np.arange(len(smooth)), sr=sr, hop_length=HOP)
    thresh = float(smooth.mean()) + 0.5 * float(smooth.std())
    hits = []
    for i in range(2, len(smooth) - 2):
        if smooth[i] > smooth[i-1] and smooth[i] > smooth[i+1] and smooth[i] > thresh:
            t = float(times[i])
            if not hits or (t - hits[-1]) >= 0.06:
                hits.append(round(t, 4))
    return hits[:MAX_HIHAT]


def _classify_beat_intensity(
    beat_time: float,
    kicks: list[float],
    snares: list[float],
    energy_curve: list[float],
    times_curve: list[float],
) -> str:
    """
    Retorna 'weak' | 'medium' | 'strong'.

    Ideia:
    - strong: kick/snare muito próximos + energia alta
    - medium: kick ou snare com energia média
    - weak: pulso leve para manter movimento sem exagerar
    """
    has_kick  = any(abs(beat_time - k) < 0.065 for k in kicks)
    has_snare = any(abs(beat_time - s) < 0.070 for s in snares)

    local_e = 0.5
    if energy_curve and times_curve:
        idx = min(range(len(times_curve)), key=lambda i: abs(times_curve[i] - beat_time))
        local_e = float(energy_curve[idx])

    if (has_kick and has_snare and local_e > 0.55) or (has_kick and local_e > 0.78):
        return "strong"
    if has_kick or has_snare or local_e > 0.58:
        return "medium"
    return "weak"


def _detect_sections(y, sr, beats: list[float], bpm: float) -> dict:
    """
    Divide a música em seções: intro / build / drop / calm / outro
    Retorna dict com timestamps de início de cada seção.
    """
    rms = librosa.feature.rms(y=y, frame_length=4096, hop_length=512)[0]
    spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)

    rms_norm = rms / (rms.max() + 1e-8)
    cent_norm = spec_cent / (spec_cent.max() + 1e-8)

    dur = float(len(y) / sr)
    sections = {
        "intro":  0.0,
        "build":  None,
        "drop":   None,
        "calm":   None,
        "outro":  None,
    }

    # Intro: primeiros 10-15% da música
    intro_end = dur * 0.12

    # Drop: maior salto de energia no intervalo 20-80%
    window = 8
    best_score = -999.0
    best_drop = None
    start_i = max(window, int(len(rms_norm) * 0.20))
    end_i   = min(len(rms_norm) - window, int(len(rms_norm) * 0.80))
    for i in range(start_i, end_i):
        before = rms_norm[i-window:i].mean()
        after  = rms_norm[i:i+window].mean()
        score  = (after - before) * 2.0 + rms_norm[i] + cent_norm[i] * 0.5
        if score > best_score:
            best_score = score
            best_drop = float(times[i])
    sections["drop"] = best_drop

    # Build: começa ~8 beats antes do drop
    if best_drop and bpm > 0:
        beat_dur = 60.0 / bpm
        sections["build"] = max(intro_end, best_drop - beat_dur * 8)

    # Calm: seção após o drop com energia reduzida
    if best_drop:
        calm_start = best_drop + dur * 0.15
        calm_idx = min(range(len(times)), key=lambda i: abs(times[i] - calm_start))
        window2 = 12
        min_e = 999.0
        calm_t = None
        for i in range(calm_idx, min(len(rms_norm) - window2, int(len(rms_norm) * 0.85))):
            e = rms_norm[i:i+window2].mean()
            if e < min_e:
                min_e = e
                calm_t = float(times[i])
        if calm_t and min_e < 0.55:
            sections["calm"] = calm_t

    # Outro: últimos 8%
    sections["outro"] = dur * 0.92

    return sections


def _energy_curve(y, sr) -> tuple[list[float], list[float]]:
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    norm = rms / (rms.max() + 1e-8)
    return norm.tolist(), times.tolist()


def _detect_drop(y, sr, beats: list[float]) -> Optional[float]:
    frame_len = int(sr * 0.5)
    hop = int(sr * 0.1)
    rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    if len(rms) < 20:
        return None
    rms_n = rms / (rms.max() + 1e-8)
    cen_n = centroid / (centroid.max() + 1e-8)
    start_i = max(4, int(len(rms_n) * 0.12))
    end_i   = min(len(rms_n) - 4, int(len(rms_n) * 0.88))
    best_score = -999.0
    best_time  = None
    window = 6
    for i in range(start_i, end_i):
        before_rms  = rms_n[max(0, i-window):i].mean()
        after_rms   = rms_n[i:i+window].mean()
        before_cen  = cen_n[max(0, i-window):i].mean()
        after_cen   = cen_n[i:i+window].mean()
        t = float(times[i])
        beats_near = sum(1 for b in beats if t <= b <= t + 1.5)
        score = (after_rms - before_rms) * 2.5 + (before_cen - after_cen) * 1.2 + rms_n[i] * 0.8 + beats_near * 0.15
        if score > best_score:
            best_score = score
            best_time  = round(t, 4)
    return best_time


def _fingerprint_energy(y, sr) -> dict:
    """
    Retorna métricas globais para escolha automática de perfil de edição.
    """
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=512)[0]
    _, y_perc = librosa.effects.hpss(y, margin=6.0)
    perc_rms = librosa.feature.rms(y=y_perc, frame_length=2048, hop_length=512)[0]

    avg_energy    = float(rms.mean() / (rms.max() + 1e-8))
    energy_var    = float(rms.std() / (rms.max() + 1e-8))
    perc_ratio    = float(perc_rms.mean() / (rms.mean() + 1e-8))
    brightness    = float(spec_rolloff.mean() / sr)
    transient_den = float(zcr.mean())

    # Categorização automática
    if perc_ratio > 0.55 and avg_energy > 0.35:
        intensity = "aggressive"   # phonk, trap, metal, electronic
    elif avg_energy > 0.25 and energy_var > 0.15:
        intensity = "medium"       # rock, funk, indie
    else:
        intensity = "chill"        # lofi, cinematic, dark atmospheric

    return {
        "avg_energy":    avg_energy,
        "energy_var":    energy_var,
        "perc_ratio":    perc_ratio,
        "brightness":    brightness,
        "transient_den": transient_den,
        "intensity":     intensity,
    }



# ═══════════════════════════════════════════════════════════════════
# EDIT PROFILE / EXPRESSIONS
# ═══════════════════════════════════════════════════════════════════

def build_edit_profile(analysis: dict) -> dict:
    """
    Converte a análise musical em um perfil prático de edição.

    Esse perfil deve ser usado pelo video_generator.py para decidir:
    - intensidade do zoom
    - força do shake
    - flash
    - logo pulsando
    - nível de glitch
    """
    fp = analysis.get("fingerprint", {}) or {}
    intensity = fp.get("intensity", "medium")
    avg_energy = float(analysis.get("avg_energy", 0.5) or 0.5)
    bpm = float(analysis.get("bpm") or 120.0)

    if intensity == "aggressive":
        profile = {
            "name": "aggressive",
            "max_zoom": 1.24,
            "zoom_speed": 0.030,
            "pulse_strength": 0.018,
            "shake_x": 18.0,
            "shake_y": 12.0,
            "beat_flash": 0.10,
            "bass_flash": 0.22,
            "drop_flash": 0.38,
            "logo_pulse": 0.18,
            "logo_drop_pulse": 0.42,
            "glitch_strength": 0.75,
            "motion_blur": 1,
        }
    elif intensity == "chill":
        profile = {
            "name": "chill",
            "max_zoom": 1.10,
            "zoom_speed": 0.014,
            "pulse_strength": 0.006,
            "shake_x": 4.5,
            "shake_y": 3.0,
            "beat_flash": 0.035,
            "bass_flash": 0.070,
            "drop_flash": 0.16,
            "logo_pulse": 0.06,
            "logo_drop_pulse": 0.18,
            "glitch_strength": 0.18,
            "motion_blur": 0,
        }
    else:
        profile = {
            "name": "medium",
            "max_zoom": 1.16,
            "zoom_speed": 0.022,
            "pulse_strength": 0.011,
            "shake_x": 9.0,
            "shake_y": 6.0,
            "beat_flash": 0.06,
            "bass_flash": 0.14,
            "drop_flash": 0.26,
            "logo_pulse": 0.11,
            "logo_drop_pulse": 0.28,
            "glitch_strength": 0.42,
            "motion_blur": 1,
        }

    # Ajuste fino por BPM e energia média
    if bpm >= 150:
        profile["shake_x"] *= 1.10
        profile["shake_y"] *= 1.10
        profile["pulse_strength"] *= 1.15
    elif bpm <= 90:
        profile["shake_x"] *= 0.82
        profile["shake_y"] *= 0.82
        profile["zoom_speed"] *= 0.85

    energy_boost = min(1.18, max(0.85, 0.85 + avg_energy * 0.55))
    for k in ("shake_x", "shake_y", "pulse_strength", "logo_pulse"):
        profile[k] = round(float(profile[k]) * energy_boost, 5)

    return profile


def stable_song_seed(audio_path: str) -> int:
    """
    Cria uma seed estável por arquivo.
    Assim cada música ganha pequenas variações, mas o resultado não muda toda hora.
    """
    p = Path(audio_path)
    raw = f"{p.name}:{p.stat().st_size if p.exists() else 0}"
    return abs(hash(raw)) % 999_999


def add_controlled_variation(profile: dict, audio_path: str, amount: float = 0.08) -> dict:
    """
    Randomização controlada anti-repetição.
    Não quebra sync porque só muda intensidade, não muda timestamps.
    """
    rng = random.Random(stable_song_seed(audio_path))
    out = dict(profile)

    for key in ("max_zoom", "zoom_speed", "pulse_strength", "shake_x", "shake_y", "logo_pulse"):
        if key in out:
            factor = rng.uniform(1.0 - amount, 1.0 + amount)
            out[key] = round(float(out[key]) * factor, 5)

    out["variation_seed"] = stable_song_seed(audio_path)
    out["drift_phase"] = round(rng.uniform(0, 6.28318), 5)
    out["rotation_phase"] = round(rng.uniform(0, 6.28318), 5)
    return out


def build_logo_pulse_expression(analysis: dict, base_scale: float = 1.0) -> str:
    """
    Expressão FFmpeg para logo pulsar com beat/bass/drop.

    Use em overlay/scale do logo:
    scale = iw*EXPR : ih*EXPR

    Kick/Bass = pulso maior.
    Beat normal = pulso menor.
    Drop = explosão controlada.
    """
    beats = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")
    bi = analysis.get("beat_intensities", {})

    expr = f"{base_scale:.4f}"

    # Beat pulse por intensidade
    beat_parts = []
    for b in beats[:110]:
        inten = bi.get(str(round(b, 4)), "weak")
        amp = 0.035 if inten == "weak" else 0.070 if inten == "medium" else 0.115
        beat_parts.append(f"{amp:.4f}*between(t,{max(0,b-0.025):.4f},{b+0.110:.4f})")
    if beat_parts:
        expr = f"({expr}+{'+'.join(beat_parts)})"

    # Bass/kick pulse mais forte
    bass_parts = [
        f"0.1050*between(t,{max(0,b-0.020):.4f},{b+0.135:.4f})"
        for b in bass_hits[:90]
    ]
    if bass_parts:
        expr = f"({expr}+{'+'.join(bass_parts)})"

    if drop_time is not None:
        expr = f"({expr}+0.2800*between(t,{max(0,drop_time-0.040):.4f},{drop_time+0.260:.4f}))"

    # Suavização visual mínima constante
    expr = f"({expr}+0.012*sin(t*6.28318))"
    return expr


def build_hihat_jitter_expression(analysis: dict, strength: float = 1.0) -> tuple[str, str]:
    """
    Expressões leves para micro-jitter em hi-hat.
    Ideal para detalhe fino, sem ficar tremedeira exagerada.
    """
    hihats = analysis.get("hihats", [])
    if not hihats:
        return "0", "0"

    parts_x = [
        f"{0.55*strength:.3f}*sin(t*95)*between(t,{max(0,h-0.010):.4f},{h+0.045:.4f})"
        for h in hihats[:160]
    ]
    parts_y = [
        f"{0.38*strength:.3f}*cos(t*110)*between(t,{max(0,h-0.010):.4f},{h+0.045:.4f})"
        for h in hihats[:160]
    ]
    return f"({'+'.join(parts_x)})", f"({'+'.join(parts_y)})"


def build_rotation_expression(analysis: dict, max_degrees: float = 1.2) -> str:
    """
    Rotação suave e cíclica para evitar frame parado.
    No drop dá um pequeno impacto extra.
    """
    drop_time = analysis.get("drop_time")
    expr = f"({max_degrees:.3f}*PI/180*sin(t*0.85))"
    if drop_time is not None:
        expr = f"({expr}+0.8*PI/180*between(t,{max(0,drop_time-0.030):.4f},{drop_time+0.180:.4f}))"
    return expr


def build_loop_safe_zoom(duration: float, max_extra: float = 0.08) -> str:
    """
    Zoom cíclico: começo e fim combinam melhor.
    Bom para loop infinito.
    """
    return f"(1+{max_extra:.5f}*(0.5-0.5*cos(2*PI*t/{float(duration):.5f})))"


def build_effect_bundle(analysis: dict, audio_path: str, duration: float, fps: int = 30) -> dict:
    """
    Pacote final para o video_generator.py consumir.
    Junta perfil, flash, shake, zoom, logo, jitter e rotação.
    """
    profile = add_controlled_variation(build_edit_profile(analysis), audio_path)

    zoom = build_zoom_expression(
        analysis=analysis,
        duration=duration,
        fps=fps,
        max_zoom=profile["max_zoom"],
        zoom_speed=profile["zoom_speed"],
        pulse_strength=profile["pulse_strength"],
    )
    flash = build_flash_expression(
        analysis=analysis,
        base_brightness=0.0,
        beat_flash=profile["beat_flash"],
        bass_flash=profile["bass_flash"],
        drop_flash=profile["drop_flash"],
    )
    shake_x, shake_y = build_shake_expression(
        analysis=analysis,
        base_x=profile["shake_x"],
        base_y=profile["shake_y"],
    )
    hihat_x, hihat_y = build_hihat_jitter_expression(
        analysis=analysis,
        strength=profile["glitch_strength"],
    )

    return {
        "profile": profile,
        "zoom_expr": zoom,
        "loop_zoom_expr": build_loop_safe_zoom(duration, max_extra=profile["pulse_strength"]),
        "flash_expr": flash,
        "shake_x_expr": shake_x,
        "shake_y_expr": shake_y,
        "hihat_x_expr": hihat_x,
        "hihat_y_expr": hihat_y,
        "rotation_expr": build_rotation_expression(analysis),
        "logo_scale_expr": build_logo_pulse_expression(
            analysis,
            base_scale=1.0,
        ),
    }



# ═══════════════════════════════════════════════════════════════════
# FFMPEG FALLBACK
# ═══════════════════════════════════════════════════════════════════

def _ffmpeg_levels(audio_path: str, sample_rate: int = 30):
    cmd = ["ffmpeg", "-i", audio_path,
           "-af", f"astats=metadata=1:reset={sample_rate}",
           "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    times, levels = [], []
    cur_time = 0.0
    for line in result.stderr.splitlines():
        if "pts_time:" in line:
            try:
                cur_time = float(line.split("pts_time:")[1].split()[0])
            except Exception:
                pass
        if "RMS level dB:" in line:
            try:
                db = float(line.split("RMS level dB:")[1].strip())
                times.append(cur_time)
                levels.append(db)
            except Exception:
                pass
    return times, levels


def _normalize(levels):
    if not levels:
        return []
    finite = [x for x in levels if math.isfinite(x)]
    if not finite:
        return [0.0] * len(levels)
    mn, mx = min(finite), max(finite)
    if mx == mn:
        return [0.0] * len(levels)
    return [(x - mn) / (mx - mn) if math.isfinite(x) else 0.0 for x in levels]


def _smooth(levels, window=5):
    half = window // 2
    return [sum(levels[max(0, i-half):i+half+1]) / len(levels[max(0, i-half):i+half+1])
            for i in range(len(levels))]


def _ffmpeg_beats(audio_path) -> list[float]:
    times, levels = _ffmpeg_levels(audio_path, 28)
    norm = _smooth(_normalize(levels), 3)
    beats = []
    for i in range(2, len(norm)-2):
        local = norm[max(0,i-30):i+30]
        thr = sum(local)/len(local) * 1.16
        if norm[i] > norm[i-1] and norm[i] > norm[i+1] and norm[i] > thr and norm[i] > 0.24:
            beats.append(times[i])
    filtered = []
    for t in beats:
        if not filtered or (t - filtered[-1]) >= MIN_BEAT_GAP:
            filtered.append(t)
    return filtered[:MAX_BEATS]


def _ffmpeg_bass(audio_path) -> list[float]:
    times, levels = _ffmpeg_levels(audio_path, 32)
    norm = _smooth(_normalize(levels), 5)
    hits = []
    for i in range(4, len(norm)-4):
        before = sum(norm[i-4:i]) / 4
        cur = norm[i]
        attack = cur - before
        if cur > 0.50 and attack > 0.10 and cur >= norm[i-1]:
            if not hits or (times[i] - hits[-1]) >= MIN_BASS_GAP:
                hits.append(times[i])
    return hits[:MAX_BASS]


def _ffmpeg_drop(audio_path, beats) -> Optional[float]:
    times, levels = _ffmpeg_levels(audio_path, 14)
    norm = _smooth(_normalize(levels), 7)
    if len(norm) < 14:
        return None
    best_score, best_time = -999.0, None
    start = max(6, int(len(norm)*0.15))
    end   = min(len(norm)-6, int(len(norm)*0.85))
    for i in range(start, end):
        before = sum(norm[max(0,i-6):i]) / 6
        after  = sum(norm[i:i+6]) / 6
        t = times[i]
        score = (after-before)*2.0 + norm[i]*0.8 + after*1.1
        if score > best_score:
            best_score = score
            best_time = t
    return best_time


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def full_analysis(audio_path: str) -> dict:
    bpm = None
    sections = {}
    beat_intensities = {}
    fingerprint = {"intensity": "medium"}
    energy_curve_data = []
    energy_times_data = []

    if LIBROSA_AVAILABLE:
        logger.info("  → [librosa] Carregando áudio…")
        y, sr = _load(audio_path)

        logger.info("  → Beats + BPM…")
        beats, bpm = _detect_beats(y, sr)

        logger.info("  → Kick isolation (40-100Hz)…")
        bass_hits = _detect_kick(y, sr)

        logger.info("  → Snare detection…")
        snares = _detect_snare(y, sr)

        logger.info("  → Hi-hat detection…")
        hihats = _detect_hihat(y, sr)

        logger.info("  → Drop detection…")
        drop_time = _detect_drop(y, sr, beats)

        logger.info("  → Energy curve…")
        energy_curve_data, energy_times_data = _energy_curve(y, sr)

        logger.info("  → Section detection…")
        sections = _detect_sections(y, sr, beats, bpm or 120.0)

        logger.info("  → Beat intensity classification…")
        for b in beats:
            intensity = _classify_beat_intensity(b, bass_hits, snares, energy_curve_data, energy_times_data)
            beat_intensities[str(round(b, 4))] = intensity

        logger.info("  → Energy fingerprint…")
        fingerprint = _fingerprint_energy(y, sr)

        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        avg_energy = float(rms.mean() / (rms.max() + 1e-8))
    else:
        beats     = _ffmpeg_beats(audio_path)
        bass_hits = _ffmpeg_bass(audio_path)
        snares    = []
        hihats    = []
        drop_time = _ffmpeg_drop(audio_path, beats)
        avg_energy = 0.5
        beat_intensities = {str(b): "medium" for b in beats}

    logger.info(
        f"  → Beats:{len(beats)} Kicks:{len(bass_hits)} "
        f"Snares:{len(snares)} Hihats:{len(hihats)} "
        f"Drop:{drop_time:.2f}s BPM:{bpm:.1f}"
        if (drop_time and bpm) else f"  → Beats:{len(beats)}"
    )

    result = {
        "beats":             beats,
        "bass_hits":         bass_hits,
        "snares":            snares,
        "hihats":            hihats,
        "drop_time":         drop_time,
        "avg_energy":        avg_energy,
        "beat_count":        len(beats),
        "bpm":               bpm,
        "beat_intensities":  beat_intensities,
        "sections":          sections,
        "fingerprint":       fingerprint,
        "energy_curve":      energy_curve_data[:500],
        "energy_times":      energy_times_data[:500],
    }

    # Perfil inicial de edição pronto para o restante do bot.
    result["edit_profile"] = build_edit_profile(result)
    return result


def find_best_window(audio_path: str, duration: int, n_candidates: int = 6) -> tuple[float, float]:
    import random
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    audio_dur = float(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip())
    if audio_dur <= duration:
        return 0.0, float(audio_dur)
    min_s = audio_dur * 0.08
    max_s = min(audio_dur * 0.30, audio_dur - duration)
    if not LIBROSA_AVAILABLE or audio_dur > 600:
        return round(random.uniform(min_s, max(min_s, max_s)), 3), float(duration)
    y, sr = _load(audio_path)
    candidates = [min_s + (max_s - min_s) * i / max(1, n_candidates-1) for i in range(n_candidates)]
    best_sc, best_st = -1.0, candidates[0]
    for s in candidates:
        seg = y[int(s*sr):int((s+duration)*sr)]
        if len(seg) < sr:
            continue
        rms = librosa.feature.rms(y=seg, frame_length=2048, hop_length=512)[0]
        sc = float(rms.mean()) * 3.0 + float(rms.std()) * 2.0
        if sc > best_sc:
            best_sc, best_st = sc, s
    return round(best_st, 3), float(duration)


def crop_analysis(analysis: dict, start: float, duration: float) -> dict:
    end = start + duration
    def crop_list(lst, max_n=300):
        return [round(t - start, 4) for t in lst if start <= t <= end][:max_n]

    beats     = crop_list(analysis["beats"])
    bass_hits = crop_list(analysis["bass_hits"])
    snares    = crop_list(analysis.get("snares", []))
    hihats    = crop_list(analysis.get("hihats", []))

    drop = None
    dt = analysis.get("drop_time")
    if dt and start <= dt <= end:
        drop = round(dt - start, 4)

    # Ajustar beat_intensities
    bi = {}
    for k, v in analysis.get("beat_intensities", {}).items():
        t = float(k)
        if start <= t <= end:
            bi[str(round(t - start, 4))] = v

    # Ajustar seções
    sec = {}
    for k, v in analysis.get("sections", {}).items():
        if v is not None:
            adj = v - start
            if -2.0 <= adj <= duration + 2.0:
                sec[k] = round(adj, 3)
            else:
                sec[k] = None
        else:
            sec[k] = None

    cropped = {
        "beats":            beats,
        "bass_hits":        bass_hits,
        "snares":           snares,
        "hihats":           hihats,
        "drop_time":        drop,
        "avg_energy":       analysis["avg_energy"],
        "bpm":              analysis.get("bpm"),
        "beat_intensities": bi,
        "sections":         sec,
        "fingerprint":      analysis.get("fingerprint", {}),
    }
    cropped["edit_profile"] = build_edit_profile(cropped)
    return cropped


def build_flash_expression(
    analysis: dict,
    base_brightness: float,
    beat_flash: float  = 0.08,
    bass_flash: float  = 0.18,
    drop_flash: float  = 0.28,
    beat_window: float = 0.040,
    bass_window: float = 0.055,
) -> str:
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")
    bi        = analysis.get("beat_intensities", {})

    def make_conds(times, window):
        parts = []
        for t in times[:150]:
            s = max(0.0, t - window * 0.3)
            e = t + window * 0.7
            parts.append(f"between(t,{s:.4f},{e:.4f})")
        return parts

    expr = str(base_brightness)

    beat_conds = make_conds(beats, beat_window)
    if beat_conds:
        bc = "+".join(beat_conds)
        expr = f"if(gt({bc},0),{beat_flash},{expr})"

    bass_conds = make_conds(bass_hits, bass_window)
    if bass_conds:
        bsc = "+".join(bass_conds)
        expr = f"if(gt({bsc},0),{bass_flash},{expr})"

    if drop_time is not None:
        expr = f"if(between(t,{drop_time-0.04:.4f},{drop_time+0.14:.4f}),{drop_flash},{expr})"

    return expr


def build_shake_expression(analysis, base_x, base_y):
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])
    sx_a = base_x * 0.65
    sx_b = base_x * 0.35
    sy_a = base_y * 0.65
    sy_b = base_y * 0.35
    shake_x = f"(sin(t*2.7)*{sx_a:.2f}+sin(t*5.3)*{sx_b:.2f})"
    shake_y = f"(cos(t*2.4)*{sy_a:.2f}+cos(t*4.9)*{sy_b:.2f})"
    if bass_hits:
        boosts = [f"1.5*between(t,{max(0,t-0.03):.4f},{t+0.16:.4f})" for t in bass_hits[:50]]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"
    if drop_time:
        dm = f"(1+2.6*between(t,{drop_time-0.03:.4f},{drop_time+0.24:.4f}))"
        shake_x = f"({shake_x})*{dm}"
        shake_y = f"({shake_y})*{dm}"
    return shake_x, shake_y


def build_zoom_expression(analysis, duration, fps, max_zoom, zoom_speed, pulse_strength):
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")
    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.45 * fps)
    base  = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength*0.7}*sin(on*0.07+0.3)*cos(on*0.031))"
    beat_pulse = "0"
    if beats:
        parts = [f"0.004*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})" for b in beats[:70]]
        beat_pulse = f"({'+'.join(parts)})"
    bass_pulse = "0"
    if bass_hits:
        parts = [f"0.010*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+5})" for b in bass_hits[:60]]
        bass_pulse = f"({'+'.join(parts)})"
    drop_expr = "0"
    if drop_time:
        df = int(drop_time * fps)
        drop_expr = (
            f"(0.07*between(on,{df-1},{df+4})"
            f"+0.035*between(on,{df+5},{df+18})"
            f"+0.014*between(on,{df+19},{df+32}))"
        )
    full = f"{base}+{drift}+{beat_pulse}+{bass_pulse}+{drop_expr}"
    return f"if(lte(on,{intro_frames}),1.0,min(max({full},1.0),{max_zoom+0.08}))"


def save_debug(analysis: dict, output_file: str = "temp/debug_analysis.json"):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(x) for x in obj]
        try:
            return float(obj)
        except Exception:
            return obj
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(_clean(analysis), f, ensure_ascii=False, indent=2)
