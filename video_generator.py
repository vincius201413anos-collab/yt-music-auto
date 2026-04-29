"""
video_generator.py — DJ DARK MARK v15.0 APEX QUALITY
══════════════════════════════════════════════════════════════════════════════
CHANGELOG v15.0 vs v14.2:

[QUALITY 1] FFMPEG_CRF: "20" → "16"  — qualidade visual máxima, sem artefatos
[QUALITY 2] FFMPEG_PRESET: "veryfast" → "fast"  — menos artefatos em gradientes/cabelos
[QUALITY 3] FFMPEG_AUDIO_BITRATE: "192k" → "256k"  — áudio mais fiel à música original
[QUALITY 4] AUDIO_FADE_IN: 0.03 → 0.012  — drop instantâneo, sem fade perceptível
[QUALITY 5] AUDIO_FADE_OUT: 0.7 → 0.55  — saída mais curta e limpa

[SYNC 1] build_elite_zoom: beat_pulse window reduzida de 0.06 → 0.04fps
         e bass_pulse window de 0.05 → 0.035fps — zoom mais apertado no beat
[SYNC 2] build_elite_zoom: bass_pulse intensity 0.024 → 0.032 — punch mais forte no grave
[SYNC 3] build_elite_shake: boost window de 0.10 → 0.075 — shake mais preciso no bass hit
[SYNC 4] build_elite_shake: boost_int 2.6 → 3.2 (heavy) — mais energia no impacto
[SYNC 5] build_elite_shake: drop_mult 5.5 → 7.0 (heavy) — drop shake máximo
[SYNC 6] hook_gate: lt(t,0.08) → lt(t,0.06) — sem shake no frame-0

[AUDIO 1] build_audio_filter: compressor threshold -16dB → -18dB, ratio 3.5 → 4.0
          — compressão mais consistente para músicas variadas
[AUDIO 2] loudnorm: I=-14 (YouTube target), TP=-1.0, LRA=9 — mantido (já é correto)
[AUDIO 3] Adicionado equalizer suave: boost 60Hz (kick punch) e 8kHz (ar/presença)

[COLOR 1] build_color_grade: removido primeiro eq base duplicado (era 1.02/1.02)
          que somava ao profile — agora direto no profile sem dupla aplicação
[COLOR 2] unsharp max cap: profile['sharpen'] limitado a 1.2 — evita halos excessivos
[COLOR 3] build_final_texture: gamma 1.012 → 1.008, saturation 1.035 → 1.025 — mais natural

[TIMING 1] heartbeat_pulse: t1 bt+0.028 → bt+0.022 — flash mais curto e preciso
[TIMING 2] rim_light_sync: snare window 0.035 → 0.028 — mais tight no snare
[TIMING 3] hypnotic_beat_lights: beat window 0.042 → 0.036 — mais preciso
[TIMING 4] hypnotic_beat_lights: bass window 0.088 → 0.075 — menos arrastamento

Mantidas todas as correções de cor do v14.2 (FIX 1-9).
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

# ══════════════════════════════════════════════════════════════════════════════
# PARÂMETROS GERAIS
# ══════════════════════════════════════════════════════════════════════════════

MIN_DURATION        = 45
MAX_DURATION        = 60
VIDEO_FADE_OUT_DUR  = 0.5
AUDIO_FADE_IN       = 0.012   # [QUALITY 4] era 0.03 — drop quase instantâneo
AUDIO_FADE_OUT      = 0.55    # [QUALITY 5] era 0.70 — saída mais limpa
MAX_SHAKE_X         = 14      # ligeiramente aumentado para mais energia
MAX_SHAKE_Y         = 14
DROP_ZOOM_PUNCH     = 0.32    # ligeiramente mais forte no drop

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

# [QUALITY 1-3] — configurações de qualidade máxima
FFMPEG_VIDEO_CODEC   = "libx264"
FFMPEG_CRF           = os.getenv("FFMPEG_CRF",     "16")    # era "20"
FFMPEG_PRESET        = os.getenv("FFMPEG_PRESET",  "fast")  # era "veryfast"
FFMPEG_AUDIO_CODEC   = "aac"
FFMPEG_AUDIO_BITRATE = "256k"                                 # era "192k"

LOGO_PATH = "assets/logo_darkmark.png"

THUMB_DIR       = "thumbnails"
THUMB_TIMESTAMP = 1.5
MAX_RETRIES     = 2
RETRY_DELAY_S   = 3
MIN_FILE_SIZE_MB = 0.5
MAX_FILE_SIZE_MB = 350.0

FFMPEG_RENDER_TIMEOUT_S = int(os.getenv("FFMPEG_RENDER_TIMEOUT", "900"))
FFMPEG_THUMB_TIMEOUT_S  = int(os.getenv("FFMPEG_THUMB_TIMEOUT",  "120"))
FINAL_GRAIN_STRENGTH    = int(os.getenv("FINAL_GRAIN_STRENGTH",   "0"))
FORCE_FPS               = int(os.getenv("FFMPEG_FPS",             "30"))

# Controles globais de efeitos
HYPNOTIC_LIGHTS_ENABLED  = os.getenv("HYPNOTIC_LIGHTS_ENABLED",  "true").lower() == "true"
EYE_GLOW_ENABLED         = os.getenv("EYE_GLOW_ENABLED",         "true").lower() == "true"
TUNNEL_RAYS_ENABLED      = os.getenv("TUNNEL_RAYS_ENABLED",       "true").lower() == "true"
CHROMATIC_ENABLED        = os.getenv("CHROMATIC_ENABLED",         "true").lower() == "true"
HEARTBEAT_ENABLED        = os.getenv("HEARTBEAT_ENABLED",         "true").lower() == "true"
RIM_LIGHT_ENABLED        = os.getenv("RIM_LIGHT_ENABLED",         "true").lower() == "true"
VIGNETTE_BEAT_ENABLED    = os.getenv("VIGNETTE_BEAT_ENABLED",     "true").lower() == "true"
DEPTH_RAYS_ENABLED       = os.getenv("DEPTH_RAYS_ENABLED",        "true").lower() == "true"
STROBO_DROP_ENABLED      = os.getenv("STROBO_DROP_ENABLED",       "true").lower() == "true"
COLOR_SHIFT_ENABLED      = os.getenv("COLOR_SHIFT_ENABLED",       "true").lower() == "true"
WATER_FX_ENABLED         = True
KEEP_FFMPEG_PROGRESS_BAR = False

HYPNOTIC_LIGHT_INTENSITY = float(os.getenv("HYPNOTIC_LIGHT_INTENSITY", "0.85"))
VIRAL_SHAKE_MULT         = float(os.getenv("VIRAL_SHAKE_MULT",          "1.0"))
VIRAL_ZOOM_MULT          = float(os.getenv("VIRAL_ZOOM_MULT",           "1.0"))

LIM_BEATS        = int(os.getenv("LIM_BEATS",    "64"))
LIM_BASS         = int(os.getenv("LIM_BASS",     "52"))
LIM_SNARES       = int(os.getenv("LIM_SNARES",   "32"))
LIM_GLITCH       = int(os.getenv("LIM_GLITCH",   "10"))
LIM_BORDER       = int(os.getenv("LIM_BORDER",   "16"))
LIM_WATER        = int(os.getenv("LIM_WATER",    "24"))
LIM_TUNNEL       = int(os.getenv("LIM_TUNNEL",   "18"))
LIM_HEARTBEAT    = int(os.getenv("LIM_HEARTBEAT","40"))
LIM_RIM          = int(os.getenv("LIM_RIM",      "28"))
LIM_DEPTH_RAYS   = int(os.getenv("LIM_DEPTH_RAYS","14"))


# ══════════════════════════════════════════════════════════════════════════════
# PALETAS NEON POR GÊNERO
# ══════════════════════════════════════════════════════════════════════════════

GENRE_NEON = {
    "phonk":      {"c1": "0xFF0066", "c2": "0x8800FF", "c3": "0xFF2200", "c4": "0xFF00AA"},
    "trap":       {"c1": "0x00CCFF", "c2": "0xCC44FF", "c3": "0x00FFEE", "c4": "0xFF00CC"},
    "dark":       {"c1": "0x8800FF", "c2": "0x00FFEE", "c3": "0xFF0088", "c4": "0x4400FF"},
    "electronic": {"c1": "0x00FFEE", "c2": "0xFF00CC", "c3": "0x00AAFF", "c4": "0xCC00FF"},
    "dubstep":    {"c1": "0x00FFCC", "c2": "0xFF0088", "c3": "0x8800FF", "c4": "0x00AAFF"},
    "darkpop":    {"c1": "0xFF44AA", "c2": "0x8800FF", "c3": "0xFF0066", "c4": "0xAA00FF"},
    "metal":      {"c1": "0xFF5500", "c2": "0xCC44FF", "c3": "0x00CCFF", "c4": "0xFF2200"},
    "rock":       {"c1": "0xFF8800", "c2": "0xFF0044", "c3": "0xCC44FF", "c4": "0xFF4400"},
    "lofi":       {"c1": "0xFFAA44", "c2": "0xFF6688", "c3": "0xAA88FF", "c4": "0xFFCC88"},
    "cinematic":  {"c1": "0xFFBB44", "c2": "0xCC44FF", "c3": "0x00CCFF", "c4": "0xFF8844"},
    "funk":       {"c1": "0xFF8800", "c2": "0xFF0044", "c3": "0xCC44FF", "c4": "0xFFAA00"},
    "pop":        {"c1": "0xFF44AA", "c2": "0xAA00FF", "c3": "0x00CCFF", "c4": "0xFF88CC"},
    "default":    {"c1": "0xCC44FF", "c2": "0x00FFEE", "c3": "0xFF0088", "c4": "0x8800FF"},
}

# ══════════════════════════════════════════════════════════════════════════════
# GENRE_COLOR_GRADE — v14.2 COLOR FIX (mantidas todas as correções)
# ══════════════════════════════════════════════════════════════════════════════

GENRE_COLOR_GRADE = {
    "phonk": (
        "colorbalance=rs=0.20:gs=-0.09:bs=0.12,"
        "colorbalance=rh=-0.02:gh=0.04:bh=0.15,"
        "eq=contrast=1.42:brightness=-0.048:saturation=1.32:gamma=0.95,"
        "curves=r='0/0 0.25/0.10 1/1':g='0/0 0.30/0.08 1/0.88':b='0/0 0.18/0.23 1/1',"
        "unsharp=5:5:1.8:5:5:0"
    ),
    "trap": (
        "colorbalance=rs=-0.05:gs=0.04:bs=0.10,"
        "colorbalance=rh=-0.02:gh=0.06:bh=0.12,"
        "eq=contrast=1.38:brightness=-0.042:saturation=1.32:gamma=0.96,"
        "unsharp=5:5:1.5:5:5:0"
    ),
    "dark": (
        "colorbalance=rs=0.02:gs=-0.08:bs=0.15,"
        "colorbalance=rh=0.08:gh=-0.04:bh=0.12,"
        "eq=contrast=1.46:brightness=-0.078:saturation=1.14:gamma=0.93,"
        "curves=all='0/0 0.16/0.03 0.55/0.42 1/1',"
        "unsharp=5:5:1.45:5:5:0"
    ),
    "dubstep": (
        "colorbalance=rs=-0.10:gs=0.14:bs=0.22,"
        "colorbalance=rh=0.18:gh=-0.06:bh=0.12,"
        "eq=contrast=1.44:brightness=-0.060:saturation=1.55:gamma=0.94,"
        "unsharp=5:5:1.4:5:5:0"
    ),
    "darkpop": (
        "colorbalance=rs=0.16:gs=-0.06:bs=0.14,"
        "colorbalance=rh=-0.04:gh=0.04:bh=0.16,"
        "eq=contrast=1.34:brightness=-0.035:saturation=1.28:gamma=0.96,"
        "unsharp=5:5:1.35:5:5:0"
    ),
    "electronic": (
        "colorbalance=rs=-0.14:gs=0.12:bs=0.24,"
        "colorbalance=rh=0.20:gh=-0.08:bh=0.14,"
        "eq=contrast=1.42:brightness=-0.058:saturation=1.52:gamma=0.94,"
        "unsharp=5:5:1.2:5:5:0"
    ),
    "lofi": (
        "colorbalance=rs=0.15:gs=0.05:bs=-0.20,"
        "eq=contrast=0.90:brightness=0.020:saturation=0.75,"
        "unsharp=3:3:0.3:3:3:0,"
    ),
    "rock": (
        "colorbalance=rs=0.20:gs=0.06:bs=-0.15,"
        "eq=contrast=1.40:brightness=0.004:saturation=1.30,"
        "unsharp=5:5:1.5:5:5:0"
    ),
    "metal": (
        "colorbalance=rs=-0.18:gs=-0.12:bs=0.15,"
        "eq=contrast=1.60:brightness=-0.10:saturation=0.70,"
        "unsharp=5:5:1.6:5:5:0,"
        "vignette=angle=1.257:mode=forward"
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
    "indie": (
        "colorbalance=rs=0.08:gs=0.05:bs=-0.10,"
        "eq=contrast=0.95:brightness=0.018:saturation=0.85,"
    ),
    "default": (
        "colorbalance=rs=-0.04:gs=-0.02:bs=0.14,"
        "eq=contrast=1.50:brightness=-0.06:saturation=1.38:gamma=0.90,"
        "unsharp=5:5:1.2:5:5:0"
    ),
}

GENRE_VIGNETTE = {
    "phonk": 0.80, "dark": 0.60, "metal": 0.0, "lofi": 0.35,
    "trap": 0.55, "electronic": 0.45, "rock": 0.45, "indie": 0.28,
    "cinematic": 0.50, "funk": 0.18, "pop": 0.15, "dubstep": 0.65,
    "darkpop": 0.50, "default": 0.55,
}

GENRE_ENERGY_RGBA = {
    "phonk":      "red@0.9",
    "trap":       "cyan@0.85",
    "dark":       "0x8800FF@0.9",
    "electronic": "0x00FFEE@0.9",
    "dubstep":    "0x00FFCC@0.9",
    "darkpop":    "0xFF44AA@0.85",
    "metal":      "0xFF5500@0.9",
    "rock":       "0xFF8800@0.85",
    "lofi":       "0xFFAA44@0.8",
    "cinematic":  "0xFFBB44@0.85",
    "funk":       "0xFF8800@0.9",
    "pop":        "0xFF44AA@0.85",
    "default":    "0xCC44FF@0.9",
}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

def get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def get_video_info(path: str) -> dict:
    import json
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
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
    cleaned = []
    for p in parts:
        if not p or not str(p).strip():
            continue
        item = str(p).strip().strip(",")
        if item:
            cleaned.append(item)
    return ",".join(cleaned)


def _odd(value: int, fallback: int = 5) -> int:
    if value < 3:
        value = 3
    return value if value % 2 == 1 else value + 1


def sanitize_ffmpeg_filter(vf: str) -> str:
    if not vf:
        return vf

    def fix_unsharp(match: re.Match) -> str:
        parts = match.group(1).split(":")
        fixed = []
        for i, p in enumerate(parts):
            if i in (0, 1, 3, 4):
                try:
                    fixed.append(str(_odd(int(float(p)))))
                except Exception:
                    fixed.append(p)
            else:
                fixed.append(p)
        return "unsharp=" + ":".join(fixed)

    vf = re.sub(r"unsharp=([^,\s]+)", fix_unsharp, vf)
    vf = re.sub(
        r"(color=(?:0x[0-9A-Fa-f]{6}|[A-Za-z]+))@'[^']*(?:sin|cos|max|min|if|\+|\*|/)[^']*'",
        r"\1@0.025",
        vf,
    )
    vf = re.sub(r",{2,}", ",", vf).strip(",")
    return vf


def clean_song_name(audio_path: str, override: str = "") -> str:
    if override:
        return override.strip()
    name = Path(audio_path).stem
    name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name


def _tail(text: str, limit: int = 1200) -> str:
    if not text:
        return ""
    return str(text)[-limit:]


def run_cmd_safe(
    cmd: list[str], name: str, timeout_s: int, capture: bool = True
) -> subprocess.CompletedProcess:
    logger.info(f"  ► {name}: timeout={timeout_s}s")
    try:
        return subprocess.run(
            cmd, check=True, text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"  ✗ {name} travou após {timeout_s}s.")
        if getattr(e, "stderr", None):
            logger.error(_tail(e.stderr))
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"  ✗ {name} falhou (exit {e.returncode}).")
        if e.stderr:
            logger.error(_tail(e.stderr))
        raise


def logo_exists() -> bool:
    return False


# ══════════════════════════════════════════════════════════════════════════════
# ███ EFEITOS HIPNÓTICOS V15 — timing apertado, sync perfeito ███
# ══════════════════════════════════════════════════════════════════════════════

# ─── 1. HOOK FLASH ───────────────────────────────────────────────────────────

def build_hook_flash(style: str = "default") -> str:
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    return (
        "drawbox=enable='between(t,0.000,0.040)':x=0:y=0:w=iw:h=ih:color=white@0.75:t=fill,"
        f"drawbox=enable='between(t,0.040,0.160)':x=0:y=0:w=iw:h=ih:color={c1}@0.32:t=fill,"
        f"drawbox=enable='between(t,0.160,0.320)':x=0:y=0:w=iw:h=ih:color={c2}@0.12:t=fill"
    )


# ─── 2. HEARTBEAT PULSE ──────────────────────────────────────────────────────

def build_heartbeat_pulse(analysis: dict, style: str = "default") -> str:
    if not HEARTBEAT_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])[:LIM_HEARTBEAT]

    parts = []
    for i, bt in enumerate(bass_hits):
        if drop_time is not None and abs(bt - drop_time) < 0.35:
            continue
        t0 = max(0.0, bt - 0.004)
        t1 = bt + 0.022   # [TIMING 1] era 0.028 — flash mais curto e preciso no beat
        t2 = bt + 0.075
        color = c1 if i % 2 == 0 else c2
        alpha1 = 0.095
        alpha2 = 0.022
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={color}@{alpha1:.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t1:.4f},{t2:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={color}@{alpha2:.3f}:t=fill"
        )

    return ",".join(parts)


# ─── 3. TUNNEL LIGHT RAYS ────────────────────────────────────────────────────

def build_tunnel_rays(analysis: dict, style: str = "default") -> str:
    if not TUNNEL_RAYS_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    c3 = neon["c3"]

    bass_hits = analysis.get("bass_hits", [])[:LIM_TUNNEL]
    drop_time = analysis.get("drop_time")

    parts = []

    cx, cy = "iw/2-2", "ih*0.40-2"
    parts.append(f"drawbox=x={cx}:y=0:w=4:h=ih:color={c2}@0.018:t=fill")
    parts.append(f"drawbox=x=0:y={cy}:w=iw:h=4:color={c2}@0.018:t=fill")

    for i, bt in enumerate(bass_hits):
        if drop_time is not None and abs(bt - drop_time) < 0.5:
            continue
        t0 = max(0.0, bt - 0.006)   # onset ligeiramente mais cedo
        t1 = bt + 0.050
        color = c1 if i % 3 == 0 else (c2 if i % 3 == 1 else c3)
        alpha = 0.18

        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw/2-3:y=0:w=6:h=ih:color={color}@{alpha:.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih*0.38:w=iw:h=6:color={color}@{alpha*0.8:.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*0.48:y=0:w=4:h=ih*0.42:color={color}@{alpha*0.6:.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*0.48:y=ih*0.38:w=4:h=ih*0.62:color={color}@{alpha*0.6:.3f}:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.010)
        t1 = drop_time + 0.200
        for offset, width, a in [
            (0, 8, 0.55), (0.02, 5, 0.35), (-0.02, 5, 0.35),
        ]:
            x_pos = f"iw*{0.5 + offset:.3f}-{width//2}"
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x={x_pos}:y=0:w={width}:h=ih:color={c1}@{a:.3f}:t=fill"
            )

    return ",".join(parts)


# ─── 4. RIM LIGHT SYNC ───────────────────────────────────────────────────────

def build_rim_light_sync(analysis: dict, style: str = "default") -> str:
    if not RIM_LIGHT_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    c3 = neon["c3"]
    c4 = neon["c4"]

    snares = analysis.get("snares", [])[:LIM_RIM]
    beats  = analysis.get("beats",  [])[:LIM_BEATS // 2]
    drop_time = analysis.get("drop_time")

    parts = []

    # Base rim — muito sutil, quase imperceptível
    parts.append(f"drawbox=x=0:y=ih*0.10:w=5:h=ih*0.75:color={c1}@0.018:t=fill")
    parts.append(f"drawbox=x=iw-5:y=ih*0.10:w=5:h=ih*0.75:color={c2}@0.018:t=fill")

    for i, st in enumerate(snares):
        if drop_time is not None and abs(st - drop_time) < 0.35:
            continue
        t0 = max(0.0, st - 0.003)
        t1 = st + 0.028    # [TIMING 2] era 0.035 — mais preciso no snare
        if i % 4 == 0:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=0:y=0:w=22:h=ih:color={c1}@0.28:t=fill"
            )
        elif i % 4 == 1:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=iw-22:y=0:w=22:h=ih:color={c2}@0.28:t=fill"
            )
        elif i % 4 == 2:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=0:y=0:w=14:h=ih:color={c3}@0.20:t=fill"
            )
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=iw-14:y=0:w=14:h=ih:color={c3}@0.20:t=fill"
            )
        else:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=0:y=0:w=iw:h=12:color={c4}@0.22:t=fill"
            )
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=0:y=ih-12:w=iw:h=12:color={c4}@0.22:t=fill"
            )

    for i, bt in enumerate(beats):
        if drop_time is not None and abs(bt - drop_time) < 0.4:
            continue
        t0 = max(0.0, bt - 0.003)
        t1 = bt + 0.036
        color = c1 if i % 2 == 0 else c2
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih*0.15:w=8:h=ih*0.70:color={color}@0.12:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-8:y=ih*0.15:w=8:h=ih*0.70:color={color}@0.12:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.010)
        t1 = drop_time + 0.150
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=35:h=ih:color={c1}@0.65:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-35:y=0:w=35:h=ih:color={c2}@0.65:t=fill"
        )

    return ",".join(parts)


# ─── 5. CHROMATIC ABERRATION ─────────────────────────────────────────────────

def build_chromatic_aberration(analysis: dict, style: str = "default") -> str:
    if not CHROMATIC_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c3 = neon["c3"]

    bass_hits = analysis.get("bass_hits", [])[:LIM_GLITCH]
    drop_time = analysis.get("drop_time")

    parts = []

    for i, bt in enumerate(bass_hits[:8]):
        t0 = max(0.0, bt - 0.003)
        t1 = bt + 0.018
        y = 300 + ((i * 233) % 1100)
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y={y}:w=iw:h=6:color={c1}@0.22:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y={y+8}:w=iw:h=4:color={c3}@0.18:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.006)
        for i, (offset, w, a, c) in enumerate([
            (0.010, 22, 0.50, c1),
            (0.018, 16, 0.42, c3),
            (0.028, 12, 0.35, c1),
            (0.042, 8,  0.25, c3),
        ]):
            y = 200 + (i * 380)
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{drop_time+offset:.4f})'"
                f":x=0:y={y}:w=iw:h={w}:color={c}@{a:.3f}:t=fill"
            )

    return ",".join(parts) if parts else ""


# ─── 6. SCANLINES BURST ──────────────────────────────────────────────────────

def build_scanlines_burst(analysis: dict, style: str = "default") -> str:
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])[:14]

    parts = []

    parts.append(f"drawbox=x=0:y='mod(t*88,ih)':w=iw:h=1:color={c1}@0.014:t=fill")
    parts.append(f"drawbox=x=0:y='mod(t*88+ih*0.5,ih)':w=iw:h=1:color={c2}@0.010:t=fill")

    for bt in bass_hits:
        t0 = max(0.0, bt - 0.004)
        t1 = bt + 0.032
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y='mod(t*110,ih)':w=iw:h=2:color={c1}@0.055:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.006)
        t1 = drop_time + 0.080
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=white@0.08:t=fill"
        )
        for row_y in [0.10, 0.25, 0.40, 0.55, 0.70, 0.85]:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{drop_time+0.060:.4f})'"
                f":x=0:y=ih*{row_y:.2f}:w=iw:h=3:color={c1}@0.42:t=fill"
            )
        parts.append(
            f"drawbox=enable='between(t,{drop_time+0.080:.4f},{drop_time+0.115:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=black@0.20:t=fill"
        )

    return ",".join(parts)


# ─── 7. DEPTH RAYS ───────────────────────────────────────────────────────────

def build_depth_rays(analysis: dict, style: str = "default") -> str:
    if not DEPTH_RAYS_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    c3 = neon["c3"]

    bass_hits = analysis.get("bass_hits", [])[:LIM_DEPTH_RAYS]
    drop_time = analysis.get("drop_time")

    parts = []

    ray_positions = [0.15, 0.30, 0.50, 0.68, 0.82]
    colors_cycle  = [c1, c2, c3, c1, c2]

    for x_ratio, color in zip(ray_positions, colors_cycle):
        parts.append(
            f"drawbox=x=iw*{x_ratio:.2f}:y=0:w=3:h=ih*0.45:color={color}@0.008:t=fill"
        )

    for i, bt in enumerate(bass_hits):
        if drop_time is not None and abs(bt - drop_time) < 0.4:
            continue
        t0 = max(0.0, bt - 0.005)
        t1 = bt + 0.060
        x_idx = i % len(ray_positions)
        x_pos = ray_positions[x_idx]
        color = colors_cycle[x_idx]
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*{x_pos:.2f}:y=0:w=10:h=ih*0.50:color={color}@0.18:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.008)
        t1 = drop_time + 0.180
        for x_ratio, color in zip(ray_positions, colors_cycle):
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=iw*{x_ratio:.2f}:y=0:w=18:h=ih:color={color}@0.35:t=fill"
            )

    return ",".join(parts)


# ─── 8. VIGNETTE BEAT ────────────────────────────────────────────────────────

def build_vignette_beat(analysis: dict, strength: float, style: str = "default") -> str:
    if not VIGNETTE_BEAT_ENABLED or strength <= 0:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c2 = neon["c2"]

    angle = round(min(strength * 1.18, 1.45), 3)
    base_vig = f"vignette=angle={angle}:mode=forward"

    bass_hits = analysis.get("bass_hits", [])[:20]
    drop_time = analysis.get("drop_time")

    borders = [
        "drawbox=x=0:y=0:w=iw:h=85:color=black@0.42:t=fill",
        "drawbox=x=0:y=ih-85:w=iw:h=85:color=black@0.42:t=fill",
        "drawbox=x=0:y=0:w=55:h=ih:color=black@0.36:t=fill",
        "drawbox=x=iw-55:y=0:w=55:h=ih:color=black@0.36:t=fill",
    ]

    for bt in bass_hits[:12]:
        t0 = max(0.0, bt - 0.004)
        t1 = bt + 0.045
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=12:color=black@0.30:t=fill"
        )
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih-12:w=iw:h=12:color=black@0.30:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time)
        t1 = drop_time + 0.140
        borders.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={c2}@0.06:t=fill"
        )

    return base_vig + "," + ",".join(borders)


# ─── 9. STROBO SAFE ──────────────────────────────────────────────────────────

def build_strobo_drop(analysis: dict, style: str = "default") -> str:
    if not STROBO_DROP_ENABLED:
        return ""

    drop_time = analysis.get("drop_time")
    if drop_time is None:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    d = float(drop_time)

    return ",".join([
        f"drawbox=enable='between(t,{max(0.0,d-0.040):.4f},{d-0.012:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color=black@0.40:t=fill",
        f"drawbox=enable='between(t,{max(0.0,d-0.010):.4f},{d+0.032:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color=white@0.68:t=fill",
        f"drawbox=enable='between(t,{d+0.045:.4f},{d+0.065:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color={c1}@0.40:t=fill",
        f"drawbox=enable='between(t,{d+0.065:.4f},{d+0.095:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color=black@0.28:t=fill",
        f"drawbox=enable='between(t,{d+0.095:.4f},{d+0.112:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color={c2}@0.32:t=fill",
        f"drawbox=enable='between(t,{d+0.120:.4f},{d+0.260:.4f})'"
        f":x=0:y=0:w=iw:h=ih:color={c1}@0.14:t=fill",
    ])


# ─── 10. COLOR SHIFT ─────────────────────────────────────────────────────────

def build_color_shift(analysis: dict, duration: float, style: str = "default") -> str:
    if not COLOR_SHIFT_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    drop_time = analysis.get("drop_time")

    parts = []

    if drop_time is not None and drop_time > 5:
        pre0 = max(0.0, drop_time - 3.0)
        pre1 = drop_time - 0.1
        parts.append(
            f"drawbox=enable='between(t,{pre0:.4f},{pre1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={c1}@0.010:t=fill"
        )

    if drop_time is not None:
        post0 = drop_time + 0.3
        post1 = min(duration, drop_time + 6.0)
        parts.append(
            f"drawbox=enable='between(t,{post0:.4f},{post1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={c1}@0.012:t=fill"
        )

    return ",".join(parts) if parts else ""


# ─── 11. EYE GLOW HYPNOSIS ───────────────────────────────────────────────────

def build_eye_glow_hypnosis(analysis: dict, style: str = "default") -> str:
    if not EYE_GLOW_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]

    bass_hits = analysis.get("bass_hits", [])[:28]
    drop_time = analysis.get("drop_time")

    parts = []

    parts.append(
        f"drawbox=x=iw*0.35:y=ih*0.210:w=iw*0.30:h=ih*0.085:color={c1}@0.012:t=fill"
    )
    parts.append(
        f"drawbox=x=iw*0.42:y=ih*0.240:w=iw*0.16:h=ih*0.020:color={c2}@0.030:t=fill"
    )

    for bt in bass_hits:
        t0 = max(0.0, bt - 0.006)
        t1 = bt + 0.060
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*0.37:y=ih*0.228:w=iw*0.26:h=ih*0.048:color={c1}@0.110:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.010)
        t1 = drop_time + 0.180
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*0.28:y=ih*0.195:w=iw*0.44:h=ih*0.115:color={c2}@0.175:t=fill"
        )

    return ",".join(parts)


# ─── 12. WATER REFLECTION FX ─────────────────────────────────────────────────

def build_cyberpunk_water_fx(analysis: dict, style: str = "default") -> str:
    if not WATER_FX_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1, c2, c3 = neon["c1"], neon["c2"], neon["c3"]
    bass_hits = analysis.get("bass_hits", [])[:LIM_WATER]
    start_y = 0.54

    parts = [
        f"drawbox=x=0:y=ih*{start_y:.2f}:w=iw:h=ih*(1-{start_y:.2f}):color={c1}@0.020:t=fill",
        f"drawbox=x=0:y=ih*0.70:w=iw:h=ih*0.30:color={c2}@0.018:t=fill",
        f"drawbox=x='iw*0.05+28*sin(t*0.65)':y='ih*0.72+14*sin(t*1.05)':w='iw*0.88':h=4:color={c1}@0.072:t=fill",
        f"drawbox=x='iw*0.10+20*sin(t*0.90+1.2)':y='ih*0.78+16*sin(t*1.30+0.5)':w='iw*0.78':h=3:color={c2}@0.060:t=fill",
        f"drawbox=x='iw*0.18+16*sin(t*0.55+2.1)':y='ih*0.85+12*sin(t*1.55+1.0)':w='iw*0.62':h=3:color={c3}@0.052:t=fill",
        f"drawbox=x='iw*0.08+38*sin(t*1.20+0.8)':y='ih*0.65+8*sin(t*2.10)':w='iw*0.82':h=2:color={c1}@0.038:t=fill",
    ]

    for i, bt in enumerate(bass_hits):
        alpha = 0.058 if i < 18 else 0.040
        t0 = max(0.0, bt - 0.006)
        t1 = bt + 0.060
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih*0.55:w=iw:h=ih*0.45:color={c1}@{alpha:.3f}:t=fill"
        )
        if i < 18:
            parts.append(
                f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
                f":x=0:y=ih*0.70:w=iw:h=ih*0.30:color={c2}@{alpha*0.7:.3f}:t=fill"
            )

    return ",".join(parts)


# ─── 13. HYPNOTIC BEAT LIGHTS ────────────────────────────────────────────────

def build_hypnotic_beat_lights(analysis: dict, style: str = "default") -> str:
    if not HYPNOTIC_LIGHTS_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1, c2, c3 = neon["c1"], neon["c2"], neon["c3"]
    beats     = analysis.get("beats",     [])[:LIM_BEATS]
    bass_hits = analysis.get("bass_hits", [])[:LIM_BASS]
    snares    = analysis.get("snares",    [])[:LIM_SNARES]
    drop_time = analysis.get("drop_time")
    intensity = max(0.25, min(float(HYPNOTIC_LIGHT_INTENSITY), 1.8))

    parts = [
        f"drawbox=x=0:y=0:w=iw*0.09:h=ih:color={c1}@{0.028*intensity:.4f}:t=fill",
        f"drawbox=x=iw*0.91:y=0:w=iw*0.09:h=ih:color={c2}@{0.028*intensity:.4f}:t=fill",
    ]

    for i, bt in enumerate(beats):
        if drop_time is not None and abs(bt - drop_time) < 0.5:
            continue
        t0 = max(0.0, bt - 0.004)
        t1 = bt + 0.036   # [TIMING 3] era 0.042 — mais preciso no beat
        color = c2 if i % 2 else c1
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={color}@{0.036*intensity:.3f}:t=fill"
        )

    for i, bt in enumerate(bass_hits):
        t0 = max(0.0, bt - 0.008)
        t1 = bt + 0.075   # [TIMING 4] era 0.088 — menos arrastamento pós-bass
        alpha_full = 0.095 * intensity if i < 20 else 0.065 * intensity
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih*0.55:w=iw:h=ih*0.45:color={c1}@{alpha_full:.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=11:h=ih:color={c1}@{min(alpha_full*1.5,0.32):.3f}:t=fill"
        )
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-11:y=0:w=11:h=ih:color={c2}@{min(alpha_full*1.5,0.32):.3f}:t=fill"
        )

    for i, st in enumerate(snares):
        if drop_time is not None and abs(st - drop_time) < 0.40:
            continue
        t0 = max(0.0, st - 0.002)
        t1 = st + 0.022
        y = 130 + ((i * 199) % 1520)
        parts.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y={y}:w=iw:h=3:color={c3}@{0.082*intensity:.3f}:t=fill"
        )

    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.018)
        parts.extend([
            f"drawbox=enable='between(t,{t0:.4f},{drop_time+0.032:.4f})':x=0:y=0:w=iw:h=ih:color=white@{min(0.60*intensity,0.92):.3f}:t=fill",
            f"drawbox=enable='between(t,{drop_time+0.032:.4f},{drop_time+0.095:.4f})':x=0:y=0:w=iw:h=ih:color=black@0.22:t=fill",
            f"drawbox=enable='between(t,{drop_time+0.095:.4f},{drop_time+0.225:.4f})':x=0:y=0:w=iw:h=ih:color={c1}@{0.22*intensity:.3f}:t=fill",
            f"drawbox=enable='between(t,{drop_time+0.095:.4f},{drop_time+0.285:.4f})':x=iw*0.17:y=0:w=iw*0.06:h=ih:color={c2}@{0.30*intensity:.3f}:t=fill",
            f"drawbox=enable='between(t,{drop_time+0.095:.4f},{drop_time+0.285:.4f})':x=iw*0.77:y=0:w=iw*0.06:h=ih:color={c3}@{0.30*intensity:.3f}:t=fill",
        ])

    return ",".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# ███ ZOOM E SHAKE — APEX BEAT SYNC v15 ███
# ══════════════════════════════════════════════════════════════════════════════

def build_elite_zoom(
    analysis: dict, duration: float, fps: int,
    max_zoom: float, zoom_speed: float, pulse_strength: float,
    style: str = "default",
) -> str:
    beats     = analysis.get("beats",     [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    total_frames = max(1, int(duration * fps))
    intro_frames = int(0.10 * fps)  # intro ligeiramente menor — zoom começa mais cedo
    heavy = style in {"phonk", "metal", "rock", "trap", "electronic", "funk", "dark", "dubstep"}
    zoom_mult = (1.70 if heavy else 1.05) * max(0.4, min(VIRAL_ZOOM_MULT, 2.0))

    base  = f"(1.0 + {zoom_speed * zoom_mult}*(0.5-0.5*cos(2*PI*on/{total_frames})))"
    drift = (
        f"({pulse_strength * 0.7}*sin(on*0.07+0.2)*cos(on*0.032)+"
        f"{pulse_strength * 0.35}*sin(on*0.13+1.4))"
    )

    # [SYNC 1] beat_pulse window: 0.06fps → 0.04fps — zoom mais apertado no beat
    beat_pulse = "0"
    if beats:
        win = max(1, int(0.04 * fps))
        parts = [
            f"0.007*max(0,1-abs(on-{int(b*fps)})/{win})"
            for b in beats[:40]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    # [SYNC 2] bass_pulse intensity 0.024 → 0.032, window 0.05 → 0.035fps
    bass_pulse = "0"
    if bass_hits:
        intensity = 0.032 if heavy else 0.018  # era 0.024/0.014
        win = max(1, int(0.035 * fps))          # era 0.05
        parts = [
            f"{intensity}*max(0,1-abs(on-{int(b*fps)})/{win})"
            for b in bass_hits[:35]
        ]
        bass_pulse = f"({'+'.join(parts)})"

    drop_punch = DROP_ZOOM_PUNCH * (1.90 if heavy else 1.25)
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({drop_punch:.3f}*max(0,1-abs(on-{df})/{max(1,int(0.04*fps))})+"
            f"0.065*max(0,({int(0.5*fps)}-abs(on-{df+int(0.08*fps)}))/{int(0.5*fps)}))"
        )

    hook_frames = max(1, int(1.8 * fps))
    hook_boost  = f"(0.058*max(0,1-on/{hook_frames}))"

    full = f"{base}+{drift}+{hook_boost}+{beat_pulse}+{bass_pulse}+{drop_expr}"
    return (
        f"if(lte(on,{intro_frames}),"
        f"1.0,"
        f"min(max({full},1.0),{max_zoom + drop_punch:.3f}))"
    )


def build_elite_shake(analysis: dict, sx: int, sy: int, style: str = "default"):
    drop_time = analysis.get("drop_time")
    bass_hits = analysis.get("bass_hits", [])
    heavy = style in {"phonk", "metal", "rock", "trap", "funk", "dark", "electronic", "dubstep"}
    shake_mult = (1.90 if heavy else 1.05) * max(0.4, min(VIRAL_SHAKE_MULT, 2.0))

    shake_x = f"(sin(t*3.1)*{sx*0.72*shake_mult}+sin(t*5.5)*{sx*0.28*shake_mult})"
    shake_y = f"(cos(t*2.8)*{sy*0.72*shake_mult}+cos(t*5.0)*{sy*0.28*shake_mult})"

    if bass_hits:
        # [SYNC 3,4] window 0.10 → 0.075, boost_int 2.6 → 3.2
        boost_int = 3.2 if heavy else 2.2   # era 2.6 / 1.9
        window    = 0.075                    # era 0.10 — mais preciso no impacto
        boosts = [
            f"{boost_int}*max(0,1-abs(t-{t:.4f})/{window:.3f})"
            for t in bass_hits[:60]
        ]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        # [SYNC 5] drop_mult 5.5 → 7.0 (heavy) — drop shake máximo
        drop_mult_val = 7.0 if heavy else 4.2  # era 5.5 / 3.8
        drop_mult = f"(1+{drop_mult_val}*max(0,1-abs(t-{drop_time:.4f})/0.18))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    # [SYNC 6] hook_gate: lt(t,0.08) → lt(t,0.06) — sem shake no frame-0
    hook_gate = "if(lt(t,0.06),0.01,1.0)"
    shake_x = f"({shake_x})*{hook_gate}"
    shake_y = f"({shake_y})*{hook_gate}"

    return shake_x, shake_y


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS BASE
# ══════════════════════════════════════════════════════════════════════════════

def build_audio_filter(duration: float) -> str:
    """
    [AUDIO 1] Compressor mais forte: threshold -16→-18dB, ratio 3.5→4.0
    [AUDIO 2] Loudnorm -14 LUFS mantido (alvo YouTube Shorts)
    [AUDIO 3] Equalizer suave: boost 60Hz (punch do kick) e 8kHz (presença/ar)
              usando equalizer simples do FFmpeg para não adicionar dependências
    """
    fo_start = max(0.0, duration - AUDIO_FADE_OUT)
    return (
        f"afade=t=in:st=0:d={AUDIO_FADE_IN},"
        f"afade=t=out:st={fo_start:.3f}:d={AUDIO_FADE_OUT},"
        "equalizer=f=60:width_type=o:width=1.0:g=2.5,"        # punch do grave/kick
        "equalizer=f=8000:width_type=o:width=1.5:g=1.8,"      # presença e ar
        "acompressor=threshold=-18dB:ratio=4.0:attack=3:release=40:makeup=2dB,"
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
    """
    [COLOR 1] Removido primeiro eq base (era 1.02/1.02) que duplicava com o profile.
              Agora somente o eq do profile + o genre grade.
    [COLOR 2] sharpen limitado a 1.2 para evitar halos nos cabelos/bordas.
    """
    genre_grade = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
    sharpen_capped = min(profile["sharpen"], 1.2)  # [COLOR 2] cap anti-halo
    base = (
        f"eq=contrast={profile['contrast']}"
        f":brightness='{brightness_expr}'"
        f":saturation={profile['saturation']},"
        f"unsharp=5:5:{sharpen_capped}:5:5:0"
    )
    return f"{base},{genre_grade}"


def build_fade_filter(duration: float) -> str:
    fo_start = max(0.0, duration - VIDEO_FADE_OUT_DUR)
    return f"fade=t=out:st={fo_start:.3f}:d={VIDEO_FADE_OUT_DUR}"


def build_final_texture() -> str:
    """[COLOR 3] gamma 1.012→1.008, saturation 1.035→1.025 — resultado mais natural"""
    strength = max(0, min(FINAL_GRAIN_STRENGTH, 8))
    if strength <= 0:
        return "eq=gamma=1.008:saturation=1.025"
    return f"noise=alls={strength}:allf=t+u,eq=gamma=1.008:saturation=1.025"


def build_logo_overlay(song_name: str, style: str = "default") -> str:
    font  = get_font()
    safe  = escape_text("DJ DARK MARK")
    neon  = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1    = neon["c1"].replace("0x", "#")
    return (
        "drawbox=x=30:y=30:w=310:h=62:color=black@0.36:t=fill,"
        f"drawtext=fontfile='{font}':text='{safe}':fontsize=28:fontcolor={c1}@0.92:"
        "borderw=2:bordercolor=black@0.75:shadowx=2:shadowy=2:shadowcolor=black@0.8:x=46:y=44"
    )


def build_progress_bar(duration: float, style: str = "default") -> str:
    if not KEEP_FFMPEG_PROGRESS_BAR:
        return ""
    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1   = neon["c1"]
    return (
        "drawbox=x=0:y=ih-8:w=iw:h=8:color=black@0.45:t=fill,"
        f"drawbox=x=0:y=ih-8:w='iw*t/{duration:.3f}':h=8:color={c1}@0.85:t=fill"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MONTAGEM COMPLETA DE FILTROS
# ══════════════════════════════════════════════════════════════════════════════

def _assemble_all_fx(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str, include_zoom: bool = False,
    shake_x_expr: str = "", shake_y_expr: str = "",
) -> str:
    fps = FORCE_FPS or profile["fps"]
    brightness_expr = build_combined_brightness(profile, analysis)
    color_grade     = build_color_grade(profile, brightness_expr, style)
    vig_strength    = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE.get("default", 0.5))
    fade            = build_fade_filter(duration)

    parts = []

    if include_zoom:
        zoom_expr = build_elite_zoom(
            analysis, duration, fps,
            profile["max_zoom"], profile["zoom_speed"], profile["pulse_strength"],
            style=style,
        )
        parts += [
            "scale=1440:2560:force_original_aspect_ratio=increase",
            "crop=1080:1920:(iw-1080)/2:(ih-1920)/2",
            (
                f"zoompan=z='{zoom_expr}'"
                f":x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)'"
                f":d=1:s=1080x1920"
            ),
        ]
    else:
        parts += [
            "scale=1140:2026:force_original_aspect_ratio=increase",
            (
                f"crop=1080:1920:"
                f"x='max(0,min(iw-1080,iw/2-540+({shake_x_expr})))':"
                f"y='max(0,min(ih-1920,ih/2-960+({shake_y_expr})))'"
            ),
        ]

    parts.append(color_grade)

    water = build_cyberpunk_water_fx(analysis, style)
    if water:
        parts.append(water)

    depth = build_depth_rays(analysis, style)
    if depth:
        parts.append(depth)

    shift = build_color_shift(analysis, duration, style)
    if shift:
        parts.append(shift)

    hyp = build_hypnotic_beat_lights(analysis, style)
    if hyp:
        parts.append(hyp)

    hb = build_heartbeat_pulse(analysis, style)
    if hb:
        parts.append(hb)

    eye = build_eye_glow_hypnosis(analysis, style)
    if eye:
        parts.append(eye)

    tunnel = build_tunnel_rays(analysis, style)
    if tunnel:
        parts.append(tunnel)

    rim = build_rim_light_sync(analysis, style)
    if rim:
        parts.append(rim)

    scan = build_scanlines_burst(analysis, style)
    if scan:
        parts.append(scan)

    chroma = build_chromatic_aberration(analysis, style)
    if chroma:
        parts.append(chroma)

    strobo = build_strobo_drop(analysis, style)
    if strobo:
        parts.append(strobo)

    hook = build_hook_flash(style)
    if hook:
        parts.append(hook)

    logo = build_logo_overlay(song_name, style)
    if logo:
        parts.append(logo)

    vig = build_vignette_beat(analysis, vig_strength, style)
    if vig:
        parts.append(vig)

    texture = build_final_texture()
    if texture:
        parts.append(texture)

    parts += [fade, f"fps={fps}"]

    bar = build_progress_bar(duration, style)
    if bar:
        parts.append(bar)

    return join_filters(parts)


def build_image_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    return _assemble_all_fx(
        profile, analysis, duration, song_name, style,
        include_zoom=True,
    )


def build_video_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps = FORCE_FPS or profile["fps"]
    sx = min(profile.get("shake_x", 6), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 6), MAX_SHAKE_Y)
    shake_x, shake_y = build_elite_shake(analysis, sx, sy, style=style)
    return _assemble_all_fx(
        profile, analysis, duration, song_name, style,
        include_zoom=False,
        shake_x_expr=shake_x,
        shake_y_expr=shake_y,
    )


# ══════════════════════════════════════════════════════════════════════════════
# COMANDO FFMPEG
# ══════════════════════════════════════════════════════════════════════════════

def _build_cmd(
    inputs: list, vf: str, audio_filter: str,
    dur: float, output_name: str, audio_input_idx: int = 1,
) -> list:
    vf = sanitize_ffmpeg_filter(vf)
    cmd = ["ffmpeg", "-y", "-nostdin"] + inputs + ["-t", str(dur)]
    cmd += ["-vf", vf, "-map", "0:v", f"-map", f"{audio_input_idx}:a"]
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
        issues.append(f"Resolução: {info['width']}x{info['height']}")
    if abs(info["duration"] - expected_duration) > 2.0:
        issues.append(f"Duração: {info['duration']:.1f}s")
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
        "eq=contrast=1.28:brightness=-0.04:saturation=1.44,"
        "vignette=angle=0.82:mode=forward,"
        "drawbox=x=0:y=ih*0.72:w=iw:h=ih*0.28:color=black@0.72:t=fill,"
        f"drawtext=fontfile='{font}':text='{clean}'"
        ":fontsize=76:fontcolor=white:borderw=5:bordercolor=black@0.95"
        ":shadowx=5:shadowy=5:shadowcolor=black@0.8:x=(w-text_w)/2:y=h*0.78,"
        f"drawtext=fontfile='{font}':text='DJ DARK MARK'"
        ":fontsize=38:fontcolor=white@0.90:borderw=2:bordercolor=black@0.75"
        ":x=(w-text_w)/2:y=h*0.90"
    )
    vf = sanitize_ffmpeg_filter(vf)
    cmd = [
        "ffmpeg", "-y", "-nostdin", "-ss", str(timestamp),
        "-i", video_path, "-vframes", "1",
        "-vf", vf, "-q:v", "2", out,
    ]
    try:
        run_cmd_safe(cmd, "Thumbnail", FFMPEG_THUMB_TIMEOUT_S, capture=True)
        logger.info(f"  ► Thumbnail: {out}")
        return out
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        logger.warning(f"  ⚠ Thumbnail falhou: {e}")
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
    audio_analysis: Optional[dict] = None,
) -> dict:
    t_start = time.time()
    result: dict = {"output_path": None, "thumbnail_path": None, "video_id": None}

    output_dir = os.path.dirname(output_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    song_name = clean_song_name(audio_path, song_name)
    logger.info(f"▶ Gerando Short V15.0 APEX: '{song_name}' | estilo={style}")
    logger.info(f"  ► Neon: {GENRE_NEON.get(style, GENRE_NEON['default'])}")
    logger.info(f"  ► Qualidade: CRF={FFMPEG_CRF} | preset={FFMPEG_PRESET} | audio={FFMPEG_AUDIO_BITRATE}")

    logger.info("  ► Analisando áudio…")
    analysis_full = audio_analysis if isinstance(audio_analysis, dict) else full_analysis(audio_path)

    if _REMOTION_AVAILABLE:
        try:
            generate_audio_data(audio_path)
            logger.info("  ► audio_data.json gerado (Remotion sync)")
        except Exception as e:
            logger.warning(f"  ⚠ erro audio_data.json: {e}")

    bpm       = analysis_full.get("bpm")
    audio_dur = get_duration(audio_path)

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
            logger.info(f"  ► Janela: {start:.1f}s – {start+dur:.1f}s ({dur:.1f}s)")
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
    logger.info(f"  ► Kicks:{kicks} | Beats:{beats} | BPM:{bpm_text}")

    drop_time = analysis.get("drop_time")
    logger.info(f"  ► Drop: {drop_time:.2f}s" if drop_time else "  ► Drop: não detectado")

    profile      = get_profile_for_bpm(bpm, style)
    audio_filter = build_audio_filter(dur)

    ext      = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    if is_image:
        vf = build_image_filter(profile, analysis, dur, song_name, style)
        inputs = ["-loop", "1", "-i", background_path, "-ss", str(start), "-i", audio_path]
        cmd = _build_cmd(inputs, vf, audio_filter, dur, output_name, audio_input_idx=1)

    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        vf       = build_video_filter(profile, analysis, dur, song_name, style)
        inputs   = ["-ss", str(bg_start), "-i", background_path, "-ss", str(start), "-i", audio_path]
        cmd = _build_cmd(inputs, vf, audio_filter, dur, output_name, audio_input_idx=1)

    else:
        genre_g   = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
        fade      = build_fade_filter(dur)
        hyp       = build_hypnotic_beat_lights(analysis, style)
        eye       = build_eye_glow_hypnosis(analysis, style)
        scan      = build_scanlines_burst(analysis, style)
        strobo    = build_strobo_drop(analysis, style)
        hook      = build_hook_flash(style)
        rim       = build_rim_light_sync(analysis, style)
        vf        = join_filters([genre_g, hyp, eye, scan, strobo, hook, rim, fade])
        inputs    = [
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
            "-ss", str(start), "-i", audio_path,
        ]
        cmd = _build_cmd(inputs, vf, audio_filter, dur, output_name, audio_input_idx=1)

    logger.info("  ► Render V15.0 APEX…")
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            run_cmd_safe(cmd, "FFmpeg V15.0", FFMPEG_RENDER_TIMEOUT_S, capture=True)
            logger.info("  ► Render concluído ✓")
            break
        except subprocess.TimeoutExpired:
            if attempt <= MAX_RETRIES:
                logger.warning(f"  ⚠ Timeout tentativa {attempt}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY_S)
            else:
                raise
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="ignore") if e.stderr else "")
            if attempt <= MAX_RETRIES:
                logger.warning(f"  ⚠ Falhou tentativa {attempt}: {_tail(stderr, 400)}")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"  ✗ Render falhou após {MAX_RETRIES+1} tentativas.\n{_tail(stderr)}")
                raise

    validation = validate_output(output_name, dur)
    if validation["ok"]:
        info = validation["info"]
        logger.info(f"  ► OK — {info['width']}x{info['height']} | {info['duration']:.1f}s | {info['size_mb']}MB")
    else:
        for issue in validation["issues"]:
            logger.warning(f"  ⚠ {issue}")

    result.update({
        "output_path": output_name,
        "validation":  validation,
        "duration":    dur,
        "bpm":         bpm,
        "drop_time":   drop_time,
        "audio_data_path": "temp/audio_data.json" if os.path.exists("temp/audio_data.json") else None,
    })

    if auto_thumbnail:
        result["thumbnail_path"] = generate_thumbnail(output_name, song_name, style)

    elapsed = round(time.time() - t_start, 1)
    result["render_time_s"] = elapsed
    logger.info(f"✅ Finalizado em {elapsed}s — V15.0 APEX QUALITY")
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
            r["task"]   = task
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
    parser = argparse.ArgumentParser(description="DJ DARK MARK — Video Generator V15.0 APEX")
    parser.add_argument("audio")
    parser.add_argument("background")
    parser.add_argument("output")
    parser.add_argument("--style",    default="phonk", choices=list(GENRE_NEON.keys()))
    parser.add_argument("--name",     default="")
    parser.add_argument("--no-thumb", action="store_true")
    parser.add_argument("--upload",   action="store_true")
    parser.add_argument("--privacy",  default="private")
    parser.add_argument("--no-smart", action="store_true")
    args = parser.parse_args()
    create_short(
        audio_path=args.audio, background_path=args.background,
        output_name=args.output, style=args.style, song_name=args.name,
        use_smart_window=not args.no_smart,
        auto_thumbnail=not args.no_thumb,
        upload=args.upload, upload_privacy=args.privacy,
    )
