import os
import time
import requests

GRAPH_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


# ===== PEGAR CREDENCIAIS =====
def _get_credentials():
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()

    if not page_id or not token:
        raise EnvironmentError(
            "Facebook não configurado — defina FB_PAGE_ID e FB_PAGE_ACCESS_TOKEN nos Secrets."
        )

    return page_id, token


# ===== UPLOAD SIMPLES (ESTÁVEL) =====
def _upload_video(page_id, token, video_path, title, description):
    url = f"{BASE_URL}/{page_id}/videos"

    with open(video_path, "rb") as f:
        response = requests.post(
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

    response.raise_for_status()
    return response.json()


# ===== FUNÇÃO PRINCIPAL =====
def upload_to_facebook(video_path, title, description, max_retries=3):
    page_id, token = _get_credentials()

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Facebook] Tentativa {attempt}/{max_retries}")

            result = _upload_video(page_id, token, video_path, title, description)

            fb_id = result.get("id") or result.get("video_id", "?")
            print(f"[Facebook] ✅ Publicado com sucesso! ID: {fb_id}")

            return result

        except requests.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            body = e.response.text[:500] if e.response else ""
            print(f"[Facebook] ❌ HTTP {status}: {body}")

            # erro de token ou permissão → não adianta tentar de novo
            if status in (400, 401, 403):
                raise

            wait = 2 ** attempt
            print(f"[Facebook] aguardando {wait}s...")
            time.sleep(wait)

        except Exception as e:
            print(f"[Facebook] ❌ erro: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError("Falha ao postar no Facebook após várias tentativas.")
