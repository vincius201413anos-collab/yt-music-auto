"""
video_generator.py — Gerador de Shorts profissional.
Foco total em retenção: zoom orgânico, flash sincronizado,
vignette, color grade por estilo, shake proporcional ao impacto.
"""

import os
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

# ── Parâmetros globais ────────────────────────────────────────────────────────
MIN_DURATION = 42
MAX_DURATION = 68
VIDEO_FADE_IN  = 0.4
VIDEO_FADE_OUT = 0.7
AUDIO_FADE_IN  = 0.4
AUDIO_FADE_OUT = 0.9
MAX_SHAKE_X    = 7
MAX_SHAKE_Y    = 7


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
    """Escolhe janela inteligente: prefere região do drop."""
    dur = random.randint(
        MIN_DURATION,
        min(MAX_DURATION, int(audio_dur)),
    )
    if audio_dur <= dur:
        return 0.0, float(dur)

    # prefere começar a partir de 15% da música (evita intro fraca)
    min_start = int(audio_dur * 0.12)
    max_start = int(audio_dur - dur)
    start = random.randint(min_start, max(min_start, max_start))
    return float(start), float(dur)


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO FILTER
# ══════════════════════════════════════════════════════════════════════════════

def build_audio_filter(duration: float) -> str:
    fade_out_start = max(0.0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fade_out_start:.3f}:d={AUDIO_FADE_OUT},"
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO FILTERS
# ══════════════════════════════════════════════════════════════════════════════

def _color_grade(profile: dict, flash_expr: str) -> str:
    """Camada de color grade + flash sincronizado."""
    return (
        f"eq=contrast=1.12:brightness=0.015:saturation=1.06,"
        f"eq=contrast={profile['contrast']}"
        f":brightness='{flash_expr}'"
        f":saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0"
    )


def _vignette_filter(strength: float) -> str:
    """Vignette que escurece as bordas — foca o olhar no centro."""
    if strength <= 0:
        return ""
    angle = round(strength * 1.2, 2)
    return f"vignette=angle={angle}:mode=forward"


def _fade_filter(duration: float) -> str:
    fade_out = max(0.0, duration - VIDEO_FADE_OUT)
    return (
        f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
        f"fade=t=out:st={fade_out:.3f}:d={VIDEO_FADE_OUT}"
    )


# ── IMAGEM ESTÁTICA ───────────────────────────────────────────────────────────

def build_image_filter(
    profile: dict,
    analysis: dict,
    duration: float,
) -> str:
    fps         = profile["fps"]
    flash_expr  = build_flash_expression(
        analysis,
        profile["brightness"],
        profile["beat_flash"],
        profile["bass_flash"],
        profile["drop_flash"],
    )
    zoom_expr = build_zoom_expression(
        analysis, duration, fps,
        profile["max_zoom"],
        profile["zoom_speed"],
        profile["pulse_strength"],
    )
    color  = _color_grade(profile, flash_expr)
    vig    = _vignette_filter(profile.get("vignette", 0.4))
    fades  = _fade_filter(duration)

    parts = [
        # escala grande para zoompan não vazar bordas pretas
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
    parts += [fades, f"fps={fps}"]

    return ",".join(parts)


# ── VÍDEO ─────────────────────────────────────────────────────────────────────

def build_video_filter(
    profile: dict,
    analysis: dict,
    duration: float,
) -> str:
    fps = profile["fps"]

    flash_expr = build_flash_expression(
        analysis,
        profile["brightness"],
        profile["beat_flash"],
        profile["bass_flash"],
        profile["drop_flash"],
    )

    sx = min(profile.get("shake_x", 3), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 3), MAX_SHAKE_Y)
    shake_x_expr, shake_y_expr = build_shake_expression(analysis, sx, sy)

    # intro hold: 0.6s sem shake para não começar tonta
    intro_hold = 0.6
    shake_gate = f"if(lt(t,{intro_hold}),0.15,1.0)"

    color = _color_grade(profile, flash_expr)
    vig   = _vignette_filter(profile.get("vignette", 0.4))
    fades = _fade_filter(duration)

    parts = [
        "scale=1140:2026:force_original_aspect_ratio=increase",
        (
            f"crop=1080:1920:"
            f"x='max(0,min(iw-1080,iw/2-540+({shake_x_expr})*{shake_gate}))':"
            f"y='max(0,min(ih-1920,ih/2-960+({shake_y_expr})*{shake_gate}))'"
        ),
        color,
    ]
    if vig:
        parts.append(vig)
    parts += [fades, f"fps={fps}"]

    return ",".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — create_short
# ══════════════════════════════════════════════════════════════════════════════

def create_short(
    audio_path: str,
    background_path: str,
    output_name: str,
    style: str,
) -> str:
    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    profile      = get_profile(style)
    audio_dur    = get_duration(audio_path)
    start, dur   = pick_window(audio_dur)

    # análise completa no áudio original
    print(f"  Analisando áudio…")
    analysis_full   = full_analysis(audio_path)
    analysis        = crop_analysis(analysis_full, start, dur)

    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    audio_filter = build_audio_filter(dur)

    ext      = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    # ── IMAGEM ──────────────────────────────────────────────────────────────
    if is_image:
        vf = build_image_filter(profile, analysis, dur)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(dur),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "16", "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_name,
        ]

    # ── VÍDEO ────────────────────────────────────────────────────────────────
    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = (
            0.0 if bg_dur <= dur
            else random.uniform(0.0, bg_dur - dur)
        )
        vf = build_video_filter(profile, analysis, dur)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start),    "-i", audio_path,
            "-t", str(dur),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "16", "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_name,
        ]

    # ── FALLBACK (fundo preto) ───────────────────────────────────────────────
    else:
        fade_out = max(0.0, dur - VIDEO_FADE_OUT)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={dur}",
            "-ss", str(start), "-i", audio_path,
            "-t", str(dur),
            "-vf", (
                f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
                f"fade=t=out:st={fade_out:.3f}:d={VIDEO_FADE_OUT}"
            ),
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_name,
        ]

    print(f"  Renderizando vídeo…")
    subprocess.run(cmd, check=True)
    return output_name
