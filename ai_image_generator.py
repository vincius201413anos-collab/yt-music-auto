import os
import tempfile
import requests
import time


# ══════════════════════════════════════════════
# OPÇÃO 1 — Replicate (pago, mas barato ~$0.003)
# ══════════════════════════════════════════════
def _generate_via_replicate(prompt: str, output_path: str) -> bool:
    """Usa Replicate via HTTP direto — evita bugs de versão da lib Python."""
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        return False

    # Endpoint correto para modelos "oficiais" (sem version hash)
    url = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",  # espera resultado síncrono (até 60s)
    }
    payload = {
        "input": {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "output_format": "png",
            "num_outputs": 1,
            "num_inference_steps": 4,
        }
    }

    try:
        print("[IA] Tentando Replicate (flux-schnell via HTTP direto)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=90)

        if resp.status_code == 402:
            print("[IA] Replicate: conta sem crédito/billing configurado")
            return False
        if resp.status_code == 422:
            print(f"[IA] Replicate 422: {resp.text}")
            return False
        if not resp.ok:
            print(f"[IA] Replicate erro {resp.status_code}: {resp.text[:200]}")
            return False

        data = resp.json()

        # Polling se não veio síncrono
        if data.get("status") not in ("succeeded",):
            prediction_url = data.get("urls", {}).get("get")
            if prediction_url:
                for _ in range(30):  # max 60s
                    time.sleep(2)
                    poll = requests.get(
                        prediction_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    ).json()
                    if poll.get("status") == "succeeded":
                        data = poll
                        break
                    if poll.get("status") == "failed":
                        print(f"[IA] Replicate prediction falhou: {poll.get('error')}")
                        return False

        output = data.get("output")
        if not output:
            print("[IA] Replicate: sem output na resposta")
            return False

        img_url = output[0] if isinstance(output, list) else output
        img_resp = requests.get(img_url, timeout=30)
        if img_resp.ok:
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
            print(f"[IA] ✅ Replicate OK: {output_path}")
            return True

    except Exception as e:
        print(f"[IA] Replicate exceção: {e}")

    return False


# ══════════════════════════════════════════════
# OPÇÃO 2 — Hugging Face (GRATUITO, sem billing)
# ══════════════════════════════════════════════
def _generate_via_huggingface(prompt: str, output_path: str) -> bool:
    """
    Usa HuggingFace Inference API — gratuito com HF_TOKEN.
    Crie token em: https://huggingface.co/settings/tokens
    Adicione como secret: HF_TOKEN
    """
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("[IA] HF_TOKEN não configurado (gratuito — veja docs)")
        return False

    # FLUX.1-schnell no HuggingFace — gratuito
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}

    try:
        print("[IA] Tentando Hugging Face (FLUX.1-schnell — gratuito)...")
        resp = requests.post(url, json=payload, headers=headers, timeout=120)

        # Modelo pode estar carregando
        if resp.status_code == 503:
            wait = resp.json().get("estimated_time", 20)
            print(f"[IA] HF modelo carregando, aguardando {wait:.0f}s...")
            time.sleep(min(wait, 30))
            resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.ok and resp.headers.get("content-type", "").startswith("image"):
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"[IA] ✅ Hugging Face OK: {output_path}")
            return True
        else:
            print(f"[IA] HF erro {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        print(f"[IA] HF exceção: {e}")

    return False


# ══════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════
def generate_image(prompt: str, output_path: str = None) -> str | None:
    """
    Gera imagem com IA. Tenta Replicate → Hugging Face → None (usa fallback).
    Retorna caminho do arquivo ou None.
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".png")

    print(f"[IA] Gerando imagem para: {prompt[:60]}...")

    if _generate_via_replicate(prompt, output_path):
        return output_path

    if _generate_via_huggingface(prompt, output_path):
        return output_path

    print("[IA] ❌ Todas as opções falharam — usando fallback local")
    return None
