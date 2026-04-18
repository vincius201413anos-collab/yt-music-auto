"""
ai_image_generator.py — Máxima variedade visual.
40 variações de personagem × ambientes × poses × iluminações.
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
# 40 VARIAÇÕES DE PERSONAGEM
# ══════════════════════════════════════════════════════════════════════

CHARACTER_POOL = [
    # 1
    {"hair": "long straight black hair, center part", "skin": "light porcelain skin", "eyes": "large dark almond eyes", "face": "soft delicate features, small nose", "vibe": "elegant and mysterious"},
    # 2
    {"hair": "long wavy chestnut brown hair", "skin": "warm olive skin, sun-kissed", "eyes": "expressive brown eyes, long lashes", "face": "high cheekbones, full lips", "vibe": "passionate and bold"},
    # 3
    {"hair": "platinum blonde in a messy bun", "skin": "fair skin with freckles", "eyes": "sharp blue-grey eyes", "face": "strong jaw, angular features", "vibe": "cool and rebellious"},
    # 4
    {"hair": "voluminous natural afro with gold pins", "skin": "deep rich brown skin, luminous", "eyes": "large dark expressive eyes", "face": "round face, radiant smile", "vibe": "powerful and joyful"},
    # 5
    {"hair": "short edgy purple-black undercut", "skin": "pale cool skin", "eyes": "dramatic violet eyes, heavy eyeliner", "face": "sharp angular face, strong brows", "vibe": "intense and alternative"},
    # 6
    {"hair": "long flowing auburn hair, loose waves", "skin": "light freckled skin, warm undertone", "eyes": "green eyes, sharp gaze", "face": "pointed chin, playful expression", "vibe": "fierce and free-spirited"},
    # 7
    {"hair": "silver-white straight bob cut", "skin": "neutral beige skin", "eyes": "glowing silver eyes", "face": "symmetrical refined features", "vibe": "futuristic and ethereal"},
    # 8
    {"hair": "black hair with neon blue streaks, half-up", "skin": "warm tan skin", "eyes": "dark eyes with colorful shadow", "face": "cute button nose, dimples", "vibe": "playful and energetic"},
    # 9
    {"hair": "long dark brown box braids with gold thread", "skin": "medium brown luminous skin", "eyes": "deep brown eyes, intense gaze", "face": "strong jaw, elegant neck", "vibe": "graceful and powerful"},
    # 10
    {"hair": "soft pastel pink wavy hair", "skin": "soft peach skin", "eyes": "wide rose-pink eyes", "face": "round soft face, gentle smile", "vibe": "dreamy and gentle"},
    # 11
    {"hair": "long midnight blue hair, pin-straight", "skin": "light cool-toned skin", "eyes": "dark navy eyes, heavy lashes", "face": "high brow, aristocratic features", "vibe": "mysterious and regal"},
    # 12
    {"hair": "wild curly red hair, untamed", "skin": "warm golden skin", "eyes": "hazel eyes, mischievous glint", "face": "round cheeks, wide grin", "vibe": "chaotic and fun"},
    # 13
    {"hair": "sleek black hair in a high ponytail", "skin": "honey skin tone", "eyes": "almond eyes, cat-eye liner", "face": "sharp cheekbones, confident smirk", "vibe": "badass and cool"},
    # 14
    {"hair": "teal-dyed twin braids with ribbons", "skin": "fair skin with pink undertones", "eyes": "sky blue doe eyes", "face": "baby face, soft round features", "vibe": "cute and kawaii"},
    # 15
    {"hair": "long ombre brown-to-blonde hair", "skin": "medium warm skin", "eyes": "honey brown eyes", "face": "heart-shaped face, natural beauty", "vibe": "warm and approachable"},
    # 16
    {"hair": "shaved sides, long dark hair on top", "skin": "deep olive skin", "eyes": "dark piercing eyes", "face": "strong jaw, tattoo on neck", "vibe": "street punk energy"},
    # 17
    {"hair": "white hair with cherry blossom pins", "skin": "porcelain pale skin", "eyes": "soft pink eyes", "face": "doll-like delicate features", "vibe": "ghostly and delicate"},
    # 18
    {"hair": "long black hair with red highlights, blowing", "skin": "pale fair skin", "eyes": "crimson red eyes", "face": "sharp vampire-like features", "vibe": "dark and intense"},
    # 19
    {"hair": "short messy brown hair, bedhead style", "skin": "natural tan skin", "eyes": "warm brown eyes, sleepy look", "face": "casual cute features, soft smile", "vibe": "cozy and relatable"},
    # 20
    {"hair": "long silver hair with lavender tips", "skin": "cool fair skin with shimmer", "eyes": "pale lilac eyes", "face": "elegant elven features", "vibe": "magical and otherworldly"},
    # 21
    {"hair": "fiery orange-red hair, short pixie cut", "skin": "warm brown skin", "eyes": "gold-amber eyes", "face": "strong features, bright energy", "vibe": "bold and fierce"},
    # 22
    {"hair": "long black hair with galaxy-blue highlights", "skin": "dark smooth skin", "eyes": "glowing blue eyes", "face": "perfect symmetry, model features", "vibe": "cosmic and stunning"},
    # 23
    {"hair": "messy blonde bob with dark roots", "skin": "light skin, rosy cheeks", "eyes": "grey-green tired eyes", "face": "soft round face, natural look", "vibe": "indie and effortless"},
    # 24
    {"hair": "braided crown with flowers", "skin": "medium brown skin", "eyes": "dark almond eyes with shimmer", "face": "graceful features, serene expression", "vibe": "ethereal and natural"},
    # 25
    {"hair": "long white hair like snow, flowing", "skin": "pale blue-tinted skin", "eyes": "ice blue glowing eyes", "face": "sharp cold beauty, stoic expression", "vibe": "frozen and powerful"},
    # 26
    {"hair": "dark green hair in loose waves", "skin": "warm tan skin", "eyes": "forest green eyes", "face": "earthy natural features, kind smile", "vibe": "nature spirit energy"},
    # 27
    {"hair": "black hair with gold geometric patterns", "skin": "rich dark brown skin", "eyes": "golden eyes, regal gaze", "face": "strong beautiful features, queen-like", "vibe": "majestic and divine"},
    # 28
    {"hair": "neon pink twin tails", "skin": "light skin with star freckles", "eyes": "sparkling magenta eyes", "face": "hyper-cute features, huge smile", "vibe": "pop idol energy"},
    # 29
    {"hair": "long flowing cream-white hair", "skin": "warm ivory skin", "eyes": "soft amber eyes, warm gaze", "face": "gentle angelic features", "vibe": "angelic and serene"},
    # 30
    {"hair": "short black hair, one eye covered", "skin": "pale skin, dark circles", "eyes": "one visible dark eye, mysterious", "face": "edgy asymmetric look", "vibe": "mysterious and secretive"},
    # 31
    {"hair": "copper-red hair in loose curls", "skin": "light skin, golden freckles", "eyes": "bright copper eyes", "face": "warm friendly features, gap tooth", "vibe": "wholesome and bright"},
    # 32
    {"hair": "long black hair with white streak", "skin": "medium cool-toned skin", "eyes": "heterochromia: one blue, one brown", "face": "unique striking features", "vibe": "unique and memorable"},
    # 33
    {"hair": "bleached white buzz cut", "skin": "dark rich skin", "eyes": "sharp dark eyes", "face": "bold strong features, confidence", "vibe": "avant-garde and bold"},
    # 34
    {"hair": "long honey-blonde hair with waves", "skin": "sun-kissed warm skin", "eyes": "sea blue eyes, sparkle", "face": "beach girl natural beauty", "vibe": "sunny and free"},
    # 35
    {"hair": "sleek brown hair with blunt bangs", "skin": "neutral medium skin", "eyes": "dark brown sharp eyes", "face": "clean classic beauty", "vibe": "smart and composed"},
    # 36
    {"hair": "wild curly black hair, voluminous", "skin": "rich chocolate skin", "eyes": "dark soulful eyes", "face": "expressive beautiful face", "vibe": "soulful and expressive"},
    # 37
    {"hair": "long rose-gold wavy hair", "skin": "peachy fair skin", "eyes": "golden-pink eyes", "face": "soft romantic features", "vibe": "romantic and dreamy"},
    # 38
    {"hair": "black hair pulled back, sharp style", "skin": "olive skin, sharp features", "eyes": "dark intense eyes", "face": "strong jaw, warrior look", "vibe": "warrior and determined"},
    # 39
    {"hair": "long teal and purple ombre hair", "skin": "light cool skin", "eyes": "teal eyes, artistic makeup", "face": "artistic striking features", "vibe": "artistic and creative"},
    # 40
    {"hair": "short silver hair, wind-blown", "skin": "warm brown skin", "eyes": "silver glowing eyes", "face": "timeless elegant features", "vibe": "timeless and elegant"},
]

# ══════════════════════════════════════════════════════════════════════
# 10 POSES POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_POSES = {
    "lofi": [
        "chin resting on hand, sitting at desk, peaceful sleepy look",
        "lying on bed face up, holding phone, soft smile",
        "sitting at window watching rain, mug in hands",
        "curled up on floor with headphones on, eyes closed",
        "leaning back on chair, feet on desk, relaxed",
        "drawing in sketchbook under lamp light",
        "sitting in beanbag chair, book on lap",
        "head tilted, looking out at night city",
        "wrapped in blanket, sipping tea slowly",
        "stretching at desk, tired but content",
    ],
    "indie": [
        "holding a vinyl record, soft wistful smile",
        "sitting on rooftop ledge, legs dangling",
        "arms out in wind, eyes closed, face to sunset",
        "lying in grass, looking at sky",
        "walking down empty street, looking back",
        "sitting on window sill, journal open",
        "playing acoustic guitar, eyes half-closed",
        "standing in field, hair blowing freely",
        "leaning on brick wall, candid natural pose",
        "hand on heart, emotional expression",
    ],
    "rock": [
        "holding electric guitar overhead, stage energy",
        "screaming into microphone, eyes fierce",
        "jumping mid-air, guitar in hand",
        "kneeling on stage, head bowed, spotlight",
        "back to audience, facing concert crowd",
        "guitar solo pose, face intense and focused",
        "sitting on amp, arms crossed, staring ahead",
        "windmill guitar move, hair flying",
        "fist raised to crowd, victorious",
        "leaning into mic stand, eyes closed in emotion",
    ],
    "metal": [
        "standing in storm, arms spread wide",
        "hands forming horns gesture, fierce stare",
        "kneeling with chains, looking up dramatically",
        "standing at cliff edge, hair in wind",
        "arms raised calling down lightning",
        "sitting on gothic throne, commanding presence",
        "back against ancient ruins, looking over shoulder",
        "walking through smoke and embers",
        "hand extended, dark magic swirling",
        "eyes glowing, surrounded by ravens",
    ],
    "phonk": [
        "leaning on car hood, arms crossed",
        "in driver seat, one hand on wheel",
        "walking toward camera, hoodie up, confident",
        "crouching on concrete, looking up",
        "standing in rain, hands in pockets",
        "back against graffiti wall, staring ahead",
        "sitting on hood, legs dangling",
        "looking over shoulder at night city",
        "arms on car roof, staring at horizon",
        "in neon light, slow confident pose",
    ],
    "trap": [
        "looking at camera through sunglasses, dripping confidence",
        "sitting at poker table, chips in hand",
        "standing at penthouse window, arms crossed",
        "phone in hand, looking away, unbothered",
        "leaning back in luxury chair, relaxed power",
        "walking with bodyguard energy",
        "at rooftop pool edge, city below",
        "gold jewelry caught in light, proud stance",
        "one hand up showing rings, fierce look",
        "sitting on car, legs crossed, owning the scene",
    ],
    "electronic": [
        "arms raised at festival, pure euphoria",
        "eyes closed, lost in the music, crowd behind",
        "jumping on stage, lights exploding",
        "hands touching holographic visuals",
        "spinning, hair flying, laser beams",
        "screaming in joy at drop, crowd energy",
        "kneeling under spotlight, arms wide",
        "facing giant LED wall, silhouette",
        "crowd surfing, people's hands below",
        "standing on speaker, commanding crowd",
    ],
    "dark": [
        "sitting in moonlight, arms wrapped around knees",
        "standing in fog, looking away",
        "floating pose, dark cloak billowing",
        "kneeling at altar of candles, head bowed",
        "back against moonlit window, shadow play",
        "hands reaching upward, darkness around",
        "sitting alone in empty cathedral",
        "walking through mist, silhouette",
        "standing at edge of cliff in storm",
        "lying on stone, peaceful but haunting",
    ],
    "pop": [
        "winking and pointing at camera",
        "spinning in confetti rain, laughing",
        "peace sign, bright smile, sparkles",
        "jumping with pom poms, idol energy",
        "sitting on moon prop, glamorous",
        "blowing kiss at camera",
        "finger gun pose, confident smile",
        "surrounded by balloons, joyful",
        "hands framing face like a heart",
        "back to camera, looking over shoulder with smile",
    ],
    "cinematic": [
        "standing at edge of world, wind in hair",
        "running toward camera from explosion",
        "slowly turning, cape billowing",
        "hand raised stopping something unseen",
        "kneeling on one knee, looking up determined",
        "standing at castle gate, sword in hand",
        "arms open at cliff overlooking kingdom",
        "falling backward into water, dramatic",
        "single tear, eyes to sky",
        "walking through fire, unafraid",
    ],
    "default": [
        "looking directly at camera, commanding",
        "in profile, thoughtful gaze",
        "hand on chin, contemplating",
        "sitting cross-legged, zen energy",
        "standing in golden light, serene",
        "walking toward viewer, confident",
        "looking up at something beyond frame",
        "arms crossed, knowing smile",
        "head tilted, curious expression",
        "silhouette against dramatic light",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# AMBIENTES POR GÊNERO (10 cada)
# ══════════════════════════════════════════════════════════════════════

GENRE_ENVIRONMENTS = {
    "lofi": [
        "cozy bedroom, warm desk lamp, rain on window, city lights below",
        "small apartment kitchen at 3am, kettle steaming, soft light",
        "attic studio with slanted ceiling, fairy lights, stacked books",
        "café corner table, empty coffee cups, night outside",
        "college dorm, laptop glow, tangled earphones",
        "tiny balcony with plants, city below, cloudy night",
        "floor mattress setup, warm amber light, vinyl on turntable",
        "reading nook under stairs, cushions, candles",
        "library at closing time, last light on, books everywhere",
        "train at night, empty car, city lights passing by",
    ],
    "indie": [
        "rooftop at golden hour, warm orange sunset, city silhouette",
        "empty highway at dawn, mist, long road ahead",
        "sunflower field, late afternoon, golden hour glow",
        "abandoned train station, overgrown, warm light",
        "vintage record store, afternoon sun through dusty windows",
        "coastal cliff, crashing waves below, wind",
        "back alley with murals, warm street lamp",
        "old bookshop exterior, cobblestone street",
        "small town bridge at dusk, river below",
        "festival campground at sunset, warm tents",
    ],
    "rock": [
        "massive concert stage, spotlights, crowd of thousands",
        "empty arena before show, lone spotlight",
        "backstage corridor, equipment everywhere, raw energy",
        "outdoor festival stage, storm clouds forming",
        "small sweaty underground venue, red lights",
        "parking lot before show, tour bus behind",
        "recording studio late night, gear everywhere",
        "bridge over industrial river at night",
        "rooftop at dusk, city spread below",
        "alley with brick walls and graffiti, harsh light",
    ],
    "metal": [
        "dark fantasy landscape, storm, castle ruins",
        "volcanic mountain, lava glow, ash in air",
        "ancient dungeon with torches, stone walls",
        "forest of dead trees, red moon sky",
        "gothic cathedral interior, crumbling arches",
        "barren wasteland, lightning strikes",
        "underground cave with glowing crystals",
        "cliff over stormy ocean, dramatic sky",
        "abandoned church, broken windows, moonlight",
        "throne room of dark castle, ember light",
    ],
    "phonk": [
        "underground parking lot 3am, red neon on wet concrete",
        "empty highway at night, passing headlights",
        "rooftop parking deck, city lights 360",
        "alley with red signs, steam from grates",
        "tunnel underpass, car doing burnout",
        "abandoned warehouse district, single light",
        "gas station at midnight, alone",
        "bridge underside, graffiti, dark water below",
        "narrow city street, neon reflections in puddles",
        "freight yard at night, industrial cold light",
    ],
    "trap": [
        "penthouse rooftop, infinity pool, city skyline",
        "luxury high-rise interior, floor-to-ceiling windows",
        "private jet interior, leather seats",
        "nightclub VIP section, soft neon light",
        "car showroom after hours, exotic cars",
        "hotel suite at night, lights of city below",
        "designer boutique, after closing, soft light",
        "helipad on skyscraper, city below",
        "yacht deck, sunset on open water",
        "mansion corridor, marble floors, chandeliers",
    ],
    "electronic": [
        "festival mainstage, laser show, crowd waves",
        "warehouse rave, strobe lights, fog machines",
        "outdoor stage at night, LED columns, thousands",
        "holographic dome venue, visuals everywhere",
        "futuristic nightclub, neon geometry",
        "desert festival stage, stars above, crowd below",
        "massive LED tunnel entrance, pulsing light",
        "boat party, open water, light show",
        "underground club, single beam on dancefloor",
        "rooftop venue, city skyline, laser beams",
    ],
    "dark": [
        "moonlit abandoned cathedral, broken glass, mist",
        "midnight forest, pale moonbeams through trees",
        "cliff edge in storm, dramatic sky",
        "empty ballroom, dusty chandeliers, faded grandeur",
        "ancient cemetery, stone crosses, fog",
        "lighthouse at night, crashing waves",
        "victorian greenhouse, overgrown, moonlight",
        "flooded basement, candles floating",
        "stone bridge at midnight, dark river",
        "haunted manor corridor, fading portraits",
    ],
    "pop": [
        "pastel studio, confetti everywhere, neon signs",
        "roller rink with disco ball, colored lights",
        "flower market in bloom, soft daylight",
        "candy-colored bedroom, balloons",
        "amusement park at night, carousel lights",
        "rooftop garden party, fairy lights",
        "backstage dressing room, mirrors and lights",
        "colorful mural street, sunny day",
        "ice cream parlor in soft pink light",
        "outdoor concert, summer day, crowd of fans",
    ],
    "cinematic": [
        "mountain peak above clouds, golden sunrise",
        "ancient temple ruins at dusk, god rays",
        "battlefield after victory, smoke and light",
        "enormous library, ladder, warm glow",
        "spaceship observation deck, stars beyond",
        "medieval castle courtyard, torches at night",
        "waterfall in magical forest, mist",
        "abandoned city, nature reclaiming, peaceful",
        "lighthouse on dramatic rocky coast",
        "train crossing mountain bridge, epic scale",
    ],
    "default": [
        "dramatic studio, single spotlight, dark background",
        "urban rooftop, golden hour, city below",
        "abstract space, floating light particles",
        "empty theatre stage, single light",
        "endless corridor of mirrors",
        "minimalist white space, perfect light",
        "underground art gallery, mood lighting",
        "glass building exterior, reflections",
        "park at magic hour, soft mist",
        "old train station, morning light shafts",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# PALETAS E HUMORES
# ══════════════════════════════════════════════════════════════════════

LIGHTING_VARIATIONS = [
    "warm golden hour light, soft shadows",
    "cold blue moonlight, high contrast",
    "dramatic rim lighting from behind",
    "neon colored reflections, cyberpunk palette",
    "soft diffused overcast light",
    "harsh single spotlight, deep shadows",
    "colorful festival lights, vivid",
    "candle and firelight, warm amber",
    "morning mist light, soft and hazy",
    "electric storm light, dramatic flashes",
    "sunset gradient, orange to purple sky",
    "underwater caustic light patterns",
    "dusty beam of light through window",
    "city lights bokeh in background",
    "blood red emergency lighting",
]

QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra-detailed, sharp focus, "
    "anime illustration style, 9:16 vertical composition, centered subject, "
    "beautiful detailed eyes, professional digital art, "
    "no text, no watermark, no extra people, single subject only"
)

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, "
    "split image, collage, multiple people, two girls, "
    "extra arms, extra fingers, deformed hands, bad anatomy, "
    "ugly face, blurry, muddy, flat lighting, "
    "low quality, stock photo, realistic photo, elderly, child, "
    "revealing outfit, bikini, generic background"
)


# ══════════════════════════════════════════════════════════════════════
# SELEÇÃO COM SEED ÚNICA POR MÚSICA+SHORT
# ══════════════════════════════════════════════════════════════════════

def _seed_from(filename: str, short_num: int) -> int:
    """Gera seed determinística mas única para cada música+short."""
    key = f"{filename}_{short_num}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _seeded_choice(pool: list, seed: int, extra_offset: int = 0) -> any:
    rng = random.Random(seed + extra_offset)
    return rng.choice(pool)


def _pick_character(filename: str, short_num: int) -> dict:
    seed = _seed_from(filename, short_num)
    return _seeded_choice(CHARACTER_POOL, seed, 0)


def _pick_pose(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_POSES.get(style, GENRE_POSES["default"])
    return _seeded_choice(pool, seed, 1)


def _pick_environment(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_ENVIRONMENTS.get(style, GENRE_ENVIRONMENTS["default"])
    return _seeded_choice(pool, seed, 2)


def _pick_lighting(filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    return _seeded_choice(LIGHTING_VARIATIONS, seed, 3)


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled Track"

def _compact_prompt(text: str, max_chars: int = 950) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)
    character = _pick_character(filename, short_num)
    pose = _pick_pose(style, filename, short_num)
    environment = _pick_environment(style, filename, short_num)
    lighting = _pick_lighting(filename, short_num)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(song_name, style, all_styles, character, pose, environment, lighting)
        except Exception as e:
            print(f"  [Claude] Falha no prompt: {e} — fallback")

    return _static_prompt(character, pose, environment, lighting)


def _claude_prompt(
    song_name: str, style: str, all_styles: str,
    character: dict, pose: str, environment: str, lighting: str,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are a master visual director for a premium YouTube Shorts music channel. "
        "Create breathtaking Flux image prompts — cinematic, scroll-stopping, emotionally powerful. "
        "ONE beautiful anime girl, central subject. Use the exact character description provided. "
        "Output ONLY the prompt in English — comma-separated, no explanation, no quotes."
    )

    user = f"""Cinematic Flux prompt for a vertical YouTube music Short.

Song: "{song_name}" | Genre: {style} ({all_styles})

CHARACTER (use exactly):
Hair: {character['hair']}
Skin: {character['skin']}
Eyes: {character['eyes']}
Face: {character['face']}
Vibe: {character['vibe']}

Pose: {pose}
Environment: {environment}
Lighting: {lighting}

Rules:
- Exactly ONE female subject with the character above
- 9:16 vertical, subject centered and prominent
- Lighting must be dramatic and intentional
- Make someone STOP scrolling
- 60-100 words, comma-separated
- No text, no watermark, no extra people"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=250,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    prompt = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{prompt}, {QUALITY_SUFFIX}"
    print(f"  [Claude] Prompt ({len(full)} chars)")
    return _compact_prompt(full)


def _static_prompt(character: dict, pose: str, environment: str, lighting: str) -> str:
    prompt = (
        f"one beautiful anime girl, {character['hair']}, {character['skin']}, "
        f"{character['eyes']}, {character['face']}, {character['vibe']} expression, "
        f"{pose}, {environment}, {lighting}, {QUALITY_SUFFIX}"
    )
    return _compact_prompt(prompt)


# ══════════════════════════════════════════════════════════════════════
# REPLICATE
# ══════════════════════════════════════════════════════════════════════

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
        print("  [Replicate] Token nao configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact_prompt(
        prompt + ", anime-style, one beautiful female character, detailed face, cinematic composition, vivid colors, dramatic lighting, sharp focus, masterpiece"
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
            output_path = str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")
        with open(output_path, "wb") as f:
            f.write(resp.content)
        if os.path.getsize(output_path) < 50_000:
            os.remove(output_path)
            return None
        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
