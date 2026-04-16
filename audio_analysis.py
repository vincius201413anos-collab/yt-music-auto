import json
import math
import subprocess
from pathlib import Path


def extract_audio_levels(audio_path: str, sample_rate: int = 24):
    """
    Extrai nível RMS ao longo do tempo usando ffmpeg astats.
    sample_rate=24 => ~24 medições por segundo
    """
    command = [
        "ffmpeg",
        "-i", audio_path,
        "-af", f"astats=metadata=1:reset={sample_rate}",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    stderr = result.stderr

    times = []
    levels = []
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
        return [0.0 for _ in levels]

    min_l = min(finite)
    max_l = max(finite)

    if max_l == min_l:
        return [0.0 for _ in levels]

    return [
        (x - min_l) / (max_l - min_l) if math.isfinite(x) else 0.0
        for x in levels
    ]


def smooth_levels(levels, window=4):
    if not levels:
        return []

    smoothed = []
    half = window // 2

    for i in range(len(levels)):
        start = max(0, i - half)
        end = min(len(levels), i + half + 1)
        chunk = levels[start:end]
        smoothed.append(sum(chunk) / len(chunk))

    return smoothed


def detect_peaks(times, levels, threshold, min_level, min_gap):
    if len(levels) < 5:
        return []

    peaks = []

    for i in range(2, len(levels) - 2):
        current = levels[i]
        local_avg = (
            levels[i - 2] + levels[i - 1] +
            levels[i + 1] + levels[i + 2]
        ) / 4

        rise = current - local_avg

        if (
            current > levels[i - 1]
            and current > levels[i + 1]
            and rise > threshold
            and current > min_level
        ):
            peaks.append(times[i])

    filtered = []
    for t in peaks:
        if not filtered or (t - filtered[-1]) >= min_gap:
            filtered.append(t)

    return filtered


def detect_beats(audio_path: str):
    times, levels = extract_audio_levels(audio_path, sample_rate=26)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, 3)

    beats = detect_peaks(
        times,
        norm,
        threshold=0.09,
        min_level=0.40,
        min_gap=0.18
    )

    return beats[:200]


def detect_bass_hits(audio_path: str):
    times, levels = extract_audio_levels(audio_path, sample_rate=30)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, 5)

    hits = []

    for i in range(3, len(norm) - 3):
        current = norm[i]

        before = (norm[i - 3] + norm[i - 2] + norm[i - 1]) / 3
        after = (norm[i + 1] + norm[i + 2] + norm[i + 3]) / 3

        rise = current - before
        sustain = (current + after) / 2

        if (
            current > 0.60
            and rise > 0.16
            and sustain > 0.52
            and current >= norm[i - 1]
            and current >= norm[i + 1]
        ):
            hits.append(times[i])

    filtered = []
    for t in hits:
        if not filtered or (t - filtered[-1]) >= 0.30:
            filtered.append(t)

    return filtered[:140]


def detect_drop(audio_path: str):
    times, levels = extract_audio_levels(audio_path, sample_rate=14)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, 6)

    if len(norm) < 12:
        return None

    best_score = -999.0
    best_time = None

    start = max(4, int(len(norm) * 0.15))
    end = min(len(norm) - 4, int(len(norm) * 0.85))

    for i in range(start, end):
        before = sum(norm[i - 4:i]) / 4
        after = sum(norm[i:i + 4]) / 4

        jump = after - before
        score = (jump * 1.4) + (norm[i] * 0.4) + (after * 0.6)

        if score > best_score:
            best_score = score
            best_time = times[i]

    return best_time


def build_flash_expression(
    beat_times,
    normal_brightness,
    beat_flash=0.16,
    beat_window=0.05,
    drop_time=None,
    drop_flash=0.30
):
    conditions = []

    for t in beat_times[:180]:
        start = max(0, t - beat_window / 2)
        end = t + beat_window / 2
        conditions.append(f"between(t,{start:.3f},{end:.3f})")

    expr = f"{normal_brightness}"

    if conditions:
        beat_cond = "+".join(conditions)
        expr = f"if(gt({beat_cond},0),{beat_flash},{normal_brightness})"

    if drop_time is not None:
        expr = (
            f"if(between(t,{drop_time-0.08:.3f},{drop_time+0.08:.3f}),"
            f"{drop_flash},{expr})"
        )

    return expr


def build_shake_multiplier_expression(drop_time=None):
    if drop_time is None:
        return "1.0"

    return (
        f"if(between(t,{drop_time-0.05:.3f},{drop_time+0.25:.3f}),2.0,"
        f"if(between(t,{drop_time-0.20:.3f},{drop_time-0.05:.3f}),1.4,1.0))"
    )


def save_debug_analysis(
    audio_path: str,
    beats,
    drop_time,
    output_file="temp/audio_analysis_debug.json",
    bass_hits=None
):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "audio_path": audio_path,
            "beats": beats,
            "bass_hits": bass_hits or [],
            "drop_time": drop_time
        }, f, ensure_ascii=False, indent=2)
