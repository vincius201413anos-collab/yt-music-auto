"""
edit_profiles.py — Perfis de edição elite por estilo musical.

Calibrado para máxima retenção em YouTube Shorts 2025:
- Saturação alta para telas mobile (OLED/AMOLED)
- Contraste ajustado para não estourar no HDR
- Flash calibrado para impacto sem causar fadiga visual
- FPS 30 padrão (melhor compatibilidade + qualidade vs 60fps)

Cada perfil define a "personalidade visual" do estilo.
"""

# ── NOTAS TÉCNICAS ────────────────────────────────────────────────────────────
# brightness: base para o flash_expression. Positivo = mais brilhante.
#             Manter >= -0.02 para não escurecer em telas mobile.
# saturation: 1.0 = original. 1.4+ = vibrante. 1.6+ = hyper-saturado.
# contrast:   1.0 = original. 1.3+ = cinema. Evitar > 1.5 (crushed blacks).
# sharpen:    0.8 = soft. 1.4 = nítido. 2.0 = over-sharpened (evitar).
# vignette:   0.0 = sem. 0.5 = moderado. 0.8 = escuro nas bordas.
# beat_flash: brilho extra no beat. 0.20 = suave. 0.35+ = agressivo.
# bass_flash: brilho extra no bass. Sempre > beat_flash.
# drop_flash: brilho extra no drop. O mais alto dos três.
# shake_x/y:  pixels de deslocamento máximo. 0 = sem shake.
# zoom_speed: velocidade da respiração base. 0.01 = lento. 0.04 = rápido.
# max_zoom:   zoom máximo da respiração (sem contar drop punch).
# pulse_strength: intensidade do micro-drift orgânico.

EDIT_PROFILES = {

    # ── PHONK ─────────────────────────────────────────────────────────────────
    # Escuro, pesado, agressivo. Cores frias com flash branco intenso.
    "phonk": {
        "zoom_speed":      0.038,
        "max_zoom":        1.24,
        "pulse_strength":  0.007,
        "brightness":      0.00,
        "contrast":        1.40,
        "saturation":      1.35,   # menos saturado — phonk é mais dessaturado
        "sharpen":         1.65,
        "blur":            0.0,
        "shake_x":         7,
        "shake_y":         6,
        "beat_flash":      0.24,
        "bass_flash":      0.34,
        "drop_flash":      0.52,
        "vignette":        0.60,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── TRAP ──────────────────────────────────────────────────────────────────
    # Urbano, escuro mas com cores. Shake médio, flash moderado.
    "trap": {
        "zoom_speed":      0.030,
        "max_zoom":        1.20,
        "pulse_strength":  0.005,
        "brightness":      0.02,
        "contrast":        1.32,
        "saturation":      1.40,
        "sharpen":         1.45,
        "blur":            0.0,
        "shake_x":         5,
        "shake_y":         4,
        "beat_flash":      0.20,
        "bass_flash":      0.30,
        "drop_flash":      0.44,
        "vignette":        0.45,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── ROCK ──────────────────────────────────────────────────────────────────
    # Energia alta, cores quentes, shake intenso.
    "rock": {
        "zoom_speed":      0.038,
        "max_zoom":        1.26,
        "pulse_strength":  0.006,
        "brightness":      0.01,
        "contrast":        1.36,
        "saturation":      1.28,
        "sharpen":         1.58,
        "blur":            0.0,
        "shake_x":         7,
        "shake_y":         6,
        "beat_flash":      0.24,
        "bass_flash":      0.32,
        "drop_flash":      0.50,
        "vignette":        0.55,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── METAL ─────────────────────────────────────────────────────────────────
    # Máxima agressividade. Praticamente dessaturado. Shake violento.
    "metal": {
        "zoom_speed":      0.044,
        "max_zoom":        1.28,
        "pulse_strength":  0.008,
        "brightness":      -0.01,
        "contrast":        1.44,
        "saturation":      1.10,   # quasi P&B
        "sharpen":         1.75,
        "blur":            0.0,
        "shake_x":         9,
        "shake_y":         8,
        "beat_flash":      0.26,
        "bass_flash":      0.36,
        "drop_flash":      0.56,
        "vignette":        0.70,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── ELECTRONIC / EDM ──────────────────────────────────────────────────────
    # Neons vibrantes, ultra-saturado, drop explosivo.
    "electronic": {
        "zoom_speed":      0.034,
        "max_zoom":        1.24,
        "pulse_strength":  0.006,
        "brightness":      0.03,
        "contrast":        1.34,
        "saturation":      1.65,   # hyper-saturado para neons
        "sharpen":         1.48,
        "blur":            0.0,
        "shake_x":         5,
        "shake_y":         4,
        "beat_flash":      0.22,
        "bass_flash":      0.32,
        "drop_flash":      0.50,
        "vignette":        0.30,   # vignette mínimo para não sufocar as cores
        "hue_shift":       0,
        "fps":             30,
    },

    # ── CINEMATIC ─────────────────────────────────────────────────────────────
    # Elegante, lento, cores frias e profundas. Sem shake.
    "cinematic": {
        "zoom_speed":      0.016,
        "max_zoom":        1.12,
        "pulse_strength":  0.002,
        "brightness":      0.02,
        "contrast":        1.22,
        "saturation":      1.10,
        "sharpen":         1.20,
        "blur":            0.0,
        "shake_x":         0,
        "shake_y":         0,
        "beat_flash":      0.10,
        "bass_flash":      0.16,
        "drop_flash":      0.28,
        "vignette":        0.65,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── LOFI ──────────────────────────────────────────────────────────────────
    # Calmo, warm, sem agressividade. Zoom quase imperceptível.
    "lofi": {
        "zoom_speed":      0.008,
        "max_zoom":        1.06,
        "pulse_strength":  0.001,
        "brightness":      0.04,
        "contrast":        1.08,
        "saturation":      0.90,   # levemente dessaturado = estético lofi
        "sharpen":         0.80,
        "blur":            0.0,
        "shake_x":         0,
        "shake_y":         0,
        "beat_flash":      0.05,
        "bass_flash":      0.08,
        "drop_flash":      0.12,
        "vignette":        0.38,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── INDIE ─────────────────────────────────────────────────────────────────
    # Suave, colorido, natural. Movimento leve.
    "indie": {
        "zoom_speed":      0.014,
        "max_zoom":        1.10,
        "pulse_strength":  0.002,
        "brightness":      0.02,
        "contrast":        1.14,
        "saturation":      1.10,
        "sharpen":         1.02,
        "blur":            0.0,
        "shake_x":         1,
        "shake_y":         1,
        "beat_flash":      0.08,
        "bass_flash":      0.13,
        "drop_flash":      0.20,
        "vignette":        0.40,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── POP ───────────────────────────────────────────────────────────────────
    # Brilhante, colorido, energético mas acessível. Perfeito para anime pop.
    "pop": {
        "zoom_speed":      0.024,
        "max_zoom":        1.18,
        "pulse_strength":  0.004,
        "brightness":      0.04,
        "contrast":        1.20,
        "saturation":      1.50,
        "sharpen":         1.25,
        "blur":            0.0,
        "shake_x":         2,
        "shake_y":         2,
        "beat_flash":      0.16,
        "bass_flash":      0.22,
        "drop_flash":      0.36,
        "vignette":        0.22,   # quase sem vignette — pop é aberto
        "hue_shift":       0,
        "fps":             30,
    },

    # ── FUNK ──────────────────────────────────────────────────────────────────
    # Groove, cores quentes, muito colorido. Shake rítmico constante.
    "funk": {
        "zoom_speed":      0.034,
        "max_zoom":        1.22,
        "pulse_strength":  0.006,
        "brightness":      0.02,
        "contrast":        1.30,
        "saturation":      1.55,
        "sharpen":         1.38,
        "blur":            0.0,
        "shake_x":         5,
        "shake_y":         5,
        "beat_flash":      0.22,
        "bass_flash":      0.30,
        "drop_flash":      0.44,
        "vignette":        0.32,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── DARK ──────────────────────────────────────────────────────────────────
    # Atmosférico, sombrio. Flash cirúrgico. Vignette forte.
    "dark": {
        "zoom_speed":      0.020,
        "max_zoom":        1.16,
        "pulse_strength":  0.003,
        "brightness":      -0.01,
        "contrast":        1.36,
        "saturation":      0.95,
        "sharpen":         1.30,
        "blur":            0.0,
        "shake_x":         3,
        "shake_y":         3,
        "beat_flash":      0.18,
        "bass_flash":      0.26,
        "drop_flash":      0.40,
        "vignette":        0.72,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── ANIME ─────────────────────────────────────────────────────────────────
    # Vibrante, nítido, energético. Otimizado para arte anime estilo 2D.
    "anime": {
        "zoom_speed":      0.028,
        "max_zoom":        1.20,
        "pulse_strength":  0.005,
        "brightness":      0.03,
        "contrast":        1.28,
        "saturation":      1.58,   # cores anime são muito saturadas
        "sharpen":         1.60,   # nitidez alta para linhas do anime
        "blur":            0.0,
        "shake_x":         4,
        "shake_y":         3,
        "beat_flash":      0.20,
        "bass_flash":      0.28,
        "drop_flash":      0.46,
        "vignette":        0.28,
        "hue_shift":       0,
        "fps":             30,
    },

    # ── DEFAULT ───────────────────────────────────────────────────────────────
    "default": {
        "zoom_speed":      0.026,
        "max_zoom":        1.20,
        "pulse_strength":  0.004,
        "brightness":      0.02,
        "contrast":        1.25,
        "saturation":      1.30,
        "sharpen":         1.25,
        "blur":            0.0,
        "shake_x":         3,
        "shake_y":         3,
        "beat_flash":      0.18,
        "bass_flash":      0.25,
        "drop_flash":      0.38,
        "vignette":        0.38,
        "hue_shift":       0,
        "fps":             30,
    },
}


def get_profile(style: str) -> dict:
    """Retorna perfil com merge seguro sobre o default."""
    default = EDIT_PROFILES["default"]
    raw     = EDIT_PROFILES.get(style.lower(), default)
    return {**default, **raw}
