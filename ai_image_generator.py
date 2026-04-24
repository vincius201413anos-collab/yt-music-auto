"""
ai_image_generator.py — v7.0 CYBERPUNK EDGERUNNERS EDITION
===========================================================
MUDANÇAS v7.0:
- Prompt reescrito para gerar personagem no estilo EXATO do anime Cyberpunk: Edgerunners
- Fundo: cidade cyberpunk à noite com neon, chuva, reflexos no chão molhado
- Personagem: menina com cabelo branco/preto, olhos brilhantes neon, roupa cyberpunk
- Estética: escuro com neon explodindo — preto profundo + roxo + ciano + magenta
- Lighting: rim light neon roxo/ciano vindo de trás — como no anime
- Estilo artístico: Studio Trigger / Edgerunners / Cyberpunk 2077 art direction
- DNA visual fixo: reconhecível em qualquer short, como mascote do canal
- Negative prompt: maximizado para evitar rostos distorcidos, cores lavadas, realismo
"""

import os
import re
import time
import logging
import random
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ai_image_generator")


# ══════════════════════════════════════════════════════════════════════════════
# DNA VISUAL FIXO v7.0 — Personagem recorrente cyberpunk
# ══════════════════════════════════════════════════════════════════════════════

# Elementos que NUNCA mudam — identidade visual do canal
CHARACTER_DNA = (
    "cyberpunk anime girl, white silver hair with black streaks, "
    "glowing magenta eyes, sharp edgy features, cold expression, "
    "black tactical bodysuit with neon purple trim, "
    "cybernetic implants glowing cyan on neck and arms, "
    "Studio Trigger art style, Cyberpunk Edgerunners aesthetic"
)

BACKGROUND_DNA = (
    "dystopian city night scene, rain soaked streets, "
    "neon signs reflecting on wet ground, purple and cyan neon lights, "
    "massive holographic billboards, dark sky, volumetric fog"
)

LIGHTING_DNA = (
    "dramatic rim lighting, purple neon backlight, cyan neon side light, "
    "deep shadows on face, high contrast chiaroscuro, "
    "lens flare from neon signs, bokeh background"
)

QUALITY_DNA = (
    "masterpiece, best quality, ultra detailed, 8k, "
    "cinematic composition, vertical portrait 9:16, "
    "dynamic pose, motion blur on background, sharp foreground"
)

NEGATIVE_PROMPT = (
    "realistic, photorealistic, 3d render, ugly, deformed face, "
    "extra limbs, bad anatomy, watermark, text, logo, "
    "blurry, low quality, washed out colors, pastel, soft colors, "
    "daytime, bright, happy, cute, chibi, flat shading, "
    "multiple people, crowd, nsfw, nude, revealing"
)

# ── Variações por gênero musical ──────────────────────────────────────────────
GENRE_STYLE_SUFFIX = {
    "phonk": (
        "red blood splatter on ground, drift car silhouette in background, "
        "aggressive energy, intense stare, smoke effects, "
        "red and purple color scheme dominant"
    ),
    "trap": (
        "cyan ice crystals floating, cold blue atmosphere, "
        "money rain bokeh, icy determined expression, "
        "blue and white neon dominant"
    ),
    "dark": (
        "ultra dark atmosphere, purple shadows, "
        "barely visible figure emerging from darkness, "
        "sinister calm expression, minimal neon accents, "
        "near black background with single rim light"
    ),
    "electronic": (
        "electronic circuit patterns glowing on skin, "
        "cyan and magenta split color scheme, "
        "digital glitch artifacts around figure, "
        "holograms and data streams in background"
    ),
    "lofi": (
        "soft neon aesthetic, retro city night, "
        "anime window reflection, rain drops, "
        "vintage VHS aesthetic, warm neon mixed with cool"
    ),
    "default": (
        "purple and cyan neon dominant, "
        "epic vertical cinematic shot, "
        "dystopian beauty, powerful stance"
    ),
}

# ── Poses variadas para não repetir ───────────────────────────────────────────
CHARACTER_POSES = [
    "looking directly at camera with cold intense stare, low angle shot",
    "side profile, face half in shadow half in neon light, three quarter view",
    "looking up at falling rain, neon reflections in eyes, close up",
    "standing at edge of rooftop, city lights below, back to camera glancing over shoulder",
    "crouching on ground, looking up at camera, dominant powerful pose",
    "walking through rain in slow motion, motion blur on background",
    "arms crossed, back against neon sign, smirking confidently",
    "emerging from fog, silhouette with neon outline, mysterious",
]


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO VIA REPLICATE — flux-dev
# ══════════════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
REPLICATE_MODEL = "black-forest-labs/flux-dev"

# Parâmetros de qualidade máxima
FLUX_PARAMS = {
    "width": 1080,
    "height": 1920,
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    """
    Constrói prompt positivo e negativo para o estilo dado.
    seed_variant randomiza a pose para variedade entre vídeos.
    """
    genre_suffix = GENRE_STYLE_SUFFIX.get(style, GENRE_STYLE_SUFFIX["default"])
    pose = CHARACTER_POSES[seed_variant % len(CHARACTER_POSES)]

    positive = (
        f"{CHARACTER_DNA}, "
        f"{pose}, "
        f"{BACKGROUND_DNA}, "
        f"{LIGHTING_DNA}, "
        f"{genre_suffix}, "
        f"{QUALITY_DNA}"
    )

    return positive, NEGATIVE_PROMPT


def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Gera imagem de fundo cyberpunk via Replicate flux-dev.
    Retorna path do arquivo salvo ou None em caso de erro.
    """
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    prompt, negative = build_prompt(style, seed_variant)
    logger.info(f"  ► Gerando background cyberpunk | estilo={style} | variante={seed_variant}")
    logger.debug(f"  ► Prompt: {prompt[:120]}...")

    # Garante diretório
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "version": "latest",
        "input": {
            **FLUX_PARAMS,
            "prompt": prompt,
            "negative_prompt": negative,
            "seed": random.randint(1000, 99999) + seed_variant * 137,
        },
    }

    for attempt in range(1, max_retries + 1):
        try:
            # Inicia predição
            resp = requests.post(
                f"https://api.replicate.com/v1/models/{REPLICATE_MODEL}/predictions",
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            prediction = resp.json()
            prediction_id = prediction["id"]
            logger.info(f"  ► Predição iniciada: {prediction_id}")

            # Polling
            poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            for _ in range(120):  # máx 2 min
                time.sleep(2)
                status_resp = requests.get(poll_url, headers=headers, timeout=15)
                status_resp.raise_for_status()
                status_data = status_resp.json()
                status = status_data.get("status")

                if status == "succeeded":
                    output_urls = status_data.get("output", [])
                    if not output_urls:
                        raise ValueError("Replicate retornou output vazio.")
                    img_url = output_urls[0]

                    # Download da imagem
                    img_resp = requests.get(img_url, timeout=60)
                    img_resp.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(img_resp.content)
                    logger.info(f"  ► Background salvo: {output_path}")
                    return output_path

                elif status == "failed":
                    err = status_data.get("error", "unknown")
                    raise RuntimeError(f"Replicate falhou: {err}")

                elif status in ("starting", "processing"):
                    continue
                else:
                    logger.warning(f"  ⚠ Status inesperado: {status}")

            raise TimeoutError("Replicate demorou mais de 4 minutos.")

        except Exception as e:
            logger.warning(f"  ⚠ Tentativa {attempt}/{max_retries} falhou: {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)
            else:
                logger.error(f"  ✗ Geração de background falhou após {max_retries} tentativas.")
                return None

    return None


def generate_background_batch(
    styles: list[str],
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 2,
) -> dict[str, list[str]]:
    """
    Gera múltiplos backgrounds por estilo.
    Útil para ter variedade nos Shorts.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {}

    for style in styles:
        results[style] = []
        for v in range(variants_per_style):
            filename = f"{style}_bg_{v:02d}.png"
            out_path = str(Path(output_dir) / filename)

            if os.path.exists(out_path):
                logger.info(f"  ► Usando cache: {out_path}")
                results[style].append(out_path)
                continue

            path = generate_background_image(
                style=style,
                output_path=out_path,
                seed_variant=v,
            )
            if path:
                results[style].append(path)
            time.sleep(2)  # rate limit

    return results


def get_or_generate_background(
    style: str = "phonk",
    output_dir: str = "assets/backgrounds",
    force_new: bool = False,
) -> Optional[str]:
    """
    Retorna um background existente ou gera um novo.
    Escolhe aleatoriamente entre os disponíveis para variedade.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Busca backgrounds existentes para o estilo
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))

    if existing and not force_new:
        chosen = random.choice(existing)
        logger.info(f"  ► Background reutilizado: {chosen}")
        return str(chosen)

    # Gera novo
    variant = random.randint(0, 99)
    filename = f"{style}_bg_{variant:02d}.png"
    out_path = str(Path(output_dir) / filename)

    return generate_background_image(
        style=style,
        output_path=out_path,
        seed_variant=variant,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="AI Image Generator v7.0 — Cyberpunk Edgerunners")
    parser.add_argument("--style", default="phonk",
                        choices=list(GENRE_STYLE_SUFFIX.keys()))
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--variant", type=int, default=0)
    parser.add_argument("--batch", action="store_true",
                        help="Gera batch de backgrounds para todos os estilos")
    args = parser.parse_args()

    if args.batch:
        results = generate_background_batch(
            styles=list(GENRE_STYLE_SUFFIX.keys()),
            output_dir="assets/backgrounds",
        )
        for style, paths in results.items():
            print(f"{style}: {len(paths)} backgrounds gerados")
    else:
        path = generate_background_image(
            style=args.style,
            output_path=args.output,
            seed_variant=args.variant,
        )
        if path:
            print(f"✅ Salvo: {path}")
        else:
            print("✗ Falha na geração.")
