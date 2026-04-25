"""
ai_image_generator.py — DJ DARK MARK v14 FINAL VIBRANT BEAUTY LOCK
============================================================
Merge v14 (prompts virais) + v7 (estrutura segura GitHub Actions).

FINALIDADE:
- Gerar imagens mais parecidas com referências virais de anime dark/phonk.
- Menos imagem genérica de IA, menos 3D, menos realismo.
- Mais: anime edit, olhos brilhando, sombra pesada, neon roxo/rosa/vermelho,
  composição forte para Shorts, rosto/olhos impactantes e variações boas.
- Compatível com o pipeline antigo: build_ai_prompt(...) e generate_image(...).
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
    "width": 1080,
    "height": 1920,
    "num_inference_steps": int(os.getenv("FLUX_STEPS", "38")),
    "guidance_scale": float(os.getenv("FLUX_GUIDANCE", "7.2")),
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# IDENTIDADE VISUAL
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ darkMark visual identity, dark anime edit, viral phonk cover art, "
    "YouTube Shorts music visualizer background, high-retention anime thumbnail"
)

CHARACTER_DNA = (
    "one adult anime girl only, beautiful dark gothic cyberpunk anime girl, "
    "pretty face, clean face, soft blush, natural anime skin tone, "
    "large glowing hypnotic eyes, glossy pupils, sharp anime eyes, readable face, "
    "varied expression: sometimes cute, sometimes evil, sometimes crazy, sometimes calm, "
    "tiny fang smile optional, mischievous smile optional, mysterious stare optional, "
    "black hair, white hair, dark purple hair or cyan-tipped hair, messy bangs, twin tails or long flowing hair, "
    "small demon horns, cat ears, cat-ear hoodie, gothic bow or hair clips optional, "
    "black techwear, gothic streetwear, oversized black hoodie, glossy black jacket, choker, subtle chains, "
    "platform-safe outfit, no nudity, no explicit outfit, alone in frame, no crowd, "
    "strong silhouette, centered character, face and eyes are the main hook"
)

ANIME_STYLE_DNA = (
    "2D anime illustration only, dark anime edit style, viral phonk anime cover art, "
    "anime pfp aesthetic, manga cover energy, sharp manga lineart, crisp cel shading, "
    "beautiful vibrant neon lighting, deep black shadows, high contrast ink shadows, "
    "glowing neon eyes, luminous aura, hot magenta neon, violet glow, red eye glow, "
    "toxic green glow sometimes, cyan rim light only, bright but tasteful light effects, "
    "not overexposed, not messy, not realistic, not 3D"
)

RETENTION_DNA = (
    "scroll stopping first frame, strong centered focal point, face and eyes readable on phone screen, "
    "simple powerful composition, high contrast, not cluttered, memorable silhouette, "
    "dark background with one dominant neon glow, space near lower center for audio waveform or DJ logo, "
    "viral anime pfp aesthetic, album cover aesthetic, music visualizer background"
)

# SKIN LOCK: neon é LUZ, não cor base da pele.
SKIN_LIGHTING_LOCK = (
    "natural anime skin tone preserved, pale skin or soft warm anime skin, "
    "skin is not blue, face is not fully cyan, no full blue face, no blue body, "
    "neon colors appear only as rim light, reflected highlights and eye glow, "
    "soft blush visible, natural face shading, beautiful readable face, "
    "dark shadows with magenta and violet glow, cinematic anime lighting"
)

QUALITY_TAGS = (
    "masterpiece, best quality, high-end anime key visual, polished anime illustration, "
    "ultra sharp lineart, clean anatomy, refined face, glossy detailed eyes, cinematic lighting, "
    "deep blacks, luminous neon highlights, vibrant magenta, violet, red and cyan lighting, "
    "beautiful anime girl, dark aesthetic, phonk aesthetic, 9:16 vertical"
)

NEGATIVE_PROMPT = (
    "photorealistic, realistic, photography, real person, 3d render, CGI, doll, plastic skin, "
    "child, teen, childish body, loli, schoolgirl, chibi, mascot, baby face, "
    "nsfw, nude, explicit, lingerie, fetish, cleavage focus, overly revealing outfit, "
    "ugly, creepy, horror monster, gore, blood splatter, deformed face, bad anatomy, bad hands, "
    "extra fingers, missing fingers, extra arms, extra legs, fused limbs, long neck, tiny head, "
    "asymmetrical eyes, lazy eye, crossed eyes, distorted mouth, melted face, uncanny, "
    "multiple people, crowd, duplicate character, text, letters, watermark, logo, signature, username, UI, "
    "low quality, blurry, low resolution, muddy, washed out, dull colors, flat lighting, plain background, "
    "generic AI art, generic purple gradient, boring composition, messy clutter, bad crop, "
    "yellow dominant, orange sunset dominant, brown dominant, daylight, sunny, photobash, "
    "blue skin, cyan skin, fully blue face, blue face, blue body, avatar skin, smurf skin, "
    "neon skin, skin completely tinted blue, overexposed cyan face, plastic blue shading, "
    "flat blue lighting, monochrome blue character, ugly blue color cast, oversaturated blue face, "
    "overexposed neon, messy lights, random scenery, empty city without character, "
    "ugly AI face, bad crop, far away character, full body too small"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES VISUAIS
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair with heavy bangs and red neon eye glow",
    "black twin tails with hot pink and cyan highlights",
    "white hair with black underlayer and glowing magenta eyes",
    "messy black bob haircut, gothic bow accessory, red eyes",
    "long blue hair in electric purple smoke, glowing cyan rim light",
    "dark purple hair, wet strands, violet neon reflections",
    "short black hair under oversized cat-ear hoodie, glowing eyes",
    "long black hair flowing in rain, crimson rim light",
]

EYE_VARIATIONS = [
    "glowing red eyes, intense hypnotic stare",
    "glowing violet eyes with glossy anime reflections",
    "bright magenta eyes, cute dangerous smile",
    "toxic green glowing eyes with supernatural flame aura",
    "cyan and pink heterochromia, cyberpunk iris glow",
]

OUTFIT_VARIATIONS = [
    "oversized black hoodie with cat-ear hood, neon rim light",
    "black gothic techwear jacket with choker and subtle chains",
    "dark cyberpunk jacket with glossy wet leather reflections",
    "black streetwear outfit with purple glowing seams",
    "gothic anime outfit with platform-safe top, collar and silver accessories",
    "hooded shadow cloak with neon inner glow, cute dark anime style",
]

POSE_VARIATIONS = [
    "close-up portrait, eyes dominating the frame, slight fang smile",
    "medium portrait, looking directly at viewer, calm dangerous expression",
    "sitting in a dark neon room holding a phone, lonely midnight vibe",
    "standing in rain with neon city bokeh behind, hair moving in wind",
    "hood up, face half hidden in shadow, glowing eyes visible",
    "three-quarter portrait, one hand near face, cute gothic expression",
    "centered album-cover pose, shoulders visible, dark aura surrounding her",
]

CAMERA_VARIATIONS = [
    "tight close-up portrait, face and eyes readable on phone screen",
    "medium close-up, chest to crown framing, centered composition",
    "album cover composition, character centered with strong neon aura",
    "low angle cinematic portrait, dramatic rim light",
    "soft close-up with shallow depth of field and neon bokeh",
]

ART_STYLES = [
    "dark anime edit style, sharp manga lines, glowing eyes, high contrast black shadows",
    "viral phonk album cover art, anime girl portrait, neon aura, clean silhouette",
    "polished anime key visual, premium cel shading, hot pink and violet neon glow",
    "gothic cyberpunk anime illustration, halftone manga texture, red eye glow",
    "cute dark anime pfp aesthetic, clean face, luminous eyes, deep black background",
]

AURA_VARIATIONS = [
    "purple lightning aura wrapping around her silhouette",
    "red neon eye bloom and black smoke tendrils around the frame",
    "toxic green flame aura shaped like cat ears behind her",
    "hot pink glitch branches and electric particles around her",
    "cyan rain reflections and magenta neon haze behind her",
    "black ink shadows with violet sparks floating in the air",
]

EXPRESSION_VARIATIONS = [
    "cute mischievous fang smile, playful but dark",
    "evil confident smile, villain anime girl energy",
    "crazy hypnotic stare, slightly unhinged anime smile, glowing eyes",
    "calm mysterious expression, beautiful and dangerous",
    "soft cute face with dangerous neon eyes",
    "smirking gothic girl, chaotic phonk energy",
    "serious cold stare, premium anime cover mood",
]

REFERENCE_STYLE_LOCKS = [
    "close-up viral dark anime phonk profile picture style",
    "gothic anime girl edit with purple neon horns and black shadows",
    "hot pink demon girl anime edit, cute fang smile, cyan highlights",
    "toxic green cat aura anime edit with glowing green eyes",
    "purple lightning anime girl, dark face, glowing magenta eyes",
    "black and pink anime edit with branches, glow, and heavy shadows",
]


# ══════════════════════════════════════════════════════════════════════
# CONCEITOS VISUAIS POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

VISUAL_CONCEPTS = {
    "phonk": [
        {
            "label": "PHONK_PURPLE_HORNS",
            "scene": (
                "{character}, tight close-up portrait, small glowing purple horns, black hair with bangs, "
                "dark alley wall, violet eyes, glossy neon highlights, {aura}, {reference_lock}"
            ),
            "palette": "deep black, violet neon, hot magenta, tiny cyan rim light",
        },
        {
            "label": "PHONK_PINK_DEMON_CUTE",
            "scene": (
                "{character}, cute demon anime girl, tiny fang smile, hot pink glow behind her, "
                "cyan hair highlights, black jacket, playful evil expression, anime pfp cover art, {aura}, {reference_lock}"
            ),
            "palette": "hot pink, cyan highlights, black outfit, violet eyes",
        },
        {
            "label": "PHONK_GREEN_CAT_AURA",
            "scene": (
                "{character}, cat ears or cat-ear hoodie, toxic green flame aura behind her, "
                "glowing green eyes, centered dark anime portrait, black background, {aura}, {reference_lock}"
            ),
            "palette": "black, toxic green, white glow, tiny violet shadows",
        },
        {
            "label": "PHONK_PURPLE_LIGHTNING",
            "scene": (
                "{character}, dark face in shadow, glowing magenta eyes, purple lightning aura around her, "
                "album cover portrait, hypnotic phonk energy, {aura}, {reference_lock}"
            ),
            "palette": "near black, neon purple, magenta eye glow, cyan edge light",
        },
    ],
    "trap": [
        {
            "label": "TRAP_GLITCH_GIRL",
            "scene": (
                "{character}, close-up anime portrait, hot pink glitch branches, black streetwear, "
                "confident trap cover art look, neon city blur behind, {aura}, {reference_lock}"
            ),
            "palette": "black, hot pink, violet, cyan shine",
        },
        {
            "label": "TRAP_BLUE_PURPLE_AURA",
            "scene": (
                "{character}, blue or black hair with purple smoke, glowing magenta eyes, dark outfit, "
                "centered album cover pose, vibrant cyber trap aesthetic, {aura}, {reference_lock}"
            ),
            "palette": "deep black, electric purple, cyan hair glow, magenta eyes",
        },
        {
            "label": "TRAP_LUXURY_DARK",
            "scene": (
                "{character}, glossy black jacket, neon city bokeh, calm boss energy, "
                "magenta eyes, clean dark anime edit, {aura}, {reference_lock}"
            ),
            "palette": "black, violet, cyan, magenta shine",
        },
    ],
    "dark": [
        {
            "label": "DARK_RED_EYES_MANGA",
            "scene": (
                "{character}, extreme dark manga portrait, black hair framing the face, "
                "glowing red eyes, grayscale shadow shading, hypnotic face, minimal background, {aura}, {reference_lock}"
            ),
            "palette": "black and gray, red eyes, faint violet edge light",
        },
        {
            "label": "DARK_HOOD_GIRL",
            "scene": (
                "{character}, hood up, face half hidden in shadow, glowing eyes under hood, "
                "rainy alley, blue neon columns behind, mysterious anime edit, {aura}, {reference_lock}"
            ),
            "palette": "black hood, blue neon, magenta face glow",
        },
        {
            "label": "DARK_PURPLE_BRANCHES",
            "scene": (
                "{character}, black branches crossing foreground, hot pink backlight, "
                "glowing purple eyes, beautiful evil anime girl, {aura}, {reference_lock}"
            ),
            "palette": "black, hot pink, violet, tiny cyan rim",
        },
    ],
    "electronic": [
        {
            "label": "ELECTRONIC_NEON_CRAZY",
            "scene": (
                "{character}, crazy cute anime expression, glowing magenta eyes, digital particles, "
                "purple and cyan neon burst, clean pfp composition, {aura}, {reference_lock}"
            ),
            "palette": "purple, magenta, cyan, black",
        },
        {
            "label": "ELECTRONIC_LASER_EYES",
            "scene": (
                "{character}, horizontal neon laser reflection across glowing eyes, rain and holograms, "
                "clean anime cyberpunk portrait, {aura}, {reference_lock}"
            ),
            "palette": "red laser, cyan rain, purple haze",
        },
    ],
    "lofi": [
        {
            "label": "LOFI_MIDNIGHT_PHONE",
            "scene": (
                "{character}, sitting alone in dark neon room holding phone, soft sad cute expression, "
                "rain outside window, purple shadows, {aura}, {reference_lock}"
            ),
            "palette": "black room, soft cyan rain, violet glow, warm small lamp",
        },
        {
            "label": "LOFI_SOFT_GOTH",
            "scene": (
                "{character}, soft cute gothic anime portrait, sleepy glowing eyes, quiet midnight vibe, "
                "deep shadows, gentle magenta aura, {aura}, {reference_lock}"
            ),
            "palette": "black, violet, soft pink, cold blue edge",
        },
    ],
    "default": [
        {
            "label": "DEFAULT_DARK_ANIME",
            "scene": (
                "{character}, {camera}, {pose}, dark anime cyberpunk portrait, glowing eyes, "
                "neon bokeh background, high contrast, {aura}, {reference_lock}"
            ),
            "palette": "black, purple, magenta, cyan, red glow",
        },
        {
            "label": "DEFAULT_GREEN_AURA",
            "scene": (
                "{character}, toxic green flame aura behind her shaped like cat ears, black outfit, "
                "glowing green eyes, cute dark anime expression, viral pfp cover art, {aura}, {reference_lock}"
            ),
            "palette": "black, toxic green, white highlights, tiny violet shadows",
        },
    ],
}

GENRE_MAP = {
    "phonk": "phonk",
    "trap": "trap",
    "dark": "dark",
    "electronic": "electronic",
    "dubstep": "electronic",
    "edm": "electronic",
    "lofi": "lofi",
    "indie": "lofi",
    "rock": "dark",
    "metal": "dark",
    "cinematic": "dark",
    "funk": "trap",
    "pop": "default",
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3900) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|darkmark_v14_final_vibrant_beauty_lock"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _rng(filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(filename, short_num))


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "dark phonk"


def _pick_concept(style: str, filename: str, short_num: int) -> dict:
    mapped = GENRE_MAP.get(style, style)
    concepts = VISUAL_CONCEPTS.get(mapped, VISUAL_CONCEPTS["default"])
    rng = _rng(filename, short_num)
    return concepts[rng.randrange(len(concepts))]


def _pick_style_parts(filename: str, short_num: int) -> dict:
    rng = _rng(filename, short_num)
    return {
        "hair": rng.choice(HAIR_VARIATIONS),
        "eyes": rng.choice(EYE_VARIATIONS),
        "outfit": rng.choice(OUTFIT_VARIATIONS),
        "pose": rng.choice(POSE_VARIATIONS),
        "camera": rng.choice(CAMERA_VARIATIONS),
        "art": rng.choice(ART_STYLES),
        "aura": rng.choice(AURA_VARIATIONS),
        "expression": rng.choice(EXPRESSION_VARIATIONS),
        "reference_lock": rng.choice(REFERENCE_STYLE_LOCKS),
    }


def _build_character(parts: dict) -> str:
    return (
        f"{CHARACTER_DNA}, {parts['hair']}, {parts['eyes']}, "
        f"{parts['outfit']}, {parts['expression']}"
    )


def _song_micro_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["car", "drive", "drift", "night", "road", "truck"]):
        return "subtle night drive detail, red taillight streaks and wet road reflections"
    if any(w in clean for w in ["ghost", "phantom", "shadow", "dark", "madrugada"]):
        return "ghostly shadow aura, midnight darkness and glowing eyes"
    if any(w in clean for w in ["rain", "cry", "sad", "alone"]):
        return "lonely rain mood, window reflections and soft melancholic neon"
    if any(w in clean for w in ["fire", "burn", "rage"]):
        return "crimson sparks, heat haze and aggressive red neon aura"
    if any(w in clean for w in ["bass", "drop", "808"]):
        return "visible bass shockwave rings and vibrating neon particles"
    return "one strong memorable visual detail connected to the song title"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list | None = None, short_num: int = 1) -> str:
    """
    Gera prompt v14 DARKMARK FINAL VIBRANT BEAUTY LOCK.
    Foco: parecer anime edit/phonk cover viral, não imagem genérica de IA.
    """
    styles = styles or []
    song_name = _clean_song_name(filename)

    concept = _pick_concept(style, filename, short_num)
    parts = _pick_style_parts(filename, short_num)
    character = _build_character(parts)
    song_detail = _song_micro_detail(song_name)
    all_styles = ", ".join([style] + [s for s in styles if s and s != style])

    scene = concept["scene"].format(
        character=character,
        camera=parts["camera"],
        pose=parts["pose"],
        aura=parts["aura"],
        reference_lock=parts["reference_lock"],
    )

    prompt = (
        f"{scene}, "
        f"song title mood: '{song_name}', {song_detail}, genre mood: {all_styles}, "
        f"palette: {concept.get('palette', 'deep black, neon purple, hot magenta, cyan, red glow')}, "
        f"{parts['art']}, "
        f"{CHANNEL_IDENTITY}, {ANIME_STYLE_DNA}, {RETENTION_DNA}, {SKIN_LIGHTING_LOCK}, {QUALITY_TAGS}, "
        "vibrant but tasteful neon, bright clean light effects on hair and eyes, beautiful polished lighting, "
        "sometimes cute, sometimes evil, sometimes crazy, sometimes calm, but always pretty and on-brand, "
        "phone-screen readable, eyes are the main hook, strong face focal point, "
        "clean 9:16 vertical composition, background dark enough for waveform and logo overlay, "
        "no text, no watermark, no logo, no letters, no photorealism, no 3d, no blue skin, no fully blue face"
    )

    return _compact(prompt, max_len=3600)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    """
    Gera imagem via Replicate (flux-dev).
    Compatível com o fluxo antigo do main.py.
    """
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    if output_path is None:
        output_path = "temp/generated_background.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Reforço final para o Flux não fugir para realismo/3D.
    full_prompt = _compact(
        prompt
        + ", 2D anime only, dark anime edit, viral phonk anime cover, glowing eyes, "
        + "manga shadows, sharp lineart, cel shading, high contrast, deep black background, "
        + "natural anime skin tone preserved, face not tinted blue, neon only as rim light and eye glow, "
        + "hot magenta violet cyan red neon, toxic green aura sometimes, beautiful gothic cyberpunk anime girl, "
        + "close-up or medium close-up, eyes dominate the image, vibrant beautiful light effects, "
        + "cute/evil/crazy/calm expression variety, polished not messy, "
        + "must look like viral dark anime phonk edit references, not generic AI art, "
        + "not realistic, not 3d, not photo, clean face, phone wallpaper quality, high retention"
    )

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"  [Replicate] Tentativa {attempt}/3 — {model}")

                payload = {
                    "input": {
                        **FLUX_PARAMS,
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed": random.randint(1000, 999999),
                    }
                }

                create_url = f"https://api.replicate.com/v1/models/{model}/predictions"
                resp = requests.post(create_url, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                pred = resp.json()

                poll_url = pred.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{pred['id']}"

                for _ in range(120):
                    time.sleep(2)
                    status_resp = requests.get(poll_url, headers=headers, timeout=30)
                    status_resp.raise_for_status()
                    data = status_resp.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output

                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")

                        img = requests.get(image_url, timeout=90)
                        img.raise_for_status()

                        with open(output_path, "wb") as f:
                            f.write(img.content)

                        logger.info(f"  [Replicate] Salvo: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error") or "Replicate falhou.")

                raise TimeoutError("Replicate demorou demais para gerar imagem.")

            except Exception as e:
                last_error = e
                logger.warning(f"  [Replicate] Falhou: {e}")
                time.sleep(3 * attempt)

    logger.error(f"  [Replicate] Todas as tentativas falharam: {last_error}")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES EXTRAS — compatibilidade com partes antigas do bot
# ══════════════════════════════════════════════════════════════════════

def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(style=style, filename=fake_filename, styles=[style], short_num=seed_variant + 1)
    return prompt, NEGATIVE_PROMPT


def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
) -> Optional[str]:
    prompt, _negative = build_prompt(style=style, seed_variant=seed_variant)
    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        logger.warning(f"  ⚠ Tentativa background {attempt}/{max_retries} falhou.")
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
        logger.info(f"  ► Background reutilizado: {chosen}")
        return str(chosen)
    variant = random.randint(0, 99)
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

    parser = argparse.ArgumentParser(description="AI Image Generator v14 — DarkMark Final Vibrant Beauty Lock")
    parser.add_argument("--style", default="phonk")
    parser.add_argument("--filename", default="dark phonk.mp3")
    parser.add_argument("--short-num", type=int, default=1)
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--prompt-only", action="store_true")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
    )

    if args.prompt_only:
        print(prompt)
    else:
        path = generate_image(prompt, args.output)
        if path:
            print(f"✅ Salvo: {path}")
        else:
            print("✗ Falha na geração.")
