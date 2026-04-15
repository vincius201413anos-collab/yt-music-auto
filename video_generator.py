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

# proteção da thumb / começo mais limpo
INTRO_HOLD_SECONDS = 1.2

# limites de segurança para não exagerar no movimento
MAX_IMAGE_ZOOM = 1.10
MAX_VIDEO_SHAKE_X = 4
MAX_VIDEO_SHAKE_Y = 4


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
    drop = (drop_time - start) if (drop_time is not None and start <= drop_time <= end) else None
    return beats[:60], drop


def build_audio_filter(duration):
    fade_out_start = max(0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fade_out_start}:d={AUDIO_FADE_OUT}"
    )


def build_image_zoom_expr(duration, fps, beat_times, drop_time=None):
    """
    Zoom cinematográfico melhorado:
    - primeiros segundos quase parados (proteção da thumb)
    - curva principal suave ao longo do short
    - micro respiração constante (parece mais humano)
    - bumps leves no beat
    - impacto extra no drop
    - tudo controlado pra evitar tontura
    """
    total_frames = max(1, int(duration * fps))
    intro_hold_frames = int(INTRO_HOLD_SECONDS * fps)

    # curva geral suave de aproximação e retorno
    base_expr = f"(1.00 + 0.045*(0.5 - 0.5*cos(2*PI*on/{total_frames})))"

    # micro respiração contínua
    breathing_expr = "0.004*sin(on*0.04)"

    # bumps leves no beat
    beat_terms = []
    for bt in beat_times[:30]:
        start_f = max(0, int((bt - 0.03) * fps))
        end_f = max(start_f + 1, int((bt + 0.08) * fps))
        beat_terms.append(f"0.005*between(on,{start_f},{end_f})")

    beat_expr = f"({' + '.join(beat_terms)})" if beat_terms else "0"

    # impacto maior no drop
    drop_expr = "0"
    if drop_time is not None:
        drop_f = int(drop_time * fps)
        drop_expr = (
            f"(0.018*between(on,{drop_f-2},{drop_f+2}) + "
            f"0.028*between(on,{drop_f+3},{drop_f+8}) + "
            f"0.012*between(on,{drop_f+9},{drop_f+14}))"
        )

    # segura o começo e depois libera o movimento
    return (
        f"if(lte(on,{intro_hold_frames}),"
        f"1.0,"
        f"{base_expr}+{breathing_expr}+{beat_expr}+{drop_expr}"
        f")"
    )


def build_image_filter(profile, flash_expr, duration, beat_times, drop_time=None):
    fade_out_start_video = max(0, duration - VIDEO_FADE_OUT)
    fps = profile["fps"]

    zoom_expr = build_image_zoom_expr(
        duration=duration,
        fps=fps,
        beat_times=beat_times,
        drop_time=drop_time
    )

    return (
        "scale=1400:2488:force_original_aspect_ratio=increase,"
        "crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
        "zoompan="
        f"z='min(max({zoom_expr},1.0),{MAX_IMAGE_ZOOM})':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920,"
        "eq=contrast=1.12:brightness=0.015:saturation=1.04,"
        f"eq=contrast={profile['contrast']}:brightness='{flash_expr}':saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0,"
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out_start_video}:d={VIDEO_FADE_OUT},"
        f"fps={fps}"
    )


def build_video_filter(profile, flash_expr, shake_expr, duration, drop_time=None):
    fade_out_start_video = max(0, duration - VIDEO_FADE_OUT)

    # shake mais controlado
    shake_x = min(profile.get("shake_x", 3), MAX_VIDEO_SHAKE_X)
    shake_y = min(profile.get("shake_y", 3), MAX_VIDEO_SHAKE_Y)

    # primeiros segundos mais estáveis
    motion_gate = f"if(lt(t,{INTRO_HOLD_SECONDS}),0.18,1)"

    # pequeno reforço extra perto do drop, sem exagero
    drop_boost = "1"
    if drop_time is not None:
        drop_boost = (
            f"(1 + 0.55*between(t,{max(drop_time-0.08, 0)},{drop_time+0.18}))"
        )

    final_shake_expr = f"(({shake_expr})*{motion_gate}*{drop_boost})"

    return (
        "scale=1140:2026:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:"
        f"x='max(0,min(iw-1080,8+sin(t*2.15)*{shake_x}*({final_shake_expr})))':"
        f"y='max(0,min(ih-1920,10+cos(t*1.90)*{shake_y}*({final_shake_expr})))',"
        "eq=contrast=1.12:brightness=0.015:saturation=1.04,"
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
        vf = build_image_filter(
            profile=profile,
            flash_expr=flash_expr,
            duration=duration,
            beat_times=beats,
            drop_time=drop
        )

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

        vf = build_video_filter(
            profile=profile,
            flash_expr=flash_expr,
            shake_expr=shake_expr,
            duration=duration,
            drop_time=drop
        )

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
