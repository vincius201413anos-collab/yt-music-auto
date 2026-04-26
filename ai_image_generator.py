"""
ai_image_generator.py — DJ DARK MARK v26 FULL BODY ULTRA VIRAL ENGINE
=============================================================
CHANGELOG v26:
- HARD BAN azul/cyan em todo o sistema (paleta + negative prompt reforçado)
- BODY LOCK reescrito com linguagem mais agressiva para forçar corpo inteiro
- Novas poses focadas em corpo completo visível
- Paleta principal: magenta + violeta + vermelho + preto
- Referências visuais: dark queen cyberpunk, phonk cover art, trap girl
- Sem close-up de rosto. Sempre corpo inteiro ou 3/4.
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
    "num_inference_steps": int(os.getenv("FLUX_STEPS",    "35")),
    "guidance_scale":      float(os.getenv("FLUX_GUIDANCE", "7.5")),
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
# LOCKS PRINCIPAIS — V26 FULL BODY REWRITE
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman only, "
    "extremely beautiful and sensual anime girl, "
    "perfect symmetrical face, smooth flawless skin, glossy lips, sharp eyeliner, "
    "ultra attractive mature face, seductive and confident energy, "
    "strong dark queen presence, slightly dangerous mysterious vibe, "
    "modern trapstar streetwear aesthetic, choker, chain accessories, subtle jewelry, "
    "subtle tattoos on neck or arms, nose or lip piercing optional, "
    "alone in frame, no other characters"
)

# ══════════════════════════════════════════════════════════════════════
# BODY LOCK — O MAIS IMPORTANTE — V26 REFORÇADO
# ══════════════════════════════════════════════════════════════════════

BODY_LOCK = (
    "ABSOLUTE MANDATORY RULE: show FULL BODY from head to feet, "
    "complete body visible: head, neck, shoulders, chest, waist, hips, thighs, knees, legs, boots or feet, "
    "camera positioned FAR BACK — medium-long shot or long shot ONLY, "
    "character height fills 70 to 85 percent of the vertical frame, "
    "face is SMALL — face takes only 10 to 18 percent of total image height, "
    "body silhouette is the main visual element — outfit, chains, tattoos, legs clearly visible, "
    "vertical 9:16 full body composition like a premium anime poster, "
    "BANNED: portrait framing, headshot, bust shot, close-up, face dominant, cropped body, "
    "BANNED: face bigger than 20 percent of frame, BANNED: missing legs, BANNED: missing torso, "
    "BANNED: half body only, BANNED: waist cut, BANNED: shoulder crop"
)

STYLE_LOCK = (
    "2D anime illustration only, premium dark anime key visual, "
    "sharp clean black lineart, polished cel shading with smooth gradients, "
    "high contrast cinematic composition, "
    "dark cyberpunk anime aesthetic, phonk trap cover art energy, "
    "very dark background — nearly black, "
    "neon magenta and violet as the ONLY rim lights, "
    "warm red or orange as secondary accent, "
    "cinematic moody lighting, controlled atmospheric glow, "
    "NOT photorealistic, NOT 3D render, NOT noisy, NOT blurry"
)

PALETTE_HARD_LOCK = (
    "COLOR HARD LOCK — STRICTLY ENFORCED: "
    "dominant colors MUST BE: neon magenta, deep violet, hot pink, crimson red, "
    "secondary colors ALLOWED: warm orange, dark red, black, near-black, "
    "COMPLETELY BANNED COLORS: blue, cyan, teal, turquoise, aqua, green, yellow, "
    "NO BLUE ANYWHERE — not in background, not in hair, not in eyes, not in lighting, "
    "NO CYAN ANYWHERE — not as rim light, not as glow, not as aura, "
    "background must be dark near-black with only magenta or violet or red neon accents"
)

LIGHTING_LOCK = (
    "cinematic split lighting: "
    "primary light — warm orange or red from one side, strong and directional, "
    "secondary light — neon magenta or violet from opposite side as rim light, "
    "face clearly illuminated and glowing beautifully, "
    "eyes highlighted with matching neon color, "
    "soft bloom glow — not overexposed, background significantly darker than subject, "
    "BANNED: blue light, BANNED: cyan rim light, BANNED: teal glow, BANNED: cold white light"
)

SKIN_LOCK = (
    "anime skin tone: pale or light warm beige, "
    "smooth soft shading with subtle blush on cheeks, "
    "natural clean readable face under neon light, "
    "BANNED: blue skin tone, BANNED: cyan skin, BANNED: green skin, "
    "BANNED: purple skin, BANNED: overexposed white face"
)

RETENTION_LOCK = (
    "scroll-stopping viral composition for YouTube Shorts and TikTok 9:16, "
    "full body character dominates the vertical frame, "
    "strong center focal point — character perfectly centered or slightly off-center, "
    "instant impact readable in under 1 second, "
    "body pose and outfit silhouette create visual tension, "
    "space reserved near bottom of frame for waveform visualizer and DJ logo overlay, "
    "high click-through rate aesthetic, professional viral anime thumbnail energy"
)

QUALITY_LOCK = (
    "masterpiece quality, best anime illustration, ultra clean lineart, "
    "beautiful detailed anatomy, clean proportions, cinematic composition, "
    "professional dark anime poster quality, "
    "looks like top viral phonk anime YouTube thumbnail"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT — V26 AZUL/CYAN TOTALMENTE BANIDO
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # qualidade anatômica
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, lazy eye, "
    "bad hands, extra fingers, missing fingers, extra limbs, fused limbs, "
    "long neck, tiny head, melted face, uncanny valley, "
    "blurry, low quality, noise, grain, jpeg artifacts, muddy colors, washed out, "

    # AZUL E CYAN — COMPLETAMENTE BANIDO
    "blue, cyan, teal, turquoise, aqua, blue background, cyan glow, teal rim light, "
    "blue hair, cyan hair, teal hair, blue eyes, cyan eyes, teal eyes, "
    "blue lighting, cyan lighting, cold blue light, ice blue, electric blue, "
    "blue skin, cyan skin, blue tones, cyan tones, cold color palette, "
    "blue neon, cyan neon, teal neon, blue aura, cyan aura, "

    # outras cores indesejadas
    "green, yellow, orange dominant, color pollution, mixed color chaos, "
    "green skin, purple skin, gray skin, unnatural skin tone, "
    "overexposed face, white overexposed skin, neon skin, "

    # realismo
    "photorealistic, realistic, photography, real person, 3D render, CGI, "
    "doll, plastic skin, lifeless eyes, hyperrealistic, "

    # personagens proibidos
    "child, teen, underage, loli, chibi, schoolgirl, baby face, "

    # nsfw excessivo
    "nsfw explicit, nude, genitalia, explicit sexual content, "
    "fully exposed body, extreme nudity, "

    # outros personagens
    "multiple people, crowd, duplicate character, two girls, group, "

    # texto / logo
    "text, letters, words, captions, logo, watermark, signature, UI, numbers, "

    # COMPOSIÇÃO RUIM — CLOSE NO ROSTO BANIDO
    "face only, headshot, portrait close-up, extreme close-up, "
    "face filling frame, face dominant, huge face, zoomed face, "
    "only eyes, bust portrait, portrait framing, close framing, "
    "cropped chest, cropped shoulders, cropped arms, cropped waist, "
    "cropped body, missing legs, missing torso, missing lower body, "
    "half body, waist up only, shoulders up only, neck up, "
    "small character in frame, character too small, empty background, "

    # excesso de glow
    "overexposed, too much glow, messy colors, bloom everywhere, "
    "toxic neon overload, 5 colors simultaneously, color chaos, "

    # estilo indesejado
    "flat lighting, generic AI art, boring composition, clutter, "
    "low contrast, washed out colors, desaturated, dull"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — V26 PALETA CORRIGIDA (SEM AZUL)
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair with subtle neon violet reflections, smooth glossy strands",
    "dark hair with hot pink neon highlights, flowing and detailed",
    "black and deep violet gradient hair, beautifully shaded",
    "dark hair softly lit by neon magenta rim light from behind",
    "long black hair with crimson red streaks, dramatic and bold",
    "dark maroon-black hair with violet sheen, elegant and dark",
    "black hair under oversized dark hood, colored strands escaping",
    "dark red and black ombre hair, wet-look shine, warm backlight",
    "short sleek black bob with violet undertones, sharp clean silhouette",
    "white silver hair with black tips, sharp bangs, magenta rim glow",
    "long silver-white hair, glowing pink under neon light",
    "black twintails with hot pink ribbon accents, cyberpunk style",
]

EYE_VARIATIONS = [
    "bright glowing magenta eyes with intense reflections",
    "deep violet eyes, glossy and emotionally powerful",
    "glowing hot pink eyes with subtle sparkle",
    "intense red-violet eyes with cinematic rim reflection",
    "glowing crimson eyes, cold hypnotic dangerous stare",
    "deep purple glowing eyes, mysterious and captivating",
]

EXPRESSION_VARIATIONS = [
    "slightly crazy beautiful smile, hypnotic eyes staring directly at viewer",
    "seductive smirk, confident dark queen energy, direct gaze",
    "cold dominant stare, emotionless but powerfully attractive",
    "intense mysterious expression, slightly parted glossy lips",
    "playful psycho smile, charming but dangerously beautiful",
    "soft emotional gaze, deep soul connection with the viewer",
    "controlled rage expression, sharp cold stare, jaw set",
    "evil confident queen smirk, trap queen dark energy",
    "sultry half-lidded eyes, slow dangerous smile",
]

POSE_VARIATIONS = [
    "standing full body pose, head to boots visible, strong confident silhouette, arms at sides or one hand on hip",
    "full body standing, one hand touching dark choker, looking directly at viewer, legs visible to ankles",
    "walking toward camera, full body head to feet, chains swinging, dark outfit flowing",
    "low-angle full body shot looking slightly down at viewer, complete body from crown to boots visible",
    "leaning against dark neon wall, full body visible head to knees minimum, one leg bent confidently",
    "three-quarter body turn, facing viewer, full silhouette clear from head to thighs or lower",
    "arms crossed over chest, full upper body and legs visible, dominant boss energy pose",
    "one hand raised touching hair, body fully visible from head to ankles, relaxed sensual confidence",
    "standing in dark alley, complete trapstar outfit visible head to boots, strong vertical frame",
    "dynamic full body stance, weight on one hip, knees visible, neon rim light outlining full silhouette",
    "sitting on dark throne or ledge, full body or nearly full body visible, legs crossed, sultry",
    "back slightly turned, looking over shoulder at viewer, full body silhouette visible",
]

OUTFIT_VARIATIONS = [
    "black oversized hoodie half-zipped, chains, black choker, dark baggy pants, chunky boots",
    "dark techwear outfit — straps, tactical belts, arm sleeves, fingerless gloves, black boots",
    "black cropped leather jacket, gothic streetwear corset underneath, dark pants, choker",
    "dark leather jacket open, chain belt, black high-waisted pants, platform boots",
    "black cyberpunk vest with red details, cargo pants, fingerless gloves, dark boots",
    "hooded black longcoat with violet seam details, chains wrapped around waist, dark boots",
    "black and violet trap streetwear — layered belts, arm warmers, chunky black boots",
    "oversized black hoodie, tactical straps, dark shorts with thigh-high boots",
    "black bodysuit under sheer dark jacket, chains, choker, thigh-high boots",
    "dark goth dress with black corset overlay, chains, fishnet stockings, platform boots",
]

SCENE_VARIATIONS = [
    "dark neon alley at night, wet ground reflecting only magenta and violet neon signs",
    "cyberpunk city rooftop at midnight, deep violet atmospheric haze behind character",
    "underground club entrance, walls lit only by magenta and red neon, heavy shadows",
    "pure near-black background with controlled magenta and violet atmospheric glow — minimal and clean",
    "abandoned dark urban street, warm red traffic light glow, violet mist rising from ground",
    "dark music studio with crimson and violet laser light beams, smoky trap atmosphere",
    "crumbling dark building interior, vine of neon magenta light through cracks",
    "rooftop edge at night, blood moon partially visible, violet and red sky glow",
]

AURA_VARIATIONS = [
    "subtle violet electric aura tracing her full body silhouette",
    "soft crimson neon smoke wrapping around her arms and waist",
    "hot magenta glitch particles scattered around her body",
    "dark purple energy mist rising from the ground around her feet",
    "deep red flame-like neon aura, subtle and controlled, outlining her form",
    "black ink shadow tendrils with magenta sparks at the edges",
    "warm orange-red energy wisps surrounding her lower body",
]

ART_STYLE_VARIATIONS = [
    "premium dark anime key visual, ultra sharp lineart, polished cel shading with deep shadows",
    "viral dark anime music cover art, cinematic lighting, professional full body composition",
    "cyberpunk anime poster art, clean dramatic silhouette, high contrast magenta and black",
    "phonk trap anime edit style, beautiful sensual character, detailed dark streetwear",
    "dark manga cover energy, deep neon glow, powerful full body vertical composition",
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

# PALETAS SEM AZUL/CYAN — V26
GENRE_PALETTES = {
    "phonk": [
        "palette: black background, hot magenta dominant rim light, deep violet secondary shadow, warm red accent",
        "palette: near-black background, crimson red primary, deep purple secondary, magenta trim glow",
        "palette: dark background, neon magenta dominant, dark blood red accent, violet atmospheric haze",
    ],
    "trap": [
        "palette: black background, hot pink neon dominant, deep violet rim light, no blue allowed",
        "palette: near-black background, red neon primary, magenta glow secondary, gold jewelry accent warm",
        "palette: dark background, violet dominant, magenta street glow, warm dark red accent, clean palette",
    ],
    "electronic": [
        "palette: black background, neon magenta laser light dominant, violet digital atmosphere, no cyan or blue",
        "palette: deep black background, hot pink primary neon, violet glow secondary, no cold colors",
        "palette: dark background, electric purple dominant, magenta accent, warm dark red hint",
    ],
    "dark": [
        "palette: near black background, dark blood red eyes and accents, deep violet aura, minimal glow",
        "palette: black background, gray-black deep shadows, crimson red neon accent only, no blue",
        "palette: black background, white silver hair contrast, magenta-pink glow, cold tone ONLY from silver hair",
    ],
    "default": [
        "palette: black background, violet and magenta dominant neon, warm dark red secondary, clean professional palette",
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
    key = f"{style}|{filename}|{short_num}|darkmark_v26_fullbody_noblue"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["bass", "808", "drop"]):
        return "visible bass shockwave rings on the wet ground around her feet"
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada"]):
        return "midnight shadow aura hugging her silhouette, dark red neon smoke at feet"
    if any(w in clean for w in ["rage", "fire", "burn"]):
        return "crimson neon flame aura outlining her body, aggressive energy"
    if any(w in clean for w in ["drive", "drift", "car", "speed"]):
        return "night drive warm red taillight streaks in background, wet asphalt reflection below"
    if any(w in clean for w in ["red", "blood", "demon", "devil"]):
        return "dark blood red energy aura wrapping her lower body and arms"
    if any(w in clean for w in ["queen", "king", "rule", "boss"]):
        return "dark throne energy, commanding full body stance, powerful presence"
    return "music energy as subtle violet neon aura outlining her full body"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — V26
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
        # IDENTIDADE E PERSONAGEM
        f"{TRAPSTAR_DNA}, "

        # CORPO — REGRA MAIS IMPORTANTE
        f"{BODY_LOCK}, "

        # ESTILO VISUAL
        f"{STYLE_LOCK}, "

        # PALETA DE CORES (SEM AZUL)
        f"{PALETTE_HARD_LOCK}, "

        # ILUMINAÇÃO
        f"{LIGHTING_LOCK}, "

        # PELE
        f"{SKIN_LOCK}, "

        # COMPOSIÇÃO PARA ENGAJAMENTO
        f"{RETENTION_LOCK}, "

        # QUALIDADE
        f"{QUALITY_LOCK}, "

        # VARIAÇÕES DINÂMICAS
        f"hair: {hair}, "
        f"eyes: {eyes}, "
        f"expression: {expression}, "
        f"pose: {pose}, "
        f"outfit: {outfit}, "
        f"scene: {scene}, "
        f"aura: {aura}, "
        f"detail: {detail}, "

        # CONTEXTO MUSICAL
        f"{palette}, "
        f"genre mood: {genre_text}, "
        f"song mood: {song_name}, "
        f"{art}, "

        # REGRAS CRÍTICAS FINAIS
        "CRITICAL FINAL RULES: "
        "MUST show complete full body from head to feet or head to knees minimum, "
        "camera MUST be pulled far back in medium-long or long shot, "
        "face MUST be small — body and outfit are the main visual focus, "
        "ABSOLUTE BAN on blue cyan teal anywhere in the image, "
        "ABSOLUTE BAN on face-only or headshot framing, "
        "character must be extremely attractive and sensual — viral dark anime queen energy, "
        "no text, no watermark, no logo, "
        "professional quality — looks like the best dark anime channel thumbnail on YouTube"
    )

    return _compact(prompt, max_len=3800)


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
# SUFIXO DE REFORÇO — Adicionado na hora da geração
# ══════════════════════════════════════════════════════════════════════

GENERATION_SUFFIX = (
    ", 2D anime illustration only, dark cyberpunk anime art, "
    "FULL BODY VISIBLE head to feet, camera far back long shot, "
    "extremely beautiful dark anime girl, sensual confident pose, "
    "neon magenta and violet ONLY as accent colors, "
    "NO BLUE NO CYAN NO TEAL ANYWHERE, "
    "dark near-black background, "
    "no text no logo no watermark, "
    "viral YouTube Shorts 9:16 thumbnail"
)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE)
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX)

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
        description="AI Image Generator — DJ DARK MARK v26 Full Body No Blue Engine"
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
        print("\n=== GENERATION SUFFIX ===")
        print(GENERATION_SUFFIX)
    else:
        path = generate_image(prompt, args.output)
        print(f"✅ Salvo: {path}" if path else "✗ Falha na geração.")
