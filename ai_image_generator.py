import os
import re
import tempfile
import requests
import time
import random
from pathlib import Path


def _clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def build_ai_prompt(style: str, filename: str, styles: list[str] | None = None) -> str:
    base_title = _clean_title(filename)
    styles = styles or [style]

    camera_angles = [
        "low angle cinematic shot",
        "close-up dramatic framing",
        "wide cinematic composition",
        "off-center artistic framing",
        "top view perspective",
    ]

    lighting_styles = [
        "harsh red lighting",
        "neon glow lighting",
        "soft cinematic shadows",
        "high contrast dramatic light",
        "dark ambient lighting",
    ]

    cinematic_boosters = [
        "album cover quality",
        "ultra detailed",
        "emotionally intense",
        "professional photography",
        "dramatic atmosphere",
        "visually striking composition",
        "rich depth and contrast",
        "not generic",
    ]

    angle = random.choice(camera_angles)
    lighting = random.choice(lighting_styles)
    booster = random.choice(cinematic_boosters)

    hybrid_extra = ""
    if len(styles) > 1:
        hybrid_extra = f"hybrid atmosphere mixing {' and '.join(styles)}, "

    prompt_map = {
        "metal": (
            f"{base_title}, dark demonic ritual scene, massive horned demon emerging from shadows, "
            f"gothic cathedral destroyed, burning altar, fire, ash, smoke, cursed atmosphere, "
            f"terrifying red and black palette, infernal energy, {hybrid_extra}"
            f"{angle}, {lighting}, {booster}"
        ),
        "rock": (
            f"{base_title}, dark underground rock concert, silhouette guitarist in red light, "
            f"heavy smoke, fire sparks, rebellious atmosphere, dramatic stage energy, "
            f"grunge cinematic mood, {hybrid_extra}"
            f"{angle}, {lighting}, {booster}"
        ),
        "phonk": (
            f"{base_title}, japanese street racing at night, neon lights reflecting on wet asphalt, "
            f"drift car sliding with smoke, cyberpunk atmosphere, purple and blue tones, "
            f"aggressive underground energy, {hybrid_extra}"
            f"{angle}, neon glow lighting, {booster}"
        ),
        "trap": (
            f"{base_title}, dark luxury trap aesthetic, expensive cars, chains, urban night scene, "
            f"mysterious silhouette, rich villain vibe, deep contrast, stylish shadows, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
        "lofi": (
            f"{base_title}, cozy melancholic room at night, rain on window, warm lamp light, "
            f"nostalgic calm atmosphere, soft shadows, peaceful but sad mood, "
            f"{hybrid_extra}{angle}, soft cinematic lighting, {booster}"
        ),
        "indie": (
            f"{base_title}, dreamy nostalgic indie scene, empty street at dusk, emotional atmosphere, "
            f"soft film look, bittersweet memory-like mood, artistic storytelling composition, "
            f"{hybrid_extra}{angle}, soft shadows, {booster}"
        ),
        "electronic": (
            f"{base_title}, futuristic cyber world, glowing neon structures, digital energy, "
            f"sci-fi atmosphere, immersive electronic mood, vivid cinematic lighting, "
            f"{hybrid_extra}{angle}, neon glow lighting, {booster}"
        ),
        "cinematic": (
            f"{base_title}, epic cinematic landscape, dramatic sky, emotional large-scale atmosphere, "
            f"movie poster feeling, powerful scene, volumetric lighting, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
        "funk": (
            f"{base_title}, brazilian funk nightlife, urban favela-inspired scene, vibrant party lights, "
            f"bold energy, loud visual style, dynamic movement, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
        "dark": (
            f"{base_title}, shadowy mysterious figure, sinister red and black tones, fog, dark cinematic mood, "
            f"ominous atmosphere, horror-inspired aesthetic, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
        "pop": (
            f"{base_title}, glossy modern pop visual, vibrant lights, stylish fashion-forward scene, "
            f"dreamy elegant atmosphere, colorful but cinematic, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
        "default": (
            f"{base_title}, cinematic aesthetic scene, strong atmosphere, dramatic lighting, "
            f"emotional composition, visually striking image, "
            f"{hybrid_extra}{angle}, {lighting}, {booster}"
        ),
    }

    core_prompt = prompt_map.get(style, prompt_map["default"])

    return (
        f"{core_prompt}, "
        "vertical 9:16, no text, no watermark, no logo, "
        "unique composition, different angle, not repetitive, masterpiece"
    )


def _enrich_prompt(prompt: str) -> str:
    micro_variations = [
        "high quality details",
        "cinematic depth",
        "dynamic perspective",
        "rich texture",
        "clean subject focus",
        "dramatic mood",
        "enhanced contrast",
        "refined visual composition",
    ]

    return f"{prompt}, {random.choice(micro_variations)}"


def _generate_via_replicate(prompt: str, output_path: str) -> bool:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
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
        print("[IA] Tentando Replicate (flux-schnell via HTTP direto)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=90)

        if resp.status_code == 402:
            print("[IA] Replicate: conta sem crédito/billing configurado")
            return False

        if resp.status_code == 422:
            print(f"[IA] Replicate 422: {resp.text[:300]}")
            return False

        if not resp.ok:
            print(f"[IA] Replicate erro {resp.status_code}: {resp.text[:300]}")
            return False

        data = resp.json()

        if data.get("status") not in ("succeeded",):
            prediction_url = data.get("urls", {}).get("get")

            if prediction_url:
                for _ in range(30):
                    time.sleep(2)

                    poll_resp = requests.get(
                        prediction_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=20
                    )

                    if not poll_resp.ok:
                        print(f"[IA] Polling Replicate falhou: {poll_resp.status_code}")
                        return False

                    poll = poll_resp.json()
                    status = poll.get("status")

                    if status == "succeeded":
                        data = poll
                        break

                    if status == "failed":
                        print(f"[IA] Replicate prediction falhou: {poll.get('error')}")
                        return False

        output = data.get("output")
        if not output:
            print("[IA] Replicate: sem output na resposta")
            return False

        img_url = output[0] if isinstance(output, list) else output

        img_resp = requests.get(img_url, timeout=60)
        if not img_resp.ok:
            print(f"[IA] Erro ao baixar imagem do Replicate: {img_resp.status_code}")
            return False

        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        print(f"[IA] ✅ Replicate OK: {output_path}")
        return True

    except Exception as e:
        print(f"[IA] Replicate exceção: {e}")

    return False


def _generate_via_huggingface(prompt: str, output_path: str) -> bool:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("[IA] HF_TOKEN não configurado")
        return False

    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": _enrich_prompt(prompt)}

    try:
        print("[IA] Tentando Hugging Face (FLUX.1-schnell)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.status_code == 503:
            try:
                wait = resp.json().get("estimated_time", 20)
            except Exception:
                wait = 20

            print(f"[IA] HF modelo carregando, aguardando {wait:.0f}s...")
            time.sleep(min(wait, 30))
            resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.ok and resp.headers.get("content-type", "").startswith("image"):
            with open(output_path, "wb") as f:
                f.write(resp.content)

            print(f"[IA] ✅ Hugging Face OK: {output_path}")
            return True

        print(f"[IA] HF erro {resp.status_code}: {resp.text[:300]}")

    except Exception as e:
        print(f"[IA] HF exceção: {e}")

    return False


def generate_image(prompt: str, output_path: str = None) -> str | None:
    """
    Gera imagem com IA.
    Tenta Replicate → Hugging Face → None.
    Retorna caminho do arquivo ou None.
    """
    if output_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        output_path = temp_path

    print(f"[IA] Gerando imagem para: {prompt[:120]}...")

    if _generate_via_replicate(prompt, output_path):
        return output_path

    if _generate_via_huggingface(prompt, output_path):
        return output_path

    print("[IA] ❌ Todas as opções falharam — usando fallback local")
    return None
