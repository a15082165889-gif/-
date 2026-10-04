"""《前进》: no narration. The film is carried by real match sound, fans and players' voices, and music."""

LANG = "zh"
VOICE = "zm_yunyang"
SPEED = 1.0
SUB_FONT = "sans"
AUDIO = "audio_real"
SPOKEN = {}
NARRATION = {}

LIB = "music/library/"
# Licensed music (Kevin MacLeod, incompetech.com, CC BY 4.0) under the real sound.
MUSIC_CUES = [
    dict(track=LIB + "Strength of the Titans.mp3", start=("tunnel", 0), end=("wulihe", "end"), src=0.0, fin=0.05,
         fout=1.5, gain=0.8),
    dict(track=LIB + "Volatile Reaction.mp3", start=("jinan", 0), end=("changsha", "end"), src=6.0, fin=1.0,
         fout=1.5, gain=0.75),
    dict(track=LIB + "Big Drumming.mp3", start=("u23", 0), end=("u23", "end"), src=84.0, fin=0.8, fout=1.2,
         gain=0.7),
    dict(track=LIB + "Strength of the Titans.mp3", start=("bronze", 0), end=("locker", "end"), src=0.0,
         fin=0.6, fout=1.5, gain=0.8),
    dict(track=LIB + "Egmont Overture Finale.mp3", start=("fans", 0), end=("end", "end"),
         src_end_at=(97.0, "end-1.0"), fin=1.5, fout=1.0, gain=0.75),
]
MUSIC_CREDITS = ("音乐：Kevin MacLeod (incompetech.com) · Strength of the Titans · Volatile Reaction · Big Drumming · "
                 "Egmont Overture Finale  CC BY 4.0")
FOOTAGE_CREDITS = "画面与现场声：哔哩哔哩公开视频（央视、亚足联转播及现场拍摄），仅供个人欣赏"
