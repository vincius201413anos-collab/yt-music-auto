"""
facebook_service.py — Upload de vídeo/Reel no Facebook via Graph API.
Versão ajustada para usar os nomes corretos dos secrets do GitHub Actions.

Secrets necessários:
  FB_PAGE_ID
  FB_PAGE_ACCESS_TOKEN
"""

import os
import time
import requests

GRAPH_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _get_credentials() -> tuple[str, str]:
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()

    if not page_id or not token:
        raise EnvironmentError(
            "Facebook não configurado — defina FB_PAGE_ID e "
            "FB_PAGE_ACCESS_TOKEN nos Secrets do GitHub Actions."
        )

    return page_id, token


# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD SIMPLES
# ──────────────────────────────────────────────────────────────────────────────

def _simple_upload(
    page_id: str,
    token: str,
    video_path: str,
    title: str,
    description: str,
) -> dict:
    """
    Upload direto para a página.
    Mais simples e mais estável para o seu caso agora.
    """
    url = f"{BASE_URL}/{page_id}/videos"

    with open(video_path, "rb") as f:
        resp = requests.post(
            url,
            params={"access_token": token},
            data={
                "title": title[:255],
                "description": description[:2200],
                "published": "true",
            },
            files={"source": f},
            timeout=300,
        )

    resp.raise_for_status()
    return resp.json()


# ──────────────────────────────────────────────────────────────────────────────
# FUNÇÃO PÚBLICA
# ──────────────────────────────────────────────────────────────────────────────

def upload_to_facebook(
    video_path: str,
    title: str,
    description: str,
    max_retries: int = 3,
) -> dict:
    """
    Publica vídeo no Facebook.

    Retorna dict com o ID do vídeo.
    """
    page_id, token = _get_credentials()

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  [Facebook] Tentativa {attempt}/{max_retries}")
            result = _simple_upload(page_id, token, video_path, title, description)

            fb_id = result.get("id") or result.get("video_id", "?")
            print(f"  [Facebook] ✅ Publicado! ID: {fb_id}")
            return result

        except requests.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            body = e.response.text[:500] if e.response else ""
            print(f"  [Facebook] ❌ HTTP {status}: {body}")

            if status in (400, 401, 403):
                raise

            wait = 2 ** attempt
            print(f"  [Facebook] Aguardando {wait}s antes de retentar…")
            time.sleep(wait)

        except Exception as e:
            print(f"  [Facebook] ❌ Erro: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError("Todas as tentativas de upload para o Facebook falharam.")


# Compatibilidade com código antigo
def upload_facebook_reel(video_path: str, title: str, description: str = "") -> dict:
    if not description:
        description = title
    return upload_to_facebook(video_path, title, description)
