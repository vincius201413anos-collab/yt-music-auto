"""
ai_image_generator.py — DJ DARK MARK v15 FULL BODY LOCK
============================================================
v15: Foco em corpo inteiro / medium-full body como nas referências.
- Personagem ocupa 70-90% do frame vertical
- Sem close-up de rosto dominante
- Roupa, silhueta e pose visíveis
- Fundo com aura/cenário forte mas secundário ao personagem
- Baseado nas referências: correntes, aura de fogo, gothic dress, cat ears
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
    "num_inference_steps": int(os.getenv("FLUX_STEPS", "40")),
    "guidance_scale": float(os.getenv("FLUX_GUIDANCE", "7.5")),
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

# v15: CHARACTER_DNA reescrito para corpo inteiro visível
CHARACTER_DNA = (
    "one adult anime girl only, beautiful dark gothic cyberpunk anime girl, "
    "full body visible from head to feet, or at minimum from head to knees, "
    "character takes up 75 percent of the vertical frame, "
    "pretty face, clean face, soft blush, natural anime skin tone, "
    "large glowing hypnotic eyes, glossy pupils, sharp anime eyes, readable face, "
    "varied expression: sometimes cute, sometimes evil, sometimes crazy, sometimes calm, "
    "tiny fang smile optional, mischievous smile optional, mysterious stare optional, "
    "black hair, white hair, dark purple hair or cyan-tipped hair, messy bangs, twin tails or long flowing hair, "
    "small demon horns, cat ears, cat-ear hoodie, gothic bow or hair clips optional, "
    "full gothic outfit visible: black gothic dress, black techwear full outfit, gothic streetwear full look, "
    "oversized black hoodie with visible torso and legs, glossy black jacket with pants or skirt, "
    "choker, chains around waist and wrists, platform boots visible at the bottom, "
    "platform-safe outfit, no nudity, no explicit outfit, alone in frame, no crowd, "
    "strong full-body silhouette, face and body both visible and in focus"
)

ANIME_STYLE_DNA = (
    "2D anime illustration only, dark anime edit style, viral phonk anime cover art, "
    "full body anime character art, manga cover energy, sharp manga lineart, crisp cel shading, "
    "beautiful vibrant neon lighting, deep black shadows, high contrast ink shadows, "
    "glowing neon eyes, luminous aura, hot magenta neon, violet glow, red eye glow, "
    "toxic green glow sometimes, cyan rim light only, bright but tasteful light effects, "
    "not overexposed, not messy, not realistic, not 3D"
)

RETENTION_DNA = (
    "scroll stopping first frame, strong full-body focal point, "
    "character silhouette readable on phone screen from head to toe, "
    "simple powerful composition, high contrast, not cluttered, memorable full silhouette, "
    "dark background with one dominant neon glow emanating from behind the character, "
    "space near lower edge for audio waveform or DJ logo overlay, "
    "viral anime full body cover art aesthetic, album cover aesthetic, music visualizer background, "
    "character centered in 9:16 frame with room at top and bottom"
)

SKIN_LIGHTING_LOCK = (
    "natural anime skin tone preserved, pale skin or soft warm anime skin, "
    "skin is not blue, face is not fully cyan, no full blue face, no blue body, "
    "neon colors appear only as rim light, reflected highlights and eye glow, "
    "soft blush visible, natural face shading, beautiful readable face, "
    "dark shadows with magenta and violet glow, cinematic anime lighting"
)

QUALITY_TAGS = (
    "masterpiece, best quality, high-end anime key visual, polished anime illustration, "
    "ultra sharp lineart, clean anatomy, refined face, full body anatomy correct, "
    "detailed hands and feet, platform boots detail, glossy detailed eyes, cinematic lighting, "
    "deep blacks, luminous neon highlights, vibrant magenta, violet, red and cyan lighting, "
    "beautiful anime girl full body, dark aesthetic, phonk aesthetic, 9:16 vertical"
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
    "overexposed neon, messy lights, random scenery, empty scene without character, "
    "ugly AI face, portrait only, face only, head only, headshot only, bust only, "
    "cropped body, missing legs, missing feet, missing torso, cut off at waist, "
    "zoomed in too much, extreme close-up, macro face shot, "
    "small character in background, character too far, character too tiny in frame"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES VISUAIS — v15 FULL BODY
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair flowing past waist with heavy bangs and red neon eye glow",
    "black twin tails reaching hips with hot pink and cyan highlights",
    "white hair falling to mid-back with black underlayer and glowing magenta eyes",
    "messy black hair to shoulders, gothic bow accessory, red glowing eyes",
    "long dark purple hair with wet strands and violet neon reflections reaching floor",
    "short black hair under oversized cat-ear hoodie, glowing eyes piercing through",
    "long black hair blowing dramatically in wind, crimson rim light all around",
    "black and red ombre hair, very long, pooling slightly at feet",
]

EYE_VARIATIONS = [
    "glowing red eyes, intense hypnotic stare, visible even from full body distance",
    "glowing violet eyes with glossy anime reflections bright enough to light her face",
    "bright magenta eyes, cute dangerous smile, eyes readable from full body shot",
    "toxic green glowing eyes with supernatural flame aura matching eye color",
    "cyan and pink heterochromia, cyberpunk iris glow, intense stare",
]

OUTFIT_VARIATIONS = [
    "long black gothic dress with silver chain details at waist, platform boots visible",
    "black techwear full outfit: jacket, cargo pants with chains, knee-high platform boots",
    "dark cyberpunk jacket with glossy wet leather, black shorts with fishnet stockings and boots",
    "gothic black ensemble: corseted top, layered skirt with chains, tall platform boots",
    "oversized black cat-ear hoodie, black shorts with thigh-high stockings, chunky boots",
    "hooded shadow cloak, full length, parted in front to show gothic outfit underneath, boots",
    "black gothic lolita dress full length with lace trim, chains, platform mary janes",
    "black sleeveless gothic dress with off-shoulder detail, chains around wrists and waist, boots",
]

# v15: POSE_VARIATIONS totalmente reescrito para corpo inteiro
POSE_VARIATIONS = [
    "standing confidently facing viewer, arms at sides, full body visible head to boots",
    "standing with one hand raised holding dark energy, other at hip, full body pose",
    "walking toward viewer slowly, chains swinging, full body dynamic pose",
    "standing in contrapposto pose, looking over shoulder with glowing eyes, full body",
    "arms crossed at chest, chin slightly down, dangerous calm stare, full body centered",
    "one knee slightly bent, hand reaching toward camera, glowing eyes intense, full body",
    "standing with both hands in hoodie pocket, head tilted, full body relaxed but dark",
    "dramatic cape or hair flowing behind, one arm extended, full body silhouette pose",
    "sitting on edge of something low, legs visible, leaning forward, full body framing",
    "back slightly turned, face looking over shoulder with glowing eyes, full body rear pose",
]

# v15: CAMERA_VARIATIONS para corpo inteiro
CAMERA_VARIATIONS = [
    "wide full body shot, character from head to feet centered in vertical frame",
    "full body portrait, slight low angle looking up at character, feet to crown visible",
    "three-quarter full body shot, head to feet slightly angled, dramatic lighting",
    "full body centered composition, 9:16 vertical, character fills 75 percent of height",
    "dynamic full body anime cover art framing, low angle, character looming beautifully",
    "full body shot with slight dutch angle, character centered, dark environment around",
    "full body standing portrait, symmetrical composition, character fills the frame vertically",
]

ART_STYLES = [
    "dark anime edit style, sharp manga lines, glowing eyes, high contrast black shadows, full body key visual",
    "viral phonk album cover art, anime girl full body portrait, neon aura, clean silhouette",
    "polished anime key visual, premium cel shading, hot pink and violet neon glow, full character art",
    "gothic cyberpunk anime illustration, halftone manga texture, red eye glow, full body composition",
    "cute dark anime full body art, clean face and full outfit visible, luminous eyes, deep black background",
]

AURA_VARIATIONS = [
    "purple lightning aura erupting from the ground around her feet and silhouette",
    "red neon eye bloom and black smoke tendrils wrapping around her entire body",
    "toxic green flame aura burning from the ground up along her silhouette like a halo",
    "hot pink energy cracks radiating from her feet into the ground around her",
    "cyan and magenta neon mist pooling at her feet and rising along her sides",
    "black ink shadows with violet sparks erupting from the floor around her boots",
    "dark crimson chains floating and wrapping loosely around her full body",
    "white-hot divine neon energy outlining her entire silhouette from boots to horns",
]

EXPRESSION_VARIATIONS = [
    "cute mischievous fang smile, playful but dark, full body relaxed stance",
    "evil confident smile, villain anime girl energy, powerful full body pose",
    "crazy hypnotic stare, slightly unhinged anime smile, glowing eyes, strong pose",
    "calm mysterious expression, beautiful and dangerous, elegant full body stance",
    "soft cute face with dangerous neon eyes, deceptively gentle full body pose",
    "smirking gothic girl, chaotic phonk energy, dynamic full body posture",
    "serious cold stare, premium anime cover mood, composed full body stance",
]

# v15: REFERENCE_STYLE_LOCKS baseados nas imagens de referência enviadas
REFERENCE_STYLE_LOCKS = [
    "full body gothic anime girl with chains and red sky background like dark album cover art",
    "full body purple demon anime girl with lightning aura and glowing purple eyes standing centered",
    "full body cat-ear hooded girl with toxic green flame aura burning from ground",
    "full body dark anime girl with pink magenta chains wrapping around her and neon background",
    "full body gothic dress anime girl surrounded by crimson crows and broken chains in red sky",
    "full body cyberpunk dark anime girl with electric blue-purple aura and platform boots visible",
    "full body black techwear anime girl with violet neon glow and city rain behind her",
    "full body white-haired demon girl with hot pink background and fang smile, full outfit visible",
]


# ══════════════════════════════════════════════════════════════════════
# CONCEITOS VISUAIS POR GÊNERO — v15 FULL BODY SCENES
# ══════════════════════════════════════════════════════════════════════

VISUAL_CONCEPTS = {
    "phonk": [
        {
            "label": "PHONK_PURPLE_CHAINS_FULLBODY",
            "scene": (
                "{character}, full body standing pose, small glowing purple horns, long black hair, "
                "dark alley wall with purple neon columns, chains floating around her full body, "
                "violet glowing eyes, gothic full outfit visible from boots to crown, {aura}, {reference_lock}"
            ),
            "palette": "deep black, violet neon, hot magenta, tiny cyan rim light, chains",
        },
        {
            "label": "PHONK_PINK_DEMON_FULLBODY",
            "scene": (
                "{character}, full body demon anime girl standing, tiny fang smile, hot pink explosion behind her, "
                "cyan hair highlights, black gothic full outfit visible, platform boots, playful evil pose, "
                "full body anime pfp cover art, {aura}, {reference_lock}"
            ),
            "palette": "hot pink background, cyan highlights, black outfit, violet eyes, platform boots",
        },
        {
            "label": "PHONK_GREEN_CAT_FULLBODY",
            "scene": (
                "{character}, cat ears or cat-ear hoodie, full body standing centered, toxic green flame aura "
                "burning up from floor around her feet and silhouette, glowing green eyes, black full outfit "
                "visible from boots to head, dark background, {aura}, {reference_lock}"
            ),
            "palette": "black, toxic green flames from ground, white glow outline, tiny violet shadows",
        },
        {
            "label": "PHONK_PURPLE_LIGHTNING_FULLBODY",
            "scene": (
                "{character}, full body standing pose, glowing magenta eyes, purple lightning aura "
                "erupting from the ground around her feet, gothic full outfit and platform boots visible, "
                "album cover full body portrait, hypnotic phonk energy, {aura}, {reference_lock}"
            ),
            "palette": "near black ground, neon purple lightning, magenta eye glow, cyan edge light on silhouette",
        },
    ],
    "trap": [
        {
            "label": "TRAP_GLITCH_GIRL_FULLBODY",
            "scene": (
                "{character}, full body anime portrait, hot pink glitch branches around her silhouette, "
                "black techwear full outfit visible, confident trap cover art stance, "
                "neon city blur behind her, boots on wet ground, {aura}, {reference_lock}"
            ),
            "palette": "black outfit, hot pink, violet, cyan shine, neon city bokeh",
        },
        {
            "label": "TRAP_BLUE_PURPLE_FULLBODY",
            "scene": (
                "{character}, blue or dark purple hair very long flowing, glowing magenta eyes, "
                "dark gothic full outfit visible, full body centered album cover pose, "
                "vibrant cyber trap aesthetic, electric smoke around feet, {aura}, {reference_lock}"
            ),
            "palette": "deep black, electric purple, cyan hair glow, magenta eyes, smoke at feet",
        },
        {
            "label": "TRAP_LUXURY_DARK_FULLBODY",
            "scene": (
                "{character}, full body standing, glossy black jacket full outfit and boots visible, "
                "neon city bokeh background, calm boss energy full body pose, "
                "magenta eyes, clean dark anime key visual, {aura}, {reference_lock}"
            ),
            "palette": "black, violet, cyan, magenta shine, city lights behind",
        },
    ],
    "dark": [
        {
            "label": "DARK_RED_CHAINS_FULLBODY",
            "scene": (
                "{character}, full body standing centered, black gothic long dress with chains floating around her, "
                "glowing red eyes, crimson red sky behind her with black crow silhouettes, "
                "dark manga full body key visual, chains in foreground and background, {aura}, {reference_lock}"
            ),
            "palette": "black dress, red sky, dark chains, glowing red eyes, crow silhouettes",
        },
        {
            "label": "DARK_HOOD_FULLBODY",
            "scene": (
                "{character}, full body standing, hood up with cat ears on hoodie, full hooded figure visible "
                "from boots to hood, glowing eyes under hood, rainy dark alley, "
                "blue neon columns behind, mysterious full body anime edit, {aura}, {reference_lock}"
            ),
            "palette": "black hood full body, blue neon columns, magenta face glow through shadow",
        },
        {
            "label": "DARK_PURPLE_AURA_FULLBODY",
            "scene": (
                "{character}, full body standing, black branches crossing foreground and background, "
                "hot pink backlight outlining her full silhouette, glowing purple eyes, "
                "beautiful evil anime girl full body, gothic dress and boots, {aura}, {reference_lock}"
            ),
            "palette": "black, hot pink backlight silhouette, violet, tiny cyan rim on edges",
        },
    ],
    "electronic": [
        {
            "label": "ELECTRONIC_NEON_FULLBODY",
            "scene": (
                "{character}, full body standing with arms slightly spread, glowing magenta eyes, "
                "digital neon particles raining around her full body, purple and cyan explosion behind, "
                "clean full body pfp composition, boots on glowing floor, {aura}, {reference_lock}"
            ),
            "palette": "purple, magenta, cyan, black, neon particle rain",
        },
        {
            "label": "ELECTRONIC_LASER_FULLBODY",
            "scene": (
                "{character}, full body standing, horizontal neon laser reflections across her glowing eyes, "
                "rain falling all around full body, holographic elements behind, "
                "clean anime cyberpunk full body portrait, boots on wet reflective floor, {aura}, {reference_lock}"
            ),
            "palette": "red laser, cyan rain, purple haze, wet floor reflections",
        },
    ],
    "lofi": [
        {
            "label": "LOFI_MIDNIGHT_FULLBODY",
            "scene": (
                "{character}, full body sitting on windowsill or low wall, legs visible, holding phone, "
                "soft sad cute expression, rain outside window, full outfit and boots visible, "
                "purple shadows filling the room, lonely midnight full body vibe, {aura}, {reference_lock}"
            ),
            "palette": "black room, soft cyan rain outside, violet glow, warm small lamp",
        },
        {
            "label": "LOFI_SOFT_GOTH_FULLBODY",
            "scene": (
                "{character}, full body standing or leaning, soft cute gothic anime portrait, "
                "sleepy glowing eyes, full gothic outfit visible, quiet midnight vibe, "
                "deep shadows with gentle magenta aura around full body, {aura}, {reference_lock}"
            ),
            "palette": "black, violet, soft pink, cold blue edge light on silhouette",
        },
    ],
    "default": [
        {
            "label": "DEFAULT_DARK_FULLBODY",
            "scene": (
                "{character}, {camera}, {pose}, dark anime cyberpunk full body portrait, glowing eyes, "
                "full gothic outfit and boots visible, neon bokeh background, high contrast, {aura}, {reference_lock}"
            ),
            "palette": "black, purple, magenta, cyan, red glow, visible outfit head to toe",
        },
        {
            "label": "DEFAULT_RED_SKY_CHAINS_FULLBODY",
            "scene": (
                "{character}, full body standing centered, long dark hair flowing, glowing red eyes, "
                "crimson dramatic sky behind with dark chain silhouettes floating, gothic full dress visible, "
                "album cover full body dark anime art, viral phonk cover energy, {aura}, {reference_lock}"
            ),
            "palette": "black dress, crimson red sky, dark chains, red glow, dramatic atmosphere",
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
    key = f"{filename}|{short_num}|darkmark_v15_fullbody_lock"
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
        return "red taillight streaks on wet ground at her feet, night drive atmosphere"
    if any(w in clean for w in ["ghost", "phantom", "shadow", "dark", "madrugada"]):
        return "ghostly shadow tendrils rising from the ground around her boots, midnight darkness"
    if any(w in clean for w in ["rain", "cry", "sad", "alone"]):
        return "rain falling around her full body, wet floor reflections below her boots"
    if any(w in clean for w in ["fire", "burn", "rage"]):
        return "crimson fire erupting from the ground around her feet, heat haze distortion"
    if any(w in clean for w in ["bass", "drop", "808"]):
        return "visible bass shockwave rings expanding from her feet on the floor"
    return "dramatic atmosphere element at ground level around her boots"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list | None = None, short_num: int = 1) -> str:
    """
    Gera prompt v15 DARKMARK FULL BODY LOCK.
    Foco: corpo inteiro da personagem, como nas referências enviadas.
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
        "CRITICAL: full body visible from head to feet, character fills 75 percent of vertical frame, "
        "full gothic outfit and platform boots clearly visible, do not crop below waist, "
        "vibrant but tasteful neon, beautiful polished lighting on full body, "
        "sometimes cute, sometimes evil, sometimes crazy, sometimes calm, but always pretty and on-brand, "
        "clean 9:16 vertical composition, background dark enough for waveform and logo overlay at bottom, "
        "no text, no watermark, no logo, no letters, no photorealism, no 3d, no blue skin, no fully blue face, "
        "no extreme close-up, no head-only shot, full body is mandatory"
    )

    return _compact(prompt, max_len=3600)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    if output_path is None:
        output_path = "temp/generated_background.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt
        + ", 2D anime only, dark anime full body edit, viral phonk anime cover, glowing eyes, "
        + "manga shadows, sharp lineart, cel shading, high contrast, deep black background, "
        + "natural anime skin tone preserved, face not tinted blue, neon only as rim light and eye glow, "
        + "hot magenta violet cyan red neon, toxic green aura sometimes, beautiful gothic cyberpunk anime girl, "
        + "FULL BODY from head to feet visible in frame, full gothic outfit and boots visible, "
        + "character takes up 75 to 85 percent of the vertical 9:16 frame height, "
        + "do not crop legs or feet, do not zoom in on face only, full silhouette visible, "
        + "cute evil crazy or calm expression variety, polished not messy, "
        + "must look like viral dark anime phonk full body edit references, not generic AI art, "
        + "not realistic, not 3d, not photo, clean face and full clean body anatomy, phone wallpaper quality"
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
# FUNÇÕES EXTRAS — compatibilidade com main.py
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

    parser = argparse.ArgumentParser(description="AI Image Generator v15 — DarkMark Full Body Lock")
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
