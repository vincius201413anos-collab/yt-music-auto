"""
video_generator.py — Elite Music Shorts Generator v6.0
=======================================================
MUDANÇAS v6.0 (LOGO BEAT-REACTIVE):
- Logo movida para o CENTRO do frame (posição premium)
- Sistema de pulse da logo sincronizado com o áudio:
    · Beat fraco  → logo pulsa +6%  (sutil)
    · Bass/kick   → logo cresce +20% + halo de glow
    · Drop        → logo explode +38% + glow máximo
- Glow animado: camada de brilho ao redor da logo que
  também pulsa porque é derivada do tamanho beat-reactive
- Zoom de fundo mais hipnótico (drift senoidal multi-axis)
- Todas as outras features da v5 mantidas intactas
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
MIN_DURATION        = 38
MAX_DURATION        = 58
VIDEO_FADE_OUT_DUR  = 0.7
AUDIO_FADE_IN       = 0.03
AUDIO_FADE_OUT      = 0.7
MAX_SHAKE_X         = 6
MAX_SHAKE_Y         = 6
DROP_ZOOM_PUNCH     = 0.12

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FFMPEG_VIDEO_CODEC   = "libx264"
FFMPEG_CRF           = "18"
FFMPEG_PRESET        = "medium"
FFMPEG_AUDIO_CODEC   = "aac"
FFMPEG_AUDIO_BITRATE = "192k"

# ── Logo — sistema v6.0 (centralizada + beat-reactive) ─────────────────────
LOGO_PATH = "assets/logo_darkmark.png"

# Tamanho base da logo: 22% da largura do vídeo (~237px em 1080p)
LOGO_BASE_WIDTH_RATIO = 0.22

# Posição vertical: centro exato (50% do frame)
# Logo no centro real do Short
LOGO_CENTER_Y_RATIO = 0.50

# Opacidade da logo principal
LOGO_OPACITY = 0.92

# Glow — camada de brilho ao redor da logo
LOGO_GLOW_SCALE      = 1.45   # glow é 45% maior que a logo
LOGO_GLOW_BLUR       = 14     # raio do blur do glow (pixels)
LOGO_GLOW_OPACITY    = 0.52   # opacidade do glow (0-1)
LOGO_GLOW_BRIGHTNESS = 3.2    # multiplicador de brilho do glow

# Intensidade do pulse por tipo de evento
LOGO_PULSE_BEAT_STRENGTH = 0.06   # beat fraco:  +6%
LOGO_PULSE_BASS_STRENGTH = 0.20   # kick/baixo:  +20%
LOGO_PULSE_DROP_STRENGTH = 0.38   # drop:        +38%

# Velocidade de decaimento do pulse (segundos)
LOGO_PULSE_BEAT_DECAY = 0.10
LOGO_PULSE_BASS_DECAY = 0.08
LOGO_PULSE_DROP_DECAY = 0.30

# Limites máximos de batidas para expressões (performance)
LOGO_MAX_BEATS     = 10
LOGO_MAX_BASS_HITS = 6

THUMB_DIR       = "thumbnails"
THUMB_TIMESTAMP = 1.5

MAX_RETRIES     = 2
RETRY_DELAY_S   = 3

MIN_FILE_SIZE_MB = 0.5
MAX_FILE_SIZE_MB = 200.0

# ── Grading de cor por gênero ──────────────────────────────────────────────
GENRE_COLOR_GRADE = {
    "phonk": (
        "colorbalance=rs=0.28:gs=-0.12:bs=-0.18,"
        "eq=contrast=1.45:brightness=-0.05:saturation=1.35,"
        "unsharp=5:5:1.8:5:5:0,"
        "noise=alls=14:allf=t+u"
    ),
    "lofi": (
        "colorbalance=rs=0.12:gs=0.04:bs=-0.16,"
        "eq=contrast=0.92:brightness=0.025:saturation=0.82,"
        "unsharp=3:3:0.3:3:3:0,"
        "noise=alls=6:allf=t"
    ),
    "trap": (
        "colorbalance=rs=-0.10:gs=0.04:bs=0.20,"
        "eq=contrast=1.28:brightness=0.008:saturation=1.30,"
        "unsharp=5:5:1.1:5:5:0"
    ),
    "dark": (
        "colorbalance=rs=-0.06:gs=-0.08:bs=0.22,"
        "eq=contrast=1.42:brightness=-0.07:saturation=0.68,"
        "unsharp=5:5:1.2:5:5:0,"
        "vignette=angle=PI/3.0:mode=forward"
    ),
    "electronic": (
        "colorbalance=rs=-0.14:gs=0.08:bs=0.26,"
        "eq=contrast=1.22:brightness=0.012:saturation=1.70,"
        "unsharp=5:5:0.9:5:5:0"
    ),
    "rock": (
        "colorbalance=rs=0.16:gs=0.06:bs=-0.12,"
        "eq=contrast=1.26:brightness=0.005:saturation=1.22,"
        "unsharp=5:5:1.2:5:5:0,"
        "noise=alls=10:allf=t"
    ),
    "metal": (
        "colorbalance=rs=-0.14:gs=-0.10:bs=0.12,"
        "eq=contrast=1.48:brightness=-0.06:saturation=0.75,"
        "unsharp=5:5:1.4:5:5:0,"
        "vignette=angle=PI/2.8:mode=forward"
    ),
    "indie": (
        "colorbalance=rs=0.08:gs=0.06:bs=-0.08,"
        "eq=contrast=0.98:brightness=0.022:saturation=0.90,"
        "unsharp=3:3:0.3:3:3:0,"
        "noise=alls=5:allf=t"
    ),
    "cinematic": (
        "colorbalance=rs=0.14:gs=-0.02:bs=-0.16,"
        "colorbalance=rs=-0.10:gs=0.04:bs=0.18:shadows=enable:highlights=disable,"
        "eq=contrast=1.16:brightness=0.005:saturation=1.12,"
        "unsharp=5:5:0.9:5:5:0"
    ),
    "funk": (
        "colorbalance=rs=0.22:gs=0.08:bs=-0.18,"
        "eq=contrast=1.18:brightness=0.015:saturation=1.55,"
        "unsharp=3:3:0.5:3:3:0"
    ),
    "pop": (
        "colorbalance=rs=0.05:gs=0.04:bs=0.05,"
        "eq=contrast=1.10:brightness=0.020:saturation=1.40,"
        "unsharp=3:3:0.6:3:3:0"
    ),
    "default": (
        "eq=contrast=1.14:brightness=0.010:saturation=1.15,"
        "unsharp=5:5:0.8:5:5:0"
    ),
}

GENRE_VIGNETTE = {
    "phonk": 0.65, "dark": 0.0, "metal": 0.0, "lofi": 0.30,
    "trap": 0.20, "electronic": 0.10, "rock": 0.35, "indie": 0.24,
    "cinematic": 0.40, "funk": 0.12, "pop": 0.10, "default": 0.32,
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
# ── Cyberpunk water/reflection FX v6.1 ─────────────────────────────────────
# Efeito visual seguro (sem mexer na análise de áudio): cria brilho de água,
# reflexo neon e linhas de luz no chão molhado. Funciona tanto com imagem quanto
# com vídeo e não depende de plugins externos do FFmpeg.
WATER_FX_ENABLED = True
WATER_FX_START_Y_RATIO = 0.54      # começa da metade pra baixo do frame
WATER_FX_BASE_ALPHA = 0.035        # brilho base da água
WATER_FX_LINE_ALPHA = 0.18         # linhas neon refletidas
WATER_FX_BASS_ALPHA = 0.12         # boost no grave/kick
WATER_FX_MAX_BASS_HITS = 45



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
    dur = random.randint(MIN_DURATION, min(MAX_DURATION, max(MIN_DURATION, int(audio_dur))))
    if audio_dur <= dur:
        return 0.0, float(audio_dur)
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
    text = text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")
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
# SISTEMA DE LOGO BEAT-REACTIVE v6.0
# ══════════════════════════════════════════════════════════════════════════════

def build_logo_pulse_expr(analysis: dict, base_width: int) -> str:
    """
    Constrói a expressão FFmpeg de largura da logo que reage ao beat.

    A expressão usa `t` (tempo em segundos) para calcular a distância
    até cada batida e aplica um envelope de decaimento linear.

    Mapa de intensidade:
        Beat fraco   → +6%  scale  (pulse sutil, sempre presente)
        Bass / kick  → +20% scale  (impacto visível)
        Drop         → +38% scale  (máximo impacto, glow explode)
    """
    beats     = analysis.get("beats", [])
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")

    parts = []

    # ── Beats fracos ──────────────────────────────────────────────────
    for t in beats[:LOGO_MAX_BEATS]:
        parts.append(
            f"{LOGO_PULSE_BEAT_STRENGTH:.3f}"
            f"*max(0,1-abs(t-{t:.4f})/{LOGO_PULSE_BEAT_DECAY:.3f})"
        )

    # ── Bass / kick ────────────────────────────────────────────────────
    for t in bass_hits[:LOGO_MAX_BASS_HITS]:
        parts.append(
            f"{LOGO_PULSE_BASS_STRENGTH:.3f}"
            f"*max(0,1-abs(t-{t:.4f})/{LOGO_PULSE_BASS_DECAY:.3f})"
        )

    # ── Drop ───────────────────────────────────────────────────────────
    if drop_time is not None:
        parts.append(
            f"{LOGO_PULSE_DROP_STRENGTH:.3f}"
            f"*max(0,1-abs(t-{drop_time:.4f})/{LOGO_PULSE_DROP_DECAY:.3f})"
        )

    if parts:
        pulse_sum = "+".join(parts)
        return f"({base_width}*(1+{pulse_sum}))"

    return str(base_width)


def build_logo_center_overlay_filter(analysis: dict) -> str:
    """
    Gera os segmentos do filter_complex para a logo centralizada
    com pulse beat-reactive e camada de glow animada.

    Grafo de filtros:
        [1:v]
          └─ scale(w=beat_expr, eval=frame)   ← tamanho pulsa com o beat
          └─ format(rgba) + opacity
          └─ split ─────────────────────────────┐
               ├─ [ls_sharp]                    │  (logo nítida, centro)
               └─ [ls_glow_src]                 │
                    └─ scale(iw*1.45)            │  ← glow maior (e também pulsa!)
                    └─ boxblur(14)               │
                    └─ colorchannelmixer(brilho) │
                    └─ [logo_glow] (centro, sob a sharp)
        [base][logo_glow] overlay(center) → [bg_glow]
        [bg_glow][ls_sharp] overlay(center) → [vout]
    
    Nota: como o glow é derivado do ls_glow_src (que já veio do split
    pós-scale), ele TAMBÉM pulsa com o beat → glow reativo automático.
    """
    base_w     = int(1080 * LOGO_BASE_WIDTH_RATIO)
    pulse_expr = str(base_w)

    # Posição central (ligeiramente abaixo do meio)
    cx = "(W-w)/2"
    cy = f"H*{LOGO_CENTER_Y_RATIO:.2f}-h/2"

    return (
        # Logo simples e segura: centro do vídeo, sem pulse e sem glow pesado.
        # Isso evita erro do FFmpeg em filter_complex e mantém a logo visível.
        f"[1:v]"
        f"scale=w='{pulse_expr}':h=-1:eval=frame,"
        f"format=rgba,"
        f"colorchannelmixer=aa={LOGO_OPACITY:.2f}"
        f"[logo_scaled];"

        f"[base][logo_scaled]overlay=x='{cx}':y='{cy}':format=auto[vout]"
    )


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS DE ÁUDIO E VÍDEO
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
    b = 0.18
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


def build_vignette(strength: float) -> str:
    if strength <= 0:
        return ""
    angle = round(strength * 1.10, 3)
    return f"vignette=angle={angle}:mode=forward"



def build_cyberpunk_water_fx(analysis: dict, style: str = "default") -> str:
    """
    Camada de acabamento visual para água/reflexo cyberpunk.

    O objetivo é melhorar a cena sem quebrar o pipeline:
    - brilho base na parte inferior (como chão molhado / água)
    - linhas neon horizontais simulando reflexos
    - pulso extra no bass/kick usando bass_hits

    É propositalmente feito com drawbox/eq, porque esses filtros são estáveis
    no FFmpeg do GitHub Actions e não exigem plugins externos.
    """
    if not WATER_FX_ENABLED:
        return ""

    bass_hits = analysis.get("bass_hits", [])[:WATER_FX_MAX_BASS_HITS]

    # Cores por estilo: puxa para cyberpunk azul/roxo/rosa.
    if style in {"phonk", "dark", "trap", "electronic"}:
        c1 = "0x00CCFF"   # cyan neon
        c2 = "0xCC44FF"   # purple neon
        c3 = "0xFF2DAA"   # magenta neon
    elif style in {"rock", "metal"}:
        c1 = "0xFF5500"
        c2 = "0xCC44FF"
        c3 = "0x00CCFF"
    else:
        c1 = "0x00CCFF"
        c2 = "0xCC44FF"
        c3 = "0xFF44AA"

    filters = []

    # Brilho base na região da água/chão molhado.
    filters.append(
        f"drawbox=x=0:y=ih*{WATER_FX_START_Y_RATIO:.2f}:w=iw:h=ih*(1-{WATER_FX_START_Y_RATIO:.2f})"
        f":color={c1}@{WATER_FX_BASE_ALPHA:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x=0:y=ih*0.68:w=iw:h=ih*0.32"
        f":color={c2}@{WATER_FX_BASE_ALPHA * 0.75:.3f}:t=fill"
    )

    # Linhas neon finas simulando reflexo tremendo na água.
    # Elas se mexem suavemente com sin(t), sem deixar a cena artificial.
    filters.append(
        f"drawbox=x='iw*0.08+24*sin(t*0.70)':y='ih*0.70+10*sin(t*1.10)'"
        f":w='iw*0.78':h=3:color={c1}@{WATER_FX_LINE_ALPHA:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x='iw*0.16+18*sin(t*0.95+1.4)':y='ih*0.78+12*sin(t*1.35)'"
        f":w='iw*0.66':h=2:color={c2}@{WATER_FX_LINE_ALPHA * 0.85:.3f}:t=fill"
    )
    filters.append(
        f"drawbox=x='iw*0.25+20*sin(t*0.55+2.1)':y='ih*0.86+9*sin(t*1.60)'"
        f":w='iw*0.50':h=2:color={c3}@{WATER_FX_LINE_ALPHA * 0.70:.3f}:t=fill"
    )

    # Pulsos rápidos no grave: dá sensação da água/reflexo reagindo à música.
    # Cada pulso aparece só por alguns frames, então fica sutil e profissional.
    for i, bt in enumerate(bass_hits):
        alpha = WATER_FX_BASS_ALPHA if i < 25 else WATER_FX_BASS_ALPHA * 0.65
        filters.append(
            f"drawbox=enable='between(t,{max(0.0, bt-0.012):.4f},{bt+0.060:.4f})'"
            f":x=0:y=ih*0.58:w=iw:h=ih*0.42:color={c1}@{alpha:.3f}:t=fill"
        )

    # Pequeno polish global para reforçar o look gráfico sem estourar a imagem.
    filters.append("eq=gamma=1.015:saturation=1.035")

    return ",".join(filters)

def build_fade_filter(duration: float) -> str:
    fo_start = max(0.0, duration - VIDEO_FADE_OUT_DUR)
    return f"fade=t=out:st={fo_start:.3f}:d={VIDEO_FADE_OUT_DUR}"


def build_energy_ring(analysis: dict, duration: float, style: str, font: str) -> str:
    bass_hits = analysis.get("bass_hits", [])
    drop_time = analysis.get("drop_time")
    energy_color = GENRE_ENERGY_RGBA.get(style, "0xCC44FF@0.9")

    cx = 540
    cy = 960
    ring_r = 180

    energy_flash_parts = []

    energy_flash_parts.append(
        f"drawbox=x={cx-ring_r}:y={cy-ring_r}"
        f":w={ring_r*2}:h={ring_r*2}"
        f":color={energy_color.replace('@0.9', '@0.08').replace('@0.85', '@0.08').replace('@0.8', '@0.08').replace('@0.75', '@0.08')}:t=fill"
    )

    if bass_hits:
        flash_w = ring_r * 3
        for i, t in enumerate(bass_hits[:80]):
            t_start = max(0.0, t - 0.010)
            t_end   = t + 0.055
            color_flash = energy_color.replace("@0.9","@0.45").replace("@0.85","@0.40").replace("@0.8","@0.35").replace("@0.75","@0.32")
            if i < 40:
                energy_flash_parts.append(
                    f"drawbox=enable='between(t,{t_start:.4f},{t_end:.4f})'"
                    f":x={cx - flash_w//2}:y={cy - flash_w//2}"
                    f":w={flash_w}:h={flash_w}"
                    f":color={color_flash}:t=fill"
                )

    if drop_time is not None:
        drop_w = ring_r * 5
        color_drop = energy_color.replace("@0.9","@0.70").replace("@0.85","@0.65").replace("@0.8","@0.60").replace("@0.75","@0.55")
        energy_flash_parts.append(
            f"drawbox=enable='between(t,{drop_time-0.01:.4f},{drop_time+0.12:.4f})'"
            f":x={cx - drop_w//2}:y={cy - drop_w//2}"
            f":w={drop_w}:h={drop_w}"
            f":color={color_drop}:t=fill"
        )

    return ",".join(energy_flash_parts)


def build_hook_text(song_name: str, style: str, font: str, duration: float) -> str:
    clean     = escape_text(song_name)
    style_tag = escape_text(f"#{style.upper()} · DJ darkMark")

    title_alpha = (
        "if(lt(t,0.03),0,"
        "if(lt(t,0.22),(t/0.22),"
        f"if(lt(t,{duration-1.2:.2f}),1.0,"
        f"if(lt(t,{duration:.2f}),({duration:.2f}-t)/1.2,0))))"
    )

    title = (
        f"drawtext=fontfile='{font}'"
        f":text='{clean}'"
        f":fontsize=58:fontcolor=white"
        f":borderw=4:bordercolor=black@0.95"
        f":shadowx=3:shadowy=3:shadowcolor=black@0.8"
        f":x=(w-text_w)/2:y=h*0.08"
        f":alpha='{title_alpha}'"
    )

    tag_alpha = (
        "if(lt(t,0.12),0,"
        "if(lt(t,0.35),(t-0.12)/0.23,"
        f"if(lt(t,{duration-1.2:.2f}),0.90,"
        f"if(lt(t,{duration:.2f}),({duration:.2f}-t)/1.2,0))))"
    )
    tag = (
        f"drawtext=fontfile='{font}'"
        f":text='{style_tag}'"
        f":fontsize=26:fontcolor=white@0.85"
        f":borderw=2:bordercolor=black@0.80"
        f":x=(w-text_w)/2:y=h*0.08+64"
        f":alpha='{tag_alpha}'"
    )

    return f"{title},{tag}"


def build_progress_bar(duration: float, style: str = "default") -> str:
    color = GENRE_ENERGY_RGBA.get(style, "0xCC44FF@0.9")
    return (
        "drawbox=x=0:y=ih-8:w=iw:h=8:color=black@0.60:t=fill,"
        f"drawbox=x=0:y=ih-8:w='iw*t/{duration:.3f}':h=8:color={color}:t=fill"
    )


def build_watermark(font: str) -> str:
    return (
        f"drawtext=fontfile='{font}'"
        f":text='@darkmrkedit'"
        f":fontsize=22:fontcolor=white@0.50"
        f":borderw=1:bordercolor=black@0.40"
        f":x=w-text_w-16:y=18"
        f":alpha='if(lt(t,1.2),0,if(lt(t,1.8),(t-1.2)/0.6,0.50))'"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ZOOM HIPNÓTICO DO FUNDO
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
    intro_frames = int(0.20 * fps)

    heavy = style in {"phonk", "metal", "rock", "trap", "electronic", "funk"}
    zoom_mult = 1.4 if heavy else 1.0

    # ── Zoom cíclico base (movimento hipnótico) ────────────────────────────
    base  = f"(1.0 + {zoom_speed * zoom_mult}*(0.5-0.5*cos(2*PI*on/{total_frames})))"

    # ── Drift multi-axis senoidal (mais orgânico que v5) ──────────────────
    drift = (
        f"({pulse_strength * 0.6}*sin(on*0.06+0.2)*cos(on*0.028)+"
        f"{pulse_strength * 0.3}*sin(on*0.11+1.4))"
    )

    # ── Pulsos nos beats ───────────────────────────────────────────────────
    beat_pulse = "0"
    if beats:
        parts = [
            f"0.0045*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.08*fps))})"
            for b in beats[:80]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    # ── Pulso de bass / kick ───────────────────────────────────────────────
    bass_pulse = "0"
    if bass_hits:
        intensity = 0.018 if heavy else 0.011
        parts = [
            f"{intensity}*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.06*fps))})"
            for b in bass_hits[:70]
        ]
        bass_pulse = f"({'+'.join(parts)})"

    # ── Punch no drop ─────────────────────────────────────────────────────
    drop_punch = DROP_ZOOM_PUNCH * (1.5 if heavy else 1.0)
    drop_expr = "0"
    if drop_time is not None:
        df = int(drop_time * fps)
        drop_expr = (
            f"({drop_punch:.3f}*max(0,1-abs(on-{df})/{max(1,int(0.05*fps))})+"
            f"0.050*max(0,({int(0.4*fps)}-abs(on-{df+int(0.1*fps)}))/{int(0.4*fps)}))"
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

    heavy = style in {"phonk", "metal", "rock", "trap", "funk"}
    shake_mult = 1.5 if heavy else 1.0

    shake_x = f"(sin(t*2.9)*{sx*0.70*shake_mult}+sin(t*5.2)*{sx*0.30*shake_mult})"
    shake_y = f"(cos(t*2.6)*{sy*0.70*shake_mult}+cos(t*4.8)*{sy*0.30*shake_mult})"

    if bass_hits:
        boost_int = 2.0 if heavy else 1.6
        boosts = [
            f"{boost_int}*max(0,1-abs(t-{t:.4f})/{0.12:.3f})"
            for t in bass_hits[:60]
        ]
        boost = f"(1+{'+'.join(boosts)})"
        shake_x = f"({shake_x})*{boost}"
        shake_y = f"({shake_y})*{boost}"

    if drop_time is not None:
        drop_mult_val = 4.0 if heavy else 2.8
        drop_mult = f"(1+{drop_mult_val}*max(0,1-abs(t-{drop_time:.4f})/0.25))"
        shake_x = f"({shake_x})*{drop_mult}"
        shake_y = f"({shake_y})*{drop_mult}"

    hook_gate = "if(lt(t,0.08),0.02,1.0)"
    shake_x = f"({shake_x})*{hook_gate}"
    shake_y = f"({shake_y})*{hook_gate}"

    return shake_x, shake_y


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS COMPLETOS (sem logo — a logo é adicionada via filter_complex)
# ══════════════════════════════════════════════════════════════════════════════

def build_image_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    """Filtro para fundo estático (imagem PNG/JPG gerada por AI)."""
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
    vig   = build_vignette(vig_strength)
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font, duration)
    pbar  = build_progress_bar(duration, style)
    wtmk  = build_watermark(font)
    energy = build_energy_ring(analysis, duration, style, font)

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
    if vig:
        parts.append(vig)

    parts.append(energy)
    parts += [fades, f"fps={fps}", hook, pbar, wtmk]
    return ",".join(parts)


def build_video_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    """Filtro para fundo de vídeo (MP4/MOV)."""
    fps  = profile["fps"]
    font = get_font()
    brightness_expr = build_combined_brightness(profile, analysis)
    sx = min(profile.get("shake_x", 4), MAX_SHAKE_X)
    sy = min(profile.get("shake_y", 4), MAX_SHAKE_Y)
    shake_x_expr, shake_y_expr = build_elite_shake(analysis, sx, sy, style=style)
    color = build_color_grade(profile, brightness_expr, style)
    water_fx = build_cyberpunk_water_fx(analysis, style)
    vig_strength = GENRE_VIGNETTE.get(style, GENRE_VIGNETTE["default"])
    vig   = build_vignette(vig_strength)
    fades = build_fade_filter(duration)
    hook  = build_hook_text(song_name, style, font, duration)
    pbar  = build_progress_bar(duration, style)
    wtmk  = build_watermark(font)
    energy = build_energy_ring(analysis, duration, style, font)

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
    if vig:
        parts.append(vig)

    parts.append(energy)
    parts += [fades, f"fps={fps}", hook, pbar, wtmk]
    return ",".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# MONTAGEM DO COMANDO FFMPEG
# ══════════════════════════════════════════════════════════════════════════════

def _build_cmd(
    inputs: list, vf_or_complex: str,
    is_complex: bool, use_logo: bool,
    audio_filter: str, dur: float, output_name: str,
    audio_input_idx: int = 1,
) -> list:
    """
    Monta o comando FFmpeg final.

    Parâmetro audio_input_idx indica qual input é o áudio:
    - sem logo: áudio é input [1]
    - com logo: áudio é input [2] (logo é [1])
    """
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
    tag   = escape_text(f"#{style.upper()}")
    genre_grade = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
    vf = (
        f"{genre_grade},"
        "eq=contrast=1.18:brightness=-0.02:saturation=1.28,"
        "vignette=angle=0.65:mode=forward,"
        "drawbox=x=0:y=ih*0.74:w=iw:h=ih*0.26:color=black@0.62:t=fill,"
        f"drawtext=fontfile='{font}':text='{clean}'"
        ":fontsize=72:fontcolor=white:borderw=4:bordercolor=black@0.92"
        ":shadowx=4:shadowy=4:shadowcolor=black@0.7"
        ":x=(w-text_w)/2:y=h*0.78,"
        f"drawtext=fontfile='{font}':text='{tag}'"
        ":fontsize=38:fontcolor=white@0.88:borderw=2:bordercolor=black@0.75"
        ":x=(w-text_w)/2:y=h*0.89"
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
    logger.info(f"  ► Energy color: {GENRE_ENERGY_COLOR.get(style, 'default')}")

    # ── Análise de áudio ──────────────────────────────────────────────────
    logger.info("  ► Analisando áudio (kick isolation ativa)…")
    analysis_full = full_analysis(audio_path)
    bpm           = analysis_full.get("bpm")
    audio_dur     = get_duration(audio_path)

    # ── Janela de tempo ───────────────────────────────────────────────────
    if use_smart_window:
        dur = random.randint(MIN_DURATION, min(MAX_DURATION, int(audio_dur)))
        try:
            start, dur = find_best_window(audio_path, dur)
            logger.info(f"  ► Janela inteligente: {start:.1f}s – {start+dur:.1f}s")
        except Exception:
            start, dur = pick_window(audio_dur)
            logger.info(f"  ► Janela fallback: {start:.1f}s – {start+dur:.1f}s")
    else:
        start, dur = pick_window(audio_dur)

    analysis = crop_analysis(analysis_full, start, dur)
    save_debug({**analysis_full, "short_start": start, "short_duration": dur})

    kicks    = len(analysis.get("bass_hits", []))
    beats    = len(analysis.get("beats", []))
    bpm_text = f"{bpm:.1f}" if bpm else "N/A"
    logger.info(f"  ► Kicks: {kicks} | Beats: {beats} | BPM: {bpm_text}")

    # Log do drop detectado
    drop_time = analysis.get("drop_time")
    if drop_time is not None:
        logger.info(f"  ► Drop detectado em: {drop_time:.2f}s")
    else:
        logger.info("  ► Drop: não detectado")

    profile      = get_profile_for_bpm(bpm, style)
    audio_filter = build_audio_filter(dur)
    use_logo     = logo_exists()

    if use_logo:
        logger.info(f"  ► Logo encontrada: {LOGO_PATH} → modo CENTRO beat-reactive")
    else:
        logger.info(f"  ⚠ Logo não encontrada em '{LOGO_PATH}' — renderizando sem logo")

    ext      = Path(background_path).suffix.lower() if background_path else ""
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    is_video = ext in (".mp4", ".mov", ".mkv", ".webm", ".gif")

    # ── IMAGEM como fundo ─────────────────────────────────────────────────
    if is_image:
        base_vf = build_image_filter(profile, analysis, dur, song_name, style)

        if use_logo:
            # filter_complex: fundo → [base]; logo beat-reactive → [vout]
            logo_fc = build_logo_center_overlay_filter(analysis)
            fc = f"[0:v]{base_vf}[base];{logo_fc}"
            inputs = [
                "-loop", "1", "-i", background_path,   # [0] fundo
                "-i", LOGO_PATH,                         # [1] logo
                "-ss", str(start), "-i", audio_path,     # [2] áudio
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name,
                             audio_input_idx=2)
        else:
            inputs = [
                "-loop", "1", "-i", background_path,   # [0] fundo
                "-ss", str(start), "-i", audio_path,     # [1] áudio
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                             audio_input_idx=1)

    # ── VÍDEO como fundo ──────────────────────────────────────────────────
    elif is_video:
        bg_dur   = get_duration(background_path)
        bg_start = 0.0 if bg_dur <= dur else random.uniform(0.0, bg_dur - dur)
        base_vf  = build_video_filter(profile, analysis, dur, song_name, style)

        if use_logo:
            logo_fc = build_logo_center_overlay_filter(analysis)
            fc = f"[0:v]{base_vf}[base];{logo_fc}"
            inputs = [
                "-ss", str(bg_start), "-i", background_path,  # [0] vídeo
                "-i", LOGO_PATH,                                # [1] logo
                "-ss", str(start), "-i", audio_path,            # [2] áudio
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name,
                             audio_input_idx=2)
        else:
            inputs = [
                "-ss", str(bg_start), "-i", background_path,  # [0] vídeo
                "-ss", str(start), "-i", audio_path,            # [1] áudio
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                             audio_input_idx=1)

    # ── FALLBACK: fundo preto ─────────────────────────────────────────────
    else:
        font    = get_font()
        hook    = build_hook_text(song_name, style, font, dur)
        pbar    = build_progress_bar(dur, style)
        wtmk    = build_watermark(font)
        fade    = build_fade_filter(dur)
        energy  = build_energy_ring(analysis, dur, style, font)
        genre_g = GENRE_COLOR_GRADE.get(style, GENRE_COLOR_GRADE["default"])
        base_vf = f"{genre_g},{energy},{fade},{hook},{pbar},{wtmk}"

        if use_logo:
            logo_fc = build_logo_center_overlay_filter(analysis)
            fc = f"[0:v]{base_vf}[base];{logo_fc}"
            inputs = [
                "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",  # [0]
                "-i", LOGO_PATH,                                               # [1]
                "-ss", str(start), "-i", audio_path,                          # [2]
            ]
            cmd = _build_cmd(inputs, fc, True, True, audio_filter, dur, output_name,
                             audio_input_idx=2)
        else:
            inputs = [
                "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",  # [0]
                "-ss", str(start), "-i", audio_path,                          # [1]
            ]
            cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                             audio_input_idx=1)

    # ── Render ────────────────────────────────────────────────────────────
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
    parser = argparse.ArgumentParser(description="Elite Music Shorts Generator v6 — Logo Beat-Reactive")
    parser.add_argument("audio")
    parser.add_argument("background")
    parser.add_argument("output")
    parser.add_argument("--style",    default="trap", choices=list_profiles())
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
