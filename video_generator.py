import os
import random
import subprocess
from pathlib import Path

from edit_profiles import EDIT_PROFILES

OUTPUT_FOLDER = "output"
MIN_SHORT_DURATION = 25
MAX_SHORT_DURATION = 35
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
        short_duration = max(1, int(audio_duration))
        start_time = 0
    else:
        short_duration = random.randint(
            MIN_SHORT_DURATION,
            min(MAX_SHORT_DURATION, int(audio_duration))
        )
        max_start = max(0, int(audio_duration - short_duration))
        start_time = random.randint(0, max_start) if max_start > 0 else 0

    return start_time, short_duration


def get_profile(style):
    default_profile = {
        "zoom_speed": 0.0015,
        "max_zoom": 1.12,
        "brightness": 0.00,
        "contrast": 1.08,
        "saturation": 1.08,
        "blur": 0,
        "fps": 30,
    }

    raw = EDIT_PROFILES.get(style, EDIT_PROFILES.get("default", {}))

    profile = {
        "zoom_speed": raw.get("zoom_speed", raw.get("zoom", default_profile["zoom_speed"])),
        "max_zoom": raw.get("max_zoom", default_profile["max_zoom"]),
        "brightness": raw.get("brightness", default_profile["brightness"]),
        "contrast": raw.get("contrast", default_profile["contrast"]),
        "saturation": raw.get("saturation", default_profile["saturation"]),
        "blur": raw.get("blur", default_profile["blur"]),
        "fps": raw.get("fps", default_profile["fps"]),
    }

    return profile


def build_image_filter(profile):
    zoom_speed = profile["zoom_speed"]
    max_zoom = profile["max_zoom"]
    brightness = profile["brightness"]
    contrast = profile["contrast"]
    saturation = profile["saturation"]
    blur = profile["blur"]
    fps = profile["fps"]

    filters = [
        "scale=1200:2133:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        (
            "zoompan="
            f"z='min(pzoom+{zoom_speed},{max_zoom})':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920"
        ),
        f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}",
    ]

    if blur and blur > 0:
        filters.append(f"gblur=sigma={blur}")

    filters.extend([
        f"fps={fps}",
        "format=yuv420p"
    ])

    return ",".join(filters)


def build_video_filter(profile):
    brightness = profile["brightness"]
    contrast = profile["contrast"]
    saturation = profile["saturation"]
    blur = profile["blur"]
    fps = profile["fps"]

    filters = [
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}",
    ]

    if blur and blur > 0:
        filters.append(f"gblur=sigma={blur}")

    filters.extend([
        f"fps={fps}",
        "format=yuv420p"
    ])

    return ",".join(filters)


def create_short(audio_path, background_path, output_name, style):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    profile = get_profile(style)
    audio_duration = get_media_duration(audio_path)
    start_time, short_duration = pick_short_window(audio_duration)

    if background_path == FALLBACK_BACKGROUND:
        command = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={short_duration}",
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration),
            "-shortest",
            "-r", str(profile["fps"]),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
    else:
        ext = Path(background_path).suffix.lower()

        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            vf = build_image_filter(profile)

            command = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", background_path,
                "-ss", str(start_time),
                "-i", audio_path,
                "-t", str(short_duration),
                "-vf", vf,
                "-shortest",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        else:
            vf = build_video_filter(profile)

            command = [
                "ffmpeg",
                "-y",
                "-stream_loop", "-1",
                "-i", background_path,
                "-ss", str(start_time),
                "-i", audio_path,
                "-t", str(short_duration),
                "-vf", vf,
                "-shortest",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]

    subprocess.run(command, check=True)
    return output_path
