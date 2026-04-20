"""
ai_image_generator.py — Sistema visual premium para YouTube Shorts.
Foco: máxima variedade visual por gênero, anti-shadowban, alta qualidade anime.
Cada short de cada música recebe uma combinação única de personagem + cena + iluminação.
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
# PERSONAGENS — 40 MULHERES ADULTAS ANIME COM IDENTIDADES ÚNICAS
# ══════════════════════════════════════════════════════════════════════

CHARACTER_POOL = [
    {
        "id": "C01",
        "hair": "long straight jet-black hair past her waist, sharp bangs",
        "skin": "pale porcelain skin with cool undertones",
        "eyes": "large dark crimson eyes with heavy lashes",
        "face": "sharp angular features, high cheekbones, thin lips",
        "body": "slender tall figure, elegant posture",
        "vibe": "cold aristocratic beauty, untouchable aura",
        "style_affinity": ["dark", "metal", "trap"],
    },
    {
        "id": "C02",
        "hair": "voluminous natural afro with loose coils, adorned with gold pins",
        "skin": "deep rich mahogany skin with luminous sheen",
        "eyes": "large warm dark eyes framed by thick lashes",
        "face": "bold rounded features, full lips, strong jawline",
        "body": "powerful athletic figure, confident stance",
        "vibe": "radiant warrior queen energy, magnetic presence",
        "style_affinity": ["rock", "metal", "electronic"],
    },
    {
        "id": "C03",
        "hair": "platinum white short bob with dark roots showing",
        "skin": "fair skin with faint freckles on nose bridge",
        "eyes": "sharp icy blue-grey eyes, cat-eye liner",
        "face": "strong jaw, androgynous features, piercing at brow",
        "body": "lean athletic build, street-ready posture",
        "vibe": "rebellious punk edge, controlled chaos energy",
        "style_affinity": ["rock", "phonk", "electronic"],
    },
    {
        "id": "C04",
        "hair": "long flowing auburn waves with copper highlights",
        "skin": "warm golden-tan skin, sun-kissed",
        "eyes": "bright hazel eyes with amber flecks",
        "face": "heart-shaped face, defined cheekbones, natural beauty",
        "body": "lithe graceful figure, dancer's posture",
        "vibe": "fierce free spirit, untamed natural energy",
        "style_affinity": ["indie", "lofi", "rock"],
    },
    {
        "id": "C05",
        "hair": "midnight blue hair with electric teal streaks, half-up style",
        "skin": "warm tan skin with subtle shimmer",
        "eyes": "vivid violet eyes with digital-glow effect",
        "face": "symmetrical editorial features, sharp cat-eye makeup",
        "body": "slim with soft curves, cyberpunk fashion silhouette",
        "vibe": "cyberpunk idol, future-tech glamour",
        "style_affinity": ["electronic", "trap", "phonk"],
    },
    {
        "id": "C06",
        "hair": "long silver-white hair with lavender ombre tips, wind-blown",
        "skin": "moonlit pale skin with faint blue undertone",
        "eyes": "glowing pale lilac eyes, otherworldly gaze",
        "face": "ethereal elven features, high brow, delicate nose",
        "body": "tall willowy figure, supernatural grace",
        "vibe": "moon goddess energy, spectral elegance",
        "style_affinity": ["dark", "lofi", "indie"],
    },
    {
        "id": "C07",
        "hair": "fiery orange-red pixie cut with shaved sides",
        "skin": "warm medium brown skin, glowing",
        "eyes": "blazing amber-gold eyes, intense stare",
        "face": "bold strong features, confident smirk, earrings",
        "body": "compact powerful build, explosive energy",
        "vibe": "wild card energy, unpredictable fire",
        "style_affinity": ["rock", "metal", "electronic"],
    },
    {
        "id": "C08",
        "hair": "long dark brown box braids with gold thread woven in",
        "skin": "smooth medium-brown skin, warm undertones",
        "eyes": "deep soulful brown eyes, knowing gaze",
        "face": "graceful angular features, elegant neck, subtle makeup",
        "body": "statuesque figure, queenly bearing",
        "vibe": "old soul wisdom, quiet unstoppable power",
        "style_affinity": ["indie", "lofi", "dark"],
    },
    {
        "id": "C09",
        "hair": "glossy black hair in a sharp high ponytail",
        "skin": "cool light skin, flawless",
        "eyes": "narrow dark eyes with dramatic winged liner",
        "face": "razor-sharp cheekbones, controlled expression, no-nonsense",
        "body": "athletic precise build, combat-ready posture",
        "vibe": "elite assassin calm, dangerous precision",
        "style_affinity": ["phonk", "trap", "dark"],
    },
    {
        "id": "C10",
        "hair": "wild curly neon pink hair, voluminous and untamed",
        "skin": "light skin with scattered star-shaped freckles",
        "eyes": "sparkling magenta eyes, playful glint",
        "face": "round cute features, bright energy, pierced lip",
        "body": "petite but dynamic, hyperactive energy",
        "vibe": "pop chaos energy, loveable mayhem",
        "style_affinity": ["electronic", "indie", "phonk"],
    },
    {
        "id": "C11",
        "hair": "long straight black hair with blood-red underlayer visible",
        "skin": "pale cool skin with visible tattoo on collarbone",
        "eyes": "striking red heterochromia left eye, dark right",
        "face": "dramatic sharp features, dark lip color, neck tattoos",
        "body": "lean with visible strength, gothic fashion",
        "vibe": "gothic queen of the underground",
        "style_affinity": ["metal", "dark", "phonk"],
    },
    {
        "id": "C12",
        "hair": "long honey-blonde waves catching golden light",
        "skin": "sun-kissed warm skin, healthy glow",
        "eyes": "warm sea-blue eyes, genuine smile reaching them",
        "face": "natural radiant beauty, dimples, effortless charm",
        "body": "athletic beach-body energy, open confident stance",
        "vibe": "golden hour energy, magnetic warmth",
        "style_affinity": ["indie", "lofi", "rock"],
    },
    {
        "id": "C13",
        "hair": "short silver buzz cut with geometric shaved pattern",
        "skin": "deep dark skin, cool undertones, commanding",
        "eyes": "sharp silver eyes, avant-garde makeup",
        "face": "bold geometric features, high-fashion editorial",
        "body": "tall imposing figure, runway model energy",
        "vibe": "avant-garde fashion icon, future aesthetics",
        "style_affinity": ["electronic", "trap", "dark"],
    },
    {
        "id": "C14",
        "hair": "long rose-gold wavy hair with soft curls",
        "skin": "peachy fair skin, soft pink flush",
        "eyes": "warm golden-rose eyes, romantic gaze",
        "face": "soft elegant features, classical beauty, gentle smile",
        "body": "graceful feminine figure, balletic posture",
        "vibe": "romantic melancholy, soft power",
        "style_affinity": ["lofi", "indie", "dark"],
    },
    {
        "id": "C15",
        "hair": "black hair with galaxy-blue highlights, loose and flowing",
        "skin": "flawless dark skin with cosmic shimmer effect",
        "eyes": "glowing electric blue eyes, unreal beauty",
        "face": "perfect symmetrical features, model-tier face",
        "body": "long-limbed graceful build, cosmic presence",
        "vibe": "star-born goddess, universe-level confidence",
        "style_affinity": ["electronic", "trap", "dark"],
    },
    {
        "id": "C16",
        "hair": "messy dark teal twin braids with ribbon ties",
        "skin": "fair skin with pink undertones, animated blush",
        "eyes": "large sky-blue eyes, expressive",
        "face": "soft round features, clean fresh makeup, small nose",
        "body": "average height, cozy comfortable energy",
        "vibe": "neighborhood girl with secret depths",
        "style_affinity": ["lofi", "indie", "phonk"],
    },
    {
        "id": "C17",
        "hair": "long white hair with cherry blossom hairpins",
        "skin": "porcelain translucent skin, ghostly pale",
        "eyes": "soft pink eyes, sorrowful haunted look",
        "face": "delicate ghostlike features, editorial minimalist makeup",
        "body": "slim ethereal silhouette, floats rather than walks",
        "vibe": "beautiful ghost, tragedy and grace",
        "style_affinity": ["dark", "lofi", "indie"],
    },
    {
        "id": "C18",
        "hair": "short choppy brown hair, perpetual bedhead, messy",
        "skin": "natural tan skin, relaxed",
        "eyes": "warm amber-brown eyes, sleepy half-lidded",
        "face": "natural casual features, genuine unposed look",
        "body": "normal relatable build, cozy hoodie energy",
        "vibe": "3am realness, raw and authentic",
        "style_affinity": ["lofi", "indie", "phonk"],
    },
    {
        "id": "C19",
        "hair": "sleek dark brown with razor-straight blunt bangs",
        "skin": "neutral medium beige skin, clean",
        "eyes": "intense dark eyes, calculating gaze",
        "face": "composed classic features, minimal precise makeup",
        "body": "lean disciplined posture, controlled movements",
        "vibe": "chess master energy, always three moves ahead",
        "style_affinity": ["trap", "phonk", "dark"],
    },
    {
        "id": "C20",
        "hair": "long teal-to-purple ombre hair, artistically styled",
        "skin": "light skin with cool undertones, artistic markings",
        "eyes": "teal eyes with artistic galaxy makeup around them",
        "face": "creative striking features, expressive",
        "body": "dynamic expressive figure, artist energy",
        "vibe": "living artwork, creative genius persona",
        "style_affinity": ["electronic", "indie", "lofi"],
    },
    {
        "id": "C21",
        "hair": "long flowing crimson red hair, dramatic movement",
        "skin": "warm ivory skin, flushed cheeks",
        "eyes": "striking green eyes with gold flecks, fierce",
        "face": "bold dramatic features, strong brows, red lip",
        "body": "statuesque commanding figure, fire energy",
        "vibe": "femme fatale confidence, dangerous beauty",
        "style_affinity": ["rock", "metal", "dark"],
    },
    {
        "id": "C22",
        "hair": "black hair with exactly one stark white streak from temples",
        "skin": "cool medium skin, mysterious quality",
        "eyes": "heterochromia: blue left, brown right, unforgettable",
        "face": "unique memorable features, doesn't blend in",
        "body": "medium athletic build, always ready",
        "vibe": "chosen one energy, unique in every crowd",
        "style_affinity": ["dark", "metal", "phonk"],
    },
    {
        "id": "C23",
        "hair": "long wild curly black hair, full and dramatic",
        "skin": "rich chocolate-brown skin, luminous",
        "eyes": "deep expressive dark eyes, full of emotion",
        "face": "expressive beautiful face, tells stories without words",
        "body": "full-figured with power and grace",
        "vibe": "soulful depth, emotional artistry",
        "style_affinity": ["indie", "lofi", "rock"],
    },
    {
        "id": "C24",
        "hair": "jet-black undercut with long top pulled back sharply",
        "skin": "deep olive skin, sharp angles",
        "eyes": "dark piercing eyes, tattooed at corners",
        "face": "strong defined jaw, neck tattoo, street-smart beauty",
        "body": "muscular lean build, street warrior presence",
        "vibe": "urban warrior, respect earned not given",
        "style_affinity": ["phonk", "trap", "metal"],
    },
    {
        "id": "C25",
        "hair": "neon green hair in twin high pigtails, cyberpunk style",
        "skin": "pale skin with UV-reactive freckle tattoos",
        "eyes": "glowing green bionic eyes, hacker aesthetic",
        "face": "sharp tech-punk features, facial LED accents",
        "body": "wiry quick build, always ready to run",
        "vibe": "system hacker, lives in the grid",
        "style_affinity": ["electronic", "phonk", "trap"],
    },
    {
        "id": "C26",
        "hair": "long dark green hair in loose romantic waves",
        "skin": "warm tan skin with earthy quality",
        "eyes": "forest-green eyes, deep and calm",
        "face": "earthy natural features, flower crown nearby",
        "body": "lithe natural figure, moves like water",
        "vibe": "forest spirit made human, ancient calm",
        "style_affinity": ["indie", "lofi", "dark"],
    },
    {
        "id": "C27",
        "hair": "shaved to skin on sides, long braided mohawk on top, black",
        "skin": "warm dark brown skin, battle-scarred beauty",
        "eyes": "amber eyes, warrior stare",
        "face": "strong fierce features, war paint makeup aesthetic",
        "body": "powerful muscular build, warrior stance",
        "vibe": "ancient warrior reborn in modern world",
        "style_affinity": ["metal", "rock", "phonk"],
    },
    {
        "id": "C28",
        "hair": "soft pastel lilac wavy hair, dreamy and soft",
        "skin": "warm peach skin with rosy glow",
        "eyes": "wide violet eyes, stars in them",
        "face": "angelic soft face, polished romantic makeup",
        "body": "petite delicate figure, floaty movements",
        "vibe": "dreaming while awake, soft magic",
        "style_affinity": ["lofi", "indie", "dark"],
    },
    {
        "id": "C29",
        "hair": "black hair with gold-painted geometric patterns",
        "skin": "rich dark brown skin, royal sheen",
        "eyes": "golden eyes, regal gaze that commands rooms",
        "face": "strong sculptural features, jeweled accessories",
        "body": "tall powerful commanding build, born to rule",
        "vibe": "divine queen, beyond reproach",
        "style_affinity": ["trap", "dark", "electronic"],
    },
    {
        "id": "C30",
        "hair": "ice-white long hair that moves like it's underwater",
        "skin": "pale cool skin, lips faintly blue",
        "eyes": "ice-blue eyes that seem to freeze on contact",
        "face": "cold sculpted features, stoic expression",
        "body": "tall and still, glacier-like presence",
        "vibe": "frozen in power, unmovable force",
        "style_affinity": ["dark", "metal", "electronic"],
    },
    {
        "id": "C31",
        "hair": "copper-red loose curls with golden highlights",
        "skin": "light skin with golden freckles",
        "eyes": "bright copper eyes, warm and welcoming",
        "face": "warm genuine features, easy authentic smile",
        "body": "average friendly build, approachable energy",
        "vibe": "unexpected depth, you underestimate her",
        "style_affinity": ["indie", "lofi", "rock"],
    },
    {
        "id": "C32",
        "hair": "bleached near-white with black tips, short sharp cut",
        "skin": "dark rich skin, flawless",
        "eyes": "sharp dark eyes with dramatic white graphic liner",
        "face": "bold editorial features, avant-garde makeup",
        "body": "commanding tall build, walks like she's on a runway",
        "vibe": "fashion week energy, defines the trend",
        "style_affinity": ["electronic", "trap", "dark"],
    },
    {
        "id": "C33",
        "hair": "long straight black hair with subtle dark purple sheen",
        "skin": "cool ivory skin, precise",
        "eyes": "deep purple eyes, rarely blinks",
        "face": "perfectly composed features, no wasted expression",
        "body": "lithe controlled figure, moves with purpose",
        "vibe": "still water runs deep, you fear what's beneath",
        "style_affinity": ["dark", "phonk", "trap"],
    },
    {
        "id": "C34",
        "hair": "wild tangled dark blue hair, wind-blown perpetually",
        "skin": "medium olive skin, restless energy",
        "eyes": "stormy blue-grey eyes, always scanning",
        "face": "dynamic expressive features, laughs easily, cries harder",
        "body": "lean energetic build, always in motion",
        "vibe": "storm given a human form",
        "style_affinity": ["rock", "indie", "electronic"],
    },
    {
        "id": "C35",
        "hair": "perfectly braided crown of black hair with gold thread",
        "skin": "warm medium brown skin with golden shimmer",
        "eyes": "dark expressive eyes with luminous shadow",
        "face": "serene graceful features, timeless beauty",
        "body": "balanced elegant figure, stillness as power",
        "vibe": "timeless grace, center of any room",
        "style_affinity": ["lofi", "indie", "dark"],
    },
    {
        "id": "C36",
        "hair": "short spiky bi-color: black base with electric yellow tips",
        "skin": "warm tan skin, energetic",
        "eyes": "vivid yellow-green eyes, adrenaline in them",
        "face": "sharp impish features, permanent grin",
        "body": "compact explosive build, springs everywhere",
        "vibe": "human lightning bolt, too fast to catch",
        "style_affinity": ["electronic", "rock", "phonk"],
    },
    {
        "id": "C37",
        "hair": "long wavy dark hair with deep wine-red ombre",
        "skin": "warm medium skin, rich tone",
        "eyes": "dark wine-colored eyes, depth like a painting",
        "face": "Renaissance painting beauty, classic and timeless",
        "body": "balanced feminine figure, painter's ideal",
        "vibe": "art come to life, classical soul in modern world",
        "style_affinity": ["indie", "dark", "lofi"],
    },
    {
        "id": "C38",
        "hair": "long silver hair with rainbow prism streaks caught in light",
        "skin": "cool fair skin with holographic shimmer",
        "eyes": "prismatic shifting eyes, each angle a new color",
        "face": "futuristic perfect features, post-human beauty",
        "body": "otherworldly proportions, effortless alien grace",
        "vibe": "arrived from a better future",
        "style_affinity": ["electronic", "dark", "trap"],
    },
    {
        "id": "C39",
        "hair": "long caramel-brown hair with natural beachy waves",
        "skin": "medium warm skin, natural glow",
        "eyes": "honey-brown eyes, genuine depth",
        "face": "girl-next-door beauty with hidden intensity",
        "body": "athletic natural build, comfortable in herself",
        "vibe": "real over perfect, authentic intensity",
        "style_affinity": ["indie", "lofi", "rock"],
    },
    {
        "id": "C40",
        "hair": "thick long black hair worn loose, ink-dark",
        "skin": "warm dark brown skin, moonlit quality",
        "eyes": "large dark eyes with inner fire",
        "face": "strong traditional beauty, defiant expression",
        "body": "powerful full figure, unstoppable presence",
        "vibe": "ancient fire, modern force",
        "style_affinity": ["metal", "dark", "rock"],
    },
]

# ══════════════════════════════════════════════════════════════════════
# EXPRESSÕES ESPECÍFICAS POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_EXPRESSIONS = {
    "phonk": [
        "cold empty stare, emotionless but radiating power",
        "slight smirk, like she knows something you don't",
        "jaw set, staring through you not at you",
        "half-lidded eyes, unfazed by everything",
        "looking over shoulder with quiet menace",
    ],
    "trap": [
        "chin raised, closed lips, dripping superiority",
        "one brow up, daring you to say something",
        "blank expensive expression, unbothered millionaire stare",
        "slow confident smile, like she just won",
        "side-eye with a smirk, knows her worth",
    ],
    "rock": [
        "eyes closed, lost in sound, pure performance",
        "teeth bared in fierce joy, screaming into it",
        "wild eyes, in the zone, electric",
        "head thrown back mid-note, fully committed",
        "direct confrontational stare, challenging the crowd",
    ],
    "metal": [
        "expressionless power, ancient force looking through you",
        "slow dark smile, the calm before catastrophe",
        "serene and terrifying, eyes full of dark knowledge",
        "stoic warrior expression, battle-calm",
        "intense downward gaze, ritual focus",
    ],
    "lofi": [
        "dreamy half-smile, lost in thought",
        "soft melancholy gaze out the window",
        "peaceful closed eyes, headphones on, gone",
        "tired but content, comfortable sadness",
        "quiet small smile, 3am clarity",
    ],
    "indie": [
        "wistful distant look, thinking of someone",
        "genuine unguarded emotion, raw and real",
        "soft surprised expression, just felt something",
        "quiet confident smile, knows who she is",
        "looking up at sky, searching for something",
    ],
    "electronic": [
        "ecstatic eyes closed, transported by the drop",
        "euphoric open smile, arms in the air energy",
        "intense focus mid-set, in command",
        "blazing eyes, crowd-staring commander",
        "half-smile with glowing eyes, in the zone",
    ],
    "dark": [
        "haunted knowing eyes, has seen too much",
        "ethereal blank gaze, not quite here",
        "slow sad smile, beautiful melancholy",
        "intense piercing stare, reads souls",
        "closed eyes, communing with darkness",
    ],
    "default": [
        "magnetic confident look, center of gravity",
        "cool measured expression, total control",
        "slight smile with knowing eyes",
        "direct powerful gaze, unshakeable",
        "contemplative look, processing something deep",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# POSES DETALHADAS POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_POSES = {
    "lofi": [
        "sitting cross-legged on floor, back against bed, arms resting on knees, full body visible, cozy compact pose",
        "lying on stomach on bed, feet up, chin resting on hands, full body in frame, lazy comfortable pose",
        "sitting sideways on windowsill, one leg inside one leg outside, looking at city below, full body shot",
        "curled up in oversized chair, knees to chest, headphones around neck, full figure visible",
        "sitting at cluttered desk, leaning back in chair, arms stretched above head, full body in frame",
        "kneeling on floor beside record player, hand reaching toward vinyl, full body visible, intimate moment",
        "standing by rain-streaked window, one hand on glass, full body silhouette against city glow",
        "seated on floor against bookshelf, surrounded by books, reading in pool of lamp light, full figure",
    ],
    "indie": [
        "standing on rooftop edge, arms out like wings, city behind her, full body visible, freedom pose",
        "walking barefoot through long grass, arms trailing, full body shot from behind and side",
        "sitting on car hood in empty lot, knees up, looking at stars, full body relaxed",
        "leaning back against chain-link fence, fingers hooked in fence behind her, full body shot",
        "spinning in empty street, one arm out, hair flying, full body in motion",
        "sitting on old wooden dock, feet dangling over water, full body side profile",
        "kneeling in field of wildflowers, holding one bloom to lips, full body in golden light",
        "standing in doorway of old building, one shoulder on frame, half-light half-shadow, full figure",
    ],
    "rock": [
        "legs wide, guitar overhead both arms raised, victorious stage pose, full body power shot",
        "gripping mic stand with both hands, leaning weight forward, full body commitment",
        "mid-jump off drum riser, frozen in air, full body visible, crowd below",
        "kneeling center stage, fist raised to sky, spotlight from above, full body dramatic",
        "back to audience, both arms out, full body silhouette against wall of lights",
        "sitting on edge of amp, legs dangling, guitar in lap, full body relaxed power",
        "crouched low at stage front, reaching to crowd, full body dynamic low angle",
        "standing still in chaos, center stage, eyes closed in performance trance, full body shot",
    ],
    "metal": [
        "standing in summoning circle, arms raised to storm sky, full body commanding ritual pose",
        "walking through fire and embers, full body visible, flames framing silhouette",
        "atop collapsed stonework, sword raised, full body warrior queen shot",
        "kneeling in ruins, one arm pressing ground, head bowed in power, full body",
        "standing back to viewer at cliff edge, storm beyond, full body silhouette composition",
        "chained but defiant, standing tall, chains falling away, full body liberation pose",
        "descending dark cathedral steps, cloak flowing, full body shot from below looking up",
        "sitting on throne of stone, legs crossed, one elbow on armrest, commanding full body",
    ],
    "phonk": [
        "leaning on hood of car, arms crossed, one ankle crossed over other, full body nonchalant",
        "sitting on car roof, one knee up, looking at city below, full body casual power",
        "standing under flickering streetlight, hands in jacket pockets, full body night silhouette",
        "walking through underground parking, hoodie half-up, looking back over shoulder, full body",
        "crouching on concrete barrier, balanced, looking down at camera, full body street pose",
        "leaning against graffiti wall, one foot up on wall behind, full body relaxed dominance",
        "sitting on steps of empty stairwell, elbows on knees, direct gaze, full body shot",
        "standing in tunnel entrance, backlit by headlights, full body silhouette emerging",
    ],
    "trap": [
        "standing at penthouse window, city at night behind, one hand on glass, full body luxury",
        "seated backward on white leather chair, arms on backrest, full body commanding",
        "lying across marble steps, propped on one elbow, full body composed luxury",
        "standing in rain of soft gold light, arms at sides, chin up, full body regal",
        "leaning against luxury car, arms folded, one heel raised, full body wealth stance",
        "sitting on edge of elevated pool, feet in water, city below, full body nighttime luxury",
        "walking toward viewer, looking straight ahead, city blurred behind, full body power walk",
        "standing on rooftop helipad, wind in hair, full body shot above city",
    ],
    "electronic": [
        "arms wide on festival stage, crowd as ocean before her, full body shot from behind into crowd",
        "spinning on podium, body mid-rotation, laser beams crossing around her, full body dynamic",
        "standing in center of circular LED rig, lights behind, full body centered composition",
        "crowd surfing, lifted by hands, full body horizontal over sea of people",
        "leaning into DJ booth, one arm on turntable, other raised, full body performance",
        "standing in tunnel of strobing lights, motion blur behind, full body sharp",
        "jumping from speaker stack, full body airborne, crowd below, pure euphoria",
        "kneeling at stage front, fingers touching crowd hands, full body emotional connection",
    ],
    "dark": [
        "standing in moonlit cemetery, long cloak, full body night composition",
        "floating inches off ground, arms at sides, full body ethereal levitation",
        "kneeling before altar of candles, arms spread wide, full body ritual pose",
        "standing alone in abandoned ballroom, dust motes in single light beam, full body",
        "walking through deep fog, barely visible, full body emerging from mist",
        "sitting on stone wall at cliff edge, legs dangling over darkness, full body side shot",
        "standing in rain, eyes closed, arms slightly out, accepting the storm, full body",
        "descending stone steps into dark water reflection, full body composition",
    ],
    "default": [
        "standing in dramatic single spotlight, full body centered, everything else dark",
        "walking down empty corridor, full body shot from the side, destination unknown",
        "standing on rooftop, wind in hair, city below, full body confident",
        "sitting cross-legged elevated above ground, full body floating composition",
        "full body profile against massive glass window with city beyond",
        "standing with back straight looking up at something vast, full body small against scene",
        "seated on edge of something high, full body silhouette against dramatic sky",
        "walking toward camera out of shadow into light, full body emergence shot",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# AMBIENTES CINEMATOGRÁFICOS POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_ENVIRONMENTS = {
    "lofi": [
        "cozy cluttered bedroom, warm amber desk lamp, rain streaking tall windows, city lights softened outside, plants on sill, vinyl records stacked, fairy lights above",
        "tiny Tokyo apartment kitchen, 3am blue light from refrigerator, steam rising from kettle, rain on metal roof, city noise muted",
        "college dorm room, laptop glow as only light, headphone cable tangled, open textbooks, outside window just darkness and quiet stars",
        "wooden attic studio, slanted ceiling, single bulb swinging gently, rain drumming above, books stacked in towers, dusty warmth",
        "café after closing, one staff member still there, wet street visible through fogged window, chairs on tables, last cup of tea",
        "childhood bedroom now empty, moonlight through curtain gap, floor mattress, single candle, most things packed away, end of era feeling",
        "library reading corner, closing time, one lamp still on, snow falling outside window barely visible, silence and paper smell",
        "train at 2am, empty car, window showing passing city lights blurred, orange overhead lighting, absolute stillness",
    ],
    "indie": [
        "golden hour rooftop garden, wildflowers in broken concrete, city skyline soft behind, warm orange sky melting to blue",
        "empty country road at dawn, mist hovering waist-high, single car in distance, endless quiet",
        "abandoned greenhouse overgrown, plants through cracked glass, afternoon light in shafts, life reclaiming space",
        "seaside cliff with crumbling lighthouse, ocean crashing below, overcast dramatic sky with light breaking through",
        "vintage record store afternoon, dust in sunbeams, record covers on every wall, warm wood and old fabric smell",
        "small town bridge at magic hour, river gold below, old streetlights flickering on, first stars appearing",
        "rolling sunflower field, one person alone in it, late afternoon, wind bending stalks in waves",
        "back alley with a single mural, warm lamplight, rain-slick cobblestones reflecting neon, intimate and forgotten",
    ],
    "rock": [
        "stadium stage mid-concert, ocean of phone lights below, backline of full Marshall stacks, spotlights cutting through smoke",
        "empty arena pre-show, lone figure, single spotlight, rows of empty seats reaching into shadow, massive scale",
        "outdoor festival in incoming storm, dark clouds split by stage lights, crowd energy matching the weather",
        "tiny underground venue, red stage lights, sweat on walls, speakers stacked floor-to-ceiling, intimate chaos",
        "rooftop in industrial district, water towers and brick behind, dusk sky, city sound rising from below",
        "recording studio at 3am, half-eaten takeout, gear everywhere, session musician's natural habitat",
        "alley behind a venue, tour bus idling, graffiti walls, the only light from an open door down the way",
        "bridge over industrial river, rust and steel, harsh security light above, defiant against the infrastructure",
    ],
    "metal": [
        "volcanic mountain at eruption, lava rivers below, ash storm in sky, apocalyptic orange-black palette",
        "ancient ruined castle, tower crumbling, lightning striking repeatedly, storm summoned for occasion",
        "deep forest of dead trees, blood-red moon, ground mist, absolute silence before terrible sound",
        "gothic cathedral interior, massive broken rose window, candle ranks, centuries of silence disturbed",
        "barren wasteland, no horizon visible, lightning chains across total sky, scorched earth in all directions",
        "underground cave system, vast chamber, black crystals glowing deep purple, cathedral of stone",
        "cliff over storm-churned ocean, waves violent below, figure above the chaos, hair and cloak violent",
        "abandoned black-stone fortress, ember fires in niches, chains hanging, throne room of a dark power",
    ],
    "phonk": [
        "underground parking structure 3am, single red fluorescent flickering, rain noise echoing in concrete, tire marks on floor",
        "empty six-lane highway at night, distant headlights only light, road markings hypnotic, total isolation",
        "rooftop parking deck top floor, city grid in every direction below, no railing, raw exposure",
        "narrow city alley, neon signs in foreign language above, steam from grate, wet surface reflecting",
        "gaslit underpass, bridge structure above, graffiti tags, water dripping, single car passing",
        "freight rail yard night, industrial lights on tall poles, massive rail cars in darkness, concrete and rust",
        "basement parking entry ramp, orange light from below, darkness above, the threshold feeling",
        "empty industrial port, shipping containers stacked, crane lights, water dark beside, total silence",
    ],
    "trap": [
        "penthouse at altitude, floor-to-ceiling glass, city grid below, infinity pool at edge, night absolute luxury",
        "private jet interior, leather and wood trim, night cloud below through oval windows, champagne",
        "high-rise hotel suite, unmade bed, service tray, full city panorama through wall of glass, dawn light",
        "luxury nightclub VIP section, booth with bottle service, dance floor below, light show in distance",
        "designer car showroom after hours, exotic cars in darkness lit only by city glow through glass facade",
        "yacht deck at open sea, no land visible, sunset, absolute freedom and wealth compressed into image",
        "rooftop helipad empty, city at feet, sky above, wind, the top of the world feeling",
        "marble-floored mansion corridor, chandeliers dim, portraits on walls, absolute silence of old money",
    ],
    "electronic": [
        "festival mainstage seen from wings, crowd to horizon, laser array firing, smoke and bass frequency visible",
        "warehouse rave, industrial ceiling high above, single beam lighting dance floor, human mass in rhythm",
        "desert festival, stars above, LED stage in middle of nothing, thousands dancing around it",
        "holographic dome venue, projections on every surface, impossible geometry, immersive total environment",
        "futuristic underground club, geometry in light, chrome surfaces, bass so low it bends the image",
        "outdoor stage at sunset, sky on fire behind, crowd silhouettes below, the sacred moment before drop",
        "massive LED tunnel entrance to festival, figure walking through, pulsing passage, transformation",
        "boat on open water at night, floating rave, city distant, water reflecting all lights, surrounded by sound",
    ],
    "dark": [
        "moonlit ruined cathedral, no roof, sky full of impossible stars, stone worn smooth by centuries",
        "deep midnight forest, silver birch trunks, single path through, full moon directly overhead, silence",
        "abandoned victorian ballroom, dust sheets on everything, single chandelier burning impossibly, decay and beauty",
        "cliff edge in storm, rain horizontal, figure against the weather, ocean chaos far below in darkness",
        "ancient cemetery, stone crosses tilted by centuries, ground mist knee-high, single lantern somewhere distant",
        "flooded crypt, candles floating on black water, arched ceiling above, absolute silence and weight",
        "lighthouse room at top, storm outside, lantern casting rotating shadow, isolation and duty",
        "Victorian greenhouse in ruins, glass panes mostly broken, ivy reclaimed everything, night sky through frame",
    ],
    "default": [
        "dramatic single spotlight in infinite darkness, everything outside the light nonexistent",
        "urban rooftop at golden hour, water tower behind, city below dissolving in warm light",
        "abstract space with floating light particles like fireflies, background suggesting vast distance",
        "massive empty theater stage, single working light, rows of seats in shadow, moment before everything",
        "endless mirrored corridor, infinite reflections diminishing, standing at the origin point",
        "glass skyscraper exterior at night, reflections of another city, vertiginous and beautiful",
        "park at fog-thick night, single lamp illuminating perfect circle, rest of world erased",
        "old abandoned train station, morning light shafts through grime-caked glass, ghost-architecture",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# ILUMINAÇÕES ESPECÍFICAS E CINEGRÁFICAS
# ══════════════════════════════════════════════════════════════════════

GENRE_LIGHTING = {
    "phonk": [
        "single red neon tube reflection on wet concrete, everything else near-black, high contrast",
        "orange sodium vapor streetlight from above, harsh cold shadow below, noir feel",
        "purple neon sign spill from out of frame, one-sided dramatic color rake",
        "distant headlights approach, character in shadow with rim light starting to define",
        "cool blue moonlight entering parking structure, slicing through pillar grid",
    ],
    "trap": [
        "cold blue moonlight from above through skylight, gold accent from below, luxury contrast",
        "luxury warm interior behind, city cold blue outside, character between two worlds",
        "single overhead spotlight in darkness, expensive subject perfectly lit",
        "champagne-warm table light with cool window glow, nightclub depth",
        "helicopter searchlight from above, character below in total command of frame",
    ],
    "rock": [
        "multiple colored PAR cans in red and amber, haze machine filling air, rock club atmosphere",
        "single hard white follow spot, everything else lost in dark, pure performance",
        "backlight from massive LED wall, character in dark silhouette against light explosion",
        "ground-level uplights throwing long shadows upward, arena scale",
        "storm lightning as strobe, violent intervals, metal sky energy",
    ],
    "metal": [
        "deep crimson light from beneath, demonic uplighting, no mercy",
        "cold lightning backlight with ember orange ground reflection, hellscape",
        "single torch light in absolute darkness, ancient intimate horror",
        "volcanic orange glow from below horizon, toxic sky above, apocalyptic",
        "moonlight on one half, total void on other, duality and power",
    ],
    "lofi": [
        "warm amber desk lamp as key light, cool blue of night through window as fill, perfect lofi balance",
        "string lights above creating starfield effect, main source is screen glow, soft and digital",
        "refrigerator light in darkness, blue-white cold at 3am, specific and real",
        "candle close to face, warm flickering, deep shadow behind, intimate",
        "rain-diffused streetlight through window, soft caustic on walls, gentle and contemplative",
    ],
    "indie": [
        "golden hour direct sun, warm rake across everything, long shadows, magic time",
        "overcast diffused light, soft and even, colors more saturated, melancholy beauty",
        "window light only, soft rectangles on floor, dust motes visible, interior warmth",
        "dusk last light, sky luminous behind, silhouette against color gradient",
        "neon from vintage sign as only light, color cast changes everything, moody atmosphere",
    ],
    "electronic": [
        "laser array from behind stage, beams cutting fog, techno cathedral feel",
        "full color LED wall backlight, character dark silhouette, thousands of pixels behind",
        "UV blacklight with reactive paint glowing, alien and electric",
        "strobe at low frequency, motion visible in still image, rave energy frozen",
        "holographic light sculpture surrounding figure, impossible colors, future venue",
    ],
    "dark": [
        "full moonlight from directly above, silver and cold, shadows dense and black",
        "multiple candles in circle, warm isolated island in darkness, ritual",
        "bioluminescent source from below, eerie blue-green, unnatural beauty",
        "single window moonlight cutting across dark room, chiaroscuro painting quality",
        "star-filled sky as only light, eyes adjusted, everything silver and navy",
    ],
    "default": [
        "cinematic neon purple and blue glow from environment, high contrast black shadows",
        "dramatic single spotlight from 45-degree angle above, all else dark",
        "golden backlight creating glow around figure, slightly overexposed beautiful haze",
        "cool blue ambient with single warm accent, split-tone professional look",
        "city light scatter as ambient, deep shadows, lived-in atmospheric",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# DETALHES DE OUTFIT POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_OUTFITS = {
    "phonk": [
        "oversized dark hoodie unzipped, black compression underneath, tactical cargo pants, chunky boots",
        "cropped leather jacket with patches, baggy dark jeans, platform sneakers, chain details",
        "black techwear with reflective strips, hood up, utility belt, modified streetwear",
        "vintage band tee knotted, high-waisted dark pants, beat-up leather jacket over shoulders",
        "all-black outfit: fitted turtleneck, flared pants, pointed boots, minimal jewelry",
    ],
    "trap": [
        "oversized designer tracksuit in monochrome, luxury logo visible, clean white trainers",
        "structured bralette with tailored wide-leg trousers, long coat, heels",
        "off-shoulder fitted dress, thigh-high boots, layered gold chains",
        "premium streetwear: logo hoodie, biker shorts, high-end crossbody, statement sunglasses",
        "sheer top with structured blazer, fitted pants, pointed heels, diamond jewelry",
    ],
    "rock": [
        "ripped fishnet under oversized band tee, leather jacket, boots with silver hardware",
        "black skinny jeans, mesh top, studded belt, leather jacket covered in pins",
        "sleeveless band shirt tied at waist, high-waisted shorts, combat boots, wristbands",
        "vintage band tee tucked in, high-waisted flared jeans, platform boots, silver rings",
        "black stage outfit: pants and crop, leather jacket open, wristbands, playing guitar",
    ],
    "metal": [
        "black gothic armor-influenced outfit, pauldron detail, dark corset elements, boots",
        "long black dress with dramatic sleeves, dark metal jewelry, ritual details",
        "black fitted bodice with flowing dark skirt, corseted, dark cloak behind",
        "all-black: tactical elements mixed with gothic couture, chains and buckles",
        "dark warrior outfit: fitted black leather, gauntlets, boots to knee, commanding",
    ],
    "lofi": [
        "oversized soft-washed hoodie, pajama pants, mismatched socks, reading glasses pushed up",
        "vintage band tee as dress, oversized cardigan, knee socks, hair clip",
        "big cozy knit sweater, leggings, slippers, messy bun, comfort as aesthetic",
        "soft flannel shirt open over crop, loose jeans, sock feet, natural and warm",
        "university crewneck, loose worn sweatpants, hair ties on wrist, authentic comfort",
    ],
    "indie": [
        "vintage slip dress over worn white tee, chunky cardigan, platform Mary Janes",
        "wide-leg vintage trousers, cropped knit, classic white tee under, woven bag",
        "sundress with worn denim jacket, white sneakers, minimal jewelry, effortless",
        "layered vintage finds: oversized blazer, midi skirt, boots, gold earrings",
        "linen wide pants, simple fitted tee, structured crossbody, comfortable artist",
    ],
    "electronic": [
        "holographic crop top, high-waisted shorts, platform boots with LED accents",
        "reflective bodysuit, structured jacket with panels, clear heeled boots",
        "color-blocked technical outfit, mesh details, futuristic accessories",
        "neon accents on dark outfit, cyber details, boots, festival-ready layers",
        "metallic mini dress, thigh boots, angular accessories, future festival fashion",
    ],
    "dark": [
        "long dark velvet dress, dramatic sleeves, subtle gold or silver jewelry only",
        "black corset with layered dark skirt, dramatic cloak over shoulders",
        "fitted black outfit with subtle gothic details, sheer panels, dark jewelry",
        "dark dramatic gown with trail, simple and overwhelming in its severity",
        "black layered outfit: tight and loose mixed, architectural silhouette",
    ],
    "default": [
        "elevated streetwear with editorial touches, monochrome with accent piece",
        "sophisticated casual: quality basics with one statement piece",
        "dark fitted outfit with interesting texture, minimal but intentional",
        "classic dark ensemble, clean lines, confident simplicity",
        "modern aesthetic: structured pieces, dark palette, precise fit",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# QUALIDADE E NEGATIVO
# ══════════════════════════════════════════════════════════════════════

QUALITY_SUFFIX = (
    "masterpiece, best quality, premium anime illustration, "
    "highly detailed character, sharp clean line art, smooth cel shading, "
    "vibrant saturated colors, professional anime key visual, "
    "trending on pixiv, artstation quality anime, studio-level artwork, "
    "full body shot mandatory, wide framing, camera distance maintained, "
    "character head to toe visible, no cropping at any edge, "
    "9:16 vertical format, centered composition, strong character silhouette, "
    "cinematic depth of field on background, no text, no watermarks, single character"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, CGI, 3D render, real human face, "
    "text, watermark, signature, logo, border, frame, vignette overlay, "
    "multiple characters, second person, crowd in foreground, extra limbs, "
    "deformed hands, fused fingers, extra fingers, bad anatomy, distorted face, "
    "crossed eyes, wrong proportions, malformed ears, asymmetric pupils, "
    "blurry background bleeding into character, muddy colors, flat lighting, "
    "cropped head, cropped legs, missing feet, face-only crop, portrait-only, "
    "zoomed in face, close-up portrait, waist-up crop, cut at mid-body, "
    "child appearance, young teen face, baby face, childlike proportions, "
    "explicit nudity, revealing underwear, fetish content, inappropriate clothing, "
    "duplicate figure, mirror ghost, watercolor wash, low contrast, washed out, "
    "generic background, plain gradient, studio void, boring composition, "
    "airbrushed look, plastic skin, doll face, uncanny valley, "
    "Western cartoon style, Pixar style, chibi, super deformed, "
    "sepia tone, old photo filter, sketch only, line art only unfinished"
)


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE SELEÇÃO DETERMINÍSTICA
# ══════════════════════════════════════════════════════════════════════

def _seed_from(filename: str, short_num: int) -> int:
    key = f"{filename}_{short_num}_v3"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _seeded_choice(pool: list, seed: int, offset: int = 0):
    rng = random.Random(seed + offset * 97)
    return rng.choice(pool)


def _pick_character(style: str, filename: str, short_num: int) -> dict:
    seed = _seed_from(filename, short_num)
    # Preferir personagens com afinidade pelo estilo, mas sempre ter diversidade
    preferred = [c for c in CHARACTER_POOL if style in c.get("style_affinity", [])]
    pool = preferred if preferred and len(preferred) >= 3 else CHARACTER_POOL
    rng = random.Random(seed)
    return rng.choice(pool)


def _pick_expression(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_EXPRESSIONS.get(style, GENRE_EXPRESSIONS["default"])
    return _seeded_choice(pool, seed, 1)


def _pick_pose(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_POSES.get(style, GENRE_POSES["default"])
    return _seeded_choice(pool, seed, 2)


def _pick_environment(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_ENVIRONMENTS.get(style, GENRE_ENVIRONMENTS["default"])
    return _seeded_choice(pool, seed, 3)


def _pick_lighting(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_LIGHTING.get(style, GENRE_LIGHTING["default"])
    return _seeded_choice(pool, seed, 4)


def _pick_outfit(style: str, filename: str, short_num: int) -> str:
    seed = _seed_from(filename, short_num)
    pool = GENRE_OUTFITS.get(style, GENRE_OUTFITS["default"])
    return _seeded_choice(pool, seed, 5)


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled Track"


def _compact_prompt(text: str, max_chars: int = 1200) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# CONSTRUÇÃO DO PROMPT
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)
    character = _pick_character(style, filename, short_num)
    expression = _pick_expression(style, filename, short_num)
    pose = _pick_pose(style, filename, short_num)
    environment = _pick_environment(style, filename, short_num)
    lighting = _pick_lighting(style, filename, short_num)
    outfit = _pick_outfit(style, filename, short_num)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                character=character,
                expression=expression,
                pose=pose,
                environment=environment,
                lighting=lighting,
                outfit=outfit,
            )
        except Exception as e:
            print(f"  [Claude] Falha no prompt: {e} — usando fallback estatico")

    return _static_prompt(
        style=style,
        character=character,
        expression=expression,
        pose=pose,
        environment=environment,
        lighting=lighting,
        outfit=outfit,
    )


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    character: dict,
    expression: str,
    pose: str,
    environment: str,
    lighting: str,
    outfit: str,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are the lead art director for a premium anime music video channel with 5 million subscribers. "
        "Your thumbnails stop thumbs and pull viewers in. You write Flux image prompts that produce "
        "scroll-stopping, cinematic anime art. "
        "Rules: exactly ONE adult anime woman, FULL BODY always visible head to toe, "
        "9:16 vertical, never portrait crop or face crop, never sexual content, "
        "platform-safe, premium anime illustration quality. "
        "Output ONLY the prompt: comma-separated descriptors, 80-120 words, no explanations, no quotes."
    )

    user = f"""Create a premium full-body anime cover art prompt.

SONG: "{song_name}"
PRIMARY GENRE: {style}
ALL GENRES: {all_styles}

CHARACTER (use all details):
- Hair: {character['hair']}
- Skin: {character['skin']}
- Eyes: {character['eyes']}
- Face: {character['face']}
- Body type: {character['body']}
- Core vibe: {character['vibe']}

SCENE ELEMENTS:
- Expression: {expression}
- Outfit: {outfit}
- Pose: {pose}
- Setting: {environment}
- Lighting: {lighting}

CRITICAL REQUIREMENTS:
1. Full body must be visible head to toe
2. 9:16 vertical composition, character centered
3. Anime illustration style, NOT realistic
4. Background complements the scene depth
5. Cinematic quality, strong silhouette
6. 80-120 words total"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_SUFFIX}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) para short #{short_num}")
    return _compact_prompt(full)


def _static_prompt(
    style: str,
    character: dict,
    expression: str,
    pose: str,
    environment: str,
    lighting: str,
    outfit: str,
) -> str:
    prompt = (
        f"masterpiece, best quality, premium anime illustration, highly detailed, "
        f"one adult anime woman, full body visible head to toe, "
        f"{character['hair']}, {character['eyes']}, {character['face']}, "
        f"{character['body']}, {character['vibe']}, "
        f"{expression}, "
        f"{outfit}, "
        f"{pose}, "
        f"{environment}, "
        f"{lighting}, "
        f"9:16 vertical composition, character centered, wide framing, "
        f"anime key visual, sharp clean lineart, smooth shading, vibrant colors, "
        f"cinematic depth, strong silhouette, no text, single character, "
        f"NOT realistic, NOT photography, NOT 3d render"
    )
    return _compact_prompt(prompt)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM VIA REPLICATE
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 30,
        "aspect_ratio": "9:16",
        "guidance": 3.8,
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
        + ", anime illustration style, full body character visible, "
          "9:16 vertical, sharp lineart, vibrant colors, no realism"
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
                    print(f"  [Replicate] URL nao encontrada na resposta")
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
