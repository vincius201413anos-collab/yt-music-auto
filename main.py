import os
import random

BASE_PATH = "assets/backgrounds"


def detect_style(filename):

    name = filename.lower()

    if "phonk" in name:
        return "phonk"

    if "trap" in name:
        return "trap"

    if "lofi" in name:
        return "lofi"

    if "dark" in name:
        return "dark"

    if "rock" in name:
        return "rock"

    if "pop" in name:
        return "pop"

    if "electronic" in name:
        return "electronic"

    return "ai_generated"


def get_random_background(style):

    folder = os.path.join(BASE_PATH, style)

    if not os.path.exists(folder):
        folder = os.path.join(BASE_PATH, "ai_generated")

    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"))
    ]

    if not files:
        folder = os.path.join(BASE_PATH, "ai_generated")

        files = [
            f for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"))
        ]

    if not files:
        raise ValueError("Nenhum background encontrado")

    return os.path.join(folder, random.choice(files))
