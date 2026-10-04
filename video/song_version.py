#!/usr/bin/env python3
"""Make a version of 大起大落 scored with a given song, reusing the rendered master picture.

    python3 song_version.py music/songs/zhuimeng.mp3 --climax 224 --tag zhuimeng \
        --credit "音乐：GALA《追梦赤子心》 · Kevin MacLeod (incompetech.com) CC BY 4.0" --duck 0.6

The song's climax (seconds into the song) is placed on the shoot-out "4:3"; only the end card is
re-rendered (for the music credit), everything else is copied from build/china/china.mp4.
"""
import argparse
import json
import os
import subprocess
import sys

os.environ["FILM"] = "china"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("song", help="song file, or 'medley' for the MEDLEY_CUES arrangement")
ap.add_argument("--climax", type=float, default=None)
ap.add_argument("--tag", required=True)
ap.add_argument("--credit", required=True)
ap.add_argument("--duck", type=float, default=0.55)
ap.add_argument("--bitrate", default="8M")
args = ap.parse_args()
if args.song == "medley":
    os.environ["MUSIC"] = "medley"
else:
    os.environ["SONG"] = os.path.abspath(args.song)
if args.climax is not None:
    os.environ["SONG_CLIMAX"] = str(args.climax)
os.environ["SONG_DUCK"] = str(args.duck)
os.environ["MUSIC_CREDITS"] = args.credit

from film import audio_epic, engine  # noqa: E402
from film.gfx import FPS  # noqa: E402

B = engine.BUILD
voice = json.load(open(os.path.join(B, "voice.json")))
shots, total = engine.build_timeline(voice)
master = os.path.join(B, "china.mp4")
wav = os.path.join(B, f"mix_{args.tag}.wav")
audio_epic.render(shots, total, voice, wav)

# re-render the final shot (end card carries the music credit)
h = [s for s in shots if s.id == "h"][0]
f0, f1 = int(round(h.start * FPS)), int(round(total * FPS))
tail = os.path.join(B, f"tail_{args.tag}.mp4")
engine.render_chunk((f0, f1, tail, 14))

out = os.path.join(B, f"china_{args.tag}.mp4")
fc = (f"[0:v]trim=end_frame={f0},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];"
      f"[a][b]concat=n=2:v=1:a=0[v]")
log = os.path.join(B, f"pass_{args.tag}")
common = ["-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-tune", "film",
          "-b:v", args.bitrate, "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p", "-passlogfile", log]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", master, "-i", tail, *common, "-pass", "1", "-an", "-f", "null",
                "-"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", master, "-i", tail, "-i", wav, *common, "-map", "2:a",
                "-pass", "2", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "224k",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("done:", out)
