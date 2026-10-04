"""Motion graphics drawn over (or instead of) footage: titles, cards, labels, map, photo print, tributes."""
import json
import math
import os
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .gfx import (ASSETS, H, TAU, W, clamp, ease_in_out, ease_out, glow, hexc, lerp, lin, rad, remap, rng,
                  rrect, smooth, src, surface_from_pil, text, text_mask, user_photo)

GOLD = hexc("#d9b46a")
CREAM = hexc("#f3ead8")
BAR = 64  # letterbox bar height


def fade_env(t, dur, fin=0.5, fout=0.5):
    return smooth(remap(t, 0, fin)) * smooth(remap(t, dur, dur - fout))


# ------------------------------------------------------------------ titles and cards
def title(ctx, t, dur, text_, sub):
    a = fade_env(t, dur, 1.8, 1.2)
    if a <= 0:
        return
    rad(ctx, W / 2, H / 2, W * 0.55, [(0, (0, 0, 0), 0.45 * a), (1, (0, 0, 0), 0)])
    ctx.paint()
    track = lerp(0.42, 0.26, ease_out(remap(t, 0, 4.0)))
    text(ctx, text_, W / 2, H / 2 - 10, 156, "bebas", 400, CREAM, a, "mm", tracking=track, shadow=0.55,
         shadow_blur=14, glow_c=GOLD, glow_a=0.12)
    a2 = fade_env(t - 1.0, dur - 1.0, 1.6, 1.2)
    text(ctx, sub, W / 2, H / 2 + 92, 24, "inter", 500, GOLD, a2 * 0.9, "mm", tracking=0.55, shadow=0.5)


def card(ctx, t, dur, num, title_):
    lin(ctx, 0, 0, 0, H, [(0, hexc("#07080a")), (1, hexc("#0d0c0b"))])
    ctx.paint()
    rad(ctx, W / 2, H / 2, W * 0.5, [(0, hexc("#2a2219"), 0.55), (1, (0, 0, 0), 0)])
    ctx.paint()
    a = fade_env(t, dur, 0.9, 0.7)
    rise = 14 * (1 - ease_out(remap(t, 0, 1.6)))
    text(ctx, num.upper(), W / 2, H / 2 - 78 + rise, 24, "inter", 600, GOLD, a, "mm", tracking=0.5)
    text(ctx, title_, W / 2, H / 2 + 6 + rise * 0.6, 98, "play", 500, CREAM, a, "mm", shadow=0.4)
    lw = 260 * ease_in_out(remap(t, 0.3, 1.8))
    ctx.set_source_rgba(*GOLD, 0.8 * a)
    ctx.rectangle(W / 2 - lw / 2, H / 2 + 86, lw, 2)
    ctx.fill()


def end_title(ctx, t, dur):
    dark = 0.7 * smooth(remap(t, 0, 3.0)) + 0.3 * smooth(remap(t, dur - 3.0, dur - 0.6))
    ctx.set_source_rgba(0, 0, 0, dark)
    ctx.paint()
    a = fade_env(t - 1.2, dur - 1.2, 1.8, 1.6)
    track = lerp(0.40, 0.26, ease_out(remap(t, 1.2, 6.0)))
    text(ctx, "STILL ROLLING", W / 2, H / 2 - 40, 148, "bebas", 400, CREAM, a, "mm", tracking=track,
         glow_c=GOLD, glow_a=0.1)
    a2 = fade_env(t - 2.4, dur - 2.4, 1.6, 1.6)
    text(ctx, "Based on a true story", W / 2, H / 2 + 52, 34, "play", 400, GOLD, a2, "mm")
    a3 = fade_env(t - 4.0, dur - 4.0, 1.4, 1.6) * 0.55
    lines = ["Footage: Kinetics-700 research dataset (public YouTube clips), used as stand-in imagery",
             "Voice: Kokoro neural TTS  ·  Original score synthesized for this film"]
    for i, ln in enumerate(lines):
        text(ctx, ln, W / 2, H - BAR - 120 + i * 34, 20, "inter", 400, CREAM, a3, "mm", tracking=0.04)


def label(ctx, t, dur, text_, small=False):
    a = fade_env(t, dur, 0.25, 0.25)
    x = 118 - 18 * (1 - ease_out(remap(t, 0, 0.5)))
    y = BAR + 104
    size = 46 if small else 64
    ctx.set_source_rgba(*GOLD, 0.95 * a)
    ctx.rectangle(x - 26, y - size * 0.36, 4, size * 0.72)
    ctx.fill()
    text(ctx, text_, x, y, size, "bebas", 400, CREAM, a, "lm", tracking=0.16, shadow=0.6, shadow_blur=10)


def lower(ctx, t, dur, title_, sub):
    a = fade_env(t, dur, 0.5, 0.5)
    k = ease_out(remap(t, 0, 0.9))
    x, y = 132, H - BAR - 250
    ctx.push_group()
    lin(ctx, 0, 0, 1100, 0, [(0, (0, 0, 0), 0.6 * a), (0.6, (0, 0, 0), 0.3 * a), (1, (0, 0, 0), 0)])
    ctx.paint()
    ctx.pop_group_to_source()
    mask = cairo.LinearGradient(0, y - 130, 0, y + 170)
    for off, al in ((0, 0), (0.35, 1), (0.7, 1), (1, 0)):
        mask.add_color_stop_rgba(off, 0, 0, 0, al)
    ctx.mask(mask)
    ctx.set_source_rgba(*GOLD, 0.95 * a)
    ctx.rectangle(x - 26, y - 34, 5, 104 * k)
    ctx.fill()
    text(ctx, title_, x + 12 * (1 - k), y, 50, "inter", 600, CREAM, a, "lm", shadow=0.6, shadow_blur=10)
    a2 = fade_env(t - 0.35, dur - 0.35, 0.5, 0.5)
    text(ctx, sub, x + 12 * (1 - k), y + 52, 30, "inter", 400, GOLD, a2, "lm", tracking=0.06, shadow=0.6)


def flash(ctx, t, dur):
    a = (1 - remap(t, 0, dur)) ** 2 * 0.85
    ctx.set_source_rgba(1, 0.97, 0.92, a)
    ctx.paint()


def counter(ctx, t, dur, n, word, sub):
    a = fade_env(t, dur, 0.6, 0.6)
    rad(ctx, W * 0.74, H / 2, W * 0.42, [(0, (0, 0, 0), 0.55 * a), (1, (0, 0, 0), 0)])
    ctx.paint()
    v = max(1, int(round(lerp(1, n, ease_out(remap(t, 0.2, 2.6))))))
    x = W * 0.74
    text(ctx, str(v), x, H / 2 - 40, 330, "bebas", 400, CREAM, a, "mm", shadow=0.4, shadow_blur=20,
         glow_c=GOLD, glow_a=0.12)
    text(ctx, word, x, H / 2 + 128, 44, "inter", 600, CREAM, a, "mm", tracking=0.6)
    a2 = fade_env(t - 1.2, dur - 1.2, 0.8, 0.6)
    text(ctx, sub, x, H / 2 + 186, 26, "inter", 500, GOLD, a2, "mm", tracking=0.7)


@lru_cache(maxsize=8)
def outline_mask(s, size, stroke):
    from .gfx import pil_font
    f = pil_font("bebas", size, 400)
    asc, desc = f.getmetrics()
    w = int(f.getlength(s)) + 4 * stroke + 20
    h = asc + desc + 4 * stroke
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    d.text((2 * stroke + 10, 2 * stroke), s, font=f, fill=255, stroke_width=stroke, stroke_fill=255, anchor="la")
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).text((2 * stroke + 10, 2 * stroke), s, font=f, fill=255, anchor="la")
    arr = np.clip(np.asarray(img).astype(np.int16) - np.asarray(inner).astype(np.int16), 0, 255).astype(np.uint8)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
    buf = np.zeros((h, stride), np.uint8)
    buf[:, :w] = arr
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_A8, w, h, stride)
    return surf, w, h, buf


def tribute(ctx, t, dur, n, name, sub):
    a = fade_env(t, dur, 0.7, 0.6)
    lin(ctx, 0, 0, W, 0, [(0, (0, 0, 0), 0.55 * a), (0.6, (0, 0, 0), 0.25 * a), (1, (0, 0, 0), 0.0)])
    ctx.paint()
    surf, w, h, _ = outline_mask(n, 560, 3)
    s = lerp(1.04, 1.0, ease_out(remap(t, 0, 3.0)))
    ctx.save()
    ctx.translate(W * 0.30, H / 2 + 10)
    ctx.scale(s, s)
    ctx.set_source_rgba(*CREAM, 0.85 * a)
    ctx.mask_surface(surf, -w / 2, -h / 2)
    ctx.restore()
    k = ease_out(remap(t, 0.3, 1.3))
    x = W * 0.50 + 30 * (1 - k)
    text(ctx, name, x, H / 2 - 18, 72, "inter", 700, CREAM, a * k, "lm", tracking=0.08, shadow=0.5)
    ctx.set_source_rgba(*GOLD, 0.9 * a * k)
    ctx.rectangle(x, H / 2 + 34, 120 * k, 3)
    ctx.fill()
    a2 = fade_env(t - 0.8, dur - 0.8, 0.7, 0.6)
    text(ctx, sub, x, H / 2 + 86, 40, "play", 400, GOLD, a2, "lm", shadow=0.5)


CJK = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"


@lru_cache(maxsize=2)
def cjk_mask(s, size):
    from PIL import ImageFont
    f = ImageFont.truetype(CJK, size)
    bbox = f.getbbox(s)
    w, h = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).text((20 - bbox[0], 20 - bbox[1]), s, font=f, fill=255)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
    buf = np.zeros((h, stride), np.uint8)
    buf[:, :w] = np.asarray(img)
    return cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_A8, w, h, stride), w, h, buf


def china(ctx, t, dur):
    a = fade_env(t, dur, 0.8, 0.7)
    rad(ctx, W / 2, H / 2, W * 0.5, [(0, (0, 0, 0), 0.5 * a), (1, (0, 0, 0), 0.0)])
    ctx.paint()
    y = H / 2 - 40
    if os.path.exists(CJK):
        surf, w, h, _ = cjk_mask("中国", 230)
        s = lerp(1.05, 1.0, ease_out(remap(t, 0, 3)))
        ctx.save()
        ctx.translate(W / 2, y)
        ctx.scale(s, s)
        ctx.set_source_rgba(*hexc("#ffd36b"), 0.95 * a)
        ctx.mask_surface(surf, -w / 2, -h / 2)
        ctx.restore()
    else:
        text(ctx, "CHINA", W / 2, y, 200, "bebas", 400, hexc("#ffd36b"), a, "mm", tracking=0.2)
    a2 = fade_env(t - 0.7, dur - 0.7, 0.7, 0.7)
    text(ctx, "CHINA  ·  NATIONAL MEN'S TEAM", W / 2, H / 2 + 128, 30, "inter", 600, CREAM, a2, "mm",
         tracking=0.45, shadow=0.6)


# ------------------------------------------------------------------ map (Chengdu -> Madrid)
CHENGDU = (104.07, 30.67)
MADRID = (-3.70, 40.42)
_K, _LON0, _LAT0, _COS = 15.2, 52.0, 37.0, math.cos(math.radians(38))


def proj(lon, lat):
    return W / 2 + (lon - _LON0) * _K * _COS, H / 2 - (lat - _LAT0) * _K


@lru_cache(maxsize=1)
def map_base():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    lin(c, 0, 0, 0, H, [(0, hexc("#0a1220")), (1, hexc("#05080f"))])
    c.paint()
    rad(c, W * 0.55, H * 0.45, W * 0.6, [(0, hexc("#1b2b45"), 0.6), (1, (0, 0, 0), 0)])
    c.paint()
    pts = json.load(open(os.path.join(ASSETS, "map_dots.json")))["points"]
    g = rng(3)
    for lon, lat in pts:
        x, y = proj(lon, lat)
        if -10 < x < W + 10 and -10 < y < H + 10:
            v = 0.42 + 0.18 * g.random()
            c.set_source_rgba(0.45 * v + 0.2, 0.58 * v + 0.25, 0.85 * v + 0.2, 0.55)
            c.arc(x, y, 2.3, 0, TAU)
            c.fill()
    return s


def _bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def _pin(ctx, x, y, c, a, t, label_, side=1, pulse=True):
    if a <= 0:
        return
    if pulse:
        for k in range(2):
            ph = ((t * 0.6 + k * 0.5) % 1.0)
            ctx.set_source_rgba(*c, a * 0.5 * (1 - ph))
            ctx.set_line_width(2)
            ctx.arc(x, y, 8 + ph * 34, 0, TAU)
            ctx.stroke()
    glow(ctx, x, y, 34, c, 0.5 * a)
    ctx.set_source_rgba(*c, a)
    ctx.arc(x, y, 7, 0, TAU)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.arc(x, y, 3, 0, TAU)
    ctx.fill()
    name, country = label_
    text(ctx, name, x + side * 26, y - 14, 40, "bebas", 400, CREAM, a, "lm" if side > 0 else "rm", tracking=0.14)
    text(ctx, country, x + side * 26, y + 20, 20, "inter", 500, c, a * 0.9, "lm" if side > 0 else "rm",
         tracking=0.35)


def map_scene(ctx, t, dur, broken=False):
    zoom = lerp(1.0, 1.07, ease_in_out(remap(t, 0, dur)))
    p0, p2 = proj(*CHENGDU), proj(*MADRID)
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    ctx.save()
    ctx.translate(mx, my + 40)
    ctx.scale(zoom, zoom)
    ctx.translate(-mx, -my - 40)
    ctx.set_source_surface(map_base(), 0, 0)
    ctx.paint_with_alpha(smooth(remap(t, 0, 1.0)) if not broken else 1.0)
    dist = math.hypot(p2[0] - p0[0], p2[1] - p0[1])
    p1 = (mx, my - dist * 0.34)
    red = hexc("#e2574c")
    gold = GOLD
    if not broken:
        a0 = smooth(remap(t, 0.6, 1.4))
        _pin(ctx, *p0, red, a0, t, ("CHENGDU", "SICHUAN · CHINA"), side=1)
        u = ease_in_out(remap(t, 1.8, 6.4))
        if u > 0:
            n = 120
            ctx.set_line_width(3.2)
            ctx.set_line_cap(1)
            for i in range(int(n * u)):
                q0, q1 = _bez(p0, p1, p2, i / n), _bez(p0, p1, p2, (i + 1) / n)
                if (i // 3) % 2 == 0:
                    ctx.set_source_rgba(*gold, 0.9)
                    ctx.move_to(*q0)
                    ctx.line_to(*q1)
                    ctx.stroke()
            hx, hy = _bez(p0, p1, p2, u)
            if u < 1:
                glow(ctx, hx, hy, 40, gold, 0.8)
                ctx.set_source_rgba(1, 1, 1, 1)
                ctx.arc(hx, hy, 5, 0, TAU)
                ctx.fill()
        a2 = smooth(remap(t, 6.2, 7.0))
        _pin(ctx, *p2, gold, a2, t, ("MADRID", "SPAIN"), side=-1)
        a3 = smooth(remap(t, 7.0, 8.0)) * smooth(remap(t, dur, dur - 0.6))
        text(ctx, "THE NEXT STEP", W / 2, BAR + 90, 26, "inter", 600, gold, a3, "mm", tracking=0.6)
    else:
        _pin(ctx, *p0, red, 1.0, t, ("CHENGDU", "SICHUAN · CHINA"), side=1)
        brk = ease_in_out(remap(t, 1.0, 4.2))
        n = 120
        g = rng(11)
        drift = g.random(n) * 0.8 + 0.4
        spin = (g.random(n) - 0.5) * 2
        ctx.set_line_width(3.2)
        ctx.set_line_cap(1)
        for i in range(n):
            if (i // 3) % 2:
                continue
            q0, q1 = _bez(p0, p1, p2, i / n), _bez(p0, p1, p2, (i + 1) / n)
            local = clamp(brk * 1.6 - (1 - i / n) * 0.6)
            fall = local ** 1.6 * 160 * drift[i]
            alpha = 0.9 * (1 - local)
            if alpha <= 0.01:
                continue
            c = (lerp(gold[0], 0.55, local), lerp(gold[1], 0.55, local), lerp(gold[2], 0.58, local))
            ctx.save()
            cx, cy = (q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2 + fall
            ctx.translate(cx, cy)
            ctx.rotate(spin[i] * local * 1.5)
            ctx.set_source_rgba(*c, alpha)
            ctx.move_to(q0[0] - (q0[0] + q1[0]) / 2, q0[1] - (q0[1] + q1[1]) / 2)
            ctx.line_to(q1[0] - (q0[0] + q1[0]) / 2, q1[1] - (q0[1] + q1[1]) / 2)
            ctx.stroke()
            ctx.restore()
        dim = 1 - 0.7 * smooth(remap(t, 2.0, 5.0))
        grey = (lerp(0.5, gold[0], dim), lerp(0.5, gold[1], dim), lerp(0.52, gold[2], dim))
        _pin(ctx, *p2, grey, 0.35 + 0.65 * dim, t, ("MADRID", "SPAIN"), side=-1, pulse=False)
    ctx.restore()


# ------------------------------------------------------------------ the old photograph
@lru_cache(maxsize=1)
def table_texture():
    g = rng(5)
    base = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    grain = (np.sin(xx * 9 + np.sin(yy * 40) * 0.6) * 0.5 + 0.5) * 0.15
    noise = g.normal(0, 1, (H // 8, W // 8)).astype(np.float32)
    noise = np.asarray(Image.fromarray(((noise * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                       np.float32) / 255
    lines = np.repeat(g.normal(0, 1, (H, 1)).astype(np.float32), W, axis=1)
    lines = np.asarray(Image.fromarray(((lines * 30) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    v = 0.55 + grain + (noise - 0.5) * 0.25 + (lines - 0.5) * 0.35
    col = np.array([0.30, 0.19, 0.11], np.float32)
    base = v[..., None] * col[None, None, :]
    rgb = (base.clip(0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB").convert("RGBA")
    return surface_from_pil(img)


@lru_cache(maxsize=2)
def photo_print(still_path, caption):
    """Build the aged print (border + photo) as a cairo surface. Uses the user's photo when provided."""
    pw, ph = 720, 540
    usr = None
    from .gfx import PHOTOS
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(PHOTOS, f"childhood.{ext}")
        if os.path.exists(p):
            usr = p
    img = Image.open(usr or still_path).convert("RGB")
    img = ImageOps.fit(img, (pw, ph), Image.LANCZOS, centering=(0.5, 0.4))
    a = np.asarray(img).astype(np.float32) / 255
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    a = a * 0.55 + lum[..., None] * 0.45
    a = a * np.array([1.08, 0.98, 0.80], np.float32) + np.array([0.06, 0.04, 0.0], np.float32)
    a = 0.08 + a * 0.86
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    d = np.sqrt(((xx - pw / 2) / (pw / 2)) ** 2 + ((yy - ph / 2) / (ph / 2)) ** 2)
    a *= (1 - 0.35 * d ** 2.4)[..., None]
    g = rng(9)
    a += g.normal(0, 0.035, a.shape).astype(np.float32)
    photo = Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(photo)
    for _ in range(22):
        x, y = g.integers(0, pw), g.integers(0, ph)
        r = g.integers(1, 3)
        dr.ellipse([x, y, x + r, y + r], fill=(235, 225, 205))
    for _ in range(4):
        x = g.integers(0, pw)
        dr.line([(x, 0), (x + g.integers(-30, 30), ph)], fill=(225, 215, 195), width=1)
    bw, top, bot = 30, 30, 120
    card_ = Image.new("RGB", (pw + 2 * bw, ph + top + bot), (236, 229, 212))
    cn = np.asarray(card_).astype(np.float32) + g.normal(0, 4, (ph + top + bot, pw + 2 * bw, 1)).astype(np.float32)
    card_ = Image.fromarray(cn.clip(0, 255).astype(np.uint8))
    card_.paste(photo, (bw, top))
    from .gfx import pil_font
    f = pil_font("caveat", 64, 600)
    ImageDraw.Draw(card_).text((bw + 26, top + ph + bot / 2), caption, font=f, fill=(48, 58, 92), anchor="lm")
    return surface_from_pil(card_.convert("RGBA"))


@lru_cache(maxsize=2)
def print_shadow(w, h):
    pad = 60
    img = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(img).rectangle([pad, pad, pad + w, pad + h], fill=170)
    img = img.filter(ImageFilter.GaussianBlur(22))
    rgba = Image.merge("RGBA", (Image.new("L", img.size, 0),) * 3 + (img,))
    return surface_from_pil(rgba)


def photo_scene(ctx, t, dur, still_path, caption):
    ctx.set_source_surface(table_texture(), 0, 0)
    ctx.paint()
    rad(ctx, W * 0.5, H * 0.45, W * 0.6, [(0, hexc("#ffcf8a"), 0.18), (1, (0, 0, 0), 0.35)])
    ctx.paint()
    pr = photo_print(still_path, caption)
    pw, ph = pr.get_width(), pr.get_height()
    s = lerp(0.98, 1.16, ease_in_out(remap(t, 0, dur + 1.5)))
    ang = math.radians(lerp(-4.0, -2.2, remap(t, 0, dur)))
    ctx.save()
    ctx.translate(W / 2, H / 2 + 10)
    ctx.scale(s, s)
    ctx.rotate(ang)
    sh = print_shadow(pw, ph)
    ctx.set_source_surface(sh, -sh.get_width() / 2 + 14, -sh.get_height() / 2 + 22)
    ctx.paint()
    ctx.set_source_surface(pr, -pw / 2, -ph / 2)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
