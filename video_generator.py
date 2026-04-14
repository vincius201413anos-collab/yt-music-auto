import os
import random
import subprocess
from pathlib import Path


OUTPUT_FOLDER = "output"
SHORT_DURATION = 20


def create_short(audio_path, background_path, output_name):

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", background_path,
        "-i", audio_path,
        "-t", str(SHORT_DURATION),
        "-vf",
        "scale=1080:1920,format=yuv420p",
        "-shortest",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    subprocess.run(command, check=True)

    return output_path
