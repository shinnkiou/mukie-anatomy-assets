# YouTube Pipeline Regression 2026-08-29

Target: https://youtu.be/JFFL7bq18QQ?si=RM-3soCDW_VYDVNB

## Run 1
`python scripts/video3d/extract_youtube.py ...`

Result: command unavailable (`python: command not found`).

Fix: use `python3` explicitly.

## Run 2
`python3 scripts/video3d/extract_youtube.py ...`

Captions and preview video were retrieved, but screenshot stage stopped with `No module named 'imageio_ffmpeg'`.

Fix: dependency preflight and install/check for `imageio-ffmpeg` and `pillow` before frame extraction.

## Run 3
After dependency preflight, pipeline returned errors=0 and generated:
- timestamped transcript
- structured transcript JSON
- raw transcript
- 12 selected screenshots
- screenshot index JSON
- contact sheet

## Next implementation rule
The reusable runner should always check:
1. `python3` executable
2. `yt_dlp`
3. `imageio_ffmpeg`
4. `PIL`
5. writable output directory
before YouTube work begins. A missing screenshot dependency must not invalidate already completed caption output.
