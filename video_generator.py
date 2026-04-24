"""
video_generator.py — Elite Music Shorts Generator v8.0 VIRAL CONTROL
=========================================================================
MUDANÇAS v8.0 (VIRAL CONTROL — 15M STYLE):
- FFmpeg agora gera uma base cyberpunk LIMPA e forte, sem brigar com o Remotion.
- Efeitos pesados foram reduzidos fora do drop: menos poluição visual, mais retenção.
- Scanlines, borda neon, water FX e glitch ficaram mais sutis.
- Flash/drop continua forte, mas mais controlado e cinematográfico.
- CRF ajustado para arquivo menor e render mais estável no GitHub Actions.
- Progress bar removida do FFmpeg para não competir com o Remotion.
- Filosofia: calmo → build → DROP → impacto, igual Shorts virais de 15M+.
- Remotion continua sendo responsável por logo, texto, partículas, túnel e glow final
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

try:
    from audio_to_remotion import generate_audio_data
    _REMOTION_AVAILABLE = True
except ImportError:
    _REMOTION_AVAILABLE = False


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "generator.log"
    fmt = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
    logging.basicConfig(
        level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

setup_logging()
logger = logging.getLogger("video_generator")

# ── Parâmetros gerais ──────────────────────────────────────────────────────
MIN_DURATION        = 45
MAX_DURATION        = 60
VIDEO_FADE_OUT_DUR  = 0.5
AUDIO_FADE_IN       = 0.03
AUDIO_FADE_OUT      = 0.7
MAX_SHAKE_X         = 10
MAX_SHAKE_Y         = 10
DROP_ZOOM_PUNCH     = 0.18

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FFMPEG_VIDEO_CODEC   = "libx264"
FFMPEG_CRF           = "23"
FFMPEG_PRESET        = "medium"
FFMPEG_AUDIO_CODEC   = "aac"
FFMPEG_AUDIO_BITRATE = "192k"

LOGO_PATH = "assets/logo_darkmark.png"
LOGO_BASE_WIDTH_RATIO = 0.22
LOGO_CENTER_Y_RATIO = 0.50
LOGO_OPACITY = 0.92
LOGO_GLOW_SCALE      = 1.45
LOGO_GLOW_BLUR       = 14
LOGO_GLOW_OPACITY    = 0.52
LOGO_GLOW_BRIGHTNESS = 3.2
LOGO_PULSE_BEAT_STRENGTH = 0.06
LOGO_PULSE_BASS_STRENGTH = 0.20
LOGO_PULSE_DROP_STRENGTH = 0.38
LOGO_PULSE_BEAT_DECAY = 0.10
LOGO_PULSE_BASS_DECAY = 0.08
LOGO_PULSE_DROP_DECAY = 0.30
LOGO_MAX_BEATS     = 10
LOGO_MAX_BASS_HITS = 6

THUMB_DIR       = "thumbnails"
THUMB_TIMESTAMP = 1.5
MAX_RETRIES     = 2
RETRY_DELAY_S   = 3
MIN_FILE_SIZE_MB = 0.5
MAX_FILE_SIZE_MB = 350.0

# ══════════════════════════════════════════════════════════════════════════════
# COLOR GRADES — v8.0 CYBERPUNK MÁXIMO
# Filosofia: fundo escuro como breu, neon explodindo, contraste brutal
# ══════════════════════════════════════════════════════════════════════════════
GENRE_COLOR_GRADE = {
    "phonk": (
        # Base escura + roxo profundo + vermelho sangue + grain cinematográfico
        "colorbalance=rs=0.35:gs=-0.20:bs=-0.25:shadows=enable,"
        "colorbalance=rs=-0.15:gs=0.05:bs=0.40:highlights=enable,"
        "eq=contrast=1.48:brightness=-0.075:saturation=1.35:gamma=0.92,"
        "curves=r='0/0 0.2/0.05 0.7/0.65 1/1':g='0/0 0.3/0.10 1/0.80':b='0/0 0.2/0.30 1/1',"
        "unsharp=7:7:2.2:7:7:0,"
        "noise=alls=20:allf=t+u"
    ),
    "trap": (
        # Azul gelo + ciano neon + preto profundo
        "colorbalance=rs=-0.25:gs=0.08:bs=0.45:shadows=enable,"
        "colorbalance=rs=-0.10:gs=0.15:bs=0.30:highlights=enable,"
        "eq=contrast=1.42:brightness=-0.065:saturation=1.32:gamma=0.93,"
        "curves=r='0/0 0.3/0.08 1/0.85':b='0/0 0.1/0.25 0.7/0.85 1/1',"
        "unsharp=5:5:1.8:5:5:0"
    ),
    "dark": (
        # Roxo puro + quase sem luz — máximo sinistro
        "colorbalance=rs=-0.10:gs=-0.15:bs=0.55:shadows=enable,"
        "colorbalance=rs=0.05:gs=-0.05:bs=0.25:highlights=enable,"
        "eq=contrast=1.50:brightness=-0.105:saturation=0.92:gamma=0.90,"
        "curves=all='0/0 0.15/0.02 0.5/0.35 1/1',"
        "unsharp=5:5:1.5:5:5:0,"
        "vignette=angle=PI/2.2:mode=forward"
    ),
    "electronic": (
        # Ciano + magenta — bifurcação neon
        "colorbalance=rs=-0.20:gs=0.15:bs=0.38:shadows=enable,"
        "colorbalance=rs=0.30:gs=-0.10:bs=0.20:highlights=enable,"
        "eq=contrast=1.40:brightness=-0.055:saturation=1.50:gamma=0.94,"
        "unsharp=5:5:1.2:5:5:0"
    ),
    "lofi": (
        "colorbalance=rs=0.15:gs=0.05:bs=-0.20,"
        "eq=contrast=0.90:brightness=0.020:saturation=0.75,"
        "unsharp=3:3:0.3:3:3:0,"
        "noise=alls=8:allf=t"
    ),
    "rock": (
        "colorbalance=rs=0.20:gs=0.06:bs=-0.15,"
        "eq=contrast=1.40:brightness=0.004:saturation=1.30,"
        "unsharp=5:5:1.5:5:5:0,"
        "noise=alls=14:allf=t"
    ),
    "metal": (
        "colorbalance=rs=-0.18:gs=-0.12:bs=0.15,"
        "eq=contrast=1.60:brightness=-0.10:saturation=0.70,"
        "unsharp=5:5:1.6:5:5:0,"
        "vignette=angle=PI/2.5:mode=forward"
    ),
    "indie": (
        "colorbalance=rs=0.08:gs=0.05:bs=-0.10,"
        "eq=contrast=0.95:brightness=0.018:saturation=0.85,"
        "noise=alls=5:allf=t"
    ),
    "cinematic": (
        "colorbalance=rs=0.16:gs=-0.04:bs=-0.20,"
        "eq=contrast=1.22:brightness=0.003:saturation=1.08,"
        "unsharp=5:5:1.0:5:5:0"
    ),
    "funk": (
        "colorbalance=rs=0.28:gs=0.10:bs=-0.22,"
        "eq=contrast=1.22:brightness=0.012:saturation=1.60,"
        "unsharp=3:3:0.6:3:3:0"
    ),
    "pop": (
        "colorbalance=rs=0.06:gs=0.05:bs=0.06,"
        "eq=contrast=1.12:brightness=0.018:saturation=1.45,"
        "unsharp=3:3:0.7:3:3:0"
    ),
    "default": (
        "colorbalance=rs=-0.08:gs=-0.05:bs=0.30:shadows=enable,"
        "eq=contrast=1.55:brightness=-0.08:saturation=1.40:gamma=0.88,"
        "unsharp=5:5:1.2:5:5:0"
    ),
}

GENRE_VIGNETTE = {
    "phonk": 0.80, "dark": 0.0, "metal": 0.0, "lofi": 0.35,
    "trap": 0.55, "electronic": 0.40, "rock": 0.45, "indie": 0.28,
    "cinematic": 0.50, "funk": 0.18, "pop": 0.15, "default": 0.50,
}

GENRE_ENERGY_COLOR = {
    "phonk":      "0xFF1122",
    "trap":       "0x00CCFF",
    "dark":       "0x8800FF",
    "electronic": "0x00FFEE",
    "metal":      "0xFF5500",
    "rock":       "0xFF8800",
    "lofi":       "0xFFAA44",
    "indie":      "0xFFDD88",
    "cinematic":  "0xFFBB44",
    "funk":       "0xFF8800",
    "pop":        "0xFF44AA",
    "default":    "0xCC44FF",
}

GENRE_ENERGY_RGBA = {
    "phonk":      "red@0.9",
    "trap":       "cyan@0.85",
    "dark":       "0x8800FF@0.9",
    "electronic": "0x00FFEE@0.9",
    "metal":      "0xFF5500@0.9",
    "rock":       "0xFF8800@0.85",
    "lofi":       "0xFFAA44@0.8",
    "indie":      "0xFFDD88@0.75",
    "cinematic":  "0xFFBB44@0.85",
    "funk":       "0xFF8800@0.9",
    "pop":        "0xFF44AA@0.85",
    "default":    "0xCC44FF@0.9",
}

# Cores neon por gênero para efeitos cyberpunk
GENRE_NEON = {
    "phonk":      {"c1": "0xFF0066", "c2": "0x8800FF", "c3": "0xFF2200"},
    "trap":       {"c1": "0x00CCFF", "c2": "0xCC44FF", "c3": "0x00FFEE"},
    "dark":       {"c1": "0x8800FF", "c2": "0x00FFEE", "c3": "0xFF0088"},
    "electronic": {"c1": "0x00FFEE", "c2": "0xFF00CC", "c3": "0x00AAFF"},
    "metal":      {"c1": "0xFF5500", "c2": "0xCC44FF", "c3": "0x00CCFF"},
    "rock":       {"c1": "0xFF8800", "c2": "0xFF0044", "c3": "0xCC44FF"},
    "lofi":       {"c1": "0xFFAA44", "c2": "0xFF6688", "c3": "0xAA88FF"},
    "default":    {"c1": "0xCC44FF", "c2": "0x00FFEE", "c3": "0xFF0088"},
}

WATER_FX_ENABLED = True
WATER_FX_START_Y_RATIO = 0.54
WATER_FX_BASE_ALPHA = 0.025
WATER_FX_LINE_ALPHA = 0.10
WATER_FX_BASS_ALPHA = 0.08
WATER_FX_MAX_BASS_HITS = 22

# Controle viral: efeitos de FFmpeg servem como base, não como protagonista.
# O protagonista final é o Remotion.
VIRAL_FX_MODE = True
KEEP_FFMPEG_PROGRESS_BAR = False
SCANLINE_BASE_ALPHA = 0.025
SCANLINE_BASS_ALPHA = 0.10
GLITCH_MAX_HITS = 10
BORDER_MAX_HITS = 16



# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
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
    import json
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration,size",
        "-of", "json", path,
    ]
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
    if audio_dur <= MIN_DURATION:
        return 0.0, float(audio_dur)
    max_allowed = min(MAX_DURATION, int(audio_dur))
    dur = random.randint(MIN_DURATION, max_allowed)
    if audio_dur <= dur:
        return 0.0, float(audio_dur)
    min_start = int(audio_dur * 0.12)
    max_start = min(int(audio_dur * 0.45), int(audio_dur - dur))
    if max_start <= min_start:
        start = max(0, int(audio_dur - dur))
    else:
        start = random.randint(min_start, max_start)
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
    text = text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")
    return text[:50]


def join_filters(parts: list[str]) -> str:
    return ",".join([p for p in parts if p and str(p).strip()])


def clean_song_name(audio_path: str, override: str = "") -> str:
    if override:
        return override.strip()
    name = Path(audio_path).stem
    name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name


def logo_exists() -> bool:
    """Logo fica no Remotion — FFmpeg gera base limpa."""
    return False


# ══════════════════════════════════════════════════════════════════════════════
# EFEITOS CYBERPUNK v8.0
# ══════════════════════════════════════════════════════════════════════════════

def build_scanlines(analysis: dict, style: str = "default") -> str:
    """
    Scanlines v8 — bem sutis fora do drop.
    Objetivo: textura premium, não poluição visual.
    """
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]

    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])[:12]

    lines = []

    # Base quase imperceptível
    lines.append(
        f"drawbox=x=0:y='mod(t*90,ih)':w=iw:h=1:color={c1}@{SCANLINE_BASE_ALPHA:.3f}:t=fill"
    )
    lines.append(
        f"drawbox=x=0:y='mod(t*90+ih/2,ih)':w=iw:h=1:color={c1}@{SCANLINE_BASE_ALPHA*0.75:.3f}:t=fill"
    )

    # Pulsos leves em alguns bass hits
    for bt in bass_hits:
        t0 = max(0.0, bt - 0.006)
        t1 = bt + 0.035
        lines.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y='mod(t*100,ih)':w=iw:h=2:color={c1}@{SCANLINE_BASS_ALPHA:.3f}:t=fill"
        )

    # Drop scan: curto e forte, só no impacto
    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.008)
        t1 = drop_time + 0.075
        lines.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=white@0.08:t=fill"
        )

    return ",".join(lines)


def build_drop_flash(analysis: dict) -> str:
    """
    Flash v8 — impacto forte, mas cinematográfico.
    Branco total muito longo mata retenção; aqui ele bate e some rápido.
    """
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])[:24]

    flashes = []

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.006)
        flashes.append(
            f"drawbox=enable='between(t,{t0:.4f},{drop_time+0.035:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=white@0.62:t=fill"
        )
        flashes.append(
            f"drawbox=enable='between(t,{drop_time+0.035:.4f},{drop_time+0.105:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=0x8800FF@0.24:t=fill"
        )
        flashes.append(
            f"drawbox=enable='between(t,{drop_time+0.105:.4f},{drop_time+0.180:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=0x00FFEE@0.10:t=fill"
        )

    # Micro flashes só nos bass hits principais
    for bt in bass_hits:
        if drop_time is not None and abs(bt - drop_time) < 0.7:
            continue
        t0 = max(0.0, bt - 0.004)
        flashes.append(
            f"drawbox=enable='between(t,{t0:.4f},{bt+0.022:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=white@0.055:t=fill"
        )

    return ",".join(flashes) if flashes else ""


def build_neon_border_pulse(analysis: dict, style: str = "default") -> str:
    """
    Borda neon v8 — respira de leve e explode apenas no drop.
    """
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]

    bass_hits = analysis.get("bass_hits", [])[:BORDER_MAX_HITS]
    drop_time = analysis.get("drop_time")

    borders = []

    # Base discreta
    borders.append(f"drawbox=x=0:y=0:w=2:h=ih:color={c1}@0.07:t=fill")
    borders.append(f"drawbox=x=iw-2:y=0:w=2:h=ih:color={c2}@0.07:t=fill")

    # Bass hits: bem mais seletivo
    for bt in bass_hits:
        t0 = max(0.0, bt - 0.006)
        t1 = bt + 0.040
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=7:h=ih:color={c1}@0.22:t=fill"
        )
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-7:y=0:w=7:h=ih:color={c2}@0.22:t=fill"
        )

    # Drop: borda explode curta
    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.008)
        t1 = drop_time + 0.120
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=20:h=ih:color={c1}@0.62:t=fill"
        )
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-20:y=0:w=20:h=ih:color={c2}@0.62:t=fill"
        )
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=10:color={c2}@0.45:t=fill"
        )
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih-10:w=iw:h=10:color={c1}@0.45:t=fill"
        )

    return ",".join(borders)


def build_glitch_slices(analysis: dict, style: str = "default") -> str:
    """
    Glitch v8 — só em drops e bass hits principais.
    Menos constante = mais impacto.
    """
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c3 = neon["c3"]

    bass_hits = analysis.get("bass_hits", [])[:GLITCH_MAX_HITS]
    drop_time = analysis.get("drop_time")

    glitches = []

    # Glitch pequeno só em poucos bass hits
    for i, bt in enumerate(bass_hits):
        t0 = max(0.0, bt - 0.003)
        t1 = bt + 0.018
        y_pos = 220 + ((i * 173) % 1420)
        glitches.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y={y_pos}:w=iw:h=4:color={c3}@0.20:t=fill"
        )

    # Drop glitch mais forte
    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.004)
        for i, offset in enumerate([0.012, 0.024, 0.040]):
            y = 260 + ((i * 421) % 1300)
            glitches.append(
                f"drawbox=enable='between(t,{t0:.4f},{drop_time+offset:.4f})'"
                f":x=0:y={y}:w=iw:h=14:color={c3}@0.42:t=fill"
            )

    return ",".join(glitches) if glitches else ""


def build_cyberpunk_water_fx(analysis: dict, style: str = "default") -> str:
    """
    Reflexo/água cyberpunk v8.0 — mais dramático, RGB split, ondas mais largas.
    """
    if not WATER_FX_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    c3 = neon["c3"]

    bass_hits = analysis.get("bass_hits", [])[:WATER_FX_MAX_BASS_HITS]

    filters = []

    # Faixas de reflexo base
    filters.append(
        f"drawbox=x=0:y=ih*{WATER_FX_START_Y_RATIO:.2f}:w=iw:h=ih*(1-{WATER_FX_START_Y_RATIO:.2f})"
        f":color={c1}@{WATER_FX_BASE_ALPHA:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x=0:y=ih*0.70:w=iw:h=ih*0.30"
        f":color={c2}@{WATER_FX_BASE_ALPHA:.3f}:t=fill"
    )

    # Ondas RGB — 3 camadas separadas (vermelho, verde, azul) para chromatic split
    filters.append(
        f"drawbox=x='iw*0.05+30*sin(t*0.65)':y='ih*0.72+14*sin(t*1.05)'"
        f":w='iw*0.88':h=4:color={c1}@{WATER_FX_LINE_ALPHA:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x='iw*0.10+22*sin(t*0.90+1.2)':y='ih*0.78+16*sin(t*1.30+0.5)'"
        f":w='iw*0.78':h=3:color={c2}@{WATER_FX_LINE_ALPHA*0.85:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x='iw*0.18+18*sin(t*0.55+2.1)':y='ih*0.85+12*sin(t*1.55+1.0)'"
        f":w='iw*0.62':h=3:color={c3}@{WATER_FX_LINE_ALPHA*0.70:.3f}:t=fill"
    )
    # Linha extra fina — animação mais rápida
    filters.append(
        f"drawbox=x='iw*0.08+40*sin(t*1.20+0.8)':y='ih*0.65+8*sin(t*2.10)'"
        f":w='iw*0.82':h=2:color={c1}@{WATER_FX_LINE_ALPHA*0.50:.3f}:t=fill"
    )

    # Pulso do reflexo no bass hit
    for i, bt in enumerate(bass_hits):
        alpha = WATER_FX_BASS_ALPHA if i < 30 else WATER_FX_BASS_ALPHA * 0.6
        filters.append(
            f"drawbox=enable='between(t,{max(0.0, bt-0.010):.4f},{bt+0.065:.4f})'"
            f":x=0:y=ih*0.56:w=iw:h=ih*0.44:color={c1}@{alpha:.3f}:t=fill"
        )
        if i < 25:
            filters.append(
                f"drawbox=enable='between(t,{max(0.0, bt-0.005):.4f},{bt+0.040:.4f})'"
                f":x=0:y=ih*0.70:w=iw:h=ih*0.30:color={c2}@{alpha*0.7:.3f}:t=fill"
            )

    filters.append("eq=gamma=1.02:saturation=1.05")
    return ",".join(filters)


def build_vignette_pulse(analysis: dict, strength: float, style: str = "default") -> str:
    """
    Vinheta cyberpunk — fica mais intensa no beat, alivia nos silêncios.
    Usando vignette base + drawbox nas bordas que pulsa.
    """
    if strength <= 0:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c2 = neon["c2"]

    angle = round(strength * 1.15, 3)
    base_vig = f"vignette=angle={angle}:mode=forward"

    # Escurecimento extra nas bordas pulsante
    bass_hits = analysis.get("bass_hits", [])[:20]
    drop_time = analysis.get("drop_time")

    borders = []
    # Vinheta base nas quatro bordas
    borders.append(f"drawbox=x=0:y=0:w=iw:h=80:color=black@0.40:t=fill")
    borders.append(f"drawbox=x=0:y=ih-80:w=iw:h=80:color=black@0.40:t=fill")
    borders.append(f"drawbox=x=0:y=0:w=60:h=ih:color=black@0.35:t=fill")
    borders.append(f"drawbox=x=iw-60:y=0:w=60:h=ih:color=black@0.35:t=fill")

    if borders:
        return base_vig + "," + ",".join(borders)
    return base_vig


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS BASE (mantidos do v6)
# ══════════════════════════════════════════════════════════════════════════════

def build_audio_filter(duration: float) -> str:
    fo_start = max(0.0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fo_start:.3f}:d={AUDIO_FADE_OUT},"
        "acompressor=threshold=-16dB:ratio=3.5:attack=4:release=45:makeup=1.5dB,"
        "loudnorm=I=-14:TP=-1.0:LRA=9"
    )


def build_hook_flash_expr() -> str:
    d = 0.06
    b = 0.22
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
        "eq=contrast=1.02:brightness=0.0:saturation=1.02,"
        f"eq=contrast={profile['contrast']}"
        f":brightness='{brightness_expr}'"
        f":saturation={profile['saturation']},"
        f"unsharp=5:5:{profile['sharpen']}:5:5:0"
    )
    return f"{base_grade},{genre_grade}"


def build_fade_filter(duration: float) -> str:
    fo_start = max(0.0, duration - VIDEO_FADE_OUT_DUR)
    return f"fade=t=out:st={fo_start:.3f}:d={VIDEO_FADE_OUT_DUR}"


def build_progress_bar(duration: float, style: str = "default") -> str:
    """
    v8: progress bar removida.
    Ela entrega o final e pode reduzir replay/loop.
    """
    if not KEEP_FFMPEG_PROGRESS_BAR:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    return (
        "drawbox=x=0:y=ih-8:w=iw:h=8:color=black@0.45:t=fill,"
        f"drawbox=x=0:y=ih-8:w='iw*t/{duration:.3f}':h=8:color={c1}@0.85:t=fill"
    )


def build_hook_text(song_name: str, style: str, font: str, duration: float) -> str:
    """Texto fica no Remotion — FFmpeg mantém base limpa."""
    return ""


def build_watermark(font: str) -> str:
    """Watermark fica no Remotion."""
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# ZOOM HIPNÓTICO v8.0 — mais agressivo
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
    intro_frames = int(0.15 * fps)

    heavy = style in {"phonk", "metal", "rock", "trap", "electronic", "funk", "dark"}
    zoom_mult = 1.6 if heavy else 1.0

    base  = f"(1.0 + {zoom_speed * zoom_mult}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = (
        f"({pulse_strength * 0.7}*sin(on*0.07+0.2)*cos(on*0.032)+"
        f"{pulse_strength * 0.35}*sin(on*0.13+1.4))"
    )

    beat_pulse = "0"
    if beats:
        parts = [
            f"0.006*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.07*fps))})"
            for b in beats[:80]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        intensity = 0.022 if heavy else 0.013
        parts = [
            f"{intensity}*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.05*fps))})"
            for b in bass_hits[:70]
        ]
        bass_pulse = f"({'+'.join(parts)})"

    drop_punch = DROP_ZOOM_PUNCH * (1.8 if heavy else 1.2)
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({drop_punch:.3f}*max(0,1-abs(on-{df})/{max(1,int(0.04*fps))})+"
            f"0.06*max(0,({int(0.5*fps)}-abs(on-{df+int(0.08*fps)}))/{int(0.5*fps)}))"
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

    heavy = style in {"phonk", "metal", "rock", "trap", "funk", "dark", "electronic"}
    shake_mult = 1.8 if heavy else 1.0

    shake_x = f"(sin(t*3.1)*{sx*0.72*shake_mult}+sin(t*5.5)*{sx*0.28*shake_mult})"
    shake_y = f"(cos(t*2.8)*{sy*0.72*shake_mult}+cos(t*5.0)*{sy*0.28*shake_mult})"

    if bass_hits:
        boost_int = 2.5 if heavy else 1.8
        boosts = [
            f"{boost_int}*max(0,1-abs(t-{t:.4f})/{0.10:.3f})"
            for t in bass_hits[:60]
        ]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        drop_mult_val = 5.0 if heavy else 3.5
        drop_mult = f"(1+{drop_mult_val}*max(0,1-abs(t-{drop_time:.4f})/0.20))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    hook_gate = "if(lt(t,0.08),0.02,1.0)"
    shake_x = f"({shake_x})*{hook_gate}"
    shake_y = f"({shake_y})*{hook_gate}"

    return shake_x, shake_y


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS COMPLETOS v8.0
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
    water_fx = build_cyberpunk_water_fx(analysis, style)
    vig_strength = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE["default"])
    vig = build_vignette_pulse(analysis, vig_strength, style)
    fades = build_fade_filter(duration)
    pbar  = build_progress_bar(duration, style)
    scanlines = build_scanlines(analysis, style)
    drop_flash = build_drop_flash(analysis)
    neon_border = build_neon_border_pulse(analysis, style)
    glitch = build_glitch_slices(analysis, style)

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
    if water_fx:
        parts.append(water_fx)
    if scanlines:
        parts.append(scanlines)
    if glitch:
        parts.append(glitch)
    if neon_border:
        parts.append(neon_border)
    if drop_flash:
        parts.append(drop_flash)
    if vig:
        parts.append(vig)

    parts += [fades, f"fps={fps}", pbar]
    return join_filters(parts)


def build_video_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps  = profile["fps"]
    font = get_font()
    brightness_expr = build_combined_brightness(profile, analysis)
    sx = min(profile.get("shake_x", 6), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 6), MAX_SHAKE_Y)
    shake_x_expr, shake_y_expr = build_elite_shake(analysis, sx, sy, style=style)
    color = build_color_grade(profile, brightness_expr, style)
    water_fx = build_cyberpunk_water_fx(analysis, style)
    vig_strength = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE["default"])
    vig = build_vignette_pulse(analysis, vig_strength, style)
    fades = build_fade_filter(duration)
    pbar  = build_progress_bar(duration, style)
    scanlines = build_scanlines(analysis, style)
    drop_flash = build_drop_flash(analysis)
    neon_border = build_neon_border_pulse(analysis, style)
    glitch = build_glitch_slices(analysis, style)

    parts = [
        "scale=1140:2026:force_original_aspect_ratio=increase",
        (
            f"crop=1080:1920:"
            f"x='max(0,min(iw-1080,iw/2-540+({shake_x_expr})))':"
            f"y='max(0,min(ih-1920,ih/2-960+({shake_y_expr})))'"
        ),
        color,
    ]
    if water_fx:
        parts.append(water_fx)
    if scanlines:
        parts.append(scanlines)
    if glitch:
        parts.append(glitch)
    if neon_border:
        parts.append(neon_border)
    if drop_flash:
        parts.append(drop_flash)
    if vig:
        parts.append(vig)

    parts += [fades, f"fps={fps}", pbar]
    return join_filters(parts)


# ══════════════════════════════════════════════════════════════════════════════
# MONTAGEM DO COMANDO FFMPEG
# ══════════════════════════════════════════════════════════════════════════════

def _build_cmd(
    inputs: list, vf_or_complex: str,
    is_complex: bool, use_logo: bool,
    audio_filter: str, dur: float, output_name: str,
    audio_input_idx: int = 1,
) -> list:
    cmd = ["ffmpeg", "-y"] + inputs + ["-t", str(dur)]

    if is_complex:
        cmd += ["-filter_complex", vf_or_complex]
        cmd += ["-map", "[vout]", "-map", f"{audio_input_idx}:a"]
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
# VALIDAÇÃO E THUMBNAIL
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


def generate_thumbnail(
    video_path: str, song_name: str, style: str,
    output_dir: str = THUMB_DIR, timestamp: float = THUMB_TIMESTAMP,
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem  = Path(video_path).stem
    out   = str(Path(output_dir) / f"{stem}_thumb.jpg")
    font  = get_font()
    clean = escape_text(song_name)
    neon  = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1    = neon["c1"].replace("0x", "#")
    genre_grade = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
    vf = (
        f"{genre_grade},"
        "eq=contrast=1.25:brightness=-0.04:saturation=1.40,"
        "vignette=angle=0.80:mode=forward,"
        "drawbox=x=0:y=ih*0.72:w=iw:h=ih*0.28:color=black@0.70:t=fill,"
        f"drawtext=fontfile='{font}':text='{clean}'"
        ":fontsize=76:fontcolor=white:borderw=5:bordercolor=black@0.95"
        ":shadowx=5:shadowy=5:shadowcolor=black@0.8"
        ":x=(w-text_w)/2:y=h*0.78,"
        f"drawtext=fontfile='{font}':text='#PHONK'"
        ":fontsize=40:fontcolor=white@0.90:borderw=2:bordercolor=black@0.75"
        ":x=(w-text_w)/2:y=h*0.90"
    )
    cmd = [
        "ffmpeg", "-y", "-ss", str(timestamp),
        "-i", video_path, "-vframes", "1",
        "-vf", vf, "-q:v", "2", out,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"  ► Thumbnail gerada: {out}")
        return out
    except subprocess.CalledProcessError as e:
        logger.warning(f"  ⚠ Thumbnail falhou: {e.stderr.decode()[-300:] if e.stderr else ''}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL — create_short
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
    logger.info(f"  ► Neon: {GENRE_NEON.get(style, GENRE_NEON['default'])}")

    # ── Análise de áudio ──────────────────────────────────────────────────
    logger.info("  ► Analisando áudio…")
    analysis_full = full_analysis(audio_path)

    if _REMOTION_AVAILABLE:
        try:
            generate_audio_data(audio_path)
            logger.info("  ► audio_data.json gerado (Remotion sync)")
        except Exception as e:
            logger.warning(f"  ⚠ erro audio_data.json: {e}")
    else:
        logger.debug("  ► audio_to_remotion não disponível.")

    bpm       = analysis_full.get("bpm")
    audio_dur = get_duration(audio_path)

    # ── Janela de tempo ───────────────────────────────────────────────────
    if use_smart_window:
        if audio_dur <= MIN_DURATION:
            target_dur = float(audio_dur)
        else:
            target_dur = random.randint(MIN_DURATION, min(MAX_DURATION, int(audio_dur)))

        try:
            start, dur = find_best_window(audio_path, target_dur)
            if audio_dur >= MIN_DURATION:
                dur = max(MIN_DURATION, min(MAX_DURATION, float(dur)))
                if start + dur > audio_dur:
                    start = max(0.0, audio_dur - dur)
            logger.info(f"  ► Janela inteligente: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")
        except Exception:
            start, dur = pick_window(audio_dur)
            logger.info(f"  ► Janela fallback: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")
    else:
        start, dur = pick_window(audio_dur)
        logger.info(f"  ► Janela manual: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")

    analysis = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    kicks    = len(analysis.get("bass_hits", []))
    beats    = len(analysis.get("beats", []))
    bpm_text = f"{bpm:.1f}" if bpm else "N/A"
    logger.info(f"  ► Kicks: {kicks} | Beats: {beats} | BPM: {bpm_text}")

    drop_time = analysis.get("drop_time")
    logger.info(f"  ► Drop: {drop_time:.2f}s" if drop_time else "  ► Drop: não detectado")

    profile      = get_profile_for_bpm(bpm, style)
    audio_filter = build_audio_filter(dur)
    use_logo     = logo_exists()

    logger.info("  ► Logo/texto no Remotion — FFmpeg gera base cyberpunk limpa.")

    ext      = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    # ── IMAGEM como fundo ─────────────────────────────────────────────────
    if is_image:
        base_vf = build_image_filter(profile, analysis, dur, song_name, style)
        inputs = [
            "-loop", "1", "-i", background_path,
            "-ss", str(start), "-i", audio_path,
        ]
        cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                         audio_input_idx=1)

    # ── VÍDEO como fundo ──────────────────────────────────────────────────
    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        base_vf  = build_video_filter(profile, analysis, dur, song_name, style)
        inputs = [
            "-ss", str(bg_start), "-i", background_path,
            "-ss", str(start), "-i", audio_path,
        ]
        cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                         audio_input_idx=1)

    # ── FALLBACK: fundo preto ─────────────────────────────────────────────
    else:
        genre_g  = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
        fade     = build_fade_filter(dur)
        pbar     = build_progress_bar(dur, style)
        scanlines = build_scanlines(analysis, style)
        drop_flash = build_drop_flash(analysis)
        neon_border = build_neon_border_pulse(analysis, style)
        base_vf  = join_filters([genre_g, scanlines, neon_border, drop_flash, fade, pbar])
        inputs = [
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
            "-ss", str(start), "-i", audio_path,
        ]
        cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                         audio_input_idx=1)

    # ── Render ────────────────────────────────────────────────────────────
    logger.info("  ► Iniciando render v8.0 (Viral Control)…")
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("  ► Render concluído ✓")
            break
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode()[-600:] if e.stderr else ""
            if attempt <= MAX_RETRIES:
                logger.warning(f"  ⚠ Render falhou (tentativa {attempt}): {err}")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"  ✗ Render falhou após {MAX_RETRIES+1} tentativas.\n{err}")
                raise

    validation = validate_output(output_name, dur)
    if validation["ok"]:
        info = validation["info"]
        logger.info(
            f"  ► OK — {info['width']}x{info['height']} | "
            f"{info['duration']:.1f}s | {info['size_mb']}MB"
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

    if auto_thumbnail:
        thumb = generate_thumbnail(output_name, song_name, style)
        result["thumbnail_path"] = thumb

    elapsed = round(time.time() - t_start, 1)
    result["render_time_s"] = elapsed
    logger.info(f"✅ Finalizado em {elapsed}s")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# BATCH
# ══════════════════════════════════════════════════════════════════════════════

def generate_batch(
    tasks: list[dict], output_dir: str = "output",
    auto_thumbnail: bool = True, upload: bool = False,
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
        logger.info(f"\n{'='*60}\n[{i}/{len(tasks)}] {name}")
        try:
            r = create_short(
                audio_path=audio_path, background_path=background_path,
                output_name=output_name, style=style, song_name=song_name,
                auto_thumbnail=auto_thumbnail, upload=upload, upload_privacy=upload_privacy,
            )
            r["task"] = task
            r["status"] = "ok"
            results.append(r)
        except Exception as e:
            logger.error(f"  ✗ Falha task {i}: {e}")
            results.append({"task": task, "status": "error", "error": str(e)})
    ok = sum(1 for r in results if r.get("status") == "ok")
    logger.info(f"\nBatch: {ok} ok, {len(results)-ok} erros.")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Elite Music Shorts Generator v8.0 — Viral Control")
    parser.add_argument("audio")
    parser.add_argument("background")
    parser.add_argument("output")
    parser.add_argument("--style",    default="phonk", choices=list_profiles())
    parser.add_argument("--name",     default="")
    parser.add_argument("--no-thumb", action="store_true")
    parser.add_argument("--upload",   action="store_true")
    parser.add_argument("--privacy",  default="private")
    parser.add_argument("--no-smart", action="store_true")
    args = parser.parse_args()
    create_short(
        audio_path=args.audio, background_path=args.background,
        output_name=args.output, style=args.style, song_name=args.name,
        use_smart_window=not args.no_smart, auto_thumbnail=not args.no_thumb,
        upload=args.upload, upload_privacy=args.privacy,
    )
