"""《前进》剪辑表：只讲赛场上的拼搏与胜利、更衣室、采访和球迷。无旁白、不分章节。

Segment options used here (see engine): snd = gain of the clip's own sound (0 = silent),
stem = "voc" to use the vocals/crowd stem separated from a clip that has background music baked in.
"""
from .edit import BLACK, S  # noqa: F401

LIVE = dict(temp=0.03, sat=1.12, contrast=1.10, lift=0.01, grain=0.02, vignette=0.40)
GLORY = dict(temp=0.07, sat=1.18, contrast=1.12, tint_red=0.05, grain=0.02, vignette=0.42)
OLD = dict(temp=0.05, sat=1.0, contrast=1.08, lift=0.02, grain=0.035, vignette=0.45)
P = 0.06


def R(bv, a, b=None, **kw):
    """Real clip at normal speed with its own sound on by default."""
    kw.setdefault("snd", 1.0)
    return S(bv, a, b, **kw)


def HL(at, year, place, home="", hs="", as_="", away="", note="", until="end-0.3"):
    return ("headline", at, until, dict(year=year, place=place, home=home, hs=hs, as_=as_, away=away, note=note))


SHOTS = [
    # ---- cold open: U17 half-time team talk (real voice) -> "前进"
    dict(id="talk", min=30.0, look=LIVE,
         segs=[R("BV1rWVw6rEPQ", 1.0, 31.0, stem="voc", snd=1.3, zoom=(1.0, 1.08))],
         overlays=[("smoke", 0, "end", dict(strength=0.15))],
         events=[("end-2.6", "riser:2.6", 0.8)]),
    dict(id="tunnel", min=13.0, look=GLORY,
         segs=[S("BV1SF4m1A7LG", 0.0, 6.5, zoom=(1.05, 1.1)), S("BV1SF4m1A7LG", 8.0, 14.0, zoom=(1.05, 1.08), tin="whip")],
         overlays=[("flash", 0.0, 0.4, {}), ("zh_title", 0.0, "end", dict(title="中国队 前进", sub="中国男足 · 赛场上的每一次胜利")),
                   ("rays", 0, "end", dict(strength=0.7))],
         events=[(0.0, "impact", 1.0)]),
    dict(id="anthem", min=17.0, look=GLORY,
         segs=[S("BV1SF4m1A7LG", 42.0, 50.0, tin="zoom"), S("BV1SF4m1A7LG", 54.0, 63.0, tin="burn")],
         overlays=[HL(0.4, 2002, "韩日世界杯 · 中国男足第一次站上世界杯舞台", until="end-0.4")],
         audio=[("BV1MRo4YgESk", 0.0, 0.0, 14.0, 1.0, None), ("BV1MRo4YgESk", 14.0, 60.0, 3.0, 0.8, None)],
         events=[(0.4, "impact", 0.7)]),
    # ---- 2001 五里河
    dict(id="wulihe", min=46.0, look=OLD,
         segs=[R("BV1zG411c7Et", 8.0, 16.0, stem="voc", snd=1.2, tin="spin"),
               R("BV1zG411c7Et", 17.5, 20.5, stem="voc", tin="burn"),
               R("BV1A3411u7P6", 14.0, 27.0, snd=1.4, tin="whip"),
               R("BV1A3411u7P6", 48.0, 56.0, snd=1.4, tin="zoom"),
               R("BV1zG411c7Et", 28.0, 34.0, stem="voc", snd=1.2, tin="glitch"),
               R("BV1A3411u7P6", 96.0, 104.0, snd=1.3, tin="whip_v"),
               R("BV11JZHYQEG1", 0.0, 9.0, fit="contain", stem="voc", snd=1.3, tin="burn")],
         overlays=[HL(0.3, 2001, "10月7日 · 沈阳五里河 · 十强赛", "中国", 1, 0, "阿曼", note="于根伟破门  提前两轮出线",
                      until=14.0),
                   ("stamp", 8.2, 10.6, dict(text_="出线了！", size=170, color="gold")),
                   ("caption", 46.3, "end-0.3", dict(text="米卢重逢2002一代国脚，泪洒当场"))],
         events=[(8.2, "impact", 1.0), (11.0, "crowd_roar", 0.5)]),
    # ---- 2004 亚洲杯半决赛
    dict(id="jinan", min=24.0, look=LIVE,
         segs=[R("BV1td4y1P7Wv", 397.0, 407.0, stem="voc", snd=1.2),
               R("BV1td4y1P7Wv", 420.0, 434.0, stem="voc", snd=1.4, tin="zoom")],
         overlays=[HL(0.3, 2004, "亚洲杯半决赛 · 北京工人体育场", note="点球大战  淘汰伊朗  闯进决赛", until=12.0),
                   ("stamp", 17.0, "end-0.2", dict(text_="闯进决赛！", size=160, color="gold"))],
         events=[(15.5, "riser:1.5", 0.5), (17.0, "impact", 1.0)]),
    # ---- 2016 西安
    dict(id="xian", min=30.0, look=LIVE,
         segs=[R("BV12W411f7WK", 103.0, 113.0, snd=1.3, tin="whip"),
               R("BV12W411f7WK", 114.0, 120.0, snd=1.3, tin="glitch"),
               R("BV12W411f7WK", 189.0, 199.0, snd=1.3, tin="zoom"),
               R("BV12W411f7WK", 212.0, 220.0, snd=1.4, tin="whip_v")],
         overlays=[HL(0.3, 2016, "3月29日 · 西安 · 世预赛", "中国", 2, 0, "卡塔尔", note="生死战取胜  奇迹晋级十二强赛",
                      until=12.0),
                   ("stamp", 26.0, "end-0.2", dict(text_="奇迹晋级！", size=160, color="gold"))],
         events=[(26.0, "impact", 1.0)]),
    # ---- 2017 长沙
    dict(id="changsha", min=40.0, look=LIVE,
         segs=[S("BV1dV4y1j7Y6", 0.0, 7.0, tin="spin", snd=0.0),
               R("BV1EN4y1m7KV", 78.0, 92.0, snd=1.3, tin="whip"),
               R("BV1dV4y1j7Y6", 51.0, 59.0, stem="voc", snd=1.2, tin="zoom"),
               R("BV1EN4y1m7KV", 193.0, 202.0, snd=1.3, tin="glitch"),
               R("BV1dV4y1j7Y6", 229.0, 241.0, stem="voc", snd=1.3, tin="burn")],
         overlays=[HL(0.3, 2017, "3月23日 · 长沙 · 世预赛", "中国", 1, 0, "韩国", note="于大宝头球破门", until=11.6),
                   ("stamp", 12.0, 15.2, dict(text_="1 : 0", size=200, color="gold"))],
         events=[(0.3, "impact", 0.8), (12.0, "impact", 1.0)]),
    # ---- 2026 U23亚洲杯
    dict(id="u23", min=34.0, look=LIVE,
         segs=[R("BV1RyrQBBEu6", 303.0, 313.0, snd=1.3, tin="burn"),
               R("BV1RyrQBBEu6", 358.0, 380.0, snd=1.4, tin="zoom"),
               R("BV1GDHq6JE4J", 56.0, 64.0, stem="voc", snd=1.3, tin="whip")],
         overlays=[HL(0.3, 2026, "1月 · U23亚洲杯 · 点球淘汰乌兹别克斯坦", note="一路杀进决赛  夺得亚军", until=12.0),
                   ("stamp", 12.2, 15.5, dict(text_="进四强！", size=160, color="gold"))],
         events=[(12.2, "impact", 1.0)]),
    # ---- 2026 亚运会铜牌（高潮）
    dict(id="bronze", min=60.0, look=GLORY,
         segs=[R("BV1qQHa6VEAs", 108.0, 114.0, stem="voc", snd=1.2, tin="whip"),
               R("BV1qQHa6VEAs", 146.0, 152.0, stem="voc", snd=1.2, tin="zoom"),
               R("BV1eAHv6CEa4", 74.0, 80.0, stem="voc", snd=1.3, tin="glitch"),
               R("BV1qQHa6VEAs", 243.0, 266.0, stem="voc", snd=1.4, tin="spin"),
               R("BV1qQHa6VEAs", 276.0, 283.0, stem="voc", snd=1.4, tin="burn"),
               R("BV1eAHv6CEa4", 428.0, 440.0, stem="voc", snd=1.3, tin="whip")],
         overlays=[HL(0.3, 2026, "10月3日 · 名古屋亚运会 · 铜牌战", "中国", 2, 2, "乌兹别克斯坦",
                      note="胡荷韬破门  王钰栋世界波", until=11.5),
                   ("shootout", 38.5, 48.5, {}),
                   ("medal", 48.5, "end-0.3", {}), ("embers", 41, "end", dict(color="gold"))],
         events=[(18.0, "heartbeat", 0.6), (38.3, "riser:1.6", 0.6), (38.5, "impact", 1.0), (48.5, "impact", 1.0)]),
    # ---- 更衣室 + 采访
    dict(id="locker", min=34.0, look=LIVE,
         segs=[R("BV1N3Hk6HEU5", 10.0, 28.0, snd=1.0),
               R("BV1jKHj6fEco", 38.0, 48.0, stem="voc", snd=1.3, tin="whip"),
               R("BV1A2Hi6PE8E", 42.0, 50.0, snd=1.0, tin="zoom")],
         overlays=[("caption", 0.5, 8.0, dict(text="名古屋 · 赛后更衣室")),
                   ("caption", 18.5, 27.0, dict(text="主帅安东尼奥：中国足球人需要好消息"))]),
    # ---- 球迷
    dict(id="fans", min=40.0, look=GLORY,
         segs=[R("BV12R4WeqEqe", 12.0, 30.0, snd=1.4),
               R("BV12R4WeqEqe", 34.0, 46.0, snd=1.5, tin="whip"),
               R("BV12R4WeqEqe", 112.0, 122.0, stem="voc", snd=1.4, tin="zoom")],
         overlays=[("chant", 30.0, "end", dict(cycles=2)), ("embers", 0, "end", dict(n=90))],
         events=[(30.0, "impact", 1.0)]),
    # ---- 结尾
    dict(id="end", min=20.0, xf=0.0, look=GLORY,
         segs=[R("BV1A3411u7P6", 246.0, 266.0, snd=1.0, zoom=(1.0, 1.08))],
         overlays=[("victory_end", 1.0, "end", {})],
         events=[(1.0, "impact", 0.8)]),
]

DEFAULTS = dict(min=3.0, lead=0.0, gap=0.0, tail=0.0, xf=0.0)
