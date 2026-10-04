"""Drawing toolkit: easing, colour, gradients, text, the football, film post-processing."""
import math
import os
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
PHOTOS = os.path.join(ROOT, "photos")
TAU = math.tau


# ---------------------------------------------------------------- maths / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def remap(x, a, b):
    """0..1 progress of x through [a, b] (clamped)."""
    if b == a:
        return 1.0 if x >= b else 0.0
    return clamp((x - a) / (b - a))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in_out(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out(t):
    return 1 - (1 - clamp(t)) ** 3


def ease_in(t):
    return clamp(t) ** 3


def ease_out_back(t, s=1.4):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def fade(t, dur, fin=0.6, fout=0.6):
    """Envelope that fades in over `fin` seconds and out over the last `fout`."""
    return smooth(remap(t, 0, fin)) * smooth(remap(t, dur, dur - fout)) if fout > 0 else smooth(remap(t, 0, fin))


def wobble(t, seed=0.0, speed=1.0):
    """Cheap smooth pseudo-noise in [-1, 1]."""
    s = seed * 12.9898
    return (math.sin(t * speed * 1.13 + s) * 0.5 + math.sin(t * speed * 2.31 + s * 1.7) * 0.3
            + math.sin(t * speed * 0.47 + s * 2.3) * 0.2)


def rng(seed):
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- colour
def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def src(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


# ---------------------------------------------------------------- shapes / gradients
def _stops(p, stops):
    for st in stops:
        off, c = st[0], st[1]
        a = st[2] if len(st) > 2 else 1.0
        p.add_color_stop_rgba(off, c[0], c[1], c[2], a)
    return p


def lin(ctx, x0, y0, x1, y1, stops):
    ctx.set_source(_stops(cairo.LinearGradient(x0, y0, x1, y1), stops))


def rad(ctx, cx, cy, r, stops, cx0=None, cy0=None, r0=0.0):
    p = cairo.RadialGradient(cx if cx0 is None else cx0, cy if cy0 is None else cy0, r0, cx, cy, r)
    ctx.set_source(_stops(p, stops))


def glow(ctx, x, y, r, c, a=1.0, falloff=(0.0, 0.35, 1.0)):
    if a <= 0.002 or r <= 0:
        return
    rad(ctx, x, y, r, [(0, c, a), (falloff[1], c, a * 0.35), (falloff[2], c, 0)])
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def ellipse(ctx, cx, cy, rx, ry):
    if rx <= 0 or ry <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def line(ctx, x0, y0, x1, y1, w, c, a=1.0, cap=cairo.LINE_CAP_ROUND):
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    src(ctx, c, a)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def shadow_blob(ctx, x, y, rx, ry, a=0.35):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(1, ry / rx)
    rad(ctx, 0, 0, rx, [(0, (0, 0, 0), a), (0.6, (0, 0, 0), a * 0.5), (1, (0, 0, 0), 0)])
    ctx.arc(0, 0, rx, 0, TAU)
    ctx.fill()
    ctx.restore()


def fill_screen(ctx, c, a=1.0):
    ctx.save()
    ctx.identity_matrix()
    src(ctx, c, a)
    ctx.paint()
    ctx.restore()


def vgrad_screen(ctx, stops, y0=0, y1=H):
    lin(ctx, 0, y0, 0, y1, stops)
    ctx.rectangle(-W, -H, 3 * W, 3 * H)
    ctx.fill()


def zoom(ctx, s, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    """Camera: scale by s around (cx, cy), then pan by (dx, dy)."""
    ctx.translate(cx + dx, cy + dy)
    ctx.scale(s, s)
    ctx.translate(-cx, -cy)


# ---------------------------------------------------------------- text
FONTS = {"bebas": "BebasNeue.ttf", "inter": "Inter.ttf", "mont": "Montserrat.ttf",
         "play": "PlayfairDisplay.ttf", "caveat": "Caveat.ttf", "sans": "NotoSansSC.ttf",
         "serif": "NotoSerifSC.ttf"}


@lru_cache(maxsize=256)
def pil_font(name, size, weight=400):
    f = ImageFont.truetype(os.path.join(ASSETS, "fonts", FONTS[name]), int(size))
    try:
        axes = f.get_variation_axes()
    except Exception:
        return f
    vals = []
    for ax in axes:
        nm = ax.get("name", b"")
        nm = nm.decode() if isinstance(nm, bytes) else str(nm)
        if "eight" in nm:
            vals.append(clamp(weight, ax["minimum"], ax["maximum"]))
        elif "ptical" in nm:
            vals.append(clamp(size * 0.75, ax["minimum"], ax["maximum"]))
        else:
            vals.append(ax["default"])
    f.set_variation_by_axes(vals)
    return f


@lru_cache(maxsize=4096)
def text_mask(s, font, size, weight, tracking, blur):
    """Render text to an A8 cairo surface. Returns (surface, width, ascent, cap_height, pad, buffer)."""
    f = pil_font(font, size, weight)
    asc, desc = f.getmetrics()
    track = tracking * size
    widths = [f.getlength(ch) for ch in s]
    width = sum(widths) + track * max(0, len(s) - 1) if tracking else f.getlength(s)
    pad = int(blur * 3 + 4)
    iw, ih = int(math.ceil(width)) + 2 * pad + 4, asc + desc + 2 * pad
    img = Image.new("L", (iw, ih), 0)
    d = ImageDraw.Draw(img)
    if tracking:
        x = pad
        for ch, w in zip(s, widths):
            d.text((x, pad), ch, font=f, fill=255, anchor="la")
            x += w + track
    else:
        d.text((pad, pad), s, font=f, fill=255, anchor="la")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, iw)
    buf = np.zeros((ih, stride), np.uint8)
    buf[:, :iw] = np.asarray(img)
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_A8, iw, ih, stride)
    cap = f.getbbox("H", anchor="ls")
    cap_h = -cap[1]
    return surf, width, asc, cap_h, pad, buf


def text_width(s, size, font="inter", weight=400, tracking=0.0):
    return text_mask(s, font, size, weight, tracking, 0)[1]


def text(ctx, s, x, y, size, font="inter", weight=400, c=(1, 1, 1), a=1.0, anchor="mm",
         tracking=0.0, shadow=0.0, shadow_blur=8, shadow_off=(0, 3), glow_c=None, glow_a=0.0):
    """Draw text. anchor: [l|m|r][t|m|b] where vertical m = middle of cap height, b = baseline."""
    if a <= 0.003 or not s:
        return
    surf, width, asc, cap_h, pad, _ = text_mask(s, font, size, weight, tracking, 0)
    hx = {"l": 0, "m": width / 2, "r": width}[anchor[0]]
    vy = {"t": asc - cap_h, "m": asc - cap_h / 2, "b": asc}[anchor[1]]
    ox, oy = x - hx - pad, y - vy - pad
    if shadow > 0:
        bs = text_mask(s, font, size, weight, tracking, shadow_blur)
        dp = bs[4] - pad
        ctx.set_source_rgba(0, 0, 0, shadow * a)
        ctx.mask_surface(bs[0], ox - dp + shadow_off[0], oy - dp + shadow_off[1])
    if glow_c is not None and glow_a > 0:
        gs = text_mask(s, font, size, weight, tracking, max(6, size // 6))
        dp = gs[4] - pad
        src(ctx, glow_c, glow_a * a)
        ctx.mask_surface(gs[0], ox - dp, oy - dp)
    src(ctx, c, a)
    ctx.mask_surface(surf, ox, oy)


def wrap(s, size, max_w, font="inter", weight=400):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, size, font, weight) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- post-processing
@lru_cache(maxsize=4)
def vignette(strength=0.55, power=2.2):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    return (1 - strength * d ** power).astype(np.float32)[..., None]


@lru_cache(maxsize=1)
def grain_bank():
    g = rng(7)
    small = g.normal(0, 1, (8, H // 2, W // 2)).astype(np.float32)
    big = np.repeat(np.repeat(small, 2, axis=1), 2, axis=2)
    return np.repeat(big[..., None], 3, axis=3) * np.array([1.0, 0.9, 1.1], np.float32)


GRAIN_SCALE = 0.45  # film grain is costly to encode; keep it subtle


def grade(frame, t, look, seed=0):
    """In-place colour grade of an HxWx4 uint8 BGRA frame (cairo's ARGB32 memory order).

    look keys: temp, sat, contrast, lift, fade, bright, tint_red, vignette, grain.
    """
    if not look:
        return frame
    x = frame[..., :3].astype(np.float32)
    x *= 1 / 255
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    sat = look.get("sat", 1.0)
    if sat != 1.0:
        x -= lum[..., None]
        x *= sat
        x += lum[..., None]
    temp = look.get("temp", 0.0)
    if temp:
        x[..., 2] *= 1 + temp
        x[..., 1] *= 1 + temp * 0.25
        x[..., 0] *= 1 - temp
    red = look.get("tint_red", 0.0)
    if red:
        x[..., 2] = x[..., 2] * (1 + red) + red * 0.05
        x[..., 1] *= 1 - red * 0.35
        x[..., 0] *= 1 - red * 0.55
    bright = look.get("bright", 1.0)
    if bright != 1.0:
        x *= bright
    con = look.get("contrast", 1.0)
    if con != 1.0:
        x -= 0.45
        x *= con
        x += 0.45
    fade = look.get("fade", 0.0)
    if fade:
        x *= 1 - fade
        x += fade * 0.4
    lift = look.get("lift", 0.0)
    if lift:
        x *= 1 - lift
        x += lift
    vg = look.get("vignette", 0.0)
    if vg:
        x *= vignette(round(vg, 2))
    gr = look.get("grain", 0.0)
    if gr:
        bank = grain_bank()
        x += bank[(int(t * FPS) + seed) % len(bank)] * (gr * GRAIN_SCALE)
    np.clip(x, 0, 1, out=x)
    x *= 255
    x += 0.5
    frame[..., :3] = x.astype(np.uint8)
    return frame


def merge_look(*looks):
    out = {}
    for lk in looks:
        if lk:
            out.update(lk)
    return out


_KEEP = []


def surface_from_pil(img):
    """PIL RGBA image -> cairo ARGB32 surface (premultiplied)."""
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    al = a[..., 3:4] / 255
    pm = np.concatenate([a[..., 2::-1] * al, a[..., 3:4]], axis=2).astype(np.uint8)
    h, w = pm.shape[:2]
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = np.zeros((h, stride // 4, 4), np.uint8)
    buf[:, :w] = pm
    s = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, w, h, stride)
    _KEEP.append(buf)  # the surface borrows this memory
    return s


@lru_cache(maxsize=16)
def user_photo(name):
    """Optional real photo dropped into video/photos/<name>.(jpg|png). Returns cairo surface or None."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(PHOTOS, f"{name}.{ext}")
        if os.path.exists(p):
            img = Image.open(p).convert("RGBA")
            img.thumbnail((2400, 2400))
            return surface_from_pil(img)
    return None


def paint_cover(ctx, surf, x, y, w, h, kb=0.0, focus=(0.5, 0.5)):
    """Paint `surf` covering the box with a slow Ken Burns zoom (kb = 0..1 progress)."""
    sw, sh = surf.get_width(), surf.get_height()
    s = max(w / sw, h / sh) * (1.04 + 0.08 * kb)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.translate(x + w * focus[0], y + h * focus[1])
    ctx.scale(s, s)
    ctx.translate(-sw * focus[0], -sh * focus[1])
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
