"""
audio_analysis.py — Análise de áudio profissional
Detecta beats, bass hits, drop, energia e constrói expressões FFmpeg.
"""

import json
import math
import subprocess
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════
# EXTRAÇÃO DE NÍVEIS
# ══════════════════════════════════════════════════════════════════════

def extract_audio_levels(audio_path: str, sample_rate: int = 30):
    """Extrai RMS dBFS ao longo do tempo via ffmpeg astats."""
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


def normalize_levels(levels):
    if not levels:
        return []
    finite = [x for x in levels if math.isfinite(x)]
    if not finite:
        return [0.0] * len(levels)
    mn, mx = min(finite), max(finite)
    if mx == mn:
        return [0.0] * len(levels)
    return [(x - mn) / (mx - mn) if math.isfinite(x) else 0.0 for x in levels]


def smooth_levels(levels, window=5):
    if not levels:
        return []
    half = window // 2
    result = []
    for i in range(len(levels)):
        chunk = levels[max(0, i - half): i + half + 1]
        result.append(sum(chunk) / len(chunk))
    return result


# ══════════════════════════════════════════════════════════════════════
# DETECÇÃO DE BEATS
# ══════════════════════════════════════════════════════════════════════

def detect_beats(audio_path: str):
    """Detecta beats com boa precisão via picos de energia."""
    times, levels = extract_audio_levels(audio_path, sample_rate=28)
    norm = smooth_levels(normalize_levels(levels), window=3)

    beats = []
    for i in range(2, len(norm) - 2):
        cur = norm[i]
        local_avg = (norm[i-2] + norm[i-1] + norm[i+1] + norm[i+2]) / 4
        rise = cur - local_avg

        if (
            cur > norm[i-1]
            and cur > norm[i+1]
            and rise > 0.08
            and cur > 0.38
        ):
            beats.append(times[i])

    # filtra beats muito próximos
    filtered = []
    for t in beats:
        if not filtered or (t - filtered[-1]) >= 0.16:
            filtered.append(t)

    return filtered[:250]


# ══════════════════════════════════════════════════════════════════════
# DETECÇÃO DE BASS HITS
# ══════════════════════════════════════════════════════════════════════

def detect_bass_hits(audio_path: str):
    """Detecta hits de grave/sub-bass com alta precisão."""
    times, levels = extract_audio_levels(audio_path, sample_rate=32)
    norm = smooth_levels(normalize_levels(levels), window=5)

    hits = []
    for i in range(4, len(norm) - 4):
        cur = norm[i]
        before = (norm[i-4] + norm[i-3] + norm[i-2] + norm[i-1]) / 4
        after  = (norm[i+1] + norm[i+2] + norm[i+3] + norm[i+4]) / 4

        rise    = cur - before
        sustain = (cur + after) / 2

        if (
            cur > 0.58
            and rise > 0.14
            and sustain > 0.48
            and cur >= norm[i-1]
            and cur >= norm[i+1]
        ):
            hits.append(times[i])

    filtered = []
    for t in hits:
        if not filtered or (t - filtered[-1]) >= 0.25:
            filtered.append(t)

    return filtered[:160]


# ══════════════════════════════════════════════════════════════════════
# DETECÇÃO DE DROP / CLÍMAX
# ══════════════════════════════════════════════════════════════════════

def detect_drop(audio_path: str):
    """Detecta o ponto de maior impacto/drop da música."""
    times, levels = extract_audio_levels(audio_path, sample_rate=14)
    norm = smooth_levels(normalize_levels(levels), window=7)

    if len(norm) < 14:
        return None

    best_score = -999.0
    best_time  = None

    start = max(5, int(len(norm) * 0.12))
    end   = min(len(norm) - 5, int(len(norm) * 0.88))

    for i in range(start, end):
        before = sum(norm[i-5:i])   / 5
        after  = sum(norm[i:i+5])   / 5
        jump   = after - before
        score  = jump * 1.5 + norm[i] * 0.5 + after * 0.7
        if score > best_score:
            best_score = score
            best_time  = times[i]

    return best_time


# ══════════════════════════════════════════════════════════════════════
# ANÁLISE COMPLETA
# ══════════════════════════════════════════════════════════════════════

def full_analysis(audio_path: str):
    """Retorna dict com beats, bass_hits, drop_time e energia média."""
    beats     = detect_beats(audio_path)
    bass_hits = detect_bass_hits(audio_path)
    drop_time = detect_drop(audio_path)

    _, levels  = extract_audio_levels(audio_path, sample_rate=10)
    norm       = normalize_levels(levels)
    avg_energy = sum(norm) / len(norm) if norm else 0.5

    return {
        "beats":      beats,
        "bass_hits":  bass_hits,
        "drop_time":  drop_time,
        "avg_energy": avg_energy,
        "beat_count": len(beats),
    }


def crop_analysis(analysis: dict, start: float, duration: float):
    """Recorta análise para a janela do short."""
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
        "beats":     beats[:100],
        "bass_hits": bass_hits[:80],
        "drop_time": drop,
        "avg_energy": analysis["avg_energy"],
    }


# ══════════════════════════════════════════════════════════════════════
# EXPRESSÕES FFMPEG
# ══════════════════════════════════════════════════════════════════════

def build_flash_expression(
    analysis: dict,
    base_brightness: float,
    beat_flash: float  = 0.18,
    bass_flash: float  = 0.24,
    drop_flash: float  = 0.38,
    beat_window: float = 0.055,
    bass_window: float = 0.065,
):
    """
    Constrói expressão FFmpeg para flash sincronizado.
    Prioridade: drop > bass hit > beat > base.
    """
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    def time_conds(times, window):
        parts = []
        for t in times[:120]:
            s = max(0.0, t - window / 2)
            e = t + window / 2
            parts.append(f"between(t,{s:.3f},{e:.3f})")
        return parts

    beat_conds = time_conds(beats, beat_window)
    bass_conds = time_conds(bass_hits, bass_window)

    expr = str(base_brightness)

    # camada beat
    if beat_conds:
        bc = "+".join(beat_conds)
        expr = f"if(gt({bc},0),{beat_flash},{expr})"

    # camada bass (sobrescreve beat)
    if bass_conds:
        bsc = "+".join(bass_conds)
        expr = f"if(gt({bsc},0),{bass_flash},{expr})"

    # camada drop (maior prioridade)
    if drop_time is not None:
        ds = drop_time - 0.10
        de = drop_time + 0.12
        expr = f"if(between(t,{ds:.3f},{de:.3f}),{drop_flash},{expr})"

    return expr


def build_shake_expression(analysis: dict, base_x: int, base_y: int):
    """Expressão de shake proporcional ao impacto."""
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])

    shake_x = f"sin(t*2.6)*{base_x}"
    shake_y = f"cos(t*2.3)*{base_y}"

    if bass_hits:
        boosts = []
        for t in bass_hits[:40]:
            boosts.append(f"1.8*between(t,{t-0.04:.3f},{t+0.18:.3f})")
        boost_expr = "(1+" + "+".join(boosts) + ")"
        shake_x = f"sin(t*2.6)*{base_x}*{boost_expr}"
        shake_y = f"cos(t*2.3)*{base_y}*{boost_expr}"

    if drop_time is not None:
        drop_boost = f"(1+3.0*between(t,{drop_time-0.05:.3f},{drop_time+0.30:.3f}))"
        shake_x = f"({shake_x})*{drop_boost}"
        shake_y = f"({shake_y})*{drop_boost}"

    return shake_x, shake_y


def build_zoom_expression(
    analysis: dict,
    duration: float,
    fps: int,
    max_zoom: float,
    zoom_speed: float,
    pulse_strength: float,
):
    """
    Zoom orgânico que pulsa com beats e explode no drop.
    Intro hold de 0.6s para não começar tonta.
    """
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames   = max(1, int(duration * fps))
    intro_frames   = int(0.6 * fps)

    # base: zoom suave que entra e volta (seno)
    base = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"

    # respiração sutil
    breathing = f"({pulse_strength}*sin(on*0.04))"

    # pulsos em beats (pequenos)
    beat_pulse = "0"
    if beats:
        parts = [f"0.004*between(on,{int(b*fps)-1},{int(b*fps)+3})" for b in beats[:50]]
        beat_pulse = f"({'+'.join(parts)})"

    # pulsos em bass (médios)
    bass_pulse = "0"
    if bass_hits:
        parts = [f"0.010*between(on,{int(b*fps)-1},{int(b*fps)+5})" for b in bass_hits[:40]]
        bass_pulse = f"({'+'.join(parts)})"

    # explosão no drop
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"(0.04*between(on,{df-2},{df+3})"
            f"+0.07*between(on,{df+4},{df+12}))"
        )

    full_expr = f"{base}+{breathing}+{beat_pulse}+{bass_pulse}+{drop_expr}"

    return (
        f"if(lte(on,{intro_frames}),"
        f"1.0,"
        f"min(max({full_expr},1.0),{max_zoom}))"
    )


# ══════════════════════════════════════════════════════════════════════
# DEBUG
# ══════════════════════════════════════════════════════════════════════

def save_debug(analysis: dict, output_file="temp/debug_analysis.json"):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
