"""
ai_image_generator.py — DJ DARK MARK v40.3 MERGE
=================================================
v37 structure + 100 WAIFUS do v40.2 + back view support
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ======================= CONFIG =======================
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "cjwbw/animagine-xl-3.1",
]

FLUX_PARAMS = {
    "width": 768,
    "height": 1024,
    "num_inference_steps": 38,
    "guidance_scale": 8.0,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

# ══════════════════════════════════════════════════════════════════════
# 100 WAIFUS — v40.2 (aparência detalhada, random por seed)
# ══════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════
# LOCKS DE QUALIDADE / COMPOSIÇÃO / ESTILO
# ══════════════════════════════════════════════════════════════════════
CHANNEL_IDENTITY = (
    "DJ Dark Mark viral trap phonk anime visual, premium anime key visual, "
    "adult extremely beautiful woman, 20+, scroll-stopping YouTube Shorts first frame"
)

CORE_CHARACTER = (
    "one adult anime woman, clearly adult, mature proportions, "
    "beautiful waifu character, expressive face, hypnotic eyes, "
    "magnetic emotional presence, strong visual identity, "
    "alone, single character, no other people, no text"
)

COMPOSITION_LOCK = (
    "vertical 9:16 mobile-first composition, "
    "face and upper body dominant, eyes in upper third, "
    "character large in frame, readable at tiny phone size, "
    "clean background, strong silhouette, clear focal point, "
    "opening frame for YouTube Shorts, designed to stop scrolling immediately"
)

STYLE_LOCK = (
    "premium anime key visual, clean sharp lineart, "
    "high-end 2D anime illustration, polished cel shading, "
    "cinematic lighting, glossy eyes, detailed hair, "
    "rich colors, high contrast, professional music cover art, "
    "not photorealistic, not 3d render"
)

MOTION_LOCK = (
    "alive frame, subtle sense of motion, hair moving in wind, "
    "floating particles, cinematic depth, glowing dust, "
    "energy in the air, dynamic but not cluttered"
)

VIRAL_HOOK_LOCK = (
    "one strong visual hook: glowing tear OR intense eye reflection OR dramatic face light "
    "OR hair blown by neon wind OR small aura around character, "
    "instantly recognizable visual moment, memorable frame"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed, crisp lineart, "
    "beautiful face, detailed shining eyes, clean anatomy, "
    "professional channel branding, high resolution, premium finish"
)

# ══════════════════════════════════════════════════════════════════════
# PALETAS
# ══════════════════════════════════════════════════════════════════════
PALETTE_WARM = (
    "dominant warm golden amber palette, sunset orange light, "
    "golden rim light on hair, warm cinematic shadows, "
    "high contrast amber glow, emotional golden-hour anime look"
)
PALETTE_TEAL = (
    "dominant teal blue cyber palette, deep navy shadows, "
    "teal neon reflections, cool cinematic atmosphere, "
    "blue-green glow around character, futuristic night mood"
)
PALETTE_CRIMSON = (
    "dominant crimson red and black palette, dark dramatic shadows, "
    "blood-red accent light, intense phonk energy, "
    "dangerous but beautiful dark anime mood"
)
PALETTE_PURPLE = (
    "dominant violet purple and indigo palette, magical dark aura, "
    "purple rim light, dreamy anime atmosphere, "
    "deep shadow with bright violet highlights"
)
PALETTE_PINK = (
    "dominant hot pink and black palette, rose neon glow, "
    "cute but dangerous dark pop mood, pink bokeh, "
    "high contrast pink highlights"
)

PALETTES = [
    ("warm",    PALETTE_WARM,    30),
    ("teal",    PALETTE_TEAL,    28),
    ("crimson", PALETTE_CRIMSON, 18),
    ("purple",  PALETTE_PURPLE,  14),
    ("pink",    PALETTE_PINK,    10),
]

# ══════════════════════════════════════════════════════════════════════
# GÊNEROS
# ══════════════════════════════════════════════════════════════════════
GENRE_MAP = {
    "phonk":      "phonk",
    "trap":       "trap",
    "dark":       "dark",
    "darkpop":    "darkpop",
    "dark pop":   "darkpop",
    "electronic": "electronic",
    "edm":        "electronic",
    "dubstep":    "electronic",
    "funk":       "trap",
    "rock":       "rock",
    "metal":      "dark",
    "cinematic":  "darkpop",
    "lofi":       "darkpop",
    "indie":      "darkpop",
    "pop":        "darkpop",
}

GENRE_BOOSTS = {
    "phonk":      "phonk atmosphere, heavy 808 bass feeling, dark street energy, crimson or teal contrast, aggressive but clean",
    "trap":       "trap music atmosphere, urban night energy, stylish confidence, warm or rose neon lighting, premium street aesthetic",
    "electronic": "electronic music atmosphere, futuristic energy, teal blue neon, clean digital glow, cyber rhythm visual",
    "darkpop":    "dark pop emotional atmosphere, romantic sadness, cinematic beauty, warm golden or rose-violet color story",
    "dark":       "dark music atmosphere, dramatic shadows, intense emotional presence, single strong accent color against darkness",
    "rock":       "rock energy atmosphere, warm firelight, concert smoke, raw emotional power, dramatic rim lighting",
    "default":    "dark music atmosphere, emotional anime beauty, cinematic contrast, premium viral Shorts visual",
}

# ══════════════════════════════════════════════════════════════════════
# FACE HOOKS e BACKGROUNDS
# ══════════════════════════════════════════════════════════════════════
FACE_HOOKS = [
    "hypnotic direct eye contact, viewer feels watched",
    "one glowing tear on cheek catching neon light",
    "eyes reflecting city lights and music waveform",
    "slight dangerous smile with soft emotional eyes",
    "wide emotional eyes, lips slightly parted, instant curiosity",
    "half-lidded confident gaze, magnetic and calm",
    "vulnerable melancholic stare, beautiful sadness",
    "subtle crazy eyes but still beautiful and controlled",
    "dreamy distant gaze as if hearing the song inside her head",
    "sharp confident stare, dark queen energy",
]

BACKGROUND_VARIATIONS = [
    "rainy neon city street, wet reflections, teal and pink bokeh",
    "golden sunset skyline, cinematic clouds, warm emotional mood",
    "dark abstract stage with smoke and rim lights",
    "cyberpunk alley with blurred neon signs, clean depth",
    "night rooftop with city lights far behind, dramatic wind",
    "purple fog atmosphere with floating particles",
    "warm indoor studio with glowing music equipment blurred behind",
    "dark concert light beams, cinematic smoke, music performance feeling",
    "black void with one strong colored rim light and particle depth",
    "anime city sunset with soft bokeh, emotional ending scene",
]

MUSIC_ELEMENTS = [
    "sleek headphones around neck",
    "one earbud visible, immersed in the song",
    "small glowing waveform behind character, very subtle",
    "microphone silhouette blurred in background",
    "music visualizer particles around her, not cluttered",
    "no music prop, emotion carries the music",
    "no music prop, pure cinematic anime portrait",
]

# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT
# ══════════════════════════════════════════════════════════════════════
NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real person, 3d render, CGI, doll, plastic skin, "
    "western cartoon, simple cartoon, childish style, "
    "child, underage, loli, young girl, schoolgirl, baby face, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic, "
    "multiple people, crowd, two girls, duplicate character, "
    "text, words, logo, watermark, signature, letters, numbers, "
    "famous anime character, exact character copy, cosplay of existing character, "
    "too dark to see face, face too small, full body tiny, "
    "cluttered background, excessive effects, neon overload, "
    "overexposed bloom, muddy colors, washed out, desaturated, "
    "messy composition, no focal point, bad eyes, dead eyes"
)

GENERATION_SUFFIX = (
    ", beautiful expressive adult anime face, eyes readable at small size, "
    "first frame optimized for Shorts feed, high contrast, clear silhouette, "
    "alive cinematic frame, motion feeling, polished anime art, "
    "no text, no logo, no watermark, no extra people"
)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
def _compact(text: str, max_len: int = 3000) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[_\-]+", " ", name)
    return name.strip()


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v40.3_merge"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _weighted_palette(rng: random.Random) -> tuple[str, str]:
    total = sum(w for _, _, w in PALETTES)
    r = rng.random() * total
    acc = 0
    for name, palette, weight in PALETTES:
        acc += weight
        if r <= acc:
            return name, palette
    return PALETTES[0][0], PALETTES[0][1]


def _song_mood_boost(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite"]):
        return "haunted night emotion, lonely but powerful, eyes carrying darkness"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "angry"]):
        return "intense fire emotion, contained rage, powerful passionate stare"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry"]):
        return "dark romantic emotion, longing eyes, beautiful bittersweet mood"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return "deep lonely emotion, quiet sadness, isolated cinematic feeling"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return "fast motion energy, focused eyes, wind and speed feeling"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule"]):
        return "dominant confident aura, dark queen energy, commanding stare"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return "dreamy floating emotion, soft surreal atmosphere, ethereal eyes"
    return "emotion matching the music, magnetic presence, cinematic feeling"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — v40.3 MERGE
# ══════════════════════════════════════════════════════════════════════
def build_ai_prompt(
    style: str = "phonk",
    filename: str = "song.mp3",
    styles: Optional[list] = None,
    short_num: int = 1,
    force_warm: bool = False,
    force_teal: bool = False,
    force_crimson: bool = False,
    force_back: bool = False,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    # Seleciona waifu aleatória das 100
    char = rng.choice(TREND_WAIFUS)

    # Vista de costas (v40.2 feature)
    back_view = (
        "dramatic back view with strong neon purple rim light, "
        "long flowing hair glowing, mysterious silhouette, side profile slightly visible, "
        if force_back else ""
    )

    # Face hook e elementos visuais
    face_hook = rng.choice(FACE_HOOKS)
    background = rng.choice(BACKGROUND_VARIATIONS)
    music_element = rng.choice(MUSIC_ELEMENTS)
    song_mood = _song_mood_boost(song_name)

    # Paleta
    if force_warm:
        palette_name, palette = "warm", PALETTE_WARM
    elif force_teal:
        palette_name, palette = "teal", PALETTE_TEAL
    elif force_crimson:
        palette_name, palette = "crimson", PALETTE_CRIMSON
    else:
        palette_name, palette = _weighted_palette(rng)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])
    genre_boost = GENRE_BOOSTS.get(mapped, GENRE_BOOSTS["default"])

    prompt = (
        f"{CHANNEL_IDENTITY}, "
        f"{CORE_CHARACTER}, "
        f"character appearance: {char}, "
        f"{back_view}"
        f"face hook: {face_hook}, "
        f"{VIRAL_HOOK_LOCK}, "
        f"music element: {music_element}, "
        f"{COMPOSITION_LOCK}, "
        f"{MOTION_LOCK}, "
        f"background: {background}, "
        f"dominant palette: {palette_name}, {palette}, "
        f"genre atmosphere: {genre_boost}, "
        f"genre: {genre_text}, "
        f"song title mood: {song_name}, "
        f"song emotion: {song_mood}, "
        f"{STYLE_LOCK}, "
        f"{QUALITY_LOCK}, "
        "opening frame for viral music Short, "
        "beautiful adult anime waifu, emotional, trendy, memorable, "
        "no text, no watermark, no logo"
    )

    return _compact(prompt, max_len=3000)


def build_prompt(style: str = "phonk", seed_variant: int = 0) -> tuple[str, str]:
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
    return prompt, fake_filename


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE)
# ══════════════════════════════════════════════════════════════════════
def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN não configurado!")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3300)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model}")

                if "flux" in model:
                    model_input = {
                        **FLUX_PARAMS,
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed": random.randint(1000, 999_999),
                    }
                else:
                    model_input = {
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "width": FLUX_PARAMS["width"],
                        "height": FLUX_PARAMS["height"],
                        "num_inference_steps": FLUX_PARAMS["num_inference_steps"],
                        "guidance_scale": FLUX_PARAMS["guidance_scale"],
                        "seed": random.randint(1000, 999_999),
                    }

                payload = {"input": model_input}
                resp = requests.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers,
                    json=payload,
                    timeout=40,
                )
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                for _ in range(90):
                    time.sleep(2.5)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")
                        img = requests.get(image_url, timeout=60)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)
                        logger.info(f"✅ Imagem salva: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error", "Unknown error"))

                logger.warning("⏳ Timeout atingido")

            except Exception as e:
                logger.error(f"❌ Falha tentativa {attempt} com {model}: {e}")
                time.sleep(4)

    logger.error("❌ Todas as tentativas falharam")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONVENIÊNCIA
# ══════════════════════════════════════════════════════════════════════
def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_warm: bool = False,
    force_teal: bool = False,
    force_crimson: bool = False,
    force_back: bool = False,
) -> Optional[str]:
    prompt = build_ai_prompt(
        style=style,
        filename=f"{style}_variant_{seed_variant}.mp3",
        styles=[style],
        short_num=seed_variant + 1,
        force_warm=force_warm,
        force_teal=force_teal,
        force_crimson=force_crimson,
        force_back=force_back,
    )
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
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))
    if existing:
        return str(random.choice(existing))
    variant = random.randint(0, 99)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:02d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list,
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 3,
) -> dict:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict = {}
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
        description="AI Image Generator — DJ DARK MARK v40.3 Merge"
    )
    parser.add_argument("--style",          default="phonk",
                        help="Gênero: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename",       default="dark phonk.mp3",
                        help="Nome da música (muda o mood do prompt)")
    parser.add_argument("--short-num",      type=int, default=1,
                        help="Número do short (varia seed e waifu)")
    parser.add_argument("--output",         default="assets/background.png")
    parser.add_argument("--force-warm",     action="store_true")
    parser.add_argument("--force-teal",     action="store_true")
    parser.add_argument("--force-crimson",  action="store_true")
    parser.add_argument("--back",           action="store_true",
                        help="Força vista de costas neon (v40.2 feature)")
    parser.add_argument("--prompt-only",    action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
        force_warm=args.force_warm,
        force_teal=args.force_teal,
        force_crimson=args.force_crimson,
        force_back=args.back,
    )

    if args.prompt_only:
        print("=== PROMPT v40.3 ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
    else:
        generate_image(prompt, args.output)
