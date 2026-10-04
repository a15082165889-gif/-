#!/bin/sh
bv=$1
[ -f "$bv.mp4" ] && exit 0
timeout 1500 yt-dlp --no-warnings --cookies /tmp/bili_cookies.txt --retries 5 --fragment-retries 5 \
  -f "bv*[height<=720][vcodec^=avc]+ba/bv*[height<=720]+ba/b" --merge-output-format mp4 -o "%(id)s.%(ext)s" \
  "https://www.bilibili.com/video/$bv" >/dev/null 2>&1
echo "$bv $( [ -f $bv.mp4 ] && echo OK || echo FAIL )"
