import os
import replicate


def generate_image(prompt: str) -> str:
    token = os.getenv("REPLICATE_API_TOKEN")

    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN não encontrado.")

    try:
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e7b2f9d9d0c4e1c9c35e5ad9d1fdfd8c4c6d7a7e9e5b",
            input={
                "prompt": prompt
            }
        )

        if isinstance(output, list):
            return output[0]

        return output

    except Exception as e:
        raise RuntimeError(f"Erro ao gerar imagem: {e}")
