import json
import librosa
import numpy as np

def generate_audio_data(input_path, output_path="remotion/public/audio_data.json"):
    y, sr = librosa.load(input_path)

    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

    # normaliza
    rms = rms / np.max(rms)

    data = rms.tolist()

    with open(output_path, "w") as f:
        json.dump(data, f)

    print(f"audio_data.json gerado com {len(data)} pontos")
