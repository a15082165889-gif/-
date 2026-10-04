"""The edit: every shot, the real footage it cuts together, its colour grade and on-screen graphics.

Segments are laid end to end inside a shot. Times are seconds in the source clip; `speed` < 1 is slow
motion. One segment per shot may set `fill=True` to stretch until the shot ends. Overlay times can
refer to the narration: "c3b" = start of that line, "c3b.end" = its end, "end" = end of the shot, and
"+/-" offsets ("c3b+4.4", "end-2").
"""


def S(clip, a, b=None, **kw):
    return dict(kind="clip", clip=clip, a=a, b=b, **kw)


def BLACK(dur, **kw):
    return dict(kind="black", dur=dur, **kw)


def FREEZE(clip, at, dur, **kw):
    return dict(kind="clip", clip=clip, a=at, b=at, freeze=dur, **kw)


WARM = dict(temp=0.06, sat=1.05, contrast=1.06, lift=0.02, grain=0.035, vignette=0.38)
GOLD = dict(temp=0.12, sat=1.08, contrast=1.08, lift=0.03, grain=0.035, vignette=0.42)
NOSTALGIA = dict(temp=0.10, sat=0.82, contrast=1.02, lift=0.06, grain=0.05, vignette=0.45, fade=0.05)
COOL = dict(temp=-0.07, sat=0.80, contrast=1.04, lift=0.03, grain=0.04, vignette=0.45)
GREY = dict(temp=-0.03, sat=0.55, contrast=1.02, lift=0.04, grain=0.045, vignette=0.5)
NIGHT = dict(temp=-0.10, sat=0.85, contrast=1.10, lift=0.01, grain=0.05, vignette=0.55)
TV = dict(temp=-0.02, sat=1.0, contrast=1.08, lift=0.02, grain=0.04, vignette=0.5)
RED = dict(temp=0.10, sat=1.1, contrast=1.1, lift=0.02, grain=0.045, vignette=0.5, tint_red=0.18)


SHOTS = [
    # ------------------------------------------------------------------ cold open
    dict(id="open", lines=["open"], min=14.0, lead=1.6, tail=6.6, look=GOLD,
         segs=[S("ball_turf", 0.0, speed=0.32, fill=True, zoom=(1.0, 1.10))],
         overlays=[("title", "open.end+0.6", "end-0.4", dict(text="STILL ROLLING", sub="A FOOTBALL STORY"))]),
    dict(id="card", min=4.2, card=("Chapter One", "Age Five"), music="child"),

    # ------------------------------------------------------------------ chapter 1
    dict(id="photo", lines=["c1a"], min=8.2, lead=1.0, tail=1.8, look=NOSTALGIA,
         segs=[dict(kind="photo", clip="kid_garden", at=8.75, user="childhood", dur=5.6, x=1.4,
                    caption="age 5"),
               S("kid_garden", 6.2, speed=0.8, fill=True, zoom=(1.08, 1.0))]),
    dict(id="sports", lines=["c1b"], min=9.6, lead=0.8, tail=2.2, look=WARM,
         segs=[S("badminton", 4.0, 7.3, zoom=(1.04, 1.1)),
               S("pingpong", 0.4, 3.3, zoom=(1.05, 1.12)),
               S("track", 0.2, speed=0.9, fill=True, zoom=(1.0, 1.08))],
         overlays=[("label", 0.4, 3.1, dict(text="BADMINTON")),
                   ("label", 3.6, 6.0, dict(text="TABLE TENNIS")),
                   ("label", 6.6, "end-0.5", dict(text="TRACK & FIELD"))]),
    dict(id="first_touch", lines=["c1c"], min=11.0, lead=1.4, tail=1.8, look=GOLD,
         segs=[S("boots_ball", 2.6, 6.6, speed=0.7, zoom=(1.0, 1.08), x=0.5),
               S("kid_sky", 0.0, speed=0.75, fill=True, zoom=(1.12, 1.0))]),
    dict(id="ball_sense", lines=["c1d"], min=10.5, lead=0.8, tail=2.2, look=WARM,
         segs=[S("juggle_boy", 0.3, 5.4, zoom=(1.0, 1.06)),
               S("pass_coach", 1.5, speed=0.9, fill=True, zoom=(1.06, 1.0))]),
    dict(id="card", min=4.2, card=("Chapter Two", "The Academy"), music="academy"),

    # ------------------------------------------------------------------ chapter 2
    dict(id="academy", lines=["c2a"], min=9.2, lead=1.2, tail=2.2, look=WARM,
         segs=[S("youth_event", 1.2, 8.6, zoom=(1.0, 1.06)),
               S("coach_two", 1.0, fill=True, zoom=(1.0, 1.05))],
         overlays=[("lower", "c2a+0.6", "end-0.4", dict(title="Sichuan Jiuniu", sub="Youth Training Academy"))]),
    dict(id="training", lines=["c2b"], min=11.5, lead=0.8, tail=3.2, look=WARM,
         segs=[S("indoor_training", 0.0, 3.1, zoom=(1.04, 1.1)),
               S("goal_net_training", 3.2, 6.4, zoom=(1.0, 1.05)),
               S("dusk_training", 0.6, speed=0.85, fill=True, zoom=(1.0, 1.12))],
         audio=[("indoor_training", 0.0, 0.0, 3.1, 0.25)]),
    dict(id="spain_map", lines=["c2c"], min=11.0, lead=1.0, tail=2.6,
         segs=[dict(kind="map", broken=False, fill=True)]),
    dict(id="card", min=4.2, card=("Chapter Three", "The Fall"), music="tension"),

    # ------------------------------------------------------------------ chapter 3
    dict(id="injury", lines=["c3a", "c3b", "c3c"], min=35.0, lead=1.0, gap=0.7, tail=3.0, look=WARM,
         segs=[S("youth_match", 0.0, 3.2, zoom=(1.05, 1.12)),
               S("low_turf", 0.5, 4.0, zoom=(1.0, 1.06)),
               S("feet_dribble", 2.3, 6.6, zoom=(1.0, 1.08)),
               S("feet_yellow", 1.4, 4.9, zoom=(1.2, 1.24)),
               S("feet_yellow", 4.9, 5.6, speed=0.25, zoom=(1.24, 1.32), look=dict(sat=0.8)),
               FREEZE("feet_yellow", 5.6, 0.9, zoom=(1.32, 1.36), shake=1.0, look=dict(sat=0.3, contrast=1.2)),
               BLACK(0.9),
               S("low_turf", 4.0, 6.0, speed=0.6, rot=-13, blur=10, zoom=(1.25, 1.3), look=GREY),
               S("physio_knee", 0.5, 3.4, speed=0.7, zoom=(1.1, 1.18), look=dict(GREY, contrast=1.15)),
               S("lone_ball", 2.0, speed=0.6, fill=True, zoom=(1.12, 1.0), look=GREY)],
         overlays=[("flash", 17.9, 18.4, {})],
         events=[(14.5, "whoosh_soft", 0.5), (17.9, "thud", 1.0), (17.9, "music_cut", 1.0),
                 (18.3, "heartbeat", 0.9), (19.3, "tinnitus", 0.35)],
         audio=[("youth_match", 0.0, 0.0, 3.2, 0.22)]),
    dict(id="corridor", min=6.0, look=COOL,
         segs=[S("rehab_corridor", 0.0, speed=0.85, fill=True, zoom=(1.0, 1.08))],
         events=[(0.0, "hospital", 0.5)]),
    dict(id="ligament", lines=["c3d"], min=8.6, lead=1.0, tail=2.0, look=COOL,
         segs=[S("knee_brace", 0.0, speed=0.95, fill=True, zoom=(1.06, 1.14))],
         overlays=[("lower", "c3d+0.8", "end-0.3", dict(title="Anterior cruciate ligament",
                                                        sub="Near-complete rupture"))]),
    dict(id="map_broken", lines=["c3e"], min=9.2, lead=0.6, tail=2.6,
         segs=[dict(kind="map", broken=True, fill=True)]),
    dict(id="recovery", lines=["c3f"], min=10.8, lead=1.0, tail=2.6, look=COOL,
         segs=[S("physio_stretch", 0.0, 4.6, zoom=(1.0, 1.06)),
               S("sunset_crutches", 5.6, speed=0.72, fill=True, zoom=(1.0, 1.1), look=GOLD)]),
    dict(id="card", min=4.2, card=("Chapter Four", "Ordinary Days"), music="ordinary"),

    # ------------------------------------------------------------------ chapter 4
    dict(id="school", lines=["c4a", "c4b"], min=16.0, lead=0.8, gap=0.9, tail=1.8, look=GREY,
         segs=[S("writing", 0.0, 4.6, zoom=(1.0, 1.06)),
               S("yawn", 1.5, 3.2, zoom=(1.0, 1.05)),
               S("writing", 5.6, 6.7),
               S("meal", 0.6, 1.7),
               S("yawn", 3.6, 4.7),
               S("doze", 0.5, 2.0),
               S("writing", 7.2, 7.6), S("meal", 8.0, 8.4), S("yawn", 5.2, 5.6), S("doze", 3.0, 3.4),
               S("writing", 8.6, 9.0), S("meal", 4.4, 4.8), S("yawn", 6.4, 6.8),
               S("doze", 4.0, speed=0.8, fill=True, zoom=(1.0, 1.06))],
         overlays=[("label", 6.0, 7.1, dict(text="CLASSES", small=True)),
                   ("label", 7.1, 8.2, dict(text="MEALS", small=True)),
                   ("label", 8.2, 9.3, dict(text="STUDY", small=True)),
                   ("label", 9.3, 10.8, dict(text="SLEEP", small=True)),
                   ("label", 10.8, "end-0.4", dict(text="REPEAT", small=True))],
         events=[(0.0, "clock", 0.35)]),
    dict(id="window", lines=["c4c"], min=10.0, lead=1.0, tail=2.6, look=COOL,
         segs=[S("far_field", 0.0, speed=0.9, fill=True, zoom=(1.0, 1.1), window=True)]),
    dict(id="card", min=4.2, card=("Chapter Five", "The Glow of the Screen"), music="screen"),

    # ------------------------------------------------------------------ chapter 5
    dict(id="tv_room", lines=["c5a"], min=7.5, lead=1.2, tail=2.6, look=NIGHT,
         segs=[S("dark_tv", 3.1, speed=0.9, fill=True, zoom=(1.0, 1.15),
                 screen=dict(clip="tv_epl", a=1.6, speed=1.0))],
         events=[(0.2, "tv_on", 0.5)]),
    dict(id="tv_bale", lines=["c5b"], min=9.0, lead=0.6, tail=1.6, look=TV,
         segs=[S("tv_espn", 0.0, 3.3, zoom=(1.0, 1.06)),
               S("bcast_run", 0.0, speed=0.9, fill=True, zoom=(1.02, 1.08), tv=True)],
         audio=[("tv_espn", 0.0, 0.0, 3.3, 0.35), ("bcast_run", 3.3, 0.0, 5.0, 0.3)]),
    dict(id="tv_ronaldo", lines=["c5c"], min=13.0, lead=0.5, tail=2.6, look=TV,
         segs=[S("bcast_netgoal", 2.6, 9.0, zoom=(1.0, 1.08), tv=True),
               S("fans_stadium", 1.0, 5.4, zoom=(1.0, 1.05)),
               S("stadium_crowd", 0.0, speed=0.9, fill=True, zoom=(1.0, 1.06))],
         events=[(6.5, "crowd_roar", 1.0)],
         audio=[("fans_stadium", 7.9, 1.0, 4.4, 0.55), ("stadium_crowd", 12.3, 0.0, 3.0, 0.4)]),
    dict(id="card", min=4.2, card=("Chapter Six", "Thirteen Years"), music="love"),

    # ------------------------------------------------------------------ chapter 6
    dict(id="devotion", lines=["c6a", "c6b"], min=13.0, lead=1.0, gap=0.8, tail=2.4, look=GOLD,
         segs=[S("golden_juggle", 0.0, 5.9, zoom=(1.0, 1.06)),
               S("bernabeu", 0.0, speed=0.8, fill=True, fit="contain", fit_x=0.1, zoom=(1.0, 1.04))],
         overlays=[("counter", "c6b+0.2", "end-0.3", dict(n=13, word="YEARS", sub="HALA MADRID"))]),
    dict(id="heroes", lines=["c6c", "c6d"], min=12.6, lead=0.8, gap=0.7, tail=2.4, look=GREY,
         segs=[S("bcast_wide", 5.2, 7.9, speed=0.6, zoom=(1.0, 1.08), look=dict(GREY, sat=0.3)),
               S("stadium_crowd", 0.0, speed=0.55, fill=True, zoom=(1.0, 1.08), look=dict(GREY, sat=0.3))],
         overlays=[("tribute", 0.3, "c6c.end+0.5", dict(n="11", name="GARETH BALE", sub="Where it began")),
                   ("tribute", "c6d-0.2", "end-0.3", dict(n="7", name="CRISTIANO RONALDO",
                                                           sub="Where it became love"))]),
    dict(id="china", lines=["c6e"], min=8.6, lead=0.8, tail=2.8, look=RED,
         segs=[S("fans_night", 0.0, 5.0, speed=0.75, zoom=(1.0, 1.06)),
               S("fans_night", 5.4, speed=0.75, fill=True, zoom=(1.0, 1.06))],
         overlays=[("china", "c6e+0.3", "end-0.3", {})]),
    dict(id="card", min=4.2, card=("Epilogue", "Still Rolling"), music="end"),

    # ------------------------------------------------------------------ epilogue
    dict(id="golden", lines=["c7a"], min=12.0, lead=1.2, tail=2.2, look=GOLD,
         segs=[S("golden_pass", 0.0, 6.0, speed=0.85, zoom=(1.0, 1.06)),
               S("golden_juggle", 5.0, speed=0.9, fill=True, zoom=(1.06, 1.0))]),
    dict(id="finale", lines=["c7b"], min=24.0, lead=0.8, tail=15.0, xf=0.0, look=GOLD,
         segs=[S("kid_sky", 0.0, 6.0, speed=0.5, zoom=(1.0, 1.1)),
               S("ball_turf", 4.4, speed=0.6, fill=True, zoom=(1.0, 1.06))],
         overlays=[("end_title", "end-9.5", "end", {})]),
]

DEFAULTS = dict(min=6.0, lead=0.8, gap=0.6, tail=1.6, xf=0.8)
