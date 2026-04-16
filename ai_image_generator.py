"""
ai_image_generator.py — Gerador de imagens IA de alta qualidade.
Usa Claude Opus para criar prompts dinâmicos e vibrantes por música,
depois envia ao Replicate (Flux) para gerar imagens pro canal de música.
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
# CLAUDE OPUS — GERADOR DE PROMPTS DINÂMICOS
# ══════════════════════════════════════════════════════════════════════

# Guia visual por estilo — diz ao Opus o que queremos visualmente
STYLE_VISUAL_GUIDE = {
    "electronic": (
        "neon-lit futuristic cityscape, electric blue and purple glowing synths, "
        "abstract digital particles exploding outward, vibrant laser beams, "
        "holographic waveforms, ultra-vivid colors"
    ),
    "phonk": (
        "dark neon city at night, bright pink and red neon signs, "
        "dramatic orange light shafts, muscular car silhouette with glowing headlights, "
        "smoke and sparks, extreme contrast, vivid magenta and gold highlights"
    ),
    "trap": (
        "luxury urban night scene, gold chains and diamonds sparkling, "
        "city skyline with bright neon, vivid teal and gold palette, "
        "dramatic spotlight, high-fashion energy, crystal clear gems"
    ),
    "rock": (
        "electric guitar explosion with sparks and fire, dramatic stage lighting, "
        "vivid orange and electric blue flames, crowd silhouettes with raised fists, "
        "raw energy, lightning bolt effects, high-contrast dramatic shadows"
    ),
    "metal": (
        "dramatic dark fantasy landscape with bright electric lightning strikes, "
        "molten lava with vivid orange glow, epic storm clouds with backlit rays, "
        "intense contrast, skull motifs in glowing neon, raw powerful energy"
    ),
    "pop": (
        "bright pastel dreamscape with shimmering sparkles, soft neon gradients, "
        "floating musical notes and stars, candy-colored palette, "
        "dreamy bokeh lights, ultra-saturated pinks and purples, joyful energy"
    ),
    "indie": (
        "golden-hour sunset over rolling hills, warm amber and rose tones, "
        "film grain aesthetic, soft lens flare, dreamy haze, "
        "vintage warmth, rich teal shadows contrasting with gold highlights"
    ),
    "lofi": (
        "cozy rain-soaked window with warm yellow café glow beyond, "
        "soft amber lamplight, vintage film aesthetic, rich warm tones, "
        "peaceful urban nightscape, comfortable and nostalgic, gentle bokeh"
    ),
    "funk": (
        "vibrant 70s retro-futuristic disco explosion, bright warm oranges and yellows, "
        "dancing silhouettes with dramatic colorful spotlights, vivid rainbow prisms, "
        "mirror ball reflections, ultra-saturated warm palette, electric energy"
    ),
    "cinematic": (
        "epic widescreen landscape with dramatic god-rays breaking through storm clouds, "
        "ultra-rich teal and orange color grade, cinematic lens flare, "
        "breathtaking scale, volumetric fog with vivid backlit glow, "
        "blockbuster visual quality"
    ),
    "dark": (
        "mysterious dark forest with vibrant bioluminescent plants glowing electric blue, "
        "vivid purple and teal mist, dramatic moonlight shafts, "
        "glowing mystical runes, rich contrast between deep shadows and vivid light"
    ),
    "default": (
        "dramatic abstract music visualization with vivid neon colors exploding outward, "
        "electric blue, purple and gold light trails, dynamic energy waves, "
        "ultra high contrast, stunning visual impact"
    ),
}

# Termos proibidos que causam imagens escuras/genéricas
NEGATIVE_PROMPT = (
    "dark, muddy, low contrast, blurry, grainy, ugly, deformed, dull, "
    "desaturated, washed out, overexposed, text, watermark, signature, "
    "logo, border, frame, split image, collage, multiple images, "
    "distorted face, extra limbs, amateur, stock photo look, "
    "generic background, boring, flat lighting, underexposed"
)


def build_ai_prompt(style: str, filename: str, styles: list) -> str:
    """
    Usa Claude Opus para gerar um prompt específico e vibrante
    baseado no nome da música e estilo detectado.
    """
    # Limpa o nome da música para o prompt
    song_name = Path(filename).stem
    song_name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", song_name)
    song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()

    visual_ref = STYLE_VISUAL_GUIDE.get(style, STYLE_VISUAL_GUIDE["default"])
    all_styles  = ", ".join(s.title() for s in styles) if styles else style.title()

    # Tenta usar Claude Opus para prompt dinâmico
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _opus_prompt(song_name, style, all_styles, visual_ref, api_key)
        except Exception as e:
            print(f"  [Opus] Falha ao gerar prompt: {e} — usando fallback")

    # Fallback: prompt estático de alta qualidade
    return _static_prompt(song_name, style, visual_ref)


def _opus_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    visual_ref: str,
    api_key: str,
) -> str:
    """Gera prompt ultra-específico com Claude Opus."""
    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "You are a professional creative director for a music YouTube channel. "
        "Your specialty is creating Stable Diffusion / Flux image generation prompts "
        "that produce STUNNING, VIRAL-WORTHY visuals for music Shorts. "
        "Your prompts always produce images that are: vivid, eye-catching, "
        "high-contrast, professional, and feel like premium music artwork. "
        "NEVER produce dark, muddy or generic images. "
        "Output ONLY the image prompt — no explanation, no quotes, no commentary."
    )

    user = f"""Create a Flux image generation prompt for a YouTube Music Short.

Song name: "{song_name}"
Music style: {style}
All detected styles: {all_styles}

Visual reference for this style: {visual_ref}

Requirements:
• ULTRA-VIBRANT, high-contrast, eye-catching — must stop the scroll
• Must feel like a professional music channel visual (NOT stock photo)
• Specific subjects: use the song name for creative inspiration
• Include: dramatic lighting, vivid colors, dynamic energy
• Vertical format (9:16) — subject centered and bold
• Quality tags: "8K, ultra-detailed, professional photography, award-winning, 
  cinematic lighting, Hasselblad quality, sharp focus, stunning"
• Length: 80-120 words max
• Style: descriptive, comma-separated visual elements

Start the prompt directly — no preamble."""

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=250,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    prompt = resp.content[0].text.strip().strip('"').strip("'")
    print(f"  [Opus] Prompt gerado: {prompt[:100]}…")
    return prompt


def _static_prompt(song_name: str, style: str, visual_ref: str) -> str:
    """Prompt de alta qualidade sem API."""
    templates = [
        (
            f"Epic music artwork for '{song_name}', {visual_ref}, "
            f"ultra-vibrant colors, dramatic cinematic lighting, "
            f"8K ultra-detailed, professional music photography, "
            f"sharp focus, award-winning composition, stunning visual impact"
        ),
        (
            f"Professional music channel visual for {style} track '{song_name}', "
            f"{visual_ref}, vivid saturated palette, dynamic energy, "
            f"cinematic quality, Hasselblad photography, masterpiece"
        ),
        (
            f"Viral YouTube Shorts background, {style} music aesthetic, "
            f"{visual_ref}, ultra high contrast, neon-vivid colors, "
            f"professional lighting, stunning depth, 8K resolution"
        ),
    ]
    return random.choice(templates)


# ══════════════════════════════════════════════════════════════════════
# REPLICATE — GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

# Modelos disponíveis por prioridade (schnell = rápido, dev = qualidade)
REPLICATE_MODELS = [
    "black-forest-labs/flux-schnell",   # rápido, bom — principal
    "black-forest-labs/flux-dev",       # melhor qualidade — fallback lento
]

# Parâmetros otimizados para cada modelo
MODEL_PARAMS = {
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 95,
        "go_fast": True,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 28,
        "aspect_ratio": "9:16",
        "guidance": 3.5,
        "output_format": "png",
        "output_quality": 95,
        "disable_safety_checker": True,
    },
}

SAVE_DIR  = Path("temp")
MAX_TRIES = 3


def generate_image(prompt: str, output_path: str = None) -> str | None:
    """
    Gera imagem via Replicate.
    Retorna o caminho do arquivo salvo ou None em caso de falha.
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] REPLICATE_API_TOKEN não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Adiciona sufixo de qualidade ao prompt
    full_prompt = (
        prompt + ", 8K, ultra-detailed, sharp focus, vivid colors, "
        "professional photography, masterpiece, best quality"
    )

    for model in REPLICATE_MODELS:
        params = {**MODEL_PARAMS.get(model, {}), "prompt": full_prompt}

        # Adiciona negative prompt se o modelo suportar
        if "flux-dev" in model:
            params["negative_prompt"] = NEGATIVE_PROMPT

        for attempt in range(1, MAX_TRIES + 1):
            try:
                print(f"  [Replicate] Tentativa {attempt} — {model.split('/')[-1]}")
                output = replicate.run(model, input=params)

                # output pode ser list, iterator ou URL direta
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
    """Extrai URL de saída do Replicate independente do formato."""
    if isinstance(output, str) and output.startswith("http"):
        return output
    if isinstance(output, list) and output:
        first = output[0]
        # FileOutput do Replicate — tem atributo url
        if hasattr(first, "url"):
            return str(first.url)
        if isinstance(first, str) and first.startswith("http"):
            return first
    # Iterator / generator
    try:
        for item in output:
            if hasattr(item, "url"):
                return str(item.url)
            if isinstance(item, str) and item.startswith("http"):
                return item
    except Exception:
        pass
    return None


def _download_image(url: str, output_path: str = None) -> str | None:
    """Faz download da imagem gerada."""
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        if not output_path:
            ts   = int(time.time())
            output_path = str(SAVE_DIR / f"ai_bg_{ts}.png")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        # Verifica se a imagem tem tamanho válido (> 50KB)
        size = os.path.getsize(output_path)
        if size < 50_000:
            print(f"  [Replicate] Imagem suspeita: {size} bytes — descartando.")
            os.remove(output_path)
            return None

        return output_path

    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
