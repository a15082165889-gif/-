"""Contact sheet with timestamps for a video: tools/sheet.py in.mp4 out.jpg [step_seconds]"""
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout.strip() or 0)
step = float(sys.argv[3]) if len(sys.argv) > 3 else max(2.0, dur / 60)
n = int(dur // step)
cols, tw, th = 8, 240, 135
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1/{step},scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
frames = [raw[i:i + tw * th * 3] for i in range(0, len(raw), tw * th * 3)]
frames = [f for f in frames if len(f) == tw * th * 3]
rows = (len(frames) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
for i, f in enumerate(frames):
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(Image.frombytes("RGB", (tw, th), f), (x, y))
    t = i * step
    d.rectangle([x, y, x + 52, y + 17], fill=(0, 0, 0))
    d.text((x + 3, y + 1), f"{int(t // 60)}:{t % 60:04.1f}", fill=(255, 220, 0), font=font)
sheet.save(out, quality=80)
print(out, len(frames), "frames, step", round(step, 1))
