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


def detect_beats(audio_path: str):
    """
    Beat sync simples:
    detecta picos de energia relativos.
    Retorna lista de tempos em segundos.
    """
    times, levels = extract_audio_levels(audio_path, sample_rate=20)
    norm = normalize_levels(levels)

    if len(norm) < 5:
        return []

    beats = []

    for i in range(2, len(norm) - 2):
        current = norm[i]
        left = norm[i - 1]
        right = norm[i + 1]

        local_avg = (norm[i - 2] + norm[i - 1] + norm[i + 1] + norm[i + 2]) / 4

        if current > left and current > right and current > local_avg + 0.12 and current > 0.45:
            beats.append(times[i])

    filtered = []
    min_gap = 0.22  # evita batida duplicada muito próxima

    for t in beats:
        if not filtered or (t - filtered[-1]) >= min_gap:
            filtered.append(t)

    return filtered


def detect_drop(audio_path: str):
    """
    Detecta o 'drop' aproximado como o ponto com maior salto de energia.
    Retorna tempo em segundos ou None.
    """
    times, levels = extract_audio_levels(audio_path, sample_rate=10)
    norm = normalize_levels(levels)

    if len(norm) < 8:
        return None

    best_score = -999
    best_time = None

    window_before = 3
    window_after = 3

    for i in range(window_before, len(norm) - window_after):
        before_avg = sum(norm[i - window_before:i]) / window_before
        after_avg = sum(norm[i:i + window_after]) / window_after

        jump = after_avg - before_avg
        score = jump + after_avg * 0.4

        if score > best_score:
            best_score = score
            best_time = times[i]

    return best_time


def build_flash_expression(beat_times, normal_brightness, beat_flash=0.22, beat_window=0.08, drop_time=None, drop_flash=0.38):
    """
    Gera expressão de brightness para ffmpeg.
    """
    conditions = []

    for t in beat_times[:120]:  # limite de segurança
        start = max(0, t - beat_window / 2)
        end = t + beat_window / 2
        conditions.append(f"between(t,{start:.3f},{end:.3f})")

    expr = f"{normal_brightness}"

    if conditions:
        beat_cond = "+".join(conditions)
        expr = f"if(gt({beat_cond},0),{beat_flash},{normal_brightness})"

    if drop_time is not None:
        drop_start = max(0, drop_time - 0.18)
        drop_end = drop_time + 0.25
        expr = f"if(between(t,{drop_start:.3f},{drop_end:.3f}),{drop_flash},{expr})"

    return expr


def build_shake_multiplier_expression(drop_time=None):
    """
    Multiplicador maior perto do drop.
    """
    if drop_time is None:
        return "1.0"

    drop_start = max(0, drop_time - 0.18)
    drop_end = drop_time + 0.30
    return f"if(between(t,{drop_start:.3f},{drop_end:.3f}),1.8,1.0)"


def save_debug_analysis(audio_path: str, beats, drop_time, output_file="temp/audio_analysis_debug.json"):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "audio_path": audio_path,
            "beats": beats,
            "drop_time": drop_time
        }, f, ensure_ascii=False, indent=2)
