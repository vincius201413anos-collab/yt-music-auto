"""
audio_analysis.py — Elite Audio Engine for Music Shorts.

Upgrades v2:
- librosa integration (real spectral analysis) with ffmpeg fallback
- True BPM detection via librosa beat_track
- Spectral bass isolation (sub-bass + mid-bass bands)
- Onset detection for tighter beat sync
- Smart window scoring: finds the most energetic + varied clip
- Drop detection using spectral centroid + energy variance
- Harmonic/percussive separation for cleaner beat grid
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("audio_analysis")

# ── Optional librosa import ────────────────────────────────────────────────────
try:
    import numpy as np
    import librosa
    LIBROSA_AVAILABLE = True
    logger.debug("librosa disponível — usando análise espectral completa.")
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa não encontrado — usando análise ffmpeg (instale: pip install librosa).")


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

SR_LIBROSA       = 22_050   # sample rate interno do librosa
HOP_LENGTH       = 512
BASS_LOW_HZ      = 40       # sub-bass
BASS_HIGH_HZ     = 200      # mid-bass
MIN_BEAT_GAP     = 0.16     # segundos mínimos entre beats
MIN_BASS_GAP     = 0.22
MIN_DROP_GAP     = 2.0      # drops devem estar separados

MAX_BEATS        = 300
MAX_BASS_HITS    = 160
MAX_BEATS_CROP   = 130
MAX_BASS_CROP    = 90


# ══════════════════════════════════════════════════════════════════════════════
# LIBROSA ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _librosa_load(audio_path: str):
    """Carrega áudio com librosa, retorna (y, sr)."""
    y, sr = librosa.load(audio_path, sr=SR_LIBROSA, mono=True)
    return y, sr


def _detect_beats_librosa(y: np.ndarray, sr: int) -> tuple[list[float], float]:
    """
    Beat detection via harmonic/percussive separation + beat tracker.
    Retorna (beat_times, bpm).
    """
    # Separar componente percussivo para beat tracking mais limpo
    _, y_perc = librosa.effects.hpss(y, margin=3.0)

    tempo, beat_frames = librosa.beat.beat_track(
        y=y_perc, sr=sr, hop_length=HOP_LENGTH,
        trim=False, units="frames"
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH)

    # Complementar com onset detection
    onset_env = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=HOP_LENGTH)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=HOP_LENGTH,
        backtrack=True, pre_max=3, post_max=3, pre_avg=5, post_avg=5,
        delta=0.07, wait=4
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH)

    # Merge beats + onsets, deduplicate
    combined = sorted(set(list(beat_times) + list(onset_times)))
    filtered: list[float] = []
    for t in combined:
        if not filtered or (t - filtered[-1]) >= MIN_BEAT_GAP:
            filtered.append(round(float(t), 4))

    bpm = float(tempo) if np.isscalar(tempo) else float(tempo[0])
    return filtered[:MAX_BEATS], bpm


def _detect_bass_librosa(y: np.ndarray, sr: int) -> list[float]:
    """
    Detecta bass hits via análise espectral (sub-bass + mid-bass).
    Muito mais preciso que RMS global.
    """
    # CQT para resolução de frequência melhor no baixo
    D = np.abs(librosa.stft(y, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr)

    bass_mask = (freqs >= BASS_LOW_HZ) & (freqs <= BASS_HIGH_HZ)
    bass_energy = D[bass_mask, :].mean(axis=0)

    # Normalizar
    if bass_energy.max() > 0:
        bass_norm = bass_energy / bass_energy.max()
    else:
        return []

    # Smooth leve
    bass_smooth = np.convolve(bass_norm, np.ones(5) / 5, mode="same")

    # Detectar picos
    times = librosa.frames_to_time(np.arange(len(bass_smooth)), sr=sr, hop_length=HOP_LENGTH)

    threshold = bass_smooth.mean() + 0.5 * bass_smooth.std()

    hits: list[float] = []
    for i in range(3, len(bass_smooth) - 3):
        is_peak = (
            bass_smooth[i] > bass_smooth[i - 1]
            and bass_smooth[i] > bass_smooth[i + 1]
            and bass_smooth[i] > threshold
            and bass_smooth[i] > 0.45
        )
        if is_peak:
            t = float(times[i])
            if not hits or (t - hits[-1]) >= MIN_BASS_GAP:
                hits.append(round(t, 4))

    return hits[:MAX_BASS_HITS]


def _detect_drop_librosa(y: np.ndarray, sr: int, beats: list[float]) -> Optional[float]:
    """
    Detecta o drop usando:
    - Salto de energia RMS
    - Salto de densidade de beats
    - Queda do centroide espectral (bass shift = drop)
    """
    frame_len = int(sr * 0.5)    # janela de 0.5s
    hop = int(sr * 0.1)          # hop de 100ms

    rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)

    if len(rms) < 20:
        return None

    # Normalizar
    rms_n = rms / (rms.max() + 1e-8)
    cen_n = centroid / (centroid.max() + 1e-8)

    start_idx = max(4, int(len(rms) * 0.12))
    end_idx   = min(len(rms) - 4, int(len(rms) * 0.88))

    best_score = -999.0
    best_time  = None
    window     = 6  # ~600ms look-back/look-ahead

    for i in range(start_idx, end_idx):
        before_rms = rms_n[max(0, i - window): i].mean()
        after_rms  = rms_n[i: i + window].mean()
        energy_jump = after_rms - before_rms

        before_cen = cen_n[max(0, i - window): i].mean()
        after_cen  = cen_n[i: i + window].mean()
        centroid_drop = before_cen - after_cen   # centroide cai no drop (mais bass)

        t = float(times[i])
        beats_near = sum(1 for b in beats if t <= b <= t + 1.5)

        score = (
            energy_jump  * 2.5
            + centroid_drop * 1.2
            + rms_n[i]   * 0.8
            + beats_near * 0.15
        )

        if score > best_score:
            best_score = score
            best_time  = round(t, 4)

    return best_time


def _score_window_librosa(
    y: np.ndarray, sr: int,
    start: float, duration: float
) -> float:
    """
    Pontua uma janela de clip:
    - Energia média alta = bom
    - Variância de energia = dinâmica = bom
    - Presença de beat density = bom
    """
    s = int(start * sr)
    e = int((start + duration) * sr)
    segment = y[s:e]

    if len(segment) < sr:
        return 0.0

    rms = librosa.feature.rms(y=segment, frame_length=2048, hop_length=512)[0]
    energy_mean = float(rms.mean())
    energy_var  = float(rms.std())

    _, beat_frames = librosa.beat.beat_track(y=segment, sr=sr, hop_length=512)
    beat_density = len(beat_frames) / max(1.0, duration)

    score = energy_mean * 3.0 + energy_var * 2.0 + (beat_density / 10.0) * 1.5
    return score


# ══════════════════════════════════════════════════════════════════════════════
# FFMPEG FALLBACK ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def extract_audio_levels(audio_path: str, sample_rate: int = 30):
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-af", f"astats=metadata=1:reset={sample_rate}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    times, levels = [], []
    current_time = 0.0

    for line in stderr.splitlines():
        line = line.strip()
        if "pts_time:" in line:
            try:
                current_time = float(line.split("pts_time:")[1].split()[0])
            except Exception:
                pass
        if "RMS level dB:" in line:
            try:
                db = float(line.split("RMS level dB:")[1].strip())
                times.append(current_time)
                levels.append(db)
            except Exception:
                pass

    return times, levels


def normalize_levels(levels: list) -> list:
    if not levels:
        return []
    finite = [x for x in levels if math.isfinite(x)]
    if not finite:
        return [0.0] * len(levels)
    mn, mx = min(finite), max(finite)
    if mx == mn:
        return [0.0] * len(levels)
    return [(x - mn) / (mx - mn) if math.isfinite(x) else 0.0 for x in levels]


def smooth_levels(levels: list, window: int = 5) -> list:
    if not levels:
        return []
    half = window // 2
    result = []
    for i in range(len(levels)):
        chunk = levels[max(0, i - half): i + half + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def _detect_beats_ffmpeg(audio_path: str) -> list[float]:
    times, levels = extract_audio_levels(audio_path, sample_rate=28)
    norm = smooth_levels(normalize_levels(levels), window=3)
    if not norm:
        return []

    beats: list[float] = []
    window = 30
    for i in range(2, len(norm) - 2):
        local_slice = norm[max(0, i - window): i + window + 1]
        local_avg = sum(local_slice) / len(local_slice)
        local_threshold = local_avg * 1.16
        cur = norm[i]
        if (
            cur > norm[i - 1]
            and cur > norm[i + 1]
            and cur > local_threshold
            and cur > 0.24
        ):
            beats.append(times[i])

    filtered: list[float] = []
    for t in beats:
        if not filtered or (t - filtered[-1]) >= MIN_BEAT_GAP:
            filtered.append(t)

    return filtered[:MAX_BEATS]


def _detect_bass_ffmpeg(audio_path: str) -> list[float]:
    times, levels = extract_audio_levels(audio_path, sample_rate=32)
    norm = smooth_levels(normalize_levels(levels), window=5)
    if not norm:
        return []

    hits: list[float] = []
    for i in range(4, len(norm) - 4):
        cur = norm[i]
        before = sum(norm[i - 4: i]) / 4
        after  = sum(norm[i: i + 4]) / 4
        attack  = cur - before
        sustain = (cur + after) / 2
        if (
            cur > 0.50
            and attack > 0.10
            and sustain > 0.42
            and cur >= norm[i - 1]
        ):
            if not hits or (times[i] - hits[-1]) >= MIN_BASS_GAP:
                hits.append(times[i])

    return hits[:MAX_BASS_HITS]


def _detect_drop_ffmpeg(audio_path: str, beats: list[float]) -> Optional[float]:
    times, levels = extract_audio_levels(audio_path, sample_rate=14)
    norm = smooth_levels(normalize_levels(levels), window=7)
    if len(norm) < 14:
        return None

    best_score = -999.0
    best_time  = None
    start = max(6, int(len(norm) * 0.15))
    end   = min(len(norm) - 6, int(len(norm) * 0.85))

    for i in range(start, end):
        before = sum(norm[max(0, i - 6): i]) / 6
        after  = sum(norm[i: i + 6]) / 6
        energy_jump = after - before
        t = times[i]
        beats_after = sum(1 for b in beats if t <= b <= t + 1.4)
        score = energy_jump * 2.0 + norm[i] * 0.8 + after * 1.1 + beats_after * 0.14

        if score > best_score:
            best_score = score
            best_time  = t

    return best_time


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def full_analysis(audio_path: str) -> dict:
    """
    Análise completa do áudio.
    Usa librosa se disponível, senão cai para ffmpeg.
    """
    bpm = None

    if LIBROSA_AVAILABLE:
        logger.info("  → [librosa] Carregando áudio…")
        y, sr = _librosa_load(audio_path)

        logger.info("  → [librosa] Detectando beats + BPM…")
        beats, bpm = _detect_beats_librosa(y, sr)

        logger.info("  → [librosa] Detectando bass hits (espectral)…")
        bass_hits = _detect_bass_librosa(y, sr)

        logger.info("  → [librosa] Detectando drop…")
        drop_time = _detect_drop_librosa(y, sr, beats)

        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        avg_energy = float(rms.mean() / (rms.max() + 1e-8))

    else:
        logger.info("  → [ffmpeg] Detectando beats…")
        beats = _detect_beats_ffmpeg(audio_path)

        logger.info("  → [ffmpeg] Detectando bass hits…")
        bass_hits = _detect_bass_ffmpeg(audio_path)

        logger.info("  → [ffmpeg] Detectando drop…")
        drop_time = _detect_drop_ffmpeg(audio_path, beats)

        _, levels = extract_audio_levels(audio_path, sample_rate=10)
        norm = normalize_levels(levels)
        avg_energy = sum(norm) / len(norm) if norm else 0.5

    drop_str = f"{drop_time:.2f}s" if drop_time else "não detectado"
    bpm_str  = f"{bpm:.1f} BPM" if bpm else "N/A"
    logger.info(
        f"  → Beats: {len(beats)} | Bass hits: {len(bass_hits)} | "
        f"Drop: {drop_str} | BPM: {bpm_str}"
    )

    return {
        "beats":      beats,
        "bass_hits":  bass_hits,
        "drop_time":  drop_time,
        "avg_energy": avg_energy,
        "beat_count": len(beats),
        "bpm":        bpm,
    }


def find_best_window(audio_path: str, duration: int, n_candidates: int = 5) -> tuple[float, float]:
    """
    Encontra a janela mais energética e dinâmica do áudio.
    Usa scoring librosa se disponível, senão escolha aleatória inteligente.
    """
    import random

    audio_dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    audio_dur = float(
        subprocess.run(audio_dur_cmd, capture_output=True, text=True, check=True).stdout.strip()
    )

    if audio_dur <= duration:
        return 0.0, float(audio_dur)

    min_start = audio_dur * 0.08
    max_start = min(audio_dur * 0.30, audio_dur - duration)

    if not LIBROSA_AVAILABLE or audio_dur > 600:
        # fallback: escolha aleatória dentro da zona segura
        start = random.uniform(min_start, max(min_start, max_start))
        return round(start, 3), float(duration)

    logger.info("  → Scoring candidatos de janela…")
    y, sr = _librosa_load(audio_path)

    candidates = [
        min_start + (max_start - min_start) * (i / max(1, n_candidates - 1))
        for i in range(n_candidates)
    ]

    best_score = -1.0
    best_start = candidates[0]
    for s in candidates:
        sc = _score_window_librosa(y, sr, s, duration)
        logger.debug(f"    candidato {s:.1f}s → score {sc:.4f}")
        if sc > best_score:
            best_score = sc
            best_start = s

    logger.info(f"  → Melhor janela: {best_start:.1f}s (score={best_score:.4f})")
    return round(best_start, 3), float(duration)


def crop_analysis(analysis: dict, start: float, duration: float) -> dict:
    end = start + duration

    beats = [
        round(t - start, 4)
        for t in analysis["beats"]
        if start <= t <= end
    ]
    bass_hits = [
        round(t - start, 4)
        for t in analysis["bass_hits"]
        if start <= t <= end
    ]

    drop = None
    if analysis["drop_time"] is not None:
        dt = analysis["drop_time"]
        if start <= dt <= end:
            drop = round(dt - start, 4)

    return {
        "beats":      beats[:MAX_BEATS_CROP],
        "bass_hits":  bass_hits[:MAX_BASS_CROP],
        "drop_time":  drop,
        "avg_energy": analysis["avg_energy"],
        "bpm":        analysis.get("bpm"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# FFMPEG EXPRESSION BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_flash_expression(
    analysis: dict,
    base_brightness: float,
    beat_flash: float   = 0.10,
    bass_flash: float   = 0.16,
    drop_flash: float   = 0.24,
    beat_window: float  = 0.050,
    bass_window: float  = 0.065,
) -> str:
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    def make_conds(times: list, window: float) -> list:
        parts = []
        for t in times[:130]:
            s = max(0.0, t - window / 2)
            e = t + window / 2
            parts.append(f"between(t,{s:.3f},{e:.3f})")
        return parts

    beat_conds = make_conds(beats, beat_window)
    bass_conds = make_conds(bass_hits, bass_window)

    expr = str(base_brightness)

    if beat_conds:
        bc = "+".join(beat_conds)
        expr = f"if(gt({bc},0),{beat_flash},{expr})"

    if bass_conds:
        bsc = "+".join(bass_conds)
        expr = f"if(gt({bsc},0),{bass_flash},{expr})"

    if drop_time is not None:
        ds = drop_time - 0.06
        de = drop_time + 0.12
        expr = f"if(between(t,{ds:.3f},{de:.3f}),{drop_flash},{expr})"

    return expr


def build_shake_expression(analysis: dict, base_x: int, base_y: int):
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])

    sx_a, sx_b = base_x * 0.65, base_x * 0.35
    sy_a, sy_b = base_y * 0.65, base_y * 0.35

    shake_x = f"(sin(t*2.7)*{sx_a:.2f}+sin(t*5.3)*{sx_b:.2f})"
    shake_y = f"(cos(t*2.4)*{sy_a:.2f}+cos(t*4.9)*{sy_b:.2f})"

    if bass_hits:
        boosts = [
            f"1.5*between(t,{max(0,t-0.04):.3f},{t+0.18:.3f})"
            for t in bass_hits[:50]
        ]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        drop_mult = f"(1+2.6*between(t,{drop_time-0.04:.3f},{drop_time+0.24:.3f}))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    return shake_x, shake_y


def build_zoom_expression(
    analysis: dict,
    duration: float,
    fps: int,
    max_zoom: float,
    zoom_speed: float,
    pulse_strength: float,
) -> str:
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.45 * fps)

    base  = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength * 0.7}*sin(on*0.07+0.3)*cos(on*0.031))"

    beat_pulse = "0"
    if beats:
        parts = [
            f"0.004*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})"
            for b in beats[:70]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        parts = [
            f"0.009*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+6})"
            for b in bass_hits[:50]
        ]
        bass_pulse = f"({'+'.join(parts)})"

    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"(0.06*between(on,{df-1},{df+4})"
            f"+0.03*between(on,{df+5},{df+18})"
            f"+0.012*between(on,{df+19},{df+32}))"
        )

    full = f"{base}+{drift}+{beat_pulse}+{bass_pulse}+{drop_expr}"
    return (
        f"if(lte(on,{intro_frames}),"
        f"1.0,"
        f"min(max({full},1.0),{max_zoom + 0.08}))"
    )


def save_debug(analysis: dict, output_file: str = "temp/debug_analysis.json") -> None:
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    # converter tipos numpy para python nativo
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(x) for x in obj]
        try:
            return float(obj)
        except (TypeError, ValueError):
            return obj

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(_clean(analysis), f, ensure_ascii=False, indent=2)
    logger.debug(f"Debug salvo em {output_file}")
