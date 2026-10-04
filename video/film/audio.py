"""Sound: voice-over placement, an original synthesized score, sound design and real clip ambience."""
import math
import os
import subprocess

import numpy as np
from scipy import signal

from .engine import BUILD, clip_path

SR = 48000
BPM = 72.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(42)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, d, s, r, sr=SR):
    t = np.arange(n) / sr
    e = np.minimum(1.0, t / max(a, 1e-4))
    dec = s + (1 - s) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    e = np.where(t < a, e, dec)
    rel_start = n / sr - r
    e *= np.clip((n / sr - t) / max(r, 1e-4), 0, 1) if r > 0 else 1
    return e


# ------------------------------------------------------------------ instruments
def piano(f, dur, vel=0.6, bright=1.0):
    n = int((dur + 2.5) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    B = 0.00018
    for k in range(1, 11):
        fk = f * k * math.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        amp = (1 / k ** 1.25) * (bright ** (k - 1))
        decay = 0.55 + 0.42 * k + f / 900
        ph = rng.random() * 6.28
        out += amp * np.exp(-t * decay) * (np.sin(2 * np.pi * fk * t + ph) + 0.35 * np.sin(2 * np.pi * fk * 1.0009 * t + ph))
    att = np.minimum(1, t / 0.004)
    rel = np.clip((dur + 0.35 - t) / 0.35, 0, 1) * 0.85 + 0.15 * np.exp(-np.maximum(0, t - dur) * 3)
    hammer = rng.normal(0, 1, n) * np.exp(-t * 90) * 0.05
    return (out * att * rel + hammer) * vel * 0.32


def bell(f, dur=1.6, vel=0.5):
    n = int((dur + 0.5) * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4.5) \
        + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 8)
    return s * np.minimum(1, t / 0.002) * vel * 0.22


def saw_voice(f, n, k_max=14, detune=0.0025, vib=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0.0, detune):
        fv = f * (1 + d)
        phase = 2 * np.pi * fv * t
        if vib:
            phase += vib * fv / 5.0 * np.sin(2 * np.pi * 5.0 * t) * 2 * np.pi * 0.05
        kk = int(min(k_max, 9000 / fv))
        ph0 = rng.random() * 6.28
        for k in range(1, kk + 1):
            out += np.sin(k * (phase + ph0)) / (k ** 1.15)
    return out / 3


def pad(freqs, dur, vel=0.5, attack=1.6, release=2.2, k_max=10, vib=0.0):
    n = int((dur + release) * SR)
    s = sum(saw_voice(f, n, k_max, vib=vib) for f in freqs) / max(1, len(freqs))
    e = env_adsr(n, attack, 1.0, 0.9, release)
    return s * e * vel * 0.30


def bass(f, dur, vel=0.5):
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    return s * env_adsr(n, 0.02, 0.6, 0.7, 0.6) * vel * 0.35


def kick(vel=0.6):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * vel * 0.7


def hat(vel=0.3, length=0.05):
    n = int(length * SR)
    x = np.diff(rng.normal(0, 1, n + 1))
    return x * np.exp(-np.arange(n) / SR * (60 / length / 20)) * vel * 0.12


def swell(dur, vel=0.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.diff(rng.normal(0, 1, n + 1))
    b, a = signal.butter(2, [3000 / (SR / 2), 12000 / (SR / 2)], "band")
    x = signal.lfilter(b, a, x)
    return x * (t / dur) ** 2.5 * vel * 0.5


# ------------------------------------------------------------------ the score
N = {"D": 50, "E": 52, "F#": 54, "G": 43, "A": 45, "B": 47, "C": 48, "Bb": 46, "F": 41, "C#": 49}


def chord(root, quality, bass_note=None):
    r = N[root] if root in N else root
    third = 3 if quality in ("m", "m7") else 4
    tones = [r + 12, r + 12 + third, r + 19, r + 24]
    if quality in ("maj7",):
        tones.append(r + 23)
    if quality in ("add9", "m7"):
        tones.append(r + 26 if quality == "add9" else r + 22)
    return (N[bass_note] if bass_note else r), tones


MOODS = {
    "open":     dict(prog=[("D", "add9"), ("B", "m7"), ("G", "maj7"), ("A", "")], bars=2, arp="slow",
                     pad=0.55, piano=0.45, bassv=0.0),
    "child":    dict(prog=[("D", "add9"), ("A", "", "C#"), ("B", "m7"), ("G", "maj7")], bars=1, arp="eighths",
                     pad=0.4, piano=0.5, bells=True, bassv=0.35),
    "academy":  dict(prog=[("B", "m7"), ("G", "maj7"), ("D", "add9"), ("A", "")], bars=1, arp="eighths",
                     pad=0.42, piano=0.45, drums="steady", bassv=0.45),
    "tension":  dict(prog=[("B", "m7"), ("G", "maj7"), ("E", "m7"), ("F#", "")], bars=1, arp="sixteenths",
                     pad=0.45, piano=0.42, drums="drive", bassv=0.5, crescendo=True),
    "fall":     dict(prog=[("D", "m"), ("Bb", "maj7"), ("F", ""), ("C", "")], bars=2, arp="sparse",
                     pad=0.5, piano=0.4, dark=True, bassv=0.3, drone=True),
    "ordinary": dict(prog=[("B", "m7"), ("G", "maj7"), ("D", ""), ("A", "")], bars=1, arp="musicbox",
                     pad=0.32, piano=0.0, bells=True, bassv=0.25),
    "screen":   dict(prog=[("E", "m7"), ("C", "maj7"), ("G", "add9"), ("D", "")], bars=1, arp="eighths",
                     pad=0.45, piano=0.45, drums="build", bassv=0.5, crescendo=True),
    "love":     dict(prog=[("G", "maj7"), ("D", "", "F#"), ("E", "m7"), ("C", "maj7")], bars=1, arp="eighths",
                     pad=0.5, piano=0.5, strings=True, melody=True, bassv=0.4),
    "end":      dict(prog=[("D", "add9"), ("A", ""), ("B", "m7"), ("G", "maj7")], bars=2, arp="eighths",
                     pad=0.55, piano=0.5, strings=True, melody=True, bassv=0.45, drums="soft"),
}

MELODY = [74, 76, 78, 81, 78, 76, 74, 71, 73, 74, 76, 74]


def render_section(mood, dur, seed=0):
    m = MOODS[mood]
    n = int((dur + 4) * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    def add(x, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        x = x[: n - i] * gain
        L[i:i + len(x)] += x * math.cos((pan + 1) * math.pi / 4)
        R[i:i + len(x)] += x * math.sin((pan + 1) * math.pi / 4)

    chord_len = m["bars"] * BAR
    nchords = int(math.ceil(dur / chord_len)) + 1
    for ci in range(nchords):
        t0 = ci * chord_len
        if t0 > dur + 0.5:
            break
        spec = m["prog"][ci % len(m["prog"])]
        b, tones = chord(spec[0], spec[1], spec[2] if len(spec) > 2 else None)
        prog_t = t0 / max(dur, 1)
        inten = 0.6 + 0.6 * prog_t if m.get("crescendo") else 1.0
        if m["pad"]:
            freqs = [midi(x) for x in tones]
            kmax = 6 if m.get("dark") else 10
            add(pad(freqs, chord_len + 0.4, m["pad"] * inten, k_max=kmax, vib=1.0 if m.get("strings") else 0), t0,
                0.0)
        if m.get("strings"):
            add(pad([midi(x + 12) for x in tones[1:3]], chord_len + 0.3, 0.22 * inten, attack=1.2, k_max=14, vib=1),
                t0, 0.25)
        if m.get("bassv"):
            add(bass(midi(b), chord_len - 0.05, m["bassv"] * inten), t0, 0.0)
        if m.get("drone"):
            add(pad([midi(b - 12), midi(b - 5)], chord_len + 0.5, 0.35, attack=2.5, k_max=4), t0, 0)
        # arpeggios
        arp = m["arp"]
        pv = m["piano"]
        notes = tones + [tones[1] + 12, tones[2] + 12]
        if arp == "slow" and pv:
            for j in range(int(chord_len / BEAT)):
                nt = notes[(j * 2) % len(notes)]
                add(piano(midi(nt), BEAT * 1.6, pv * (0.8 + 0.2 * rng.random())), t0 + j * BEAT, (j % 3 - 1) * 0.4)
        elif arp == "eighths" and pv:
            pattern = [0, 2, 4, 3, 1, 2, 4, 5]
            for j in range(int(chord_len / (BEAT / 2))):
                nt = notes[pattern[j % len(pattern)] % len(notes)]
                acc = 1.0 if j % 4 == 0 else 0.75
                add(piano(midi(nt), BEAT * 0.9, pv * acc * inten * 0.8), t0 + j * BEAT / 2, (j % 4 - 1.5) * 0.25)
        elif arp == "sixteenths" and pv:
            pattern = [0, 2, 4, 2]
            for j in range(int(chord_len / (BEAT / 4))):
                nt = notes[pattern[j % 4] % len(notes)] + (12 if j % 8 >= 4 else 0)
                add(piano(midi(nt), BEAT * 0.5, pv * 0.55 * inten, bright=0.9), t0 + j * BEAT / 4, (j % 2 - 0.5) * 0.5)
        elif arp == "sparse" and pv:
            for j, beat in enumerate((0, 3, 5.5)):
                if t0 + beat * BEAT < dur:
                    nt = notes[[3, 2, 4][j]] + 12
                    add(piano(midi(nt), BEAT * 3, pv * 0.6, bright=0.7), t0 + beat * BEAT, 0.2 * (j - 1))
        elif arp == "musicbox":
            pattern = [0, 2, 4, 5, 4, 2, 3, 1]
            for j in range(8):
                nt = notes[pattern[j] % len(notes)] + 12
                add(bell(midi(nt), 1.0, 0.45), t0 + j * BEAT / 2, (j % 2 - 0.5) * 0.6)
        if m.get("bells") and arp != "musicbox":
            add(bell(midi(tones[-1] + 12), 1.4, 0.35), t0 + BEAT * 2, 0.5)
        if m.get("melody"):
            for j in range(2):
                nt = MELODY[(ci * 2 + j) % len(MELODY)]
                add(piano(midi(nt), BEAT * 1.8, 0.42, bright=1.05), t0 + j * BEAT * 2 + BEAT, -0.15)
        # drums
        d = m.get("drums")
        if d:
            beats = int(chord_len / BEAT)
            for j in range(beats):
                tb = t0 + j * BEAT
                if d in ("steady", "build", "drive", "soft") and j % 2 == 0:
                    add(kick(0.5 * inten if d != "soft" else 0.3), tb)
                if d in ("drive", "build"):
                    for h in range(2 if d == "build" else 4):
                        add(hat(0.4 * inten), tb + h * BEAT / (2 if d == "build" else 4), 0.3)
                elif d == "steady":
                    add(hat(0.35), tb + BEAT / 2, 0.3)
    return np.stack([L[: int(dur * SR) + 3 * SR], R[: int(dur * SR) + 3 * SR]])


def reverb_ir(seconds=2.6, damp=0.55):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        x = rng.normal(0, 1, n) * np.exp(-t / damp)
        b, a = signal.butter(1, 4500 / (SR / 2))
        x = signal.lfilter(b, a, x)
        x[: int(0.012 * SR)] = 0
        out.append(x / np.sqrt(np.sum(x ** 2)))
    return np.stack(out)


def add_reverb(x, wet=0.28, seconds=2.6):
    ir = reverb_ir(seconds)
    y = np.stack([signal.fftconvolve(x[c], ir[c])[: x.shape[1]] for c in range(2)])
    return x * (1 - wet * 0.5) + y * wet * 3.0


def music_track(moods, total, lifts):
    """moods: [(t, mood, fade_in)] sorted. Returns stereo array (2, n)."""
    n = int((total + 4) * SR)
    out = np.zeros((2, n))
    for i, (t0, mood, fin) in enumerate(moods):
        t1 = moods[i + 1][0] if i + 1 < len(moods) else total
        dur = max(1.0, t1 - t0)
        sec = render_section(mood, dur + 1.8)
        tt = np.arange(sec.shape[1]) / SR
        env = np.clip(tt / max(fin, 0.01), 0, 1)
        nxt_fin = moods[i + 1][2] if i + 1 < len(moods) else 3.0
        fade_len = max(0.15, min(2.0, nxt_fin))
        env *= np.clip((dur + fade_len * 0.5 - tt) / fade_len, 0, 1)
        sec *= env
        i0 = int(t0 * SR)
        m = min(sec.shape[1], n - i0)
        out[:, i0:i0 + m] += sec[:, :m]
    for t, dur, gain in lifts:
        s = swell(dur, gain)
        i0 = int((t - dur) * SR)
        if i0 >= 0:
            out[:, i0:i0 + len(s)] += s
    return add_reverb(out, 0.32)


# ------------------------------------------------------------------ sound design
def sfx(name, length=None):
    if name == "thud":
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        f = 38 + 60 * np.exp(-t * 18)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
        nz = rng.normal(0, 1, n) * np.exp(-t * 25)
        b, a = signal.butter(2, 400 / (SR / 2))
        x = x + signal.lfilter(b, a, nz) * 0.8
        x2 = np.roll(x, int(0.32 * SR)) * 0.45
        x2[: int(0.32 * SR)] = 0
        return np.stack([x + x2, x + x2]) * 0.9
    if name == "heartbeat":
        n = int(4.0 * SR)
        x = np.zeros(n)
        for k in range(4):
            for off, g in ((0.0, 1.0), (0.26, 0.7)):
                i = int((k * 0.95 + off) * SR)
                m = int(0.25 * SR)
                t = np.arange(m) / SR
                beat_ = np.sin(2 * np.pi * (42 + 30 * np.exp(-t * 20)) * t) * np.exp(-t * 16) * g
                x[i:i + m] += beat_[: n - i] * (1 - k * 0.18)
        return np.stack([x, x]) * 0.9
    if name == "tinnitus":
        n = int(6.0 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 6200 * t) * np.clip(t / 0.8, 0, 1) * np.clip((6 - t) / 3, 0, 1)
        return np.stack([x, x * 0.9]) * 0.05
    if name == "whoosh_soft":
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        x = rng.normal(0, 1, n)
        out = np.zeros(n)
        for i in range(0, n, 2400):
            fc = 300 + 2500 * (i / n)
            b, a = signal.butter(2, [fc / (SR / 2), min(0.99, fc * 2.2 / (SR / 2))], "band")
            out[i:i + 2400] = signal.lfilter(b, a, x[i:i + 2400])
        env = np.sin(np.pi * t / 1.2) ** 2
        return np.stack([out * env, out * env * 0.8]) * 0.35
    if name == "hit":
        n = int(2.5 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (34 + 25 * np.exp(-t * 10)) * t) * np.exp(-t * 1.6)
        nz = signal.lfilter(*signal.butter(2, 1200 / (SR / 2)), rng.normal(0, 1, n)) * np.exp(-t * 6) * 0.3
        return np.stack([x + nz, x + nz]) * 0.6
    if name == "hospital":
        n = int((length or 6) * SR)
        t = np.arange(n) / SR
        tone = signal.lfilter(*signal.butter(1, 300 / (SR / 2)), rng.normal(0, 1, n)) * 0.25
        tone += 0.05 * np.sin(2 * np.pi * 60 * t) + 0.03 * np.sin(2 * np.pi * 120 * t)
        beep = np.zeros(n)
        for k in np.arange(0.6, length or 6, 1.25):
            i = int(k * SR)
            m = int(0.14 * SR)
            beep[i:i + m] += np.sin(2 * np.pi * 980 * np.arange(m) / SR)[: n - i] * np.hanning(m)[: n - i]
        x = tone + beep * 0.06
        return np.stack([x, x * 0.95]) * 0.6
    if name == "clock":
        n = int((length or 10) * SR)
        x = np.zeros(n)
        for k in np.arange(0.2, length or 10, 1.0):
            i = int(k * SR)
            m = int(0.02 * SR)
            click = np.diff(rng.normal(0, 1, m + 1)) * np.exp(-np.arange(m) / SR * 300)
            click += np.sin(2 * np.pi * 2400 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 250) * 0.5
            x[i:i + m] += click[: n - i]
        return np.stack([x * 0.9, x]) * 0.5
    if name == "tv_on":
        n = int(1.0 * SR)
        t = np.arange(n) / SR
        x = np.diff(rng.normal(0, 1, n + 1)) * np.exp(-t * 9) * 0.4
        x[: int(0.01 * SR)] += 0.6
        return np.stack([x, x]) * 0.6
    if name == "crowd_roar":
        n = int((length or 6) * SR)
        t = np.arange(n) / SR
        chans = []
        for c in range(2):
            x = rng.normal(0, 1, n)
            b, a = signal.butter(2, [250 / (SR / 2), 2800 / (SR / 2)], "band")
            x = signal.lfilter(b, a, x)
            am = 1 + 0.25 * np.sin(2 * np.pi * 0.7 * t + c) + 0.15 * np.sin(2 * np.pi * 3.1 * t + 2 * c)
            env = np.clip(t / 0.6, 0, 1) ** 1.5 * np.clip((length or 6) - t, 0, 2.5) / 2.5
            chans.append(x * am * env)
        return np.stack(chans) * 0.35
    raise KeyError(name)


def load_voice(path):
    import soundfile as sf
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    g = math.gcd(sr, SR)
    return signal.resample_poly(x, SR // g, sr // g)


def clip_audio(name, a, dur):
    out = os.path.join(BUILD, "audio_cache", f"{name}_{a:.2f}_{dur:.2f}.f32")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(out):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", clip_path(name),
                        "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", out], check=True)
    x = np.fromfile(out, np.float32).reshape(-1, 2).T.astype(np.float64)
    m = x.shape[1]
    f = int(0.35 * SR)
    ramp = np.ones(m)
    ramp[:f] = np.linspace(0, 1, min(f, m))[: min(f, m)]
    ramp[-f:] = np.minimum(ramp[-f:], np.linspace(1, 0, min(f, m)))
    peak = np.max(np.abs(x)) + 1e-9
    return x * ramp / peak * 0.5


def place(bus, x, t, gain=1.0):
    i = int(t * SR)
    if i >= bus.shape[1] or i + x.shape[1] <= 0:
        return
    if i < 0:
        x = x[:, -i:]
        i = 0
    m = min(x.shape[1], bus.shape[1] - i)
    bus[:, i:i + m] += x[:, :m] * gain


def render(shots, total, voice, out_wav):
    n = int((total + 1) * SR)
    vo = np.zeros((2, n))
    fx = np.zeros((2, n))
    amb = np.zeros((2, n))
    for sh in shots:
        for lid, (a, b) in sh.cues.items():
            v = load_voice(voice[lid][0])
            v = v / (np.max(np.abs(v)) + 1e-9) * 0.7
            place(vo, np.stack([v, v]), sh.start + a)
        for ev in sh.events:
            t, name, gain = ev
            if name == "music_cut":
                continue
            length = sh.dur - t if name in ("hospital", "clock") else None
            place(fx, sfx(name, length), sh.start + t, gain)
        if sh.card:
            place(fx, sfx("hit"), sh.start + 0.2, 0.55)
        for clip, lt, a, dur, gain in sh.audio:
            place(amb, clip_audio(clip, a, dur), sh.start + lt, gain)
    # music plan
    moods = [(0.0, "open", 2.0)]
    lifts = []
    for sh in shots:
        mood = sh.spec.get("music")
        if mood:
            moods.append((sh.start + 0.2, mood, 1.2))
        for t, name, _ in sh.events:
            if name == "music_cut":
                moods.append((sh.start + t, "fall", 2.5))
            if name == "crowd_roar":
                lifts.append((sh.start + t, 2.5, 0.35))
        if sh.id == "open":
            lifts.append((sh.start + sh.resolve("open.end+0.6"), 2.2, 0.25))
    moods.sort()
    print(f"  score: {len(moods)} sections", flush=True)
    mus = music_track(moods, total, lifts)[:, :n]
    if mus.shape[1] < n:
        mus = np.pad(mus, ((0, 0), (0, n - mus.shape[1])))
    # duck music + ambience under the voice
    env = np.abs(vo[0])
    win = int(0.05 * SR)
    env = signal.filtfilt(np.ones(win) / win, [1.0], env)
    env = np.clip(env / 0.08, 0, 1)
    rel = int(0.6 * SR)
    env = np.clip(signal.filtfilt(np.ones(rel) / rel, [1.0], env) * 1.6, 0, 1)
    duck = 1 - 0.5 * np.clip(env * 1.4, 0, 1)
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.42
    # fade the score out at the very end
    tt = np.arange(n) / SR
    mus *= np.clip((total + 0.2 - tt) / 6.0, 0, 1)
    mix = vo + mus * duck + fx * 0.8 + amb * (0.4 + 0.6 * duck)
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / max(peak, 1e-9) * 1.35) / math.tanh(1.35) * 0.93
    import soundfile as sf
    sf.write(out_wav, mix.T.astype(np.float32), SR, subtype="PCM_24")
    print(f"  mix written: {out_wav}", flush=True)
    return out_wav
