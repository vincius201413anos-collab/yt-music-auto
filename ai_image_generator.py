"""
ai_image_generator.py — Gerador de imagens IA de alta qualidade.
Versão 2.0 — Personagens cinematográficas ultra-específicas por gênero.
Cada estilo gera uma garota com estética, ambiente e mood únicos.
"""

import os
import re
import time
import random
import requests
from pathlib import Path

import replicate
import anthropic

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

SAVE_DIR = Path("temp")
MAX_TRIES = 3

# Singleton do cliente Anthropic — instancia uma só vez
_anthropic_client: anthropic.Anthropic | None = None

def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurado.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client

def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")


# ══════════════════════════════════════════════════════════════════════
# PERFIS VISUAIS CINEMATOGRÁFICOS POR GÊNERO
# Cada perfil define: personagem + ambiente + paleta + elementos únicos
# ══════════════════════════════════════════════════════════════════════

GENRE_PROFILES = {

    # ── LOFI ────────────────────────────────────────────────────────
    "lofi": {
        "character": (
            "one beautiful anime girl, soft melancholic expression, big dreamy eyes, "
            "oversized hoodie or cozy knit sweater, messy bun or loose hair, "
            "wearing large over-ear headphones, chin resting on hand, "
            "peaceful and slightly tired look, warm skin tone, detailed soft face"
        ),
        "environment": (
            "cozy bedroom at night, warm desk lamp casting amber light, "
            "rain drops on window glass, city lights blurred in background, "
            "scattered notebooks and pencils, a steaming mug of coffee, "
            "fairy lights strung along shelves, plants on windowsill"
        ),
        "palette": "warm amber and deep blue, soft candlelight, purple night sky",
        "mood": "calm, nostalgic, intimate, studying late at night",
        "unique_elements": "floating musical notes, soft bokeh rain outside, moonlight",
    },

    # ── INDIE ───────────────────────────────────────────────────────
    "indie": {
        "character": (
            "one beautiful anime girl, wistful emotional expression, slightly sad eyes, "
            "vintage band tee or flowy blouse, light freckles, natural soft makeup, "
            "long wavy hair blowing gently, small gold earrings, "
            "holding a vinyl record or sitting by a window"
        ),
        "environment": (
            "rooftop at golden hour, warm orange sunset behind city silhouette, "
            "worn brick walls covered in posters, string lights, "
            "wooden crates and vintage speakers, polaroid photos pinned nearby, "
            "warm wind making hair flutter"
        ),
        "palette": "golden amber, dusty rose, warm film grain overlay, faded vintage tones",
        "mood": "emotional, nostalgic, free, bittersweet",
        "unique_elements": "film grain texture, Polaroid photos, sunset lens flare",
    },

    # ── ROCK ────────────────────────────────────────────────────────
    "rock": {
        "character": (
            "one beautiful anime girl, fierce rebellious expression, sharp piercing eyes, "
            "ripped band tee, leather jacket with pins and patches, "
            "short edgy haircut or wild dark hair with streaks, "
            "heavy boots, fingerless gloves, holding electric guitar, "
            "confident powerful stance"
        ),
        "environment": (
            "dramatic concert stage with intense spotlights, smoke machines, "
            "electric guitar in foreground, amplifiers behind, "
            "crowd silhouettes below, dramatic back-lighting, "
            "sparks and light streaks"
        ),
        "palette": "deep orange and electric blue stage lights, high contrast shadows, vivid highlights",
        "mood": "raw power, rebellion, adrenaline, electric energy",
        "unique_elements": "guitar sparks, stage smoke, crowd energy, dramatic rim lighting",
    },

    # ── METAL ───────────────────────────────────────────────────────
    "metal": {
        "character": (
            "one beautiful gothic anime girl, intense red glowing eyes, "
            "elegant black corset dress with dark lace details, "
            "long flowing dark hair with red highlights, pale skin, "
            "dark lipstick, ornate gothic jewelry, chains around wrists, "
            "dramatic powerful presence, standing in wind"
        ),
        "environment": (
            "dark epic fantasy landscape, storm clouds with red lightning, "
            "ancient castle ruins in distance, glowing embers floating upward, "
            "chains and black ravens in background, dramatic red and black sky, "
            "fog rolling across stone floor"
        ),
        "palette": "deep crimson red, pitch black, glowing ember orange, silver highlights",
        "mood": "dark power, gothic elegance, epic, intense, mythic",
        "unique_elements": "glowing runes, floating chains, black ravens, ember particles",
    },

    # ── PHONK ───────────────────────────────────────────────────────
    "phonk": {
        "character": (
            "one beautiful anime girl, cool intimidating expression, half-lidded eyes, "
            "oversized hoodie with kanji or logo, cap tilted low, "
            "dark streetwear aesthetic, tattoo on neck, "
            "leaning against a car, hands in pockets, "
            "red and black color scheme outfit"
        ),
        "environment": (
            "underground parking lot at 3am, red neon lights reflecting on wet concrete, "
            "sports car with headlights on, cigarette smoke drifting, "
            "graffiti on walls, city highway visible in distance, "
            "dramatic single overhead light"
        ),
        "palette": "deep red neon, pitch black, concrete grey, magenta highlights",
        "mood": "aggressive, cool, underground, night drive energy",
        "unique_elements": "wet concrete reflections, neon signs, car headlights, smoke wisps",
    },

    # ── TRAP ────────────────────────────────────────────────────────
    "trap": {
        "character": (
            "one beautiful anime girl, confident luxury expression, stylish makeup, "
            "designer streetwear with gold jewelry, long styled nails, "
            "high-end sneakers, sleek straight hair or braids, "
            "holding a phone, premium aesthetic, boss energy"
        ),
        "environment": (
            "penthouse rooftop at night, luxury city skyline below, "
            "swimming pool with teal light reflections, gold and chrome decor, "
            "premium speakers, moody dramatic lighting, "
            "helicopter lights in distance"
        ),
        "palette": "teal and gold, deep purple night sky, chrome reflections, premium black",
        "mood": "wealth, ambition, luxury, power, cool confidence",
        "unique_elements": "city light reflections on water, gold accents, neon skyline glow",
    },

    # ── ELECTRONIC / EDM ────────────────────────────────────────────
    "electronic": {
        "character": (
            "one beautiful futuristic anime girl, glowing neon tattoos on skin, "
            "holographic visor or LED headphones, futuristic outfit with light-up details, "
            "silver or pastel hair, wide excited eyes reflecting laser lights, "
            "arms raised, dancing, euphoric expression"
        ),
        "environment": (
            "massive festival mainstage at night, laser beams cutting through darkness, "
            "LED screen visuals behind, crowd of thousands with glowsticks, "
            "holographic particles floating, fog machines, "
            "electric energy in the air"
        ),
        "palette": "electric blue, neon purple, cyan, vivid magenta lasers, dark night backdrop",
        "mood": "euphoria, energy, futuristic, transcendent, peak moment",
        "unique_elements": "laser grid patterns, holographic particles, crowd glow, bass-wave distortion",
    },

    # ── DARK AMBIENT ────────────────────────────────────────────────
    "dark": {
        "character": (
            "one beautiful mysterious anime girl, half face hidden in shadow, "
            "flowing dark cloak or elegant black dress, "
            "pale ghostly skin, glowing violet or silver eyes, "
            "dark hair with ethereal white streaks, "
            "standing alone, melancholic powerful aura"
        ),
        "environment": (
            "moonlit abandoned cathedral interior, broken stained glass windows, "
            "moonbeams cutting through dust, overgrown with dark vines, "
            "candles flickering on stone floor, "
            "mist rolling in from outside, crow perched on ruined arch"
        ),
        "palette": "deep indigo, silver moonlight, cold teal mist, near-black shadows",
        "mood": "mysterious, haunting, ethereal, solitary, poetic darkness",
        "unique_elements": "moonlight shafts, dust motes, vine details, flickering candles",
    },

    # ── POP ─────────────────────────────────────────────────────────
    "pop": {
        "character": (
            "one beautiful idol anime girl, bright radiant smile, sparkling eyes, "
            "colorful pastel outfit with accessories, cute hair accessories, "
            "soft blush makeup, heart gesture or peace sign, "
            "cheerful confident stance, kawaii aesthetic"
        ),
        "environment": (
            "dreamy pastel studio with neon signs saying music notes, "
            "confetti and sakura petals floating, "
            "ring lights and cute props, colorful streamers, "
            "soft cloud backdrop, glitter everywhere"
        ),
        "palette": "soft pink, lavender, sky blue, sparkle gold, pastel rainbow accents",
        "mood": "joyful, energetic, fresh, youthful, feel-good",
        "unique_elements": "confetti burst, sparkle particles, heart shapes, pastel bokeh",
    },

    # ── FUNK ────────────────────────────────────────────────────────
    "funk": {
        "character": (
            "one beautiful anime girl, big vibrant smile, dancing pose, "
            "colorful retro 70s-inspired outfit with flared pants, "
            "afro or big curly hair with colorful scrunchie, "
            "platform shoes, gold hoop earrings, "
            "full of joy and groove energy"
        ),
        "environment": (
            "retro-futuristic disco hall, mirror ball casting light spots everywhere, "
            "neon dance floor with glowing tiles, vintage speakers stacked high, "
            "palm trees with lights wrapped around them, "
            "warm orange and yellow party atmosphere"
        ),
        "palette": "warm orange, vibrant yellow, retro gold, disco mirror reflections",
        "mood": "joyful, groovy, party energy, feel-good, playful",
        "unique_elements": "disco ball light spots, neon dance floor tiles, confetti, warm glow",
    },

    # ── CINEMATIC / ORCHESTRAL ───────────────────────────────────────
    "cinematic": {
        "character": (
            "one beautiful anime girl, intense determined expression, "
            "elegant warrior or adventurer attire, flowing cape, "
            "hair blowing in heroic wind, emotional tear on cheek, "
            "strong powerful pose, hand on chest or reaching forward"
        ),
        "environment": (
            "epic landscape at dramatic sunset, towering mountains and storm clouds, "
            "god rays breaking through clouds, ancient temple ruins, "
            "hero standing at edge of cliff overlooking vast world, "
            "magical particles floating around her"
        ),
        "palette": "teal and orange cinematic grade, dramatic god rays, golden-hour warmth",
        "mood": "epic, emotional, heroic, cinematic scale, beautiful sadness",
        "unique_elements": "god rays, floating magical particles, epic scale, cinematic lens flare",
    },

    # ── SERTANEJO ───────────────────────────────────────────────────
    "sertanejo": {
        "character": (
            "one beautiful anime girl, warm joyful smile, "
            "stylish country-chic outfit with boots and hat, "
            "long wavy chestnut hair, natural sun-kissed look, "
            "sitting on a wooden fence or horseback, "
            "casual confident warmth"
        ),
        "environment": (
            "vast Brazilian countryside at golden hour, open fields and rolling hills, "
            "warm sunset painting the sky orange and pink, "
            "fireflies beginning to appear, wooden barn in distance, "
            "tall grass swaying in breeze"
        ),
        "palette": "warm golden hour, earthy orange, sky rose, green fields",
        "mood": "warm, romantic, nostalgic, open-air freedom, soulful",
        "unique_elements": "fireflies, golden grass, sunset color gradient, rural Brazilian landscape",
    },

    # ── MPB ─────────────────────────────────────────────────────────
    "mpb": {
        "character": (
            "one beautiful anime girl, thoughtful soulful expression, "
            "natural wavy hair, minimal elegant style, "
            "playing acoustic guitar or holding microphone, "
            "warm brown skin tone, authentic emotional presence, "
            "artistic and poetic vibe"
        ),
        "environment": (
            "intimate jazz bar at night, warm candlelight on small round tables, "
            "vintage microphone stand, acoustic guitar on stage, "
            "soft spotlight, wooden floor, bossa nova atmosphere, "
            "audience silhouettes in warm dim light"
        ),
        "palette": "warm amber, deep brown, candlelight gold, soft shadows",
        "mood": "soulful, intimate, poetic, warm Brazillian soul",
        "unique_elements": "candlelight flicker, vintage mic, acoustic warmth, soft spotlight",
    },

    # ── DEFAULT ─────────────────────────────────────────────────────
    "default": {
        "character": (
            "one beautiful anime girl, expressive emotional eyes, "
            "stylish contemporary look, detailed face, "
            "listening to music with headphones, captivating presence"
        ),
        "environment": (
            "dramatic music-inspired atmosphere, cinematic lighting, "
            "premium aesthetic environment matching the song's mood"
        ),
        "palette": "vivid dramatic colors, high contrast, cinematic grade",
        "mood": "emotional, captivating, scroll-stopping",
        "unique_elements": "musical atmosphere, premium visual quality",
    },
}

# Sufixo de qualidade universal — aplicado em TODOS os prompts
QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra-detailed, sharp focus, "
    "anime illustration style, 9:16 vertical composition, centered subject, "
    "beautiful detailed eyes, cinematic lighting, vivid saturated colors, "
    "high contrast, professional digital art, "
    "no text, no watermark, no extra people, single subject only"
)

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, "
    "split image, collage, multiple people, duplicate person, two girls, "
    "extra arms, extra fingers, deformed hands, bad anatomy, "
    "ugly face, blurry, muddy, dull, flat lighting, "
    "underexposed, overexposed, low quality, stock photo, "
    "realistic photo, elderly, child, "
    "sexualized pose, revealing outfit, bikini, cleavage focus, "
    "generic background, boring composition"
)

# Variações de cena para evitar repetição entre shorts da mesma música
SCENE_VARIANTS = {
    "lofi":       ["late night studying", "rainy window mood", "3am city lights", "soft lamplight corner", "pre-dawn quiet"],
    "indie":      ["golden hour rooftop", "film photo moment", "sunset window", "vintage afternoon", "bittersweet memory"],
    "rock":       ["concert climax", "backstage intensity", "solo guitar moment", "crowd energy peak", "electric storm"],
    "metal":      ["dark storm ritual", "ember and chain chaos", "gothic throne scene", "ravens in red sky", "power awakening"],
    "phonk":      ["3am parking lot", "night highway drift", "red neon alley", "underground scene", "cold concrete night"],
    "trap":       ["penthouse night view", "luxury poolside", "midnight city hustle", "gold and chrome moment", "skyline boss"],
    "electronic": ["festival drop moment", "laser rave peak", "holographic future", "neon crowd wave", "mainstage euphoria"],
    "dark":       ["moonlit cathedral", "abandoned church fog", "midnight forest", "silver moonbeam", "solitary darkness"],
    "pop":        ["sparkle confetti burst", "idol stage debut", "pastel dream world", "glitter rain moment", "kawaii peak"],
    "funk":       ["disco ball spotlight", "retro dance floor", "groove party peak", "warm neon party", "funky golden glow"],
    "cinematic":  ["epic cliff reveal", "heroic wind moment", "god rays emergence", "emotional skyline", "legendary stance"],
    "sertanejo":  ["golden sunset field", "countryside magic hour", "firefly night", "open sky freedom", "warm farm glow"],
    "mpb":        ["candlelight concert", "bossa nova night", "soulful spotlight", "intimate acoustic", "warm jazz bar"],
    "default":    ["premium music mood", "dramatic light scene", "vivid cinematic", "emotional atmosphere", "scroll-stopping visual"],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _clean_song_name(filename: str) -> str:
    song_name = Path(filename).stem
    song_name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", song_name)
    song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()
    return song_name or "Untitled Track"

def _pick_variant(style: str, short_num: int) -> str:
    pool = SCENE_VARIANTS.get(style, SCENE_VARIANTS["default"])
    index = max(0, (short_num - 1) % len(pool))
    return pool[index]

def _compact_prompt(text: str, max_chars: int = 950) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list[str], short_num: int = 1) -> str:
    """
    Gera prompt cinematográfico ultra-específico para o gênero musical.
    Garante personagem feminina única e ambiente temático coerente.
    """
    song_name = _clean_song_name(filename)
    profile = GENRE_PROFILES.get(style, GENRE_PROFILES["default"])
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()
    scene_variant = _pick_variant(style, short_num)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                profile=profile,
                scene_variant=scene_variant,
            )
        except Exception as e:
            print(f"  [Claude] Falha ao gerar prompt: {e} — usando fallback estático")

    return _static_prompt(
        song_name=song_name,
        profile=profile,
        scene_variant=scene_variant,
    )


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    profile: dict,
    scene_variant: str,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are a master visual director for a premium YouTube music Shorts channel. "
        "You create breathtaking Flux image prompts that are cinematic, scroll-stopping, and emotionally powerful. "
        "Each prompt must feature exactly ONE beautiful anime-style girl as the central subject. "
        "She must embody the genre's aesthetic — her look, expression, outfit and environment must "
        "feel authentically connected to the music style. "
        "The image must feel like a still from a premium anime music video, not a generic illustration. "
        "Output ONLY the prompt in English — comma-separated visual elements, no explanation, no quotes."
    )

    user = f"""Create a cinematic Flux prompt for a vertical YouTube music Short.

Song: "{song_name}"
Genre: {style} ({all_styles})
Scene variation: {scene_variant}

Character direction:
{profile['character']}

Environment:
{profile['environment']}

Color palette: {profile['palette']}
Emotional mood: {profile['mood']}
Signature visual elements: {profile['unique_elements']}

Rules:
- Exactly ONE female subject — she IS the visual story
- Her aesthetic must match {style} music authentically
- Environment must complement and frame her perfectly
- Use the color palette to create visual identity
- Include the unique elements to add richness and detail
- Composition: subject centered and prominent in 9:16 vertical frame
- Lighting must be dramatic and intentional — not flat
- The final image must make someone STOP scrolling
- 60–100 words max, comma-separated
- No text, no watermark, no extra people"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=250,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    prompt = resp.content[0].text.strip().strip('"').strip("'")
    # Garante o sufixo de qualidade
    full_prompt = f"{prompt}, {QUALITY_SUFFIX}"
    full_prompt = _compact_prompt(full_prompt)
    print(f"  [Claude] Prompt gerado ({len(full_prompt)} chars)")
    return full_prompt


def _static_prompt(song_name: str, profile: dict, scene_variant: str) -> str:
    """Fallback de alta qualidade — usa os perfis cinematográficos detalhados."""
    templates = [
        (
            f"{profile['character']}, {profile['environment']}, "
            f"{scene_variant}, {profile['palette']}, "
            f"inspired by '{song_name}', {profile['unique_elements']}, "
            f"{QUALITY_SUFFIX}"
        ),
        (
            f"cinematic anime music visual for '{song_name}', "
            f"{profile['character']}, {profile['environment']}, "
            f"{profile['mood']}, {profile['palette']}, "
            f"{profile['unique_elements']}, {QUALITY_SUFFIX}"
        ),
        (
            f"premium YouTube Shorts visual, {scene_variant}, "
            f"{profile['character']}, {profile['environment']}, "
            f"{profile['palette']}, {profile['mood']}, "
            f"{profile['unique_elements']}, {QUALITY_SUFFIX}"
        ),
    ]
    return _compact_prompt(random.choice(templates))


# ══════════════════════════════════════════════════════════════════════
# REPLICATE — GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

# flux-dev PRIMEIRO para qualidade premium, schnell como fallback rápido
REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 28,
        "aspect_ratio": "9:16",
        "guidance": 3.5,
        "output_format": "png",
        "output_quality": 95,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 95,
        "go_fast": True,
        "disable_safety_checker": True,
    },
}


def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] REPLICATE_API_TOKEN não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Adiciona reforço de qualidade no prompt final enviado ao modelo
    quality_reinforcement = (
        ", anime-style, one beautiful female character, "
        "detailed face, premium cinematic composition, "
        "vivid colors, dramatic lighting, sharp focus, masterpiece"
    )
    full_prompt = _compact_prompt(prompt + quality_reinforcement)

    for model in REPLICATE_MODELS:
        params = {**MODEL_PARAMS.get(model, {}), "prompt": full_prompt}
        if "flux-dev" in model:
            params["negative_prompt"] = NEGATIVE_PROMPT

        for attempt in range(1, MAX_TRIES + 1):
            try:
                model_short = model.split("/")[-1]
                print(f"  [Replicate] Tentativa {attempt}/{MAX_TRIES} — {model_short}")
                output = replicate.run(model, input=params)
                url = _extract_url(output)
                if not url:
                    print("  [Replicate] URL não encontrada na resposta.")
                    continue
                saved = _download_image(url, output_path)
                if saved:
                    print(f"  [Replicate] Imagem salva: {saved}")
                    return saved
            except Exception as e:
                wait = 2 ** attempt
                print(f"  [Replicate] Erro ({e}). Aguardando {wait}s…")
                time.sleep(wait)

    print("  [Replicate] Todas as tentativas falharam.")
    return None


def _extract_url(output) -> str | None:
    if isinstance(output, str) and output.startswith("http"):
        return output
    if isinstance(output, list) and output:
        first = output[0]
        if hasattr(first, "url"):
            return str(first.url)
        if isinstance(first, str) and first.startswith("http"):
            return first
    try:
        for item in output:
            if hasattr(item, "url"):
                return str(item.url)
            if isinstance(item, str) and item.startswith("http"):
                return item
    except Exception:
        pass
    return None


def _download_image(url: str, output_path: str | None = None) -> str | None:
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        if not output_path:
            ts = int(time.time())
            output_path = str(SAVE_DIR / f"ai_bg_{ts}.png")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        size = os.path.getsize(output_path)
        if size < 50_000:
            print(f"  [Replicate] Imagem suspeita: {size} bytes — descartando.")
            os.remove(output_path)
            return None

        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
