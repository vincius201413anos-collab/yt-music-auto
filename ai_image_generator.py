"""
ai_image_generator.py — v5.0 ANIME DARK CYBERPUNK EDITION
===========================================================
MUDANÇAS v5.0:
- Todos os gêneros agora geram imagens no estilo ANIME DARK CYBERPUNK
- Paleta unificada: vermelho sangue + roxo neon + preto absoluto
- 4 CONCEITOS VISUAIS rotacionando: personagem, cenário, cinematográfico, abstrato
- Sem personagem fixa — teste A/B automático por short_num para descobrir qual performa mais
- Cada conceito tem um label para rastrear no analytics do YouTube
- Canal: DJ darkMark | Phonk / Trap / Dubstep
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
# ANIME DARK CYBERPUNK — 4 CONCEITOS VISUAIS
#
# Todos os gêneros usam essa temática centralizada.
# Rotação por short_num: 1=A, 2=B, 3=C, 4=D
# Rastreie no YouTube Analytics qual conceito gera mais views.
#
# CONCEITO A — PERSONAGEM: anime girl, close/retrato, rosto + expressão
# CONCEITO B — CENÁRIO: ambiente sem personagem dominante
# CONCEITO C — CINEMATOGRÁFICO: escala épica, silhueta vs ambiente
# CONCEITO D — ABSTRATO: música visualizada como forma visual
# ══════════════════════════════════════════════════════════════════════

VISUAL_CONCEPTS = {

    # ── PHONK ─────────────────────────────────────────────────────────
    "phonk": [
        # A — PERSONAGEM
        {
            "type": "character",
            "label": "PHONK_CHARACTER",
            "scene": "anime woman, sharp cold features, expressionless face, glowing crimson eyes, black technical jacket with hood, standing alone in empty parking structure at 3am, single blood-red neon tube casting hard shadows on wet concrete below",
            "palette": "blood red neon slash across absolute darkness, wet concrete reflections, zero warmth, maximum contrast between light and shadow",
            "mood": "cold calculated dangerous energy, she owns the dark",
        },
        # B — CENÁRIO
        {
            "type": "scene",
            "label": "PHONK_SCENE",
            "scene": "empty midnight highway stretching to horizon, no character, red tail lights dissolving into fog, wet asphalt mirror reflecting crimson and violet neon signs, single orange sodium lamp at road edge, low ground fog",
            "palette": "deep crimson and charcoal black, neon reflections bleeding in wet road, violet fog at distance, maximum darkness with selective light",
            "mood": "midnight drive at 3am, the city as pure emptiness and speed",
        },
        # C — CINEMATOGRÁFICO
        {
            "type": "cinematic",
            "label": "PHONK_CINEMATIC",
            "scene": "low angle cinematic shot, anime woman silhouette walking away down dark underground tunnel, massive crimson neon portal at far vanishing point, her shadow stretching backwards, fog at ankle level, never looking back",
            "palette": "pitch black tunnel with single red vanishing point of light, silhouette vs glow, dramatic forced perspective",
            "mood": "inevitability, she was always going to walk into that light",
        },
        # D — ABSTRATO
        {
            "type": "abstract",
            "label": "PHONK_ABSTRACT",
            "scene": "808 bass wave made visible as crimson shockwave tearing through dark cyberpunk city, shattered glass floating in slow motion caught in red light, vinyl record spinning with fire edge and neon purple glow, concrete cracking from sub-bass pressure",
            "palette": "blood red and absolute black, aggressive energy made physical and visible, purple accent in cracks",
            "mood": "raw bass power as destruction, the drop as geological event",
        },
    ],

    # ── TRAP ──────────────────────────────────────────────────────────
    "trap": [
        # A — PERSONAGEM
        {
            "type": "character",
            "label": "TRAP_CHARACTER",
            "scene": "anime woman, sharp dark features, glowing violet eyes, structured black jacket, standing at floor-to-ceiling penthouse window at night, entire neon city grid spread below, rain on glass, arms crossed",
            "palette": "midnight black and electric violet neon below, premium cold luxury, the palette of someone who made it",
            "mood": "composed power, the city is just context for her presence",
        },
        # B — CENÁRIO
        {
            "type": "scene",
            "label": "TRAP_SCENE",
            "scene": "rain-soaked cyberpunk rooftop at night, no character, puddles reflecting violet and red neon signs below, dark skyline, single powerful spotlight beam cutting through storm clouds, expensive emptiness",
            "palette": "deep black and electric purple neon reflections, rain as texture, premium contrast",
            "mood": "the top of the city, beauty without needing an audience",
        },
        # C — CINEMATOGRÁFICO
        {
            "type": "cinematic",
            "label": "TRAP_CINEMATIC",
            "scene": "wide cinematic shot, anime woman tiny figure at rooftop edge against enormous neon-lit city skyline, scale makes her larger not smaller, storm clouds above, city grid stretching to horizon below",
            "palette": "deep navy storm sky, warm amber and violet city lights below, epic vertical composition",
            "mood": "elevation, belonging at the top was never in question",
        },
        # D — ABSTRATO
        {
            "type": "abstract",
            "label": "TRAP_ABSTRACT",
            "scene": "808 waveform as violet architecture floating in dark city void, bass frequency rings expanding outward in neon purple, gold chain links dissolving into light particles, luxury geometry in darkness",
            "palette": "electric violet and black, neon purple accents, premium dark minimalism",
            "mood": "the sound of power made visible and geometric",
        },
    ],

    # ── ELECTRONIC / DUBSTEP ──────────────────────────────────────────
    "electronic": [
        # A — PERSONAGEM
        {
            "type": "character",
            "label": "ELECTRONIC_CHARACTER",
            "scene": "anime woman, dark hair with electric red streaks, glowing crimson eyes, dark streetwear with neon circuit details, standing in heavy rain on city street, neon signs reflecting in puddles around her, looking straight at camera",
            "palette": "electric crimson and deep violet, rain as texture, dark city glow from every surface",
            "mood": "the drop is her, she is the frequency",
        },
        # B — CENÁRIO
        {
            "type": "scene",
            "label": "ELECTRONIC_SCENE",
            "scene": "underground rave venue empty before the crowd, no character, laser grid cutting through smoke and fog, dark concrete walls, massive subwoofer stacks glowing red, UV light catching floating dust particles",
            "palette": "UV purple floor, blood red laser lines, deep black space, fluorescent crimson geometry",
            "mood": "the space that holds the ritual, charged before it begins",
        },
        # C — CINEMATOGRÁFICO
        {
            "type": "cinematic",
            "label": "ELECTRONIC_CINEMATIC",
            "scene": "rear view from stage, anime woman DJ silhouette facing enormous dark crowd, massive LED wall exploding with red and violet visuals behind her, her silhouette the only dark point in the light storm",
            "palette": "silhouette against crimson and violet LED explosion, chromatic aberration at edges, scale overwhelming",
            "mood": "she controls the frequency of thousands",
        },
        # D — ABSTRATO
        {
            "type": "abstract",
            "label": "ELECTRONIC_ABSTRACT",
            "scene": "sound wave architecture in darkness, bass drop visualized as supernova of crimson and violet expanding from center point, frequency rings as concentric neon circles, the moment of impact frozen",
            "palette": "electric crimson and vivid purple on absolute black, maximum saturation at center fading to dark",
            "mood": "the drop as big bang, music as creation event",
        },
    ],

    # ── DARK ──────────────────────────────────────────────────────────
    "dark": [
        # A — PERSONAGEM
        {
            "type": "character",
            "label": "DARK_CHARACTER",
            "scene": "ghostly pale anime woman, long dark hair floating in zero gravity, glowing blood-red irises, dark tactical outfit, surrounded by fragments of shattered neon signs in dark void, slight knowing smile",
            "palette": "near-monochrome darkness with bleeding crimson eye glow, shattered neon fragments as only other light sources, violet accent at edges",
            "mood": "beautiful and dangerous, the smile is the warning",
        },
        # B — CENÁRIO
        {
            "type": "scene",
            "label": "DARK_SCENE",
            "scene": "abandoned cyberpunk district at night, no character, crumbling neon signs still flickering red and violet, rain filling cracked streets, overgrown dark vines on destroyed buildings, fog at ground level, one working lamp",
            "palette": "cold darkness with flickering crimson and violet neon remnants, rain texture, atmosphere of beautiful decay",
            "mood": "the city that was, beauty outliving its purpose",
        },
        # C — CINEMATOGRÁFICO
        {
            "type": "cinematic",
            "label": "DARK_CINEMATIC",
            "scene": "extreme wide shot, anime woman tiny figure at center of vast dark space, single circle of blood-red light surrounding her, absolute darkness pressing from all sides, rain visible in the light circle only",
            "palette": "absolute black surrounding single vivid crimson circle of light, the human figure as only reference point",
            "mood": "the light she carries is the only light, darkness is not empty",
        },
        # D — ABSTRATO
        {
            "type": "abstract",
            "label": "DARK_ABSTRACT",
            "scene": "dark melody visualized as black ink spreading through neon-lit water, crimson sound waves bleeding at edges, heartbeat rhythm made visible as concentric dark rings with glowing red centers, void with pulse",
            "palette": "black ink and deep crimson, neon violet at edges, darkness with rhythmic pulse",
            "mood": "darkness is not absence it is presence, music as organism",
        },
    ],

    # ── DEFAULT (inclui gêneros não mapeados) ─────────────────────────
    "default": [
        # A — PERSONAGEM
        {
            "type": "character",
            "label": "DEFAULT_CHARACTER",
            "scene": "anime woman, striking features, glowing red eyes, dark hooded jacket, standing in rain-soaked neon-lit alley, crimson and violet reflections in puddles, atmospheric fog, looking directly at viewer",
            "palette": "blood red and electric violet neon, absolute black shadows, rain as texture, premium dark anime aesthetic",
            "mood": "presence that stops the scroll, dangerous beauty",
        },
        # B — CENÁRIO
        {
            "type": "scene",
            "label": "DEFAULT_SCENE",
            "scene": "rain-soaked cyberpunk street at 3am, no character, neon signs in red and violet reflecting in every puddle, empty except for fog at ground level, fire escape ladders cutting geometric shadows",
            "palette": "deep midnight with vivid crimson and violet light sources, rich contrast, wet reflections doubling every neon",
            "mood": "the city after midnight, pure atmosphere",
        },
        # C — CINEMATOGRÁFICO
        {
            "type": "cinematic",
            "label": "DEFAULT_CINEMATIC",
            "scene": "wide cinematic shot, anime woman silhouette against enormous neon city, rain falling in light beams, scale makes her presence larger, violet storm clouds above, crimson city below",
            "palette": "cold electric violet sky and warm crimson city lights, cinematic contrast, rain visible in every beam",
            "mood": "the feeling of dark music made visual",
        },
        # D — ABSTRATO
        {
            "type": "abstract",
            "label": "DEFAULT_ABSTRACT",
            "scene": "bass frequency made visible as crimson and violet light sculpture, music waveform as glowing architecture in darkness, sound as physical force bending neon light, abstract beauty with emotional weight",
            "palette": "vivid crimson and deep violet on absolute black, bass frequencies as warm red, treble as cool violet",
            "mood": "music that you can see and feel, sound as form",
        },
    ],
}

# Mapear gêneros para os conceitos existentes
GENRE_MAP = {
    "lofi":       "dark",        # lofi dark = dark concepts
    "indie":      "default",
    "rock":       "electronic",  # rock = energia eletrônica
    "metal":      "dark",        # metal = dark concepts
    "cinematic":  "dark",
    "funk":       "trap",        # funk = trap concepts
    "pop":        "default",
}


# ══════════════════════════════════════════════════════════════════════
# QUALIDADE & NEGATIVO — otimizados para Anime Dark Cyberpunk
# ══════════════════════════════════════════════════════════════════════

QUALITY_TAGS = (
    "masterpiece, best quality, ultra-detailed anime illustration, "
    "professional anime key visual, perfect cel shading, clean sharp lineart, "
    "ultra-vivid saturated colors, deep rich blacks, luminous neon highlights, "
    "cinematic composition, razor-sharp focus, "
    "richly detailed dark cyberpunk background with atmospheric depth, "
    "volumetric neon lighting, dramatic light and shadow interplay, "
    "studio-level dark anime production quality, "
    "trending on pixiv dark cyberpunk, ArtStation quality, 9:16 vertical format, "
    "scroll-stopping visual impact, premium dark anime visual novel quality"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, 3D render, CGI, real human face, "
    "text, watermark, signature, logo, border, frame, "
    "multiple characters, extra limbs, deformed hands, fused fingers, bad anatomy, "
    "distorted face, wrong proportions, malformed body parts, "
    "child appearance, young teen face, childlike proportions, "
    "explicit nudity, fetish content, nsfw, "
    "blurry, muddy colors, flat boring lighting, desaturated washed-out colors, "
    "pastel colors, soft colors, warm cozy aesthetic, "
    "bright daylight, cheerful, kawaii cute style, "
    "generic gradient background, plain studio void, empty background, "
    "airbrushed plastic skin, uncanny valley, "
    "Western cartoon, Pixar style, chibi, super deformed, "
    "sketch only, unfinished lineart, low quality, "
    "generic anime waifu, bland background, same composition as always, "
    "repetitive, seen before, boring, forgettable, "
    "green colors, yellow dominant, orange dominant, warm sunset colors"
)


# ══════════════════════════════════════════════════════════════════════
# SEED E SELEÇÃO DE CONCEITO
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v5_dark_cyberpunk"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick_concept(style: str, filename: str, short_num: int) -> dict:
    """
    Seleciona conceito visual com rotação garantida.
    short_num 1,2,3,4 = conceitos A(character),B(scene),C(cinematic),D(abstract)
    
    Isso permite rastrear no YouTube Analytics qual tipo gera mais views:
    - short #1 = sempre CHARACTER
    - short #2 = sempre SCENE
    - short #3 = sempre CINEMATIC
    - short #4 = sempre ABSTRACT
    """
    # Mapear gênero para conceitos disponíveis
    mapped_style = GENRE_MAP.get(style, style)
    concepts = VISUAL_CONCEPTS.get(mapped_style, VISUAL_CONCEPTS["default"])
    
    # Rotação determinística: short_num define o tipo de conceito
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
        "character": (
            "ONE specific anime woman character. Sharp, cold, powerful expression. "
            "She must have GLOWING RED or VIOLET eyes — non-negotiable. "
            "Background must be rich dark cyberpunk environment, not just backdrop. "
            "Close to medium shot, character fills 60-70% of frame."
        ),
        "scene": (
            "ENVIRONMENT IS THE SUBJECT — no dominant character visible. "
            "Every detail tells the story. Rain, neon reflections, fog, darkness. "
            "The scene must feel alive and charged with energy. "
            "Viewer should feel the music just looking at the empty space."
        ),
        "cinematic": (
            "EPIC SCALE — if character present, she is small vs the environment. "
            "Widescreen cinematic feel in 9:16 vertical format. "
            "Think movie poster: one powerful composition, one mood, no clutter. "
            "The scale contrast IS the statement."
        ),
        "abstract": (
            "MUSIC VISUALIZED AS PHYSICAL REALITY — no literal people. "
            "Sound waves, bass frequencies, the DROP made visible. "
            "Neon light as sound energy. Darkness as pressure. "
            "The image should feel like the track sounds."
        ),
    }

    concept_instruction = concept_type_instructions.get(concept["type"], "")
    concept_label = concept.get("label", concept["type"].upper())

    system = (
        "You are an elite dark anime art director for YouTube Shorts thumbnails. "
        "Your aesthetic: ANIME DARK CYBERPUNK. Always. No exceptions.\n\n"
        "CHANNEL: DJ darkMark | Phonk, Trap, Dubstep, Electronic\n"
        "VISUAL IDENTITY: Blood red + electric violet + absolute black + rain + neon\n\n"
        "ABSOLUTE RULES:\n"
        "1. ALWAYS dark cyberpunk — never bright, never warm, never cute\n"
        "2. PALETTE: crimson/blood red + electric violet/purple + absolute black\n"
        "3. Rain, wet surfaces, neon reflections are ALWAYS welcome\n"
        "4. If character present: glowing eyes (red or violet), dark outfit, cold expression\n"
        "5. Background always dark cyberpunk city, never gradient void\n"
        "6. Colors must be ULTRA-VIVID neons against absolute darkness\n"
        "7. 9:16 vertical format, platform-safe, non-sexualized\n"
        "8. Output ONLY the final prompt: comma-separated, 90-120 words, no preamble"
    )

    user = f"""Create a scroll-stopping ANIME DARK CYBERPUNK illustration prompt.

SONG: "{song_name}"
GENRE: {style} | ALL: {all_styles}
SHORT #: {short_num} | CONCEPT: {concept_label}

VISUAL CONCEPT TYPE: {concept["type"].upper()}
{concept_instruction}

SCENE FOUNDATION:
{concept["scene"]}

COLOR PALETTE (execute exactly — DARK CYBERPUNK ONLY):
{concept["palette"]}

EMOTIONAL MOOD:
{concept["mood"]}

CRITICAL: 
- Colors MUST be blood red + electric violet/purple + absolute black. Nothing warm.
- The image must emotionally connect to "{song_name}".
- Let the song title influence one specific visual detail.
- 90-120 words, comma-separated only, no explanation."""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=350,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw  = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) — short #{short_num} [{concept_label}]")
    return _compact(full)


def _static_prompt(concept: dict) -> str:
    prompt = (
        f"masterpiece, best quality, ultra-detailed premium dark cyberpunk anime illustration, "
        f"{concept['scene']}, "
        f"color palette: {concept['palette']}, "
        f"mood: {concept['mood']}, "
        f"blood red and electric violet neon against absolute black, "
        f"rain wet surfaces neon reflections, "
        f"ultra-vivid saturated neon colors, deep rich blacks, luminous neon highlights, "
        f"cinematic volumetric dark lighting, atmospheric cyberpunk depth, richly detailed, "
        f"clean sharp anime lineart, perfect cel shading, "
        f"9:16 vertical composition, scroll-stopping visual impact, dark anime pixiv quality"
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
        + ", dark cyberpunk anime illustration style, NOT photorealistic, NOT 3D render, "
        + "blood red and electric violet neon, absolute black shadows, "
        + "ultra-vibrant dark neon colors, deep rich blacks, luminous crimson and violet highlights, "
        + "sharp clean lineart, premium dark anime key visual quality, "
        + "rain wet surfaces neon city, specific distinctive dark visual, NOT generic"
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
