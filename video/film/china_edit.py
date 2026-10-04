"""《大起大落》剪辑表。时间可写成 "a1"(该句开始) / "a1.end" / "end" 加减偏移。"""
from .edit import BLACK, FREEZE, S  # noqa: F401

HYPE = dict(temp=0.04, sat=1.15, contrast=1.14, lift=0.01, grain=0.03, vignette=0.45)
GLORY = dict(temp=0.08, sat=1.22, contrast=1.16, tint_red=0.08, grain=0.03, vignette=0.45)
BW = dict(sat=0.0, contrast=1.18, lift=0.05, grain=0.07, vignette=0.55, fade=0.04)
OLD = dict(temp=0.12, sat=0.35, contrast=1.08, lift=0.06, grain=0.06, vignette=0.5, fade=0.06)
COLD = dict(temp=-0.10, sat=0.55, contrast=1.1, lift=0.02, grain=0.045, vignette=0.55)
DESAT = dict(sat=0.22, contrast=1.12, lift=0.03, grain=0.05, vignette=0.6)
P = 0.07  # punch-in on hard cuts


def card(num, title, years, upto, tone="dark", music=None, upfrom=None):
    return dict(id="card", min=3.4, xf=0.0, tin="zoom", segs=[dict(kind="bg", tone=tone)], look=dict(grain=0.03),
                overlays=[("zh_card", 0, "end", dict(num=num, title=title, years=years,
                                                     upto_from=upfrom or upto - 3, upto_to=upto)),
                          ("streak", 0.0, 0.7, {}), ("embers", 0, "end", dict(n=30, strength=0.6))],
                events=[(0.02, "impact", 0.9)], music=music, music_at=0.0, music_fade=0.05)


def HL(at, year, place, home="", hs="", as_="", away="", note="", until="end-0.2"):
    return ("headline", at, until, dict(year=year, place=place, home=home, hs=hs, as_=as_, away=away, note=note))


SHOTS = [
    # ------------------------------------------------------------------ cold open
    dict(id="cold", lines=["o1", "o2"], lead=0.6, gap=0.5, tail=4.8, min=10.0, xf=0.2,
         segs=[S("bw_match", 0.0, 1.3, look=BW, punch=P), S("crowd_sea", 0.5, 1.5, look=HYPE, punch=P),
               S("keeper_dive", 4.2, 5.0, speed=0.5, look=COLD, punch=P, zoom=(1.18, 1.22), focus=(0.45, 0.55)),
               S("sad_man", 0.6, 1.6, look=OLD, punch=P), S("fans_night", 6.0, 7.1, look=GLORY, punch=P),
               S("tvgol", 3.4, 4.3, look=HYPE, punch=P, zoom=(1.4, 1.46), focus=(0.42, 0.48)), S("fist_stand", 3.6, 4.6, look=HYPE, punch=P),
               S("confetti", 0.6, speed=0.8, fill=True, look=GLORY, zoom=(1.0, 1.1))],
         overlays=[("embers", 0, "end", {}), ("leak", 0, "end", {}), ("flash", "o2.end+0.15", "o2.end+0.6", {}), ("zh_title", "o2.end+0.15", "end", {})],
         events=[("o2.end+0.15", "riser:2.5", 0.7), ("o2.end+0.15", "impact", 1.0)]),

    # ------------------------------------------------------------------ 一 梦起
    card("第一章", "梦起", "1982 — 1985", 1985.5, music="tension", upfrom=1980),
    dict(id="a1", lines=["a1"], lead=0.3, tail=1.0,
         segs=[S("bw_match", 0.0, 3.6, speed=0.8, look=BW, zoom=(1.02, 1.1)),
               S("night_dirt", 0.5, fill=True, look=OLD, zoom=(1.0, 1.08), punch=P)],
         overlays=[HL("a1+0.2", 1982, "世界杯预选赛附加赛 · 新加坡", "中国", 1, 2, "新西兰")],
         events=[("a1+0.2", "impact", 0.7)]),
    dict(id="a2", lines=["a2"], lead=0.2, tail=2.2,
         segs=[S("bw_crowd", 5.0, 7.4, look=BW, punch=P), S("sad_man", 0.6, 4.2, look=OLD, punch=P),
               S("night_dirt", 3.0, fill=True, look=OLD, zoom=(1.08, 1.16))],
         overlays=[HL("a2+0.2", 1985, "5月19日 · 北京工人体育场", "中国", 1, 2, "香港", note="只需战平即可出线",
                      until="a2.end"),
                   ("stamp", "a2.end+0.1", "end", dict(text_="5 · 19", size=200))],
         events=[("a2+0.2", "impact", 0.7), ("a2.end+0.1", "impact", 1.0)]),

    # ------------------------------------------------------------------ 二 春天
    card("第二章", "春天", "1994 — 1997", 1997.5, tone="gold", music="hope", upfrom=1986),
    dict(id="b1", lines=["b1"], lead=0.2, tail=0.8, look=HYPE,
         segs=[S("crowd_hands", 0.0, 2.2, punch=P), S("stadium_lights", 4.4, 6.6, punch=P),
               S("fans_stadium", 1.0, 2.8, punch=P), S("youth_match", 0.0, fill=True, zoom=(1.02, 1.1))],
         overlays=[HL("b1+0.2", 1994, "甲A联赛 · 职业化元年")],
         events=[("b1+0.2", "impact", 0.6)]),
    dict(id="b2", lines=["b2", "b3"], lead=0.2, gap=0.6, tail=2.0,
         segs=[S("bcast_wide", 5.2, 7.8, look=HYPE, punch=P), S("tvgol", 0.0, 2.4, look=HYPE, zoom=(1.4, 1.46), focus=(0.42, 0.48)),
               S("keeper_dive", 4.0, 5.6, speed=0.5, look=COLD, punch=P, zoom=(1.18, 1.22), focus=(0.45, 0.55)),
               S("bcast_keeper", 0.0, 2.3, speed=0.5, look=COLD, punch=P),
               S("sad_man", 4.4, fill=True, look=COLD, zoom=(1.06, 1.14))],
         overlays=[HL("b2+0.2", 1997, "9月13日 · 大连金州 · 十强赛首战", "中国", 2, 4, "伊朗", until="b2.end"),
                   ("stamp", "b3", "end", dict(text_="金州，不相信眼泪", size=110, color="cream"))],
         events=[("b2+0.2", "impact", 0.7), ("b2+3.6", "mood:dark", 1), ("b2+3.6", "boom", 0.8),
                 ("b3", "impact", 1.0)]),

    # ------------------------------------------------------------------ 三 巅峰
    card("第三章", "巅峰", "2001 — 2004", 2004.5, tone="gold", music="build", upfrom=1998),
    dict(id="c1", lines=["c1", "c2"], lead=0.2, gap=0.3, tail=2.6, look=GLORY,
         segs=[S("tvgol", 0.0, 5.2, speed=0.95, look=HYPE, zoom=(1.4, 1.46), focus=(0.42, 0.48)),
               S("confetti", 0.4, 3.0, punch=0.12), S("fans_night", 5.2, 7.4, punch=P),
               S("crowd_sea", 0.0, 2.4, punch=P), S("fist_stand", 1.0, fill=True, zoom=(1.0, 1.08))],
         overlays=[("embers", 0, "end", {}), ("leak", 0, "end", {}), HL("c1+0.2", 2001, "10月7日 · 沈阳五里河", "中国", 1, 0, "阿曼", until="c1.end"),
                   ("flash", "c1.end", "c1.end+0.5", {}),
                   ("stamp", "c2+0.1", "end", dict(text_="44 年", size=210, color="gold", sub="首次闯进世界杯"))],
         events=[("c1+0.2", "impact", 0.6), ("c1.end", "riser:2.0", 0.6), ("c1.end", "mood:heroic", 1),
                 ("c1.end", "impact", 1.0), ("c1.end", "crowd_roar", 0.7)]),
    dict(id="c3", lines=["c3"], lead=0.2, tail=1.0,
         segs=[S("yellow_red", 3.0, 7.6, speed=0.8, look=HYPE, punch=P, zoom=(1.2, 1.26), focus=(0.55, 0.55)),
               S("bcast_netgoal", 3.8, 5.6, look=HYPE, punch=P),
               S("stadium_crowd", 0.0, fill=True, speed=0.7, look=dict(HYPE, sat=0.7), zoom=(1.0, 1.08))],
         overlays=[HL("c3+0.2", 2002, "韩日世界杯", note="3战全负 · 0进球 · 失9球")],
         events=[("c3+0.2", "impact", 0.6)]),
    dict(id="c4", lines=["c4"], lead=0.2, tail=1.4,
         segs=[S("bcast_ucl", 0.0, 3.0, look=HYPE, punch=P, zoom=(1.36, 1.42), focus=(0.42, 0.45)), S("red_hug", 5.0, 9.4, look=HYPE, punch=P, zoom=(1.3, 1.36), focus=(0.5, 0.4)),
               S("sad_man", 6.0, fill=True, look=COLD)],
         overlays=[HL("c4+0.2", 2004, "亚洲杯决赛 · 北京工人体育场", "中国", 1, 3, "日本")],
         events=[("c4+0.2", "impact", 0.7)]),

    # ------------------------------------------------------------------ 四 坠落
    card("第四章", "坠落", "2009 — 2013", 2013.5, tone="cold", music="dark", upfrom=2005),
    dict(id="d1", lines=["d1"], lead=0.2, tail=0.8, look=DESAT,
         segs=[S("bcast_wide", 5.2, 7.4, punch=P), S("bw_crowd", 5.0, 7.0, look=BW, punch=P),
               S("tv_epl", 1.0, 3.0, punch=P), S("sad_man", 0.0, fill=True, zoom=(1.05, 1.15))],
         overlays=[("glitch", "d1+0.1", "d1+4.2", dict(words=("假球", "黑哨", "赌球")))],
         events=[("d1+0.1", "boom", 0.8), ("d1+0.65", "boom", 0.8), ("d1+1.2", "boom", 0.8)]),
    dict(id="d2", lines=["d2"], lead=0.2, tail=1.6, look=DESAT,
         segs=[S("stadium_crowd", 4.0, 6.2, speed=0.7, punch=P), S("far_field", 2.0, 4.0, punch=P),
               S("lone_ball", 2.0, fill=True, speed=0.6, zoom=(1.1, 1.0))],
         overlays=[HL("d2+0.2", 2013, "6月15日 · 合肥", "中国", 1, 5, "泰国")],
         events=[("d2+0.2", "impact", 0.8)]),

    # ------------------------------------------------------------------ 五 狂潮
    card("第五章", "狂潮", "2013 — 2019", 2019.5, tone="gold", music="drive", upfrom=2013),
    dict(id="e1", lines=["e1"], lead=0.2, tail=0.6, look=HYPE,
         segs=[S("tv_espn", 0.0, 2.4, punch=P), S("bcast_ucl", 0.0, 2.6, punch=P, zoom=(1.36, 1.42), focus=(0.42, 0.45)),
               S("freekick", 4.0, 6.2, punch=P, zoom=(1.28, 1.32), focus=(0.45, 0.45)), S("stadium_crowd", 0.0, fill=True, zoom=(1.0, 1.08))],
         overlays=[HL("e1+0.2", "2013 · 2015", "广州恒大 · 两夺亚冠")],
         events=[("e1+0.2", "impact", 0.6)]),
    dict(id="e2", lines=["e2"], lead=0.2, tail=1.2, look=HYPE,
         segs=[S("bcast_run", 0.0, 3.4, look=HYPE), S("confetti", 0.4, 2.6, punch=0.12, look=GLORY),
               S("fist_stand", 1.0, fill=True, look=GLORY)],
         overlays=[HL("e2+0.2", 2017, "3月23日 · 长沙", "中国", 1, 0, "韩国"),
                   ("flash", "e2+3.4", "e2+3.9", {})],
         events=[("e2+0.2", "impact", 0.6), ("e2+3.4", "impact", 0.9), ("e2+3.4", "crowd_roar", 0.5)]),

    # ------------------------------------------------------------------ 六 崩塌
    card("第六章", "崩塌", "2021 — 2025", 2025.5, tone="cold", music="dark", upfrom=2019),
    dict(id="f1", lines=["f1"], lead=0.2, tail=1.8, look=DESAT,
         segs=[S("stadium_crowd", 0.0, 2.0, punch=P), S("far_field", 0.0, 3.0, punch=P),
               S("lone_ball", 2.0, fill=True, speed=0.6, zoom=(1.0, 1.12))],
         overlays=[HL("f1+3.0", 2021, "江苏苏宁 · 中超冠军", until="f1.end"),
                   ("stamp", "f1.end+0.05", "end", dict(text_="停止运营", size=150))],
         events=[("f1+3.0", "impact", 0.6), ("f1.end+0.05", "impact", 1.0)]),
    dict(id="f2", lines=["f2"], lead=0.2, tail=1.0, look=DESAT,
         segs=[S("bcast_keeper", 0.0, 2.3, speed=0.6, punch=P), S("sad_man", 2.0, fill=True, zoom=(1.0, 1.1))],
         overlays=[HL("f2+0.2", 2022, "大年初一", "中国", 1, 3, "越南")],
         events=[("f2+0.2", "impact", 0.8)]),
    dict(id="f3", lines=["f3"], lead=0.2, tail=1.8, look=GLORY,
         segs=[S("feet_dribble", 0.6, 2.4, punch=P), S("fans_german", 0.0, 2.6, punch=P, zoom=(1.4, 1.45), focus=(0.5, 0.5)),
               S("confetti", 2.0, 4.6, punch=P), S("fans_night", 6.0, fill=True, zoom=(1.0, 1.08))],
         overlays=[("embers", 0, "end", {}), ("leak", 0, "end", {}), HL("f3+0.2", 2022, "2月6日 · 亚洲杯决赛", "中国女足", 3, 2, "韩国", note="0比2落后  连扳三球")],
         events=[("f3", "mood:heroic", 1), ("f3", "impact", 1.0), ("f3.end", "crowd_roar", 0.5)]),
    dict(id="f4", lines=["f4"], lead=0.2, tail=1.2, look=DESAT,
         segs=[S("keeper_dive", 6.8, 8.6, speed=0.6, punch=P, zoom=(1.18, 1.22), focus=(0.45, 0.55)), S("bw_crowd", 5.0, 7.0, look=BW, punch=P),
               S("sad_man", 2.0, fill=True, zoom=(1.0, 1.1))],
         overlays=[HL("f4+0.2", 2024, "9月 · 世预赛18强赛", "中国", 0, 7, "日本", until="f4+3.4"),
                   ("stamp", "f4+3.5", "end", dict(text_="20 年", size=190, sub="前国足主帅李铁获刑"))],
         events=[("f4", "mood:dark", 1), ("f4+0.2", "impact", 0.9), ("f4+3.5", "impact", 1.0)]),
    dict(id="f5", lines=["f5"], lead=0.2, tail=2.8, look=DESAT,
         segs=[S("stadium_crowd", 4.0, 6.0, speed=0.6, punch=P),
               S("lone_ball", 2.0, fill=True, speed=0.5, zoom=(1.15, 1.0))],
         overlays=[HL("f5+0.2", 2025, "6月 · 雅加达", "中国", 0, 1, "印尼", until="f5.end"),
                   ("stamp", "f5.end+0.1", "end", dict(text_="无缘世界杯", size=140, color="cream"))],
         events=[("f5+0.2", "impact", 0.8), ("f5.end+0.1", "impact", 1.0), ("f5.end+0.4", "mood:none", 1),
                 ("f5.end+0.5", "heartbeat", 0.8)]),

    # ------------------------------------------------------------------ 七 少年
    card("第七章", "少年", "2026", 2026.0, tone="gold", music="tension", upfrom=2025),
    dict(id="g1", lines=["g1", "g2"], lead=0.2, gap=0.4, tail=0.8, look=HYPE,
         segs=[S("kid_sky", 0.0, 2.4, punch=P), S("juggle_boy", 0.4, 2.4, punch=P),
               S("dusk_training", 0.6, 3.0, punch=P), S("indoor_training", 0.0, 2.4, punch=P),
               S("youth_match", 0.0, fill=True, zoom=(1.0, 1.1))],
         overlays=[HL("g2+0.1", 2026, "U23亚洲杯 · 亚军")],
         events=[("g2+0.1", "impact", 0.7)]),
    dict(id="g3", lines=["g3"], lead=0.2, tail=0.4, look=HYPE,
         segs=[S("stadium_lights", 5.0, 7.4, punch=P), S("crowd_hands", 2.0, fill=True, zoom=(1.0, 1.08))],
         overlays=[HL("g3+0.1", 2026, "10月3日 · 名古屋亚运会", note="男足铜牌争夺战  vs 乌兹别克斯坦")],
         events=[("g3+0.1", "impact", 0.8)]),
    dict(id="g4", lines=["g4"], lead=0.2, tail=1.6, look=GLORY,
         segs=[S("bcast_run", 3.6, 6.2, punch=P), S("freekick", 4.0, 6.6, speed=0.9, punch=P, zoom=(1.28, 1.32), focus=(0.45, 0.45)),
               S("bcast_netgoal", 5.6, 8.0, punch=P), S("pen_kick", 0.0, fill=True, speed=0.6, look=HYPE)],
         overlays=[("flash", "g4+1.2", "g4+1.6", {}), ("flash", "g4+2.8", "g4+3.2", {}),
                   ("stamp", "g4.end+0.05", "end", dict(text_="点球大战", size=150, color="gold"))],
         events=[("g4+1.2", "impact", 0.9), ("g4+1.2", "crowd_roar", 0.5), ("g4+2.8", "impact", 1.0),
                 ("g4.end+0.05", "impact", 0.9), ("g4.end+0.05", "mood:tension", 1),
                 ("g4.end", "whistle", 0.8)]),
    dict(id="g5", lines=["g5", "g6"], lead=1.6, gap=0.5, tail=3.0, look=GLORY,
         segs=[S("pen_kick", 3.6, 4.6, speed=0.35, look=HYPE),
               S("keeper_dive", 4.0, 5.4, speed=0.4, look=HYPE, punch=0.12, zoom=(1.18, 1.22), focus=(0.45, 0.55)),
               S("red_hug", 5.0, 9.6, speed=0.8, punch=P, zoom=(1.3, 1.36), focus=(0.5, 0.4)), S("fist_stand", 1.0, 5.6, punch=P),
               S("confetti", 0.4, 6.2, speed=0.8, punch=P), S("fans_night", 5.0, fill=True)],
         overlays=[("embers", 0, "end", {}), ("leak", 0, "end", {}), ("flash", "g5+0.5", "g5+0.95", {}), ("flash", "g5.end-0.9", "g5.end-0.3", {}),
                   ("shootout", "g5.end-0.9", "g6+0.3", {}),
                   ("medal", "g6+0.2", "end", {})],
         events=[(0.0, "heartbeat", 0.8), ("g5+0.5", "impact", 1.0), ("g5.end-0.9", "impact", 1.0),
                 ("g5.end-0.9", "riser:1.5", 0.6), ("g5.end-0.9", "mood:anthem", 1),
                 ("g5.end-0.9", "crowd_roar", 0.8), ("g6+0.2", "impact", 0.9)]),

    # ------------------------------------------------------------------ 清醒：国奥不是国家队
    dict(id="i1", lines=["i1"], lead=1.0, tail=1.2, look=DESAT, music="sad", music_at=0.6,
         segs=[BLACK(0.6), S("stadium_lights", 0.0, 3.0, speed=0.7, punch=P),
               S("bw_crowd", 5.0, 7.0, look=BW, punch=P), S("sad_man", 4.0, fill=True, zoom=(1.0, 1.1))],
         overlays=[HL("i1+0.3", 2026, "10月2日 · 重庆国际足球邀请赛", "中国", 0, 5, "巴勒斯坦",
                      note="此前 0比3 负新西兰")],
         events=[(0.0, "mood:none", 1), (0.6, "boom", 1.0), ("i1+0.3", "impact", 0.8)]),
    dict(id="i2", lines=["i2", "i3"], lead=0.3, gap=0.6, tail=1.6, look=COLD,
         segs=[S("lone_ball", 2.0, 4.6, speed=0.6), S("far_field", 0.0, 3.0, speed=0.8),
               S("writing", 0.0, fill=True, look=dict(COLD, sat=0.3), zoom=(1.0, 1.08))],
         overlays=[("stamp", "i2+0.1", "i2.end+0.2", dict(text_="国奥 ≠ 国家队", size=130, color="cream")),
                   ("stamp", "i3+0.1", "end", dict(text_="正视差距", size=160, color="red", sub="中国足球 仍需努力"))],
         events=[("i2+0.1", "boom", 0.8), ("i3+0.1", "impact", 0.9)]),

    # ------------------------------------------------------------------ 八 呐喊：球迷与国家队同进退
    card("第八章", "呐喊", "1982 — 2026", 2026.0, tone="dark", music="build", upfrom=1982),
    dict(id="j1", lines=["j1"], lead=0.2, tail=0.6,
         segs=[S("crowd_hands", 0.0, 2.3, look=HYPE, punch=P), S("stadium_lights", 4.4, 6.6, look=HYPE, punch=P),
               S("bw_crowd", 5.0, 7.0, look=BW, punch=P), S("stadium_crowd", 4.0, fill=True, speed=0.8, look=COLD)],
         overlays=[("leak", 0, "end", {})]),
    dict(id="j2", lines=["j2"], lead=0.2, tail=0.8, look=HYPE,
         segs=[dict(kind="chinamap", fill=False, dur=3.6),
               S("dark_tv", 3.1, 5.6, look=dict(temp=-0.1, sat=0.85, contrast=1.1, grain=0.05, vignette=0.55),
                 zoom=(1.0, 1.1), screen=dict(clip="tv_epl", a=1.6, speed=1.0)),
               S("fans_night", 6.0, fill=True, look=GLORY, punch=P)],
         events=[(0.3, "boom", 0.5), (3.6, "shake", 0.7)]),
    dict(id="j3", lines=["j3"], lead=0.2, tail=1.6, look=GLORY,
         segs=[S("fist_stand", 1.0, 3.4, punch=P), S("crowd_sea", 0.0, fill=True, zoom=(1.0, 1.08))],
         overlays=[("stamp", "j3+0.6", "end", dict(text_="同进退 · 共荣辱", size=120, color="gold")),
                   ("embers", 0, "end", {})],
         events=[("j3+0.6", "impact", 1.0)]),
    dict(id="chant", min=12.6, look=GLORY,
         segs=[S("crowd_sea", 0.0, 1.0, punch=0.12), S("fist_stand", 1.0, 2.0, punch=0.12),
               S("fans_night", 6.0, 7.0, punch=0.12), S("crowd_hands", 2.0, 3.0, punch=0.12),
               S("stadium_lights", 5.0, 6.0, punch=0.12), S("confetti", 0.6, 1.6, punch=0.12),
               S("fans_stadium", 1.0, 2.0, punch=0.12), S("crowd_sea", 3.0, 4.0, punch=0.12),
               S("fist_stand", 3.0, 4.0, punch=0.12), S("fans_night", 7.4, 8.4, punch=0.12),
               S("confetti", 2.6, 3.6, punch=0.12), S("crowd_hands", 5.0, fill=True, punch=0.12)],
         overlays=[("chant", 0.2, 12.2, {}), ("embers", 0, "end", dict(n=90))],
         events=[(0.0, "mood:none", 1), (0.2, "chant", 1.0)]
         + [(0.2 + c * 4.0 + b, "shake", 0.6) for c in range(3) for b in (0.0, 1.0, 2.0, 2.5, 3.0, 3.25, 3.5)]),
    dict(id="j4", lines=["j4"], lead=0.1, tail=2.2, look=GLORY,
         segs=[S("confetti", 2.0, fill=True, speed=0.7, zoom=(1.0, 1.1))],
         overlays=[("flash", 0.0, 0.5, {}), ("embers", 0, "end", {}), ("leak", 0, "end", {})],
         events=[(0.0, "mood:anthem", 1), (0.0, "impact", 1.0), (0.0, "crowd_roar", 0.7)]),

    # ------------------------------------------------------------------ 终章
    card("终章", "火", "1982 — 2026", 2026.0, tone="dark", music="outro", upfrom=1982),
    dict(id="h", lines=["h1", "h2"], lead=0.6, gap=0.8, tail=11.0, xf=0.0, look=dict(GLORY, sat=1.05),
         segs=[S("kid_garden", 6.2, 9.8, speed=0.8), S("golden_pass", 0.0, 4.0, speed=0.8),
               S("golden_juggle", 2.0, 6.0, speed=0.8), S("kid_sky", 0.0, fill=True, speed=0.5, zoom=(1.0, 1.1))],
         overlays=[("embers", 0, "end", {}), ("leak", 0, "end", {}), ("zh_end", "h2.end+0.8", "end", {})],
         events=[("h2.end+0.8", "impact", 0.7)]),
]

DEFAULTS = dict(min=3.0, lead=0.3, gap=0.4, tail=1.0, xf=0.0)


# ------------------------------------------------------------------ transitions ("百万级转场")
# The shot after each chapter card enters with a spin or a light burn; montage cuts cycle through
# whip / zoom / glitch / vertical whip; sombre shots get glitches and burns only.
_HOT = ["whip", "zoom", "glitch", "whip_v", "spin", "whip", "burn", "zoom"]
_LOW = ["glitch", "burn"]
_LOWSHOTS = {"d1", "d2", "f1", "f2", "f4", "f5", "i1", "i2", "j1"}
_n = 0
for _i, _sh in enumerate(SHOTS):
    if _i > 0 and SHOTS[_i - 1]["id"] == "card" and _sh["id"] != "card":
        _sh.setdefault("tin", "burn" if _sh["id"] in _LOWSHOTS else ("spin" if _n % 2 else "zoom"))
    elif _i > 0 and _sh["id"] != "card" and _sh["id"] not in ("chant",):
        _sh.setdefault("tin", (_LOW if _sh["id"] in _LOWSHOTS else _HOT)[_n % 2 if _sh["id"] in _LOWSHOTS else _n % len(_HOT)])
    if _sh["id"] == "chant":
        continue  # chant cuts land on the claps with shakes; keep them hard
    for _j, _sg in enumerate(_sh.get("segs", [])):
        if _j == 0 or _sg.get("kind") in ("black", "bg"):
            continue
        if _sh["id"] in _LOWSHOTS:
            _sg.setdefault("tin", _LOW[_n % 2])
        else:
            _sg.setdefault("tin", _HOT[_n % len(_HOT)])
        _n += 1
    _n += 1


# ------------------------------------------------------------------ atmosphere layers
_SMOKY = {"a1", "a2", "b2", "d1", "d2", "f1", "f2", "f4", "f5", "i1", "i2", "j1"}
_BRIGHT = {"cold", "b1", "c1", "e2", "f3", "g3", "g4", "g5", "j3", "j4", "h"}
for _sh in SHOTS:
    ov = _sh.setdefault("overlays", [])
    if _sh["id"] in _SMOKY:
        ov.insert(0, ("smoke", 0, "end", dict(strength=0.28)))
    if _sh["id"] in _BRIGHT:
        ov.insert(0, ("rays", 0, "end", dict(strength=0.8)))
        ov.insert(1, ("flare", 0, "end", dict(strength=0.7)))
