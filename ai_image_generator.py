"""
ai_image_generator.py — v4.0 ANTI-REPETIÇÃO RADICAL
=====================================================
MUDANÇAS v4.0:
- 4 CONCEITOS VISUAIS que rotacionam: personagem, cenário, abstrato, cinematográfico
- Sem mais "close de rosto genérico" como padrão
- Cada gênero tem visuais que FOGEM do óbvio
- Prompts mais curtos e diretos = melhor fidelidade do modelo
- Seed garante que mesma música nunca repete conceito
"""

import os
import re
import time
import random
import hashlib
import requests
from pathlib import Path

import replicate
import anthropic

SAVE_DIR = Path("temp")
MAX_TRIES = 3

_anthropic_client: anthropic.Anthropic | None = None


def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nao configurado.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")


# ══════════════════════════════════════════════════════════════════════
# CONCEITOS VISUAIS — 4 abordagens distintas por gênero
# Rotacionam para garantir variedade máxima no feed
# ══════════════════════════════════════════════════════════════════════

# CONCEITO A — Personagem (close/retrato)
# CONCEITO B — Cenário sem personagem dominante
# CONCEITO C — Cinematográfico / épico
# CONCEITO D — Abstrato / atmosférico

VISUAL_CONCEPTS = {

    # ── LOFI ──────────────────────────────────────────────────────────
    "lofi": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime girl at wooden desk, oversized hoodie, headphones around neck, rain hitting window behind her, warm amber desk lamp, late night, cozy and quiet",
            "palette": "deep amber warm lamp light vs cold blue moonlight from window, rich contrast, film grain",
            "mood": "peaceful concentration, 3am productivity",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "cozy bedroom at night, no character, vinyl records scattered on floor, open sketchbook, glowing amber lamp, rain on window showing blurred city lights, steam rising from forgotten mug",
            "palette": "warm honey amber interior vs cold midnight blue window, rich shadows, analog warmth",
            "mood": "inviting, quiet, the room tells the story",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "anime girl silhouette at floor-to-ceiling window, rain-soaked city below, warm room behind her cold glass in front, she is between two worlds",
            "palette": "warm interior gold vs cold neon-lit city below in rain, cinematic depth",
            "mood": "introspective, the city never sleeps but she has found peace",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "musical notes dissolving into rain drops, headphone cable becoming a river, cassette tape unwinding into autumn leaves, warm golden light from below",
            "palette": "warm amber and soft blue, dreamy and soft, analog textures",
            "mood": "nostalgia made visible, music as feeling",
        },
    ],

    # ── PHONK ─────────────────────────────────────────────────────────
    "phonk": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, sharp features, emotionless expression, black technical jacket, standing in empty parking structure at 3am, single crimson neon tube overhead",
            "palette": "blood red neon slash in absolute darkness, wet concrete reflections, zero warmth",
            "mood": "cold, controlled, dangerous",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "empty highway at night, no character, red tail lights stretching to horizon, wet asphalt mirror, single orange sodium lamp, fog at ground level",
            "palette": "deep crimson and charcoal black, neon reflections in wet road, maximum contrast",
            "mood": "midnight drive, the city as emptiness",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "low angle shot of anime woman walking away down dark tunnel, crimson neon at far end, her silhouette cutting the light, never looking back",
            "palette": "pitch black with single red vanishing point, dramatic perspective, cinematic",
            "mood": "inevitability, she owns the dark",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "808 bass wave made visible as crimson shockwave tearing through dark city, car drifting leaving red light trails, vinyl record spinning with fire edge",
            "palette": "blood red and absolute black, aggressive energy made visual",
            "mood": "raw power, bass as destruction",
        },
    ],

    # ── TRAP ──────────────────────────────────────────────────────────
    "trap": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, natural afro with gold thread, structured black coat, standing at floor-to-ceiling penthouse window, entire city grid spread below at night",
            "palette": "midnight navy and burnished gold, luxury cold, the palette of arrival",
            "mood": "composed power, the city is context",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "penthouse interior at night, no character, city lights through massive windows, gold and glass decor, expensive emptiness, champagne glass catching light",
            "palette": "deep black and champagne gold, premium contrast, luxury at rest",
            "mood": "arrived but not showing off",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "wide cinematic shot, anime woman small figure against enormous lit city skyline, she stands at rooftop edge, arms relaxed, the scale makes her larger not smaller",
            "palette": "deep navy sky and warm amber city lights below, epic vertical composition",
            "mood": "elevation, belonging at the top",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "gold chain links floating in dark space, diamond catching light from multiple directions, 808 waveform as golden architecture, luxury geometry",
            "palette": "pure black and vivid burnished gold, premium minimal",
            "mood": "the sound of money made visible",
        },
    ],

    # ── DARK ──────────────────────────────────────────────────────────
    "dark": [
        # A — Personagem
        {
            "type": "character",
            "scene": "ghostly pale anime woman, impossibly long black hair floating slightly, glowing crimson irises, slight smile that knows something terrible, moonlit ruins background",
            "palette": "near-monochrome silver and absolute black, single bleeding crimson accent, manga negative space",
            "mood": "beautiful and wrong, the smile is the warning",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "moonlit abandoned cathedral, no character, fractured stained glass casting colored shadows, overgrown with dark vines, single candle flame at altar, darkness alive",
            "palette": "cold silver moonlight and deep shadow, violet accent from broken glass, atmosphere of sacred decay",
            "mood": "beauty that has outlived its purpose",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "extreme wide shot, anime woman tiny figure at center of vast dark space, single circle of violet light surrounding her, the void pressing in from all sides",
            "palette": "absolute black and vivid absinthe-violet circle of light, dramatic scale contrast",
            "mood": "the light she carries is the only light",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "dark melody visualized as black ink spreading through water, crimson notes bleeding at edges, void with heartbeat rhythm made visible as concentric dark rings",
            "palette": "black ink and deep crimson, water texture, darkness with pulse",
            "mood": "darkness is not empty it is full",
        },
    ],

    # ── ELECTRONIC ────────────────────────────────────────────────────
    "electronic": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, electric blue hair geometric bob, UV-reactive face art, arms raised at festival, laser beams cutting fog above crowd, ocean of phone lights behind her",
            "palette": "electric cyan vs deep magenta, maximum saturation, rave light as sculpture",
            "mood": "ecstatic, she is the drop",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "empty dance floor from above, no character, laser grid ceiling, fog at ankle level, colorful light beams cutting through haze, the venue before it fills",
            "palette": "UV purple floor, cyan and magenta laser grid, deep black space, fluorescent geometry",
            "mood": "the space that holds the ritual",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "rear view from stage level, anime woman DJ facing enormous crowd, massive LED wall exploding with abstract visuals behind her, her silhouette the only dark thing",
            "palette": "silhouette vs rainbow LED explosion, chromatic aberration at edges, scale overwhelming",
            "mood": "she controls the frequency of thousands",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "sound wave architecture, bass frequencies as glowing blue columns, treble as electric sparks, the drop visualized as supernova of cyan and magenta light",
            "palette": "electric cyan and vivid magenta on black, maximum saturation, frequency as art",
            "mood": "music made visible and physical",
        },
    ],

    # ── ROCK ──────────────────────────────────────────────────────────
    "rock": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, fiery copper pixie cut, leather jacket with patches, mid-scream into mic, harsh amber stage light from above, crowd hands visible below as sea",
            "palette": "volcanic amber stage light vs pitch black, raw energy in light, no softness",
            "mood": "catharsis, the scream is the truth",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "empty concert venue, no character, stage lit with warm amber flood, crowd barrier, drum kit and guitar stand alone under light, the stage before chaos",
            "palette": "warm stage amber and deep venue shadow, concrete and metal textures",
            "mood": "the quiet before it all starts",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "wide shot, anime woman silhouette backlit by massive wall of stage lights, hair wild in wind, crowd silhouette at her feet as dark mass, arms open",
            "palette": "pure white concert lights creating halo vs absolute crowd darkness, binary power",
            "mood": "she owns the room the room owns her",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "guitar string vibration made visible as amber shockwave, pick strike creating ripple of distortion, vinyl record cracked and burning at edge, amplifier grill glowing warm",
            "palette": "deep amber and raw black, electric energy as visual texture",
            "mood": "the sound that changes something",
        },
    ],

    # ── METAL ─────────────────────────────────────────────────────────
    "metal": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, impossibly long dark hair with blood-red underlayer, warrior armor-influenced outfit, standing on cliff edge, storm with multiple lightning strikes surrounding her",
            "palette": "volcanic deep orange and absolute char-black, lightning white cutting storm purple sky",
            "mood": "the storm obeys her or fears her",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "ancient stone fortress in storm, no character, lightning illuminating every crack, fire torches bending in wind, drawbridge chains, epic scale of old power",
            "palette": "cold lightning white and storm-black, amber torch fire as only warmth, stone grey textures",
            "mood": "architecture of endurance",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "extreme wide, anime woman tiny figure atop highest tower, simultaneous lightning strikes in circle around her, the scale of natural power vs human will",
            "palette": "electric white lightning on purple-black storm sky, the single human figure as contrast",
            "mood": "she chose to stand here",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "breakdown visualized as tectonic plates cracking, guitar riff as shockwave shattering stone, double bass drum as earthquake ripple, fire erupting from cracks in dark ground",
            "palette": "volcanic crimson and charcoal black, destruction as beauty",
            "mood": "heavy music made geological",
        },
    ],

    # ── INDIE ─────────────────────────────────────────────────────────
    "indie": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, honey-blonde waves genuinely uncurated, vintage slip dress, sitting in golden field at magic hour, looking directly at viewer with something true",
            "palette": "deep honey-amber of last golden hour, long shadows, natural beauty at maximum",
            "mood": "absolutely herself, the authenticity is the point",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "abandoned railway at sunset, no character, wildflowers growing between tracks, golden hour light through tall grass, warm and forgotten and beautiful",
            "palette": "rich warm honey and deep burgundy, autumn tones, overgrown beauty",
            "mood": "the world keeps being beautiful without asking permission",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "medium shot from passenger seat, anime woman driving at golden hour, late afternoon light through windshield catching her profile perfectly, movement implied",
            "palette": "deep orange amber through glass, warm grain, film photography quality",
            "mood": "going somewhere or leaving something",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "cassette tape unspooling into wildflower field, music notes becoming fireflies at dusk, vinyl record growing as tree ring cross-section, warm golden light through everything",
            "palette": "honey gold and deep green, warm grain, analog nostalgia",
            "mood": "music grows in you like something living",
        },
    ],

    # ── CINEMATIC ─────────────────────────────────────────────────────
    "cinematic": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, long dark hair in wind, dramatic long coat, standing at edge of impossible cliff, vast storm-breaking sky behind, single ray of amber light through dark clouds",
            "palette": "desaturated environment vs single vivid golden beam, deep rich shadows, chiaroscuro at scale",
            "mood": "protagonist at the moment of decision",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "fog-filled valley at dawn, no character, ancient stone bridge, single lantern at center, mountain peaks emerging from mist, the world before it wakes",
            "palette": "cold blue-grey fog vs warm golden lantern, epic atmospheric depth, layers of mist",
            "mood": "the world holds its breath",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "perfect widescreen composition, anime woman at end of long architectural corridor, single vanishing point, storm light from window at far end, her silhouette sharp against light",
            "palette": "teal and orange color science, premium cinematography grade, anamorphic lens quality",
            "mood": "intention given visual form",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "film frame borders visible, multiple exposures of the same scene at different moments, time as visual layer, rain and light as abstract architecture",
            "palette": "vivid teal shadows and warm amber highlights, film grain, cinematic color science",
            "mood": "memory and moment as the same thing",
        },
    ],

    # ── FUNK ──────────────────────────────────────────────────────────
    "funk": [
        # A — Personagem
        {
            "type": "character",
            "scene": "anime woman, voluminous natural afro with gold pins, warm deep skin, wide genuine smile, colorful vintage-inspired outfit, caught mid-dance in warm-lit venue",
            "palette": "deep warm orange and rich red-brown of late night venue, soulful heat, colors that feel alive",
            "mood": "pure joy without performance, the groove took over",
        },
        # B — Cenário
        {
            "type": "scene",
            "scene": "record store interior, no character, warm afternoon light through dusty window, vinyl records everywhere, old speakers, plant growing through shelf crack, alive and loved",
            "palette": "deep gold and rich mahogany, soulful warmth, texture of old wood and good music",
            "mood": "the place where the music lives",
        },
        # C — Cinematográfico
        {
            "type": "cinematic",
            "scene": "medium shot, anime woman at rooftop at sunset, city warm below, natural expression between songs, exhale and real smile, the moment between performances",
            "palette": "vivid coral sunset and deep warm teal, saturated alive, the color of music that moves you",
            "mood": "the real person under the performer",
        },
        # D — Abstrato
        {
            "type": "abstract",
            "scene": "bass groove visualized as warm concentric rings in water, vinyl record spinning with rainbow light, brass instrument bell made of golden light, rhythm as architecture",
            "palette": "electric yellow and deep purple, vivid as celebration feels, warm and alive",
            "mood": "the groove is a physical place",
        },
    ],

    # ── DEFAULT ───────────────────────────────────────────────────────
    "default": [
        {
            "type": "character",
            "scene": "anime woman, striking distinctive features, confident presence, dramatic lighting, atmospheric environment with depth and story",
            "palette": "vivid neon purple and deep black, premium saturation, cinematic contrast",
            "mood": "presence that stops the scroll",
        },
        {
            "type": "scene",
            "scene": "atmospheric urban environment at night, no character, neon lights reflecting in wet streets, layers of depth and color, the city as emotional space",
            "palette": "deep midnight with vivid colored light sources, rich contrast, wet reflections",
            "mood": "the city after midnight, beauty without audience",
        },
        {
            "type": "cinematic",
            "scene": "wide cinematic shot, single figure against vast dramatic environment, epic scale, premium color grading, anamorphic quality",
            "palette": "cold electric blue and warm gold, cinematic contrast, premium visual language",
            "mood": "the feeling of the music made visual",
        },
        {
            "type": "abstract",
            "scene": "sound wave made visible as vivid light sculpture, music frequency as architectural form, abstract beauty with emotional resonance",
            "palette": "vivid amber and deep indigo, warm cold contrast, cinematic quality",
            "mood": "music that you can see",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════
# QUALIDADE & NEGATIVO
# ══════════════════════════════════════════════════════════════════════

QUALITY_TAGS = (
    "masterpiece, best quality, ultra-detailed anime illustration, "
    "professional anime key visual, perfect cel shading, clean sharp lineart, "
    "ultra-vivid saturated colors, maximum color depth, rich vivid hues, "
    "deep blacks and luminous highlights, cinematic composition, razor-sharp focus, "
    "richly detailed background with atmospheric depth, volumetric lighting, "
    "dynamic light and shadow interplay, studio-level production quality, "
    "trending on pixiv, ArtStation quality, 9:16 vertical format, "
    "scroll-stopping visual impact, premium anime visual novel quality"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, 3D render, CGI, real human face, "
    "text, watermark, signature, logo, border, frame, "
    "multiple characters, extra limbs, deformed hands, fused fingers, bad anatomy, "
    "distorted face, wrong proportions, malformed body parts, "
    "child appearance, young teen face, childlike proportions, "
    "explicit nudity, fetish content, nsfw, cleavage, revealing clothing, "
    "blurry, muddy colors, flat boring lighting, desaturated washed-out colors, "
    "generic gradient background, plain studio void, empty background, "
    "airbrushed plastic skin, uncanny valley, "
    "Western cartoon, Pixar style, chibi, super deformed, "
    "sketch only, unfinished lineart, low quality, "
    "generic anime waifu, bland background, same composition as always, "
    "repetitive, seen before, boring, forgettable"
)


# ══════════════════════════════════════════════════════════════════════
# SEED DETERMINÍSTICA
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v7"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick_concept(style: str, filename: str, short_num: int) -> dict:
    """
    Seleciona conceito visual com rotação garantida.
    short_num 1,2,3,4 = conceitos A,B,C,D em ordem determinística.
    Nunca repete o mesmo conceito para a mesma música.
    """
    concepts = VISUAL_CONCEPTS.get(style, VISUAL_CONCEPTS["default"])
    # Rotação por short_num garante variedade sequencial
    concept_idx = (short_num - 1) % len(concepts)
    return concepts[concept_idx]


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled"


def _compact(text: str, max_chars: int = 1600) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# CONSTRUÇÃO DO PROMPT
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)
    concept   = _pick_concept(style, filename, short_num)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                concept=concept,
                short_num=short_num,
            )
        except Exception as e:
            print(f"  [Claude] Prompt falhou: {e} — usando fallback")

    return _static_prompt(concept)


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    concept: dict,
    short_num: int,
) -> str:
    client = get_anthropic_client()

    concept_type_instructions = {
        "character": "Focus on ONE specific character with distinctive appearance. Background must be rich and detailed, not just backdrop.",
        "scene":     "NO dominant character. The environment IS the subject. Every detail of the scene tells the story.",
        "cinematic": "Epic scale and composition. If character present, she is small vs environment. Widescreen feel in vertical format.",
        "abstract":  "Music visualized as physical reality. No literal people. Sound, emotion, and energy made into visual form.",
    }

    concept_instruction = concept_type_instructions.get(concept["type"], "")

    system = (
        "You are an elite anime art director for YouTube Shorts thumbnails. "
        "Your images stop people mid-scroll because they are UNEXPECTED and SPECIFIC.\n\n"
        "ABSOLUTE RULES:\n"
        "1. NEVER generic close-up faces as default — vary the concept type\n"
        "2. ULTRA-VIVID colors, deep blacks, luminous highlights — never flat\n"
        "3. Specific lighting with location, color, intensity\n"
        "4. Background tells a story — never a gradient void\n"
        "5. The image must FEEL like the music, not just decorate it\n"
        "6. 9:16 vertical format, platform-safe, non-sexualized\n"
        "7. Output ONLY the final prompt: comma-separated, 90-120 words, no preamble"
    )

    user = f"""Create a scroll-stopping anime illustration prompt.

SONG: "{song_name}"
GENRE: {style} | ALL: {all_styles}
SHORT #: {short_num}

VISUAL CONCEPT TYPE: {concept["type"].upper()}
{concept_instruction}

SCENE FOUNDATION:
{concept["scene"]}

COLOR PALETTE (execute exactly):
{concept["palette"]}

EMOTIONAL MOOD:
{concept["mood"]}

CRITICAL: The image must emotionally connect to "{song_name}". 
Let the song title influence one specific visual detail.
90-120 words, comma-separated only, no explanation."""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=350,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw  = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    concept_label = concept["type"].upper()
    print(f"  [Claude] Prompt gerado ({len(full)} chars) — short #{short_num} [{concept_label}]")
    return _compact(full)


def _static_prompt(concept: dict) -> str:
    prompt = (
        f"masterpiece, best quality, ultra-detailed premium anime illustration, "
        f"{concept['scene']}, "
        f"color palette: {concept['palette']}, "
        f"mood: {concept['mood']}, "
        f"ultra-vivid saturated colors, deep rich blacks, luminous highlights, "
        f"cinematic volumetric lighting, atmospheric depth, richly detailed, "
        f"clean sharp anime lineart, perfect cel shading, "
        f"9:16 vertical composition, scroll-stopping visual impact, pixiv quality"
    )
    return _compact(prompt)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO VIA REPLICATE
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 35,
        "aspect_ratio": "9:16",
        "guidance": 4.5,
        "output_format": "png",
        "output_quality": 98,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 98,
        "go_fast": True,
        "disable_safety_checker": True,
    },
}


def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] Token não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt
        + ", anime illustration style, NOT photorealistic, NOT 3D render, "
        + "ultra-vibrant saturated colors, deep rich shadows, luminous vivid highlights, "
        + "sharp clean lineart, premium anime key visual quality, "
        + "specific distinctive visual, NOT generic, NOT repetitive"
    )

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
                    print("  [Replicate] URL não encontrada")
                    continue
                saved = _download_image(url, output_path)
                if saved:
                    print(f"  [Replicate] Salvo: {saved}")
                    return saved
            except Exception as e:
                wait = 2 ** attempt
                print(f"  [Replicate] Erro: {e}. Aguardando {wait}s...")
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
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()

        if not output_path:
            output_path = str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        size = os.path.getsize(output_path)
        if size < 80_000:
            print(f"  [Replicate] Imagem muito pequena ({size} bytes), descartando")
            os.remove(output_path)
            return None

        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
