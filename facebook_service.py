"""
facebook_service.py — Upload de Reels no Facebook via Graph API v19.
Posta vídeo curto (Reel) em sincronismo com o YouTube.

Variáveis de ambiente necessárias (adicionar nos Secrets do GitHub Actions):
  FB_PAGE_ID         → ID numérico da sua página do Facebook
  FB_ACCESS_TOKEN    → Page Access Token com permissões:
                       pages_manage_posts, pages_read_engagement,
                       publish_video (ou publish_to_groups)

Como obter o token:
  1. https://developers.facebook.com → criar App → adicionar produto "Pages API"
  2. Gerar Page Access Token de longa duração (60 dias) via Graph Explorer
  3. Colar como secret FB_ACCESS_TOKEN no GitHub
"""

import os
import time
import requests
from pathlib import Path

GRAPH_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _get_credentials() -> tuple[str, str]:
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        raise EnvironmentError(
            "Facebook não configurado — defina FB_PAGE_ID e FB_ACCESS_TOKEN "
            "nos Secrets do GitHub Actions."
        )
    return page_id, token


# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD RESUMABLE (recomendado para arquivos > 1 MB)
# ──────────────────────────────────────────────────────────────────────────────

def _init_upload_session(page_id: str, token: str, file_size: int) -> str:
    """Inicia sessão de upload e retorna video_id."""
    url = f"{BASE_URL}/{page_id}/video_reels"
    resp = requests.post(
        url,
        params={"access_token": token},
        json={
            "upload_phase": "start",
            "file_size": file_size,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    video_id = data.get("video_id")
    if not video_id:
        raise RuntimeError(f"Falha ao iniciar sessão FB: {data}")
    return video_id


def _upload_video_bytes(
    video_id: str,
    token: str,
    video_path: str,
) -> None:
    """Envia os bytes do vídeo para a sessão de upload."""
    url = f"{BASE_URL}/{video_id}"
    file_size = os.path.getsize(video_path)

    with open(video_path, "rb") as f:
        resp = requests.post(
            url,
            params={"access_token": token},
            headers={
                "Content-Type": "application/octet-stream",
                "file_size": str(file_size),
                "file_offset": "0",
            },
            data=f,
            timeout=300,
        )
    resp.raise_for_status()


def _finish_upload(
    page_id: str,
    token: str,
    video_id: str,
    title: str,
    description: str,
) -> dict:
    """Finaliza o upload e publica o Reel."""
    url = f"{BASE_URL}/{page_id}/video_reels"
    resp = requests.post(
        url,
        params={"access_token": token},
        json={
            "upload_phase": "finish",
            "video_id": video_id,
            "title": title[:255],
            "description": description[:2200],
            "video_state": "PUBLISHED",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD SIMPLES (fallback para arquivos pequenos / testes)
# ──────────────────────────────────────────────────────────────────────────────

def _simple_upload(
    page_id: str,
    token: str,
    video_path: str,
    title: str,
    description: str,
) -> dict:
    """Upload direto sem sessão — para vídeos < 1 GB."""
    url = f"{BASE_URL}/{page_id}/videos"
    with open(video_path, "rb") as f:
        resp = requests.post(
            url,
            params={"access_token": token},
            data={
                "title": title[:255],
                "description": description[:2200],
                "published": "true",
                "reels_targeting": "true",       # marca como Reel
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
    Publica um Reel no Facebook.

    Retorna o dict com 'id' do vídeo publicado.
    Lança exceção se todos os retries falharem.
    """
    page_id, token = _get_credentials()
    file_size = os.path.getsize(video_path)

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  [Facebook] Tentativa {attempt}/{max_retries} "
                  f"({file_size / 1_048_576:.1f} MB)")

            if file_size > 1_048_576:          # > 1 MB → resumable
                video_id = _init_upload_session(page_id, token, file_size)
                print(f"  [Facebook] Sessão iniciada — video_id: {video_id}")
                _upload_video_bytes(video_id, token, video_path)
                result = _finish_upload(page_id, token, video_id, title, description)
            else:                              # ≤ 1 MB → simples (só testes)
                result = _simple_upload(page_id, token, video_path, title, description)

            fb_id = result.get("id") or result.get("video_id", "?")
            print(f"  [Facebook] ✅ Publicado! ID: {fb_id}")
            return result

        except requests.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            body = e.response.text[:300] if e.response else ""
            print(f"  [Facebook] ❌ HTTP {status}: {body}")

            # Token expirado ou sem permissão — não adianta retentar
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
