import os
import re
import tempfile
import requests
import time
import random
from pathlib import Path

def *clean_title(filename: str) -> str:
name = Path(filename).stem
name = re.sub(r"[[^]]+]", "", name)
name = re.sub(r"[*-]+", " ", name)
name = re.sub(r"\s+", " ", name).strip()
return name

# 🔥 NOVO BLOCO GLOBAL (ANTI-ESCURIDÃO)

GLOBAL_QUALITY = """
ultra high quality, professional cinematic scene,
perfect lighting, balanced exposure, no darkness,
clear subject focus, subject fully visible,
sharp details, 8k, highly detailed,
high contrast but NOT underexposed,
clean composition, thumbnail style,
vibrant colors, rich color grading,
no muddy shadows, no black crush,
no silhouette-only subject
"""

def build_ai_prompt(style: str, filename: str, styles: list[str] | None = None) -> str:
base_title = _clean_title(filename)
styles = styles or [style]

```
angle = random.choice([
    "low angle cinematic shot",
    "close-up dramatic framing",
    "wide cinematic composition",
    "center focus subject",
])

hybrid_extra = ""
if len(styles) > 1:
    hybrid_extra = f"hybrid atmosphere mixing {' and '.join(styles)}, "

prompt_map = {
    "metal": (
        f"{base_title}, epic metal scene, guitarist on fire stage, "
        f"flames, sparks, smoke, powerful energy, red lighting BUT visible subject, "
        f"{hybrid_extra}{angle}"
    ),

    "rock": (
        f"{base_title}, rock concert, guitarist under red stage lights, "
        f"smoke, sparks, dramatic but clear lighting, subject visible, "
        f"{hybrid_extra}{angle}"
    ),

    "phonk": (
        f"{base_title}, neon street racing, car drifting, cyberpunk city, "
        f"purple neon glow, wet asphalt reflection, clear subject, "
        f"{hybrid_extra}{angle}"
    ),

    "trap": (
        f"{base_title}, luxury trap aesthetic, stylish person, chains, car, "
        f"neon lighting, strong highlights, clear face visibility, "
        f"{hybrid_extra}{angle}"
    ),

    "lofi": (
        f"{base_title}, cozy room, warm lamp, rain window, soft light, "
        f"clear subject, calm atmosphere, "
        f"{hybrid_extra}{angle}"
    ),

    "indie": (
        f"{base_title}, dreamy indie scene, street at sunset, soft light, "
        f"warm tones, subject visible, cinematic look, "
        f"{hybrid_extra}{angle}"
    ),

    "electronic": (
        f"{base_title}, futuristic neon world, glowing lights, "
        f"digital environment, vibrant colors, subject clear, "
        f"{hybrid_extra}{angle}"
    ),

    "cinematic": (
        f"{base_title}, epic cinematic scene, dramatic sky, "
        f"volumetric light, subject highlighted, not dark, "
        f"{hybrid_extra}{angle}"
    ),

    "funk": (
        f"{base_title}, brazilian funk party, vibrant lights, "
        f"colorful scene, energetic vibe, subject clear, "
        f"{hybrid_extra}{angle}"
    ),

    "dark": (
        f"{base_title}, dark aesthetic BUT visible subject, "
        f"red glow, fog, cinematic lighting, not too dark, "
        f"{hybrid_extra}{angle}"
    ),

    "pop": (
        f"{base_title}, glossy pop visual, model, neon lights, "
        f"fashion lighting, vibrant, clean, sharp face, "
        f"{hybrid_extra}{angle}"
    ),

    "default": (
        f"{base_title}, cinematic aesthetic, strong lighting, "
        f"clear subject, visually striking, not dark, "
        f"{hybrid_extra}{angle}"
    ),
}

core = prompt_map.get(style, prompt_map["default"])

return (
    f"{GLOBAL_QUALITY}, {core}, "
    "vertical 9:16, no text, no watermark, masterpiece"
)
```

def _enrich_prompt(prompt: str) -> str:
extras = [
"cinematic depth",
"high detail textures",
"professional color grading",
"sharp focus subject",
"clean lighting",
]
return f"{prompt}, {random.choice(extras)}"

# 👇 RESTO DO ARQUIVO IGUAL (NÃO PRECISA MEXER)

def _generate_via_replicate(prompt: str, output_path: str) -> bool:
token = os.environ.get("REPLICATE_API_TOKEN")
if not token:
return False

```
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
    print("[IA] Tentando Replicate...")
    resp = requests.post(url, json=payload, headers=headers, timeout=90)

    if not resp.ok:
        return False

    data = resp.json()
    output = data.get("output")

    if not output:
        return False

    img_url = output[0] if isinstance(output, list) else output
    img_resp = requests.get(img_url, timeout=60)

    with open(output_path, "wb") as f:
        f.write(img_resp.content)

    return True

except Exception:
    return False
```

def generate_image(prompt: str, output_path: str = None) -> str | None:
if output_path is None:
fd, temp_path = tempfile.mkstemp(suffix=".png")
os.close(fd)
output_path = temp_path

```
if _generate_via_replicate(prompt, output_path):
    return output_path

return None
```
