import os
import subprocess

OUTPUT_FOLDER = "output"
SHORT_DURATION = 20
FALLBACK_BACKGROUND = "__AUTO_BLACK__"


def create_short(audio_path, background_path, output_name):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    if background_path == FALLBACK_BACKGROUND:
        command = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1080x1920:d=20",
            "-i", audio_path,
            "-t", str(SHORT_DURATION),
            "-shortest",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
    else:
        if background_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            command = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", background_path,
                "-i", audio_path,
                "-t", str(SHORT_DURATION),
                "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0008,1.08)':d=1:s=1080x1920",
                "-shortest",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        else:
            command = [
                "ffmpeg",
                "-y",
                "-stream_loop", "-1",
                "-i", background_path,
                "-i", audio_path,
                "-t", str(SHORT_DURATION),
                "-vf", "scale=1080:1920,format=yuv420p",
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
