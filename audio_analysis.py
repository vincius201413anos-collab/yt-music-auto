import json
import math
import subprocess
from pathlib import Path


def extract_audio_levels(audio_path: str, sample_rate: int = 20):
    """
    Extrai nível de volume ao longo do tempo usando ffmpeg astats.
    sample_rate=20 => ~20 medições por segundo
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

    finite_levels = [x for x in levels if math.isfinite(x)]
    if not finite_levels:
        return [0.0 for _ in levels]

    min_level = min(finite_levels)
    max_level = max(finite_levels)

    if max_level == min_level:
        return [0.0 for _ in levels]

    normalized = []
    for x in levels:
        if not math.isfinite(x):
            normalized.append(0.0)
        else:
            normalized.append((x - min_level) / (max_level - min_level))

    return normalized


def smooth_levels(levels, window_size=3):
    if not levels:
        return []

    window_size = max(1, int(window_size))
    half = window_size // 2
    smoothed = []

    for i in range(len(levels)):
        start = max(0, i - half)
        end = min(len(levels), i + half + 1)
        chunk = levels[start:end]
        smoothed.append(sum(chunk) / len(chunk))

    return smoothed


def detect_peaks(times, levels, threshold=0.12, min_level=0.45, min_gap=0.22):
    """
    Detecta picos locais de energia com filtragem simples.
    """
    if len(levels) < 5:
        return []

    peaks = []

    for i in range(2, len(levels) - 2):
        current = levels[i]
        left = levels[i - 1]
        right = levels[i + 1]

        local_avg = (levels[i - 2] + levels[i - 1] + levels[i + 1] + levels[i + 2]) / 4
        rise = current - local_avg

        if (
            current > left
            and current > right
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
    """
    Detecta batidas principais.
    Uso:
    - flash leve
    - micro pulse
    - sync visual
    """
    times, levels = extract_audio_levels(audio_path, sample_rate=24)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, window_size=3)

    if len(norm) < 5:
        return []

    beats = detect_peaks(
        times=times,
        levels=norm,
        threshold=0.10,
        min_level=0.42,
        min_gap=0.20
    )

    return beats[:180]


def detect_bass_hits(audio_path: str):
    """
    Detecta impactos mais fortes de grave.
    Aqui a lógica é mais seletiva que beat normal.
    """
    times, levels = extract_audio_levels(audio_path, sample_rate=28)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, window_size=5)

    if len(norm) < 7:
        return []

    bass_hits = []

    for i in range(3, len(norm) - 3):
        current = norm[i]
        local_before = (norm[i - 3] + norm[i - 2] + norm[i - 1]) / 3
        local_after = (norm[i + 1] + norm[i + 2] + norm[i + 3]) / 3

        rise = current - local_before
        sustain = (current + local_after) / 2

        if (
            current > 0.58
            and rise > 0.14
            and sustain > 0.50
            and current >= norm[i - 1]
            and current >= norm[i + 1]
        ):
            bass_hits.append(times[i])

    filtered = []
    min_gap = 0.28

    for t in bass_hits:
        if not filtered or (t - filtered[-1]) >= min_gap:
            filtered.append(t)

    return filtered[:120]


def detect_drop(audio_path: str):
    """
    Detecta o drop aproximado como o ponto com maior salto de energia.
    Melhorado para:
    - ignorar começo demais
    - ignorar final demais
    - procurar subida forte + energia sustentada
    """
    times, levels = extract_audio_levels(audio_path, sample_rate=14)
    norm = normalize_levels(levels)
    norm = smooth_levels(norm, window_size=5)

    if len(norm) < 12:
        return None

    best_score = -999.0
    best_time = None

    window_before = 4
    window_after = 4

    start_index = max(window_before, int(len(norm) * 0.12))
    end_index = min(len(norm) - window_after, int(len(norm) * 0.88))

    for i in range(start_index, end_index):
        before_avg = sum(norm[i - window_before:i]) / window_before
        after_avg = sum(norm[i:i + window_after]) / window_after

        jump = after_avg - before_avg
        peak_weight = norm[i]
        sustain_weight = after_avg

        score = (jump * 1.25) + (peak_weight * 0.35) + (sustain_weight * 0.45)

        if score > best_score:
            best_score = score
            best_time = times[i]

    return best_time


def build_flash_expression(
    beat_times,
    normal_brightness,
    beat_flash=0.18,
    beat_window=0.06,
    drop_time=None,
    drop_flash=0.28
):
    """
    Gera expressão de brightness para ffmpeg.
    Melhorado para:
    - flash mais controlado
    - mais natural
    - drop com impacto maior
    """
    conditions = []

    for t in beat_times[:160]:
        start = max(0, t - beat_window / 2)
        end = t + beat_window / 2
        conditions.append(f"between(t,{start:.3f},{end:.3f})")

    expr = f"{normal_brightness}"

    if conditions:
        beat_cond = "+".join(conditions)
        expr = (
            f"if(gt({beat_cond},0),"
            f"{beat_flash},"
            f"{normal_brightness})"
        )

    if drop_time is not None:
        drop_start_1 = max(0, drop_time - 0.10)
        drop_end_1 = drop_time + 0.06

        drop_start_2 = max(0, drop_time + 0.06)
        drop_end_2 = drop_time + 0.24

        expr = (
            f"if(between(t,{drop_start_1:.3f},{drop_end_1:.3f}),{drop_flash},"
            f"if(between(t,{drop_start_2:.3f},{drop_end_2:.3f}),{drop_flash * 0.72:.3f},{expr}))"
        )

    return expr


def build_shake_multiplier_expression(drop_time=None):
    """
    Multiplicador maior perto do drop.
    Melhorado com duas fases:
    - pré-impacto
    - impacto principal
    """
    if drop_time is None:
        return "1.0"

    pre_start = max(0, drop_time - 0.18)
    pre_end = drop_time - 0.02

    hit_start = max(0, drop_time - 0.02)
    hit_end = drop_time + 0.22

    return (
        f"if(between(t,{hit_start:.3f},{hit_end:.3f}),1.9,"
        f"if(between(t,{pre_start:.3f},{pre_end:.3f}),1.35,1.0))"
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
