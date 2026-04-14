import os
import random

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
    return "random"


def get_random_background(style):
    backgrounds = get_all_backgrounds()

    if not backgrounds:
        print("Nenhum background encontrado. Usando fundo automático.")
        return FALLBACK_BACKGROUND

    chosen = random.choice(backgrounds)
    print(f"Background escolhido: {chosen}")
    return chosen
