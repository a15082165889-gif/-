"""热血配乐与音效：太鼓、弦乐快弓 ostinato、铜管、braam、上升音、冲击音。按章节/事件切换情绪。"""
import math
from functools import lru_cache

import numpy as np
from scipy import signal

from .audio import (SR, add_reverb, bass, clip_audio, env_adsr, load_voice, pad, piano, place, saw_voice, sfx,
                    swell)

rng = np.random.default_rng(7)
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10,
        "B": 11}


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def triad(name):
    minor = name.endswith("m")
    root = NOTE[name[:-1] if minor else name]
    r = 36 + root  # C2-based bass octave
    return r, [r + 12, r + 12 + (3 if minor else 4), r + 19, r + 24]


# ------------------------------------------------------------------ instruments (cached waveforms)
@lru_cache(maxsize=8)
def taiko(pitch=1.0):
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = (62 + 70 * np.exp(-t * 22)) * pitch
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    skin = signal.lfilter(*signal.butter(2, 900 / (SR / 2)), rng.normal(0, 1, n)) * np.exp(-t * 30) * 0.9
    room = signal.lfilter(*signal.butter(1, 300 / (SR / 2)), rng.normal(0, 1, n)) * np.exp(-t * 5) * 0.25
    x = np.tanh((body + skin + room) * 1.6)
    return x * 0.8


@lru_cache(maxsize=2)
def snare():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    nz = signal.lfilter(*signal.butter(2, [1200 / (SR / 2), 9000 / (SR / 2)], "band"), rng.normal(0, 1, n))
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 25)
    return (nz * np.exp(-t * 11) * 0.7 + body * 0.6) * 0.6


@lru_cache(maxsize=64)
def string_note(m, length=0.16):
    n = int((length + 0.12) * SR)
    x = saw_voice(midi(m), n, k_max=12, detune=0.004)
    e = env_adsr(n, 0.006, 0.08, 0.55, 0.12)
    return signal.lfilter(*signal.butter(2, 5200 / (SR / 2)), x * e) * 0.32


@lru_cache(maxsize=32)
def brass(notes, length):
    n = int((length + 0.6) * SR)
    t = np.arange(n) / SR
    lo = sum(saw_voice(midi(m), n, k_max=4, detune=0.003) for m in notes)
    hi = sum(saw_voice(midi(m), n, k_max=16, detune=0.003) for m in notes)
    bright = np.clip(t / 0.18, 0, 1) * np.exp(-t * 0.6) * 0.8 + 0.2
    x = lo * (1 - bright) + hi * bright
    e = env_adsr(n, 0.05, 0.6, 0.75, 0.45)
    return np.tanh(x * e / len(notes) * 1.4) * 0.35


@lru_cache(maxsize=8)
def braam(root):
    n = int(4.5 * SR)
    t = np.arange(n) / SR
    notes = [root - 12, root, root + 7, root + 12]
    x = sum(saw_voice(midi(m) * (1 - 0.01 * np.exp(-t * 3)).mean(), n, k_max=10, detune=0.006) for m in notes)
    x = np.tanh(x * 0.9)
    e = env_adsr(n, 0.04, 1.6, 0.35, 1.8)
    return signal.lfilter(*signal.butter(2, 2400 / (SR / 2)), x * e) * 0.55


def riser(length=3.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    x = rng.normal(0, 1, n)
    step = 2400
    for i in range(0, n, step):
        fc = 300 * (1 + 25 * (i / n) ** 2)
        b, a = signal.butter(2, [fc / (SR / 2), min(0.98, fc * 1.8 / (SR / 2))], "band")
        out[i:i + step] = signal.lfilter(b, a, x[i:i + step])
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (3 * t / length)) / SR) * 0.15
    e = (t / length) ** 2.2
    return (out * 0.9 + tone) * e * 0.8


def impact():
    n = int(3.5 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-t * 9)) / SR) * np.exp(-t * 1.4)
    crack = signal.lfilter(*signal.butter(2, 3000 / (SR / 2), "high"), rng.normal(0, 1, n)) * np.exp(-t * 8) * 0.5
    x = np.tanh((boom * 1.4 + crack + np.pad(taiko(0.8), (0, n - len(taiko(0.8))))) * 1.2)
    return x * 0.75


def whistle():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 2900 + 120 * np.sin(2 * np.pi * 32 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * (np.sin(2 * np.pi * 32 * t) > 0))
    e = np.clip(t / 0.02, 0, 1) * np.clip((0.85 - t) / 0.1, 0, 1)
    return x * e * 0.25


def tick_track(length, bpm=120):
    n = int(length * SR)
    x = np.zeros(n)
    beat = 60 / bpm
    for k in np.arange(0, length, beat / 2):
        i = int(k * SR)
        m = int(0.03 * SR)
        click = signal.lfilter(*signal.butter(2, 5000 / (SR / 2), "high"), rng.normal(0, 1, m)) * np.exp(
            -np.arange(m) / SR * 200)
        x[i:i + m] += click[: n - i] * (1.0 if (k / (beat / 2)) % 2 < 1 else 0.6)
    return x * 0.35


# ------------------------------------------------------------------ moods
MOODS = {
    "build":   dict(bpm=120, prog=["Dm", "Bb", "F", "C"], ost=8, ost16_after=0.5, taiko="build", pad=0.5,
                    cresc=True),
    "drive":   dict(bpm=126, prog=["Dm", "Bb", "F", "C"], ost=16, taiko="drive", snare=True, pad=0.5,
                    brass="stabs"),
    "hope":    dict(bpm=120, prog=["Bb", "F", "Dm", "C"], ost=8, taiko="light", pad=0.55, piano=True),
    "heroic":  dict(bpm=128, prog=["D", "A", "Bm", "G"], ost=16, taiko="drive", snare=True, pad=0.6,
                    brass="long", melody=True),
    "sad":     dict(bpm=70, prog=["Dm", "Bb", "Gm", "A"], pad=0.5, piano="sparse", bars=2),
    "dark":    dict(bpm=90, prog=["Dm", "Eb", "Dm", "C"], ost=4, taiko="sparse", pad=0.45, braam=True, bars=2),
    "tension": dict(bpm=120, prog=["Dm", "Dm", "Eb", "Eb"], ost=16, taiko="heart", pad=0.35, cresc=True,
                    ticks=True),
    "anthem":  dict(bpm=128, prog=["D", "A", "Bm", "G"], ost=16, taiko="drive", snare=True, pad=0.7,
                    brass="long", melody=True, big=True),
    "outro":   dict(bpm=76, prog=["D", "A", "Bm", "G"], pad=0.6, piano="arp", melody=True, bars=2),
}
MELODY = [74, 76, 78, 81, 78, 76, 74, 71, 73, 74, 76, 81, 79, 78, 76, 74]


def render_section(mood, dur):
    m = MOODS[mood]
    beat = 60 / m["bpm"]
    bar = 4 * beat
    clen = bar * m.get("bars", 1)
    n = int((dur + 4) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(x, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        x = x[: n - i] * gain
        L[i:i + len(x)] += x * math.cos((pan + 1) * math.pi / 4)
        R[i:i + len(x)] += x * math.sin((pan + 1) * math.pi / 4)

    nch = int(math.ceil(dur / clen)) + 1
    for ci in range(nch):
        t0 = ci * clen
        if t0 > dur:
            break
        u = t0 / max(dur, 1e-3)
        inten = (0.55 + 0.6 * u) if m.get("cresc") else 1.0
        if m.get("big"):
            inten *= 1.15
        b, tones = triad(m["prog"][ci % len(m["prog"])])
        if m.get("pad"):
            add(pad([midi(x) for x in tones], clen + 0.4, m["pad"] * inten, attack=0.5, k_max=9, vib=1.0), t0)
            add(pad([midi(x + 12) for x in tones[1:3]], clen + 0.3, 0.22 * inten, attack=0.6, k_max=12, vib=1),
                t0, 0.3)
        add(bass(midi(b), clen - 0.05, 0.55 * inten), t0)
        # ostinato
        ost = m.get("ost")
        if ost:
            step = bar / ost
            pat = [0, 0, 2, 0, 1, 0, 2, 3] if ost >= 8 else [0, 2, 1, 2]
            for j in range(int(clen / step)):
                o = ost
                if m.get("ost16_after") is not None and u < m["ost16_after"]:
                    o = 8
                    if j % 2:
                        continue
                nt = tones[pat[j % len(pat)]] + 12
                add(string_note(nt, 0.14 if o >= 16 else 0.22), t0 + j * step, (j % 2 - 0.5) * 0.4,
                    0.55 * inten * (1.0 if j % 4 == 0 else 0.75))
        # drums
        tk = m.get("taiko")
        beats = int(clen / beat)
        for j in range(beats):
            tb = t0 + j * beat
            if tk == "drive":
                add(taiko(1.0), tb, -0.1, 0.9 * inten if j % 2 == 0 else 0.55 * inten)
                if j % 4 == 3:
                    add(taiko(1.25), tb + beat / 2, 0.2, 0.6 * inten)
                    add(taiko(1.4), tb + beat * 0.75, -0.2, 0.5 * inten)
            elif tk == "build":
                if j % 2 == 0 or u > 0.5:
                    add(taiko(1.0), tb, 0, 0.75 * inten)
                if u > 0.75:
                    add(taiko(1.3), tb + beat / 2, 0.2, 0.5 * inten)
            elif tk == "light" and j % 2 == 0:
                add(taiko(1.1), tb, 0, 0.5)
            elif tk == "sparse" and j % 4 == 0:
                add(taiko(0.8), tb, 0, 0.8)
            elif tk == "heart" and j % 2 == 0:
                add(taiko(0.9), tb, 0, 0.55 * inten)
                add(taiko(0.9), tb + 0.26, 0, 0.38 * inten)
            if m.get("snare") and j % 2 == 1:
                add(snare(), tb, 0.15, 0.55 * inten)
        if m.get("brass") == "stabs":
            add(brass(tuple(tones[:3]), beat * 0.9), t0, 0, 0.7 * inten)
            add(brass(tuple(tones[:3]), beat * 0.4), t0 + beat * 2.5, 0, 0.5 * inten)
        elif m.get("brass") == "long":
            add(brass(tuple(tones[:3]), clen * 0.95), t0, 0, 0.75 * inten)
        if m.get("braam"):
            add(braam(b + 12), t0, 0, 0.9)
        if m.get("piano") == "sparse":
            for k_, bt in enumerate((0, 3, 5.5)):
                add(piano(midi(tones[[3, 2, 1][k_]] + 12), beat * 3, 0.5, bright=0.7), t0 + bt * beat, 0.2)
        elif m.get("piano") == "arp" or m.get("piano") is True:
            for j in range(int(clen / (beat / 2))):
                nt = (tones + [tones[1] + 12])[[0, 2, 4, 1, 3, 2, 4, 1][j % 8]]
                add(piano(midi(nt + 12), beat, 0.4), t0 + j * beat / 2, (j % 3 - 1) * 0.3)
        if m.get("melody"):
            for j in range(2):
                nt = MELODY[(ci * 2 + j) % len(MELODY)]
                note = pad([midi(nt)], beat * 1.9, 0.5 * inten, attack=0.08, release=0.6, k_max=14, vib=1.5)
                add(note, t0 + j * beat * 2, -0.1)
        if m.get("ticks") and ci == 0:
            add(tick_track(dur, m["bpm"]), 0, 0.3, 0.6)
    k = int((dur + 3) * SR)
    return np.stack([L[:k], R[:k]])


def music_track(plan, total):
    n = int((total + 4) * SR)
    out = np.zeros((2, n))
    for i, (t0, mood, fin) in enumerate(plan):
        t1 = plan[i + 1][0] if i + 1 < len(plan) else total
        dur = max(0.5, t1 - t0)
        if mood == "none":
            continue
        sec = render_section(mood, dur + 1.5)
        tt = np.arange(sec.shape[1]) / SR
        e = np.clip(tt / max(fin, 0.01), 0, 1)
        nxt = plan[i + 1] if i + 1 < len(plan) else None
        fade = 0.12 if (nxt and nxt[1] == "none") else max(0.15, min(1.5, nxt[2] if nxt else 3.0))
        e *= np.clip((dur + fade * 0.5 - tt) / fade, 0, 1)
        sec *= e
        i0 = int(t0 * SR)
        mlen = min(sec.shape[1], n - i0)
        out[:, i0:i0 + mlen] += sec[:, :mlen]
    return add_reverb(out, 0.22, 2.0)


# ------------------------------------------------------------------ mix
CHANT_VOICES = ["zm_yunjian", "zm_yunxi", "zm_yunyang", "zm_yunxia", "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao",
                "zf_xiaoyi"]


def _chant_words():
    """Synthesize '中国队' and '加油' with many voices (cached)."""
    import os

    import soundfile as sf

    from .engine import BUILD
    d = os.path.join(BUILD, "chant")
    os.makedirs(d, exist_ok=True)
    out = {}
    kok = g2p = None
    for word, key in (("中国队！", "zgd"), ("加油！", "jy")):
        for v in CHANT_VOICES:
            p = os.path.join(d, f"{key}_{v}.wav")
            if not os.path.exists(p):
                if kok is None:
                    from kokoro_onnx import Kokoro
                    from misaki import zh
                    from .gfx import ROOT
                    kok = Kokoro(os.path.join(ROOT, ".models", "kokoro.onnx"), os.path.join(ROOT, ".models", "voices.bin"))
                    g2p = zh.ZHG2P()
                ph, _ = g2p(word)
                x, sr = kok.create(ph, voice=v, speed=1.25, is_phonemes=True)
                sf.write(p, x, sr)
            out.setdefault(key, []).append(load_voice(p))
    return out


def clap():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(14):  # many hands
        off = int(abs(rng.normal(0, 0.012)) * SR)
        nz = signal.lfilter(*signal.butter(2, [900 / (SR / 2), 5000 / (SR / 2)], "band"), rng.normal(0, 1, n))
        out[off:] += (nz * np.exp(-t * 45))[: n - off]
    return out / 14 * 1.6


def chant_track(cycles=3, cycle=4.0, claps=(2.0, 2.5, 3.0, 3.25, 3.5)):
    words = _chant_words()
    n = int((cycles * cycle + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def put(x, t, pan, g):
        i = int(t * SR)
        if i < 0 or i >= n:
            return
        x = x[: n - i] * g
        L[i:i + len(x)] += x * math.cos((pan + 1) * math.pi / 4)
        R[i:i + len(x)] += x * math.sin((pan + 1) * math.pi / 4)

    for c in range(cycles):
        t0 = c * cycle
        loud = 0.6 + 0.25 * c
        reps = 2 + c  # more people each round
        for key, at in (("zgd", 0.0), ("jy", 1.0)):
            for r in range(reps):
                for v in words[key]:
                    rate = 1 + rng.normal(0, 0.035)
                    vv = signal.resample(v, int(len(v) / rate))
                    vv = vv / (np.max(np.abs(vv)) + 1e-9)
                    put(vv, t0 + at + rng.normal(0, 0.03) + 0.02 * r, rng.uniform(-0.9, 0.9), 0.18 * loud)
        for ct in claps:
            put(clap(), t0 + ct, rng.uniform(-0.3, 0.3), 0.9 * loud)
            put(taiko(1.0), t0 + ct, 0, 0.55 * loud)
        put(taiko(0.85), t0, 0, 0.8 * loud)
        put(taiko(0.85), t0 + 1.0, 0, 0.8 * loud)
    x = np.stack([L, R])
    bed = sfx("crowd_roar", cycles * cycle + 2.5) * 0.9
    x[:, : bed.shape[1]] += bed[:, : x.shape[1]]
    return add_reverb(x, 0.35, 2.2)


def whoosh(length=0.6, peak=0.4, lo=300, hi=6000, gain=0.7):
    """Air whoosh whose loudest point is at `peak` seconds."""
    n = int(length * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    step = 1200
    for i in range(0, n, step):
        u = clamp01(1 - abs(i / SR - peak) / max(peak, length - peak))
        fc = lo + (hi - lo) * u ** 1.5
        b, a = signal.butter(2, [fc / (SR / 2) * 0.6, min(0.98, fc / (SR / 2) * 1.4)], "band")
        out[i:i + step] = signal.lfilter(b, a, x[i:i + step])
    env_ = np.where(t < peak, (t / peak) ** 2.5, np.exp(-(t - peak) * 9))
    return out * env_ * gain


def clamp01(v):
    return max(0.0, min(1.0, v))


def transition_sfx(kind):
    """Returns (stereo, offset): offset = seconds before the cut where the sound starts."""
    if kind in ("whip", "whip_v"):
        w = whoosh(0.5, 0.22, 600, 8000, 0.8)
        L = np.concatenate([w, np.zeros(2000)])
        R = np.concatenate([np.zeros(2000), w])
        return np.stack([L, R]), 0.22
    if kind in ("zoom", "spin"):
        w = whoosh(0.8, 0.3, 200, 5000, 0.8)
        hit = np.pad(taiko(1.2) * 0.5, (int(0.3 * SR), 0))[: len(w)]
        x = w + hit
        return np.stack([x, x]), 0.3
    if kind == "glitch":
        n = int(0.4 * SR)
        x = np.zeros(n)
        for k in range(10):
            i = int(rng.uniform(0, 0.32) * SR)
            m = int(rng.uniform(0.01, 0.04) * SR)
            f = rng.uniform(300, 3000)
            x[i:i + m] += np.sign(np.sin(2 * np.pi * f * np.arange(m) / SR)) * 0.25
        x += rng.normal(0, 1, n) * 0.08 * np.exp(-np.arange(n) / SR * 6)
        return np.stack([x, x]), 0.2
    if kind == "burn":
        w = whoosh(1.0, 0.3, 150, 3000, 0.6)
        b = impact()[: len(w) + int(0.3 * SR)] * 0.5
        x = np.zeros(max(len(w), len(b)))
        x[: len(w)] += w
        x[int(0.3 * SR): int(0.3 * SR) + len(b) - int(0.3 * SR)] += b[: len(b) - int(0.3 * SR)]
        return np.stack([x, x]), 0.3
    return None, 0


def make_sfx(name, length=None):
    if name == "chant":
        return chant_track()
    if name == "impact":
        x = impact()
    elif name == "boom":
        x = impact() * 0.6
    elif name.startswith("riser"):
        x = riser(float(name.split(":")[1]) if ":" in name else 3.0)
    elif name == "whistle":
        x = whistle()
    elif name == "taiko":
        x = taiko(1.0)
    else:
        return sfx(name, length)
    return np.stack([x, x])


def find_song():
    import glob
    import os

    from .gfx import ROOT
    for ext in ("mp3", "m4a", "flac", "wav", "aac", "ogg"):
        hits = sorted(glob.glob(os.path.join(ROOT, "music", f"*.{ext}")))
        if hits:
            return hits[0]
    return None


def load_song(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)


def song_climax(x, window=14.0):
    """Start time of the loudest sustained passage (usually the last big chorus)."""
    mono = np.abs(x).mean(axis=0)
    hop = int(0.5 * SR)
    e = np.array([np.sqrt(np.mean(mono[i:i + hop] ** 2)) for i in range(0, len(mono) - hop, hop)])
    w = int(window / 0.5)
    if len(e) <= w:
        return 0.0
    sm = np.convolve(e, np.ones(w) / w, mode="valid")
    # prefer choruses in the second half of the song, and the start of that loud plateau
    sc = sm * np.linspace(0.92, 1.0, len(sm))
    best = int(np.argmax(sc))
    i = best
    while i > 0 and sc[i - 1] >= 0.97 * sc[best]:
        i -= 1
    return float(i * 0.5)


def song_bus(plan, total, n, climax_film, synth):
    """Arrange the user's song so its climax lands on the film's climax; synth score fills any gaps."""
    path = find_song()
    x = load_song(path)
    x = x / (np.max(np.abs(x)) + 1e-9)
    cs = song_climax(x)
    start = climax_film - cs  # film time where song time 0 lands
    print(f"  song: {path} (climax {cs:.1f}s -> film {climax_film:.1f}s, song starts at film {start:.1f}s)",
          flush=True)
    bus = np.zeros((2, n))
    a = max(0, int(start * SR))
    b = max(0, int(-start * SR))
    m = min(n - a, x.shape[1] - b)
    bus[:, a:a + m] = x[:, b:b + m]
    t = np.arange(n) / SR
    song_on = np.zeros(n)
    song_on[a:a + m] = 1.0
    fade = int(1.5 * SR)
    if a > 0:
        song_on[a:a + fade] = np.linspace(0, 1, min(fade, m))
    end = a + m
    if end < n:
        song_on[max(a, end - fade):end] = np.linspace(1, 0, end - max(a, end - fade))
    # gain automation from the mood plan: dip the song in silent / sombre / chant passages
    gain = np.ones(n)
    for i, (t0, mood, _f) in enumerate(plan):
        t1 = plan[i + 1][0] if i + 1 < len(plan) else total
        g = {"none": 0.12, "sad": 0.45, "dark": 0.7}.get(mood, 1.0)
        i0, i1 = int(t0 * SR), min(n, int(t1 * SR))
        gain[i0:i1] = g
    k = int(0.6 * SR)
    gain = np.convolve(gain, np.ones(k) / k, mode="same")
    synth_n = synth / (np.max(np.abs(synth)) + 1e-9)
    return bus * song_on * gain + synth_n * (1 - song_on) * 0.8


def render(shots, total, voice, out_wav):
    import soundfile as sf
    n = int((total + 1) * SR)
    vo, fx, amb = np.zeros((2, n)), np.zeros((2, n)), np.zeros((2, n))
    plan = [(0.0, "build", 0.5)]
    for sh in shots:
        for lid, (a, b) in sh.cues.items():
            v = load_voice(voice[lid][0])
            v = v / (np.max(np.abs(v)) + 1e-9) * 0.75
            place(vo, np.stack([v, v]), sh.start + a)
        if sh.spec.get("music"):
            plan.append((sh.start + sh.spec.get("music_at", 0.0), sh.spec["music"], sh.spec.get("music_fade", 0.3)))
        for ev in sh.events:
            t, name, gain = ev
            tt = sh.start + (sh.resolve(t) if isinstance(t, str) else t)
            if name.startswith("mood:"):
                plan.append((tt, name[5:], 0.25))
                continue
            if name.startswith("riser"):
                ln = float(name.split(":")[1]) if ":" in name else 3.0
                place(fx, make_sfx(name), tt - ln, gain)
                continue
            if name == "shake":
                continue
            length = sh.dur - (tt - sh.start) if name in ("hospital", "clock", "crowd_roar") else None
            place(fx, make_sfx(name, length), tt, gain)
        for clip, lt, a, dur, gain in sh.audio:
            place(amb, clip_audio(clip, a, dur), sh.start + lt, gain)
    from .engine import transitions
    for c, kind in transitions(shots):
        x, off = transition_sfx(kind)
        if x is not None:
            place(fx, x, c - off, 0.75)
    plan.sort()
    print(f"  score: {len(plan)} sections", flush=True)
    mus = music_track(plan, total)[:, :n]
    if mus.shape[1] < n:
        mus = np.pad(mus, ((0, 0), (0, n - mus.shape[1])))
    if find_song():
        climax = next((sh.start + sh.resolve("g5.end-0.9") for sh in shots if "g5" in sh.cues), total * 0.7)
        mus = song_bus(plan, total, n, climax, mus)
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.55
    env = np.abs(vo[0])
    win = int(0.05 * SR)
    env = signal.filtfilt(np.ones(win) / win, [1.0], env)
    rel = int(0.5 * SR)
    env = np.clip(signal.filtfilt(np.ones(rel) / rel, [1.0], np.clip(env / 0.08, 0, 1)) * 1.6, 0, 1)
    duck = 1 - 0.42 * env
    tt = np.arange(n) / SR
    mus *= np.clip((total + 0.3 - tt) / 5.0, 0, 1)
    mix = vo * 1.05 + mus * duck + fx * 0.75 + amb * (0.45 + 0.55 * duck)
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / max(peak, 1e-9) * 1.6) / math.tanh(1.6) * 0.93
    sf.write(out_wav, mix.T.astype(np.float32), SR, subtype="PCM_24")
    print(f"  mix written: {out_wav}", flush=True)
    return out_wav
