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

MIN_SHORT_DURATION = 40
MAX_SHORT_DURATION = 70

VIDEO_FADE_IN = 0.5
VIDEO_FADE_OUT = 0.8
AUDIO_FADE_IN = 0.5
AUDIO_FADE_OUT = 1.0

INTRO_HOLD_SECONDS = 0.8
MAX_IMAGE_ZOOM = 1.12
MAX_VIDEO_SHAKE_X = 5
MAX_VIDEO_SHAKE_Y = 5


def get_media_duration(file_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def pick_short_window(audio_duration):
    if audio_duration <= MIN_SHORT_DURATION:
        return 0, int(audio_duration)

    duration = random.randint(
        MIN_SHORT_DURATION,
        min(MAX_SHORT_DURATION, int(audio_duration)),
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
    drop = (drop_time - start) if (drop_time is not None and start <= drop_time <= end) else None
    return beats[:80], drop


def build_audio_filter(duration):
    fade_out_start = max(0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fade_out_start}:d={AUDIO_FADE_OUT}"
    )


def build_image_zoom_expr(duration, fps, beat_times, drop_time=None):
    total_frames = max(1, int(duration * fps))
    intro_hold_frames = int(INTRO_HOLD_SECONDS * fps)

    base = f"(1.0 + 0.06*(0.5 - 0.5*cos(2*PI*on/{total_frames})))"
    breathing = "0.006*sin(on*0.045)"

    beat_expr = "0"
    if beat_times:
        parts = []
        for bt in beat_times[:40]:
            f = int(bt * fps)
            parts.append(f"0.006*between(on,{f-1},{f+2})")
        beat_expr = f"({' + '.join(parts)})"

    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"(0.03*between(on,{df-2},{df+2}) + "
            f"0.05*between(on,{df+3},{df+8}))"
        )

    return (
        f"if(lte(on,{intro_hold_frames}),"
        f"1.0,"
        f"{base}+{breathing}+{beat_expr}+{drop_expr})"
    )


def build_image_filter(profile, flash_expr, duration, beat_times, drop_time=None):
    fade_out_start = max(0, duration - VIDEO_FADE_OUT)
    fps = profile["fps"]

    zoom_expr = build_image_zoom_expr(duration, fps, beat_times, drop_time)

    return (
        "scale=1400:2488:force_original_aspect_ratio=increase,"
        "crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
        "zoompan="
        f"z='min(max({zoom_expr},1.0),{MAX_IMAGE_ZOOM})':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:s=1080x1920,"
        "eq=contrast=1.15:brightness=0.02:saturation=1.05,"
        f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out_start}:d={VIDEO_FADE_OUT},"
        f"fps={fps}"
    )


def build_video_filter(profile, flash_expr, shake_expr, duration, drop_time=None):
    fade_out_start = max(0, duration - VIDEO_FADE_OUT)

    shake_x = min(profile.get("shake_x", 3), MAX_VIDEO_SHAKE_X)
    shake_y = min(profile.get("shake_y", 3), MAX_VIDEO_SHAKE_Y)

    motion_gate = f"if(lt(t,{INTRO_HOLD_SECONDS}),0.2,1)"

    drop_boost = "1"
    if drop_time is not None:
        drop_boost = f"(1 + 0.8*between(t,{drop_time-0.05},{drop_time+0.2}))"

    final = f"(({shake_expr})*{motion_gate}*{drop_boost})"

    return (
        "scale=1140:2026:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:"
        f"x='max(0,min(iw-1080,8+sin(t*2.4)*{shake_x}*({final})))':"
        f"y='max(0,min(ih-1920,10+cos(t*2.1)*{shake_y}*({final})))',"
        "eq=contrast=1.15:brightness=0.02:saturation=1.05,"
        f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out_start}:d={VIDEO_FADE_OUT},"
        f"fps={profile['fps']}"
    )


def create_short(audio_path, background_path, output_name, style):
    output_path = output_name
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    profile = get_profile(style)
    audio_duration = get_media_duration(audio_path)

    start, duration = pick_short_window(audio_duration)

    beats_full = detect_beats(audio_path)
    drop_full = detect_drop(audio_path)

    beats, drop = crop_analysis(beats_full, drop_full, start, duration)

    flash_expr = build_flash_expression(
        beats,
        profile["brightness"],
        beat_flash=0.18,
        beat_window=0.05,
        drop_time=drop,
        drop_flash=0.32,
    )

    shake_expr = build_shake_multiplier_expression(drop)
    audio_filter = build_audio_filter(duration)

    ext = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        vf = build_image_filter(profile, flash_expr, duration, beats, drop)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-crf", "17",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

    elif is_video:
        video_duration = get_media_duration(background_path)
        bg_start = 0 if video_duration <= duration else random.uniform(0, video_duration - duration)

        vf = build_video_filter(profile, flash_expr, shake_expr, duration, drop)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-crf", "17",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

    else:
        fade_out_start = max(0, duration - VIDEO_FADE_OUT)

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-ss", str(start), "-i", audio_path,
            "-t", str(duration),
            "-vf", (
                "eq=contrast=1.10:brightness=0.01:saturation=1.02,"
                f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
                f"fade=t=out:st={fade_out_start}:d={VIDEO_FADE_OUT}"
            ),
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264",
            "-crf", "17",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

    subprocess.run(cmd, check=True)
    return output_path
