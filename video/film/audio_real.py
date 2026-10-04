"""Sound for 《前进》: the real sound of each clip (or its separated vocals/crowd stem) is the lead layer;
licensed music sits underneath and ducks under voices; transitions and slams get their own hits."""
import hashlib
import math
import os
import subprocess

import numpy as np
from scipy import signal

from .audio import SR, place
from .audio_epic import apply_cues, make_sfx, transition_sfx
from .engine import BUILD, clip_path
from .gfx import ROOT

STEMS = os.path.join(ROOT, "build", "stems")
UVR_DIR = os.path.join(ROOT, ".models", "uvr")
_sep = None


def _extract(src, a, dur, path, sr=SR, ch=2):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vn",
                    "-ac", str(ch), "-ar", str(sr), path], check=True)


def stem(clip, a, dur):
    """Vocals/crowd stem of a clip range (cached); background music baked into the upload is removed."""
    global _sep
    os.makedirs(STEMS, exist_ok=True)
    key = hashlib.sha1(f"{clip}|{a:.2f}|{dur:.2f}".encode()).hexdigest()[:12]
    out = os.path.join(STEMS, f"{clip}_{key}_voc.wav")
    if os.path.exists(out):
        return out
    wav = os.path.join(STEMS, f"{clip}_{key}.wav")
    _extract(clip_path(clip), a, dur, wav, 44100)
    if _sep is None:
        from audio_separator.separator import Separator
        _sep = Separator(model_file_dir=UVR_DIR, output_dir=STEMS, output_format="WAV", log_level=40)
        _sep.load_model("UVR-MDX-NET-Voc_FT.onnx")
    files = _sep.separate(wav, {"Vocals": f"{clip}_{key}_voc", "Instrumental": f"{clip}_{key}_ins"})
    os.remove(wav)
    ins = os.path.join(STEMS, f"{clip}_{key}_ins.wav")
    if os.path.exists(ins):
        os.remove(ins)
    print(f"  stem {clip} {a:.1f}+{dur:.1f}s", flush=True)
    return out


def load(path, a=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error"]
    if a:
        cmd += ["-ss", f"{a:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)


def level(x, target_db=-18.0):
    """Loudness-normalise by the louder half of 400 ms blocks (ignores silence)."""
    mono = x.mean(axis=0)
    hop = int(0.4 * SR)
    if len(mono) < hop:
        return x
    blocks = np.array([np.sqrt(np.mean(mono[i:i + hop] ** 2)) for i in range(0, len(mono) - hop, hop)])
    ref = np.percentile(blocks, 70) + 1e-6
    g = 10 ** (target_db / 20) / ref
    return x * min(g, 30.0)


def fades(x, fin=0.06, fout=0.12):
    n = x.shape[1]
    e = np.ones(n)
    a, b = min(n, int(fin * SR)), min(n, int(fout * SR))
    if a:
        e[:a] = np.linspace(0, 1, a)
    if b:
        e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return x * e


def presence(x):
    """Bring voices / crowd forward: gentle high-pass + presence lift + soft compression."""
    b, a = signal.butter(2, 90 / (SR / 2), "high")
    y = signal.lfilter(b, a, x, axis=1)
    b2, a2 = signal.butter(2, [1800 / (SR / 2), 5000 / (SR / 2)], "band")
    y = y + 0.35 * signal.lfilter(b2, a2, y, axis=1)
    return np.tanh(y * 1.6) / 1.6 * 1.25


def render(shots, total, voice, out_wav):
    import soundfile as sf
    n = int((total + 1) * SR)
    live = np.zeros((2, n))
    fx = np.zeros((2, n))
    for sh in shots:
        for s in sh.segs:
            sp = s.spec
            g = sp.get("snd", 0.0)
            if s.kind != "clip" or g <= 0 or abs(s.speed - 1.0) > 0.02:
                continue
            src_dur = s.t1 - s.t0
            if sp.get("stem") == "voc":
                x = load(stem(sp["clip"], s.a, src_dur))
            else:
                x = load(clip_path(sp["clip"]), s.a, src_dur)
            x = fades(presence(level(x)))
            place(live, x, sh.start + s.t0, g)
        for item in sh.audio:
            clip, lt, a, dur, gain = item[:5]
            st = item[5] if len(item) > 5 else None
            x = load(stem(clip, a, dur)) if st == "voc" else load(clip_path(clip), a, dur)
            place(live, fades(presence(level(x)), 0.3, 0.6), sh.start + lt, gain)
        for t, name, gain in sh.events:
            tt = sh.start + (sh.resolve(t) if isinstance(t, str) else t)
            if name.startswith("riser"):
                ln = float(name.split(":")[1]) if ":" in name else 3.0
                place(fx, make_sfx(name), tt - ln, gain)
            elif name in ("impact", "boom", "heartbeat", "whistle", "crowd_roar"):
                length = 5.0 if name == "crowd_roar" else None
                place(fx, make_sfx(name, length), tt, gain)
    from .engine import transitions
    for c, kind in transitions(shots):
        x, off = transition_sfx(kind)
        if x is not None:
            place(fx, x, c - off, 0.6)
    print("  music cues", flush=True)
    mus = apply_cues(shots, total, n, np.zeros((2, n)))[:, :n]
    if mus.shape[1] < n:
        mus = np.pad(mus, ((0, 0), (0, n - mus.shape[1])))
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.5
    # duck music under the live layer (voices and roars stay on top)
    env = np.abs(live).mean(axis=0)
    win = int(0.08 * SR)
    env = signal.filtfilt(np.ones(win) / win, [1.0], env)
    rel = int(0.5 * SR)
    env = signal.filtfilt(np.ones(rel) / rel, [1.0], np.clip(env / 0.06, 0, 1))
    duck = 1 - 0.55 * np.clip(env, 0, 1)
    tt = np.arange(n) / SR
    mus *= np.clip((total + 0.2 - tt) / 4.0, 0, 1)
    mix = live * 1.0 + mus * duck + fx * 0.7
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / max(peak, 1e-9) * 1.8) / math.tanh(1.8) * 0.93
    sf.write(out_wav, mix.T.astype(np.float32), SR, subtype="PCM_24")
    print(f"  mix written: {out_wav}", flush=True)
    return out_wav
