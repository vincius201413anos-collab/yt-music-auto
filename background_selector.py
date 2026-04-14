import os
import random

BASE_PATH = "assets/backgrounds"

SUPPORTED = (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov")


def get_all_backgrounds():
    backgrounds = []

    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.lower().endswith(SUPPORTED):
                backgrounds.append(os.path.join(root, file))

    return backgrounds


def detect_style(filename):
    return "random"


def get_random_background(style):

    backgrounds = get_all_backgrounds()

    if not backgrounds:
        raise ValueError("Nenhum background encontrado")

    return random.choice(backgrounds)
