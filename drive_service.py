import os
import json
from pathlib import Path
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

SUPPORTED_AUDIO = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")

SUPPORTED_ASSETS = (
    ".png", ".jpg", ".jpeg", ".webp",
    ".mp4", ".mov", ".webm", ".mkv"
)

LOCAL_ASSETS_DIR = "assets"

DEFAULT_LOGO_NAME = "logo_darkmark.png"

OPTIONAL_EFFECT_FILES = [
    "rain_overlay.mp4",
    "water_ripple.mp4",
    "particles.mp4",
    "light_leaks.mp4",
]


def get_drive_service():
    """Service Account — para leitura do Drive."""
    credentials_json = os.getenv("GOOGLE_CREDENTIALS") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not credentials_json:
        raise ValueError("Secret GOOGLE_CREDENTIALS nao encontrado.")

    creds = Credentials.from_service_account_info(
        json.loads(credentials_json),
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def get_oauth_drive_service():
    """
    OAuth do usuário — usa as mesmas credenciais do YouTube.
    Tem acesso ao Drive pessoal e Shared Drive.
    """
    raw = os.getenv("YOUTUBE_CREDENTIALS")
    if not raw:
        raise ValueError("YOUTUBE_CREDENTIALS nao encontrado para backup OAuth.")

    creds = OAuthCredentials.from_authorized_user_info(
        json.loads(raw),
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def _safe_name(name: str) -> str:
    return name.replace("'", "\\'")


def find_folder_id(service, parent_folder_id: str, folder_name: str) -> str | None:
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{_safe_name(folder_name)}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )

    try:
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=10,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute()
    except Exception:
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=10,
        ).execute()

    files = results.get("files", [])
    return files[0]["id"] if files else None


def find_file_id(service, parent_folder_id: str, file_name: str) -> str | None:
    """
    Procura um arquivo específico dentro de uma pasta do Drive.
    Retorna o ID ou None.
    """
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{_safe_name(file_name)}' and "
        f"trashed = false and "
        f"mimeType != 'application/vnd.google-apps.folder'"
    )

    try:
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=10,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute()
    except Exception:
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=10,
        ).execute()

    files = results.get("files", [])
    return files[0]["id"] if files else None


def list_files_in_folder(service, folder_id: str) -> list:
    query = (
        f"'{folder_id}' in parents and "
        f"trashed = false and "
        f"mimeType != 'application/vnd.google-apps.folder'"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=500,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()

    return results.get("files", [])


def list_audio_files_in_folder(service, folder_id: str) -> list:
    files = list_files_in_folder(service, folder_id)
    return [f for f in files if f["name"].lower().endswith(SUPPORTED_AUDIO)]


def download_drive_file(service, file_id: str, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    request = service.files().get_media(
        fileId=file_id,
        supportsAllDrives=True,
    )

    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return output_path


def download_drive_file_safe(service, file_id: str, output_path: str) -> str | None:
    """
    Baixa arquivo sem quebrar o bot.
    Se falhar, retorna None.
    """
    try:
        return download_drive_file(service, file_id, output_path)
    except Exception as e:
        print(f"[drive_service] Aviso: falha ao baixar {output_path}: {e}")
        return None


def download_assets_from_drive(
    service,
    parent_folder_id: str,
    assets_folder_name: str = "assets",
    local_assets_dir: str = LOCAL_ASSETS_DIR,
) -> dict:
    """
    Baixa assets opcionais do Drive.

    Estrutura esperada no Drive:

    pasta_principal/
    ├── musicas/
    ├── assets/
    │   ├── logo_darkmark.png
    │   ├── rain_overlay.mp4
    │   ├── water_ripple.mp4
    │   └── particles.mp4

    Se não achar assets, logo ou efeitos, apenas ignora e continua.
    """
    result = {
        "assets_folder_found": False,
        "logo_path": None,
        "effects": {},
        "downloaded": [],
        "missing": [],
    }

    Path(local_assets_dir).mkdir(parents=True, exist_ok=True)

    assets_folder_id = find_folder_id(service, parent_folder_id, assets_folder_name)

    if not assets_folder_id:
        print(f"[drive_service] Pasta '{assets_folder_name}' nao encontrada no Drive. Ignorando assets.")
        return result

    result["assets_folder_found"] = True
    print(f"[drive_service] Pasta de assets encontrada: {assets_folder_name}")

    # Logo
    logo_file_id = find_file_id(service, assets_folder_id, DEFAULT_LOGO_NAME)

    if logo_file_id:
        local_logo_path = str(Path(local_assets_dir) / DEFAULT_LOGO_NAME)
        downloaded = download_drive_file_safe(service, logo_file_id, local_logo_path)

        if downloaded:
            result["logo_path"] = downloaded
            result["downloaded"].append(DEFAULT_LOGO_NAME)
            print(f"[drive_service] Logo baixada: {downloaded}")
    else:
        result["missing"].append(DEFAULT_LOGO_NAME)
        print(f"[drive_service] Logo nao encontrada no Drive: {DEFAULT_LOGO_NAME}")

    # Efeitos opcionais
    for effect_name in OPTIONAL_EFFECT_FILES:
        effect_file_id = find_file_id(service, assets_folder_id, effect_name)

        if not effect_file_id:
            result["missing"].append(effect_name)
            print(f"[drive_service] Efeito opcional nao encontrado: {effect_name}")
            continue

        local_effect_path = str(Path(local_assets_dir) / effect_name)
        downloaded = download_drive_file_safe(service, effect_file_id, local_effect_path)

        if downloaded:
            result["effects"][effect_name] = downloaded
            result["downloaded"].append(effect_name)
            print(f"[drive_service] Efeito baixado: {downloaded}")

    return result


def download_all_assets_in_folder(
    service,
    parent_folder_id: str,
    assets_folder_name: str = "assets",
    local_assets_dir: str = LOCAL_ASSETS_DIR,
) -> dict:
    """
    Baixa todos os arquivos suportados da pasta assets.
    Útil se depois você quiser colocar novos efeitos sem alterar código.

    Se não achar nada, ignora.
    """
    result = {
        "assets_folder_found": False,
        "downloaded": [],
        "skipped": [],
    }

    Path(local_assets_dir).mkdir(parents=True, exist_ok=True)

    assets_folder_id = find_folder_id(service, parent_folder_id, assets_folder_name)

    if not assets_folder_id:
        print(f"[drive_service] Pasta '{assets_folder_name}' nao encontrada. Ignorando.")
        return result

    result["assets_folder_found"] = True

    files = list_files_in_folder(service, assets_folder_id)

    for f in files:
        name = f.get("name", "")

        if not name.lower().endswith(SUPPORTED_ASSETS):
            result["skipped"].append(name)
            continue

        local_path = str(Path(local_assets_dir) / name)
        downloaded = download_drive_file_safe(service, f["id"], local_path)

        if downloaded:
            result["downloaded"].append(name)

    print(f"[drive_service] Assets baixados: {result['downloaded']}")
    return result


def upload_file_to_drive(service, folder_id: str, file_path: str) -> dict:
    """
    Faz upload para o Drive.
    Tenta primeiro com Service Account.
    Se falhar por quota, tenta OAuth do usuário.
    """
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id],
    }

    media = MediaFileUpload(file_path, resumable=True)

    try:
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name",
            supportsAllDrives=True,
        ).execute()
        return uploaded

    except Exception as e:
        if "storageQuota" in str(e) or "quota" in str(e).lower() or "403" in str(e):
            print("[drive_service] Service Account sem quota — tentando OAuth do usuario...")

            oauth_service = get_oauth_drive_service()
            media2 = MediaFileUpload(file_path, resumable=True)

            uploaded = oauth_service.files().create(
                body=file_metadata,
                media_body=media2,
                fields="id,name",
                supportsAllDrives=True,
            ).execute()
            return uploaded

        raise


def delete_drive_file(service, file_id: str):
    service.files().delete(
        fileId=file_id,
        supportsAllDrives=True,
    ).execute()
