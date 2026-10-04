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


def zh_card(ctx, t, dur, num, title, years, upto_from, upto_to):
    a = env(t, dur, 0.25, 0.3)
    box = (180, H * 0.60, W - 360, 220)
    upto = lerp(upto_from, upto_to, ease_in_out(remap(t, 0.2, dur - 0.5)))
    ecg(ctx, t, upto, box, 0.85 * a)
    k = ease_out_back(remap(t, 0.0, 0.5), 2.2)
    s = lerp(1.25, 1.0, k)
    text(ctx, num, W / 2, H * 0.24, 30, "sans", 600, GOLD, a, "mm", tracking=0.6)
    ctx.save()
    ctx.translate(W / 2, H * 0.37)
    ctx.scale(s, s)
    text(ctx, title, 0, 0, 132, "serif", 900, CREAM, a, "mm", tracking=0.2, shadow=0.7, shadow_blur=18,
         glow_c=RED, glow_a=0.35)
    ctx.restore()
    text(ctx, years, W / 2, H * 0.48, 40, "bebas", 400, RED, a, "mm", tracking=0.35)


def zh_title(ctx, t, dur):
    a = env(t, dur, 0.15, 1.0)
    k = ease_out_back(remap(t, 0, 0.6), 2.5)
    s = lerp(1.6, 1.0, k)
    rad(ctx, W / 2, H / 2, W * 0.6, [(0, (0, 0, 0), 0.6 * a), (1, (0, 0, 0), 0.2 * a)])
    ctx.paint()
    sh = 12 * (1 - remap(t, 0, 0.5))
    ctx.save()
    ctx.translate(W / 2 + math.sin(t * 90) * sh, H / 2 - 30 + math.cos(t * 77) * sh)
    ctx.scale(s, s)
    text(ctx, "大起大落", 0, 0, 230, "serif", 900, CREAM, a, "mm", tracking=0.12, shadow=0.8, shadow_blur=24,
         glow_c=RED, glow_a=0.5)
    ctx.restore()
    a2 = env(t - 0.6, dur - 0.6, 0.6, 1.0)
    lw = 520 * ease_in_out(remap(t, 0.5, 1.4))
    ctx.set_source_rgba(*RED, a2)
    ctx.rectangle(W / 2 - lw / 2, H / 2 + 110, lw, 4)
    ctx.fill()
    text(ctx, "中国足球  1982 — 2026", W / 2, H / 2 + 160, 40, "sans", 600, GOLD, a2, "mm", tracking=0.4)


def headline(ctx, t, dur, year, place, home="", hs="", as_="", away="", note=""):
    """Big year + place, and an optional scoreboard, in the lower-left."""
    a = env(t, dur, 0.2, 0.35)
    k = ease_out(remap(t, 0, 0.45))
    x = 130 - 80 * (1 - k)
    y = H - BAR - 330
    lin(ctx, 0, 0, 1300, 0, [(0, (0, 0, 0), 0.7 * a), (0.6, (0, 0, 0), 0.35 * a), (1, (0, 0, 0), 0)])
    ctx.rectangle(0, y - 120, 1300, 330)
    ctx.fill()
    ctx.set_source_rgba(*RED, a)
    ctx.rectangle(x - 34, y - 92, 10, 250 * k)
    ctx.fill()
    text(ctx, str(year), x, y - 30, 128, "bebas", 400, RED, a, "lm", tracking=0.04, shadow=0.6)
    text(ctx, place, x + 6, y + 50, 40, "sans", 600, CREAM, a, "lm", tracking=0.12, shadow=0.6)
    if home:
        a2 = env(t - 0.35, dur - 0.35, 0.25, 0.35)
        k2 = ease_out_back(remap(t, 0.35, 0.8), 2.0)
        yy = y + 128
        text(ctx, home, x + 6, yy, 46, "sans", 700, CREAM, a2, "lm")
        hw = 46 * len(home) + 30
        sc = f"{hs} : {as_}"
        ctx.save()
        ctx.translate(x + hw + 90, yy)
        ctx.scale(lerp(1.5, 1.0, k2), lerp(1.5, 1.0, k2))
        text(ctx, sc, 0, 0, 84, "bebas", 400, GOLD, a2, "mm", tracking=0.05, shadow=0.6)
        ctx.restore()
        text(ctx, away, x + hw + 190, yy, 46, "sans", 700, CREAM, a2, "lm")
    if note:
        a3 = env(t - 0.6, dur - 0.6, 0.3, 0.35)
        text(ctx, note, x + 6, y + 190 if home else y + 110, 30, "sans", 500, GOLD, a3, "lm", tracking=0.1)


def stamp(ctx, t, dur, text_, size=150, color="red", sub=""):
    """Centre-screen impact text that slams in."""
    a = env(t, dur, 0.08, 0.4)
    k = ease_out_back(remap(t, 0, 0.35), 2.8)
    s = lerp(2.2, 1.0, k)
    rad(ctx, W / 2, H / 2, W * 0.55, [(0, (0, 0, 0), 0.55 * a), (1, (0, 0, 0), 0.15 * a)])
    ctx.paint()
    c = {"red": RED, "gold": GOLD, "cream": CREAM}[color]
    sh = 16 * (1 - remap(t, 0.0, 0.4))
    ctx.save()
    ctx.translate(W / 2 + math.sin(t * 97) * sh, H / 2 - 20 + math.cos(t * 83) * sh)
    ctx.scale(s, s)
    font = "bebas" if all(ch.isascii() for ch in text_) else "serif"
    text(ctx, text_, 0, 0, size, font, 900, c, a, "mm", tracking=0.08, shadow=0.8, shadow_blur=20,
         glow_c=c, glow_a=0.3)
    ctx.restore()
    if sub:
        a2 = env(t - 0.3, dur - 0.3, 0.3, 0.4)
        text(ctx, sub, W / 2, H / 2 + size * 0.62 + 20, 40, "sans", 600, CREAM, a2, "mm", tracking=0.3, shadow=0.6)


def glitch(ctx, t, dur, words):
    """Words flicker in like a bad signal: 假球 · 黑哨 · 赌球."""
    a = env(t, dur, 0.1, 0.4)
    n = len(words)
    for i, w_ in enumerate(words):
        ti = t - i * 0.55
        if ti < 0:
            continue
        flick = 1.0 if ti > 0.3 else (0.2 if int(ti * 40) % 2 else 1.0)
        x = W / 2 + (i - (n - 1) / 2) * 420
        dx = (math.sin(t * 53 + i) * 6) if int(t * 7 + i) % 5 == 0 else 0
        text(ctx, w_, x + dx + 4, H / 2 - 40, 140, "serif", 900, (0.1, 0.8, 0.9), 0.35 * a * flick, "mm")
        text(ctx, w_, x + dx - 4, H / 2 - 40, 140, "serif", 900, RED, 0.5 * a * flick, "mm")
        text(ctx, w_, x + dx, H / 2 - 40, 140, "serif", 900, CREAM, a * flick, "mm", shadow=0.7)


def shootout(ctx, t, dur):
    """Penalty shoot-out result board."""
    a = env(t, dur, 0.3, 0.5)
    k = ease_out(remap(t, 0, 0.5))
    y = H * 0.22
    lin(ctx, 0, y - 90, 0, y + 200, [(0, (0, 0, 0), 0), (0.3, (0, 0, 0), 0.6 * a), (0.7, (0, 0, 0), 0.6 * a),
                                    (1, (0, 0, 0), 0)])
    ctx.rectangle(0, y - 90, W, 290)
    ctx.fill()
    text(ctx, "点球大战", W / 2, y - 40, 34, "sans", 700, GOLD, a, "mm", tracking=0.6)
    kk = ease_out_back(remap(t, 0.4, 0.9), 2.4)
    ctx.save()
    ctx.translate(W / 2, y + 60)
    ctx.scale(lerp(1.8, 1.0, kk), lerp(1.8, 1.0, kk))
    text(ctx, "4 : 3", 0, 0, 150, "bebas", 400, CREAM, a * smooth(remap(t, 0.4, 0.6)), "mm", tracking=0.06,
         shadow=0.7, glow_c=RED, glow_a=0.35)
    ctx.restore()
    text(ctx, "中国", W / 2 - 300 * k, y + 64, 56, "sans", 800, CREAM, a, "mm")
    text(ctx, "乌兹别克斯坦", W / 2 + 330 * k + 40, y + 64, 44, "sans", 700, CREAM, a * 0.85, "mm")
    a3 = env(t - 1.0, dur - 1.0, 0.4, 0.5)
    text(ctx, "门将 李昊  扑出 2 球", W / 2, y + 170, 36, "sans", 600, GOLD, a3, "mm", tracking=0.2)


def medal(ctx, t, dur):
    """Bronze medal with '28 年'."""
    a = env(t, dur, 0.4, 0.8)
    k = ease_out_back(remap(t, 0, 0.7), 1.8)
    cx, cy, r = W * 0.72, H * 0.43, 150 * lerp(0.6, 1.0, k)
    glow(ctx, cx, cy, r * 2.4, hexc("#d08a45"), 0.45 * a)
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
    a2 = env(t - 0.5, dur - 0.5, 0.5, 0.8)
    text(ctx, "28", W * 0.30, H * 0.40, 260, "bebas", 400, GOLD, a2, "mm", glow_c=GOLD, glow_a=0.25, shadow=0.7)
    text(ctx, "年", W * 0.30 + 175, H * 0.40 + 70, 70, "serif", 900, CREAM, a2, "mm")
    text(ctx, "1998 曼谷  →  2026 名古屋", W * 0.30, H * 0.40 + 170, 34, "sans", 600, CREAM, a2 * 0.9, "mm",
         tracking=0.1)


def zh_end(ctx, t, dur):
    dark = 0.75 * smooth(remap(t, 0, 2.5))
    ctx.set_source_rgba(0, 0, 0, dark)
    ctx.paint()
    a = env(t - 0.8, dur - 0.8, 1.2, 1.5)
    box = (220, H * 0.60, W - 440, 170)
    ecg(ctx, t, lerp(1982, 2026, ease_in_out(remap(t, 0.5, 5.0))), box, 0.7 * a, labels=False)
    text(ctx, "大起大落", W / 2, H * 0.34, 170, "serif", 900, CREAM, a, "mm", tracking=0.12, glow_c=RED,
         glow_a=0.35, shadow=0.7)
    a2 = env(t - 2.2, dur - 2.2, 1.2, 1.5)
    text(ctx, "致每一个，还在等待的人", W / 2, H * 0.47, 46, "sans", 600, GOLD, a2, "mm", tracking=0.3)
    a3 = env(t - 4.0, dur - 4.0, 1.0, 1.5) * 0.5
    for i, ln in enumerate(["画面：Kinetics-700 数据集公开视频片段（示意画面，非比赛原始影像）",
                            "配音：Kokoro 神经网络语音  ·  配乐：本片原创合成"]):
        text(ctx, ln, W / 2, H - BAR - 96 + i * 34, 22, "sans", 400, CREAM, a3, "mm", tracking=0.05)


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


def chant(ctx, t, dur, cycles=3):
    """'中国队 加油!' kinetic type in time with the chant and claps."""
    c = int(t // CHANT_CYCLE)
    lt = t - c * CHANT_CYCLE
    if c >= cycles:
        return
    big = 1.0 + 0.12 * c
    rad(ctx, W / 2, H / 2, W * 0.6, [(0, (0, 0, 0), 0.35), (1, (0, 0, 0), 0.0)])
    ctx.paint()
    # 中国队
    a1 = smooth(remap(lt, 0, 0.06)) * smooth(remap(lt, CHANT_CYCLE - 0.1, CHANT_CYCLE - 0.35))
    k1 = ease_out_back(remap(lt, 0, 0.3), 3.0)
    ctx.save()
    ctx.translate(W / 2, H * 0.38)
    s = lerp(2.4, 1.0, k1) * big
    ctx.scale(s, s)
    text(ctx, "中国队", 0, 0, 150, "serif", 900, CREAM, a1, "mm", tracking=0.25, shadow=0.8, shadow_blur=20,
         glow_c=RED, glow_a=0.5)
    ctx.restore()
    # 加油！
    a2 = smooth(remap(lt, 1.0, 1.06)) * smooth(remap(lt, CHANT_CYCLE - 0.1, CHANT_CYCLE - 0.35))
    k2 = ease_out_back(remap(lt, 1.0, 1.3), 3.0)
    if a2 > 0:
        ctx.save()
        ctx.translate(W / 2, H * 0.62)
        s = lerp(2.6, 1.0, k2) * big
        ctx.scale(s, s)
        text(ctx, "加油！", 0, 0, 190, "serif", 900, RED, a2, "mm", tracking=0.2, shadow=0.8, shadow_blur=20,
             glow_c=GOLD, glow_a=0.4)
        ctx.restore()
    # claps: red edge pulses
    for ct in CHANT_CLAPS:
        d = lt - ct
        if 0 <= d < 0.25:
            p = (1 - d / 0.25) ** 2
            rad(ctx, W / 2, H / 2, W * 0.75, [(0, RED, 0.0), (0.65, RED, 0.0), (1, RED, 0.55 * p)])
            ctx.paint()


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
