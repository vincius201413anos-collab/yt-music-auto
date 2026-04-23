"""
ai_image_generator.py — v6.0 IDENTITY EDITION
===============================================
MUDANÇAS v6.0:
- Personagem recorrente com DNA visual fixo: cabelo preto, olhos vermelhos sangue,
  expressão fria e calculada — reconhecível em qualquer short
- Prompts com referência artística ESPECÍFICA: mangá, cel-shading, painterly dark anime
- 4 ESTILOS ARTÍSTICOS rotativos para fugir do look AI genérico
- Cenários ultra-específicos por gênero (não só "cyberpunk city")
- Negativo altamente refinado para eliminar o look "AI slop"
- Sistema de micro-detalhes: cada prompt tem 1 detalhe único que ancora a cena
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
# DNA DA PERSONAGEM — IDENTIDADE FIXA DO CANAL
#
# Essa personagem aparece em TODOS os shorts de tipo "character" e "cinematic".
# Ela é a mascote não-oficial do DJ darkMark.
# Traços imutáveis:
#   - cabelo preto liso longo com franja cortada reta
#   - olhos vermelhos sangue grandes, íris com brilho interno
#   - expressão neutra-fria, nunca sorrindo, nunca com medo
#   - pele pálida quase cinza, sem blush
#   - roupa escura com detalhes técnicos/táticos
#   - sempre sozinha em cena — nunca grupo
# ══════════════════════════════════════════════════════════════════════

CHARACTER_DNA = (
    "one anime woman, straight black hair with blunt cut bangs, "
    "large blood-red eyes with internal crimson glow, "
    "pale gray-white skin, no blush, cold neutral expression, "
    "dark tactical outfit with subtle neon accent seams, "
    "alone in frame, no other characters"
)

# 4 estilos artísticos que rotacionam para evitar homogeneidade visual
ART_STYLES = [
    # Estilo A — Mangá high-contrast (como a imagem manga monocromática que você enviou)
    (
        "manga-inspired dark illustration, heavy ink linework, "
        "high contrast black and white base with selective blood-red color accent only on eyes and neon elements, "
        "cross-hatching in shadow areas, sharp clean edges, "
        "inspired by Junji Ito composition meets cyberpunk aesthetics"
    ),
    # Estilo B — Cel-shading premium (como a violet demon que você enviou)
    (
        "premium cel-shaded anime illustration, clean flat color fills, "
        "sharp shadow boundaries no gradients, "
        "vivid saturated neon against deep flat black, "
        "professional anime key visual quality, "
        "similar to Studio Trigger dark aesthetic"
    ),
    # Estilo C — Painterly dark (como a pink chain girl)
    (
        "dark painterly anime illustration, loose confident brushstrokes, "
        "atmospheric color bleeds at edges, "
        "dramatic chiaroscuro lighting, "
        "oil painting texture meets digital anime, "
        "Yoji Shinkawa meets dark cyberpunk"
    ),
    # Estilo D — Glitch/digital (original, sem referência direta)
    (
        "dark digital anime illustration with chromatic aberration effects, "
        "RGB color split at edges of subject, "
        "scanline texture overlay, "
        "corrupted pixel details in shadows, "
        "feels like a corrupted file that became art"
    ),
]


# ══════════════════════════════════════════════════════════════════════
# CONCEITOS VISUAIS v6 — ULTRA-ESPECÍFICOS POR GÊNERO
#
# Cada conceito tem:
#   - scene: descrição ultra-específica com 1 micro-detalhe único
#   - palette: instrução de cor precisa
#   - anchor: o ÚNICO elemento que define essa cena (impede o prompt de ser genérico)
# ══════════════════════════════════════════════════════════════════════

VISUAL_CONCEPTS = {

    # ── PHONK ─────────────────────────────────────────────────────────
    "phonk": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "PHONK_CHARACTER",
            "anchor": "cassette tape unraveling in wind",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing in abandoned underground parking lot at 3am, "
                "single flickering fluorescent tube above casting hard downward shadows, "
                "cassette tape ribbon unraveling in wind around her feet catching neon red light, "
                "wet oil-stained concrete floor reflecting crimson, "
                "close shot framing chest to crown, slight upward angle"
            ),
            "palette": "blood red single light source, absolute black fill, wet concrete gray, zero warmth",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "PHONK_SCENE",
            "anchor": "single payphone glowing red in empty lot",
            "scene": (
                "empty midnight parking lot, no character, "
                "single payphone with handset dangling, internal red glow, "
                "fog at ankle level pooling around painted lines on asphalt, "
                "overhead sodium lamp creating one cone of orange-red light, "
                "chain-link fence at background with torn phonk flyers, "
                "wide establishing shot"
            ),
            "palette": "desaturated asphalt gray with single blood-red glow source, orange-red sodium cast, maximum darkness",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "PHONK_CINEMATIC",
            "anchor": "she walks INTO the tunnel not away from it",
            "scene": (
                f"{CHARACTER_DNA}, "
                "extreme low angle, she walks directly toward camera into massive underground tunnel, "
                "enormous blood-red neon circle at far vanishing point behind her, "
                "tunnel ceiling dripping water catching neon light, "
                "her shadow stretches toward viewer, she does not look at camera, "
                "cinematic 2.39:1 crop feel in 9:16 format"
            ),
            "palette": "absolute black with single red vanishing point, tunnel gray concrete, zero other colors",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "PHONK_ABSTRACT",
            "anchor": "vinyl record cracking under bass pressure",
            "scene": (
                "vinyl record at center cracking outward under bass pressure, "
                "crimson shockwave rings expanding from crack lines, "
                "cassette magnetic tape spiraling outward catching neon violet light, "
                "concrete floor fragmenting at edges, "
                "no character, pure sound-as-destruction concept"
            ),
            "palette": "blood red shockwave against absolute black, violet magnetic tape, concrete gray at edges",
        },
    ],

    # ── TRAP ──────────────────────────────────────────────────────────
    "trap": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "TRAP_CHARACTER",
            "anchor": "rain on floor-to-ceiling glass reflects entire city grid",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing at floor-to-ceiling penthouse window, arms at sides, "
                "entire neon city grid visible below through rain-streaked glass, "
                "rain droplets on glass each refracting violet city lights, "
                "her reflection ghosted in glass overlaying the city, "
                "medium shot, she looks at the city not at viewer"
            ),
            "palette": "electric violet city below, cold blue-black room behind, premium dark luxury palette",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "TRAP_SCENE",
            "anchor": "rooftop helipad H marking glowing violet in rain",
            "scene": (
                "luxury building rooftop at night, no character, "
                "helipad H marking glowing violet in rain puddle, "
                "entire neon city visible beyond glass railing, "
                "storm clouds lit from below by city light, "
                "two champagne glasses abandoned on ledge, rain filling them slowly"
            ),
            "palette": "electric violet dominant, deep navy storm sky, warm amber city far distance, wet black foreground",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "TRAP_CINEMATIC",
            "anchor": "shot from rooftop edge looking down at her looking up",
            "scene": (
                f"{CHARACTER_DNA}, "
                "extreme overhead shot looking straight down, "
                "she stands alone on rooftop looking straight up at camera, "
                "entire city grid spreads concentrically around her from above, "
                "she is the still center of the moving city, "
                "rain visible as streaks in the downward shot"
            ),
            "palette": "violet city grid radiating outward, deep black between buildings, her as pale still point",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "TRAP_ABSTRACT",
            "anchor": "808 sine wave as neon architecture",
            "scene": (
                "808 bass waveform rendered as violet neon architecture floating in void, "
                "sine wave physically bending space around it, "
                "gold chain links dissolving into frequency particles at edges, "
                "sub-bass pressure visible as concentric compression rings, "
                "no character, pure frequency as luxury object"
            ),
            "palette": "electric violet architecture, gold dissolving to particles, absolute black void",
        },
    ],

    # ── ELECTRONIC / DUBSTEP ──────────────────────────────────────────
    "electronic": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "ELECTRONIC_CHARACTER",
            "anchor": "single red laser cuts across her face at eye level",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing in heavy rain, "
                "single horizontal red laser beam cuts across frame at her eye level, "
                "beam diffracts in rain creating red mist halo, "
                "neon circuit-board pattern barely visible on wet street around her feet, "
                "medium close shot, she looks through the laser not at it"
            ),
            "palette": "blood red laser against absolute black, rain as silver texture, circuit green accent barely visible",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "ELECTRONIC_SCENE",
            "anchor": "empty rave stage before the crowd — lasers pre-programmed running for no one",
            "scene": (
                "underground rave venue completely empty before the crowd, no character, "
                "laser grid running pre-programmed for no audience, "
                "smoke machine running on timer, beams cutting through fog, "
                "massive subwoofer stacks glowing faint red, "
                "single technician's coffee cup abandoned on equipment, "
                "the ritual space before the ritual"
            ),
            "palette": "UV purple floor haze, blood red laser geometry, deep black negative space, green laser accent",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "ELECTRONIC_CINEMATIC",
            "anchor": "her silhouette IS the drop — the moment everything hits",
            "scene": (
                f"{CHARACTER_DNA}, "
                "rear silhouette view from stage level, "
                "she faces enormous crowd in darkness, "
                "massive LED wall behind her exploding with crimson and violet at the exact drop moment, "
                "crowd hands raised as single dark mass, "
                "her silhouette the only darkness in the light storm, "
                "wide shot, epic scale"
            ),
            "palette": "silhouette pure black, LED explosion crimson and violet, crowd dark gray, chromatic aberration at frame edges",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "ELECTRONIC_ABSTRACT",
            "anchor": "the drop as supernova expanding from exact center",
            "scene": (
                "bass drop visualized as supernova expanding from absolute center, "
                "crimson energy wave at inner ring, violet at outer expansion, "
                "frequency rings as physically real neon circles bending outward, "
                "the exact moment of impact frozen in time, "
                "no character, music as creation event, pure energy"
            ),
            "palette": "blood red core expanding to electric violet outer rings, absolute black background, white hot center point",
        },
    ],

    # ── DARK / ATMOSPHERIC ────────────────────────────────────────────
    "dark": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "DARK_CHARACTER",
            "anchor": "shattered mirror shards floating — each reflects a different version of her",
            "scene": (
                f"{CHARACTER_DNA}, "
                "surrounded by shattered mirror fragments floating in zero gravity, "
                "each mirror shard reflects a different angle of her face, "
                "slight knowing smile — the only time she smiles and it is not reassuring, "
                "dark void background, fragments catch crimson light from her eyes, "
                "close to medium shot, fragments at all depths"
            ),
            "palette": "near-monochrome void, mirror shards as silver geometry, blood red eye glow the only warm color",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "DARK_SCENE",
            "anchor": "abandoned arcade machine still running its attract loop",
            "scene": (
                "abandoned cyberpunk district at night, no character, "
                "crumbling building facade with one arcade machine in alcove still running attract mode, "
                "flickering pixel game casting color on wet street, "
                "dark vines growing through cracked neon sign frame, "
                "fog at ground level, beautiful decay, "
                "the technology outlasted its purpose"
            ),
            "palette": "cold darkness, pixel arcade warm orange-red glow as only light, violet neon remnants flickering, rain texture",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "DARK_CINEMATIC",
            "anchor": "she carries the only light and doesn't look back",
            "scene": (
                f"{CHARACTER_DNA}, "
                "extreme wide shot from behind, tiny figure in vast flooded underground space, "
                "she holds a single red emergency flare, "
                "circle of crimson light surrounds her, absolute darkness beyond, "
                "water at ankle level reflecting the flare, "
                "she walks away from viewer, never looking back, "
                "scale: she is 10% of the frame height"
            ),
            "palette": "single crimson circle against absolute black, water as dark mirror, no other light sources",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "DARK_ABSTRACT",
            "anchor": "heartbeat flatline that suddenly isn't flat",
            "scene": (
                "EKG heartbeat line across dark screen, "
                "flatline that suddenly erupts into violent crimson pulse, "
                "dark melody made visible as black ink bleeding through neon-lit water, "
                "pulse rings expanding from heartbeat spike like sonar, "
                "the moment between silence and sound, darkness with a pulse"
            ),
            "palette": "black and deep crimson dominant, violet at outer pulse rings, near-medical green accent on flatline only",
        },
    ],

    # ── LOFI / CHILL ──────────────────────────────────────────────────
    "lofi": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "LOFI_CHARACTER",
            "anchor": "she reads by the light of her own eyes",
            "scene": (
                f"{CHARACTER_DNA}, "
                "seated on windowsill in abandoned library at 3am, "
                "reading a book illuminated only by her own crimson eye glow, "
                "rain on the window beside her, city fog outside, "
                "stacked books around her, one candle burned to stub, "
                "medium shot, peaceful despite the darkness"
            ),
            "palette": "warm candlelight amber fading to cold darkness, crimson eye glow as reading light, rain-gray window",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "LOFI_SCENE",
            "anchor": "coffee shop closed, one lamp still on, rain on glass",
            "scene": (
                "small city coffee shop after closing, no character, "
                "one pendant lamp still illuminated over empty counter, "
                "rain streaming down floor-to-ceiling glass front, "
                "steam rising from forgotten cup on counter, "
                "neon OPEN sign turned to CLOSED but still half-lit, "
                "3am, the city passes unaware outside"
            ),
            "palette": "warm amber single light, cold blue-black outside, neon red-pink sign half-dark, rain silver texture",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "LOFI_CINEMATIC",
            "anchor": "the last train she didn't take",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing on empty subway platform watching train depart, "
                "train lights streak into tunnel darkness, "
                "she deliberately didn't board, holds headphones wire, "
                "platform wet from rain through ceiling grate above, "
                "wide shot from end of platform, she small against departure"
            ),
            "palette": "train warm yellow streak, platform dark teal, crimson eye glow, departure as motion blur",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "LOFI_ABSTRACT",
            "anchor": "vinyl scratch frozen mid-rotation",
            "scene": (
                "vinyl record frozen mid-rotation, stylus visible mid-groove, "
                "sound waves coming off grooves as visible warmth distortion, "
                "dust particles suspended in beam of amber lamplight, "
                "the groove itself glowing faintly as it plays, "
                "peaceful and precise, music as physical ritual"
            ),
            "palette": "warm amber lamplight, deep black record surface, dust as gold particles, groove as crimson hairline glow",
        },
    ],

    # ── METAL / ROCK ──────────────────────────────────────────────────
    "metal": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "METAL_CHARACTER",
            "anchor": "her hands are the only thing in focus — everything else motion blur",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing in ruined cathedral at night, "
                "stained glass windows shattered, neon violet bleeding through frame, "
                "her hands pressed against cracked stone wall, "
                "everything in motion blur except her hands and face, "
                "as if she is the still point in destruction, "
                "medium close shot with dramatic upward angle"
            ),
            "palette": "violet stained glass remnants, absolute black ruin, blood red eye glow, stone gray textures",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "METAL_SCENE",
            "anchor": "burning guitar standing alone in empty field",
            "scene": (
                "open field at night, no character, "
                "electric guitar standing upright in field, on fire, "
                "fire the only light source, amber and crimson, "
                "smoke rising, sparks floating up into absolute darkness, "
                "charred ground around guitar base, "
                "epic and isolated, beautiful destruction"
            ),
            "palette": "amber and crimson fire against absolute black sky, smoke as dark texture, charred ground",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "METAL_CINEMATIC",
            "anchor": "she's the last one standing",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing in center of destroyed concert venue, debris around her, "
                "ceiling partially collapsed, neon sign sparking above, "
                "she is completely still, everyone else gone, "
                "wide shot from above looking down into destruction, "
                "she is the eye of the storm"
            ),
            "palette": "destruction amber and gray, blood red eye glow from distance, sparking neon crimson, dust haze",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "METAL_ABSTRACT",
            "anchor": "guitar waveform as seismic event",
            "scene": (
                "guitar distortion waveform rendered as seismic graph, "
                "amplitude peaks tearing through dark ground like earthquake, "
                "riff made physical as crimson lightning crackling horizontal, "
                "the breakdown as geological event, cracks glowing violet, "
                "no character, pure sonic force made visible"
            ),
            "palette": "blood red waveform lightning, violet crack glow, absolute black field, seismic gray ground texture",
        },
    ],

    # ── INDIE ─────────────────────────────────────────────────────────
    "indie": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "INDIE_CHARACTER",
            "anchor": "polaroid photos pinned to wall behind her, all blank",
            "scene": (
                f"{CHARACTER_DNA}, "
                "in minimal apartment at 3am, "
                "wall behind her covered in pinned polaroid photos, all completely blank white, "
                "she stares at them, "
                "single desk lamp casting warm amber cone in cold dark room, "
                "medium shot, melancholic and still"
            ),
            "palette": "warm amber single lamp, cold blue-black room, blank white polaroid squares as geometric accent",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "INDIE_SCENE",
            "anchor": "cassette player on roof edge, playing to no one, city below",
            "scene": (
                "rooftop edge at night, no character, "
                "portable cassette player at roof edge playing to the entire empty city below, "
                "cassette wheels visible turning, "
                "city spread below receiving the music it doesn't know it's getting, "
                "wind barely visible in ambient light, "
                "intimate gesture in vast scale"
            ),
            "palette": "warm cassette player amber, cold vast city below in blue and violet, intimate vs scale contrast",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "INDIE_CINEMATIC",
            "anchor": "train window, city passing, her reflection overlays the world",
            "scene": (
                f"{CHARACTER_DNA}, "
                "seated at night train window, city lights passing outside, "
                "her reflection in dark glass perfectly overlays the moving city, "
                "she and the city exist in same plane in the reflection, "
                "medium shot through the glass, double exposure effect naturally achieved, "
                "headphone wire visible"
            ),
            "palette": "city lights warm amber and violet passing, glass as dark blue mirror, double exposure layered",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "INDIE_ABSTRACT",
            "anchor": "song visualized as constellations rearranging",
            "scene": (
                "star field rearranging itself into musical notation, "
                "constellations that form and dissolve as melody progresses, "
                "note shapes drawn in starlight, "
                "some stars brighter, some fading mid-phrase, "
                "the music as temporary order imposed on infinite space"
            ),
            "palette": "deep space black, white and warm amber stars, violet nebula soft glow at distance",
        },
    ],

    # ── CINEMATIC / EPIC ──────────────────────────────────────────────
    "cinematic": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "CINEMATIC_CHARACTER",
            "anchor": "she is the conductor — city lights respond to her raised hand",
            "scene": (
                f"{CHARACTER_DNA}, "
                "on cliff edge overlooking vast dark city, "
                "one hand raised as if conducting, "
                "city lights below pulse in response to her gesture, "
                "wind moving her hair, "
                "extreme wide shot from side, she 20% of frame, city 80%, "
                "epic scale composition"
            ),
            "palette": "city lights warm amber below, cold violet storm sky, her as dark silhouette with crimson eye glow visible at distance",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "CINEMATIC_SCENE",
            "anchor": "ancient stone gate with modern neon frame installed in it",
            "scene": (
                "massive ancient stone gate in darkness, no character, "
                "modern neon frame installed in ancient opening, glowing blood red, "
                "the contrast: thousand-year stone and yesterday's neon, "
                "fog at base, stars visible through gate opening, "
                "wide establishing shot, monumental scale"
            ),
            "palette": "ancient stone cold gray, blood red neon frame, star field cold blue through opening, fog silver-gray base",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "CINEMATIC_CINEMATIC",
            "anchor": "the moment before the storm reaches the city",
            "scene": (
                f"{CHARACTER_DNA}, "
                "on building rooftop, massive storm wall approaching city from distance, "
                "lightning illuminating storm interior in violet and white, "
                "she faces the storm directly, arms at sides, "
                "city behind her unaware, "
                "wide shot: storm approaching from one side, city behind, her as pivot point"
            ),
            "palette": "violet and white storm lightning, city warm amber behind, absolute black storm wall, her as still dark figure",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "CINEMATIC_ABSTRACT",
            "anchor": "orchestral swell visualized as visible sound pressure bending light",
            "scene": (
                "orchestral swell rendered as physical sound pressure, "
                "visible waves bending light itself around their passage, "
                "neon lines curving as pressure wave passes through, "
                "the crescendo as physical reality distortion, "
                "lensing effect at peak amplitude, "
                "music as gravitational force"
            ),
            "palette": "blood red pressure wave, electric violet light bending, absolute black field, white at highest amplitude",
        },
    ],

    # ── DEFAULT ───────────────────────────────────────────────────────
    "default": [
        # A — CHARACTER
        {
            "type": "character",
            "label": "DEFAULT_CHARACTER",
            "anchor": "rain only falls in her light — everywhere else dry",
            "scene": (
                f"{CHARACTER_DNA}, "
                "standing in dark alley, "
                "rain falls only in the cone of light above her — darkness around her is dry, "
                "this is physically wrong and that is the point, "
                "neon signs in red and violet reflected in puddles around her feet, "
                "medium close shot, mysterious and precise"
            ),
            "palette": "blood red and violet neon, absolute black dry darkness, silver rain column over her only",
        },
        # B — SCENE
        {
            "type": "scene",
            "label": "DEFAULT_SCENE",
            "anchor": "entire city seen through shattered windshield of abandoned car",
            "scene": (
                "interior of abandoned car, no character, "
                "shattered windshield frames entire city skyline in fractured pieces, "
                "each shard reflects different part of neon city differently, "
                "dashboard overgrown with small plants, "
                "radio static visible on cracked display, "
                "the city as mosaic through the broken frame"
            ),
            "palette": "deep midnight city blue, neon red and violet through glass shards, plant green small accent, dashboard amber glow",
        },
        # C — CINEMATIC
        {
            "type": "cinematic",
            "label": "DEFAULT_CINEMATIC",
            "anchor": "the city reflected in a single raindrop on her face",
            "scene": (
                f"{CHARACTER_DNA}, "
                "extreme close shot, single raindrop on her cheekbone, "
                "entire city skyline reflected in miniature in the raindrop, "
                "her crimson eye visible in extreme shallow depth of field beyond the drop, "
                "background bokeh of city lights in red and violet, "
                "the infinite in the microscopic"
            ),
            "palette": "blood red eye in shallow focus, city violet and amber in raindrop reflection, skin pale gray-white, bokeh red-violet",
        },
        # D — ABSTRACT
        {
            "type": "abstract",
            "label": "DEFAULT_ABSTRACT",
            "anchor": "sound as architecture — the song is a building",
            "scene": (
                "musical waveform rendered as physical architecture, "
                "bass frequencies as foundation columns, "
                "melody as glass spire reaching dark sky, "
                "rhythm as repeating archways, "
                "the entire song as a building you could walk into, "
                "no character, music as inhabitable space"
            ),
            "palette": "blood red structural elements, electric violet glass, absolute black sky, warm amber interior glow from windows",
        },
    ],
}

# Mapear gêneros para os conceitos existentes
GENRE_MAP = {
    "lofi":      "lofi",
    "indie":     "indie",
    "rock":      "metal",
    "metal":     "metal",
    "cinematic": "cinematic",
    "funk":      "trap",
    "pop":       "default",
    "trap":      "trap",
    "phonk":     "phonk",
    "electronic": "electronic",
    "dark":      "dark",
}


# ══════════════════════════════════════════════════════════════════════
# QUALIDADE — refinado para combater o look AI genérico
# ══════════════════════════════════════════════════════════════════════

QUALITY_TAGS = (
    "masterpiece, best quality, highly detailed dark anime illustration, "
    "professional anime key visual, intentional artistic style, "
    "not AI-generated looking, not generic, specific and distinctive, "
    "ultra-vivid saturated neon colors against absolute darkness, "
    "cinematic composition with strong focal point, "
    "richly detailed environment with atmospheric depth, "
    "dramatic chiaroscuro lighting, "
    "dark anime aesthetic, trending on pixiv dark, ArtStation quality, "
    "9:16 vertical format optimized, scroll-stopping visual impact"
)

NEGATIVE_PROMPT = (
    # Aparência física problemática
    "photorealistic, hyperrealistic, photography, 3D render, CGI, "
    "real human face, uncanny valley, airbrushed plastic skin, "
    # Problemas anatômicos
    "multiple characters, extra limbs, deformed hands, fused fingers, "
    "bad anatomy, distorted face, wrong proportions, malformed body parts, "
    # Conteúdo problemático
    "child appearance, young teen face, childlike proportions, "
    "explicit nudity, fetish content, nsfw, "
    # Visual genérico AI
    "generic purple gradient on white, generic anime waifu, "
    "predictable composition, boring background, gradient void background, "
    "seen before, forgettable, same as every AI image, "
    "overexposed, blown out highlights, "
    # Estética errada para o canal
    "bright daylight, cheerful, kawaii cute, pastel colors, "
    "warm cozy aesthetic, soft colors, fluffy, adorable, "
    "Western cartoon, Pixar style, chibi, super deformed, "
    # Qualidade baixa
    "blurry, muddy colors, flat boring lighting, "
    "sketch only, unfinished, low quality, draft, "
    # Cores erradas
    "green dominant, yellow dominant, orange dominant, warm sunset colors, "
    "brown dominant, pink pastel, baby blue"
)


# ══════════════════════════════════════════════════════════════════════
# SEED E SELEÇÃO
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v6_identity"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick_concept(style: str, filename: str, short_num: int) -> dict:
    """
    Rotação garantida:
    short_num 1 = CHARACTER, 2 = SCENE, 3 = CINEMATIC, 4 = ABSTRACT
    """
    mapped_style = GENRE_MAP.get(style, style)
    concepts = VISUAL_CONCEPTS.get(mapped_style, VISUAL_CONCEPTS["default"])
    concept_idx = (short_num - 1) % len(concepts)
    return concepts[concept_idx]


def _pick_art_style(filename: str, short_num: int) -> str:
    """
    Estilo artístico rota independentemente do conceito visual.
    Isso garante que mesmo o mesmo tipo de conceito não repita o mesmo look.
    """
    idx = _seed(filename, short_num) % len(ART_STYLES)
    return ART_STYLES[idx]


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
                filename=filename,
            )
        except Exception as e:
            print(f"  [Claude] Prompt falhou: {e} — usando fallback")

    return _static_prompt(concept, filename, short_num)


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    concept: dict,
    short_num: int,
    filename: str,
) -> str:
    client = get_anthropic_client()
    art_style = _pick_art_style(filename, short_num)
    concept_label = concept.get("label", concept["type"].upper())
    anchor = concept.get("anchor", "")

    type_rules = {
        "character": (
            "CHARACTER must have: straight black hair + blunt bangs, blood-red glowing eyes, "
            "pale gray skin, cold expression, dark tactical outfit. "
            "She is ALONE. Medium to close shot. She must feel SPECIFIC not generic."
        ),
        "scene": (
            "NO dominant character. The ANCHOR DETAIL is the subject. "
            "Every element serves the anchor. Empty spaces must feel inhabited by absence. "
            "The scene should feel like a story just happened or is about to happen."
        ),
        "cinematic": (
            "SCALE IS THE STATEMENT. If character present, she is small vs environment. "
            "One powerful composition. The relationship between subject and space is the meaning. "
            "Think movie poster frozen frame."
        ),
        "abstract": (
            "MUSIC AS PHYSICAL REALITY. No people. Sound made visible. "
            "The anchor detail is the visual metaphor for the track. "
            "Should feel like you can hear it just by looking."
        ),
    }

    system = (
        "You are an elite dark anime art director. You create SPECIFIC, DISTINCTIVE prompts "
        "that avoid generic AI aesthetics. Your character has fixed DNA that appears in every short.\n\n"
        "CHANNEL IDENTITY: DJ darkMark | dark cyberpunk anime visual identity\n"
        "CHARACTER DNA (NEVER deviate): straight black hair + blunt bangs, blood-red glowing eyes, "
        "pale gray skin, cold neutral expression, dark tactical outfit, always alone\n\n"
        "ABSOLUTE RULES:\n"
        "1. EVERY prompt must have ONE specific anchor detail that makes it unforgettable\n"
        "2. PALETTE: blood red + electric violet + absolute black. Nothing warm unless genre demands\n"
        "3. Specific > Generic always: 'cassette tape ribbon in wind' > 'dark atmosphere'\n"
        "4. Let the SONG TITLE influence one specific visual micro-detail\n"
        "5. The art style instruction MUST appear verbatim in the output\n"
        "6. 9:16 vertical format, platform-safe\n"
        "7. Output ONLY the prompt: comma-separated, 100-130 words, no preamble, no explanation"
    )

    user = f"""Create a SPECIFIC, DISTINCTIVE dark anime illustration prompt.

SONG: "{song_name}"
GENRE: {style} | ALL GENRES: {all_styles}
SHORT #: {short_num} | CONCEPT TYPE: {concept_label}

TYPE RULES:
{type_rules.get(concept["type"], "")}

SCENE FOUNDATION (use this as base, make it more specific):
{concept["scene"]}

ANCHOR DETAIL (this specific element must be in the prompt):
{anchor}

COLOR PALETTE (execute exactly):
{concept["palette"]}

ART STYLE (include this verbatim):
{art_style}

CRITICAL REQUIREMENTS:
- The song title "{song_name}" must influence one specific visual element
- Include the anchor detail: {anchor}
- Character (if present) must match DNA: black blunt bangs, blood-red glowing eyes, pale skin, cold expression
- 100-130 words, comma-separated, no preamble"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw  = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) — short #{short_num} [{concept_label}] anchor: {anchor}")
    return _compact(full)


def _static_prompt(concept: dict, filename: str, short_num: int) -> str:
    art_style = _pick_art_style(filename, short_num)
    anchor = concept.get("anchor", "")
    prompt = (
        f"masterpiece, best quality, ultra-detailed dark anime illustration, "
        f"{concept['scene']}, "
        f"anchor detail: {anchor}, "
        f"color palette: {concept['palette']}, "
        f"{art_style}, "
        f"blood red and electric violet neon against absolute black, "
        f"specific and distinctive composition, not generic AI image, "
        f"cinematic atmospheric depth, dark anime pixiv quality, "
        f"9:16 vertical composition, scroll-stopping visual impact"
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
        + ", dark anime illustration style, NOT photorealistic, NOT 3D render, NOT generic AI image, "
        + "specific distinctive composition, blood red and electric violet neon, absolute black shadows, "
        + "ultra-vivid saturated neon colors, deep rich blacks, luminous crimson and violet highlights, "
        + "intentional artistic style, not template-looking, "
        + "rain wet surfaces neon city where relevant, "
        + "premium dark anime key visual quality"
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
