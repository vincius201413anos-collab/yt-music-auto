"""
edit_profiles.py — Perfis de edição calibrados para Shorts de música.

v2 upgrades:
- Perfis novos: gaming, horror, hyperpop, rnb, chill
- Suporte a herança: perfis derivam de "default" automaticamente
- blend_profiles(): mistura dois perfis com peso
- get_profile_for_bpm(): escolhe perfil dinâmico baseado no BPM detectado
- Todos os valores comentados para fácil calibração
"""

from __future__ import annotations
from copy import deepcopy
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# BASE DEFAULT (herança automática para todos os perfis)
# ══════════════════════════════════════════════════════════════════════════════

_DEFAULT: dict = {
    # Motion
    "zoom_speed":      0.022,   # velocidade do zoom (0=estático, 0.05=rápido)
    "max_zoom":        1.16,    # zoom máximo (1.0=sem zoom, 1.3=muito próximo)
    "pulse_strength":  0.003,   # intensidade do pulso no zoom
    "shake_x":         3,       # shake horizontal (px)
    "shake_y":         3,       # shake vertical (px)

    # Color grading
    "brightness":      0.00,    # brilho base (-0.05=escuro, +0.05=claro)
    "contrast":        1.18,    # contraste (1.0=neutro, 1.4=alto)
    "saturation":      1.18,    # saturação (0.0=P&B, 1.5=vibrante)
    "sharpen":         1.18,    # nitidez (0=suave, 2.0=muito nítido)
    "blur":            0.0,

    # Beat reactions
    "beat_flash":      0.08,    # brilho no beat
    "bass_flash":      0.14,    # brilho no bass hit
    "drop_flash":      0.22,    # brilho no drop

    # Post-processing
    "vignette":        0.30,    # vinheta (0=sem, 1.0=forte)
    "hue_shift":       0,

    # Output
    "fps":             30,
}

# ══════════════════════════════════════════════════════════════════════════════
# PROFILES
# ══════════════════════════════════════════════════════════════════════════════

_PROFILES: dict[str, dict] = {

    # ── TRAP ──────────────────────────────────────────────────────────────────
    "trap": {
        "zoom_speed":     0.028,
        "max_zoom":       1.17,
        "pulse_strength": 0.004,
        "brightness":     0.00,
        "contrast":       1.24,
        "saturation":     1.22,
        "sharpen":        1.30,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.10,
        "bass_flash":     0.16,
        "drop_flash":     0.24,
        "vignette":       0.36,
    },

    # ── PHONK ─────────────────────────────────────────────────────────────────
    "phonk": {
        "zoom_speed":     0.034,
        "max_zoom":       1.20,
        "pulse_strength": 0.005,
        "brightness":     -0.01,
        "contrast":       1.30,
        "saturation":     1.18,
        "sharpen":        1.45,
        "shake_x":        6,
        "shake_y":        5,
        "beat_flash":     0.12,
        "bass_flash":     0.18,
        "drop_flash":     0.28,
        "vignette":       0.48,
    },

    # ── ROCK ──────────────────────────────────────────────────────────────────
    "rock": {
        "zoom_speed":     0.034,
        "max_zoom":       1.22,
        "pulse_strength": 0.005,
        "brightness":     0.00,
        "contrast":       1.28,
        "saturation":     1.16,
        "sharpen":        1.42,
        "shake_x":        6,
        "shake_y":        5,
        "beat_flash":     0.12,
        "bass_flash":     0.18,
        "drop_flash":     0.28,
        "vignette":       0.48,
    },

    # ── METAL ─────────────────────────────────────────────────────────────────
    "metal": {
        "zoom_speed":     0.040,
        "max_zoom":       1.24,
        "pulse_strength": 0.006,
        "brightness":     -0.02,
        "contrast":       1.34,
        "saturation":     1.00,
        "sharpen":        1.55,
        "shake_x":        8,
        "shake_y":        7,
        "beat_flash":     0.14,
        "bass_flash":     0.20,
        "drop_flash":     0.30,
        "vignette":       0.58,
    },

    # ── ELECTRONIC ────────────────────────────────────────────────────────────
    "electronic": {
        "zoom_speed":     0.030,
        "max_zoom":       1.20,
        "pulse_strength": 0.005,
        "brightness":     0.01,
        "contrast":       1.24,
        "saturation":     1.34,
        "sharpen":        1.30,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.12,
        "bass_flash":     0.18,
        "drop_flash":     0.28,
        "vignette":       0.24,
    },

    # ── CINEMATIC ─────────────────────────────────────────────────────────────
    "cinematic": {
        "zoom_speed":     0.014,
        "max_zoom":       1.10,
        "pulse_strength": 0.002,
        "brightness":     0.01,
        "contrast":       1.16,
        "saturation":     1.02,
        "sharpen":        1.10,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.06,
        "bass_flash":     0.10,
        "drop_flash":     0.16,
        "vignette":       0.55,
    },

    # ── LOFI ──────────────────────────────────────────────────────────────────
    "lofi": {
        "zoom_speed":     0.007,
        "max_zoom":       1.05,
        "pulse_strength": 0.001,
        "brightness":     0.02,
        "contrast":       1.06,
        "saturation":     0.88,
        "sharpen":        0.78,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.03,
        "bass_flash":     0.05,
        "drop_flash":     0.08,
        "vignette":       0.32,
    },

    # ── INDIE ─────────────────────────────────────────────────────────────────
    "indie": {
        "zoom_speed":     0.012,
        "max_zoom":       1.08,
        "pulse_strength": 0.002,
        "brightness":     0.01,
        "contrast":       1.10,
        "saturation":     1.04,
        "sharpen":        0.98,
        "shake_x":        1,
        "shake_y":        1,
        "beat_flash":     0.05,
        "bass_flash":     0.08,
        "drop_flash":     0.12,
        "vignette":       0.34,
    },

    # ── POP ───────────────────────────────────────────────────────────────────
    "pop": {
        "zoom_speed":     0.022,
        "max_zoom":       1.14,
        "pulse_strength": 0.003,
        "brightness":     0.02,
        "contrast":       1.14,
        "saturation":     1.28,
        "sharpen":        1.18,
        "shake_x":        2,
        "shake_y":        2,
        "beat_flash":     0.08,
        "bass_flash":     0.12,
        "drop_flash":     0.18,
        "vignette":       0.18,
    },

    # ── FUNK ──────────────────────────────────────────────────────────────────
    "funk": {
        "zoom_speed":     0.030,
        "max_zoom":       1.18,
        "pulse_strength": 0.005,
        "brightness":     0.01,
        "contrast":       1.24,
        "saturation":     1.30,
        "sharpen":        1.24,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.10,
        "bass_flash":     0.16,
        "drop_flash":     0.24,
        "vignette":       0.26,
    },

    # ── DARK ──────────────────────────────────────────────────────────────────
    "dark": {
        "zoom_speed":     0.018,
        "max_zoom":       1.12,
        "pulse_strength": 0.002,
        "brightness":     -0.02,
        "contrast":       1.28,
        "saturation":     0.92,
        "sharpen":        1.20,
        "shake_x":        2,
        "shake_y":        2,
        "beat_flash":     0.08,
        "bass_flash":     0.14,
        "drop_flash":     0.22,
        "vignette":       0.62,
    },

    # ── ANIME ─────────────────────────────────────────────────────────────────
    # Alta saturação, zoom rápido, flashes intensos no beat — estilo AMV
    "anime": {
        "zoom_speed":     0.032,
        "max_zoom":       1.22,
        "pulse_strength": 0.006,
        "brightness":     0.01,
        "contrast":       1.26,
        "saturation":     1.44,
        "sharpen":        1.50,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.13,
        "bass_flash":     0.20,
        "drop_flash":     0.30,
        "vignette":       0.20,
    },

    # ── GAMING ────────────────────────────────────────────────────────────────
    # Estilo stream/montage: cores neon, movimento agressivo, alto contraste
    "gaming": {
        "zoom_speed":     0.038,
        "max_zoom":       1.26,
        "pulse_strength": 0.007,
        "brightness":     0.01,
        "contrast":       1.32,
        "saturation":     1.40,
        "sharpen":        1.60,
        "shake_x":        7,
        "shake_y":        6,
        "beat_flash":     0.14,
        "bass_flash":     0.22,
        "drop_flash":     0.32,
        "vignette":       0.28,
    },

    # ── HORROR ────────────────────────────────────────────────────────────────
    # Dessaturado, escuro, vinheta forte, shake suave e perturbador
    "horror": {
        "zoom_speed":     0.016,
        "max_zoom":       1.14,
        "pulse_strength": 0.003,
        "brightness":     -0.04,
        "contrast":       1.36,
        "saturation":     0.70,
        "sharpen":        1.25,
        "shake_x":        3,
        "shake_y":        3,
        "beat_flash":     0.06,
        "bass_flash":     0.12,
        "drop_flash":     0.26,
        "vignette":       0.72,
    },

    # ── HYPERPOP ──────────────────────────────────────────────────────────────
    # Super saturado, flashes extremos, movimento caótico
    "hyperpop": {
        "zoom_speed":     0.045,
        "max_zoom":       1.28,
        "pulse_strength": 0.009,
        "brightness":     0.02,
        "contrast":       1.22,
        "saturation":     1.55,
        "sharpen":        1.40,
        "shake_x":        8,
        "shake_y":        8,
        "beat_flash":     0.16,
        "bass_flash":     0.24,
        "drop_flash":     0.36,
        "vignette":       0.14,
    },

    # ── R&B ───────────────────────────────────────────────────────────────────
    # Suave, quente, movimento lento, cores ricas
    "rnb": {
        "zoom_speed":     0.016,
        "max_zoom":       1.10,
        "pulse_strength": 0.002,
        "brightness":     0.01,
        "contrast":       1.14,
        "saturation":     1.20,
        "sharpen":        1.05,
        "shake_x":        1,
        "shake_y":        1,
        "beat_flash":     0.06,
        "bass_flash":     0.10,
        "drop_flash":     0.16,
        "vignette":       0.30,
    },

    # ── CHILL ─────────────────────────────────────────────────────────────────
    # Relaxado, cores pastel, movimento quase imperceptível
    "chill": {
        "zoom_speed":     0.008,
        "max_zoom":       1.06,
        "pulse_strength": 0.001,
        "brightness":     0.02,
        "contrast":       1.08,
        "saturation":     1.10,
        "sharpen":        0.85,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.04,
        "bass_flash":     0.06,
        "drop_flash":     0.10,
        "vignette":       0.22,
    },
}

# Aliases
_PROFILES["default"] = deepcopy(_DEFAULT)
_PROFILES["edm"]     = deepcopy(_PROFILES["electronic"])
_PROFILES["hiphop"]  = deepcopy(_PROFILES["trap"])
_PROFILES["drill"]   = deepcopy(_PROFILES["trap"])


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_profile(style: str) -> dict:
    """Retorna perfil completo (herança de _DEFAULT garantida)."""
    raw = _PROFILES.get(style.lower().strip(), _PROFILES["default"])
    return {**_DEFAULT, **raw}


def list_profiles() -> list[str]:
    """Lista todos os perfis disponíveis."""
    return sorted(_PROFILES.keys())


def blend_profiles(style_a: str, style_b: str, weight: float = 0.5) -> dict:
    """
    Mistura dois perfis.
    weight=0.0 → 100% style_a | weight=1.0 → 100% style_b
    """
    weight = max(0.0, min(1.0, weight))
    pa = get_profile(style_a)
    pb = get_profile(style_b)

    blended = {}
    for key in pa:
        va = pa[key]
        vb = pb[key]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            blended[key] = type(va)(va * (1 - weight) + vb * weight)
        else:
            blended[key] = va if weight < 0.5 else vb

    return blended


def get_profile_for_bpm(bpm: Optional[float], style_hint: str = "default") -> dict:
    """
    Ajusta dinamicamente o perfil com base no BPM detectado.
    - BPM < 80  → chill/lofi adjustments
    - BPM 80-120 → perfil base
    - BPM > 120 → +energia (zoom, shake, flash)
    - BPM > 150 → hyperpop/metal territory
    """
    profile = get_profile(style_hint)

    if bpm is None:
        return profile

    p = deepcopy(profile)

    if bpm < 80:
        p["zoom_speed"]    *= 0.7
        p["shake_x"]       = max(0, p["shake_x"] - 2)
        p["shake_y"]       = max(0, p["shake_y"] - 2)
        p["beat_flash"]    *= 0.8

    elif bpm > 150:
        p["zoom_speed"]    = min(p["zoom_speed"] * 1.35, 0.050)
        p["shake_x"]       = min(p["shake_x"] + 2, 8)
        p["shake_y"]       = min(p["shake_y"] + 2, 8)
        p["beat_flash"]    = min(p["beat_flash"] * 1.2, 0.20)
        p["bass_flash"]    = min(p["bass_flash"] * 1.2, 0.28)

    elif bpm > 120:
        p["zoom_speed"]    = min(p["zoom_speed"] * 1.15, 0.045)
        p["beat_flash"]    = min(p["beat_flash"] * 1.1, 0.18)

    return p


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Perfis disponíveis:", list_profiles())
    print("\nPerfil trap:")
    import json
    print(json.dumps(get_profile("trap"), indent=2))
    print("\nBlend trap+anime (0.4):")
    print(json.dumps(blend_profiles("trap", "anime", 0.4), indent=2))
    print("\nPerfil trap @ 160 BPM:")
    print(json.dumps(get_profile_for_bpm(160, "trap"), indent=2))
