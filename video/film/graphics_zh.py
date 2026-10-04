"""《大起大落》的动态图形：片头、章节卡（含"心电图"曲线）、比分标题、冲击大字、点球大战、片尾。"""
import math

from .gfx import H, TAU, W, clamp, ease_in_out, ease_out, ease_out_back, glow, hexc, lerp, lin, rad, remap, smooth, text

RED = hexc("#e0262b")
GOLD = hexc("#f2c14e")
CREAM = hexc("#f6efe2")
INK = hexc("#0a0a0c")
BAR = 64


def env(t, dur, fin=0.35, fout=0.35):
    return smooth(remap(t, 0, fin)) * smooth(remap(t, dur, dur - fout))


def background(ctx, t, dur, tone="dark"):
    lin(ctx, 0, 0, 0, H, [(0, hexc("#0b0b0e")), (1, hexc("#050506"))])
    ctx.paint()
    c = {"dark": hexc("#3a0d0e"), "gold": hexc("#3a2a0e"), "cold": hexc("#0e1a2a")}[tone]
    k = 0.55 + 0.1 * math.sin(t * 1.3)
    rad(ctx, W / 2, H * 0.48, W * 0.55, [(0, c, k), (1, (0, 0, 0), 0)])
    ctx.paint()


# ------------------------------------------------------------------ the "ECG" of Chinese football
CURVE = [(1982, .46), (1985, .20), (1994, .66), (1997, .26), (2001, .98), (2002, .56), (2004, .70),
         (2009, .20), (2013, .07), (2015, .42), (2017, .60), (2021, .26), (2022, .12), (2024, .03),
         (2025, .06), (2026, .58)]
Y0, Y1 = 1980, 2027


def _cpt(year, v, box):
    x0, y0, w, h = box
    return x0 + (year - Y0) / (Y1 - Y0) * w, y0 + h - v * h


def ecg(ctx, t, upto, box, alpha=1.0, labels=True, head_glow=True):
    """Draw the rise-and-fall line up to year `upto` (animated)."""
    x0, y0, w, h = box
    ctx.set_line_width(1)
    for yr in range(1980, 2030, 5):
        x, _ = _cpt(yr, 0, box)
        ctx.set_source_rgba(1, 1, 1, 0.07 * alpha)
        ctx.move_to(x, y0)
        ctx.line_to(x, y0 + h)
        ctx.stroke()
        if labels:
            text(ctx, str(yr), x, y0 + h + 26, 20, "bebas", 400, CREAM, 0.45 * alpha, "mm", tracking=0.08)
    pts = []
    for (ya, va), (yb, vb) in zip(CURVE, CURVE[1:]):
        for i in range(24):
            u = i / 24
            yr = lerp(ya, yb, u)
            if yr > upto:
                break
            pts.append(_cpt(yr, lerp(va, vb, (1 - math.cos(u * math.pi)) / 2), box))
    if upto >= CURVE[-1][0]:
        pts.append(_cpt(*CURVE[-1], box))
    if len(pts) < 2:
        return
    for width, a in ((14, 0.12), (6, 0.3), (3, 1.0)):
        ctx.set_line_width(width)
        ctx.set_line_cap(1)
        ctx.set_line_join(1)
        lin(ctx, x0, 0, x0 + w, 0, [(0, GOLD, a * alpha), (0.5, RED, a * alpha), (1, GOLD, a * alpha)])
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.stroke()
    for yr, v in CURVE:
        if yr <= upto:
            x, y = _cpt(yr, v, box)
            ctx.set_source_rgba(*CREAM, 0.9 * alpha)
            ctx.arc(x, y, 4, 0, TAU)
            ctx.fill()
    if head_glow:
        hx, hy = pts[-1]
        glow(ctx, hx, hy, 46, RED, 0.8 * alpha)
        ctx.set_source_rgba(1, 1, 1, alpha)
        ctx.arc(hx, hy, 6, 0, TAU)
        ctx.fill()










# ------------------------------------------------------------------ particles, light, transitions
import cairo  # noqa: E402
import numpy as np  # noqa: E402

_EMBERS = np.random.default_rng(21).random((90, 6))


def embers(ctx, t, dur, n=70, color="fire", strength=1.0):
    """Rising sparks, additive."""
    a = env(t, dur, 0.6, 0.8) * strength
    if a <= 0:
        return
    cols = {"fire": [hexc("#ff8a2a"), hexc("#ffcf5a"), hexc("#ff3b2e")], "gold": [hexc("#ffd36b"), hexc("#fff0b0")]}[
        color]
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for i in range(min(n, len(_EMBERS))):
        x0, sp, ph, sz, sw, ci = _EMBERS[i]
        u = (t * (0.08 + 0.12 * sp) + ph) % 1.0
        x = x0 * W + math.sin(t * (0.6 + sw) + ph * 9) * 60
        y = H + 40 - u * (H + 120)
        r = 2 + sz * 5
        fl = 0.6 + 0.4 * math.sin(t * 9 + ph * 20)
        al = a * fl * smooth(remap(u, 0, 0.15)) * smooth(remap(u, 1.0, 0.7))
        c = cols[int(ci * len(cols))]
        glow(ctx, x, y, r * 5, c, 0.35 * al)
        ctx.set_source_rgba(*c, al)
        ctx.arc(x, y, r * 0.6, 0, TAU)
        ctx.fill()
    ctx.restore()


def leak(ctx, t, dur, warm=True):
    """Drifting warm light leaks, additive."""
    a = env(t, dur, 0.8, 0.8)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    cs = [hexc("#ff7a1a"), hexc("#ff2d2d"), hexc("#ffc04a")] if warm else [hexc("#3a7bff"), hexc("#8ad4ff")]
    for i, c in enumerate(cs):
        x = W * (0.15 + 0.7 * ((math.sin(t * 0.21 + i * 2.1) + 1) / 2))
        y = H * (0.2 + 0.6 * ((math.cos(t * 0.17 + i * 1.3) + 1) / 2))
        r = W * (0.35 + 0.1 * math.sin(t * 0.5 + i))
        rad(ctx, x, y, r, [(0, c, 0.16 * a), (1, c, 0.0)])
        ctx.paint()
    ctx.restore()


def streak(ctx, t, dur):
    """A bright light streak sweeping across (transition accent)."""
    u = ease_in_out(remap(t, 0, dur))
    x = lerp(-W * 0.3, W * 1.3, u)
    a = math.sin(math.pi * clamp(t / dur)) * 0.9
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.translate(x, H / 2)
    ctx.rotate(-0.25)
    lin(ctx, -260, 0, 260, 0, [(0, (1, 0.6, 0.3), 0), (0.45, (1, 0.8, 0.5), 0.35 * a), (0.5, (1, 1, 1), 0.9 * a),
                               (0.55, (1, 0.8, 0.5), 0.35 * a), (1, (1, 0.6, 0.3), 0)])
    ctx.rectangle(-260, -H, 520, 2 * H)
    ctx.fill()
    ctx.restore()


# ------------------------------------------------------------------ fans: chant and map
CHANT_CYCLE = 4.0
CHANT_CLAPS = (2.0, 2.5, 3.0, 3.25, 3.5)



CITIES = [("北京工体", 116.4, 39.9, True), ("沈阳五里河", 123.4, 41.8, True), ("大连金州", 121.6, 38.9, True),
          ("上海", 121.5, 31.2, True), ("广州", 113.3, 23.1, True), ("成都", 104.1, 30.7, True),
          ("重庆", 106.5, 29.6, True), ("武汉", 114.3, 30.6, False), ("西安", 108.9, 34.3, False),
          ("长沙", 112.9, 28.2, False), ("合肥", 117.3, 31.8, False), ("天津", 117.2, 39.1, False),
          ("济南", 117.0, 36.7, False), ("杭州", 120.2, 30.3, False), ("昆明", 102.7, 25.0, False),
          ("哈尔滨", 126.6, 45.8, False), ("青岛", 120.4, 36.1, False), ("深圳", 114.1, 22.5, False),
          ("南京", 118.8, 32.1, False), ("兰州", 103.8, 36.1, False), ("乌鲁木齐", 87.6, 43.8, False),
          ("长春", 125.3, 43.9, False), ("郑州", 113.6, 34.7, False), ("贵阳", 106.6, 26.6, False),
          ("南宁", 108.3, 22.8, False), ("福州", 119.3, 26.1, False), ("石家庄", 114.5, 38.0, False),
          ("太原", 112.5, 37.9, False), ("呼和浩特", 111.7, 40.8, False), ("拉萨", 91.1, 29.7, False),
          ("西宁", 101.8, 36.6, False), ("银川", 106.2, 38.5, False), ("南昌", 115.9, 28.7, False),
          ("海口", 110.3, 20.0, False)]
_MK, _MLON, _MLAT = 26.0, 106.0, 35.0


def _mp(lon, lat):
    return W / 2 + (lon - _MLON) * _MK * 0.82, H / 2 + 10 - (lat - _MLAT) * _MK


_MAPSURF = []


def _map_base():
    if _MAPSURF:
        return _MAPSURF[0]
    import json
    import os
    from .gfx import ASSETS
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    pts = json.load(open(os.path.join(ASSETS, "map_dots.json")))["points"]
    for lon, lat in pts:
        x, y = _mp(lon, lat)
        if -20 < x < W + 20 and -20 < y < H + 20:
            c.set_source_rgba(0.55, 0.42, 0.40, 0.42)
            c.arc(x, y, 3.2, 0, TAU)
            c.fill()
    _MAPSURF.append(s)
    return s


def china_map(ctx, t, dur):
    """Fan lights spreading across the country."""
    background(ctx, t, dur, "dark")
    z = lerp(1.0, 1.08, ease_in_out(remap(t, 0, dur)))
    ctx.save()
    ctx.translate(W / 2, H / 2)
    ctx.scale(z, z)
    ctx.translate(-W / 2, -H / 2)
    ctx.set_source_surface(_map_base(), 0, 0)
    ctx.paint_with_alpha(smooth(remap(t, 0, 0.6)))
    bj = _mp(116.4, 39.9)
    for i, (name, lon, lat, label) in enumerate(CITIES):
        t0 = 0.3 + (0 if i < 3 else 0.9 + (i - 3) * 0.06)
        if t < t0:
            continue
        x, y = _mp(lon, lat)
        k = remap(t, t0, t0 + 0.5)
        # link back to Beijing for the first wave
        if 0 < i and k < 1:
            ctx.set_source_rgba(*GOLD, 0.5 * (1 - k))
            ctx.set_line_width(2)
            ctx.move_to(*bj)
            ctx.line_to(lerp(bj[0], x, k), lerp(bj[1], y, k))
            ctx.stroke()
        ph = ((t - t0) * 0.8) % 1.0
        ctx.set_source_rgba(*RED, 0.6 * (1 - ph))
        ctx.set_line_width(2)
        ctx.arc(x, y, 6 + ph * (40 if label else 22), 0, TAU)
        ctx.stroke()
        glow(ctx, x, y, 60 if label else 32, RED, 0.7 * smooth(k))
        ctx.set_source_rgba(1, 0.92, 0.8, smooth(k))
        ctx.arc(x, y, 5 if label else 3.5, 0, TAU)
        ctx.fill()
        if label:
            text(ctx, name, x + 16, y - 14, 30, "sans", 700, CREAM, smooth(k), "lm", shadow=0.8)
    ctx.restore()
    a = smooth(remap(t, 1.8, 2.4)) * smooth(remap(t, dur, dur - 0.3))
    text(ctx, "每一座城市，都有为国家队呐喊的声音", W / 2, BAR + 90, 36, "sans", 600, GOLD, a, "mm", tracking=0.15,
         shadow=0.7)


# ------------------------------------------------------------------ high-impact text
from functools import lru_cache  # noqa: E402

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from .gfx import pil_font  # noqa: E402

STYLES = {
    # fill gradient (top -> bottom), outline, extrude, glow
    "gold": dict(fill=[(0, "#fff6d0"), (0.45, "#f7c64a"), (0.55, "#c9871c"), (1, "#ffe39a")],
                 outline="#2a0d05", extrude="#6b1a0c", glow="#ff9a2a"),
    "red": dict(fill=[(0, "#ffd9a8"), (0.4, "#ff4a2a"), (0.6, "#c4100f"), (1, "#ff6a3a")],
                outline="#1a0303", extrude="#4a0606", glow="#ff2a1a"),
    "silver": dict(fill=[(0, "#ffffff"), (0.48, "#dfe6ee"), (0.55, "#8d99a8"), (1, "#f2f6fa")],
                   outline="#05070a", extrude="#1c2430", glow="#8fc4ff"),
    "white": dict(fill=[(0, "#ffffff"), (1, "#f3e9d6")], outline="#120606", extrude="#3a0a08", glow="#ff5a3a"),
}


@lru_cache(maxsize=512)
def _glyph_masks(s, font, size, weight):
    """(fill, outline, glow) A8 masks for one string, plus geometry."""
    f = pil_font(font, size, weight)
    asc, desc = f.getmetrics()
    w = int(f.getlength(s)) + 1
    pad = int(size * 0.35)
    iw, ih = w + 2 * pad, asc + desc + 2 * pad
    img = Image.new("L", (iw, ih), 0)
    ImageDraw.Draw(img).text((pad, pad), s, font=f, fill=255, anchor="la")
    r = max(3, int(size * 0.055)) | 1
    out = img.filter(ImageFilter.MaxFilter(r)).filter(ImageFilter.MaxFilter(r))
    gl = out.filter(ImageFilter.GaussianBlur(size * 0.12))

    def a8(im):
        import cairo as _c
        stride = _c.ImageSurface.format_stride_for_width(_c.FORMAT_A8, iw)
        buf = np.zeros((ih, stride), np.uint8)
        buf[:, :iw] = np.asarray(im)
        return _c.ImageSurface.create_for_data(memoryview(buf), _c.FORMAT_A8, iw, ih, stride), buf

    cap = f.getbbox("国" if any(ord(ch) > 0x3000 for ch in s) else "H", anchor="ls")
    return dict(fill=a8(img), outline=a8(out), glow=a8(gl), w=w, pad=pad, asc=asc, cap=-cap[1], iw=iw, ih=ih)


def fx_text(ctx, s, x, y, size, t=10.0, style="gold", font="serif", weight=900, tracking=0.08, stagger=0.06,
            anchor="m", alpha=1.0, slam=True, depth=None, shine=True):
    """Metallic gradient text with outline, 3D extrusion, glow, light sweep and per-character slam-in."""
    if alpha <= 0.01 or not s:
        return
    st = STYLES[style]
    chars = list(s)
    ms = [_glyph_masks(ch, font, size, weight) for ch in chars]
    track = tracking * size
    total = sum(m["w"] for m in ms) + track * (len(ms) - 1)
    x0 = x - (total / 2 if anchor == "m" else 0 if anchor == "l" else total)
    depth = int(size * 0.06) if depth is None else depth
    cx = x0
    for i, (ch, m) in enumerate(zip(chars, ms)):
        ti = t - i * stagger
        if ti < 0:
            cx += m["w"] + track
            continue
        k = ease_out_back(remap(ti, 0, 0.32), 2.4) if slam else 1.0
        sc = lerp(2.8, 1.0, k) if slam else 1.0
        a = alpha * (smooth(remap(ti, 0, 0.07)) if slam else 1.0)
        gx_, gy_ = cx + m["w"] / 2, y
        ctx.save()
        ctx.translate(gx_, gy_)
        ctx.scale(sc, sc)
        ox, oy = -m["w"] / 2 - m["pad"], -(m["asc"] - m["cap"] / 2) - m["pad"]
        # glow
        ctx.set_source_rgba(*hexc(st["glow"]), 0.55 * a)
        ctx.mask_surface(m["glow"][0], ox, oy)
        # 3D extrusion
        for d in range(depth, 0, -1):
            sh_ = 0.55 + 0.45 * (1 - d / depth)
            c = hexc(st["extrude"])
            ctx.set_source_rgba(c[0] * sh_, c[1] * sh_, c[2] * sh_, a)
            ctx.mask_surface(m["outline"][0], ox + d * 0.6, oy + d)
        # outline
        ctx.set_source_rgba(*hexc(st["outline"]), a)
        ctx.mask_surface(m["outline"][0], ox, oy)
        # gradient fill
        top, h = oy + m["pad"] + m["asc"] - m["cap"], m["cap"]
        g = cairo.LinearGradient(0, top - h * 0.1, 0, top + h * 1.1)
        for off, col in st["fill"]:
            g.add_color_stop_rgba(off, *hexc(col), a)
        ctx.set_source(g)
        ctx.mask_surface(m["fill"][0], ox, oy)
        # light sweep across the glyphs
        if shine:
            u = ((t * 0.55) % 2.2) - 0.6
            sx = lerp(-total * 0.6, total * 0.6, u) - (gx_ - x)
            sg = cairo.LinearGradient(sx - size * 0.5, -size, sx + size * 0.5, size)
            sg.add_color_stop_rgba(0, 1, 1, 1, 0)
            sg.add_color_stop_rgba(0.5, 1, 1, 1, 0.7 * a)
            sg.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(sg)
            ctx.mask_surface(m["fill"][0], ox, oy)
        ctx.restore()
        cx += m["w"] + track
    return total


def shockwave(ctx, x, y, t, r_max=700, color=GOLD, width=10):
    """Expanding bright ring right after a slam."""
    if t < 0 or t > 0.6:
        return
    u = ease_out(t / 0.6)
    r = 40 + u * r_max
    a = (1 - u) ** 1.5
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for w_, aa in ((width * 4, 0.15), (width * 1.6, 0.35), (width * 0.6, 0.9)):
        ctx.set_line_width(w_ * (1 - u * 0.6))
        ctx.set_source_rgba(*color, aa * a)
        ctx.arc(x, y, r, 0, TAU)
        ctx.stroke()
    ctx.restore()


_BURST = np.random.default_rng(5).random((48, 3))


def sparks_burst(ctx, x, y, t, n=40, speed=900, color=GOLD):
    if t < 0 or t > 0.9:
        return
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for i in range(min(n, len(_BURST))):
        ang, sp, ln = _BURST[i]
        ang *= TAU
        v = speed * (0.4 + 0.6 * sp)
        d = v * t * (1 - 0.45 * t)
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d + 300 * t * t
        tail = 0.05 + 0.08 * ln
        qx, qy = x + math.cos(ang) * max(0, d - v * tail), y + math.sin(ang) * max(0, d - v * tail) + 300 * t * t
        a = (1 - t / 0.9) ** 1.2
        ctx.set_line_width(3)
        ctx.set_line_cap(1)
        ctx.set_source_rgba(*color, a)
        ctx.move_to(qx, qy)
        ctx.line_to(px, py)
        ctx.stroke()
    ctx.restore()


@lru_cache(maxsize=4)
def brush_strip(w=980, h=150, seed=3, color="#c81414"):
    """A rough red ink brush stroke (Chinese calligraphy style banner)."""
    g = np.random.default_rng(seed)
    img = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = hexc(color)
    col = tuple(int(v * 255) for v in c)
    for k in range(260):
        yy = 40 + g.normal(h / 2, h * 0.22)
        x0 = 40 + g.uniform(-20, 60)
        x1 = 40 + w - g.uniform(0, 160) * (abs(yy - 40 - h / 2) / (h / 2)) ** 1.5 - g.uniform(0, 40)
        th = int(g.uniform(2, 10))
        a = int(g.uniform(60, 160))
        d.line([(x0, yy), (x1, yy + g.normal(0, 3))], fill=col + (a,), width=th)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    arr = np.asarray(img).astype(np.float32)
    noise = g.random(arr.shape[:2]) * 0.35 + 0.75
    arr[..., 3] = np.clip(arr[..., 3] * 1.6 * noise, 0, 255)
    from .gfx import surface_from_pil
    return surface_from_pil(Image.fromarray(arr.astype(np.uint8), "RGBA"))


def brush(ctx, x, y, t, w=980, h=150, reveal=0.35, alpha=1.0, color="#c81414"):
    s = brush_strip(w, h, 3, color)
    k = ease_out(remap(t, 0, reveal))
    ctx.save()
    ctx.rectangle(x - 40, y - h / 2 - 40, (w + 80) * k, h + 80)
    ctx.clip()
    ctx.set_source_surface(s, x - 40, y - h / 2 - 40)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ------------------------------------------------------------------ light & atmosphere
def flare(ctx, t, dur, x=None, y=None, strength=1.0, color=(0.55, 0.75, 1.0)):
    """Anamorphic lens flare: long horizontal streak + ghosts."""
    a = env(t, dur, 0.4, 0.5) * strength
    if a <= 0:
        return
    x = W * (0.25 + 0.5 * ((math.sin(t * 0.35) + 1) / 2)) if x is None else x
    y = H * 0.28 if y is None else y
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    fl = 0.85 + 0.15 * math.sin(t * 13)
    glow(ctx, x, y, 180, (1, 0.95, 0.85), 0.55 * a * fl)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(1, 0.018)
    rad(ctx, 0, 0, W * 0.9, [(0, color, 0.9 * a * fl), (0.3, color, 0.35 * a), (1, color, 0)])
    ctx.arc(0, 0, W * 0.9, 0, TAU)
    ctx.fill()
    ctx.restore()
    cxs, cys = W / 2, H / 2
    for k, (f, r, col) in enumerate(((0.4, 60, (0.4, 0.9, 0.6)), (-0.3, 110, (0.9, 0.5, 1.0)),
                                     (-0.8, 40, (1.0, 0.7, 0.3)), (-1.2, 160, (0.4, 0.6, 1.0)))):
        gx_, gy_ = cxs + (cxs - x) * f, cys + (cys - y) * f
        rad(ctx, gx_, gy_, r, [(0, col, 0.0), (0.7, col, 0.10 * a), (1, col, 0)])
        ctx.arc(gx_, gy_, r, 0, TAU)
        ctx.fill()
    ctx.restore()


def rays(ctx, t, dur, x=None, y=-80, strength=1.0, color=(1.0, 0.85, 0.6)):
    """Volumetric god rays from a light above the frame."""
    a = env(t, dur, 0.6, 0.6) * strength
    x = W * 0.62 if x is None else x
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    g = np.random.default_rng(9)
    for i in range(16):
        ang = math.pi / 2 + (g.random() - 0.5) * 1.6 + math.sin(t * 0.3 + i) * 0.04
        wdt = 0.02 + g.random() * 0.06
        al = (0.04 + 0.08 * g.random()) * a * (0.7 + 0.3 * math.sin(t * (0.7 + g.random()) + i))
        L_ = H * 1.8
        ctx.move_to(x, y)
        ctx.line_to(x + math.cos(ang - wdt) * L_, y + math.sin(ang - wdt) * L_)
        ctx.line_to(x + math.cos(ang + wdt) * L_, y + math.sin(ang + wdt) * L_)
        ctx.close_path()
        lg = cairo.LinearGradient(x, y, x + math.cos(ang) * L_, y + math.sin(ang) * L_)
        lg.add_color_stop_rgba(0, *color, al)
        lg.add_color_stop_rgba(1, *color, 0)
        ctx.set_source(lg)
        ctx.fill()
    ctx.restore()


_SMOKE = []


def _smoke_tex():
    if _SMOKE:
        return _SMOKE[0]
    g = np.random.default_rng(13)
    acc = np.zeros((270, 480), np.float32)
    for oc, amp in ((8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12)):
        n = g.random((270 // (270 // oc) + 2, 480 // (270 // oc) + 2)).astype(np.float32)
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((480 * 2, 270 * 2), Image.BICUBIC).crop((0, 0, 480, 270))
        acc += np.asarray(im, np.float32) / 255 * amp
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    acc = np.clip((acc - 0.45) * 2.2, 0, 1) ** 1.4
    a = (acc * 255).astype(np.uint8)
    img = Image.merge("RGBA", (Image.fromarray(a), Image.fromarray(a), Image.fromarray(a), Image.fromarray(a)))
    img = img.resize((W * 2, H * 2), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    from .gfx import surface_from_pil
    _SMOKE.append(surface_from_pil(img))
    return _SMOKE[0]


def smoke(ctx, t, dur, strength=0.35, warm=True):
    """Drifting haze / smoke layers (screen-like add)."""
    a = env(t, dur, 0.8, 0.8) * strength
    tex = _smoke_tex()
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD if warm else cairo.OPERATOR_SCREEN)
    for k, (sp, sc) in enumerate(((22, 1.0), (-14, 1.3))):
        ctx.save()
        ox = -((t * sp + k * 400) % W)
        ctx.translate(ox, -H * 0.3 + math.sin(t * 0.2 + k) * 40)
        ctx.scale(sc, sc)
        ctx.set_source_surface(tex, 0, 0)
        ctx.get_source().set_extend(cairo.EXTEND_REPEAT)
        ctx.paint_with_alpha(a * (0.6 if k else 1.0))
        ctx.restore()
    ctx.restore()



# ------------------------------------------------------------------ titles, cards, headlines (impact versions)
def zh_title(ctx, t, dur):
    a = env(t, dur, 0.1, 1.0)
    rad(ctx, W / 2, H / 2, W * 0.6, [(0, (0, 0, 0), 0.65 * a), (1, (0, 0, 0), 0.25 * a)])
    ctx.paint()
    rays(ctx, t, dur, x=W / 2, y=-120, strength=0.9)
    st = 0.14
    for i in range(4):
        shockwave(ctx, W / 2 - 330 + i * 220, H / 2 - 40, t - i * st - 0.05, 420, RED, 8)
        sparks_burst(ctx, W / 2 - 330 + i * 220, H / 2 - 40, t - i * st - 0.05, 26, 800)
    fx_text(ctx, "大起大落", W / 2, H / 2 - 40, 230, t, "gold", "serif", 900, tracking=0.08, stagger=st,
            alpha=a)
    a2 = env(t - 0.9, dur - 0.9, 0.4, 1.0)
    brush(ctx, W / 2 - 380, H / 2 + 135, t - 0.9, 760, 86, alpha=0.95 * a2)
    text(ctx, "中国足球  1982 — 2026", W / 2, H / 2 + 136, 44, "sans", 800, CREAM, a2, "mm", tracking=0.35,
         shadow=0.8)
    flare(ctx, t, dur, x=W / 2 + 420 - t * 40, y=H / 2 - 120, strength=0.8)


def zh_card(ctx, t, dur, num, title, years, upto_from, upto_to):
    a = env(t, dur, 0.15, 0.3)
    smoke(ctx, t, dur, 0.22)
    box = (180, H * 0.62, W - 360, 200)
    upto = lerp(upto_from, upto_to, ease_in_out(remap(t, 0.2, dur - 0.5)))
    ecg(ctx, t, upto, box, 0.85 * a)
    brush(ctx, W / 2 - 150, H * 0.2, t, 300, 64, alpha=0.95 * a)
    text(ctx, num, W / 2, H * 0.2, 34, "sans", 900, CREAM, a, "mm", tracking=0.5, shadow=0.7)
    style = "red" if title in ("坠落", "崩塌") else "gold"
    n = len(title)
    sz = 170 if n <= 2 else 150
    fx_text(ctx, title, W / 2, H * 0.37, sz, t - 0.1, style, "serif", 900, tracking=0.25, stagger=0.12, alpha=a)
    for i in range(n):
        cxp = W / 2 + (i - (n - 1) / 2) * sz * 1.25
        shockwave(ctx, cxp, H * 0.37, t - 0.1 - i * 0.12, 380, RED if style == "red" else GOLD, 6)
        sparks_burst(ctx, cxp, H * 0.37, t - 0.1 - i * 0.12, 20, 650)
    a3 = smooth(remap(t, 0.5, 0.9)) * a
    text(ctx, years, W / 2, H * 0.505, 46, "bebas", 400, GOLD, a3, "mm", tracking=0.35, shadow=0.7)


def headline(ctx, t, dur, year, place, home="", hs="", as_="", away="", note=""):
    a = env(t, dur, 0.2, 0.35)
    x = 120
    y = H - BAR - 330
    lin(ctx, 0, 0, 1300, 0, [(0, (0, 0, 0), 0.65 * a), (0.6, (0, 0, 0), 0.3 * a), (1, (0, 0, 0), 0)])
    ctx.rectangle(0, y - 140, 1300, 360)
    ctx.fill()
    brush(ctx, x - 50, y - 26, t, 520 if len(str(year)) <= 4 else 720, 132, alpha=0.95 * a)
    fx_text(ctx, str(year), x, y - 26, 132, t, "gold", "bebas", 400, tracking=0.04, stagger=0.05, anchor="l",
            alpha=a, depth=6)
    shockwave(ctx, x + 140, y - 26, t, 320, GOLD, 6)
    k = ease_out(remap(t, 0.15, 0.55))
    text(ctx, place, x + 6 + 30 * (1 - k), y + 70, 42, "sans", 800, CREAM, a * k, "lm", tracking=0.1,
         shadow=0.9, shadow_blur=6)
    if home:
        a2 = env(t - 0.35, dur - 0.35, 0.25, 0.35)
        yy = y + 150
        text(ctx, home, x + 6, yy, 52, "sans", 900, CREAM, a2, "lm", shadow=0.9, shadow_blur=6)
        hw = 52 * len(home) + 40
        fx_text(ctx, f"{hs} : {as_}", x + hw, yy, 100, t - 0.35, "red" if int(str(hs)) < int(str(as_)) else "gold",
                "bebas", 400, tracking=0.05, stagger=0.04, anchor="l", alpha=a2, depth=5)
        sparks_burst(ctx, x + hw + 80, yy, t - 0.4, 22, 600)
        text(ctx, away, x + hw + 210, yy, 52, "sans", 900, CREAM, a2, "lm", shadow=0.9, shadow_blur=6)
    if note:
        a3 = env(t - 0.6, dur - 0.6, 0.3, 0.35)
        text(ctx, note, x + 6, y + (225 if home else 140), 32, "sans", 700, GOLD, a3, "lm", tracking=0.1,
             shadow=0.9)


def stamp(ctx, t, dur, text_, size=150, color="red", sub=""):
    a = env(t, dur, 0.05, 0.4)
    rad(ctx, W / 2, H / 2, W * 0.55, [(0, (0, 0, 0), 0.6 * a), (1, (0, 0, 0), 0.2 * a)])
    ctx.paint()
    style = {"red": "red", "gold": "gold", "cream": "silver"}[color]
    c = {"red": RED, "gold": GOLD, "cream": (0.7, 0.85, 1.0)}[color]
    shockwave(ctx, W / 2, H / 2 - 20, t, 900, c, 12)
    sparks_burst(ctx, W / 2, H / 2 - 20, t, 44, 1100, c)
    font = "bebas" if all(ch.isascii() for ch in text_) else "serif"
    fx_text(ctx, text_, W / 2, H / 2 - 20, size, t, style, font, 900 if font == "serif" else 400, tracking=0.08,
            stagger=0.05, alpha=a)
    if sub:
        a2 = env(t - 0.35, dur - 0.35, 0.3, 0.4)
        brush(ctx, W / 2 - 330, H / 2 + size * 0.62 + 22, t - 0.35, 660, 70, alpha=0.9 * a2)
        text(ctx, sub, W / 2, H / 2 + size * 0.62 + 22, 40, "sans", 800, CREAM, a2, "mm", tracking=0.3, shadow=0.8)


def glitch(ctx, t, dur, words):
    a = env(t, dur, 0.1, 0.4)
    n = len(words)
    for i, w_ in enumerate(words):
        ti = t - i * 0.55
        if ti < 0:
            continue
        flick = 1.0 if ti > 0.3 else (0.15 if int(ti * 40) % 2 else 1.0)
        x = W / 2 + (i - (n - 1) / 2) * 440
        jit = (math.sin(t * 53 + i) * 10) if int(t * 7 + i) % 4 == 0 else 0
        text(ctx, w_, x + jit + 7, H / 2 - 40, 150, "serif", 900, (0.1, 0.9, 1.0), 0.45 * a * flick, "mm")
        text(ctx, w_, x + jit - 7, H / 2 - 40, 150, "serif", 900, RED, 0.6 * a * flick, "mm")
        fx_text(ctx, w_, x + jit, H / 2 - 40, 150, ti + 1, "silver", "serif", 900, tracking=0.05, alpha=a * flick,
                slam=False, shine=False)
        shockwave(ctx, x, H / 2 - 40, ti, 300, RED, 6)


def shootout(ctx, t, dur):
    a = env(t, dur, 0.3, 0.5)
    k = ease_out(remap(t, 0, 0.5))
    y = H * 0.24
    lin(ctx, 0, y - 110, 0, y + 230, [(0, (0, 0, 0), 0), (0.3, (0, 0, 0), 0.65 * a), (0.7, (0, 0, 0), 0.65 * a),
                                     (1, (0, 0, 0), 0)])
    ctx.rectangle(0, y - 110, W, 340)
    ctx.fill()
    brush(ctx, W / 2 - 160, y - 50, t, 320, 62, alpha=0.95 * a)
    text(ctx, "点球大战", W / 2, y - 50, 36, "sans", 900, CREAM, a, "mm", tracking=0.6)
    fx_text(ctx, "4 : 3", W / 2, y + 60, 170, t - 0.4, "gold", "bebas", 400, tracking=0.06, stagger=0.08, alpha=a)
    shockwave(ctx, W / 2, y + 60, t - 0.4, 900, GOLD, 12)
    sparks_burst(ctx, W / 2, y + 60, t - 0.4, 48, 1200)
    text(ctx, "中国", W / 2 - 330 * k, y + 64, 64, "sans", 900, CREAM, a, "mm", shadow=0.9)
    text(ctx, "乌兹别克斯坦", W / 2 + 350 * k + 50, y + 64, 48, "sans", 800, CREAM, a * 0.9, "mm", shadow=0.9)
    a3 = env(t - 1.0, dur - 1.0, 0.4, 0.5)
    text(ctx, "门将 李昊  扑出 2 球", W / 2, y + 185, 40, "sans", 800, GOLD, a3, "mm", tracking=0.2, shadow=0.9)


def medal(ctx, t, dur):
    a = env(t, dur, 0.4, 0.8)
    k = ease_out_back(remap(t, 0, 0.7), 1.8)
    cx, cy, r = W * 0.72, H * 0.43, 150 * lerp(0.6, 1.0, k)
    rays(ctx, t, dur, x=cx, y=cy, strength=0.9, color=(1.0, 0.75, 0.45))
    glow(ctx, cx, cy, r * 2.6, hexc("#d08a45"), 0.5 * a)
    rad(ctx, cx - r * 0.3, cy - r * 0.35, r * 1.3, [(0, hexc("#f3c08a"), a), (0.55, hexc("#b8713a"), a),
                                                     (1, hexc("#6e3d18"), a)])
    ctx.arc(cx, cy, r, 0, TAU)
    ctx.fill()
    ctx.set_line_width(r * 0.06)
    ctx.set_source_rgba(1, 0.9, 0.75, 0.5 * a)
    ctx.arc(cx, cy, r * 0.82, 0, TAU)
    ctx.stroke()
    text(ctx, "铜", cx, cy, r * 0.9, "serif", 900, hexc("#5a2e10"), 0.85 * a, "mm")
    sweep = (t * 0.5) % 1.6
    if sweep < 1:
        ang = -1 + sweep * 2
        glow(ctx, cx + ang * r * 0.7, cy - ang * r * 0.4, r * 0.5, (1, 1, 1), 0.35 * a)
    fx_text(ctx, "28", W * 0.27, H * 0.40, 280, t - 0.4, "gold", "bebas", 400, tracking=0.04, stagger=0.1, alpha=a)
    shockwave(ctx, W * 0.27, H * 0.40, t - 0.4, 700, GOLD, 10)
    fx_text(ctx, "年", W * 0.27 + 190, H * 0.40 + 70, 80, t - 0.6, "white", "serif", 900, alpha=a)
    a2 = env(t - 0.9, dur - 0.9, 0.4, 0.8)
    text(ctx, "1998 曼谷  →  2026 名古屋", W * 0.27, H * 0.40 + 180, 36, "sans", 800, CREAM, a2, "mm",
         tracking=0.1, shadow=0.9)
    flare(ctx, t, dur, x=cx - r * 0.4, y=cy - r * 0.5, strength=0.7, color=(1.0, 0.7, 0.4))


def zh_end(ctx, t, dur):
    dark = 0.75 * smooth(remap(t, 0, 2.5))
    ctx.set_source_rgba(0, 0, 0, dark)
    ctx.paint()
    a = env(t - 0.8, dur - 0.8, 1.2, 1.5)
    smoke(ctx, t, dur, 0.25)
    box = (220, H * 0.62, W - 440, 160)
    ecg(ctx, t, lerp(1982, 2026, ease_in_out(remap(t, 0.5, 5.0))), box, 0.7 * a, labels=False)
    fx_text(ctx, "大起大落", W / 2, H * 0.33, 190, t - 0.8, "gold", "serif", 900, tracking=0.08, stagger=0.15,
            alpha=a)
    for i in range(4):
        shockwave(ctx, W / 2 - 290 + i * 195, H * 0.33, t - 0.8 - i * 0.15, 380, GOLD, 6)
    a2 = env(t - 2.2, dur - 2.2, 1.2, 1.5)
    brush(ctx, W / 2 - 360, H * 0.475, t - 2.2, 720, 76, alpha=0.9 * a2)
    text(ctx, "致每一个，还在等待的人", W / 2, H * 0.475, 46, "sans", 900, CREAM, a2, "mm", tracking=0.3, shadow=0.8)
    a3 = env(t - 4.0, dur - 4.0, 1.0, 1.5) * 0.5
    from .project import story
    for i, ln in enumerate(["画面：Kinetics-700 数据集公开视频片段（示意画面，非比赛原始影像）",
                            getattr(story, "MUSIC_CREDITS", "配乐：本片原创合成"),
                            "配音：Kokoro 神经网络语音  ·  音效与部分配乐：本片原创合成"]):
        text(ctx, ln, W / 2, H - BAR - 120 + i * 32, 21, "sans", 400, CREAM, a3, "mm", tracking=0.03)
    flare(ctx, t, dur, x=W * 0.2 + t * 30, y=H * 0.3, strength=0.6)


def chant(ctx, t, dur, cycles=3):
    c = int(t // CHANT_CYCLE)
    lt = t - c * CHANT_CYCLE
    if c >= cycles:
        return
    big = 1.0 + 0.1 * c
    rad(ctx, W / 2, H / 2, W * 0.6, [(0, (0, 0, 0), 0.4), (1, (0, 0, 0), 0.0)])
    ctx.paint()
    fade_out = smooth(remap(lt, CHANT_CYCLE - 0.1, CHANT_CYCLE - 0.35))
    ctx.save()
    ctx.translate(W / 2, H * 0.37)
    ctx.scale(big, big)
    fx_text(ctx, "中国队", 0, 0, 160, lt, "white", "serif", 900, tracking=0.25, stagger=0.09, alpha=fade_out)
    ctx.restore()
    shockwave(ctx, W / 2, H * 0.37, lt, 800, (0.7, 0.85, 1.0), 10)
    if lt >= 1.0:
        ctx.save()
        ctx.translate(W / 2, H * 0.63)
        ctx.scale(big, big)
        fx_text(ctx, "加油！", 0, 0, 200, lt - 1.0, "red", "serif", 900, tracking=0.2, stagger=0.08,
                alpha=fade_out)
        ctx.restore()
        shockwave(ctx, W / 2, H * 0.63, lt - 1.0, 1000, RED, 14)
        sparks_burst(ctx, W / 2, H * 0.63, lt - 1.0, 48, 1300)
    for ct in CHANT_CLAPS:
        d = lt - ct
        if 0 <= d < 0.25:
            p = (1 - d / 0.25) ** 2
            rad(ctx, W / 2, H / 2, W * 0.75, [(0, RED, 0.0), (0.65, RED, 0.0), (1, RED, 0.6 * p)])
            ctx.paint()
