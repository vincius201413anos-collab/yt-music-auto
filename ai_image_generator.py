import base64
import io
import os
from pathlib import Path

import requests
from PIL import Image

OUTPUT_DIR = "assets/generated"
SD_URL = "http://127.0.0.1:7860"

STYLE_PROMPTS = {
    "phonk": "dark japanese street, drift car, neon lights, night, cyberpunk, cinematic, aggressive atmosphere, high contrast, vertical composition, no text, no watermark",
    "rock": "intense rock concert atmosphere, smoke, red lights, dramatic stage energy, cinematic, high contrast, vertical composition, no text, no watermark",
    "metal": "heavy metal concert, dark stage, aggressive lighting, smoke, dramatic atmosphere, red lights, cinematic, vertical composition, no text, no watermark",
    "electronic": "futuristic abstract neon lights, digital energy, cyberpunk atmosphere, cinematic, vibrant glow, vertical composition, no text, no watermark",
    "trap": "urban night street, luxury mood, dark cinematic atmosphere, aggressive modern aesthetic, vertical composition, no text, no watermark",
    "lofi": "cozy lofi anime-style city, soft rain, calm aesthetic, dreamy atmosphere, cinematic, vertical composition, no text, no watermark",
    "pop": "bright colorful lights, stylish modern pop aesthetic, glossy cinematic atmosphere, vertical composition, no text, no watermark",
    "indie": "indie aesthetic, cinematic, soft film grain, vintage colors, emotional atmosphere, artistic composition, vertical composition, no text, no watermark",
    "instrumental": "cinematic ambient background, emotional lighting, atmospheric scene, dramatic cinematic composition, vertical composition, no text, no watermark",
    "dark": "dark cinematic background, smoke, dramatic lighting, moody atmosphere, vertical composition, no text, no watermark",
    "random": "cinematic abstract background, dramatic lighting, aesthetic, vertical composition, no text, no watermark"
}


def generate_ai_image(style, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_stem = Path(filename).stem.replace("/", "_").replace("\\", "_")
    image_path = os.path.join(OUTPUT_DIR, f"{safe_stem}_{style}.png")

    if os.path.exists(image_path):
        print(f"Imagem IA já existe: {image_path}")
        return image_path

    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["random"])

    payload = {
        "prompt": prompt,
        "negative_prompt": "text, watermark, logo, blurry, low quality, deformed, ugly",
        "steps": 25,
        "cfg_scale": 7,
        "width": 512,
        "height": 912,
        "sampler_name": "DPM++ 2M",
        "batch_size": 1,
        "n_iter": 1
    }

    try:
        response = requests.post(
            f"{SD_URL}/sdapi/v1/txt2img",
            json=payload,
            timeout=300
        )
        response.raise_for_status()

        result = response.json()

        if not result.get("images"):
            print("Nenhuma imagem retornada pela IA local.")
            return None

        image_b64 = result["images"][0]
        image_data = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_data))
        image.save(image_path)

        print(f"Imagem IA gerada com sucesso: {image_path}")
        return image_path

    except Exception as e:
        print(f"Erro ao gerar imagem com IA local: {e}")
        return None
