import os
import tempfile
import requests
import time
import random


def _enrich_prompt(prompt: str) -> str:
    variations = [
        "unique composition",
        "different camera angle",
        "alternate framing",
        "dynamic perspective",
        "cinematic depth",
        "dramatic lighting",
        "center-focused composition",
        "fresh visual arrangement",
        "distinct scene layout",
        "new artistic framing",
    ]

    booster = random.choice(variations)

    return (
        f"{prompt}, {booster}, "
        "high quality, ultra detailed, no text, no watermark, no logo"
    )


# ══════════════════════════════════════════════
# OPÇÃO 1 — Replicate
# ══════════════════════════════════════════════
def _generate_via_replicate(prompt: str, output_path: str) -> bool:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        return False

    url = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }

    payload = {
        "input": {
            "prompt": _enrich_prompt(prompt),
            "aspect_ratio": "9:16",
            "output_format": "png",
            "num_outputs": 1,
            "num_inference_steps": 4,
            "seed": random.randint(1, 999999999),
        }
    }

    try:
        print("[IA] Tentando Replicate (flux-schnell via HTTP direto)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=90)

        if resp.status_code == 402:
            print("[IA] Replicate: conta sem crédito/billing configurado")
            return False

        if resp.status_code == 422:
            print(f"[IA] Replicate 422: {resp.text[:300]}")
            return False

        if not resp.ok:
            print(f"[IA] Replicate erro {resp.status_code}: {resp.text[:300]}")
            return False

        data = resp.json()

        if data.get("status") not in ("succeeded",):
            prediction_url = data.get("urls", {}).get("get")

            if prediction_url:
                for _ in range(30):
                    time.sleep(2)

                    poll_resp = requests.get(
                        prediction_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=20
                    )

                    if not poll_resp.ok:
                        print(f"[IA] Polling Replicate falhou: {poll_resp.status_code}")
                        return False

                    poll = poll_resp.json()
                    status = poll.get("status")

                    if status == "succeeded":
                        data = poll
                        break

                    if status == "failed":
                        print(f"[IA] Replicate prediction falhou: {poll.get('error')}")
                        return False

        output = data.get("output")
        if not output:
            print("[IA] Replicate: sem output na resposta")
            return False

        img_url = output[0] if isinstance(output, list) else output

        img_resp = requests.get(img_url, timeout=60)
        if not img_resp.ok:
            print(f"[IA] Erro ao baixar imagem do Replicate: {img_resp.status_code}")
            return False

        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        print(f"[IA] ✅ Replicate OK: {output_path}")
        return True

    except Exception as e:
        print(f"[IA] Replicate exceção: {e}")

    return False


# ══════════════════════════════════════════════
# OPÇÃO 2 — Hugging Face
# ══════════════════════════════════════════════
def _generate_via_huggingface(prompt: str, output_path: str) -> bool:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("[IA] HF_TOKEN não configurado")
        return False

    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": _enrich_prompt(prompt)}

    try:
        print("[IA] Tentando Hugging Face (FLUX.1-schnell)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.status_code == 503:
            try:
                wait = resp.json().get("estimated_time", 20)
            except Exception:
                wait = 20

            print(f"[IA] HF modelo carregando, aguardando {wait:.0f}s...")
            time.sleep(min(wait, 30))
            resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.ok and resp.headers.get("content-type", "").startswith("image"):
            with open(output_path, "wb") as f:
                f.write(resp.content)

            print(f"[IA] ✅ Hugging Face OK: {output_path}")
            return True

        print(f"[IA] HF erro {resp.status_code}: {resp.text[:300]}")

    except Exception as e:
        print(f"[IA] HF exceção: {e}")

    return False


# ══════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════
def generate_image(prompt: str, output_path: str = None) -> str | None:
    """
    Gera imagem com IA.
    Tenta Replicate → Hugging Face → None.
    Retorna caminho do arquivo ou None.
    """
    if output_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        output_path = temp_path

    print(f"[IA] Gerando imagem para: {prompt[:80]}...")

    if _generate_via_replicate(prompt, output_path):
        return output_path

    if _generate_via_huggingface(prompt, output_path):
        return output_path

    print("[IA] ❌ Todas as opções falharam — usando fallback local")
    return None
