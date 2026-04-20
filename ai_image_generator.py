"""
ai_image_generator.py — geração visual premium para YouTube Shorts.
Foco: CTR alto, semi-realismo, dark/trap/phonk vibe, variedade visual.
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
# PERSONAGENS — ADULT WOMEN ONLY
# ══════════════════════════════════════════════════════════════════════

CHARACTER_POOL = [
    {"hair": "long straight black hair, center part", "skin": "light porcelain skin", "eyes": "large dark almond eyes", "face": "soft delicate features, small nose", "vibe": "elegant and mysterious"},
    {"hair": "long wavy chestnut brown hair", "skin": "warm olive skin, sun-kissed", "eyes": "expressive brown eyes, long lashes", "face": "high cheekbones, full lips", "vibe": "passionate and bold"},
    {"hair": "platinum blonde in a messy bun", "skin": "fair skin with freckles", "eyes": "sharp blue-grey eyes", "face": "strong jaw, angular features", "vibe": "cool and rebellious"},
    {"hair": "voluminous natural afro with gold pins", "skin": "deep rich brown skin, luminous", "eyes": "large dark expressive eyes", "face": "round face, refined features", "vibe": "powerful and radiant"},
    {"hair": "short edgy purple-black undercut", "skin": "pale cool skin", "eyes": "dramatic violet eyes, heavy eyeliner", "face": "sharp angular face, strong brows", "vibe": "intense and alternative"},
    {"hair": "long flowing auburn hair, loose waves", "skin": "light freckled skin, warm undertone", "eyes": "green eyes, sharp gaze", "face": "pointed chin, confident expression", "vibe": "fierce and free-spirited"},
    {"hair": "silver-white straight bob cut", "skin": "neutral beige skin", "eyes": "glowing silver eyes", "face": "symmetrical refined features", "vibe": "futuristic and ethereal"},
    {"hair": "black hair with neon blue streaks, half-up", "skin": "warm tan skin", "eyes": "dark eyes with colorful shadow", "face": "cute button nose, model-like face", "vibe": "playful and energetic"},
    {"hair": "long dark brown box braids with gold thread", "skin": "medium brown luminous skin", "eyes": "deep brown eyes, intense gaze", "face": "strong jaw, elegant neck", "vibe": "graceful and powerful"},
    {"hair": "soft pastel pink wavy hair", "skin": "soft peach skin", "eyes": "wide rose-pink eyes", "face": "soft face, polished makeup", "vibe": "dreamy and magnetic"},
    {"hair": "long midnight blue hair, pin-straight", "skin": "light cool-toned skin", "eyes": "dark navy eyes, heavy lashes", "face": "high brow, aristocratic features", "vibe": "mysterious and regal"},
    {"hair": "wild curly red hair, untamed", "skin": "warm golden skin", "eyes": "hazel eyes, mischievous glint", "face": "defined cheekbones, bold smile", "vibe": "chaotic and fun"},
    {"hair": "sleek black hair in a high ponytail", "skin": "honey skin tone", "eyes": "almond eyes, cat-eye liner", "face": "sharp cheekbones, confident smirk", "vibe": "badass and cool"},
    {"hair": "teal-dyed twin braids with ribbons", "skin": "fair skin with pink undertones", "eyes": "sky blue eyes", "face": "soft round features, clean makeup", "vibe": "cute and stylish"},
    {"hair": "long ombre brown-to-blonde hair", "skin": "medium warm skin", "eyes": "honey brown eyes", "face": "heart-shaped face, natural beauty", "vibe": "warm and approachable"},
    {"hair": "shaved sides, long dark hair on top", "skin": "deep olive skin", "eyes": "dark piercing eyes", "face": "strong jaw, tattoo on neck", "vibe": "street punk energy"},
    {"hair": "white hair with cherry blossom pins", "skin": "porcelain pale skin", "eyes": "soft pink eyes", "face": "delicate features, editorial makeup", "vibe": "ghostly and delicate"},
    {"hair": "long black hair with red highlights, blowing", "skin": "pale fair skin", "eyes": "crimson red eyes", "face": "sharp dramatic features", "vibe": "dark and intense"},
    {"hair": "short messy brown hair, bedhead style", "skin": "natural tan skin", "eyes": "warm brown eyes, sleepy look", "face": "natural features, subtle smile", "vibe": "cozy and relatable"},
    {"hair": "long silver hair with lavender tips", "skin": "cool fair skin with shimmer", "eyes": "pale lilac eyes", "face": "elegant elven features", "vibe": "magical and otherworldly"},
    {"hair": "fiery orange-red hair, short pixie cut", "skin": "warm brown skin", "eyes": "gold-amber eyes", "face": "strong features, bright energy", "vibe": "bold and fierce"},
    {"hair": "long black hair with galaxy-blue highlights", "skin": "dark smooth skin", "eyes": "glowing blue eyes", "face": "perfect symmetry, model features", "vibe": "cosmic and stunning"},
    {"hair": "messy blonde bob with dark roots", "skin": "light skin, rosy cheeks", "eyes": "grey-green tired eyes", "face": "soft round face, editorial style", "vibe": "indie and effortless"},
    {"hair": "braided crown with flowers", "skin": "medium brown skin", "eyes": "dark almond eyes with shimmer", "face": "graceful features, serene expression", "vibe": "ethereal and natural"},
    {"hair": "long white hair like snow, flowing", "skin": "pale cool skin", "eyes": "ice blue glowing eyes", "face": "sharp cold beauty, stoic expression", "vibe": "frozen and powerful"},
    {"hair": "dark green hair in loose waves", "skin": "warm tan skin", "eyes": "forest green eyes", "face": "earthy natural features", "vibe": "nature spirit energy"},
    {"hair": "black hair with gold geometric patterns", "skin": "rich dark brown skin", "eyes": "golden eyes, regal gaze", "face": "strong beautiful features, queen-like", "vibe": "majestic and divine"},
    {"hair": "neon pink twin tails", "skin": "light skin with star freckles", "eyes": "sparkling magenta eyes", "face": "hyper-stylized beauty features", "vibe": "pop idol energy"},
    {"hair": "long flowing cream-white hair", "skin": "warm ivory skin", "eyes": "soft amber eyes, warm gaze", "face": "gentle angelic features", "vibe": "angelic and serene"},
    {"hair": "short black hair, one eye covered", "skin": "pale skin, subtle dark eye makeup", "eyes": "one visible dark eye, mysterious", "face": "edgy asymmetric look", "vibe": "mysterious and secretive"},
    {"hair": "copper-red hair in loose curls", "skin": "light skin, golden freckles", "eyes": "bright copper eyes", "face": "warm friendly features", "vibe": "wholesome and bright"},
    {"hair": "long black hair with white streak", "skin": "medium cool-toned skin", "eyes": "heterochromia: one blue, one brown", "face": "unique striking features", "vibe": "unique and memorable"},
    {"hair": "bleached white buzz cut", "skin": "dark rich skin", "eyes": "sharp dark eyes", "face": "bold strong features, confidence", "vibe": "avant-garde and bold"},
    {"hair": "long honey-blonde hair with waves", "skin": "sun-kissed warm skin", "eyes": "sea blue eyes, sparkle", "face": "beach-girl natural beauty", "vibe": "sunny and free"},
    {"hair": "sleek brown hair with blunt bangs", "skin": "neutral medium skin", "eyes": "dark brown sharp eyes", "face": "clean classic beauty", "vibe": "smart and composed"},
    {"hair": "wild curly black hair, voluminous", "skin": "rich chocolate skin", "eyes": "dark soulful eyes", "face": "expressive beautiful face", "vibe": "soulful and expressive"},
    {"hair": "long rose-gold wavy hair", "skin": "peachy fair skin", "eyes": "golden-pink eyes", "face": "soft romantic features", "vibe": "romantic and dreamy"},
    {"hair": "black hair pulled back, sharp style", "skin": "olive skin, sharp features", "eyes": "dark intense eyes", "face": "strong jaw, warrior look", "vibe": "warrior and determined"},
    {"hair": "long teal and purple ombre hair", "skin": "light cool skin", "eyes": "teal eyes, artistic makeup", "face": "artistic striking features", "vibe": "artistic and creative"},
    {"hair": "short silver hair, wind-blown", "skin": "warm brown skin", "eyes": "silver glowing eyes", "face": "timeless elegant features", "vibe": "timeless and elegant"},
]

ATTITUDE_VARIATIONS = [
    "confident smirk, dominant energy, strong eye contact",
    "subtle seductive expression, intense gaze, cool attitude",
    "cold expression, slightly arrogant look, dark feminine energy",
    "playful teasing expression, direct eye contact, magnetic presence",
    "unbothered attitude, looking down slightly, expensive aura",
    "mysterious face, half-smile, dangerous elegance",
    "piercing eyes, commanding presence, moody confidence",
    "soft but provocative expression, editorial beauty mood",
]

STYLE_PROFILE = {
    "phonk": {
        "tone": "dark urban drift energy, underground night vibe",
        "palette": "neon purple, crimson red, deep blue, black shadows",
        "fashion": "streetwear, oversized jacket, tactical details, luxury edge",
        "camera": "close-up or medium portrait, dynamic angle, night reflections",
    },
    "trap": {
        "tone": "luxury night energy, dominant aura, expensive lifestyle mood",
        "palette": "purple neon, cold blue, gold highlights, deep black contrast",
        "fashion": "fashion-forward streetwear, leather, chains, designer silhouette",
        "camera": "editorial portrait, strong face framing, premium lighting",
    },
    "rock": {
        "tone": "raw intensity, rebellious performance vibe",
        "palette": "red light, amber glow, black shadows, smoky contrast",
        "fashion": "band aesthetic, dark fitted outfit, stage attitude",
        "camera": "performance portrait, dramatic angle, motion feel",
    },
    "metal": {
        "tone": "dark fantasy aggression, commanding chaos",
        "palette": "black, deep red, ember orange, cold silver accents",
        "fashion": "gothic armor-inspired fashion, black leather, ritual details",
        "camera": "epic portrait, dramatic shadows, powerful silhouette",
    },
    "lofi": {
        "tone": "late-night introspective calm, dreamy mood",
        "palette": "soft blue, purple, warm lamp amber, haze",
        "fashion": "cozy dark casual, hoodie, soft textures",
        "camera": "gentle portrait, soft focus background, intimate framing",
    },
    "indie": {
        "tone": "emotional, artistic, wistful confidence",
        "palette": "golden hour, dusty pink, muted teal, cinematic warmth",
        "fashion": "effortless vintage style, layered textures",
        "camera": "cinematic portrait, natural pose, film-like mood",
    },
    "electronic": {
        "tone": "festival euphoria, futuristic nightlife pulse",
        "palette": "electric blue, magenta, violet glow, laser contrast",
        "fashion": "futuristic nightlife fashion, glossy textures, cyber details",
        "camera": "high-energy portrait, vivid lights, immersive depth",
    },
    "dark": {
        "tone": "haunting beauty, moonlit power, gothic softness",
        "palette": "violet, black, moon blue, silver highlights",
        "fashion": "dark gothic elegance, fitted silhouette, dramatic details",
        "camera": "moody portrait, centered composition, ethereal contrast",
    },
    "default": {
        "tone": "cinematic modern portrait, magnetic presence",
        "palette": "purple blue pink cinematic glow, rich shadows",
        "fashion": "elevated streetwear with editorial styling",
        "camera": "clean portrait, premium framing, depth of field",
    },
}


# ══════════════════════════════════════════════════════════════════════
# POSES
# ══════════════════════════════════════════════════════════════════════

GENRE_POSES = {
    "lofi": [
        "chin resting on hand, sitting at desk, thoughtful gaze",
        "lying on bed face up, holding phone, relaxed expression",
        "sitting at window watching rain, mug in hands",
        "curled up on floor with headphones on, eyes closed",
        "leaning back on chair, feet on desk, relaxed mood",
        "drawing in sketchbook under lamp light",
        "sitting in beanbag chair, calm posture",
        "head tilted, looking out at night city",
        "wrapped in blanket, sipping tea slowly",
        "stretching at desk, tired but composed",
    ],
    "indie": [
        "holding a vinyl record, wistful expression",
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
        "leaning into microphone, fierce eyes",
        "jumping mid-air, guitar in hand",
        "kneeling on stage, head bowed, spotlight",
        "back to audience, facing concert crowd",
        "guitar solo pose, intense and focused",
        "sitting on amp, arms crossed, staring ahead",
        "hair flying with performance energy",
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
        "hand extended, dark energy swirling",
        "eyes glowing, dramatic posture",
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
        "in neon light, calm confident pose",
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
        "standing on speaker, commanding crowd",
        "intense rave portrait pose, neon energy",
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
    "default": [
        "looking directly at camera, commanding",
        "in profile, thoughtful gaze",
        "hand near chin, confident pose",
        "sitting cross-legged, relaxed control",
        "standing in dramatic light, serene confidence",
        "walking toward viewer, magnetic presence",
        "looking up beyond frame, cinematic emotion",
        "arms crossed, knowing smile",
        "head tilted, curious but intense look",
        "silhouette against dramatic light",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# AMBIENTES
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
        "small underground venue, red lights, smoky air",
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
    "default": [
        "dramatic studio, single spotlight, dark background",
        "urban rooftop, golden hour, city below",
        "abstract space, floating light particles",
        "empty theatre stage, single light",
        "endless corridor of mirrors",
        "minimalist dark set, perfect light",
        "underground art gallery, mood lighting",
        "glass building exterior, reflections",
        "park at magic hour, soft mist",
        "old train station, morning light shafts",
    ],
}


LIGHTING_VARIATIONS = [
    "cinematic neon purple and blue glow, high contrast shadows",
    "cold blue moonlight with dramatic rim light",
    "crimson red accent light with deep black shadows",
    "soft diffused light with moody purple undertones",
    "harsh single spotlight, dramatic editorial contrast",
    "city lights bokeh in background, face lit from the side",
    "storm light flashes, dark cinematic atmosphere",
    "violet backlight with glossy highlights",
    "warm amber edge light mixed with cool blue fill",
    "luxury nightclub lighting, reflective glow and shadow depth",
    "wet street reflections and neon spill light",
    "dusty beam of light through window, cinematic haze",
]

QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra-detailed, sharp focus, "
    "semi-realistic, cinematic portrait, ultra realistic skin texture, "
    "9:16 vertical composition, centered subject, single adult woman, "
    "high contrast, depth of field, 85mm lens, bokeh, "
    "detailed eyes, expressive face, polished makeup, "
    "professional photography style, editorial lighting, dramatic mood, "
    "trending tiktok aesthetic, viral thumbnail style, high CTR composition, "
    "no text, no watermark, no extra people, single subject only"
)

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, "
    "split image, collage, multiple people, two girls, crowd focus, "
    "extra arms, extra fingers, deformed hands, bad anatomy, bad eyes, "
    "blurry, muddy, flat lighting, low quality, oversaturated, "
    "child, teenager, baby face, underage, elderly, "
    "nudity, explicit cleavage, bikini, lingerie, fetish, revealing outfit, "
    "cropped face, duplicate face, distorted mouth, generic background"
)


def _seed_from(filename: str, short_num: int) -> int:
    key = f"{filename}_{short_num}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _seeded_choice(pool: list, seed: int, extra_offset: int = 0):
    rng = random.Random(seed + extra_offset)
    return rng.choice(pool)


def _pick_character(filename: str, short_num: int) -> dict:
    seed = _seed_from(filename, short_num)
    return _seeded_choice(CHARACTER_POOL, seed, 0)


def _pick_attitude(filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    return _seeded_choice(ATTITUDE_VARIATIONS, seed, 4)


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


def _compact_prompt(text: str, max_chars: int = 1100) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)
    character = _pick_character(filename, short_num)
    attitude = _pick_attitude(filename, short_num)
    pose = _pick_pose(style, filename, short_num)
    environment = _pick_environment(style, filename, short_num)
    lighting = _pick_lighting(filename, short_num)
    profile = STYLE_PROFILE.get(style, STYLE_PROFILE["default"])
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                character=character,
                attitude=attitude,
                pose=pose,
                environment=environment,
                lighting=lighting,
                profile=profile,
            )
        except Exception as e:
            print(f"  [Claude] Falha no prompt: {e} — fallback")

    return _static_prompt(
        style=style,
        character=character,
        attitude=attitude,
        pose=pose,
        environment=environment,
        lighting=lighting,
        profile=profile,
    )


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    character: dict,
    attitude: str,
    pose: str,
    environment: str,
    lighting: str,
    profile: dict,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are a master visual director for a premium YouTube Shorts music channel. "
        "Create elite Flux prompts for scroll-stopping vertical cover art. "
        "The image must feature exactly ONE adult woman, central subject, cinematic, seductive only in a subtle platform-safe way, never explicit, never underage. "
        "Output ONLY the prompt in English, comma-separated, no explanation, no quotes."
    )

    user = f"""Create a premium image prompt for a vertical YouTube music Short.

Song: "{song_name}"
Genre: {style} ({all_styles})

Character:
Hair: {character['hair']}
Skin: {character['skin']}
Eyes: {character['eyes']}
Face: {character['face']}
Vibe: {character['vibe']}
Expression / attitude: {attitude}

Pose: {pose}
Environment: {environment}
Lighting: {lighting}

Style profile:
Tone: {profile['tone']}
Palette: {profile['palette']}
Fashion: {profile['fashion']}
Camera: {profile['camera']}

Rules:
- Exactly one adult woman
- Semi-realistic, premium editorial, cinematic portrait
- Platform-safe, subtle seductive energy only, not explicit
- Strong eyes and expression for click-through rate
- Dark, stylish, memorable
- 9:16 vertical, centered subject, premium composition
- 70-120 words, comma-separated
- No text, no watermark, no extra people"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=280,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    prompt = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{prompt}, {QUALITY_SUFFIX}"
    print(f"  [Claude] Prompt ({len(full)} chars)")
    return _compact_prompt(full)


def _static_prompt(
    style: str,
    character: dict,
    attitude: str,
    pose: str,
    environment: str,
    lighting: str,
    profile: dict,
) -> str:
    prompt = (
        f"one adult woman, semi-realistic cinematic portrait, "
        f"{character['hair']}, {character['skin']}, {character['eyes']}, {character['face']}, "
        f"{character['vibe']}, {attitude}, "
        f"{profile['fashion']}, {profile['tone']}, {profile['palette']}, {profile['camera']}, "
        f"{pose}, {environment}, {lighting}, "
        f"strong eye contact, expressive face, subtle provocative energy, platform-safe styling, "
        f"luxury visual direction, polished skin texture, dramatic shadows, glossy highlights, "
        f"{QUALITY_SUFFIX}"
    )
    return _compact_prompt(prompt)


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
        prompt
        + ", premium editorial portrait, one adult woman, semi-realistic, "
          "cinematic composition, dark feminine energy, detailed face, sharp eyes, "
          "high contrast, dramatic lighting, premium skin texture, masterpiece"
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
