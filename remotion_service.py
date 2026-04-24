import os
import shutil
import subprocess

def render_remotion_video(input_video, audio_data_path, output_path):
    """
    Renderiza vídeo final com Remotion usando:
    - input.mp4
    - audio_data.json
    - logo.png
    """

    remotion_dir = "remotion"
    public_dir = os.path.join(remotion_dir, "public")

    os.makedirs(public_dir, exist_ok=True)

    # copia vídeo base
    shutil.copy(input_video, os.path.join(public_dir, "input.mp4"))

    # copia audio data
    if os.path.exists(audio_data_path):
        shutil.copy(audio_data_path, os.path.join(public_dir, "audio_data.json"))

    # garante logo
    if os.path.exists("assets/logo.png"):
        shutil.copy("assets/logo.png", os.path.join(public_dir, "logo.png"))

    # roda render do remotion
    cmd = [
        "npx",
        "remotion",
        "render",
        "MyComposition",
        output_path,
    ]

    subprocess.run(cmd, cwd=remotion_dir, check=True)

    return output_path
