"""
ai_image_generator.py — DJ DARK MARK v40 ULTIMATE TRAP/PHONK
=======================================================
100 WAIFUS ULTRA SEXY + MALVADAS + TRAPSTAR NEON
Otimizado para Shorts de Trap e Phonk
"""

from __future__ import annotations
import hashlib
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

logger = logging.getLogger("ai_image_generator")

# ======================= CONFIG =======================
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "cjwbw/animagine-xl-3.1",
    "lucataco/anything-v5-better-vae",
]

FLUX_PARAMS = {
    "width": 768,
    "height": 1024,
    "num_inference_steps": 42,
    "guidance_scale": 7.8,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

# ======================= LOCKS =======================
CORE_IDENTITY = (
    "DJ Dark Mark viral trap phonk anime visual, premium anime key visual, "
    "adult extremely beautiful woman, clearly 20+, mature seductive proportions, "
    "perfect face, scroll-stopping first frame, high CTR YouTube Shorts"
)

COMPOSITION = (
    "face and upper body dominant, eyes in upper third, strong silhouette, "
    "clean dark background, neon rim light, highly readable on mobile"
)

MOTION = (
    "alive cinematic frame, hair flowing in neon wind, glowing particles floating, "
    "subtle energy aura, dynamic but clean, trap phonk atmosphere"
)

VIRAL_HOOK = (
    "extreme viral hook: intense glowing eye reflection OR glowing neon tear OR "
    "dramatic face neon light OR glowing tattoo pulsing OR seductive dangerous smirk"
)

QUALITY = (
    "masterpiece, best quality, ultra detailed, absurdres, sharp lineart, "
    "glossy reflective eyes, perfect seductive face, cinematic neon lighting, "
    "high contrast, rich vibrant colors, professional trap phonk music visual"
)

NEGATIVE_PROMPT = (
    "ugly, bad anatomy, deformed, extra limbs, fused fingers, mutated, blurry, low quality, "
    "watermark, text, logo, child, loli, underage, babyface, multiple people, "
    "photorealistic, 3d render, western cartoon, bad proportions, overexposed"
)

# ======================= PALETAS =======================
PALETTES = [
    ("crimson", "dominant crimson red + black, blood neon accents, intense phonk energy", 35),
    ("teal", "dominant cyber teal + deep purple, neon reflections, dark trap night", 30),
    ("pink", "hot pink + black, rose neon glow, seductive dangerous vibe", 20),
    ("purple", "deep violet + indigo, magical dark trap aura", 10),
    ("warm", "amber red + gold neon, luxury trapstar sunset mood", 5),
]

# ======================= 100 WAIFUS =======================
TREND_WAIFUS = [
    "long hot pink hair flowing, glowing neon pink eyes, seductive yandere trap queen, glowing heart tattoo on neck pulsing neon",
    "teal blue long straight hair, electric cyan eyes, cold psycho street boss, neon circuit tattoo glowing on collarbone",
    "crimson red wavy hair, blood red glowing eyes, dangerous mafia queen, rose tattoo with neon thorns on chest",
    "silver white hair with black roots, violet neon eyes, ice cold luxury villainess, glowing spiderweb tattoo on neck",
    "deep purple twin tails, hot magenta eyes, crazy seductive trapstar, neon barcode tattoo on throat glowing",
    "black hair with neon pink streaks, electric blue eyes, dark gang leader queen, glowing dragon tattoo on arm",
    "emerald green long hair, golden amber glowing eyes, venom beauty trap queen, neon poison ivy tattoo on collarbone",
    "ruby red hair with black tips, crimson glowing eyes, seductive final boss waifu, glowing crown tattoo on forehead",
    "lavender hair with silver highlights, neon purple eyes, yandere calm danger, glowing butterfly tattoo pulsing on neck",
    "obsidian black hair with teal underlights, electric teal eyes, shadow assassin trapstar, neon skull tattoo glowing on chest",
    "rose gold hair, hot pink glowing eyes, luxury mafia princess, glowing money rose tattoo on shoulder",
    "neon blue bob cut, sapphire glowing eyes, cyber hacker queen, glowing circuit tattoo covering neck",
    "fiery orange hair, lava red eyes, rage beauty trap queen, neon flame tattoo pulsing on collarbone",
    "platinum blonde with black streaks, ice blue glowing eyes, cold emotionless killer queen, glowing dagger tattoo",
    "candy pink long hair, glowing magenta eyes, psycho cute but deadly, neon heart dagger tattoo on chest",
    "midnight purple hair, violet neon eyes, gothic trap queen, glowing bat wings tattoo on back visible on shoulders",
    "toxic green hair, acid green glowing eyes, venomous seductive boss, glowing skull rose tattoo on neck",
    "sunset orange hair, amber neon eyes, street racer queen, glowing speed lines tattoo on arm",
    "blood red long hair, ruby glowing eyes, vampire trapstar, glowing bite mark tattoo pulsing neon",
    "electric purple hair, neon violet eyes, chaotic yandere queen, glowing broken heart tattoo on chest",
    "jet black hair with crimson highlights, blood neon eyes, silent assassin beauty, glowing katana tattoo on neck",
    "neon yellow hair, electric lime eyes, hyper trapstar girl, glowing lightning tattoo pulsing",
    "deep burgundy hair, garnet glowing eyes, luxury villainess, glowing diamond tattoo on collarbone",
    "icy silver hair, arctic blue glowing eyes, emotionless mafia queen, glowing snowflake tattoo neon",
    "hot magenta hair, glowing fuchsia eyes, dangerous flirt trap queen, glowing lips tattoo on neck",
    "neon cyan hair, glowing turquoise eyes, cyberpunk street goddess, glowing binary tattoo on throat",
    "ruby crimson hair, glowing scarlet eyes, final boss energy, glowing throne tattoo on chest",
    "pastel pink with black roots, glowing pink eyes, soft but psycho trapstar, glowing teddy bear knife tattoo",
    "dark navy hair with teal tips, glowing sea blue eyes, night club queen, glowing microphone tattoo neon",
    "golden blonde with pink streaks, glowing rose gold eyes, rich drip trap queen, glowing chain tattoo",
    "neon violet long hair, glowing amethyst eyes, dark pop trap idol, glowing music note tattoo pulsing",
    "crimson black ombre hair, glowing ember eyes, fire rage beauty, glowing phoenix tattoo on shoulder",
    "electric blue long hair, glowing sapphire eyes, hacker boss queen, glowing keyboard tattoo on neck",
    "hot red hair with silver streaks, glowing ruby eyes, seductive gang leader, glowing gun rose tattoo",
    "neon green hair, glowing emerald eyes, toxic cute deadly, glowing poison bottle tattoo",
    "platinum silver hair, glowing diamond eyes, luxury ice queen, glowing crown of thorns tattoo",
    "deep rose hair, glowing coral eyes, romantic toxic waifu, glowing broken chain tattoo",
    "black hair with neon purple underlights, glowing amethyst eyes, shadow queen trapstar, glowing eclipse tattoo",
    "fiery red hair, glowing lava eyes, unstoppable trap queen, glowing explosion tattoo on collarbone",
    "neon pink bob hair, glowing bubblegum eyes, chaotic cute psycho, glowing lollipop knife tattoo",
    "silver white hair with crimson tips, glowing blood eyes, fallen angel trapstar, glowing halo broken tattoo",
    "teal and black hair, glowing cyan eyes, cyber street rebel, glowing glitch tattoo pulsing",
    "hot purple hair, glowing violet eyes, yandere trap boss, glowing eye tattoo on neck",
    "crimson wavy hair, glowing scarlet eyes, seductive dark siren, glowing wave tattoo neon",
    "neon orange hair, glowing sunset eyes, speed queen trapstar, glowing tire burn tattoo",
    "midnight black hair, glowing red eyes, ultimate boss queen, glowing throne of skulls tattoo",
    "lavender silver hair, glowing lilac eyes, elegant dangerous beauty, glowing rose vine tattoo",
    "electric pink hair, glowing hot pink eyes, hyper yandere queen, glowing knife heart tattoo",
    "ruby red hair, glowing garnet eyes, mafia luxury queen, glowing money stack tattoo neon",
    "neon teal hair, glowing aqua eyes, underwater trap queen, glowing mermaid skeleton tattoo",
    "black hair with neon crimson streaks, glowing blood red eyes, silent killer beauty, glowing blood drip tattoo",
    "golden pink hair, glowing champagne eyes, rich drip queen, glowing luxury bag tattoo",
    "deep violet hair, glowing purple eyes, gothic neon queen, glowing bat neon tattoo",
    "hot magenta long hair, glowing fuchsia eyes, club boss seductive, glowing stage light tattoo",
    "neon lime hair, glowing acid green eyes, toxic street queen, glowing biohazard tattoo",
    "silver blue hair, glowing ice eyes, cold emotionless trapstar, glowing snow storm tattoo",
    "crimson purple ombre, glowing amethyst eyes, dark romantic queen, glowing heart cage tattoo",
    "electric cyan hair, glowing blue eyes, cyber trap goddess, glowing robot heart tattoo",
    "fiery orange red hair, glowing ember eyes, rage beauty final boss, glowing fire crown tattoo",
    "pastel blue with pink tips, glowing bubblegum eyes, soft psycho trap queen, glowing candy skull tattoo",
    "neon black hair with pink glow, glowing hot pink eyes, ultimate trapstar, glowing 808 tattoo pulsing",
    "ruby silver hair, glowing scarlet eyes, luxury villainess, glowing diamond chain tattoo",
    "electric purple bob, glowing violet eyes, hacker yandere, glowing code tattoo on neck",
    "deep red hair, glowing blood eyes, seductive assassin queen, glowing dagger rose tattoo",
    "neon green long hair, glowing emerald eyes, venom trap queen, glowing snake tattoo glowing",
    "platinum blonde black roots, glowing arctic eyes, ice cold boss, glowing frost tattoo",
    "hot pink silver hair, glowing magenta eyes, chaotic luxury queen, glowing money flame tattoo",
    "midnight purple hair, glowing amethyst eyes, dark goddess trapstar, glowing moon tattoo pulsing",
    "crimson teal hair, glowing ruby cyan eyes, fire ice queen, glowing split tattoo neon",
    "neon yellow pink hair, glowing electric eyes, hyper street queen, glowing lightning rose tattoo",
    "obsidian hair with neon red, glowing blood eyes, shadow trap queen, glowing void tattoo",
    "rose gold long hair, glowing pink gold eyes, rich mafia beauty, glowing crown tattoo",
    "electric blue purple hair, glowing sapphire violet eyes, cyber yandere boss, glowing glitch heart",
    "fiery crimson hair, glowing lava eyes, unstoppable trap queen, glowing phoenix wings tattoo",
    "neon teal silver hair, glowing cyan eyes, night club goddess, glowing microphone skull tattoo",
    "black hair neon pink, glowing hot pink eyes, psycho seductive queen, glowing broken mirror tattoo",
    "deep burgundy hair, glowing garnet eyes, elegant dark queen, glowing wine poison tattoo",
    "silver lavender hair, glowing lilac eyes, fallen luxury queen, glowing angel wings broken neon",
    "hot magenta teal hair, glowing fuchsia cyan eyes, chaotic trapstar, glowing dice skull tattoo",
    "ruby black hair, glowing scarlet eyes, final boss seductive, glowing throne neon tattoo",
    "neon orange silver hair, glowing sunset eyes, speed racer queen, glowing flame tire tattoo",
    "platinum pink hair, glowing rose eyes, luxury psycho queen, glowing teddy bear gun tattoo",
    "electric green hair, glowing acid eyes, toxic beauty boss, glowing bio rose tattoo",
    "deep navy hair neon purple, glowing indigo eyes, night shadow queen, glowing eclipse rose tattoo",
    "crimson gold hair, glowing amber eyes, rich trap queen, glowing money wings tattoo",
    "neon violet red hair, glowing amethyst scarlet eyes, dark siren trapstar, glowing siren tattoo",
    "silver black hair, glowing diamond eyes, ice mafia queen, glowing snow diamond tattoo",
    "hot pink crimson hair, glowing magenta blood eyes, yandere final boss, glowing heart blood tattoo",
    "electric cyan magenta hair, glowing turquoise pink eyes, cyber club queen, glowing stage glitch tattoo",
    "ruby teal hair, glowing scarlet cyan eyes, fire water queen, glowing lava ice tattoo",
    "neon black pink hair, glowing void pink eyes, ultimate dark queen, glowing 808 crown tattoo",
    "lavender crimson hair, glowing lilac blood eyes, romantic psycho queen, glowing rose blood tattoo",
    "platinum teal hair, glowing arctic cyan eyes, cold cyber queen, glowing robot rose tattoo",
    "hot red silver hair, glowing ruby ice eyes, rage ice beauty, glowing fire snow tattoo",
    "neon purple gold hair, glowing violet champagne eyes, luxury trap goddess, glowing money neon tattoo",
    "obsidian crimson hair, glowing blood scarlet eyes, shadow final boss, glowing void throne tattoo",
    "electric pink teal hair, glowing hot pink cyan eyes, hyper yandere trapstar, glowing knife neon tattoo",
    "deep rose black hair, glowing coral dark eyes, seductive street queen, glowing lips chain tattoo",
    "silver neon green hair, glowing diamond acid eyes, luxury toxic queen, glowing diamond poison tattoo",
    "crimson neon blue hair, glowing scarlet electric eyes, ultimate trap phonk queen, glowing full neon tattoo set pulsing",
]

TREND_BAD_BOYS = [
    "white-haired strongest sorcerer, godlike aura, piercing eyes",
    "pink-haired cursed fighter, chaotic energy, dangerous smirk",
    "black-haired cold rival, sharp jawline, intimidating presence",
    "fire aura warrior, aggressive handsome face, glowing eyes",
    "scarred street king, dominant bad boy, neck tattoos",
]

# ======================= HELPERS =======================
def _compact(text: str, max_len: int = 3800) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len].rstrip(", ")

def _seed(style: str, filename: str, num: int) -> int:
    key = f"darkmark_v40_trap_phonk_{style}_{filename}_{num}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 999999999

def _rng(style: str, filename: str, num: int):
    return random.Random(_seed(style, filename, num))

def _get_palette(rng, force_palette: str | None = None) -> Tuple[str, str]:
    if force_palette:
        for name, desc, _ in PALETTES:
            if name == force_palette:
                return name, desc
    total = sum(w for _, _, w in PALETTES)
    r = rng.random() * total
    acc = 0
    for name, desc, weight in PALETTES:
        acc += weight
        if r <= acc:
            return name, desc
    return PALETTES[0][0], PALETTES[0][1]

# ======================= PROMPT BUILDER =======================
def build_ai_prompt(
    style: str = "phonk",
    filename: str = "song.mp3",
    short_num: int = 1,
    force_male: bool = False,
    force_female: bool = False,
    force_palette: str | None = None,
) -> str:
    rng = _rng(style, filename, short_num)
    
    if force_male:
        is_male = True
    elif force_female or rng.random() > 0.35:
        is_male = False
    else:
        is_male = True

    if is_male:
        char = rng.choice(TREND_BAD_BOYS)
        gender = "one adult anime man, masculine sharp jaw, strong male presence, attractive bad boy"
    else:
        char = rng.choice(TREND_WAIFUS)
        gender = "one adult extremely beautiful anime woman, seductive face, villainous smirk, perfect body, sexy trapstar"

    palette_name, palette_desc = _get_palette(rng, force_palette)

    prompt = f"""
    {CORE_IDENTITY}, {gender}, {char},
    {style} trap phonk music atmosphere, dark street luxury aesthetic, heavy neon glow,
    {COMPOSITION}, {MOTION}, {VIRAL_HOOK},
    dominant palette: {palette_name}, {palette_desc},
    dramatic cinematic neon lighting, high contrast, intense seductive expression,
    {QUALITY}
    """.strip()

    return _compact(prompt)

# ======================= GENERATION =======================
def generate_image(prompt: str, output_path: str = "output.png") -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado")
        return None

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    full_prompt = prompt + ", no text, no watermark, no logo, ultra vibrant neon"

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"Tentativa {attempt}/3 com {model}")
                payload = {"input": {"prompt": full_prompt, "negative_prompt": NEGATIVE_PROMPT, **FLUX_PARAMS}}
                headers = {"Authorization": f"Token {REPLICATE_API_TOKEN}", "Content-Type": "application/json"}

                resp = requests.post(f"https://api.replicate.com/v1/models/{model}/predictions",
                                   headers=headers, json=payload, timeout=30)
                resp.raise_for_status()
                pred = resp.json()

                poll_url = pred.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{pred['id']}"

                for _ in range(100):
                    time.sleep(2)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()

                    if data.get("status") == "succeeded":
                        output = data.get("output")
                        img_url = output[0] if isinstance(output, list) else output
                        img = requests.get(img_url, timeout=60)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)
                        logger.info(f"✅ Imagem salva: {output_path}")
                        return output_path

                    if data.get("status") == "failed":
                        raise RuntimeError(data.get("error"))
                raise TimeoutError("Timeout")
            except Exception as e:
                logger.warning(f"Falha {model} tentativa {attempt}: {e}")
                time.sleep(3)
    logger.error("Todas as tentativas falharam")
    return None

# ======================= CLI =======================
if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="DJ DARK MARK v40 — 100 Waifus Trap/Phonk")
    parser.add_argument("--style", default="phonk")
    parser.add_argument("--filename", default="song.mp3")
    parser.add_argument("--short-num", type=int, default=1)
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--male", action="store_true")
    parser.add_argument("--female", action="store_true")
    parser.add_argument("--palette", choices=["crimson", "teal", "pink", "purple", "warm"])
    parser.add_argument("--prompt-only", action="store_true")

    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        short_num=args.short_num,
        force_male=args.male,
        force_female=args.female,
        force_palette=args.palette,
    )

    if args.prompt_only:
        print(prompt)
    else:
        result = generate_image(prompt, args.output)
        print("✅ Gerado com sucesso!" if result else "❌ Falha na geração")
