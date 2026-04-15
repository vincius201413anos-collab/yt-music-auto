import os
import random
import subprocess
from pathlib import Path

from edit_profiles import EDIT_PROFILES
from audio_analysis import (
    detect_beats,
    detect_drop,
    build_flash_expression,
    build_shake_multiplier_expression,
)

OUTPUT_FOLDER = "output"
MIN_SHORT_DURATION = 40
MAX_SHORT_DURATION = 70
FALLBACK_BACKGROUND = "__AUTO_BLACK__"


def get_media_duration(file_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def pick_short_window(audio_duration):
    if audio_duration <= MIN_SHORT_DURATION:
        return 0, int(audio_duration)

    duration = random.randint(
        MIN_SHORT_DURATION,
        min(MAX_SHORT_DURATION, int(audio_duration))
    )

    start = random.randint(0, int(audio_duration - duration))
    return start, duration


def get_profile(style):
    default = EDIT_PROFILES.get("default", {})
    raw = EDIT_PROFILES.get(style, default)

    return {**default, **raw}


def crop_analysis(beat_times, drop_time, start, duration):
    end = start + duration

    beats = [t - start for t in beat_times if start <= t <= end]
    drop = (drop_time - start) if (drop_time and start <= drop_time <= end) else None

    return beats[:80], drop  # 🔥 limite evita travar ffmpeg


def create_short(audio_path, background_path, output_name, style):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    profile = get_profile(style)
    audio_duration = get_media_duration(audio_path)

    start, duration = pick_short_window(audio_duration)

    # 🔥 ANALISE DE ÁUDIO
    beats_full = detect_beats(audio_path)
    drop_full = detect_drop(audio_path)

    beats, drop = crop_analysis(beats_full, drop_full, start, duration)

    flash_expr = build_flash_expression(
        beat_times=beats,
        normal_brightness=profile["brightness"],
        beat_flash=profile["flash_strength"],
        beat_window=0.07,
        drop_time=drop,
        drop_flash=max(profile["flash_strength"] + 0.15, 0.35)
    )

    shake_expr = build_shake_multiplier_expression(drop)

    ext = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    # 🔥 BASE FILTERS
    if is_image:
        vf = (
            "scale=1400:2488:force_original_aspect_ratio=increase,"
            f"zoompan=z='1+{profile['zoom_speed']}*on+{profile['pulse_strength']}*sin(on/6)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920,"
            f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
            f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
            f"fps={profile['fps']}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]

    elif is_video:
        video_duration = get_media_duration(background_path)
        bg_start = 0 if video_duration <= duration else random.uniform(0, video_duration - duration)

        vf = (
            "scale=1120:1992:force_original_aspect_ratio=increase,"
            f"crop=1080:1920:x='20+sin(t*7)*{profile['shake_x']}*({shake_expr})':"
            f"y='20+cos(t*6)*{profile['shake_y']}*({shake_expr})',"
            f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
            f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
            f"fps={profile['fps']}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]

    else:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]

    subprocess.run(cmd, check=True)
    return output_path
