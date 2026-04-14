import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]

SUPPORTED_AUDIO = (
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg"
)


def get_drive_service():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    if not credentials_json:
        raise ValueError("Secret GOOGLE_CREDENTIALS não encontrado.")

    creds = Credentials.from_service_account_info(
        json.loads(credentials_json),
        scopes=SCOPES
    )

    service = build("drive", "v3", credentials=creds)
    return service


def find_folder_id(service, parent_folder_id, folder_name):
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=10
    ).execute()

    files = results.get("files", [])
    if not files:
        return None

    return files[0]["id"]


def list_audio_files_in_folder(service, folder_id):
    query = (
        f"'{folder_id}' in parents and "
        f"trashed = false and "
        f"mimeType != 'application/vnd.google-apps.folder'"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()

    files = results.get("files", [])

    audio_files = []
    for file in files:
        if file["name"].lower().endswith(SUPPORTED_AUDIO):
            audio_files.append(file)

    return audio_files
