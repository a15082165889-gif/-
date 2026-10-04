# Still Rolling — a football story

A ~5-minute documentary-style short built from the outline you wrote: childhood sports, the youth
academy, the knee injury that ended the move to Spain, ordinary school days, the TV nights with Bale
and Ronaldo, thirteen years of Real Madrid, and the national team.

## Structure

| Chapter | Content |
|---|---|
| Cold open | Ball on the turf, title |
| One · Age Five | Old photograph → badminton, table tennis, track & field → first touch → ball sense |
| Two · The Academy | Sichuan Jiuniu Youth Training Academy, training montage, animated map Chengdu → Madrid |
| Three · The Fall | Match → sharp stop → knee gives way (slow motion, freeze, flash) → ball rolling away → rehab corridor, knee brace, the map breaking apart, recovery |
| Four · Ordinary Days | Classes, meals, study, sleep — and a ball outside the window |
| Five · The Glow of the Screen | Dark bedroom, football on the TV, the goal, the crowd |
| Six · Thirteen Years | Real Madrid, tributes to No. 11 and No. 7, the Chinese national team |
| Epilogue · Still Rolling | Golden-hour football, end title |

Narration is in `film/story.py` (lines marked ADDED are new beats; delete or edit any line and
rebuild — shot lengths follow the voice). The edit — which footage, grading, slow motion and
graphics — is in `film/edit.py`.

## Building

```bash
pip install pycairo numpy scipy pillow soundfile kokoro-onnx
python3 build.py              # -> build/still_rolling.mp4 (+ .srt subtitles)
python3 build.py --plan       # shot timings
python3 build.py --stills 60  # check single frames
```

The first build downloads the Kokoro voice model (GitHub releases) and the Kinetics-700 clips the
edit uses (Amazon S3) into `.models/` and `.footage/`.

## Sources

- **Footage:** real YouTube clips from the Kinetics-700 research dataset (validation split), used as
  stand-in imagery for the real-life scenes. They are not of you or of the players named; your own
  photo can replace the childhood print (see `photos/README.md`). For private viewing only.
- **Voice:** Kokoro neural TTS (`am_michael`), generated locally.
- **Music and sound design:** synthesized from scratch in `film/audio.py`.
- **Map:** Natural Earth land outlines (public domain), pre-baked into `assets/map_dots.json`.
- **Fonts:** Bebas Neue, Inter, Montserrat, Playfair Display, Caveat (SIL Open Font License).
