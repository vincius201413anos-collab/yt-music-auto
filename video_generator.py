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

VIDEO_FADE_IN = 0.6
VIDEO_FADE_OUT = 0.8
AUDIO_FADE_IN = 0.6
AUDIO_FADE_OUT = 1.0


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
    return beats[:60], drop


def build_audio_filter(duration):
    fade_out_start = max(0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fade_out_start}:d={AUDIO_FADE_OUT}"
    )


def build_image_zoom_expr(duration, fps, beat_times):
    """
    Zoom cinematográfico:
    - começa normal
    - aproxima devagar
    - chega no máximo no meio
    - volta devagar até o fim
    - pequenos bumps no beat (bem sutis)
    """
    total_frames = max(1, int(duration * fps))

    # curva suave: 0 -> 1 -> 0
    base_expr = (
        f"(1.00 + 0.055*(0.5 - 0.5*cos(2*PI*on/{total_frames})))"
    )

    # bumps bem leves no beat, pra não dar tontura
    beat_terms = []
    for bt in beat_times[:30]:
        start_f = max(0, int((bt - 0.04) * fps))
        end_f = max(start_f + 1, int((bt + 0.10) * fps))
        beat_terms.append(f"0.006*between(on,{start_f},{end_f})")

    if beat_terms:
        return f"{base_expr}+({' + '.join(beat_terms)})"

    return base_expr


def build_image_filter(profile, flash_expr, duration, beat_times):
    fade_out_start_video = max(0, duration - VIDEO_FADE_OUT)
    fps = profile["fps"]

    zoom_expr = build_image_zoom_expr(duration, fps, beat_times)

    return (
        "scale=1400:2488:force_original_aspect_ratio=increase,"
        "crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
        "zoompan="
        f"z='min(max({zoom_expr},1.0),1.08)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920,"
        "eq=contrast=1.14:brightness=0.02:saturation=1.06,"
        f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out_start_video}:d={VIDEO_FADE_OUT},"
        f"fps={fps}"
    )


def build_video_filter(profile, flash_expr, shake_expr, duration):
    fade_out_start_video = max(0, duration - VIDEO_FADE_OUT)

    # shake bem mais controlado pra não dar tontura
    shake_x = min(profile.get("shake_x", 3), 4)
    shake_y = min(profile.get("shake_y", 3), 4)

    return (
        "scale=1140:2026:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:"
        f"x='max(0,min(iw-1080,8+sin(t*2.3)*{shake_x}*({shake_expr})))':"
        f"y='max(0,min(ih-1920,10+cos(t*2.0)*{shake_y}*({shake_expr})))',"
        "eq=contrast=1.14:brightness=0.02:saturation=1.06,"
        f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out_start_video}:d={VIDEO_FADE_OUT},"
        f"fps={profile['fps']}"
    )


def create_short(audio_path, background_path, output_name, style):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    profile = get_profile(style)
    audio_duration = get_media_duration(audio_path)

    start, duration = pick_short_window(audio_duration)

    beats_full = detect_beats(audio_path)
    drop_full = detect_drop(audio_path)

    beats, drop = crop_analysis(beats_full, drop_full, start, duration)

    flash_expr = build_flash_expression(
        beat_times=beats,
        normal_brightness=profile["brightness"],
        beat_flash=min(profile["flash_strength"], 0.20),
        beat_window=0.06,
        drop_time=drop,
        drop_flash=max(min(profile["flash_strength"] + 0.08, 0.28), 0.20)
    )

    shake_expr = build_shake_multiplier_expression(drop)
    audio_filter = build_audio_filter(duration)

    ext = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        vf = build_image_filter(profile, flash_expr, duration, beats)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    elif is_video:
        video_duration = get_media_duration(background_path)
        bg_start = 0 if video_duration <= duration else random.uniform(0, video_duration - duration)

        vf = build_video_filter(profile, flash_expr, shake_expr, duration)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    else:
        fade_out_start_video = max(0, duration - VIDEO_FADE_OUT)

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", (
                "eq=contrast=1.10:brightness=0.01:saturation=1.02,"
                f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
                f"fade=t=out:st={fade_out_start_video}:d={VIDEO_FADE_OUT}"
            ),
            "-af", audio_filter,
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    subprocess.run(cmd, check=True)
    return output_path
