"""
video_generator.py — Elite Music Shorts Generator v2

Upgrades:
- Python logging profissional (arquivo + console)
- find_best_window() via audio scoring (libros a)
- Thumbnail automática (FFmpeg + overlays)
- YouTube Data API v3 upload (opcional, requer token)
- Retry automático em falha de render
- Validação do output (duração, resolução, tamanho)
- BPM-aware profile selection
- Batch processing via generate_batch()
- Métricas de render (tempo, tamanho, qualidade estimada)
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
# LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """Configura logging para arquivo e console."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "generator.log"

    fmt = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
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
MAX_DURATION        = 48
VIDEO_FADE_OUT_DUR  = 1.0
AUDIO_FADE_IN       = 0.15
AUDIO_FADE_OUT      = 0.9
HOOK_FLASH_BRIGHTNESS = 0.28
HOOK_FLASH_DECAY    = 0.12
MAX_SHAKE_X         = 8
MAX_SHAKE_Y         = 8
DROP_ZOOM_PUNCH     = 0.08

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FFMPEG_VIDEO_CODEC  = "libx264"
FFMPEG_CRF          = "19"
FFMPEG_PRESET       = "medium"
FFMPEG_AUDIO_CODEC  = "aac"
FFMPEG_AUDIO_BITRATE = "192k"

LOGO_PATH            = "assets/logo_darkmark.png"
LOGO_RELATIVE_WIDTH  = 0.10
LOGO_MARGIN_X        = 22
LOGO_MARGIN_Y        = 110
LOGO_OPACITY         = 0.88

# Thumbnail
THUMB_DIR            = "thumbnails"
THUMB_WIDTH          = 1080
THUMB_HEIGHT         = 1920
THUMB_TIMESTAMP      = 3.0   # segundos do vídeo para capturar frame

# Render retries
MAX_RETRIES          = 2
RETRY_DELAY_S        = 3

# Output validation
MIN_FILE_SIZE_MB     = 0.5
MAX_FILE_SIZE_MB     = 200.0


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
    """Retorna {width, height, duration, fps, size_mb}."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration,size",
        "-of", "json", path,
    ]
    import json
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)

    stream = data.get("streams", [{}])[0]
    fmt    = data.get("format", {})

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
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p

    result = subprocess.run(
        ["find", "/usr/share/fonts", "-name", "*Bold*", "-name", "*.ttf"],
        capture_output=True, text=True, check=False,
    )
    fonts = [f for f in result.stdout.strip().split("\n") if f]
    if fonts:
        return fonts[0]

    logger.warning("Nenhuma fonte Bold encontrada — usando default.")
    return FONT_PATHS[0]


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
# AUDIO FILTER
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
# COLOR / BRIGHTNESS
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
    clean     = escape_text(song_name)
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
        f":fontsize=58:fontcolor=white"
        f":borderw=3:bordercolor=black@0.88"
        f":shadowx=3:shadowy=3:shadowcolor=black@0.6"
        f":x=(w-text_w)/2:y=h*0.11"
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
        f":fontsize=30:fontcolor=white@0.82"
        f":borderw=2:bordercolor=black@0.75"
        f":x=(w-text_w)/2:y=h*0.11+68"
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
        f":fontsize=22:fontcolor=white@0.50"
        f":borderw=1:bordercolor=black@0.35"
        f":x=w-text_w-18:y=18"
        f":alpha='if(lt(t,3.0),0,if(lt(t,3.8),(t-3.0)/0.8,0.50))'"
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
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.45 * fps)

    base  = f"(1.0 + {zoom_speed}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = f"({pulse_strength * 0.7}*sin(on*0.07+0.3)*cos(on*0.031))"

    beat_pulse = "0"
    if beats:
        parts = [
            f"0.004*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+4})"
            for b in beats[:60]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        parts = [
            f"0.010*between(on,{max(0,int(b*fps)-1)},{int(b*fps)+6})"
            for b in bass_hits[:50]
        ]
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
        boosts = [
            f"1.6*between(t,{max(0,t-0.03):.3f},{t+0.18:.3f})"
            for t in bass_hits[:50]
        ]
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
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps  = profile["fps"]
    font = get_font()
    brightness_expr = build_combined_brightness(profile, analysis)
    zoom_expr = build_elite_zoom(
        analysis, duration, fps,
        profile["max_zoom"], profile["zoom_speed"], profile["pulse_strength"],
    )
    color = build_color_grade(profile, brightness_expr)
    vig   = build_vignette(profile.get("vignette", 0.4))
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font)
    pbar  = build_progress_bar(duration)
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
    shake_x_expr, shake_y_expr = build_elite_shake(analysis, sx, sy)
    color = build_color_grade(profile, brightness_expr)
    vig   = build_vignette(profile.get("vignette", 0.4))
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font)
    pbar  = build_progress_bar(duration)
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
    """
    Valida o vídeo gerado.
    Retorna dict com 'ok' (bool) e 'issues' (list).
    """
    issues = []

    if not os.path.exists(output_path):
        return {"ok": False, "issues": ["Arquivo não encontrado."]}

    try:
        info = get_video_info(output_path)
    except Exception as e:
        return {"ok": False, "issues": [f"ffprobe falhou: {e}"]}

    # Resolução
    if info["width"] != 1080 or info["height"] != 1920:
        issues.append(f"Resolução incorreta: {info['width']}x{info['height']} (esperado 1080x1920)")

    # Duração (tolerância ±2s)
    if abs(info["duration"] - expected_duration) > 2.0:
        issues.append(
            f"Duração incorreta: {info['duration']:.1f}s (esperado ~{expected_duration:.1f}s)"
        )

    # Tamanho
    if info["size_mb"] < MIN_FILE_SIZE_MB:
        issues.append(f"Arquivo muito pequeno: {info['size_mb']}MB")
    if info["size_mb"] > MAX_FILE_SIZE_MB:
        issues.append(f"Arquivo muito grande: {info['size_mb']}MB")

    result = {
        "ok": len(issues) == 0,
        "issues": issues,
        "info": info,
    }
    return result


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
    """
    Gera thumbnail do Short: frame capturado + overlay de título.
    Retorna o caminho da thumbnail ou None em caso de erro.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem  = Path(video_path).stem
    out   = str(Path(output_dir) / f"{stem}_thumb.jpg")
    font  = get_font()
    clean = escape_text(song_name)
    tag   = escape_text(f"#{style.upper()}")

    vf = (
        # Grade escura para destacar o texto
        "eq=contrast=1.12:brightness=-0.02:saturation=1.22,"
        "vignette=angle=0.6:mode=forward,"
        # Faixa semi-transparente no rodapé
        "drawbox=x=0:y=ih*0.75:w=iw:h=ih*0.25:color=black@0.55:t=fill,"
        # Título centralizado
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=72:fontcolor=white"
        f":borderw=4:bordercolor=black@0.9"
        f":shadowx=4:shadowy=4:shadowcolor=black@0.7"
        f":x=(w-text_w)/2:y=h*0.78,"
        # Tag de estilo
        f"drawtext=fontfile='{font}'"
        f":text='{tag}'"
        f":fontsize=38:fontcolor=white@0.85"
        f":borderw=2:bordercolor=black@0.7"
        f":x=(w-text_w)/2:y=h*0.88"
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
        logger.warning(f"  ⚠ Falha ao gerar thumbnail: {e.stderr.decode()[-300:]}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# YOUTUBE UPLOAD (opcional)
# ══════════════════════════════════════════════════════════════════════════════

def upload_to_youtube(
    video_path: str,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    category_id: str = "10",          # Music
    privacy: str = "private",         # private | unlisted | public
    credentials_file: str = "client_secrets.json",
) -> Optional[str]:
    """
    Faz upload para o YouTube via googleapiclient.
    Requer: pip install google-api-python-client google-auth-oauthlib
    Retorna o video_id ou None em caso de erro.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.error(
            "google-api-python-client não instalado. "
            "Execute: pip install google-api-python-client google-auth-oauthlib"
        )
        return None

    token_file = "token.json"
    if not os.path.exists(token_file):
        logger.error(f"Token OAuth não encontrado: {token_file}")
        return None

    try:
        creds = Credentials.from_authorized_user_file(token_file)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": (tags or [])[:500],
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy},
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,   # 10MB chunks
        )

        logger.info(f"  ► Iniciando upload para YouTube: '{title}'…")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                logger.info(f"     Upload: {pct}%")

        video_id = response.get("id")
        logger.info(f"  ► Upload concluído! https://youtu.be/{video_id}")
        return video_id

    except Exception as e:
        logger.error(f"  ✗ Erro no upload: {e}")
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
    """
    Gera um YouTube Short.

    Retorna dict com:
        output_path, thumbnail_path, video_id (se upload=True),
        duration, bpm, drop_time, render_time_s, validation
    """
    t_start = time.time()
    result: dict = {"output_path": None, "thumbnail_path": None, "video_id": None}

    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    song_name = clean_song_name(audio_path, song_name)
    logger.info(f"▶ Gerando Short: '{song_name}' | estilo={style}")

    # ── Análise de áudio ───────────────────────────────────────────────────────
    logger.info("  ► Analisando áudio…")
    analysis_full = full_analysis(audio_path)
    bpm      = analysis_full.get("bpm")
    audio_dur = get_duration(audio_path)

    # Selecionar janela
    if use_smart_window:
        dur = random.randint(MIN_DURATION, min(MAX_DURATION, int(audio_dur)))
        start, dur = find_best_window(audio_path, dur)
    else:
        start, dur = pick_window(audio_dur)

    logger.info(f"  ► Janela: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")
    analysis = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    # Profile (BPM-aware)
    profile       = get_profile_for_bpm(bpm, style)
    audio_filter  = build_audio_filter(dur)
    use_logo      = logo_exists()

    # ── Background ────────────────────────────────────────────────────────────
    ext      = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        base_vf = build_image_filter(profile, analysis, dur, song_name, style)
        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = [
                "-loop", "1", "-i", background_path,
                "-i", LOGO_PATH,
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = [
                "-loop", "1", "-i", background_path,
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        base_vf  = build_video_filter(profile, analysis, dur, song_name, style)
        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = [
                "-ss", str(bg_start), "-i", background_path,
                "-i", LOGO_PATH,
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = [
                "-ss", str(bg_start), "-i", background_path,
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

    else:
        # Fundo preto
        font    = get_font()
        hook    = build_hook_text(song_name, style, font)
        pbar    = build_progress_bar(dur)
        wtmk    = build_watermark(font)
        fade    = build_fade_filter(dur)
        base_vf = f"{fade},{hook},{pbar},{wtmk}"
        if use_logo:
            fc = f"[0:v]{base_vf}[base];{build_logo_overlay_filter()}"
            inputs = [
                "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
                "-i", LOGO_PATH,
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name)
        else:
            inputs = [
                "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
                "-ss", str(start), "-i", audio_path,
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name)

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
                logger.warning(f"  ⚠ Render falhou (tentativa {attempt}/{MAX_RETRIES+1}): {err}")
                logger.info(f"  Aguardando {RETRY_DELAY_S}s antes de nova tentativa…")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"  ✗ Render falhou após {MAX_RETRIES+1} tentativas.\n{err}")
                raise

    # ── Validação ─────────────────────────────────────────────────────────────
    validation = validate_output(output_name, dur)
    if validation["ok"]:
        info = validation["info"]
        logger.info(
            f"  ► Validação OK — {info['width']}x{info['height']} | "
            f"{info['duration']:.1f}s | {info['size_mb']}MB | {info['fps']} fps"
        )
    else:
        for issue in validation["issues"]:
            logger.warning(f"  ⚠ {issue}")

    result["output_path"] = output_name
    result["validation"]  = validation
    result["duration"]    = dur
    result["bpm"]         = bpm
    result["drop_time"]   = analysis.get("drop_time")

    # ── Thumbnail ─────────────────────────────────────────────────────────────
    if auto_thumbnail:
        thumb = generate_thumbnail(output_name, song_name, style)
        result["thumbnail_path"] = thumb

    # ── Upload (opcional) ─────────────────────────────────────────────────────
    if upload:
        tags = [style, "shorts", "music", song_name.lower()]
        vid_id = upload_to_youtube(
            output_name,
            title=f"{song_name} 🔥 #{style.upper()} #SHORTS",
            description=f"#{style} #shorts #music\n\nFollow for more!",
            tags=tags,
            privacy=upload_privacy,
        )
        result["video_id"] = vid_id

    # ── Métricas ──────────────────────────────────────────────────────────────
    elapsed = round(time.time() - t_start, 1)
    result["render_time_s"] = elapsed
    logger.info(
        f"✅ Finalizado em {elapsed}s | "
        f"BPM={bpm:.0f}" if bpm else f"✅ Finalizado em {elapsed}s"
    )
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
    """
    Processa múltiplos vídeos em sequência.

    Cada task deve ter:
        audio_path, background_path, style, song_name (opcional)

    Retorna lista de resultados.
    """
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
            r["task"] = task
            r["status"] = "ok"
            results.append(r)
        except Exception as e:
            logger.error(f"  ✗ Falha no task {i}: {e}")
            results.append({"task": task, "status": "error", "error": str(e)})

    ok    = sum(1 for r in results if r.get("status") == "ok")
    fails = len(results) - ok
    logger.info(f"\n{'='*60}")
    logger.info(f"Batch finalizado: {ok} ok, {fails} erros.")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Elite Music Shorts Generator")
    parser.add_argument("audio",       help="Caminho do áudio (.mp3/.wav)")
    parser.add_argument("background",  help="Imagem ou vídeo de fundo")
    parser.add_argument("output",      help="Nome do arquivo de saída (.mp4)")
    parser.add_argument(
        "--style", default="trap",
        choices=list_profiles(),
        help="Estilo de edição (default: trap)",
    )
    parser.add_argument("--name",      default="", help="Nome da música (opcional)")
    parser.add_argument("--no-thumb",  action="store_true", help="Desativa geração de thumbnail")
    parser.add_argument("--upload",    action="store_true", help="Faz upload para o YouTube")
    parser.add_argument("--privacy",   default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--no-smart",  action="store_true", help="Usa janela aleatória (sem scoring)")

    args = parser.parse_args()

    create_short(
        audio_path      = args.audio,
        background_path = args.background,
        output_name     = args.output,
        style           = args.style,
        song_name       = args.name,
        use_smart_window = not args.no_smart,
        auto_thumbnail  = not args.no_thumb,
        upload          = args.upload,
        upload_privacy  = args.privacy,
    )
