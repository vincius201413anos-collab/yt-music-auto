import os
import random
import re

from ai_image_generator import generate_ai_image

BASE_PATH = "assets/backgrounds"

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".mp4",
    ".mov",
    ".webm"
)

FALLBACK_BACKGROUND = "__AUTO_BLACK__"

KNOWN_STYLES = [
    "phonk",
    "rock",
    "electronic",
    "trap",
    "lofi",
    "dark",
    "pop",
    "indie",
    "metal",
    "instrumental",
    "ai_generated"
]


def extract_style_from_filename(filename):
    filename_lower = filename.lower()

    match = re.search(r"\[(.*?)\]", filename_lower)
    if match:
        style = match.group(1).strip()
        if style in KNOWN_STYLES:
            return style

    for style in KNOWN_STYLES:
        if style in filename_lower:
            return style

    return "dark"


def get_backgrounds_for_style(style):
    style_path = os.path.join(BASE_PATH, style)
    backgrounds = []

    if not os.path.exists(style_path):
        print(f"Pasta de estilo não encontrada: {style_path}")
        return backgrounds

    for file in os.listdir(style_path):
        if file.lower().endswith(SUPPORTED_EXTENSIONS):
            backgrounds.append(os.path.join(style_path, file))

    return backgrounds


def get_all_backgrounds():
    backgrounds = []

    if not os.path.exists(BASE_PATH):
        print(f"Pasta não encontrada: {BASE_PATH}")
        return backgrounds

    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                backgrounds.append(os.path.join(root, file))

    return backgrounds


def detect_style(filename):
    style = extract_style_from_filename(filename)
    print(f"Estilo detectado: {style}")
    return style


def get_ai_background(style, filename):
    try:
        image_path = generate_ai_image(style, filename)

        if image_path and os.path.exists(image_path):
            print(f"Background IA gerado: {image_path}")
            return image_path

        print("Imagem IA ainda não existe. Seguindo para backgrounds locais.")
        return None
    except Exception as e:
        print(f"Erro ao gerar background com IA: {e}")
        return None


def get_random_background(style, filename=None):
    if filename:
        ai_background = get_ai_background(style, filename)
        if ai_background:
            return ai_background

    backgrounds = get_backgrounds_for_style(style)

    if not backgrounds:
        print("Nenhum background do estilo encontrado. Usando fallback.")
        backgrounds = get_all_backgrounds()

    if not backgrounds:
        print("Nenhum background encontrado. Usando fundo automático.")
        return FALLBACK_BACKGROUND

    chosen = random.choice(backgrounds)
    print(f"Background escolhido: {chosen}")
    return chosen
