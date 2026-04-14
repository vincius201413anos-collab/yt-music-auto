import os
import base64
from pathlib import Path

from openai import OpenAI

OUTPUT_DIR = "assets/generated"

STYLE_PROMPTS = {
    "phonk": "dark japanese street, drift car, neon lights, night, cyberpunk, cinematic, aggressive atmosphere, high contrast, vertical composition, no text, no watermark",
    "rock": "intense rock concert atmosphere, smoke, red lights, dramatic stage energy, cinematic, high contrast, vertical composition, no text, no watermark",
    "electronic": "futuristic abstract neon lights, digital energy, cyberpunk atmosphere, cinematic, vibrant glow, vertical composition, no text, no watermark",
    "trap": "urban night street, luxury mood, dark cinematic atmosphere, aggressive modern aesthetic, vertical composition, no text, no watermark",
    "lofi": "cozy lofi anime-style city, soft rain, calm aesthetic, dreamy atmosphere, cinematic, vertical composition, no text, no watermark",
    "pop": "bright colorful lights, stylish modern pop aesthetic, glossy cinematic atmosphere, vertical composition, no text, no watermark",
    "dark": "dark cinematic background, smoke, dramatic lighting, moody atmosphere, vertical composition, no text, no watermark",
    "random": "cinematic abstract background, dramatic lighting, aesthetic, vertical composition, no text, no watermark"
}


def generate_ai_image(style, filename):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY não encontrado. Pulando geração de imagem por IA.")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_stem = Path(filename).stem.replace("/", "_").replace("\\", "_")
    image_path = os.path.join(OUTPUT_DIR, f"{safe_stem}_{style}.png")

    if os.path.exists(image_path):
        print(f"Imagem IA já existe: {image_path}")
        return image_path

    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["random"])

    try:
        client = OpenAI(api_key=api_key)

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        print(f"Imagem IA gerada com sucesso: {image_path}")
        return image_path

    except Exception as e:
        print(f"Erro ao gerar imagem com IA: {e}")
        return None
