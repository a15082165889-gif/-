"""Timeline, footage preparation and frame rendering."""
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import tarfile
import urllib.request

import cairo
import numpy as np

from . import graphics as gx
from .edit import DEFAULTS, SHOTS
from .gfx import FPS, H, ROOT, W, clamp, ease_in_out, grade, lerp, merge_look, remap, smooth, text, wrap
from .story import NARRATION

FOOTAGE = os.path.join(ROOT, ".footage")
BUILD = os.path.join(ROOT, "build")
CLIPS = json.load(open(os.path.join(ROOT, "film", "clips.json")))
K700 = "https://s3.amazonaws.com/kinetics/700_2020"


# ------------------------------------------------------------------ footage
def clip_path(name):
    c = CLIPS[name]
    return os.path.join(FOOTAGE, c["cls"], c["file"])


def ensure_footage():
    """Download the Kinetics-700 validation archives that hold the clips the edit uses."""
    missing = {}
    for name, c in CLIPS.items():
        if not os.path.exists(clip_path(name)):
            missing.setdefault(c["cls"], []).append(c["file"])
    if not missing:
        return
    os.makedirs(FOOTAGE, exist_ok=True)
    ann = os.path.join(FOOTAGE, "val.csv")
    if not os.path.exists(ann):
        urllib.request.urlretrieve(f"{K700}/annotations/val.csv", ann)
    labels = sorted({r["label"] for r in csv.DictReader(open(ann))})
    for cls, files in missing.items():
        url = f"{K700}/val/k700_val_{labels.index(cls) + 1:03d}.tar.gz"
        print(f"  fetching {cls} ({len(files)} clips) from {url}", flush=True)
        data = urllib.request.urlopen(url).read()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            for f in files:
                tf.extract(f"{cls}/{f}", FOOTAGE)


# ------------------------------------------------------------------ timeline
class Seg:
    pass


class Shot:
    def __init__(self, idx, spec, voice):
        o = dict(DEFAULTS)
        o.update(spec)
        self.idx, self.spec, self.id = idx, spec, spec["id"]
        self.lines = spec.get("lines", [])
        self.cues = {}
        t = o["lead"]
        for lid in self.lines:
            d = voice[lid][1]
            self.cues[lid] = (t, t + d)
            t += d + o["gap"]
        end = t - o["gap"] + o["tail"] if self.lines else 0.0
        self.dur = max(o["min"], end)
        self.xf = o["xf"]
        self.look = spec.get("look")
        self.card = spec.get("card")
        self.overlays = [(k, self.resolve(a), self.resolve(b), p) for k, a, b, p in spec.get("overlays", [])]
        self.events = spec.get("events", [])
        self.audio = spec.get("audio", [])
        self.segs = self._layout(spec.get("segs", []))

    def resolve(self, e):
        if isinstance(e, (int, float)):
            return float(e)
        m = re.match(r"^([a-z0-9_]+)(\.end)?([+-][0-9.]+)?$", e)
        base, is_end, off = m.group(1), m.group(2), float(m.group(3) or 0)
        if base == "end":
            v = self.dur
        else:
            v = self.cues[base][1 if is_end else 0]
        return v + off

    def _layout(self, specs):
        segs = []
        for sp in specs:
            s = Seg()
            s.spec = sp
            s.kind = sp["kind"]
            s.x = sp.get("x", 0.0)
            s.speed = sp.get("speed", 1.0)
            if s.kind == "clip":
                s.a = sp["a"]
                if sp.get("freeze"):
                    s.dur = sp["freeze"]
                elif sp.get("fill"):
                    s.dur = None
                else:
                    s.dur = (sp["b"] - sp["a"]) / s.speed
            elif s.kind in ("black", "photo"):
                s.dur = sp["dur"]
            elif s.kind == "map":
                s.dur = None
            segs.append(s)
        fixed = sum(s.dur for s in segs if s.dur is not None) - sum(s.x for s in segs[:-1])
        for s in segs:
            if s.dur is None:
                s.dur = max(0.5, self.dur - fixed)
                if s.kind == "clip":
                    avail = CLIPS[s.spec["clip"]]["dur"] - s.a - 0.12
                    if s.dur * s.speed > avail:
                        s.speed = avail / s.dur
        for s in segs:
            scr = s.spec.get("screen")
            if scr:
                sub = Seg()
                sub.kind, sub.x = "clip", 0.0
                sub.spec = dict(kind="clip", clip=scr["clip"], a=scr["a"])
                sub.a, sub.dur = scr["a"], s.dur
                sub.speed = min(scr.get("speed", 1.0), (CLIPS[scr["clip"]]["dur"] - scr["a"] - 0.12) / s.dur)
                s.screen = sub
        t = 0.0
        for i, s in enumerate(segs):
            s.t0 = t
            s.t1 = t + s.dur
            t = s.t1 - s.x
        if segs and segs[-1].t1 < self.dur:
            segs[-1].t1 = self.dur + 0.01
            segs[-1].dur = segs[-1].t1 - segs[-1].t0
        return segs


def build_timeline(voice):
    shots = [Shot(i, sp, voice) for i, sp in enumerate(SHOTS)]
    t = 0.0
    for s in shots:
        s.start = t
        t += s.dur - s.xf
    total = shots[-1].start + shots[-1].dur
    return shots, total


# ------------------------------------------------------------------ segment preparation (ffmpeg)
def seg_key(s):
    sp = s.spec
    key = json.dumps([sp["clip"], round(s.a, 3), round(s.dur, 3), round(s.speed, 4), sp.get("fit", "cover"),
                      sp.get("fit_x", 0.5), sp.get("freeze", 0), 2], sort_keys=True)
    return hashlib.sha1(key.encode()).hexdigest()[:14]


def prepare_segment(s):
    """Transcode a clip segment to 1920x1080 @ FPS (speed-adjusted). Returns the cache path."""
    os.makedirs(os.path.join(BUILD, "seg"), exist_ok=True)
    out = os.path.join(BUILD, "seg", seg_key(s) + (".png" if s.spec.get("freeze") else ".mp4"))
    s.path = out
    if os.path.exists(out):
        return out
    src = clip_path(s.spec["clip"])
    info = CLIPS[s.spec["clip"]]
    lowres = info["h"] <= 480
    pre = "hqdn3d=2:2:4:4," if lowres else ""
    sharpen = ",unsharp=5:5:0.7:5:5:0.0" if lowres else ""
    if s.spec.get("fit") == "contain":
        vf = (f"{pre}split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=30:3,eq=brightness=-0.12:saturation=0.8[bg];"
              f"[b]scale=-2:{H}:flags=lanczos{sharpen}[fg];[bg][fg]overlay=(W-w)*{s.spec.get('fit_x', 0.5)}:0")
    else:
        vf = f"{pre}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}{sharpen}"
    if s.spec.get("freeze"):
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{s.a:.3f}", "-i", src, "-frames:v", "1",
               "-filter_complex" if "split" in vf else "-vf", vf, out]
    else:
        need = s.dur * s.speed + 0.25
        timing = f"setpts=(PTS-STARTPTS)/{s.speed:.5f}"
        if s.speed < 0.95:  # motion-compensated slow motion, computed at source resolution
            timing += f",minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
        else:
            timing += f",fps={FPS}"
        full = f"{timing},{vf}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{s.a:.3f}", "-t", f"{need:.3f}", "-i", src, "-an",
               "-filter_complex", full, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "12", "-g", "15", out]
    subprocess.run(cmd, check=True)
    return out


def prepare_all(shots, jobs=4):
    from concurrent.futures import ThreadPoolExecutor
    segs = [s for sh in shots for s in sh.segs if s.kind == "clip"]
    segs += [s.screen for s in segs if getattr(s, "screen", None)]
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(prepare_segment, segs))
    for sh in shots:
        for s in sh.segs:
            if s.kind == "photo":
                p = os.path.join(BUILD, "seg", f"still_{s.spec['clip']}_{s.spec['at']}.png")
                if not os.path.exists(p):
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s.spec["at"]), "-i",
                                    clip_path(s.spec["clip"]), "-frames:v", "1", p], check=True)
                s.path = p


# ------------------------------------------------------------------ frame readers
class Reader:
    def __init__(self, path):
        self.path = path
        self.proc = None
        self.pos = -1
        self.frame = None
        self.still = path.endswith(".png")
        if self.still:
            from PIL import Image
            im = Image.open(path).convert("RGB").resize((W, H))
            a = np.asarray(im)
            self.frame = np.empty((H, W, 4), np.uint8)
            self.frame[..., 0] = a[..., 2]
            self.frame[..., 1] = a[..., 1]
            self.frame[..., 2] = a[..., 0]
            self.frame[..., 3] = 255

    def _open(self, idx):
        self.close()
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{idx / FPS:.4f}", "-i", self.path,
                                      "-f", "rawvideo", "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE,
                                     bufsize=W * H * 4 * 2)
        self.pos = idx - 1

    def get(self, idx):
        if self.still:
            return self.frame
        idx = max(0, idx)
        if self.proc is None or idx < self.pos or idx > self.pos + 45:
            self._open(idx)
        while self.pos < idx:
            buf = self.proc.stdout.read(W * H * 4)
            if len(buf) < W * H * 4:
                break  # past the end: keep the last frame
            self.frame = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
            self.pos += 1
        return self.frame

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.kill()
            self.proc.wait()
            self.proc = None


# ------------------------------------------------------------------ rendering
def new_surface():
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)


def as_array(surf):
    surf.flush()
    return np.ndarray((H, W, 4), np.uint8, surf.get_data())


class Renderer:
    def __init__(self, shots, total, voice):
        self.shots, self.total = shots, total
        self.readers = {}
        self.out = new_surface()
        self.layers = [new_surface(), new_surface()]
        self.segl = [new_surface(), new_surface()]
        self.frame_surf = None
        self.small = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // 8, H // 8)
        self.subs = build_subtitles(shots, voice)
        self._scan = None

    def reader(self, path):
        r = self.readers.get(path)
        if r is None:
            r = self.readers[path] = Reader(path)
        return r

    def close(self):
        for r in self.readers.values():
            r.close()

    # ---------------------------------------------------------- segments
    def draw_clip(self, ctx, sh, s, lt):
        sp = s.spec
        if sp.get("freeze"):
            fr = self.reader(s.path).get(0)
        else:
            fr = self.reader(s.path).get(int(round(lt * FPS)))
        if fr is None:
            return
        if getattr(s, "screen", None):
            fr = self.replace_screen(fr, s, lt)
        img = cairo.ImageSurface.create_for_data(memoryview(fr), cairo.FORMAT_ARGB32, W, H)
        u = remap(lt, 0, s.dur)
        z0, z1 = sp.get("zoom", (1.0, 1.0))
        z = lerp(z0, z1, ease_in_out(u) * 0.6 + u * 0.4)
        ctx.save()
        ctx.translate(W / 2, H / 2)
        if sp.get("shake"):
            k = sp["shake"] * 14
            ctx.translate(math.sin(lt * 63) * k, math.cos(lt * 71) * k * 0.7)
        if sp.get("rot"):
            ctx.rotate(math.radians(sp["rot"]))
            z *= 1.0 + abs(math.radians(sp["rot"])) * 0.9
        ctx.scale(z, z)
        ctx.translate(-W / 2, -H / 2)
        if sp.get("blur"):
            sc = cairo.Context(self.small)
            sc.scale(1 / 8, 1 / 8)
            sc.set_source_surface(img, 0, 0)
            sc.paint()
            ctx.scale(8, 8)
            ctx.set_source_surface(self.small, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
            ctx.get_source().set_extend(cairo.EXTEND_PAD)
            ctx.paint()
        else:
            ctx.set_source_surface(img, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_GOOD)
            ctx.get_source().set_extend(cairo.EXTEND_PAD)
            ctx.paint()
        ctx.restore()
        if sp.get("tv"):
            self.tv_effect(ctx, lt)
        if sp.get("window"):
            window_frame(ctx)

    def replace_screen(self, fr, s, lt):
        """Find the bright TV screen in a dark room and show other footage on it."""
        fr = fr.copy()
        sm = fr[::4, ::4, :3].astype(np.float32)
        lum = sm[..., 2] * 0.3 + sm[..., 1] * 0.59 + sm[..., 0] * 0.11
        ys, xs = np.nonzero(lum > 70)
        if len(xs) < 50:
            return fr
        box = np.array([np.percentile(xs, 2), np.percentile(ys, 2), np.percentile(xs, 98), np.percentile(ys, 98)]) * 4
        prev = getattr(s, "_box", None)
        if prev is not None and abs(getattr(s, "_box_t", -9) - lt) < 0.2:
            box = prev * 0.75 + box * 0.25
        s._box, s._box_t = box, lt
        x0, y0, x1, y1 = box
        sub = self.reader(s.screen.path).get(int(round(lt * FPS)))
        surf = cairo.ImageSurface.create_for_data(memoryview(fr), cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(surf)
        c.rectangle(x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4)
        c.clip()
        c.translate(x0, y0)
        c.scale((x1 - x0) / W, (y1 - y0) / H)
        c.set_source_surface(cairo.ImageSurface.create_for_data(memoryview(sub), cairo.FORMAT_ARGB32, W, H), 0, 0)
        c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(0.97)
        surf.flush()
        return fr

    def tv_effect(self, ctx, lt):
        if self._scan is None:
            self._scan = new_surface()
            c = cairo.Context(self._scan)
            for y in range(0, H, 4):
                c.rectangle(0, y, W, 1.6)
            c.set_source_rgba(0, 0, 0, 0.22)
            c.fill()
        ctx.set_source_surface(self._scan, 0, 0)
        ctx.paint()
        gx.rad(ctx, W / 2, H / 2, W * 0.62, [(0, (0.6, 0.75, 1.0), 0.06 + 0.02 * math.sin(lt * 31)),
                                              (0.7, (0, 0, 0), 0.0), (1, (0, 0, 0), 0.55)])
        ctx.paint()

    def draw_seg(self, ctx, sh, s, lt):
        if s.kind == "clip":
            self.draw_clip(ctx, sh, s, lt)
        elif s.kind == "black":
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
        elif s.kind == "photo":
            gx.photo_scene(ctx, lt, s.dur, s.path, s.spec.get("caption", ""))
        elif s.kind == "map":
            gx.map_scene(ctx, lt, s.dur, s.spec.get("broken", False))

    # ---------------------------------------------------------- shots
    def draw_shot(self, surf, sh, lt):
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        if sh.card:
            gx.card(ctx, lt, sh.dur, *sh.card)
            grade(as_array(surf), lt, dict(grain=0.03, vignette=0.3), seed=sh.idx * 7)
            surf.mark_dirty()
            return
        active = [s for s in sh.segs if s.t0 - 1e-6 <= lt < s.t1]
        for i, s in enumerate(active[-2:]):
            a = 1.0
            if i == 1:
                prev = active[-2]
                a = smooth(remap(lt, s.t0, prev.t1)) if prev.x > 0 else 1.0
            layer = self.segl[i]
            lc = cairo.Context(layer)
            lc.set_source_rgb(0, 0, 0)
            lc.paint()
            self.draw_seg(lc, sh, s, lt - s.t0)
            look = merge_look(sh.look, s.spec.get("look"))
            if look:
                grade(as_array(layer), lt + sh.start, look, seed=sh.idx * 7)
                layer.mark_dirty()
            ctx.set_source_surface(layer, 0, 0)
            ctx.paint_with_alpha(a)
        for kind, a, b, p in sh.overlays:
            if a <= lt < b:
                self.draw_overlay(ctx, kind, lt - a, b - a, p)

    def draw_overlay(self, ctx, kind, t, dur, p):
        if kind == "title":
            gx.title(ctx, t, dur, p["text"], p["sub"])
        elif kind == "label":
            gx.label(ctx, t, dur, p["text"], p.get("small", False))
        elif kind == "lower":
            gx.lower(ctx, t, dur, p["title"], p["sub"])
        elif kind == "flash":
            gx.flash(ctx, t, dur)
        elif kind == "counter":
            gx.counter(ctx, t, dur, p["n"], p["word"], p["sub"])
        elif kind == "tribute":
            gx.tribute(ctx, t, dur, p["n"], p["name"], p["sub"])
        elif kind == "china":
            gx.china(ctx, t, dur)
        elif kind == "end_title":
            gx.end_title(ctx, t, dur)

    def render(self, fi):
        T = fi / FPS
        out = self.out
        ctx = cairo.Context(out)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        act = [sh for sh in self.shots if sh.start - 1e-6 <= T < sh.start + sh.dur]
        for i, sh in enumerate(act[-2:]):
            a = 1.0
            if i == 1:
                prev = act[-2]
                a = smooth(remap(T, sh.start, prev.start + prev.dur))
            layer = self.layers[i]
            self.draw_shot(layer, sh, T - sh.start)
            ctx.set_source_surface(layer, 0, 0)
            ctx.paint_with_alpha(a)
        # final fade from/to black
        edge = min(smooth(remap(T, 0, 1.2)), smooth(remap(T, self.total, self.total - 1.0)))
        if edge < 1:
            ctx.set_source_rgba(0, 0, 0, 1 - edge)
            ctx.paint()
        # letterbox
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, W, gx.BAR)
        ctx.rectangle(0, H - gx.BAR, W, gx.BAR)
        ctx.fill()
        draw_subtitles(ctx, self.subs, T)
        out.flush()
        return bytes(out.get_data())


def window_frame(ctx):
    c = (0.035, 0.038, 0.045)
    ctx.set_source_rgba(*c, 0.97)
    t = 90
    ctx.rectangle(0, 0, W, t + 40)
    ctx.rectangle(0, H - t - 40, W, t + 40)
    ctx.rectangle(0, 0, t + 60, H)
    ctx.rectangle(W - t - 60, 0, t + 60, H)
    ctx.rectangle(W * 0.6 - 22, 0, 44, H)
    ctx.rectangle(0, H * 0.36 - 18, W, 36)
    ctx.fill()
    gx.lin(ctx, 0, 0, W, H, [(0, (1, 1, 1), 0.0), (0.45, (1, 1, 1), 0.06), (0.55, (1, 1, 1), 0.0)])
    ctx.paint()


# ------------------------------------------------------------------ subtitles
def split_line(text_, max_chars=92):
    if len(text_) <= max_chars:
        return [text_]
    parts = re.split(r"(?<=[,.;])\s+", text_)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        chunks.append(cur)
    return chunks


def build_subtitles(shots, voice):
    subs = []
    for sh in shots:
        for lid, (a, b) in sh.cues.items():
            chunks = split_line(NARRATION[lid])
            total = sum(len(c) for c in chunks)
            t = sh.start + a
            span = b - a
            for c in chunks:
                d = span * len(c) / total
                subs.append((t, t + d, c))
                t += d
    return subs


def draw_subtitles(ctx, subs, T):
    for a, b, s in subs:
        if a - 0.1 <= T < b + 0.25:
            al = smooth(remap(T, a - 0.1, a + 0.08)) * smooth(remap(T, b + 0.25, b + 0.05))
            lines = wrap(s, 40, 1500, "inter", 500)
            y0 = H - gx.BAR - 46 - (len(lines) - 1) * 52
            for i, ln in enumerate(lines):
                text(ctx, ln, W / 2, y0 + i * 52, 40, "inter", 500, (1, 1, 1), al, "mb", shadow=0.95,
                     shadow_blur=6, shadow_off=(0, 2))


def write_srt(subs, path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as f:
        for i, (a, b, s) in enumerate(subs, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n")


# ------------------------------------------------------------------ parallel encode
def render_chunk(args):
    f0, f1, out_path, crf = args
    from .tts import synthesize  # noqa: F401  (ensures package import in worker)
    voice = json.load(open(os.path.join(BUILD, "voice.json")))
    shots, total = build_timeline(voice)
    for sh in shots:
        for s in sh.segs:
            if s.kind == "clip":
                s.path = os.path.join(BUILD, "seg", seg_key(s) + (".png" if s.spec.get("freeze") else ".mp4"))
                if getattr(s, "screen", None):
                    s.screen.path = os.path.join(BUILD, "seg", seg_key(s.screen) + ".mp4")
            elif s.kind == "photo":
                s.path = os.path.join(BUILD, "seg", f"still_{s.spec['clip']}_{s.spec['at']}.png")
    r = Renderer(shots, total, voice)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                            "-pix_fmt", "yuv420p", "-x264-params", "threads=2", out_path], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        enc.stdin.write(r.render(fi))
    enc.stdin.close()
    enc.wait()
    r.close()
    return out_path
