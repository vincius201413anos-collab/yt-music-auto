import random

def build_ai_prompt(style, filename, variant_index=1):
    base_title = Path(filename).stem.replace("_", " ")

    # 🎥 variações de câmera (evita repetição)
    camera_angles = [
        "low angle cinematic shot",
        "close-up dramatic framing",
        "wide cinematic composition",
        "off-center artistic framing",
        "top view perspective"
    ]

    lighting_styles = [
        "harsh red lighting",
        "neon glow lighting",
        "soft cinematic shadows",
        "high contrast dramatic light",
        "dark ambient lighting"
    ]

    textures = [
        "smoke and fog everywhere",
        "rain particles and wet reflections",
        "fire sparks and ash in the air",
        "dust and cinematic grain",
        "glitch distortion atmosphere"
    ]

    angle = camera_angles[variant_index % len(camera_angles)]
    lighting = lighting_styles[variant_index % len(lighting_styles)]
    texture = textures[variant_index % len(textures)]

    # 🎨 PROMPTS POR ESTILO (NÍVEL ALBUM)
    prompts = {

        "metal": f"""
        dark demonic ritual scene, massive horned demon emerging from shadows,
        gothic cathedral destroyed, burning altar, fire and ash everywhere,
        terrifying presence, red and black color palette,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic composition, album cover quality,
        emotionally intense, not generic, no text, no watermark, vertical 9:16
        """,

        "rock": f"""
        dark rock concert scene, silhouette guitarist in red light,
        heavy smoke, fire sparks, underground stage energy,
        rebellious atmosphere, dramatic shadows,
        {angle}, {lighting}, {texture},
        cinematic, ultra detailed, album cover style,
        strong emotional impact, no text, no watermark, vertical 9:16
        """,

        "phonk": f"""
        japanese street at night, neon lights reflecting on wet asphalt,
        drift car sliding with smoke, cyberpunk vibe,
        purple and blue tones, underground street racing energy,
        {angle}, neon glow lighting, rain reflections,
        ultra detailed, cinematic, album cover quality,
        aggressive mood, no text, no watermark, vertical 9:16
        """,

        "trap": f"""
        dark luxury trap aesthetic, expensive cars, chains, shadows,
        urban night scene, mysterious figure, rich villain vibe,
        moody lighting, deep contrast,
        {angle}, {lighting}, {texture},
        cinematic, ultra detailed, album cover style,
        powerful and stylish, no text, no watermark, vertical 9:16
        """,

        "lofi": f"""
        lonely room at night, rain on window, warm lamp light,
        nostalgic atmosphere, soft shadows, emotional silence,
        calm and melancholic vibe,
        {angle}, soft cinematic lighting, dust particles,
        ultra detailed, cinematic composition,
        peaceful but sad, no text, no watermark, vertical 9:16
        """,

        "indie": f"""
        dreamy nostalgic scene, empty street at dusk,
        soft light, emotional atmosphere, memory-like feeling,
        cinematic storytelling composition,
        {angle}, soft shadows, film grain,
        ultra detailed, indie aesthetic,
        unique emotional vibe, no text, no watermark, vertical 9:16
        """,

        "electronic": f"""
        futuristic cyber world, glowing lights, digital structures,
        neon energy flowing, sci-fi environment,
        immersive electronic atmosphere,
        {angle}, neon lighting, glitch effects,
        ultra detailed, cinematic, album cover quality,
        modern and intense, no text, no watermark, vertical 9:16
        """,

        "cinematic": f"""
        epic cinematic scene, massive landscape, glowing sky,
        dramatic lighting, emotional scale, film-like composition,
        powerful atmosphere,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic masterpiece,
        high impact visual, no text, no watermark, vertical 9:16
        """,

        "funk": f"""
        brazilian funk nightlife, urban favela aesthetic,
        vibrant colors, party lights, energetic scene,
        bold contrast and movement,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic, album cover style,
        high energy vibe, no text, no watermark, vertical 9:16
        """,

        "dark": f"""
        shadowy mysterious figure, fog, dark red tones,
        sinister cinematic atmosphere,
        ominous presence, horror-inspired visual,
        {angle}, {lighting}, {texture},
        ultra detailed, dramatic composition,
        emotionally intense, no text, no watermark, vertical 9:16
        """,

        "default": f"""
        cinematic aesthetic scene, strong atmosphere,
        dramatic lighting, emotional composition,
        visually striking image,
        {angle}, {lighting}, {texture},
        ultra detailed, album cover quality,
        not generic, no text, no watermark, vertical 9:16
        """
    }

    return prompts.get(style, prompts["default"])
