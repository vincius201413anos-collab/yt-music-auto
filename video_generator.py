"""
video_generator.py — Gerador de Shorts profissional.
Melhorias de retenção: hook text overlay nos primeiros 3s,
progress bar, zoom orgânico, flash sincronizado, color grade premium.
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

# ── Parâmetros globais ────────────────────────────────────────────────────────
MIN_DURATION   = 42
MAX_DURATION   = 62       # reduzido: shorts mais curtos = mais retenção
VIDEO_FADE_IN  = 0.3
VIDEO_FADE_OUT = 0.6
AUDIO_FADE_IN  = 0.3
AUDIO_FADE_OUT = 0.8
MAX_SHAKE_X    = 7
MAX_SHAKE_Y    = 7

# Fonte padrão no Ubuntu (GitHub Actions)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# Fallback
FONT_PATH_FALLBACK = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


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
    Escolhe janela inteligente.
    Prefere começo ligeiramente no início (pula intro fraca)
    e garante duração otimizada para retenção.
    """
    dur = random.randint(
        MIN_DURATION,
        min(MAX_DURATION, int(audio_dur)),
    )
    if audio_dur <= dur:
        return 0.0, float(dur)

    # Começa entre 10% e 30% da música (evita intro e pega melhor parte)
    min_start = int(audio_dur * 0.10)
    max_start = min(int(audio_dur * 0.30), int(audio_dur - dur))
    start = random.randint(min_start, max(min_start, max_start))
    return float(start), float(dur)


def get_font() -> str:
    """Retorna fonte disponível no sistema."""
    if os.path.exists(FONT_PATH):
        return FONT_PATH
    if os.path.exists(FONT_PATH_FALLBACK):
        return FONT_PATH_FALLBACK
    # Busca qualquer fonte Bold disponível
    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Bold*", "-name", "*.ttf"],
        capture_output=True, text=True
    )
    fonts = [f for f in result.stdout.strip().split("\n") if f]
    return fonts[0] if fonts else FONT_PATH


def escape_text(text: str) -> str:
    """Escapa texto para uso no filtro drawtext do FFmpeg."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    return text[:50]  # limita tamanho para caber na tela


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
# OVERLAY FILTERS — RETENÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def build_hook_text_filter(song_name: str, style: str, font: str) -> str:
    """
    Hook text overlay — aparece nos primeiros 3.5s com fade suave.
    Prova científica: os primeiros 2-3s determinam se o viewer fica.
    """
    clean = escape_text(song_name)

    # Linha superior: nome da música (grande)
    title_filter = (
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=58"
        f":fontcolor=white"
        f":borderw=3:bordercolor=black@0.9"
        f":shadowx=2:shadowy=2:shadowcolor=black@0.7"
        f":x=(w-text_w)/2"
        f":y=h*0.12"
        f":alpha='if(lt(t,0.3),t/0.3,if(lt(t,3.0),1.0,if(lt(t,3.8),(3.8-t)/0.8,0)))'"
    )

    # Linha inferior: estilo (menor, mais discreta)
    style_label = escape_text(f"#{style.upper()} #SHORTS")
    style_filter = (
        f"drawtext=fontfile='{font}'"
        f":text='{style_label}'"
        f":fontsize=32"
        f":fontcolor=white@0.85"
        f":borderw=2:bordercolor=black@0.8"
        f":x=(w-text_w)/2"
        f":y=h*0.12+72"
        f":alpha='if(lt(t,0.5),0,if(lt(t,0.9),(t-0.5)/0.4,if(lt(t,3.0),1.0,if(lt(t,3.8),(3.8-t)/0.8,0))))'"
    )

    return f"{title_filter},{style_filter}"


def build_progress_bar_filter(duration: float) -> str:
    """
    Barra de progresso no rodapé — técnica de retenção eficaz.
    Cria expectativa do tipo 'wait for the drop / best part'.
    """
    return (
        # Fundo da barra (escuro)
        f"drawbox=x=0:y=ih-10:w=iw:h=10:color=black@0.6:t=fill,"
        # Barra de progresso que avança
        f"drawbox=x=0:y=ih-10"
        f":w='iw*t/{duration:.3f}'"
        f":h=10"
        f":color=0xE8354A@0.95"   # vermelho vibrante
        f":t=fill"
    )


def build_watermark_filter(font: str) -> str:
    """
    Marca d'água sutil no canto — branding do canal.
    Aparece de forma discreta a partir de 3s.
    """
    return (
        f"drawtext=fontfile='{font}'"
        f":text='@darkmrkedit'"
        f":fontsize=24"
        f":fontcolor=white@0.55"
        f":borderw=1:bordercolor=black@0.4"
        f":x=w-text_w-20"
        f":y=20"
        f":alpha='if(lt(t,3),0,if(lt(t,3.6),(t-3)/0.6,0.55))'"
    )


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO FILTERS
# ══════════════════════════════════════════════════════════════════════════════

def _color_grade(profile: dict, flash_expr: str) -> str:
    """Camada de color grade premium + flash sincronizado."""
    return (
        # Primeiro passe: normalização base
        f"eq=contrast=1.08:brightness=0.01:saturation=1.05,"
        # Segundo passe: perfil do estilo + flash dinâmico
        f"eq=contrast={profile['contrast']}"
        f":brightness='{flash_expr}'"
        f":saturation={profile['saturation']},"
        # Sharpening
        f"unsharp=5:5:{profile['sharpen']}:5:5:0"
    )


def _vignette_filter(strength: float) -> str:
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
    song_name: str,
    style: str,
) -> str:
    fps        = profile["fps"]
    font       = get_font()
    flash_expr = build_flash_expression(
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
    hook   = build_hook_text_filter(song_name, style, font)
    pbar   = build_progress_bar_filter(duration)
    wtmk   = build_watermark_filter(font)

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
    parts += [
        fades,
        f"fps={fps}",
        hook,
        pbar,
        wtmk,
    ]

    return ",".join(parts)


# ── VÍDEO ─────────────────────────────────────────────────────────────────────

def build_video_filter(
    profile: dict,
    analysis: dict,
    duration: float,
    song_name: str,
    style: str,
) -> str:
    fps  = profile["fps"]
    font = get_font()

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

    intro_hold = 0.6
    shake_gate = f"if(lt(t,{intro_hold}),0.15,1.0)"

    color  = _color_grade(profile, flash_expr)
    vig    = _vignette_filter(profile.get("vignette", 0.4))
    fades  = _fade_filter(duration)
    hook   = build_hook_text_filter(song_name, style, font)
    pbar   = build_progress_bar_filter(duration)
    wtmk   = build_watermark_filter(font)

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
    parts += [
        fades,
        f"fps={fps}",
        hook,
        pbar,
        wtmk,
    ]

    return ",".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — create_short
# ══════════════════════════════════════════════════════════════════════════════

def create_short(
    audio_path: str,
    background_path: str,
    output_name: str,
    style: str,
    song_name: str = "",   # novo parâmetro para overlays
) -> str:
    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Extrai nome da música do caminho se não passado
    if not song_name:
        song_name = Path(audio_path).stem
        song_name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", song_name)
        song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()

    profile    = get_profile(style)
    audio_dur  = get_duration(audio_path)
    start, dur = pick_window(audio_dur)

    print(f"  Analisando áudio…")
    analysis_full = full_analysis(audio_path)
    analysis      = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    audio_filter = build_audio_filter(dur)

    ext      = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    # ── IMAGEM ──────────────────────────────────────────────────────────────
    if is_image:
        vf = build_image_filter(profile, analysis, dur, song_name, style)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
            "-t", str(dur),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "15", "-preset", "slow",
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
        vf = build_video_filter(profile, analysis, dur, song_name, style)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start),    "-i", audio_path,
            "-t", str(dur),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "15", "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_name,
        ]

    # ── FALLBACK (fundo preto) ───────────────────────────────────────────────
    else:
        font    = get_font()
        hook    = build_hook_text_filter(song_name, style, font)
        pbar    = build_progress_bar_filter(dur)
        wtmk    = build_watermark_filter(font)
        fade_out = max(0.0, dur - VIDEO_FADE_OUT)
        vf = (
            f"fade=t=in:st=0:d={VIDEO_FADE_IN},"
            f"fade=t=out:st={fade_out:.3f}:d={VIDEO_FADE_OUT},"
            f"{hook},{pbar},{wtmk}"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={dur}",
            "-ss", str(start), "-i", audio_path,
            "-t", str(dur),
            "-vf", vf,
            "-af", audio_filter,
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-crf", "15",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_name,
        ]

    print(f"  Renderizando vídeo…")
    subprocess.run(cmd, check=True)
    return output_name
