import os
import replicate

def generate_image(prompt):
    # pega o token do ambiente (GitHub Actions)
    token = os.getenv("REPLICATE_API_TOKEN")

    if not token:
        raise RuntimeError("❌ REPLICATE_API_TOKEN não encontrado")

    try:
        output = replicate.run(
            "stability-ai/sdxl:latest",
            input={
                "prompt": prompt,
                "width": 1024,
                "height": 1792
            }
        )

        # garante que retornou algo válido
        if not output or len(output) == 0:
            raise RuntimeError("❌ Replicate não retornou imagem")

        return output[0]

    except Exception as e:
        raise RuntimeError(f"❌ Erro ao gerar imagem: {e}")
