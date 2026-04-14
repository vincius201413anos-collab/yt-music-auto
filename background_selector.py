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


def get_all_backgrounds():
    backgrounds = []

    if not os.path.exists(BASE_PATH):
        raise ValueError(f"Pasta não encontrada: {BASE_PATH}")

    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                backgrounds.append(os.path.join(root, file))

    return backgrounds


def detect_style(filename):
    # Agora não dependemos mais do nome
    return "random"


def get_random_background(style):

    backgrounds = get_all_backgrounds()

    if not backgrounds:
        raise ValueError("Nenhum background encontrado em assets/backgrounds")

    chosen = random.choice(backgrounds)

    print(f"Background escolhido: {chosen}")

    return chosen
