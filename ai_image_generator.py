import os
import random
import replicate

# 🔥 BASE FIXA (QUALIDADE + ESTILO)
BASE_STYLE = """
beautiful anime girl, cute, soft lighting, cozy atmosphere,
natural pose, candid moment, not looking at camera,
detailed environment, cinematic lighting, depth of field,
soft glow, high detail, anime aesthetic, masterpiece
"""

# 🎬 CENAS DINÂMICAS (EVITA IMAGEM PARADA)
SCENES = [
    "sitting by window at night, rain outside, listening to music",
    "lying on bed with headphones, looking at ceiling, calm mood",
    "writing in notebook, desk lamp, night study vibe",
    "looking at city skyline through window, neon lights",
    "drinking coffee in cozy room, night atmosphere",
    "walking alone in night city, headphones on",
    "sitting on floor with fairy lights, relaxed mood",
    "leaning on desk, listening to music, night vibes",
    "watching the sky through window, deep thinking mood",
    "sitting on bed hugging knees, emotional vibe"
]

# 🎨 ESTILO POR GÊNERO (combina com música)
STYLE_MAP = {
    "phonk": "dark neon, cyberpunk, purple lighting, night city",
    "trap": "urban night, street lights, cinematic shadows",
    "lofi": "cozy room, warm light, relaxing atmosphere",
    "drill": "dark mood, aggressive lighting, red tones",
    "sad": "rain, melancholic mood, soft blue tones",
    "ambient": "dreamy, soft glow, peaceful atmosphere"
}

def detect_style(filename):
    name = filename.lower()
    for key in STYLE_MAP:
        if key in name:
            return STYLE_MAP[key]
    return "cinematic lighting, night aesthetic"

# 🚀 GERADOR FINAL
def generate_image(music_filename, output_path):
    style = detect_style(music_filename)
    scene = random.choice(SCENES)

    prompt = f"""
    {BASE_STYLE},
    {scene},
    {style},
    soft motion feeling, wind in hair, subtle movement,
    highly detailed anime illustration, best quality
    """

    print("🎨 Gerando imagem IA...")

    output = replicate.run(
        "stability-ai/sdxl:latest",
        input={
            "prompt": prompt,
            "width": 1024,
            "height": 1024
        }
    )

    image_url = output[0]

    import requests
    img_data = requests.get(image_url).content

    with open(output_path, "wb") as f:
        f.write(img_data)

    print("✅ Imagem salva:", output_path)
