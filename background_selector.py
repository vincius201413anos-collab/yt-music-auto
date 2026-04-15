import os
from ai_image_generator import generate_image

def resolve_background(style, music_name):
    print("Resolvendo background...")

    background_folder = "assets/backgrounds"

    # tenta achar background local primeiro
    local_background = None

    if os.path.exists(background_folder):
        for file in os.listdir(background_folder):
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                local_background = os.path.join(background_folder, file)
                break

    if local_background:
        print(f"Background local encontrado: {local_background}")
        return local_background

    print("Nenhum background local válido encontrado. Gerando imagem com IA...")

    # prompt simples (você pode melhorar depois)
    prompt = f"{music_name}, {style} music visual, neon atmosphere, moody lights, vertical 9:16, ultra detailed"
    print(f"Prompt IA: {prompt}")

    try:
        image_url = generate_image(prompt)
        print(f"Imagem gerada com sucesso: {image_url}")
        return image_url

    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com IA: {e}")

        # fallback final
        fallback_path = "assets/backgrounds/default.jpg"

        if os.path.exists(fallback_path):
            print(f"Usando fallback padrão: {fallback_path}")
            return fallback_path

        raise RuntimeError(
            "Nenhum background local encontrado e a geração por IA falhou."
        )
