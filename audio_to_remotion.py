import json
import librosa
import numpy as np
import os

def generate_audio_data(input_path, output_path="remotion/public/audio_data.json"):
# garante que a pasta existe
os.makedirs(os.path.dirname(output_path), exist_ok=True)

```
y, sr = librosa.load(input_path)

hop_length = 512
rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

# evita divisão por zero
max_val = np.max(rms) if np.max(rms) != 0 else 1
rms = rms / max_val

data = rms.tolist()

with open(output_path, "w") as f:
    json.dump(data, f)

print(f"audio_data.json gerado com {len(data)} pontos")
```
