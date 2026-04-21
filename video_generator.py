"""
video_generator.py — Final version for high-retention music Shorts.

Objetivos:
- hook forte sem estourar o branco
- beat sync limpo
- drop impactante
- movimento constante
- duração equilibrada para canal de música
- qualidade boa sem pesar demais no Actions
"""

import os
import re
import random
import subprocess
from pathlib import Path

from edit_profiles import get_profile
from audio_analysis import (
    full_analysis,
    crop_analysis,
    build_flash_expression,
    build_shake_expression,
    build_zoom_expression,
    save_debug,
)

# ── Duração ───────────────────────────────────────────────────────────────────
MIN_DURATION = 38
MAX_DURATION = 48

# ── Fades ─────────────────────────────────────────────────────────────────────
VIDEO_FADE_IN = 0.0
VIDEO_FADE_OUT_DUR = 1.0
AUDIO_FADE_IN = 0.15
AUDIO_FADE_OUT = 0.9

# ── Hook ──────────────────────────────────────────────────────────────────────
HOOK_FLASH_BRIGHTNESS = 0.28
HOOK_FLASH_DECAY = 0.12

# ── Shake máximo ──────────────────────────────────────────────────────────────
MAX_SHAKE_X = 8
MAX_SHAKE_Y = 8

# ── Drop ──────────────────────────────────────────────────────────────────────
DROP_ZOOM_PUNCH = 0.08

# ── Fonte ─────────────────────────────────────────────────────────────────────
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_FALLBACK = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ── Render ────────────────────────────────────────────────────────────────────
FFMPEG_VIDEO_CODEC = "libx264"
FFMPEG_CRF = "19"
FFMPEG_PRESET = "medium"
FFMPEG_AUDIO_CODEC = "aac"
FFMPEG_AUDIO_BITRATE = "192k"

# ── Logo ──────────────────────────────────────────────────────────────────────
LOGO_PATH = "assets/logo_darkmark.png"
LOGO_RELATIVE_WIDTH = 0.10
LOGO_MARGIN_X = 22
LOGO_MARGIN_Y = 110
LOGO_OPACITY = 0.88


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def pick_window(audio_dur: float) -> tuple[float, float]:
    """
    Escolhe janela equilibrada para música:
    nem curta demais, nem longa a ponto de arrastar.
    """
    dur = random.randint(
        MIN_DURATION,
        min(MAX_DURATION, max(MIN_DURATION, int(audio_dur))),
    )

    if audio_dur <= dur:
        return 0.0, float(audio_dur)

    min_start = int(audio_dur * 0.08)
    max_start = min(int(audio_dur * 0.25), int(audio_dur - dur))
    start = random.randint(min_start, max(min_start, max_start))
    return float(start), float(dur)


def get_font() -> str:
    for p in (FONT_PATH, FONT_PATH_FALLBACK):
        if os.path.exists(p):
            return p

    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Bold*", "-name", "*.ttf"],
        capture_output=True,
        text=True,
        check=False,
    )
    fonts = [f for f in result.stdout.strip().split("\n") if f]
    return fonts[0] if fonts else FONT_PATH


def escape_text(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    return text[:50]


def logo_exists() -> bool:
    return os.path.exists(LOGO_PATH)


def build_logo_overlay_filter() -> str:
    logo_w = int(1080 * LOGO_RELATIVE_WIDTH)
    return (
        f"[1:v]scale={logo_w}:-1,format=rgba,"
        f"colorchannelmixer=aa={LOGO_OPACITY}[logo];"
        f"[base][logo]overlay="
        f"x=W-w-{LOGO_MARGIN_X}:y=H-h-{LOGO_MARGIN_Y}:format=auto[vout]"
    )


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO
# ══════════════════════════════════════════════════════════════════════════════

def build_audio_filter(duration: float) -> str:
    fo_start = max(0.0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fo_start:.3f}:d={AUDIO_FADE_OUT},"
        "acompressor=threshold=-16dB:ratio=3.5:attack=4:release=45:makeup=1.5dB,"
        "loudnorm=I=-14:TP=-1.0:LRA=9"
    )


# ══════════════════════════════════════════════════════════════════════════════
# BRIGHTNESS / COLOR
# ══════════════════════════════════════════════════════════════════════════════

def build_hook_flash_expr() -> str:
    d = HOOK_FLASH_DECAY
    b = HOOK_FLASH_BRIGHTNESS
    return f"if(lt(t,{d:.3f}),{b}*(1-(t/{d:.3f})),0)"


def build_combined_brightness(profile: dict, analysis: dict) -> str:
    beat_expr = build_flash_expression(
        analysis,
        profile["brightness"],
        profile["beat_flash"],
        profile["bass_flash"],
        profile["drop_flash"],
    )
    hook_expr = build_hook_flash_expr()
    return f"({beat_expr})+({hook_expr})"


def build_color_grade(profile: dict, brightness_expr: str) -> str:
    return (
        "eq=contrast=1.04:brightness=0.0:saturation=1.04,"
        f"eq=contrast={profile['contrast']}"
        f":brightness='{brightness_expr}'"
        f":saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0"
    )


def build_vignette(strength: float) -> str:
    if strength <= 0:
        return ""
    angle = round(strength * 1.10, 3)
    return f"vignette=angle={angle}:mode=forward"


def build_fade_filter(duration: float) -> str:
    fo_start = max(0.0, duration - VIDEO_FADE_OUT_DUR)
    return f"fade=t=out:st={fo_start:.3f}:d={VIDEO_FADE_OUT_DUR}"


# ══════════════════════════════════════════════════════════════════════════════
# OVERLAYS
# ══════════════════════════════════════════════════════════════════════════════

def build_hook_text(song_name: str, style: str, font: str) -> str:
    clean = escape_text(song_name)
    style_tag = escape_text(f"#{style.upper()} #SHORTS")

    title_alpha = (
        "if(lt(t,0.20),0,"
        "if(lt(t,0.55),(t-0.20)/0.35,"
        "if(lt(t,3.2),1.0,"
        "if(lt(t,3.8),(3.8-t)/0.6,0))))"
    )

    title = (
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=58"
        f":fontcolor=white"
        f":borderw=3:bordercolor=black@0.88"
        f":shadowx=3:shadowy=3:shadowcolor=black@0.6"
        f":x=(w-text_w)/2"
        f":y=h*0.11"
        f":alpha='{title_alpha}'"
    )

    tag_alpha = (
        "if(lt(t,0.45),0,"
        "if(lt(t,0.85),(t-0.45)/0.40,"
        "if(lt(t,3.2),0.95,"
        "if(lt(t,3.8),(3.8-t)/0.6,0))))"
    )

    tag = (
        f"drawtext=fontfile='{font}'"
        f":text='{style_tag}'"
        f":fontsize=30"
        f":fontcolor=white@0.82"
        f":borderw=2:bordercolor=black@0.75"
        f":x=(w-text_w)/2"
        f":y=h*0.11+68"
        f":alpha='{tag_alpha}'"
    )

    return f"{title},{tag}"


def build_progress_bar(duration: float) -> str:
    return (
        "drawbox=x=0:y=ih-8:w=iw:h=8:color=black@0.55:t=fill,"
        f"drawbox=x=0:y=ih-8:w='iw*t/{duration:.3f}':h=8:color=0xFF2244@0.92:t=fill"
    )


def build_watermark(font: str) -> str:
    return (
        f"drawtext=fontfile='{font}'"
        f":text='@darkmrkedit'"
        f":fontsize=22"
        f":fontcolor=white@0.50"
        f":borderw=1:bordercolor=black@0.35"
        f":x=w-text_w-18"
        f":y=18"
        f":alpha='if(lt(t,3.0),0,if(lt(t,3.8),(t-3.0)/0.8,0.50))'"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MOTION
# ══════════════════════════════════════════════════════════════════════════════

def build_elite_zoom(
    analysis: dict,
    duration: float,
    fps: int,
    max_zoom: float,
    zoom_speed: float,
    pulse_strength: float,
) -> str:
    beats = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.45 * fps)

    base = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength * 0.7}*sin(on*0.07+0.3)*cos(on*0.031))"

    beat_pulse = "0"
    if beats:
        parts = [f"0.004*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})" for b in beats[:60]]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        parts = [f"0.010*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+6})" for b in bass_hits[:50]]
        bass_pulse = f"({'+'.join(parts)})"

    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({DROP_ZOOM_PUNCH}*between(on,{df-1},{df+4})"
            f"+0.045*between(on,{df+5},{df+18})"
            f"+0.015*between(on,{df+19},{df+32}))"
        )

    full = f"{base}+{drift}+{beat_pulse}+{bass_pulse}+{drop_expr}"

    return (
        f"if(lte(on,{intro_frames}),"
        f"1.0,"
        f"min(max({full},1.0),{max_zoom + DROP_ZOOM_PUNCH}))"
    )


def build_elite_shake(analysis: dict, sx: int, sy: int):
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])

    shake_x = f"(sin(t*2.8)*{sx*0.68}+sin(t*5.1)*{sx*0.32})"
    shake_y = f"(cos(t*2.5)*{sy*0.68}+cos(t*4.7)*{sy*0.32})"

    if bass_hits:
        boosts = [f"1.6*between(t,{max(0,t-0.03):.3f},{t+0.18:.3f})" for t in bass_hits[:50]]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        drop_mult = f"(1+3.0*between(t,{drop_time-0.03:.3f},{drop_time+0.28:.3f}))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    hook_gate = "if(lt(t,0.45),0.08,1.0)"
    shake_x = f"({shake_x})*{hook_gate}"
    shake_y = f"({shake_y})*{hook_gate}"

    return shake_x, shake_y


# ══════════════════════════════════════════════════════════════════════════════
# FILTER BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_image_filter(
    profile: dict,
    analysis: dict,
    duration: float,
    song_name: str,
    style: str,
) -> str:
    fps = profile["fps"]
    font = get_font()

    brightness_expr = build_combined_brightness(profile, analysis)
    zoom_expr = build_elite_zoom(
        analysis, duration, fps,
        profile["max_zoom"], profile["zoom_speed"], profile["pulse_strength"],
    )

    color = build_color_grade(profile, brightness_expr)
    vig = build_vignette(profile.get("vignette", 0.4))
    fades = build_fade_filter(duration)
    hook = build_hook_text(song_name, style, font)
    pbar = build_progress_bar(duration)
    wtmk = build_watermark(font)

    parts = [
        "scale=1440:2560:force_original_aspect_ratio=increase",
        "crop=1080:1920:(iw-1080)/2:(ih-1920)/2",
        (
            f"zoompan="
            f"z='{zoom_expr}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d=1:s=1080x1920"
        ),
        color,
    ]
    if vig:
        parts.append(vig)
    parts += [fades, f"fps={fps}", hook, pbar, wtmk]
    return ",".join(parts)


def build_video_filter(
    profile: dict,
    analysis: dict,
    duration: float,
    song_name: str,
    style: str,
) -> str:
    fps = profile["fps"]
    font = get_font()

    brightness_expr = build_combined_brightness(profile, analysis)
    sx = min(profile.get("shake_x", 4), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 4), MAX_SHAKE_Y)
    shake_x_expr, shake_y_expr = build_elite_shake(analysis, sx, sy)

    color = build_color_grade(profile, brightness_expr)
    vig = build_vignette(profile.get("vignette", 0.4))
    fades = build_fade_filter(duration)
    hook = build_hook_text(song_name, style, font)
    pbar = build_progress_bar(duration)
    wtmk = build_watermark(font)

    parts = [
        "scale=1140:2026:force_original_aspect_ratio=increase",
        (
            f"crop=1080:1920:"
            f"x='max(0,min(iw-1080,iw/2-540+({shake_x_expr})))':"
            f"y='max(0,min(ih-1920,ih/2-960+({shake_y_expr})))'"
        ),
        color,
    ]
    if vig:
        parts.append(vig)
    parts += [fades, f"fps={fps}", hook, pbar, wtmk]
    return ",".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def _build_cmd(
    inputs: list,
    vf_or_complex: str,
    is_complex: bool,
    use_logo: bool,
    audio_filter: str,
    dur: float,
    output_name: str,
) -> list:
    cmd = ["ffmpeg", "-y"] + inputs + ["-t", str(dur)]

    if is_complex:
        cmd += ["-filter_complex", vf_or_complex]
        if use_logo:
            cmd += ["-map", "[vout]", "-map", "2:a"]
        else:
            cmd += ["-map", "[vout]", "-map", "1:a"]
    else:
        cmd += ["-vf", vf_or_complex, "-map", "0:v", "-map", "1:a"]

    cmd += [
        "-af", audio_filter,
        "-shortest",
        "-c:v", FFMPEG_VIDEO_CODEC,
        "-crf", FFMPEG_CRF,
        "-preset", FFMPEG_PRESET,
        "-pix_fmt", "yuv420p",
        "-c:a", FFMPEG_AUDIO_CODEC,
        "-b:a", FFMPEG_AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_name,
    ]
    return cmd


def create_short(
    audio_path: str,
    background_path: str,
    output_name: str,
    style: str,
    song_name: str = "",
) -> str:
    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not song_name:
        song_name = Path(audio_path).stem
        song_name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", song_name)
        song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()

    profile = get_profile(style)
    audio_dur = get_duration(audio_path)
    start, dur = pick_window(audio_dur)

    print("  ► Analisando áudio…")
    analysis_full = full_analysis(audio_path)
    analysis = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    audio_filter = build_audio_filter(dur)
    use_logo = logo_exists()

    ext = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        base_vf = build_image_filter(profile, analysis, dur, song_name, style)

        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-loop", "1", "-i", background_path, "-i", LOGO_PATH,
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-loop", "1", "-i", background_path,
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    elif is_video:
        bg_dur = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        base_vf = build_video_filter(profile, analysis, dur, song_name, style)

        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-ss", str(bg_start), "-i", background_path,
                      "-i", LOGO_PATH,
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-ss", str(bg_start), "-i", background_path,
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    else:
        font = get_font()
        hook = build_hook_text(song_name, style, font)
        pbar = build_progress_bar(dur)
        wtmk = build_watermark(font)
        fade = build_fade_filter(dur)
        base_vf = f"{fade},{hook},{pbar},{wtmk}"

        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
                      "-i", LOGO_PATH,
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
                      "-ss", str(start), "-i", audio_path]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    print("  ► Iniciando render…")
    subprocess.run(cmd, check=True)
    print("  ► Render concluído ✓")
    return output_name
