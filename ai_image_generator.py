import os
import requests
from pathlib import Path

OUTPUT_DIR = "assets/generated"

STYLE_PROMPTS = {
    "phonk": "dark japanese street, drift car, neon lights, night, cyberpunk, cinematic, vertical",
    "rock": "rock concert, smoke, red lights, stage, dramatic, cinematic, vertical",
    "electronic": "futuristic abstract lights, neon, digital, cyberpunk, cinematic, vertical",
    "trap": "urban night, luxury, dark street, cinematic, vertical",
    "lofi": "lofi anime city, rain, calm, aesthetic, cozy, vertical",
    "pop": "bright colorful lights, modern pop style, aesthetic, vertical",
    "dark": "dark cinematic background, smoke, dramatic lighting, vertical",
    "random": "cinematic abstract background, aesthetic, vertical"
}


def generate_ai_image(style, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["random"])

    image_path = os.path.join(
        OUTPUT_DIR,
        f"{Path(filename).stem}_{style}.jpg"
    )

    # Placeholder simples por enquanto
    # depois vamos conectar IA real
    return image_path
