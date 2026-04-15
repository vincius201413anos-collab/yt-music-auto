import os
import replicate


def generate_image(prompt: str) -> str:
    token = os.getenv("REPLICATE_API_TOKEN")

    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN não encontrado nas variáveis de ambiente.")

    try:
        output = replicate.run(
            "stability-ai/stable-diffusion",
            input={
                "prompt": prompt
            }
        )

        if not output:
            raise RuntimeError("O Replicate não retornou nenhuma imagem.")

        if isinstance(output, list):
            return output[0]

        return output

    except Exception as e:
        raise RuntimeError(f"Erro ao gerar imagem no Replicate: {e}")
