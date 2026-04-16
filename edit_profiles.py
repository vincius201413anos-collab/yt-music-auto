"""
edit_profiles.py — Perfis de edição profissionais por estilo musical.
Cores mais vivas e contraste otimizado para retenção em Shorts.
Calibrado para o algoritmo de música no YouTube 2025.
"""

# NOTA SOBRE BRIGHTNESS:
# O valor base de brightness aqui é usado como BASE no flash_expression.
# O flash dinâmico (beat/bass/drop) vai flutuar acima desse valor.
# Valores positivos = mais brilhante, negativos = mais escuro.
# Para canais de música: manter >= -0.02 para evitar imagens escuras.

EDIT_PROFILES = {

    # ── PHONK ──────────────────────────────────────────────────────────────
    "phonk": {
        "zoom_speed":     0.034,
        "max_zoom":       1.22,
        "pulse_strength": 0.006,

        "brightness":     0.01,    # ligeiramente brilhante (evita escuro)
        "contrast":       1.35,
        "saturation":     1.45,    # mais vibrante
        "sharpen":        1.60,
        "blur":           0.0,

        "shake_x":        6,
        "shake_y":        5,

        "beat_flash":     0.22,
        "bass_flash":     0.30,
        "drop_flash":     0.45,

        "vignette":       0.50,
        "hue_shift":      5,

        "fps": 30,
    },

    # ── TRAP ───────────────────────────────────────────────────────────────
    "trap": {
        "zoom_speed":     0.028,
        "max_zoom":       1.19,
        "pulse_strength": 0.004,

        "brightness":     0.02,
        "contrast":       1.28,
        "saturation":     1.35,
        "sharpen":        1.42,
        "blur":           0.0,

        "shake_x":        4,
        "shake_y":        4,

        "beat_flash":     0.19,
        "bass_flash":     0.26,
        "drop_flash":     0.40,

        "vignette":       0.40,
        "hue_shift":      3,

        "fps": 30,
    },

    # ── ROCK ───────────────────────────────────────────────────────────────
    "rock": {
        "zoom_speed":     0.034,
        "max_zoom":       1.24,
        "pulse_strength": 0.005,

        "brightness":     0.01,
        "contrast":       1.32,
        "saturation":     1.22,
        "sharpen":        1.55,
        "blur":           0.0,

        "shake_x":        6,
        "shake_y":        6,

        "beat_flash":     0.22,
        "bass_flash":     0.30,
        "drop_flash":     0.46,

        "vignette":       0.55,
        "hue_shift":      5,

        "fps": 30,
    },

    # ── METAL ──────────────────────────────────────────────────────────────
    "metal": {
        "zoom_speed":     0.040,
        "max_zoom":       1.26,
        "pulse_strength": 0.007,

        "brightness":     0.00,
        "contrast":       1.38,
        "saturation":     1.15,
        "sharpen":        1.70,
        "blur":           0.0,

        "shake_x":        7,
        "shake_y":        7,

        "beat_flash":     0.24,
        "bass_flash":     0.34,
        "drop_flash":     0.52,

        "vignette":       0.65,
        "hue_shift":      6,

        "fps": 30,
    },

    # ── ELECTRONIC ─────────────────────────────────────────────────────────
    # Mais vibrante — canal de música eletrônica precisa de CORES VIVAS
    "electronic": {
        "zoom_speed":     0.030,
        "max_zoom":       1.22,
        "pulse_strength": 0.005,

        "brightness":     0.03,    # mais brilhante que antes
        "contrast":       1.32,
        "saturation":     1.55,    # ultra saturado para neons vibrantes
        "sharpen":        1.45,
        "blur":           0.0,

        "shake_x":        5,
        "shake_y":        4,

        "beat_flash":     0.20,
        "bass_flash":     0.28,
        "drop_flash":     0.45,

        "vignette":       0.35,    # vignette menor para não escurecer
        "hue_shift":      10,

        "fps": 30,
    },

    # ── CINEMATIC ──────────────────────────────────────────────────────────
    "cinematic": {
        "zoom_speed":     0.016,
        "max_zoom":       1.12,
        "pulse_strength": 0.002,

        "brightness":     0.02,
        "contrast":       1.20,
        "saturation":     1.12,
        "sharpen":        1.18,
        "blur":           0.0,

        "shake_x":        1,
        "shake_y":        1,

        "beat_flash":     0.10,
        "bass_flash":     0.16,
        "drop_flash":     0.26,

        "vignette":       0.60,
        "hue_shift":      0,

        "fps": 30,
    },

    # ── LOFI ───────────────────────────────────────────────────────────────
    "lofi": {
        "zoom_speed":     0.009,
        "max_zoom":       1.07,
        "pulse_strength": 0.001,

        "brightness":     0.03,    # mais warm/brilhante
        "contrast":       1.10,
        "saturation":     0.92,
        "sharpen":        0.85,
        "blur":           0.0,

        "shake_x":        0,
        "shake_y":        0,

        "beat_flash":     0.05,
        "bass_flash":     0.08,
        "drop_flash":     0.12,

        "vignette":       0.35,
        "hue_shift":      0,

        "fps": 30,
    },

    # ── INDIE ──────────────────────────────────────────────────────────────
    "indie": {
        "zoom_speed":     0.014,
        "max_zoom":       1.10,
        "pulse_strength": 0.002,

        "brightness":     0.02,
        "contrast":       1.14,
        "saturation":     1.05,
        "sharpen":        1.00,
        "blur":           0.0,

        "shake_x":        1,
        "shake_y":        1,

        "beat_flash":     0.08,
        "bass_flash":     0.12,
        "drop_flash":     0.18,

        "vignette":       0.40,
        "hue_shift":      0,

        "fps": 30,
    },

    # ── POP ────────────────────────────────────────────────────────────────
    "pop": {
        "zoom_speed":     0.022,
        "max_zoom":       1.17,
        "pulse_strength": 0.003,

        "brightness":     0.04,    # bem brilhante — pop é colorido
        "contrast":       1.18,
        "saturation":     1.40,
        "sharpen":        1.20,
        "blur":           0.0,

        "shake_x":        2,
        "shake_y":        2,

        "beat_flash":     0.14,
        "bass_flash":     0.20,
        "drop_flash":     0.32,

        "vignette":       0.25,    # quase sem vignette — pop é aberto
        "hue_shift":      3,

        "fps": 30,
    },

    # ── FUNK ───────────────────────────────────────────────────────────────
    "funk": {
        "zoom_speed":     0.032,
        "max_zoom":       1.22,
        "pulse_strength": 0.005,

        "brightness":     0.02,
        "contrast":       1.30,
        "saturation":     1.50,    # funk é COLORIDO
        "sharpen":        1.35,
        "blur":           0.0,

        "shake_x":        5,
        "shake_y":        5,

        "beat_flash":     0.22,
        "bass_flash":     0.30,
        "drop_flash":     0.44,

        "vignette":       0.35,
        "hue_shift":      4,

        "fps": 30,
    },

    # ── DARK ───────────────────────────────────────────────────────────────
    "dark": {
        "zoom_speed":     0.024,
        "max_zoom":       1.17,
        "pulse_strength": 0.003,

        "brightness":    -0.01,    # ligeiramente escuro mas NÃO demais
        "contrast":       1.34,
        "saturation":     1.00,
        "sharpen":        1.28,
        "blur":           0.0,

        "shake_x":        3,
        "shake_y":        3,

        "beat_flash":     0.16,
        "bass_flash":     0.22,
        "drop_flash":     0.34,

        "vignette":       0.70,
        "hue_shift":      0,

        "fps": 30,
    },

    # ── DEFAULT ────────────────────────────────────────────────────────────
    "default": {
        "zoom_speed":     0.024,
        "max_zoom":       1.18,
        "pulse_strength": 0.003,

        "brightness":     0.02,    # sempre positivo — evita escuro
        "contrast":       1.22,
        "saturation":     1.25,
        "sharpen":        1.22,
        "blur":           0.0,

        "shake_x":        3,
        "shake_y":        3,

        "beat_flash":     0.16,
        "bass_flash":     0.22,
        "drop_flash":     0.34,

        "vignette":       0.38,
        "hue_shift":      0,

        "fps": 30,
    },
}


def get_profile(style: str) -> dict:
    """Retorna perfil com fallback para default."""
    default = EDIT_PROFILES["default"]
    raw     = EDIT_PROFILES.get(style, default)
    return {**default, **raw}
