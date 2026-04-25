"""
video_generator.py — Elite Music Shorts Generator v11 FINAL VIBRANT HYPNOTIC
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

FIX v8.1:
- Removido parâmetro 'shadows=enable' do filtro colorbalance (não suportado pelo FFmpeg do runner).
  Substituído por dois filtros colorbalance separados: um para sombras (rs/gs/bs baixo) e outro
  para highlights (rs/gs/bs alto), que é a forma correta e compatível.

FIX v8.2 SAFE RUNNER:
- Adicionado timeout no FFmpeg para impedir render infinito no GitHub Actions.
- Logs de erro do FFmpeg agora aparecem com trecho final limpo.
- Thumbnail também ganhou timeout para não prender o job.
- IMPORTANTE: este arquivo gera a base FFmpeg. Se o log travar em "Iniciando render Remotion",
  o ponto final do travamento está no arquivo que chama o Remotion depois deste gerador.

V11.1 HOTFIX DRAWBOX ALPHA:
- Corrigido alpha dinâmico no drawbox: FFmpeg do GitHub Actions não aceita @expressao com sin(t).
- Mantida vibe hipnótica com alpha fixo seguro para não quebrar o render.

V11.2 SAFE GITHUB ACTIONS:
- Corrigido unsharp com matriz par 4x4, que quebra no FFmpeg do runner.
- Adicionado sanitizador final de filtros FFmpeg antes do render.
- Removido PI/2.5 em vignette para número fixo compatível.
- Mantidos efeitos neon/beat, mas só com sintaxe segura para GitHub Actions.

V11 FINAL VIBRANT HYPNOTIC:
- Luzes vibrantes no beat/kick com overlays neon bonitos e controlados.
- Glitch mais forte no drop, sem pesar demais no GitHub.
- Glow central/olhos bonito e controlado para sensação hipnótica.
- Movimento constante mais vivo: micro pulso + respiração visual.
- Mantém FFmpeg seguro, sem Remotion obrigatório.
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
DROP_ZOOM_PUNCH     = 0.28

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

FFMPEG_VIDEO_CODEC   = "libx264"
FFMPEG_CRF           = os.getenv("FFMPEG_CRF", "20")
FFMPEG_PRESET        = os.getenv("FFMPEG_PRESET", "veryfast")
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

# Segurança contra travamento infinito no GitHub Actions / runners fracos
FFMPEG_RENDER_TIMEOUT_S = int(os.getenv("FFMPEG_RENDER_TIMEOUT", "720"))   # 12 min
FFMPEG_THUMB_TIMEOUT_S  = int(os.getenv("FFMPEG_THUMB_TIMEOUT", "120"))    # 2 min
FINAL_GRAIN_STRENGTH  = int(os.getenv("FINAL_GRAIN_STRENGTH", "4"))
FORCE_FPS             = int(os.getenv("FFMPEG_FPS", "30"))

# V10 — luzes hipnóticas sincronizadas no beat
HYPNOTIC_LIGHTS_ENABLED = os.getenv("HYPNOTIC_LIGHTS_ENABLED", "true").lower() == "true"
HYPNOTIC_LIGHT_INTENSITY = float(os.getenv("HYPNOTIC_LIGHT_INTENSITY", "0.82"))
HYPNOTIC_MAX_BEATS = int(os.getenv("HYPNOTIC_MAX_BEATS", "46"))
HYPNOTIC_MAX_BASS = int(os.getenv("HYPNOTIC_MAX_BASS", "36"))
HYPNOTIC_MAX_SNARES = int(os.getenv("HYPNOTIC_MAX_SNARES", "18"))
EYE_GLOW_ENABLED = os.getenv("EYE_GLOW_ENABLED", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════════════════
# COLOR GRADES — v8.1 CYBERPUNK MÁXIMO
# FIX: 'shadows=enable' e 'highlights=enable' não são parâmetros válidos do
# filtro colorbalance. O filtro aceita apenas rs/gs/bs/rm/gm/bm/rh/gh/bh.
# Separamos em dois colorbalance encadeados para simular o mesmo efeito.
# ══════════════════════════════════════════════════════════════════════════════
GENRE_COLOR_GRADE = {
    "phonk": (
        # FINAL: roxo/rosa/vermelho vibrante sem destruir pele/rosto.
        "colorbalance=rs=0.20:gs=-0.09:bs=0.12,"
        "colorbalance=rh=-0.06:gh=0.04:bh=0.22,"
        "eq=contrast=1.40:brightness=-0.045:saturation=1.30:gamma=0.95,"
        "curves=r='0/0 0.25/0.10 1/1':g='0/0 0.30/0.08 1/0.88':b='0/0 0.18/0.23 1/1',"
        "unsharp=5:5:1.8:5:5:0,"
        "noise=alls=7:allf=t+u"
    ),
    "trap": (
        # FINAL: ciano/roxo bonito, sem azul artificial chapado.
        "colorbalance=rs=-0.08:gs=0.04:bs=0.18,"
        "colorbalance=rh=-0.04:gh=0.08:bh=0.20,"
        "eq=contrast=1.36:brightness=-0.040:saturation=1.30:gamma=0.96,"
        "curves=r='0/0 0.3/0.10 1/0.92':b='0/0 0.2/0.20 1/1',"
        "unsharp=5:5:1.5:5:5:0,"
        "noise=alls=5:allf=t+u"
    ),
    "dark": (
        # FINAL: escuro, bonito, roxo/rosa controlado.
        "colorbalance=rs=0.02:gs=-0.10:bs=0.28,"
        "colorbalance=rh=0.10:gh=-0.04:bh=0.18,"
        "eq=contrast=1.44:brightness=-0.075:saturation=1.12:gamma=0.93,"
        "curves=all='0/0 0.16/0.03 0.55/0.42 1/1',"
        "unsharp=5:5:1.45:5:5:0,"
        "noise=alls=6:allf=t+u"
    ),
    "electronic": (
        # Ciano + magenta — bifurcação neon
        "colorbalance=rs=-0.20:gs=0.15:bs=0.38,"
        "colorbalance=rh=0.30:gh=-0.10:bh=0.20,"
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
        "vignette=angle=1.257:mode=forward"
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
        "colorbalance=rs=-0.08:gs=-0.05:bs=0.30,"
        "colorbalance=rh=-0.08:gh=-0.05:bh=0.30,"
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
WATER_FX_BASE_ALPHA = 0.020
WATER_FX_LINE_ALPHA = 0.075
WATER_FX_BASS_ALPHA = 0.055
WATER_FX_MAX_BASS_HITS = 22

# Controle viral: efeitos de FFmpeg servem como base, não como protagonista.
# O protagonista final é o Remotion.
VIRAL_FX_MODE = True
KEEP_FFMPEG_PROGRESS_BAR = False
SCANLINE_BASE_ALPHA = 0.016
SCANLINE_BASS_ALPHA = 0.065
GLITCH_MAX_HITS = 7
BORDER_MAX_HITS = 12



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


def _odd_ffmpeg_kernel(value: str, fallback: int = 5) -> str:
    """FFmpeg unsharp exige matrizes ímpares: 3, 5, 7..."""
    try:
        n = int(float(value))
    except Exception:
        return str(fallback)
    if n < 3:
        n = 3
    if n % 2 == 0:
        n += 1
    return str(n)


def sanitize_ffmpeg_filter(vf: str) -> str:
    """
    Camada final de segurança para GitHub Actions.
    Corrige automaticamente:
    - unsharp=4:4 / 6:6 etc. para tamanho ímpar
    - alpha dinâmico em drawbox/color, que quebra no runner
    - PI/2.5 em vignette para número fixo
    """
    if not vf:
        return vf

    vf = vf.replace("vignette=angle=PI/2.5:mode=forward", "vignette=angle=1.257:mode=forward")

    def fix_unsharp(match: re.Match) -> str:
        parts = match.group(1).split(":")
        if len(parts) >= 2:
            parts[0] = _odd_ffmpeg_kernel(parts[0])
            parts[1] = _odd_ffmpeg_kernel(parts[1])
        if len(parts) >= 5:
            parts[3] = _odd_ffmpeg_kernel(parts[3])
            parts[4] = _odd_ffmpeg_kernel(parts[4])
        return "unsharp=" + ":".join(parts)

    vf = re.sub(r"unsharp=([^,\s]+)", fix_unsharp, vf)

    vf = re.sub(
        r"(color=(?:0x[0-9A-Fa-f]{6}|[A-Za-z]+))@'[^']*(?:sin|cos|max|min|if|\+|\*|/)[^']*'",
        r"\1@0.025",
        vf,
    )

    vf = re.sub(
        r"(color=(?:0x[0-9A-Fa-f]{6}|[A-Za-z]+))@[0-9.]+[^,:]*(?:sin|cos|max|min|if|\+|\*|/)[^,:]*(?=[:,])",
        r"\1@0.025",
        vf,
    )

    return vf


def clean_song_name(audio_path: str, override: str = "") -> str:
    if override:
        return override.strip()
    name = Path(audio_path).stem
    name = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name


def _tail(text: str, limit: int = 1200) -> str:
    """Retorna só o final do log para não poluir o GitHub Actions."""
    if not text:
        return ""
    text = str(text)
    return text[-limit:]


def run_cmd_safe(cmd: list[str], name: str, timeout_s: int, capture: bool = True) -> subprocess.CompletedProcess:
    """
    Executa comando externo com timeout.
    Isso impede o job de ficar infinito quando FFmpeg/runner trava.
    """
    logger.info(f"  ► {name}: timeout={timeout_s}s")
    try:
        return subprocess.run(
            cmd,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"  ✗ {name} travou/estourou timeout após {timeout_s}s.")
        if getattr(e, "stderr", None):
            logger.error(_tail(e.stderr))
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"  ✗ {name} falhou com exit code {e.returncode}.")
        if e.stderr:
            logger.error(_tail(e.stderr))
        raise


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
                f":x=0:y={y}:w=iw:h=18:color={c3}@0.55:t=fill"
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



def build_hypnotic_beat_lights(analysis: dict, style: str = "default") -> str:
    """
    V10 — luzes piscando no beat/kick.
    Feito só com drawbox para ser seguro no GitHub Actions.
    Resultado: sensação de setup/club light pulsando junto com a música.
    """
    if not HYPNOTIC_LIGHTS_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]
    c3 = neon["c3"]

    beats = analysis.get("beats", [])[:HYPNOTIC_MAX_BEATS]
    bass_hits = analysis.get("bass_hits", [])[:HYPNOTIC_MAX_BASS]
    snares = analysis.get("snares", [])[:HYPNOTIC_MAX_SNARES]
    drop_time = analysis.get("drop_time")

    intensity = max(0.25, min(float(HYPNOTIC_LIGHT_INTENSITY), 1.8))
    filters = []

    # Respiração constante bem leve — evita imagem morta/parada.
    filters.append(
        f"drawbox=x=0:y=0:w=iw:h=ih:color={c2}@"
        f"{0.016*intensity:.4f}:t=fill"
    )

    # Luzes laterais respirando, estilo palco/club.
    filters.append(
        f"drawbox=x=0:y=0:w=iw*0.10:h=ih:color={c1}@"
        f"{0.030*intensity:.4f}:t=fill"
    )
    filters.append(
        f"drawbox=x=iw*0.90:y=0:w=iw*0.10:h=ih:color={c2}@"
        f"{0.030*intensity:.4f}:t=fill"
    )

    # Beat geral: flashes curtos e suaves. Dá vida sem poluir.
    for i, bt in enumerate(beats):
        if drop_time is not None and abs(bt - drop_time) < 0.55:
            continue
        t0 = max(0.0, bt - 0.006)
        t1 = bt + 0.045
        color = c2 if i % 2 else c1
        alpha = 0.038 * intensity
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={color}@{alpha:.3f}:t=fill"
        )

    # Bass/kick: pulso mais forte, principalmente embaixo e laterais.
    for i, bt in enumerate(bass_hits):
        t0 = max(0.0, bt - 0.010)
        t1 = bt + 0.085
        alpha = 0.092 * intensity if i < 18 else 0.062 * intensity
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=ih*0.55:w=iw:h=ih*0.45:color={c1}@{alpha:.3f}:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y=0:w=12:h=ih:color={c1}@{min(alpha*1.55,0.32):.3f}:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw-12:y=0:w=12:h=ih:color={c2}@{min(alpha*1.55,0.32):.3f}:t=fill"
        )

    # Snare/hat: linhas rápidas no alto, dá percepção de ritmo.
    for i, st in enumerate(snares):
        if drop_time is not None and abs(st - drop_time) < 0.45:
            continue
        t0 = max(0.0, st - 0.004)
        t1 = st + 0.026
        y = 120 + ((i * 197) % 1520)
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=0:y={y}:w=iw:h=3:color={c3}@{0.085*intensity:.3f}:t=fill"
        )

    # Drop: flash grande + blackout curto + túnel de luz.
    if drop_time is not None:
        t0 = max(0.0, drop_time - 0.020)
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{drop_time+0.030:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=white@{min(0.58*intensity,0.90):.3f}:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{drop_time+0.030:.4f},{drop_time+0.090:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color=black@0.24:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{drop_time+0.090:.4f},{drop_time+0.220:.4f})'"
            f":x=0:y=0:w=iw:h=ih:color={c1}@{0.24*intensity:.3f}:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{drop_time+0.090:.4f},{drop_time+0.280:.4f})'"
            f":x=iw*0.18:y=0:w=iw*0.06:h=ih:color={c2}@{0.30*intensity:.3f}:t=fill"
        )
        filters.append(
            f"drawbox=enable='between(t,{drop_time+0.090:.4f},{drop_time+0.280:.4f})'"
            f":x=iw*0.76:y=0:w=iw*0.06:h=ih:color={c3}@{0.30*intensity:.3f}:t=fill"
        )

    return ",".join(filters)


def build_eye_glow_hypnosis(analysis: dict, style: str = "default") -> str:
    """
    V10 — simula brilho nos olhos/centro do personagem.
    Como FFmpeg não sabe onde estão os olhos, o glow fica na região superior central,
    que é onde seus prompts colocam o rosto na maioria das imagens.
    """
    if not EYE_GLOW_ENABLED:
        return ""

    neon = GENRE_NEON.get(style, GENRE_NEON["default"])
    c1 = neon["c1"]
    c2 = neon["c2"]

    bass_hits = analysis.get("bass_hits", [])[:28]
    drop_time = analysis.get("drop_time")

    filters = []

    # Glow fixo sutil no rosto/olhos.
    filters.append(
        f"drawbox=x=iw*0.36:y=ih*0.215:w=iw*0.28:h=ih*0.080:"
        f"color={c1}@0.027:t=fill"
    )
    filters.append(
        f"drawbox=x=iw*0.42:y=ih*0.245:w=iw*0.16:h=ih*0.018:"
        f"color={c2}@0.070:t=fill"
    )

    # Pulso de olhos no grave.
    for bt in bass_hits:
        t0 = max(0.0, bt - 0.010)
        t1 = bt + 0.065
        filters.append(
            f"drawbox=enable='between(t,{t0:.4f},{t1:.4f})'"
            f":x=iw*0.38:y=ih*0.232:w=iw*0.24:h=ih*0.045:color={c1}@0.105:t=fill"
        )

    if drop_time is not None:
        filters.append(
            f"drawbox=enable='between(t,{max(0.0, drop_time-0.010):.4f},{drop_time+0.160:.4f})'"
            f":x=iw*0.31:y=ih*0.205:w=iw*0.38:h=ih*0.105:color={c2}@0.165:t=fill"
        )

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

    bass_hits = analysis.get("bass_hits", [])[:20]
    drop_time = analysis.get("drop_time")

    borders = []
    borders.append(f"drawbox=x=0:y=0:w=iw:h=80:color=black@0.40:t=fill")
    borders.append(f"drawbox=x=0:y=ih-80:w=iw:h=80:color=black@0.40:t=fill")
    borders.append(f"drawbox=x=0:y=0:w=60:h=ih:color=black@0.35:t=fill")
    borders.append(f"drawbox=x=iw-60:y=0:w=60:h=ih:color=black@0.35:t=fill")

    if borders:
        return base_vig + "," + ",".join(borders)
    return base_vig


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS BASE
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



def build_final_texture() -> str:
    """Textura final v11: brilho premium + grain leve para tirar cara de imagem parada/IA lisa."""
    if FINAL_GRAIN_STRENGTH <= 0:
        return "eq=gamma=1.015:saturation=1.045"
    strength = max(1, min(FINAL_GRAIN_STRENGTH, 8))
    return f"noise=alls={strength}:allf=t+u,eq=gamma=1.015:saturation=1.045"

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
            for b in beats[:40]
        ]
        beat_pulse = f"({'+'.join(parts)})"

    bass_pulse = "0"
    if bass_hits:
        intensity = 0.022 if heavy else 0.013
        parts = [
            f"{intensity}*max(0,1-abs(on-{int(b*fps)})/{max(1,int(0.05*fps))})"
            for b in bass_hits[:35]
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

    hook_frames = max(1, int(1.8 * fps))
    hook_boost = f"(0.055*max(0,1-on/{hook_frames}))"

    full = f"{base}+{drift}+{hook_boost}+{beat_pulse}+{bass_pulse}+{drop_expr}"
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
    fps  = FORCE_FPS or profile["fps"]
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
    hypnotic_lights = build_hypnotic_beat_lights(analysis, style)
    eye_glow = build_eye_glow_hypnosis(analysis, style)

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
    if hypnotic_lights:
        parts.append(hypnotic_lights)
    if eye_glow:
        parts.append(eye_glow)
    if neon_border:
        parts.append(neon_border)
    if drop_flash:
        parts.append(drop_flash)
    if vig:
        parts.append(vig)

    texture = build_final_texture()
    if texture:
        parts.append(texture)

    parts += [fades, f"fps={fps}", pbar]
    return join_filters(parts)


def build_video_filter(
    profile: dict, analysis: dict, duration: float,
    song_name: str, style: str,
) -> str:
    fps  = FORCE_FPS or profile["fps"]
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
    hypnotic_lights = build_hypnotic_beat_lights(analysis, style)
    eye_glow = build_eye_glow_hypnosis(analysis, style)

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
    if hypnotic_lights:
        parts.append(hypnotic_lights)
    if eye_glow:
        parts.append(eye_glow)
    if neon_border:
        parts.append(neon_border)
    if drop_flash:
        parts.append(drop_flash)
    if vig:
        parts.append(vig)

    texture = build_final_texture()
    if texture:
        parts.append(texture)

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
    vf_or_complex = sanitize_ffmpeg_filter(vf_or_complex)
    cmd = ["ffmpeg", "-y", "-nostdin"] + inputs + ["-t", str(dur)]

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
    vf = sanitize_ffmpeg_filter(vf)
    cmd = [
        "ffmpeg", "-y", "-nostdin", "-ss", str(timestamp),
        "-i", video_path, "-vframes", "1",
        "-vf", vf, "-q:v", "2", out,
    ]
    try:
        run_cmd_safe(cmd, "Thumbnail FFmpeg", FFMPEG_THUMB_TIMEOUT_S, capture=True)
        logger.info(f"  ► Thumbnail gerada: {out}")
        return out
    except subprocess.TimeoutExpired:
        logger.warning("  ⚠ Thumbnail travou/timeout — seguindo sem thumbnail.")
        return None
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="ignore") if e.stderr else "")
        logger.warning(f"  ⚠ Thumbnail falhou: {_tail(stderr, 300)}")
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
        hypnotic_lights = build_hypnotic_beat_lights(analysis, style)
        eye_glow = build_eye_glow_hypnosis(analysis, style)
        base_vf  = join_filters([genre_g, scanlines, hypnotic_lights, eye_glow, neon_border, drop_flash, fade, pbar])
        inputs = [
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur}",
            "-ss", str(start), "-i", audio_path,
        ]
        cmd = _build_cmd(inputs, base_vf, False, False, audio_filter, dur, output_name,
                         audio_input_idx=1)

    # ── Render ────────────────────────────────────────────────────────────
    logger.info("  ► Iniciando render v11 FINAL VIBRANT HYPNOTIC…")
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            run_cmd_safe(cmd, "Render FFmpeg v11 FINAL VIBRANT HYPNOTIC", FFMPEG_RENDER_TIMEOUT_S, capture=True)
            logger.info("  ► Render concluído ✓")
            break
        except subprocess.TimeoutExpired:
            err = f"Timeout de {FFMPEG_RENDER_TIMEOUT_S}s no FFmpeg base."
            if attempt <= MAX_RETRIES:
                logger.warning(f"  ⚠ Render travou (tentativa {attempt}): {err}")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"  ✗ Render travou após {MAX_RETRIES+1} tentativas. {err}")
                raise
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="ignore") if e.stderr else "")
            err = _tail(stderr, 600)
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
    parser = argparse.ArgumentParser(description="Elite Music Shorts Generator v11 — Final Vibrant Hypnotic")
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
