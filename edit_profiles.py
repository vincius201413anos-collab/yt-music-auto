"""
edit_profiles.py — Perfis de edição calibrados para o canal DjDarkMark.

Foco:
- phonk / trap / dark underground
- contraste mais forte
- menos visual lavado
- movimento e impacto coerentes com música pesada
- perfis suaves ainda existem, mas default puxa para o lado dark/trap
"""

from __future__ import annotations
from copy import deepcopy
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# BASE DEFAULT
# ══════════════════════════════════════════════════════════════════════════════

_DEFAULT: dict = {
    # Motion
    "zoom_speed":      0.028,
    "max_zoom":        1.18,
    "pulse_strength":  0.004,
    "shake_x":         4,
    "shake_y":         4,

    # Color grading
    "brightness":      -0.01,
    "contrast":        1.24,
    "saturation":      1.12,
    "sharpen":         1.24,
    "blur":            0.0,

    # Beat reactions
    "beat_flash":      0.09,
    "bass_flash":      0.15,
    "drop_flash":      0.24,

    # Post-processing
    "vignette":        0.42,
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
        "zoom_speed":     0.030,
        "max_zoom":       1.19,
        "pulse_strength": 0.0045,
        "brightness":     -0.005,
        "contrast":       1.28,
        "saturation":     1.16,
        "sharpen":        1.30,
        "shake_x":        5,
        "shake_y":        4,
        "beat_flash":     0.10,
        "bass_flash":     0.16,
        "drop_flash":     0.25,
        "vignette":       0.38,
    },

    # ── PHONK ─────────────────────────────────────────────────────────────────
    "phonk": {
        "zoom_speed":     0.036,
        "max_zoom":       1.22,
        "pulse_strength": 0.0055,
        "brightness":     -0.02,
        "contrast":       1.34,
        "saturation":     1.08,
        "sharpen":        1.44,
        "shake_x":        7,
        "shake_y":        6,
        "beat_flash":     0.11,
        "bass_flash":     0.18,
        "drop_flash":     0.30,
        "vignette":       0.52,
    },

    # ── DARK ──────────────────────────────────────────────────────────────────
    "dark": {
        "zoom_speed":     0.022,
        "max_zoom":       1.14,
        "pulse_strength": 0.003,
        "brightness":     -0.03,
        "contrast":       1.32,
        "saturation":     0.90,
        "sharpen":        1.20,
        "shake_x":        3,
        "shake_y":        3,
        "beat_flash":     0.07,
        "bass_flash":     0.12,
        "drop_flash":     0.20,
        "vignette":       0.62,
    },

    # ── ELECTRONIC ────────────────────────────────────────────────────────────
    "electronic": {
        "zoom_speed":     0.032,
        "max_zoom":       1.20,
        "pulse_strength": 0.005,
        "brightness":     0.00,
        "contrast":       1.26,
        "saturation":     1.24,
        "sharpen":        1.28,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.11,
        "bass_flash":     0.17,
        "drop_flash":     0.27,
        "vignette":       0.26,
    },

    # ── ROCK ──────────────────────────────────────────────────────────────────
    "rock": {
        "zoom_speed":     0.032,
        "max_zoom":       1.20,
        "pulse_strength": 0.0045,
        "brightness":     -0.005,
        "contrast":       1.28,
        "saturation":     1.10,
        "sharpen":        1.36,
        "shake_x":        6,
        "shake_y":        5,
        "beat_flash":     0.10,
        "bass_flash":     0.16,
        "drop_flash":     0.26,
        "vignette":       0.42,
    },

    # ── METAL ─────────────────────────────────────────────────────────────────
    "metal": {
        "zoom_speed":     0.040,
        "max_zoom":       1.24,
        "pulse_strength": 0.006,
        "brightness":     -0.03,
        "contrast":       1.38,
        "saturation":     0.96,
        "sharpen":        1.52,
        "shake_x":        8,
        "shake_y":        7,
        "beat_flash":     0.12,
        "bass_flash":     0.18,
        "drop_flash":     0.30,
        "vignette":       0.58,
    },

    # ── CINEMATIC ─────────────────────────────────────────────────────────────
    "cinematic": {
        "zoom_speed":     0.015,
        "max_zoom":       1.10,
        "pulse_strength": 0.002,
        "brightness":     -0.005,
        "contrast":       1.18,
        "saturation":     1.00,
        "sharpen":        1.08,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.05,
        "bass_flash":     0.08,
        "drop_flash":     0.14,
        "vignette":       0.52,
    },

    # ── LOFI ──────────────────────────────────────────────────────────────────
    "lofi": {
        "zoom_speed":     0.008,
        "max_zoom":       1.05,
        "pulse_strength": 0.001,
        "brightness":     0.01,
        "contrast":       1.04,
        "saturation":     0.86,
        "sharpen":        0.76,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.02,
        "bass_flash":     0.04,
        "drop_flash":     0.07,
        "vignette":       0.28,
    },

    # ── INDIE ─────────────────────────────────────────────────────────────────
    "indie": {
        "zoom_speed":     0.012,
        "max_zoom":       1.08,
        "pulse_strength": 0.002,
        "brightness":     0.00,
        "contrast":       1.08,
        "saturation":     1.00,
        "sharpen":        0.96,
        "shake_x":        1,
        "shake_y":        1,
        "beat_flash":     0.04,
        "bass_flash":     0.07,
        "drop_flash":     0.11,
        "vignette":       0.34,
    },

    # ── POP ───────────────────────────────────────────────────────────────────
    "pop": {
        "zoom_speed":     0.020,
        "max_zoom":       1.13,
        "pulse_strength": 0.003,
        "brightness":     0.01,
        "contrast":       1.12,
        "saturation":     1.22,
        "sharpen":        1.14,
        "shake_x":        2,
        "shake_y":        2,
        "beat_flash":     0.07,
        "bass_flash":     0.11,
        "drop_flash":     0.17,
        "vignette":       0.18,
    },

    # ── FUNK ──────────────────────────────────────────────────────────────────
    "funk": {
        "zoom_speed":     0.030,
        "max_zoom":       1.18,
        "pulse_strength": 0.0048,
        "brightness":     0.00,
        "contrast":       1.22,
        "saturation":     1.24,
        "sharpen":        1.20,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.09,
        "bass_flash":     0.15,
        "drop_flash":     0.23,
        "vignette":       0.24,
    },

    # ── ANIME ─────────────────────────────────────────────────────────────────
    "anime": {
        "zoom_speed":     0.030,
        "max_zoom":       1.18,
        "pulse_strength": 0.005,
        "brightness":     0.00,
        "contrast":       1.24,
        "saturation":     1.30,
        "sharpen":        1.42,
        "shake_x":        4,
        "shake_y":        4,
        "beat_flash":     0.11,
        "bass_flash":     0.17,
        "drop_flash":     0.26,
        "vignette":       0.20,
    },

    # ── GAMING ────────────────────────────────────────────────────────────────
    "gaming": {
        "zoom_speed":     0.038,
        "max_zoom":       1.24,
        "pulse_strength": 0.0065,
        "brightness":     0.00,
        "contrast":       1.30,
        "saturation":     1.30,
        "sharpen":        1.52,
        "shake_x":        7,
        "shake_y":        6,
        "beat_flash":     0.12,
        "bass_flash":     0.19,
        "drop_flash":     0.30,
        "vignette":       0.24,
    },

    # ── HORROR ────────────────────────────────────────────────────────────────
    "horror": {
        "zoom_speed":     0.016,
        "max_zoom":       1.14,
        "pulse_strength": 0.003,
        "brightness":     -0.04,
        "contrast":       1.36,
        "saturation":     0.68,
        "sharpen":        1.22,
        "shake_x":        3,
        "shake_y":        3,
        "beat_flash":     0.05,
        "bass_flash":     0.10,
        "drop_flash":     0.22,
        "vignette":       0.72,
    },

    # ── HYPERPOP ──────────────────────────────────────────────────────────────
    "hyperpop": {
        "zoom_speed":     0.045,
        "max_zoom":       1.26,
        "pulse_strength": 0.008,
        "brightness":     0.01,
        "contrast":       1.22,
        "saturation":     1.46,
        "sharpen":        1.34,
        "shake_x":        8,
        "shake_y":        8,
        "beat_flash":     0.14,
        "bass_flash":     0.22,
        "drop_flash":     0.34,
        "vignette":       0.12,
    },

    # ── RNB ───────────────────────────────────────────────────────────────────
    "rnb": {
        "zoom_speed":     0.015,
        "max_zoom":       1.09,
        "pulse_strength": 0.002,
        "brightness":     0.005,
        "contrast":       1.12,
        "saturation":     1.14,
        "sharpen":        1.02,
        "shake_x":        1,
        "shake_y":        1,
        "beat_flash":     0.05,
        "bass_flash":     0.09,
        "drop_flash":     0.14,
        "vignette":       0.28,
    },

    # ── CHILL ─────────────────────────────────────────────────────────────────
    "chill": {
        "zoom_speed":     0.008,
        "max_zoom":       1.05,
        "pulse_strength": 0.001,
        "brightness":     0.01,
        "contrast":       1.06,
        "saturation":     1.04,
        "sharpen":        0.84,
        "shake_x":        0,
        "shake_y":        0,
        "beat_flash":     0.03,
        "bass_flash":     0.05,
        "drop_flash":     0.08,
        "vignette":       0.20,
    },
}

# Aliases
_PROFILES["default"] = deepcopy(_DEFAULT)
_PROFILES["edm"] = deepcopy(_PROFILES["electronic"])
_PROFILES["hiphop"] = deepcopy(_PROFILES["trap"])
_PROFILES["drill"] = deepcopy(_PROFILES["trap"])


def get_profile(style: str) -> dict:
    raw = _PROFILES.get(style.lower().strip(), _PROFILES["default"])
    return {**_DEFAULT, **raw}


def list_profiles() -> list[str]:
    return sorted(_PROFILES.keys())


def blend_profiles(style_a: str, style_b: str, weight: float = 0.5) -> dict:
    weight = max(0.0, min(1.0, weight))
    pa = get_profile(style_a)
    pb = get_profile(style_b)

    blended = {}
    for key in pa:
        va = pa[key]
        vb = pb[key]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            blended[key] = va * (1 - weight) + vb * weight
        else:
            blended[key] = va if weight < 0.5 else vb

    # normalizações úteis
    blended["max_zoom"] = min(max(blended["max_zoom"], 1.04), 1.28)
    blended["zoom_speed"] = min(max(blended["zoom_speed"], 0.006), 0.05)
    blended["beat_flash"] = min(max(blended["beat_flash"], 0.02), 0.18)
    blended["bass_flash"] = min(max(blended["bass_flash"], 0.04), 0.26)
    blended["drop_flash"] = min(max(blended["drop_flash"], 0.08), 0.36)
    blended["shake_x"] = int(min(max(round(blended["shake_x"]), 0), 8))
    blended["shake_y"] = int(min(max(round(blended["shake_y"]), 0), 8))
    blended["fps"] = 30
    return blended


def get_profile_for_bpm(bpm: Optional[float], style_hint: str = "default") -> dict:
    """
    Ajuste dinâmico por BPM com foco em música dark/trap/phonk.
    """
    profile = get_profile(style_hint)
    if bpm is None:
        return profile

    p = deepcopy(profile)

    if bpm < 80:
        p["zoom_speed"] *= 0.75
        p["shake_x"] = max(0, p["shake_x"] - 2)
        p["shake_y"] = max(0, p["shake_y"] - 2)
        p["beat_flash"] *= 0.85
        p["bass_flash"] *= 0.90

    elif bpm > 155:
        p["zoom_speed"] = min(p["zoom_speed"] * 1.20, 0.050)
        p["max_zoom"] = min(p["max_zoom"] + 0.03, 1.28)
        p["shake_x"] = min(p["shake_x"] + 1, 8)
        p["shake_y"] = min(p["shake_y"] + 1, 8)
        p["beat_flash"] = min(p["beat_flash"] * 1.15, 0.18)
        p["bass_flash"] = min(p["bass_flash"] * 1.15, 0.26)
        p["drop_flash"] = min(p["drop_flash"] * 1.10, 0.36)

    elif bpm > 125:
        p["zoom_speed"] = min(p["zoom_speed"] * 1.10, 0.045)
        p["beat_flash"] = min(p["beat_flash"] * 1.08, 0.16)
        p["bass_flash"] = min(p["bass_flash"] * 1.08, 0.24)

    return p


if __name__ == "__main__":
    import json
    print("Perfis disponíveis:", list_profiles())
    print("\nPerfil phonk:")
    print(json.dumps(get_profile("phonk"), indent=2))
    print("\nBlend trap+dark (0.35):")
    print(json.dumps(blend_profiles("trap", "dark", 0.35), indent=2))
    print("\nPerfil phonk @ 160 BPM:")
    print(json.dumps(get_profile_for_bpm(160, "phonk"), indent=2))
