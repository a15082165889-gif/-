"""Label 3-second windows of each clip's audio: Speech / BGM / Applause / Laughter, plus loudness."""
import glob, json, os, subprocess, sys
import numpy as np, sherpa_onnx
M = os.path.join(os.path.dirname(__file__), "..", ".models", "sherpa", "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17")
rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f"{M}/model.int8.onnx", tokens=f"{M}/tokens.txt",
                                                     use_itn=True, num_threads=4)
out = {}
for p in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    w = []
    for i in range(0, len(x) - 8000, 48000):
        seg = x[i:i + 48000]
        s = rec.create_stream(); s.accept_waveform(16000, seg); rec.decode_stream(s)
        r = s.result
        db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        w.append([round(i / 16000), r.event.strip("<|>"), r.emotion.strip("<|>"), round(float(db)), r.text[:24]])
    out[os.path.basename(p)] = w
    print(os.path.basename(p), " ".join(f"{t}:{e[:3]}" for t, e, *_ in w), flush=True)
json.dump(out, open("audio_events.json", "w"), ensure_ascii=False, indent=0)
