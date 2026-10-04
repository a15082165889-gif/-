#!/bin/sh
# Final deliverables from a finished cut:
#   deliver.sh build/china/china_zhuimeng.mp4 output/大起大落
# -> <name>_720p.mp4  (single file under 30 MB, H.265)
#    <name>_1080p.mp4 (single file under 100 MB, H.265, fits in a git repo)
set -e
IN="$1"; NAME="$2"; LOG=$(mktemp -d)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
enc() { # $1 scale $2 video kbps $3 audio kbps $4 out
  ffmpeg -v error -y -i "$IN" -vf "hqdn3d=1.5:1.5:6:6,scale=$1:flags=lanczos" -c:v libx265 -preset slow \
    -b:v "$2"k -x265-params "pass=1:stats=$LOG/x265.log:log-level=error" -an -f null -
  ffmpeg -v error -y -i "$IN" -vf "hqdn3d=1.5:1.5:6:6,scale=$1:flags=lanczos" -c:v libx265 -preset slow \
    -b:v "$2"k -x265-params "pass=2:stats=$LOG/x265.log:log-level=error" -tag:v hvc1 \
    -c:a aac -b:a "$3"k -movflags +faststart "$4"
}
V720=$(python3 -c "print(int(29*8*1024*1024/$DUR/1000 - 80 - 12))")
V1080=$(python3 -c "print(int(95*8*1024*1024/$DUR/1000 - 128 - 20))")
enc 1280:720 "$V720" 80 "${NAME}_720p.mp4"
enc 1920:1080 "$V1080" 128 "${NAME}_1080p.mp4"
ls -la "${NAME}"_*.mp4
