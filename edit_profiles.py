"""
edit_profiles.py — Perfis de edição profissionais por estilo musical.
Cada perfil é calibrado para maximizar retenção em Shorts.
"""

# Todos os perfis seguem a mesma estrutura.
# Parâmetros de zoom/shake são limites — o código os modula dinamicamente.

EDIT_PROFILES = {

    # ── PHONK ──────────────────────────────────────────────────────────────
    "phonk": {
        # zoom
        "zoom_speed":    0.030,   # velocidade do ciclo de zoom (seno)
        "max_zoom":      1.20,    # limite máximo de zoom
        "pulse_strength":0.005,   # pulso de respiração

        # cor
        "brightness":   -0.04,
        "contrast":      1.32,
        "saturation":    1.30,
        "sharpen":       1.55,
        "blur":          0.0,

        # shake
        "shake_x":       5,
        "shake_y":       5,

        # flash
        "beat_flash":    0.20,
        "bass_flash":    0.28,
        "drop_flash":    0.42,

        # color grading extra (hue shift, vignette)
        "vignette":      0.55,
        "hue_shift":     4,       # graus de hue shift no drop

        "fps": 30,
    },

    # ── TRAP ───────────────────────────────────────────────────────────────
    "trap": {
        "zoom_speed":    0.026,
        "max_zoom":      1.18,
        "pulse_strength":0.004,

        "brightness":   -0.02,
        "contrast":      1.26,
        "saturation":    1.22,
        "sharpen":       1.38,
        "blur":          0.0,

        "shake_x":       4,
        "shake_y":       4,

        "beat_flash":    0.17,
        "bass_flash":    0.24,
        "drop_flash":    0.38,

        "vignette":      0.45,
        "hue_shift":     3,

        "fps": 30,
    },

    # ── ROCK ───────────────────────────────────────────────────────────────
    "rock": {
        "zoom_speed":    0.032,
        "max_zoom":      1.22,
        "pulse_strength":0.005,

        "brightness":   -0.04,
        "contrast":      1.28,
        "saturation":    1.14,
        "sharpen":       1.50,
        "blur":          0.0,

        "shake_x":       6,
        "shake_y":       6,

        "beat_flash":    0.20,
        "bass_flash":    0.28,
        "drop_flash":    0.44,

        "vignette":      0.60,
        "hue_shift":     5,

        "fps": 30,
    },

    # ── METAL ──────────────────────────────────────────────────────────────
    "metal": {
        "zoom_speed":    0.038,
        "max_zoom":      1.24,
        "pulse_strength":0.006,

        "brightness":   -0.06,
        "contrast":      1.36,
        "saturation":    1.08,
        "sharpen":       1.65,
        "blur":          0.0,

        "shake_x":       7,
        "shake_y":       7,

        "beat_flash":    0.22,
        "bass_flash":    0.32,
        "drop_flash":    0.50,

        "vignette":      0.70,
        "hue_shift":     6,

        "fps": 30,
    },

    # ── ELECTRONIC ─────────────────────────────────────────────────────────
    "electronic": {
        "zoom_speed":    0.028,
        "max_zoom":      1.20,
        "pulse_strength":0.004,

        "brightness":    0.00,
        "contrast":      1.28,
        "saturation":    1.28,
        "sharpen":       1.38,
        "blur":          0.0,

        "shake_x":       4,
        "shake_y":       4,

        "beat_flash":    0.18,
        "bass_flash":    0.26,
        "drop_flash":    0.42,

        "vignette":      0.40,
        "hue_shift":     8,

        "fps": 30,
    },

    # ── CINEMATIC ──────────────────────────────────────────────────────────
    "cinematic": {
        "zoom_speed":    0.014,
        "max_zoom":      1.10,
        "pulse_strength":0.002,

        "brightness":   -0.01,
        "contrast":      1.16,
        "saturation":    1.04,
        "sharpen":       1.12,
        "blur":          0.0,

        "shake_x":       1,
        "shake_y":       1,

        "beat_flash":    0.08,
        "bass_flash":    0.14,
        "drop_flash":    0.22,

        "vignette":      0.65,
        "hue_shift":     0,

        "fps": 30,
    },

    # ── LOFI ───────────────────────────────────────────────────────────────
    "lofi": {
        "zoom_speed":    0.008,
        "max_zoom":      1.06,
        "pulse_strength":0.001,

        "brightness":    0.02,
        "contrast":      1.06,
        "saturation":    0.88,
        "sharpen":       0.80,
        "blur":          0.0,

        "shake_x":       0,
        "shake_y":       0,

        "beat_flash":    0.04,
        "bass_flash":    0.07,
        "drop_flash":    0.10,

        "vignette":      0.40,
        "hue_shift":     0,

        "fps": 30,
    },

    # ── INDIE ──────────────────────────────────────────────────────────────
    "indie": {
        "zoom_speed":    0.012,
        "max_zoom":      1.09,
        "pulse_strength":0.002,

        "brightness":    0.00,
        "contrast":      1.10,
        "saturation":    0.96,
        "sharpen":       0.95,
        "blur":          0.0,

        "shake_x":       1,
        "shake_y":       1,

        "beat_flash":    0.06,
        "bass_flash":    0.10,
        "drop_flash":    0.15,

        "vignette":      0.45,
        "hue_shift":     0,

        "fps": 30,
    },

    # ── POP ────────────────────────────────────────────────────────────────
    "pop": {
        "zoom_speed":    0.020,
        "max_zoom":      1.15,
        "pulse_strength":0.003,

        "brightness":    0.02,
        "contrast":      1.14,
        "saturation":    1.20,
        "sharpen":       1.12,
        "blur":          0.0,

        "shake_x":       2,
        "shake_y":       2,

        "beat_flash":    0.12,
        "bass_flash":    0.18,
        "drop_flash":    0.28,

        "vignette":      0.30,
        "hue_shift":     2,

        "fps": 30,
    },

    # ── FUNK ───────────────────────────────────────────────────────────────
    "funk": {
        "zoom_speed":    0.030,
        "max_zoom":      1.20,
        "pulse_strength":0.004,

        "brightness":    0.00,
        "contrast":      1.28,
        "saturation":    1.32,
        "sharpen":       1.32,
        "blur":          0.0,

        "shake_x":       5,
        "shake_y":       5,

        "beat_flash":    0.20,
        "bass_flash":    0.28,
        "drop_flash":    0.42,

        "vignette":      0.40,
        "hue_shift":     3,

        "fps": 30,
    },

    # ── DARK ───────────────────────────────────────────────────────────────
    "dark": {
        "zoom_speed":    0.022,
        "max_zoom":      1.15,
        "pulse_strength":0.003,

        "brightness":   -0.07,
        "contrast":      1.30,
        "saturation":    0.92,
        "sharpen":       1.20,
        "blur":          0.0,

        "shake_x":       3,
        "shake_y":       3,

        "beat_flash":    0.14,
        "bass_flash":    0.20,
        "drop_flash":    0.30,

        "vignette":      0.75,
        "hue_shift":     0,

        "fps": 30,
    },

    # ── DEFAULT ────────────────────────────────────────────────────────────
    "default": {
        "zoom_speed":    0.022,
        "max_zoom":      1.16,
        "pulse_strength":0.003,

        "brightness":    0.00,
        "contrast":      1.18,
        "saturation":    1.12,
        "sharpen":       1.18,
        "blur":          0.0,

        "shake_x":       3,
        "shake_y":       3,

        "beat_flash":    0.14,
        "bass_flash":    0.20,
        "drop_flash":    0.32,

        "vignette":      0.40,
        "hue_shift":     0,

        "fps": 30,
    },
}


def get_profile(style: str) -> dict:
    """Retorna perfil com fallback para default."""
    default = EDIT_PROFILES["default"]
    raw     = EDIT_PROFILES.get(style, default)
    return {**default, **raw}
