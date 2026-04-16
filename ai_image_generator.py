import os
import re
import tempfile
import requests
import random
from pathlib import Path


# =========================
# LIMPEZA DE TÍTULO
# =========================
def _clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# =========================
# QUALIDADE GLOBAL (ANTI ESCURIDÃO)
# =========================
GLOBAL_QUALITY = """
ultra high quality, professional cinematic scene,
perfect lighting, balanced exposure,
clear subject, NOT dark, NOT silhouette,
sharp details, highly detailed,
clean composition, thumbnail style,
vibrant colors, rich color grading,
no crushed blacks, no heavy shadows,
subject fully visible
""".strip()


# =========================
# PROMPT PRINCIPAL
# =========================
def build_ai_prompt(style: str, filename: str, styles=None) -> str:
    base_title = _clean_title(filename)
    styles = styles or [style]

    angle = random.choice([
        "low angle cinematic shot",
        "close-up dramatic framing",
        "wide cinematic composition",
        "center focus subject",
    ])

    hybrid = ""
    if len(styles) > 1:
        hybrid = f"mix of {' and '.join(styles)}, "

    prompt_map = {
        "phonk": f"{base_title}, neon street racing, car drifting, cyberpunk city, purple neon lights, reflections, clear subject, {hybrid}{angle}",
        "trap": f"{base_title}, luxury trap aesthetic, stylish person, neon lighting, strong highlights, face visible, {hybrid}{angle}",
        "rock": f"{base_title}, rock concert, guitarist, stage lights, smoke, sparks, subject visible, {hybrid}{angle}",
        "metal": f"{base_title}, metal concert, fire, flames, aggressive energy, subject clear, {hybrid}{angle}",
        "lofi": f"{base_title}, cozy room, rain window, warm light, calm vibe, subject visible, {hybrid}{angle}",
        "indie": f"{base_title}, dreamy street scene, sunset lighting, cinematic tones, subject visible, {hybrid}{angle}",
        "electronic": f"{base_title}, futuristic neon environment, glowing lights, vibrant colors, subject clear, {hybrid}{angle}",
        "cinematic": f"{base_title}, epic cinematic scene, volumetric lighting, dramatic sky, subject highlighted, {hybrid}{angle}",
        "dark": f"{base_title}, dark aesthetic BUT subject visible, red glow, fog, cinematic lighting, not too dark, {hybrid}{angle}",
        "pop": f"{base_title}, glossy pop aesthetic, model, neon lights, fashion lighting, vibrant colors, {hybrid}{angle}",
        "default": f"{base_title}, cinematic scene, strong lighting, clear subject, visually striking, {hybrid}{angle}",
    }

    core = prompt_map.get(style, prompt_map["default"])

    return f"{GLOBAL_QUALITY}, {core}, vertical 9:16, no text, no watermark"


# =========================
# ENRIQUECER PROMPT
# =========================
def _enrich_prompt(prompt: str) -> str:
    extras = [
        "cinematic depth",
        "professional color grading",
        "sharp focus subject",
        "clean lighting",
    ]
    return f"{prompt}, {random.choice(extras)}"


# =========================
# REPLICATE (GERAÇÃO)
# =========================
def _generate_via_replicate(prompt: str, output_path: str) -> bool:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("[IA] Sem token replicate")
        return False

    url = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }

    payload = {
        "input": {
            "prompt": _enrich_prompt(prompt),
            "aspect_ratio": "9:16",
            "output_format": "png",
            "num_outputs": 1,
            "num_inference_steps": 4,
            "seed": random.randint(1, 999999999),
        }
    }

    try:
        print("[IA] Gerando imagem...")

        resp = requests.post(url, json=payload, headers=headers, timeout=90)

        if not resp.ok:
            print("[IA] erro replicate:", resp.status_code)
            return False

        data = resp.json()
        output = data.get("output")

        if not output:
            print("[IA] sem output")
            return False

        img_url = output[0] if isinstance(output, list) else output

        img_resp = requests.get(img_url, timeout=60)

        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        print("[IA] imagem criada:", output_path)
        return True

    except Exception as e:
        print("[IA] erro:", e)
        return False


# =========================
# FUNÇÃO PRINCIPAL
# =========================
def generate_image(prompt: str, output_path: str = None):
    if output_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        output_path = temp_path

    if _generate_via_replicate(prompt, output_path):
        return output_path

    return None
