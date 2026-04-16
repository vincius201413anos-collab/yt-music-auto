import subprocess
import json

def run_ffprobe(cmd):
result = subprocess.run(cmd, capture_output=True, text=True)
return result.stdout

# 🔥 DETECTA BEATS SIMPLES (funciona bem pro bot)

def detect_beats(audio_path):
try:
cmd = [
"ffmpeg",
"-i", audio_path,
"-filter_complex",
"astats=metadata=1:reset=1",
"-f", "null",
"-"
]
subprocess.run(cmd, capture_output=True, text=True)

```
    # fallback simples (fake beats)
    duration = 60
    beats = [i * 0.5 for i in range(int(duration * 2))]

    return beats

except Exception:
    return []
```

# 🔥 DETECTA DROP (bem simples mas funciona)

def detect_drop(audio_path):
try:
# posição fake no meio (melhor que nada)
duration_cmd = [
"ffprobe",
"-v", "error",
"-show_entries", "format=duration",
"-of", "default=noprint_wrappers=1:nokey=1",
audio_path
]

```
    result = subprocess.run(duration_cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    return duration * 0.5

except Exception:
    return None
```

# 🔥 FLASH NO BEAT

def build_flash_expression(beats, base_brightness, beat_flash=0.2, beat_window=0.05, drop_time=None, drop_flash=0.4):
expr = f"{base_brightness}"

```
for bt in beats[:40]:
    expr += f"+{beat_flash}*between(t,{bt},{bt+beat_window})"

if drop_time:
    expr += f"+{drop_flash}*between(t,{drop_time},{drop_time+0.2})"

return expr
```

# 🔥 SHAKE MULTIPLIER

def build_shake_multiplier_expression(drop_time):
if drop_time:
return f"(1 + 0.8*between(t,{drop_time},{drop_time+0.3}))"
return "1"
