import os
import random
import subprocess
from pathlib import Path

from edit_profiles import EDIT_PROFILES

OUTPUT_FOLDER = "output"
MIN_SHORT_DURATION = 25
MAX_SHORT_DURATION = 35
FALLBACK_BACKGROUND = "__AUTO_BLACK__"


def get_media_duration(file_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def pick_short_window(audio_duration):
    if audio_duration <= MIN_SHORT_DURATION:
        short_duration = max(1, int(audio_duration))
        start_time = 0
    else:
        short_duration = random.randint(
            MIN_SHORT_DURATION,
            min(MAX_SHORT_DURATION, int(audio_duration))
        )
        max_start = max(0, int(audio_duration - short_duration))
        start_time = random.randint(0, max_start) if max_start > 0 else 0

    return start_time, short_duration


def get_profile(style):
    default_profile = {
        "zoom_speed": 0.0020,
        "max_zoom": 1.18,
        "brightness": 0.00,
        "contrast": 1.12,
        "saturation": 1.08,
        "blur": 0.0,
        "fps": 30,
        "sharpen": 1.2,
        "shake_x": 4,
        "shake_y": 4,
        "flash_strength": 0.18,
        "flash_interval": 0.75,
        "flash_duration": 0.07,
        "pulse_strength": 0.0025,
    }

    raw = EDIT_PROFILES.get(style, EDIT_PROFILES.get("default", {}))

    return {
        "zoom_speed": raw.get("zoom_speed", raw.get("zoom", default_profile["zoom_speed"])),
        "max_zoom": raw.get("max_zoom", default_profile["max_zoom"]),
        "brightness": raw.get("brightness", default_profile["brightness"]),
        "contrast": raw.get("contrast", default_profile["contrast"]),
        "saturation": raw.get("saturation", default_profile["saturation"]),
        "blur": raw.get("blur", default_profile["blur"]),
        "fps": raw.get("fps", default_profile["fps"]),
        "sharpen": raw.get("sharpen", default_profile["sharpen"]),
        "shake_x": raw.get("shake_x", default_profile["shake_x"]),
        "shake_y": raw.get("shake_y", default_profile["shake_y"]),
        "flash_strength": raw.get("flash_strength", default_profile["flash_strength"]),
        "flash_interval": raw.get("flash_interval", default_profile["flash_interval"]),
        "flash_duration": raw.get("flash_duration", default_profile["flash_duration"]),
        "pulse_strength": raw.get("pulse_strength", default_profile["pulse_strength"]),
    }


def build_base_image_filter(profile):
    zoom_speed = profile["zoom_speed"]
    max_zoom = profile["max_zoom"]
    brightness = profile["brightness"]
    contrast = profile["contrast"]
    saturation = profile["saturation"]
    blur = profile["blur"]
    fps = profile["fps"]
    sharpen = profile["sharpen"]
    flash_strength = profile["flash_strength"]
    flash_interval = profile["flash_interval"]
    flash_duration = profile["flash_duration"]
    pulse_strength = profile["pulse_strength"]

    filters = [
        "scale=1400:2488:force_original_aspect_ratio=increase",
        (
            "zoompan="
            f"z='if(lte(on,1),1.0,min(1.0+{zoom_speed}*on+{pulse_strength}*sin(on/6),{max_zoom}))':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920"
        ),
        (
            f"eq=contrast={contrast}:"
            f"brightness='if(lt(mod(t,{flash_interval}),{flash_duration}),{flash_strength},{brightness})':"
            f"saturation={saturation}"
        ),
        f"unsharp=5:5:{sharpen}:5:5:0.0",
    ]

    if blur and blur > 0:
        filters.append(f"gblur=sigma={blur}")

    filters.extend([
        f"fps={fps}",
        "format=yuv420p"
    ])

    return ",".join(filters)


def build_base_video_filter(profile):
    brightness = profile["brightness"]
    contrast = profile["contrast"]
    saturation = profile["saturation"]
    blur = profile["blur"]
    fps = profile["fps"]
    sharpen = profile["sharpen"]
    shake_x = profile["shake_x"]
    shake_y = profile["shake_y"]
    flash_strength = profile["flash_strength"]
    flash_interval = profile["flash_interval"]
    flash_duration = profile["flash_duration"]

    filters = [
        "scale=1120:1992:force_original_aspect_ratio=increase",
        f"crop=1080:1920:x='20+sin(t*7)*{shake_x}':y='20+cos(t*6)*{shake_y}'",
        (
            f"eq=contrast={contrast}:"
            f"brightness='if(lt(mod(t,{flash_interval}),{flash_duration}),{flash_strength},{brightness})':"
            f"saturation={saturation}"
        ),
        f"unsharp=5:5:{sharpen}:5:5:0.0",
    ]

    if blur and blur > 0:
        filters.append(f"gblur=sigma={blur}")

    filters.extend([
        f"fps={fps}",
        "format=yuv420p"
    ])

    return ",".join(filters)


def build_overlay_chain(style, use_fire, particles_exists, glitch_exists):
    chains = []

    if use_fire:
        chains.append(
            "[1:v]scale=1080:1920,fps=30,format=rgba,colorchannelmixer=aa=0.24[fire];"
            "[base][fire]overlay=0:0:format=auto[v1]"
        )
        current = "v1"
    else:
        current = "base"

    if particles_exists:
        index = 2 if use_fire else 1
        chains.append(
            f"[{index}:v]scale=1080:1920,fps=30,format=rgba,colorchannelmixer=aa=0.16[particles];"
            f"[{current}][particles]overlay=0:0:format=auto[v2]"
        )
        current = "v2"

    if glitch_exists:
        index = 3 if use_fire and particles_exists else 2 if (use_fire or particles_exists) else 1
        chains.append(
            f"[{index}:v]scale=1080:1920,fps=30,format=rgba,colorchannelmixer=aa=0.10[glitch];"
            f"[{current}][glitch]overlay=0:0:format=auto[v]"
        )
        current = "v"
    else:
        if current != "v":
            chains.append(f"[{current}]copy[v]")

    return "".join(chains)


def create_short(audio_path, background_path, output_name, style):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    profile = get_profile(style)
    audio_duration = get_media_duration(audio_path)
    start_time, short_duration = pick_short_window(audio_duration)

    fire_overlay = "assets/overlays/fire.mp4"
    particles_overlay = "assets/overlays/particles.mp4"
    glitch_overlay = "assets/overlays/glitch.mp4"

    use_fire = style in ("rock", "metal") and os.path.exists(fire_overlay)
    use_particles = os.path.exists(particles_overlay)
    use_glitch = style in ("phonk", "electronic", "trap") and os.path.exists(glitch_overlay)

    ext = Path(background_path).suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp")

    if background_path == FALLBACK_BACKGROUND:
        command = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={short_duration}",
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration),
            "-shortest",
            "-r", str(profile["fps"]),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(command, check=True)
        return output_path

    if is_image:
        base_filter = build_base_image_filter(profile)

        inputs = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", background_path
        ]

        if use_fire:
            inputs += ["-stream_loop", "-1", "-i", fire_overlay]
        if use_particles:
            inputs += ["-stream_loop", "-1", "-i", particles_overlay]
        if use_glitch:
            inputs += ["-stream_loop", "-1", "-i", glitch_overlay]

        audio_input_index = 1 + int(use_fire) + int(use_particles) + int(use_glitch)

        inputs += [
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration)
        ]

        filter_complex = (
            f"[0:v]{base_filter}[base];" +
            build_overlay_chain(style, use_fire, use_particles, use_glitch)
        )

        command = inputs + [
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", f"{audio_input_index}:a",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    else:
        base_filter = build_base_video_filter(profile)

        inputs = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", background_path
        ]

        if use_fire:
            inputs += ["-stream_loop", "-1", "-i", fire_overlay]
        if use_particles:
            inputs += ["-stream_loop", "-1", "-i", particles_overlay]
        if use_glitch:
            inputs += ["-stream_loop", "-1", "-i", glitch_overlay]

        audio_input_index = 1 + int(use_fire) + int(use_particles) + int(use_glitch)

        inputs += [
            "-ss", str(start_time),
            "-i", audio_path,
            "-t", str(short_duration)
        ]

        filter_complex = (
            f"[0:v]{base_filter}[base];" +
            build_overlay_chain(style, use_fire, use_particles, use_glitch)
        )

        command = inputs + [
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", f"{audio_input_index}:a",
            "-shortest",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    subprocess.run(command, check=True)
    return output_path
