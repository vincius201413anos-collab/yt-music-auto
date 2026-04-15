import replicate
import requests
import os
import tempfile
from pathlib import Path


def generate_image(prompt: str, output_path: str = None) -> str | None:
    """
    Gera imagem via Replicate e salva localmente.
    Retorna o caminho do arquivo salvo, ou None em caso de falha.
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("[IA] REPLICATE_API_TOKEN não configurado")
        return None

    if output_path is None:
        output_path = tempfile.mktemp(suffix=".png")

    # ✅ Modelos em ordem de preferência (do mais rápido/barato ao mais pesado)
    MODELS = [
        {
            "id": "black-forest-labs/flux-schnell",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "9:16",   # perfeito para Shorts
                "output_format": "png",
                "num_outputs": 1,
            },
        },
        {
            "id": "stability-ai/stable-diffusion-3",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "output_format": "png",
            },
        },
        {
            # SDXL com hash fixo — versão estável conhecida
            "id": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1792,
                "num_outputs": 1,
            },
        },
    ]

    for model in MODELS:
        try:
            print(f"[IA] Tentando modelo: {model['id']}")
            output = replicate.run(model["id"], input=model["input"])

            # ✅ output é lista de FileOutput — pegar o primeiro
            if not output:
                print("[IA] Output vazio, tentando próximo modelo...")
                continue

            file_output = output[0]

            # ✅ Duas formas de obter a imagem:
            # Opção A — via .read() direto (recomendado)
            image_bytes = file_output.read()
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            print(f"[IA] ✅ Imagem gerada com sucesso: {output_path}")
            return output_path

        except replicate.exceptions.ModelError as e:
            print(f"[IA] ModelError em {model['id']}: {e}")
            continue
        except Exception as e:
            print(f"[IA] Erro em {model['id']}: {e}")
            continue

    print("[IA] ❌ Todos os modelos falharam")
    return None


def get_image_url(prompt: str) -> str | None:
    """
    Versão alternativa que retorna a URL da imagem (sem baixar).
    Útil se quiser passar a URL direto pro FFmpeg.
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return None

    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "output_format": "png",
                "num_outputs": 1,
            },
        )
        if output:
            return output[0].url   # ✅ .url retorna a string da URL
    except Exception as e:
        print(f"[IA] Erro ao obter URL: {e}")

    return None
