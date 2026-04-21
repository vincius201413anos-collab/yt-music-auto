"""
audio_analysis.py — Audio engine calibrado para Shorts musicais.

Mantém:
- beat detection adaptativo
- bass hits
- drop detection
- expressões FFmpeg
"""

import json
import math
import subprocess
from pathlib import Path


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


def detect_beats(audio_path: str) -> list:
    times, levels = extract_audio_levels(audio_path, sample_rate=28)
    norm = smooth_levels(normalize_levels(levels), window=3)

    if not norm:
        return []

    beats = []
    window = 30

    for i in range(2, len(norm) - 2):
        local_slice = norm[max(0, i - window): i + window + 1]
        local_avg = sum(local_slice) / len(local_slice)
        local_threshold = local_avg * 1.16

        cur = norm[i]
        is_peak = (
            cur > norm[i - 1]
            and cur > norm[i + 1]
            and cur > local_threshold
            and cur > 0.24
        )

        if is_peak:
            beats.append(times[i])

    filtered = []
    for t in beats:
        if not filtered or (t - filtered[-1]) >= 0.16:
            filtered.append(t)

    return filtered[:260]


def detect_bass_hits(audio_path: str) -> list:
    times, levels = extract_audio_levels(audio_path, sample_rate=32)
    norm = smooth_levels(normalize_levels(levels), window=5)

    if not norm:
        return []

    hits = []
    for i in range(4, len(norm) - 4):
        cur = norm[i]
        before = sum(norm[i - 4: i]) / 4
        after = sum(norm[i: i + 4]) / 4
        attack = cur - before
        sustain = (cur + after) / 2

        if (
            cur > 0.50
            and attack > 0.10
            and sustain > 0.42
            and cur >= norm[i - 1]
        ):
            hits.append(times[i])

    filtered = []
    for t in hits:
        if not filtered or (t - filtered[-1]) >= 0.22:
            filtered.append(t)

    return filtered[:160]


def detect_drop(audio_path: str) -> float | None:
    times, levels = extract_audio_levels(audio_path, sample_rate=14)
    norm = smooth_levels(normalize_levels(levels), window=7)

    if len(norm) < 14:
        return None

    beats = detect_beats(audio_path)

    best_score = -999.0
    best_time = None

    start = max(6, int(len(norm) * 0.15))
    end = min(len(norm) - 6, int(len(norm) * 0.85))

    for i in range(start, end):
        before = sum(norm[max(0, i - 6): i]) / 6
        after = sum(norm[i: i + 6]) / 6
        energy_jump = after - before

        t_point = times[i]
        beats_after = sum(1 for b in beats if t_point <= b <= t_point + 1.4)

        score = (
            energy_jump * 2.0
            + norm[i] * 0.8
            + after * 1.1
            + beats_after * 0.14
        )

        if score > best_score:
            best_score = score
            best_time = times[i]

    return best_time


def full_analysis(audio_path: str) -> dict:
    print("    → Detectando beats…")
    beats = detect_beats(audio_path)

    print("    → Detectando bass hits…")
    bass_hits = detect_bass_hits(audio_path)

    print("    → Detectando drop…")
    drop_time = detect_drop(audio_path)

    _, levels = extract_audio_levels(audio_path, sample_rate=10)
    norm = normalize_levels(levels)
    avg_energy = sum(norm) / len(norm) if norm else 0.5

    print(
        f"    → Beats: {len(beats)} | Bass hits: {len(bass_hits)} | Drop: {drop_time:.2f}s"
        if drop_time else
        f"    → Beats: {len(beats)} | Bass hits: {len(bass_hits)} | Drop: não detectado"
    )

    return {
        "beats": beats,
        "bass_hits": bass_hits,
        "drop_time": drop_time,
        "avg_energy": avg_energy,
        "beat_count": len(beats),
    }


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
        "beats": beats[:120],
        "bass_hits": bass_hits[:90],
        "drop_time": drop,
        "avg_energy": analysis["avg_energy"],
    }


def build_flash_expression(
    analysis: dict,
    base_brightness: float,
    beat_flash: float = 0.10,
    bass_flash: float = 0.16,
    drop_flash: float = 0.24,
    beat_window: float = 0.050,
    bass_window: float = 0.065,
) -> str:
    beats = analysis.get("beats", [])
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
        boosts = [f"1.5*between(t,{max(0,t-0.04):.3f},{t+0.18:.3f})" for t in bass_hits[:50]]
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
    beats = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.45 * fps)

    base = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength * 0.7}*sin(on*0.07+0.3)*cos(on*0.031))"

    beat_pulse = "0"
    if beats:
        parts = [f"0.004*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})" for b in beats[:70]]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        parts = [f"0.009*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+6})" for b in bass_hits[:50]]
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


def save_debug(analysis: dict, output_file: str = "temp/debug_analysis.json"):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
