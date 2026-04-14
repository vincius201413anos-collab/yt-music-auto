import os
import random
import re

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


def extract_style_from_filename(filename):
    match = re.search(r"\[(.*?)\]", filename.lower())
    if match:
        return match.group(1).strip()
    return "random"


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
        print(f"Pasta não encontrada: {BASE_PATH}. Usando fundo automático.")
        return backgrounds

    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                backgrounds.append(os.path.join(root, file))

    return backgrounds


def detect_style(filename):
    style = extract_style_from_filename(filename)
    print(f"Estilo detectado pelo nome: {style}")
    return style


def get_random_background(style):
    backgrounds = get_backgrounds_for_style(style)

    if not backgrounds:
        print("Nenhum background do estilo encontrado. Usando random.")
        backgrounds = get_all_backgrounds()

    if not backgrounds:
        print("Nenhum background encontrado. Usando fundo automático.")
        return FALLBACK_BACKGROUND

    chosen = random.choice(backgrounds)
    print(f"Background escolhido: {chosen}")
    return chosen
