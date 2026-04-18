import os
import time
import requests

GRAPH_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _get_credentials():
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()

    if not page_id or not token:
        raise EnvironmentError(
            "Facebook não configurado — defina FB_PAGE_ID e FB_PAGE_ACCESS_TOKEN nos Secrets."
        )

    return page_id, token


def _start_reel_upload(page_id, token, file_size):
    url = f"{BASE_URL}/{page_id}/video_reels"

    response = requests.post(
        url,
        params={"access_token": token},
        data={
            "upload_phase": "start",
            "file_size": str(file_size),
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    video_id = data.get("video_id")
    upload_url = data.get("upload_url")

    if not video_id or not upload_url:
        raise RuntimeError(f"Resposta inválida no start do Reel: {data}")

    return video_id, upload_url


def _transfer_reel_bytes(upload_url, video_path):
    file_size = os.path.getsize(video_path)

    with open(video_path, "rb") as f:
        response = requests.post(
            upload_url,
            headers={
                "Authorization": "OAuth",
                "offset": "0",
                "file_size": str(file_size),
            },
            data=f,
            timeout=300,
        )

    response.raise_for_status()
    return response.json() if response.text else {}


def _finish_reel_upload(page_id, token, video_id, title, description):
    url = f"{BASE_URL}/{page_id}/video_reels"

    response = requests.post(
        url,
        params={"access_token": token},
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description[:2200],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def upload_to_facebook(video_path, title, description, max_retries=3):
    page_id, token = _get_credentials()
    file_size = os.path.getsize(video_path)

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Facebook] Tentativa {attempt}/{max_retries}")

            video_id, upload_url = _start_reel_upload(page_id, token, file_size)
            print(f"[Facebook] Sessão iniciada. video_id={video_id}")

            _transfer_reel_bytes(upload_url, video_path)
            print("[Facebook] Upload dos bytes concluído.")

            result = _finish_reel_upload(page_id, token, video_id, title, description)
            fb_id = result.get("id") or result.get("video_id") or video_id

            print(f"[Facebook] ✅ Publicado com sucesso! ID: {fb_id}")
            return result

        except requests.HTTPError as e:
            response = getattr(e, "response", None)
            status = response.status_code if response is not None else "?"
            body = response.text[:1000] if response is not None and response.text else repr(e)
            print(f"[Facebook] ❌ HTTP {status}: {body}")

            if status in (400, 401, 403):
                raise

            wait = 2 ** attempt
            print(f"[Facebook] aguardando {wait}s...")
            time.sleep(wait)

        except requests.RequestException as e:
            print(f"[Facebook] ❌ RequestException: {repr(e)}")
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            print(f"[Facebook] aguardando {wait}s...")
            time.sleep(wait)

        except Exception as e:
            print(f"[Facebook] ❌ erro inesperado: {repr(e)}")
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            print(f"[Facebook] aguardando {wait}s...")
            time.sleep(wait)

    raise RuntimeError("Falha ao postar no Facebook após várias tentativas.")
