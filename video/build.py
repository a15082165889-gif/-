#!/usr/bin/env python3
"""Build the film.

    python3 build.py                 # full build -> build/still_rolling.mp4
    python3 build.py --stills 12 80  # render single frames (seconds) to build/stills/ for checking
    python3 build.py --plan          # print the shot timings

Your own photos can replace the stand-in imagery: put them in video/photos/ (see photos/README.md).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from film import engine  # noqa: E402
from film.gfx import FPS, H, W  # noqa: E402
from film.tts import synthesize  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
MODELS = os.path.join(HERE, ".models")
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


def ensure_models():
    os.makedirs(MODELS, exist_ok=True)
    for name, url in (("kokoro.onnx", f"{KOKORO}/kokoro-v1.0.int8.onnx"), ("voices.bin", f"{KOKORO}/voices-v1.0.bin")):
        p = os.path.join(MODELS, name)
        if not os.path.exists(p):
            print(f"  downloading {name}", flush=True)
            subprocess.run(["curl", "-sSL", "-o", p, url], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--out", default=os.path.join(BUILD, "still_rolling.mp4"))
    ap.add_argument("--range", nargs=2, type=float, help="render only this time range (seconds)")
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    t0 = time.time()

    print("voice-over", flush=True)
    voice_path = os.path.join(BUILD, "voice.json")
    if args.plan or args.stills is not None:
        voice = json.load(open(voice_path)) if os.path.exists(voice_path) else None
    else:
        voice = None
    if voice is None:
        ensure_models()
        voice = synthesize(BUILD, MODELS)
    shots, total = engine.build_timeline(voice)
    if args.plan:
        for s in shots:
            print(f"{s.start:7.2f}  {s.dur:6.2f}  {s.id:14s} " + " ".join(f"{k}@{v[0]:.1f}" for k, v in s.cues.items()))
        print(f"total {total:.1f}s")
        return

    print("footage", flush=True)
    engine.ensure_footage()
    engine.prepare_all(shots, args.jobs)

    if args.stills is not None:
        import cairo  # noqa: F401
        os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
        r = engine.Renderer(shots, total, voice)
        for t in args.stills:
            data = r.render(int(round(t * FPS)))
            from PIL import Image
            img = Image.frombuffer("RGBA", (W, H), data, "raw", "BGRA", 0, 1).convert("RGB")
            p = os.path.join(BUILD, "stills", f"t{t:07.2f}.jpg")
            img.save(p, quality=88)
            print(p)
        r.close()
        return

    print("sound", flush=True)
    from film import audio
    wav = os.path.join(BUILD, "mix.wav")
    audio.render(shots, total, voice, wav)
    engine.write_srt(engine.build_subtitles(shots, voice), os.path.join(BUILD, "still_rolling.srt"))

    print(f"picture: {total:.1f}s, {int(total * FPS)} frames", flush=True)
    f_start, f_end = 0, int(round(total * FPS))
    if args.range:
        f_start, f_end = int(args.range[0] * FPS), int(args.range[1] * FPS)
    n = max(1, args.jobs * 3)
    bounds = [f_start + (f_end - f_start) * i // n for i in range(n + 1)]
    parts = [(bounds[i], bounds[i + 1], os.path.join(BUILD, f"part{i:02d}.mp4"), args.crf) for i in range(n)]
    with Pool(args.jobs) as pool:
        for i, p in enumerate(pool.imap(engine.render_chunk, parts)):
            print(f"  part {i + 1}/{n} done  ({time.time() - t0:.0f}s)", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p[2]}'\n")
    a_off = f_start / FPS
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ss", f"{a_off:.3f}", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "224k", "-shortest", "-movflags", "+faststart", args.out], check=True)
    for p in parts:
        os.remove(p[2])
    print(f"done: {args.out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
