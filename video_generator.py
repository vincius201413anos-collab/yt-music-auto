import os
import random
import subprocess

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


def build_ffmpeg_command(audio_path, background_path, output_path, start_time, short_duration):
    if background_path == FALLBACK_BACKGROUND:
        return [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={short_duration}",
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration),
            "-shortest",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    if background_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", background_path,
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration),
            "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0008,1.08)':d=1:s=1080x1920",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    return [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", background_path,
        "-ss", str(start_time),
        "-i", audio_path,
        "-t", str(short_duration),
        "-vf", "scale=1080:1920,format=yuv420p",
        "-shortest",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]


def pick_non_repeating_segments(audio_duration, count=3):
    segments = []

    usable_max_duration = min(MAX_SHORT_DURATION, int(audio_duration))
    usable_min_duration = min(MIN_SHORT_DURATION, usable_max_duration)

    if usable_max_duration <= 1:
        return [(0, max(1, int(audio_duration)))]

    attempts = 0
    max_attempts = 200

    while len(segments) < count and attempts < max_attempts:
        attempts += 1

        short_duration = random.randint(usable_min_duration, usable_max_duration)
        max_start = max(0, int(audio_duration - short_duration))
        start_time = random.randint(0, max_start) if max_start > 0 else 0
        end_time = start_time + short_duration

        overlaps = False
        for existing_start, existing_duration in segments:
            existing_end = existing_start + existing_duration

            # margem de segurança de 3 segundos
            if not (end_time <= existing_start + 3 or start_time >= existing_end - 3):
                overlaps = True
                break

        if not overlaps:
            segments.append((start_time, short_duration))

    # fallback se não conseguir 3 segmentos totalmente separados
    if len(segments) < count:
        segment_size = max(usable_min_duration, min(usable_max_duration, int(audio_duration / max(count, 1))))
        max_start = max(0, int(audio_duration - segment_size))

        if count == 1:
            starts = [0]
        else:
            starts = []
            for i in range(count):
                if max_start == 0:
                    starts.append(0)
                else:
                    starts.append(int((max_start * i) / max(count - 1, 1)))

        segments = []
        for start in starts[:count]:
            duration = min(segment_size, int(audio_duration - start))
            if duration > 0:
                segments.append((start, duration))

    return segments[:count]


def create_short(audio_path, background_path, output_name, start_time=None, short_duration=None):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    audio_duration = get_media_duration(audio_path)

    if start_time is None or short_duration is None:
        if audio_duration <= MIN_SHORT_DURATION:
            short_duration = max(1, int(audio_duration))
            start_time = 0
        else:
            short_duration = random.randint(MIN_SHORT_DURATION, min(MAX_SHORT_DURATION, int(audio_duration)))
            max_start = max(0, int(audio_duration - short_duration))
            start_time = random.randint(0, max_start) if max_start > 0 else 0

    command = build_ffmpeg_command(
        audio_path=audio_path,
        background_path=background_path,
        output_path=output_path,
        start_time=start_time,
        short_duration=short_duration
    )

    subprocess.run(command, check=True)
    return output_path


def create_three_shorts(audio_path, background_path, base_output_name):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    audio_duration = get_media_duration(audio_path)
    segments = pick_non_repeating_segments(audio_duration, count=3)

    created_files = []

    base_name, ext = os.path.splitext(base_output_name)
    if not ext:
        ext = ".mp4"

    for i, (start_time, short_duration) in enumerate(segments, start=1):
        output_name = f"{base_name}_{i}{ext}"
        output_path = create_short(
            audio_path=audio_path,
            background_path=background_path,
            output_name=output_name,
            start_time=start_time,
            short_duration=short_duration
        )
        created_files.append(output_path)

    return created_files
