import os
import json
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
SUPPORTED_AUDIO = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")


def get_drive_service():
    """Service Account — para leitura do inbox."""
    credentials_json = os.getenv("GOOGLE_CREDENTIALS") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not credentials_json:
        raise ValueError("Secret GOOGLE_CREDENTIALS nao encontrado.")
    creds = Credentials.from_service_account_info(
        json.loads(credentials_json), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def get_oauth_drive_service():
    """
    OAuth do usuário — usa as mesmas credenciais do YouTube.
    Tem acesso ao Meu Drive pessoal, resolve o erro 403 de quota da Service Account.
    """
    raw = os.getenv("YOUTUBE_CREDENTIALS")
    if not raw:
        raise ValueError("YOUTUBE_CREDENTIALS nao encontrado para backup OAuth.")
    creds = OAuthCredentials.from_authorized_user_info(
        json.loads(raw),
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def find_folder_id(service, parent_folder_id: str, folder_name: str) -> str | None:
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{folder_name}' and "
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
        files = results.get("files", [])
        return files[0]["id"] if files else None
    except Exception:
        # Fallback sem supportsAllDrives (OAuth pessoal não precisa)
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=10,
        ).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None


def list_audio_files_in_folder(service, folder_id: str) -> list:
    query = (
        f"'{folder_id}' in parents and "
        f"trashed = false and "
        f"mimeType != 'application/vnd.google-apps.folder'"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=200,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()
    files = results.get("files", [])
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


def upload_file_to_drive(service, folder_id: str, file_path: str) -> dict:
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id],
    }
    media = MediaFileUpload(file_path, resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name",
    ).execute()
    return uploaded


def delete_drive_file(service, file_id: str):
    service.files().delete(fileId=file_id).execute()
