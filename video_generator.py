import os
import random
import subprocess
from pathlib import Path

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


def create_short(audio_path, background_path, output_name):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    audio_duration = get_media_duration(audio_path)

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
            "-r", "30",
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
            command = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", background_path,
                "-ss", str(start_time),
                "-i", audio_path,
                "-t", str(short_duration),
                "-vf",
                (
                    "scale=1080:1920,"
                    "zoompan="
                    "z='min(zoom+0.0006,1.12)':"
                    "x='iw/2-(iw/zoom/2)':"
                    "y='ih/2-(ih/zoom/2)':"
                    "d=1:"
                    "s=1080x1920,"
                    "fps=30"
                ),
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
            command = [
                "ffmpeg",
                "-y",
                "-stream_loop", "-1",
                "-i", background_path,
                "-ss", str(start_time),
                "-i", audio_path,
                "-t", str(short_duration),
                "-vf", "scale=1080:1920,fps=30,format=yuv420p",
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
