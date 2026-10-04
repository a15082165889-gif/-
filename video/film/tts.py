"""Voice-over synthesis with Kokoro (local ONNX model). Results are cached by text."""
import hashlib
import json
import os
import re

import numpy as np

from .story import NARRATION, SPEED, SPOKEN, VOICE

SR = 24000


def _spoken(text):
    for k, v in SPOKEN.items():
        text = re.sub(rf"\b{k}\b", v, text)
    return text


def synthesize(build_dir, model_dir):
    """Returns {line_id: (wav_path, seconds)}; synthesizes only what is not cached."""
    import soundfile as sf
    out_dir = os.path.join(build_dir, "voice")
    os.makedirs(out_dir, exist_ok=True)
    kokoro = None
    result = {}
    for lid, text in NARRATION.items():
        spoken = _spoken(text)
        key = hashlib.sha1(f"{VOICE}|{SPEED}|{spoken}".encode()).hexdigest()[:12]
        path = os.path.join(out_dir, f"{lid}-{key}.wav")
        if not os.path.exists(path):
            if kokoro is None:
                from kokoro_onnx import Kokoro
                kokoro = Kokoro(os.path.join(model_dir, "kokoro.onnx"), os.path.join(model_dir, "voices.bin"))
            samples, sr = kokoro.create(spoken, voice=VOICE, speed=SPEED, lang="en-us")
            samples = _trim(np.asarray(samples, np.float32), sr)
            sf.write(path, samples, sr)
            print(f"  voice {lid}: {len(samples) / sr:.2f}s", flush=True)
        info = sf.info(path)
        result[lid] = (path, info.frames / info.samplerate)
    with open(os.path.join(build_dir, "voice.json"), "w") as f:
        json.dump(result, f, indent=1)
    return result


def _trim(x, sr, thresh=0.004):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.02 * sr))
    b = min(len(x), idx[-1] + int(0.08 * sr))
    return x[a:b]
