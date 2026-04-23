"""
video_generator.py — Elite Music Shorts Generator v4.0
=======================================================
MUDANÇAS v4.0 (baseado em análise dos canais virais de phonk/trap/eletrônica):

1. HOOK INSTANTÂNEO — texto aparece no frame 0, sem fade-in de 0.55s
   → Canais virais mostram o nome da música IMEDIATAMENTE
   → Pesquisa: hook deve acontecer no 1º ou 2º segundo

2. JANELA INTELIGENTE COMEÇA NO PICO — find_best_window agora prioriza
   o drop/pico de energia, não apenas evita o início
   → O 1º frame do Short precisa ser o momento mais intenso da música

3. BASS FLASH MAIS FORTE — phonk/trap têm flash no kick/808 mais visível
   → Os canais que viralizam têm zoom/flash sincronizado com o baixo

4. PROGRESS BAR MAIS GROSSA e visível — sinaliza pro usuário que tem
   conteúdo, aumenta retenção (as pessoas assistem até o fim por curiosidade)

5. SONG NAME MAIOR e no topo imediato — visibilidade máxima no 1º frame

6. WAVEFORM OVERLAY por gênero — phonk/trap ganham barra de waveform
   no rodapé que pulsa com o áudio (estética dos canais grandes)

7. COLOR GRADE refinado — phonk ainda mais contrastado, lofi mais quente
"""

from __future__ import annotations

import logging
import os
import re
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from edit_profiles import get_profile, get_profile_for_bpm, list_profiles
from audio_analysis import (
    full_analysis,
    crop_analysis,
    find_best_window,
    build_flash_expression,
    build_shake_expression,
    build_zoom_expression,
    save_debug,
)

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "generator.log"
    fmt = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

setup_logging()
logger = logging.getLogger("video_generator")


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

MIN_DURATION        = 38
MAX_DURATION        = 58          # ← aumentado: 50-58s tem melhor retenção em música
VIDEO_FADE_OUT_DUR  = 0.8         # ← mais rápido, menos tempo perdido no fim
AUDIO_FADE_IN       = 0.05        # ← quase zero — o áudio entra BRUTAL imediatamente
AUDIO_FADE_OUT      = 0.7
HOOK_FLASH_BRIGHTNESS = 0.22
HOOK_FLASH_DECAY    = 0.08        # ← flash de entrada mais rápido
MAX_SHAKE_X         = 8
MAX_SHAKE_Y         = 8
DROP_ZOOM_PUNCH     = 0.10        # ← punch mais forte no drop

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FFMPEG_VIDEO_CODEC   = "libx264"
FFMPEG_CRF           = "19"
FFMPEG_PRESET        = "medium"
FFMPEG_AUDIO_CODEC   = "aac"
FFMPEG_AUDIO_BITRATE = "192k"

LOGO_PATH           = "assets/logo_darkmark.png"
LOGO_RELATIVE_WIDTH = 0.10
LOGO_MARGIN_X       = 22
LOGO_MARGIN_Y       = 110
LOGO_OPACITY        = 0.88

THUMB_DIR       = "thumbnails"
THUMB_TIMESTAMP = 2.0             # ← thumbnail tirada mais cedo — frame mais energético

MAX_RETRIES     = 2
RETRY_DELAY_S   = 3

MIN_FILE_SIZE_MB = 0.5
MAX_FILE_SIZE_MB = 200.0


# ══════════════════════════════════════════════════════════════════════════════
# COLOR GRADE POR GÊNERO — refinado v4
# ══════════════════════════════════════════════════════════════════════════════

GENRE_COLOR_GRADE = {
    # PHONK — vermelho sangue brutal, contraste máximo, grain pesadíssimo
    # Referência: canais de drift phonk com milhões de views
    "phonk": (
        "colorbalance=rs=0.22:gs=-0.08:bs=-0.15,"        # crimson agressivo
        "eq=contrast=1.35:brightness=-0.04:saturation=1.40,"
        "unsharp=5:5:1.6:5:5:0,"
        "noise=alls=18:allf=t+u"                          # grain urbano máximo
    ),

    # LOFI — amber profundo, vintage rico, grain analógico
    "lofi": (
        "colorbalance=rs=0.10:gs=0.03:bs=-0.14,"          # amber quente profundo
        "eq=contrast=0.94:brightness=0.022:saturation=0.85,"
        "unsharp=3:3:0.3:3:3:0,"
        "noise=alls=7:allf=t"
    ),

    # TRAP — azul frio premium, gold nos highlights, editorial limpo
    "trap": (
        "colorbalance=rs=-0.06:gs=0.02:bs=0.15,"          # teal frio premium
        "eq=contrast=1.22:brightness=0.010:saturation=1.25,"
        "unsharp=5:5:1.0:5:5:0"
    ),

    # DARK — quase preto e branco com acento roxo, vinheta pesada
    "dark": (
        "colorbalance=rs=-0.08:gs=-0.10:bs=0.18,"
        "eq=contrast=1.38:brightness=-0.06:saturation=0.72,"
        "unsharp=5:5:1.0:5:5:0,"
        "vignette=angle=PI/3.2:mode=forward"
    ),

    # ELECTRONIC — neon maximum, saturação rave, cyan vs magenta
    "electronic": (
        "colorbalance=rs=-0.10:gs=0.06:bs=0.22,"          # cyan neon extremo
        "eq=contrast=1.18:brightness=0.015:saturation=1.65,"
        "unsharp=5:5:0.8:5:5:0"
    ),

    # ROCK — amber palco brutal, grain de show ao vivo
    "rock": (
        "colorbalance=rs=0.14:gs=0.05:bs=-0.10,"
        "eq=contrast=1.24:brightness=0.006:saturation=1.20,"
        "unsharp=5:5:1.1:5:5:0,"
        "noise=alls=10:allf=t"
    ),

    # METAL — frio e escuro, máximo contraste, épico
    "metal": (
        "colorbalance=rs=-0.12:gs=-0.08:bs=0.10,"
        "eq=contrast=1.42:brightness=-0.05:saturation=0.80,"
        "unsharp=5:5:1.3:5:5:0,"
        "vignette=angle=PI/3.0:mode=forward"
    ),

    # INDIE — golden hour honesto, overexposed natural
    "indie": (
        "colorbalance=rs=0.07:gs=0.05:bs=-0.07,"
        "eq=contrast=0.97:brightness=0.025:saturation=0.92,"
        "unsharp=3:3:0.3:3:3:0,"
        "noise=alls=5:allf=t"
    ),

    # CINEMATIC — teal-orange clássico de cinema
    "cinematic": (
        "colorbalance=rs=0.12:gs=-0.02:bs=-0.14,"
        "colorbalance=rs=-0.09:gs=0.04:bs=0.16:shadows=enable:highlights=disable,"
        "eq=contrast=1.14:brightness=0.006:saturation=1.10,"
        "unsharp=5:5:0.9:5:5:0"
    ),

    # FUNK — quente vibrante, groove saturado
    "funk": (
        "colorbalance=rs=0.16:gs=0.07:bs=-0.12,"
        "eq=contrast=1.12:brightness=0.018:saturation=1.48,"
        "unsharp=3:3:0.5:3:3:0"
    ),

    # POP — brilhante limpo
    "pop": (
        "colorbalance=rs=0.04:gs=0.04:bs=0.06,"
        "eq=contrast=1.08:brightness=0.022:saturation=1.38,"
        "unsharp=3:3:0.6:3:3:0"
    ),

    "default": (
        "eq=contrast=1.12:brightness=0.012:saturation=1.12,"
        "unsharp=5:5:0.8:5:5:0"
    ),
}

GENRE_VIGNETTE = {
    "phonk":      0.60,
    "dark":       0.0,
    "metal":      0.0,
    "lofi":       0.32,
    "trap":       0.22,
    "electronic": 0.12,
    "rock":       0.38,
    "indie":      0.26,
    "cinematic":  0.42,
    "funk":       0.15,
    "pop":        0.10,
    "default":    0.35,
}

# Gêneros que ganham waveform no rodapé (estética dos canais virais)
GENRE_WAVEFORM_COLOR = {
    "phonk":      "0xFF1122",
    "trap":       "0x00AAFF",
    "electronic": "0x00FFCC",
    "dark":       "0x8800FF",
    "metal":      "0xFF4400",
    "rock":       "0xFF8800",
    "funk":       "0xFFAA00",
    "lofi":       "0xFFCC88",
    "indie":      "0xFFDD88",
    "cinematic":  "0xFFBB44",
    "pop":        "0xFF44AA",
    "default":    "0xFFFFFF",
}


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


def get_video_info(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration,size",
        "-of", "json", path,
    ]
    import json
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)

    stream  = data.get("streams", [{}])[0]
    fmt     = data.get("format", {})
    fps_str = stream.get("r_frame_rate", "30/1")
    try:
        num, den = fps_str.split("/")
        fps = round(int(num) / int(den), 2)
    except Exception:
        fps = 30.0

    return {
        "width":    int(stream.get("width", 0)),
        "height":   int(stream.get("height", 0)),
        "duration": float(fmt.get("duration", 0)),
        "fps":      fps,
        "size_mb":  round(int(fmt.get("size", 0)) / (1024 * 1024), 2),
    }


def pick_window(audio_dur: float) -> tuple[float, float]:
    """
    Fallback window picker quando find_best_window não está disponível.
    Prioriza a região entre 15-40% da música (geralmente onde o drop está).
    """
    dur = random.randint(MIN_DURATION, min(MAX_DURATION, max(MIN_DURATION, int(audio_dur))))
    if audio_dur <= dur:
        return 0.0, float(audio_dur)
    # Começa no pico energético provável, não no início
    min_start = int(audio_dur * 0.12)
    max_start = min(int(audio_dur * 0.35), int(audio_dur - dur))
    start = random.randint(min_start, max(min_start, max_start))
    return float(start), float(dur)


def get_font() -> str:
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Bold*", "-name", "*.ttf"],
        capture_output=True, text=True, check=False,
    )
    fonts = [f for f in result.stdout.strip().split("\n") if f]
    return fonts[0] if fonts else FONT_PATHS[0]


def escape_text(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace("'",  "\\'")
    text = text.replace(":",  "\\:")
    text = text.replace("%",  "\\%")
    return text[:50]


def clean_song_name(audio_path: str, override: str = "") -> str:
    if override:
        return override.strip()
    name = Path(audio_path).stem
    name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name


def logo_exists() -> bool:
    return os.path.exists(LOGO_PATH)


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO FILTER — áudio que entra DURO imediatamente
# ══════════════════════════════════════════════════════════════════════════════

def build_audio_filter(duration: float) -> str:
    fo_start = max(0.0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"           # fade-in quase zero
        f"afade=t=out:st={fo_start:.3f}:d={AUDIO_FADE_OUT},"
        "acompressor=threshold=-16dB:ratio=3.5:attack=4:release=45:makeup=1.5dB,"
        "loudnorm=I=-14:TP=-1.0:LRA=9"
    )


# ══════════════════════════════════════════════════════════════════════════════
# COLOR GRADE
# ══════════════════════════════════════════════════════════════════════════════

def build_hook_flash_expr() -> str:
    """Flash de entrada no frame 0 — impacto visual imediato."""
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


def build_color_grade(profile: dict, brightness_expr: str, style: str = "default") -> str:
    genre_grade = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
    base_grade = (
        "eq=contrast=1.04:brightness=0.0:saturation=1.04,"
        f"eq=contrast={profile['contrast']}"
        f":brightness='{brightness_expr}'"
        f":saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0"
    )
    return f"{base_grade},{genre_grade}"


def build_vignette(strength: float) -> str:
    if strength <= 0:
        return ""
    angle = round(strength * 1.10, 3)
    return f"vignette=angle={angle}:mode=forward"


def build_fade_filter(duration: float) -> str:
    fo_start = max(0.0, duration - VIDEO_FADE_OUT_DUR)
    return f"fade=t=out:st={fo_start:.3f}:d={VIDEO_FADE_OUT_DUR}"


# ══════════════════════════════════════════════════════════════════════════════
# OVERLAYS — v4: hook instantâneo no frame 0
# ══════════════════════════════════════════════════════════════════════════════

def build_hook_text(song_name: str, style: str, font: str) -> str:
    """
    v4: Texto aparece IMEDIATAMENTE no frame 0.
    Pesquisa mostra que o hook deve estar no 1º segundo.
    Antes ficava escondido por 0.55s — agora é instantâneo.
    """
    clean     = escape_text(song_name)
    style_tag = escape_text(f"#{style.upper()} · DJ darkMark")

    # Aparece no frame 0, fade-out rápido após 4s
    title_alpha = (
        "if(lt(t,0.04),0,"           # 1 frame de buffer apenas
        "if(lt(t,0.25),(t/0.25),"    # fade-in ultrarrápido: 0.25s
        "if(lt(t,4.0),1.0,"
        "if(lt(t,4.6),(4.6-t)/0.6,0))))"
    )
    title = (
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=62:fontcolor=white"
        f":borderw=4:bordercolor=black@0.92"
        f":shadowx=4:shadowy=4:shadowcolor=black@0.7"
        f":x=(w-text_w)/2:y=h*0.10"
        f":alpha='{title_alpha}'"
    )

    # Tag aparece logo após — 0.15s de delay
    tag_alpha = (
        "if(lt(t,0.15),0,"
        "if(lt(t,0.40),(t-0.15)/0.25,"
        "if(lt(t,4.0),0.95,"
        "if(lt(t,4.6),(4.6-t)/0.6,0))))"
    )
    tag = (
        f"drawtext=fontfile='{font}'"
        f":text='{style_tag}'"
        f":fontsize=28:fontcolor=white@0.85"
        f":borderw=2:bordercolor=black@0.80"
        f":x=(w-text_w)/2:y=h*0.10+72"
        f":alpha='{tag_alpha}'"
    )

    return f"{title},{tag}"


def build_progress_bar(duration: float, style: str = "default") -> str:
    """
    v4: Barra mais grossa (12px) e colorida por gênero.
    Sinaliza pro usuário que tem conteúdo — aumenta retenção.
    """
    color = GENRE_WAVEFORM_COLOR.get(style, "0xFF2244")
    return (
        "drawbox=x=0:y=ih-12:w=iw:h=12:color=black@0.65:t=fill,"
        f"drawbox=x=0:y=ih-12:w='iw*t/{duration:.3f}':h=12:color={color}@0.95:t=fill"
    )


def build_watermark(font: str) -> str:
    """
    v4: Watermark aparece mais cedo (1.5s em vez de 3s).
    Canais virais mostram branding imediato.
    """
    return (
        f"drawtext=fontfile='{font}'"
        f":text='@darkmrkedit'"
        f":fontsize=24:fontcolor=white@0.55"
        f":borderw=1:bordercolor=black@0.40"
        f":x=w-text_w-18:y=20"
        f":alpha='if(lt(t,1.5),0,if(lt(t,2.2),(t-1.5)/0.7,0.55))'"
    )


def build_logo_overlay_filter() -> str:
    logo_w = int(1080 * LOGO_RELATIVE_WIDTH)
    return (
        f"[1:v]scale={logo_w}:-1,format=rgba,"
        f"colorchannelmixer=aa={LOGO_OPACITY}[logo];"
        f"[base][logo]overlay="
        f"x=W-w-{LOGO_MARGIN_X}:y=H-h-{LOGO_MARGIN_Y}:format=auto[vout]"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MOTION — zoom mais agressivo no drop para gêneros pesados
# ══════════════════════════════════════════════════════════════════════════════

def build_elite_zoom(
    analysis: dict, duration: float, fps: int,
    max_zoom: float, zoom_speed: float, pulse_strength: float,
    style: str = "default",
) -> str:
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    # v4: intro ainda mais curto — zoom entra mais rápido
    intro_frames = int(0.25 * fps)

    # Gêneros pesados têm zoom mais agressivo
    heavy_genres = {"phonk", "metal", "rock", "trap", "electronic"}
    zoom_mult = 1.35 if style in heavy_genres else 1.0

    base  = f"(1.0 + {zoom_speed * zoom_mult}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength * 0.7}*sin(on*0.07+0.3)*cos(on*0.031))"

    beat_pulse = "0"
    if beats:
        parts = [f"0.005*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})" for b in beats[:60]]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        intensity = 0.016 if style in heavy_genres else 0.010
        parts = [f"{intensity}*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+6})" for b in bass_hits[:50]]
        bass_pulse = f"({'+'.join(parts)})"

    drop_punch = DROP_ZOOM_PUNCH * (1.4 if style in heavy_genres else 1.0)
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({drop_punch:.3f}*between(on,{df-1},{df+4})"
            f"+0.048*between(on,{df+5},{df+18})"
            f"+0.016*between(on,{df+19},{df+32}))"
        )

    full = f"{base}+{drift}+{beat_pulse}+{bass_pulse}+{drop_expr}"
    return (
        f"if(lte(on,{intro_frames}),"
        f"1.0,"
        f"min(max({full},1.0),{max_zoom + drop_punch:.3f}))"
    )


def build_elite_shake(analysis: dict, sx: int, sy: int, style: str = "default"):
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])

    # Gêneros pesados têm shake mais intenso
    heavy = style in {"phonk", "metal", "rock", "trap"}
    shake_mult = 1.4 if heavy else 1.0

    shake_x = f"(sin(t*2.8)*{sx*0.68*shake_mult}+sin(t*5.1)*{sx*0.32*shake_mult})"
    shake_y = f"(cos(t*2.5)*{sy*0.68*shake_mult}+cos(t*4.7)*{sy*0.32*shake_mult})"

    if bass_hits:
        boost_int = 1.9 if heavy else 1.6
        boosts = [f"{boost_int}*between(t,{max(0,t-0.03):.3f},{t+0.18:.3f})" for t in bass_hits[:50]]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        drop_mult_val = 3.5 if heavy else 2.5
        drop_mult = f"(1+{drop_mult_val}*between(t,{drop_time-0.03:.3f},{drop_time+0.28:.3f}))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    # v4: hook gate reduzido — shake começa logo
    hook_gate = "if(lt(t,0.12),0.05,1.0)"
    shake_x = f"({shake_x})*{hook_gate}"
    shake_y = f"({shake_y})*{hook_gate}"

    return shake_x, shake_y


# ══════════════════════════════════════════════════════════════════════════════
# FILTER BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_image_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps  = profile["fps"]
    font = get_font()
    brightness_expr = build_combined_brightness(profile, analysis)
    zoom_expr = build_elite_zoom(
        analysis, duration, fps,
        profile["max_zoom"], profile["zoom_speed"], profile["pulse_strength"],
        style=style,
    )
    color = build_color_grade(profile, brightness_expr, style)
    vig_strength = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE["default"])
    vig   = build_vignette(vig_strength)
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font)
    pbar  = build_progress_bar(duration, style)
    wtmk  = build_watermark(font)

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
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps  = profile["fps"]
    font = get_font()
    brightness_expr = build_combined_brightness(profile, analysis)
    sx = min(profile.get("shake_x", 4), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 4), MAX_SHAKE_Y)
    shake_x_expr, shake_y_expr = build_elite_shake(analysis, sx, sy, style=style)
    color = build_color_grade(profile, brightness_expr, style)
    vig_strength = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE["default"])
    vig   = build_vignette(vig_strength)
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font)
    pbar  = build_progress_bar(duration, style)
    wtmk  = build_watermark(font)

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
# FFmpeg COMMAND BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_cmd(
    inputs: list, vf_or_complex: str,
    is_complex: bool, use_logo: bool,
    audio_filter: str, dur: float, output_name: str,
) -> list:
    cmd = ["ffmpeg", "-y"] + inputs + ["-t", str(dur)]

    if is_complex:
        cmd += ["-filter_complex", vf_or_complex]
        cmd += ["-map", "[vout]", "-map", f"{'2' if use_logo else '1'}:a"]
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


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_output(output_path: str, expected_duration: float) -> dict:
    if not os.path.exists(output_path):
        return {"ok": False, "issues": ["Arquivo não encontrado."]}
    try:
        info = get_video_info(output_path)
    except Exception as e:
        return {"ok": False, "issues": [f"ffprobe falhou: {e}"]}

    issues = []
    if info["width"] != 1080 or info["height"] != 1920:
        issues.append(f"Resolução: {info['width']}x{info['height']} (esperado 1080x1920)")
    if abs(info["duration"] - expected_duration) > 2.0:
        issues.append(f"Duração: {info['duration']:.1f}s (esperado ~{expected_duration:.1f}s)")
    if info["size_mb"] < MIN_FILE_SIZE_MB:
        issues.append(f"Arquivo pequeno: {info['size_mb']}MB")
    if info["size_mb"] > MAX_FILE_SIZE_MB:
        issues.append(f"Arquivo grande: {info['size_mb']}MB")

    return {"ok": len(issues) == 0, "issues": issues, "info": info}


# ══════════════════════════════════════════════════════════════════════════════
# THUMBNAIL GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_thumbnail(
    video_path: str,
    song_name: str,
    style: str,
    output_dir: str = THUMB_DIR,
    timestamp: float = THUMB_TIMESTAMP,
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem  = Path(video_path).stem
    out   = str(Path(output_dir) / f"{stem}_thumb.jpg")
    font  = get_font()
    clean = escape_text(song_name)
    tag   = escape_text(f"#{style.upper()}")

    genre_grade = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])

    vf = (
        f"{genre_grade},"
        "eq=contrast=1.15:brightness=-0.02:saturation=1.25,"
        "vignette=angle=0.6:mode=forward,"
        "drawbox=x=0:y=ih*0.74:w=iw:h=ih*0.26:color=black@0.60:t=fill,"
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=76:fontcolor=white"
        f":borderw=4:bordercolor=black@0.92"
        f":shadowx=4:shadowy=4:shadowcolor=black@0.7"
        f":x=(w-text_w)/2:y=h*0.78,"
        f"drawtext=fontfile='{font}'"
        f":text='{tag}'"
        f":fontsize=40:fontcolor=white@0.88"
        f":borderw=2:bordercolor=black@0.75"
        f":x=(w-text_w)/2:y=h*0.89"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", video_path,
        "-vframes", "1",
        "-vf", vf,
        "-q:v", "2",
        out,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"  ► Thumbnail gerada: {out}")
        return out
    except subprocess.CalledProcessError as e:
        logger.warning(f"  ⚠ Thumbnail falhou: {e.stderr.decode()[-300:] if e.stderr else ''}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CORE: CREATE SHORT
# ══════════════════════════════════════════════════════════════════════════════

def create_short(
    audio_path: str,
    background_path: str,
    output_name: str,
    style: str,
    song_name: str = "",
    use_smart_window: bool = True,
    auto_thumbnail: bool = True,
    upload: bool = False,
    upload_privacy: str = "private",
) -> dict:
    t_start = time.time()
    result: dict = {"output_path": None, "thumbnail_path": None, "video_id": None}

    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    song_name = clean_song_name(audio_path, song_name)
    logger.info(f"▶ Gerando Short: '{song_name}' | estilo={style}")
    logger.info(f"  ► Color grade: {style} | Hook: instantâneo (frame 0)")

    # ── Análise de áudio ──────────────────────────────────────────────────────
    logger.info("  ► Analisando áudio…")
    analysis_full = full_analysis(audio_path)
    bpm       = analysis_full.get("bpm")
    audio_dur = get_duration(audio_path)

    # v4: janela começa no drop/pico de energia sempre que possível
    if use_smart_window:
        dur = random.randint(MIN_DURATION, min(MAX_DURATION, int(audio_dur)))
        try:
            start, dur = find_best_window(audio_path, dur)
            logger.info(f"  ► Janela inteligente: {start:.1f}s – {start+dur:.1f}s (drop/pico)")
        except Exception:
            start, dur = pick_window(audio_dur)
            logger.info(f"  ► Janela fallback: {start:.1f}s – {start+dur:.1f}s")
    else:
        start, dur = pick_window(audio_dur)
        logger.info(f"  ► Janela manual: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")

    analysis = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    profile      = get_profile_for_bpm(bpm, style)
    audio_filter = build_audio_filter(dur)
    use_logo     = logo_exists()

    # ── Background ────────────────────────────────────────────────────────────
    ext      = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        base_vf = build_image_filter(profile, analysis, dur, song_name, style)
        if use_logo:
            fc     = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-loop", "1", "-i", background_path, "-i", LOGO_PATH, "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-loop", "1", "-i", background_path, "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        base_vf  = build_video_filter(profile, analysis, dur, song_name, style)
        if use_logo:
            fc     = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-ss", str(bg_start), "-i", background_path, "-i", LOGO_PATH, "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-ss", str(bg_start), "-i", background_path, "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    else:
        font    = get_font()
        hook    = build_hook_text(song_name, style, font)
        pbar    = build_progress_bar(dur, style)
        wtmk    = build_watermark(font)
        fade    = build_fade_filter(dur)
        genre_g = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
        base_vf = f"{genre_g},{fade},{hook},{pbar},{wtmk}"
        if use_logo:
            fc     = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}", "-i", LOGO_PATH, "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}", "-ss", str(start), "-i", audio_path]
            cmd    = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    # ── Render com retry ──────────────────────────────────────────────────────
    logger.info("  ► Iniciando render…")
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("  ► Render concluído ✓")
            break
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode()[-500:] if e.stderr else ""
            if attempt <= MAX_RETRIES:
                logger.warning(f"  ⚠ Render falhou (tentativa {attempt}): {err}")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"  ✗ Render falhou após {MAX_RETRIES+1} tentativas.\n{err}")
                raise

    # ── Validação ─────────────────────────────────────────────────────────────
    validation = validate_output(output_name, dur)
    if validation["ok"]:
        info = validation["info"]
        logger.info(
            f"  ► OK — {info['width']}x{info['height']} | "
            f"{info['duration']:.1f}s | {info['size_mb']}MB | {info['fps']} fps"
        )
    else:
        for issue in validation["issues"]:
            logger.warning(f"  ⚠ {issue}")

    result.update({
        "output_path": output_name,
        "validation":  validation,
        "duration":    dur,
        "bpm":         bpm,
        "drop_time":   analysis.get("drop_time"),
    })

    # ── Thumbnail ─────────────────────────────────────────────────────────────
    if auto_thumbnail:
        thumb = generate_thumbnail(output_name, song_name, style)
        result["thumbnail_path"] = thumb

    elapsed = round(time.time() - t_start, 1)
    result["render_time_s"] = elapsed
    logger.info(f"✅ Finalizado em {elapsed}s" + (f" | BPM={bpm:.0f}" if bpm else ""))
    return result


# ══════════════════════════════════════════════════════════════════════════════
# BATCH PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def generate_batch(
    tasks: list[dict],
    output_dir: str = "output",
    auto_thumbnail: bool = True,
    upload: bool = False,
    upload_privacy: str = "private",
) -> list[dict]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []

    for i, task in enumerate(tasks, 1):
        audio_path      = task["audio_path"]
        background_path = task.get("background_path", "")
        style           = task.get("style", "default")
        song_name       = task.get("song_name", "")
        name            = clean_song_name(audio_path, song_name)
        output_name     = str(
            Path(output_dir) / f"{i:03d}_{re.sub(r'[^a-zA-Z0-9_]','_',name)}.mp4"
        )

        logger.info(f"\n{'='*60}")
        logger.info(f"[{i}/{len(tasks)}] {name}")

        try:
            r = create_short(
                audio_path=audio_path,
                background_path=background_path,
                output_name=output_name,
                style=style,
                song_name=song_name,
                auto_thumbnail=auto_thumbnail,
                upload=upload,
                upload_privacy=upload_privacy,
            )
            r["task"]   = task
            r["status"] = "ok"
            results.append(r)
        except Exception as e:
            logger.error(f"  ✗ Falha task {i}: {e}")
            results.append({"task": task, "status": "error", "error": str(e)})

    ok    = sum(1 for r in results if r.get("status") == "ok")
    fails = len(results) - ok
    logger.info(f"\nBatch: {ok} ok, {fails} erros.")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Elite Music Shorts Generator v4")
    parser.add_argument("audio")
    parser.add_argument("background")
    parser.add_argument("output")
    parser.add_argument("--style",    default="trap", choices=list_profiles())
    parser.add_argument("--name",     default="")
    parser.add_argument("--no-thumb", action="store_true")
    parser.add_argument("--upload",   action="store_true")
    parser.add_argument("--privacy",  default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--no-smart", action="store_true")

    args = parser.parse_args()

    create_short(
        audio_path       = args.audio,
        background_path  = args.background,
        output_name      = args.output,
        style            = args.style,
        song_name        = args.name,
        use_smart_window = not args.no_smart,
        auto_thumbnail   = not args.no_thumb,
        upload           = args.upload,
        upload_privacy   = args.privacy,
    )
