"""
ai_image_generator.py — DJ DARK MARK v25 ULTRA VIRAL ENGINE
=============================================================
Versão profissional unificada (V18→V24 best-of merge).

Objetivo visual:
- Anime 2D premium, dark cyberpunk, phonk / trap / electronic / dark pop.
- Garota adulta com vibe trapstar/dark queen — sempre bonita, sempre viral.
- Composição pensada para CTR alto em YouTube Shorts e TikTok.
- Paleta controlada: magenta + violeta + preto (sem poluição de cor).
- Expressão emocional forte: olhar direto na câmera, impacto em 0.5s.
- Sem texto, sem logo, sem watermark.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("ai_image_generator")


# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    "width":               int(os.getenv("FLUX_WIDTH",    "832")),
    "height":              int(os.getenv("FLUX_HEIGHT",   "1216")),
    "num_inference_steps": int(os.getenv("FLUX_STEPS",    "30")),
    "guidance_scale":      float(os.getenv("FLUX_GUIDANCE", "7.0")),
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# IDENTIDADE DO CANAL
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ darkMark visual identity, dark anime edit, viral phonk cover art, "
    "YouTube Shorts music visualizer background, underground trap and electronic music aesthetic"
)


# ══════════════════════════════════════════════════════════════════════
# LOCKS PRINCIPAIS (V25 MERGED)
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman only, extremely beautiful anime girl, "
    "perfect symmetrical face, smooth soft skin, subtle blush, glossy lips, "
    "sharp eyeliner, ultra attractive face, hypnotic beauty, "
    "strong emotional presence, captivating personality, slightly crazy or mysterious vibe, "
    "clean modern trapstar streetwear aesthetic, choker, minimal chains, subtle jewelry, "
    "subtle face or neck or arm tattoos, nose or eyebrow or lip piercing, "
    "clean composition, visually striking, alone in frame, no crowd"
)

BODY_LOCK = (
    "medium full body or upper body portrait, character visible from head to thighs or knees, "
    "body centered, fills most of vertical frame, "
    "outfit and silhouette clearly visible, strong pose, "
    "not a face-only headshot, not cropped at neck, not tiny in background"
)

STYLE_LOCK = (
    "2D anime illustration only, premium anime key visual, sharp clean lineart, "
    "polished cel shading, soft smooth shading, high contrast but clean, "
    "dark cyberpunk anime aesthetic, viral phonk/trap cover art energy, "
    "dark background, neon magenta and violet rim light only, "
    "cinematic lighting, soft controlled glow, not overexposed, "
    "not realistic, not 3D, not noisy, not messy"
)

RETENTION_LOCK = (
    "extreme scroll-stopping composition, strong center focal point, "
    "face dominant, takes 50 to 65 percent of frame, "
    "eyes positioned slightly above center for mobile framing, "
    "tight cinematic portrait, perfect for vertical 9:16 YouTube Shorts and TikTok, "
    "instant readability in under 1 second, "
    "space near bottom for waveform and DJ logo overlay"
)

LIGHTING_LOCK = (
    "cinematic high-contrast lighting, "
    "strong warm light from one side (orange or red), "
    "cool neon magenta or violet from opposite side, "
    "face clearly lit and glowing, eyes highlighted, "
    "soft bloom — no overexposure, background darker than subject"
)

COLOR_LOCK = (
    "dominant neon magenta and violet tones, "
    "secondary warm orange or red highlights, "
    "clean controlled palette, no color pollution, "
    "no green dominance, no yellow, no cyan overload, no mixed tones"
)

SKIN_LOCK = (
    "natural anime skin tone, pale or light warm skin, "
    "smooth shading, soft blush, clean readable face, "
    "no blue skin, no green skin, no purple skin, no overexposed cyan face"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra clean anime illustration, "
    "sharp lineart, clean anatomy, beautiful detailed face, "
    "high resolution look, cinematic shadows, "
    "looks like viral anime thumbnail with high click-through rate"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT DEFINITIVO
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # qualidade
    "ugly, bad face, distorted face, bad anatomy, bad hands, extra fingers, "
    "missing fingers, extra arms, extra legs, fused limbs, long neck, tiny head, "
    "lazy eye, crossed eyes, asymmetrical eyes, distorted mouth, melted face, uncanny, "
    "blurry, low quality, noise, grain, jpeg artifacts, low resolution, muddy colors, "
    # pele / cor
    "blue skin, green skin, purple skin, gray skin, cyan skin, neon skin, "
    "overexposed cyan face, fully blue face, unnatural skin tone, "
    "color pollution, mixed color chaos, green dominance, yellow dominance, "
    # realismo / 3D
    "photorealistic, realistic, photography, real person, 3D, CGI, "
    "doll, plastic skin, lifeless eyes, "
    # idades / personagens proibidos
    "child, teen, underage, loli, chibi, schoolgirl, baby face, mascot, "
    # nsfw
    "nsfw, nude, explicit, cleavage focus, fetish, overly revealing outfit, "
    # outros personagens
    "multiple people, crowd, duplicate character, two girls, "
    # texto / logo
    "text, letters, words, captions, logo, watermark, signature, username, UI, numbers, "
    # excesso de glow
    "overexposed, too much glow, messy colors, heavy glow everywhere, "
    "toxic neon overload, 5 colors at once, "
    # composição ruim
    "face only, headshot only, portrait only, cropped body, missing legs, missing torso, "
    "small character, character too far, empty background without character, "
    # estilo indesejado
    "low quality, flat lighting, generic AI art, boring composition, clutter, bad crop"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES (ANTI-GENÉRICO)
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "black hair with subtle neon purple highlights, clean strands",
    "dark hair with pink neon reflections, glossy shine",
    "black and violet gradient hair, detailed shading",
    "dark hair softly lit by neon magenta light",
    "long black hair with red neon streaks, wet bangs",
    "electric blue-black hair with twin tails, cyan rim accent",
    "black hair under oversized hood, colored strands visible",
    "dark red and black ombre hair, wet shine, crimson backlight",
    "short black bob with deep violet tones, clean silhouette",
    "white silver hair with black tips, sharp bangs, magenta glow",
]

EYE_VARIATIONS = [
    "bright glowing magenta eyes with strong reflections",
    "deep violet eyes, glossy and detailed",
    "soft glowing pink eyes with light sparkle",
    "intense purple eyes with cinematic rim reflection",
    "glowing red eyes, cold hypnotic stare",
    "cyan and pink heterochromia, electric gaze",
    "toxic green glowing eyes, dangerous smirk",
]

EXPRESSION_VARIATIONS = [
    "slightly crazy beautiful smile, hypnotic glowing eyes",
    "seductive smirk, confident and calm, direct gaze",
    "cold dominant stare, emotionless but powerful",
    "intense mysterious stare, slightly parted lips",
    "playful psycho smile, charming but dangerous",
    "soft emotional look, deep connection with viewer",
    "furious controlled rage, sharp stare",
    "evil confident smirk, trap queen energy",
]

POSE_VARIATIONS = [
    "leaning slightly forward toward viewer, intense direct eye contact",
    "hand near lips, teasing expression, eyes locked on viewer",
    "head tilted slightly, eyes glowing, soft smile",
    "looking over shoulder, direct eye contact, tattoos visible",
    "arms crossed, chin down, dominant boss pose",
    "one hand touching hair, relaxed but confident",
    "standing confidently, full outfit visible, strong silhouette",
    "low angle full body, looking down at viewer",
    "walking toward viewer, chains swinging",
    "close framing, face dominant, soft body angle",
]

OUTFIT_VARIATIONS = [
    "black oversized hoodie, chains, choker, minimal streetwear",
    "dark techwear outfit, straps, belts, chains, stylish",
    "black cropped jacket, gothic streetwear, choker",
    "dark leather jacket, choker, chain belt, black pants",
    "black cyberpunk vest, cargo pants, fingerless gloves",
    "hooded black coat, neon seams, chains around waist",
    "black and violet trap outfit, layered belts, arm sleeves",
    "oversized black hoodie, tactical belt, chunky boots",
]

SCENE_VARIATIONS = [
    "dark neon alley, wet ground reflections, violet smoke, blurred bokeh",
    "cyberpunk city rooftop at midnight, soft electric aura behind",
    "underground club entrance, magenta and red neon lights",
    "dark background with controlled neon glow — clean and minimal",
    "abandoned subway tunnel, violet lights, bass shockwave rings",
    "night drive street, red taillight streaks, wet asphalt reflection",
    "dark studio with laser lights, smoky trap atmosphere",
    "futuristic nightclub, cyan magenta rim, heavy shadows",
]

AURA_VARIATIONS = [
    "subtle purple lightning aura around her silhouette",
    "soft red neon smoke wrapping around her arms",
    "hot pink glitch particles behind her",
    "cyan and violet electric mist rising from the floor",
    "bass shockwave rings expanding around her",
    "crimson flame-like neon aura, subtle",
    "dark ink shadows with magenta sparks",
]

ART_STYLE_VARIATIONS = [
    "premium anime key visual, sharp lineart, glossy cel shading",
    "viral anime music cover art, polished cinematic lighting",
    "cyberpunk anime poster, clean silhouette, high contrast",
    "phonk anime edit style, beautiful face, detailed streetwear",
    "dark manga cover energy, neon glow, strong composition",
]


# ══════════════════════════════════════════════════════════════════════
# MAPEAMENTO DE GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_MAP = {
    "phonk":      "phonk",
    "trap":       "trap",
    "dark":       "dark",
    "darkpop":    "dark",
    "dark pop":   "dark",
    "electronic": "electronic",
    "edm":        "electronic",
    "dubstep":    "electronic",
    "funk":       "trap",
    "rock":       "dark",
    "metal":      "dark",
    "cinematic":  "dark",
    "lofi":       "dark",
    "indie":      "dark",
    "pop":        "default",
}

GENRE_PALETTES = {
    "phonk": [
        "black, hot magenta dominant, deep violet shadows",
        "black, crimson, purple lightning aura",
        "black, magenta neon, dark red smoke",
    ],
    "trap": [
        "black, pink neon dominant, icy violet rim light",
        "black, red neon, magenta glow, gold jewelry accent",
        "black, violet, magenta street glow, clean palette",
    ],
    "electronic": [
        "black, magenta laser light, violet digital particles",
        "deep blue-black, neon pink dominant, violet glow",
        "black, teal accent, electric purple, clean club lighting",
    ],
    "dark": [
        "near black, red eyes, violet aura, minimal glow",
        "black, gray deep shadows, blood red neon accent",
        "black, purple smoke, white hair highlights, cold tone",
    ],
    "default": [
        "black, violet and magenta dominant, warm red secondary",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3800) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip() or "dark trap phonk"


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v25_ultra_viral"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["bass", "808", "drop"]):
        return "visible bass shockwave rings on the wet floor"
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada"]):
        return "midnight shadow aura, subtle red neon smoke"
    if any(w in clean for w in ["rage", "fire", "burn"]):
        return "crimson neon flame aura, aggressive energy"
    if any(w in clean for w in ["drive", "drift", "car", "speed"]):
        return "night drive reflections, blurred car lights in background"
    if any(w in clean for w in ["blue", "cyber", "electric", "digital"]):
        return "cyan electronic glow, digital particles subtle"
    return "music energy as subtle neon aura around character"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str,
    filename: str,
    styles: list | None = None,
    short_num: int = 1,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng    = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    hair        = rng.choice(HAIR_VARIATIONS)
    eyes        = rng.choice(EYE_VARIATIONS)
    expression  = rng.choice(EXPRESSION_VARIATIONS)
    pose        = rng.choice(POSE_VARIATIONS)
    outfit      = rng.choice(OUTFIT_VARIATIONS)
    scene       = rng.choice(SCENE_VARIATIONS)
    aura        = rng.choice(AURA_VARIATIONS)
    art         = rng.choice(ART_STYLE_VARIATIONS)
    palette     = rng.choice(GENRE_PALETTES.get(mapped, GENRE_PALETTES["default"]))
    detail      = _song_detail(song_name)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])

    prompt = (
        f"{TRAPSTAR_DNA}, "
        f"{BODY_LOCK}, "
        f"{STYLE_LOCK}, "
        f"{RETENTION_LOCK}, "
        f"{LIGHTING_LOCK}, "
        f"{COLOR_LOCK}, "
        f"{SKIN_LOCK}, "
        f"{QUALITY_LOCK}, "

        # variações dinâmicas
        f"{hair}, "
        f"{eyes}, "
        f"expression: {expression}, "
        f"pose: {pose}, "
        f"outfit: {outfit}, "
        f"scene: {scene}, "
        f"aura: {aura}, "
        f"{detail}, "

        # contexto musical
        f"palette: {palette}, "
        f"genre mood: {genre_text}, "
        f"song mood: {song_name}, "
        f"{art}, "

        # regras críticas finais
        "CRITICAL: must be extremely attractive, scroll-stopping, visually clean, "
        "must look like viral anime thumbnail with high click-through rate, "
        "face must be the main focus and beautiful instantly, "
        "no text anywhere, no watermark, no logo, no letters, "
        "no messy glow, no color pollution, no overexposure, "
        "must look professional and viral, must create emotional reaction in first second"
    )

    return _compact(prompt, max_len=3600)


def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    """Atalho para gerar prompt sem arquivo real."""
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
    return prompt, NEGATIVE_PROMPT


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE)
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # reforça o estilo na hora da geração
    full_prompt = _compact(
        prompt
        + ", 2D anime only, premium dark trapstar anime girl, beautiful face, "
        + "clean anatomy, natural anime skin tone, neon only as rim light and eye glow, "
        + "no text, no logo, no watermark, viral YouTube Shorts thumbnail"
    )

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model}")

                payload = {
                    "input": {
                        **FLUX_PARAMS,
                        "prompt":          full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed":            random.randint(1000, 999_999),
                    }
                }

                create_url = f"https://api.replicate.com/v1/models/{model}/predictions"
                resp = requests.post(create_url, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                for _ in range(120):
                    time.sleep(2)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data   = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output    = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")

                        img = requests.get(image_url, timeout=90)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)
                        logger.info(f"[Replicate] Salvo: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error") or "Replicate falhou.")

                raise TimeoutError("Replicate demorou demais.")

            except Exception as e:
                last_error = e
                logger.warning(f"[Replicate] Falhou tentativa {attempt}: {e}")
                time.sleep(3 * attempt)

    logger.error(f"[Replicate] Todas as tentativas falharam: {last_error}")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONVENIÊNCIA
# ══════════════════════════════════════════════════════════════════════

def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
) -> Optional[str]:
    prompt, _ = build_prompt(style=style, seed_variant=seed_variant)
    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        logger.warning(f"Tentativa background {attempt}/{max_retries} falhou.")
        time.sleep(3 * attempt)
    return None


def get_or_generate_background(
    style: str = "phonk",
    output_dir: str = "assets/backgrounds",
    force_new: bool = False,
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))

    if existing and not force_new:
        chosen = random.choice(existing)
        logger.info(f"Background reutilizado: {chosen}")
        return str(chosen)

    variant     = random.randint(0, 99)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:02d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list[str],
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 2,
) -> dict[str, list[str]]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {}

    for style in styles:
        results[style] = []
        for v in range(variants_per_style):
            output_path = str(Path(output_dir) / f"{style}_bg_{v:02d}.png")
            if os.path.exists(output_path):
                results[style].append(output_path)
                continue
            path = generate_background_image(style=style, output_path=output_path, seed_variant=v)
            if path:
                results[style].append(path)

    return results


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="AI Image Generator — DJ DARK MARK v25 Ultra Viral Engine"
    )
    parser.add_argument("--style",       default="phonk",
                        help="Gênero musical (phonk, trap, electronic, dark, etc.)")
    parser.add_argument("--filename",    default="dark phonk.mp3",
                        help="Nome da música (usado para variar o prompt)")
    parser.add_argument("--short-num",   type=int, default=1,
                        help="Número do short (varia seed)")
    parser.add_argument("--output",      default="assets/background.png")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
    )

    if args.prompt_only:
        print("=== PROMPT ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
    else:
        path = generate_image(prompt, args.output)
        print(f"✅ Salvo: {path}" if path else "✗ Falha na geração.")
