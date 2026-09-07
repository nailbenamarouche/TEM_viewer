# DM4 Converter — User Guide

Practical guide to the DM3/DM4 → video conversion dialog defined in
`dm4_converter.py`. For architecture/implementation details, see
[README.md](README.md). For the editor this hands off to, see
[USER_GUIDE_VIDEO_PROCESSOR.md](USER_GUIDE_VIDEO_PROCESSOR.md).

**Note**: `dm4_converter.py` is a utility module, not a standalone program —
it has no window of its own to launch directly. It's imported by
`tem_video_processor.py`, which shows its dialog automatically on startup.
The two files must stay in the same folder.

## 1. Opening the dialog

```bash
python tem_video_processor.py
```

The **TEM Video Processor — DM4 to Video** dialog opens first, before the
main editor window. From here you either convert a folder of DM3/DM4
frames into a video, or skip conversion entirely and open an existing
video file.

## 2. Selecting the input folder

Click **Browse…** next to **DM4/DM3 folder** and pick either:

- a **flat folder** of individual DM3/DM4 frame files, or
- an **hour folder** containing `minute_XX` subfolders, each containing
  `second_XX` subfolders of frames (the layout Ximea/OneView capture
  sessions are often organized in).

The hierarchical layout is auto-detected. When it is, the status line
reports how many minutes/seconds/frames were found, and **Source FPS is
automatically set** from the real capture timing (total frames ÷ total
second-folders — each `second_XX` folder represents exactly one recorded
second). You can still override it by hand afterward.

**File pattern** (default `*.dm4`) controls which files are picked up
inside each folder — change it (e.g. to `*.dm3`) and the folder is
rescanned automatically.

## 3. Output and quality

- **Output video**: path is pre-filled next to the input folder when you
  browse for input, but you can change it with its own **Browse…**.
- **Quality**:
  - **Lossy H.264 (8-bit, smaller files)** — always encodes to 8-bit
    `yuv420p`. If the source frames are 16-bit, this truncates them; you'll
    get a warning dialog when conversion finishes scanning if that's about
    to happen.
  - **Lossless FFV1 (native bit depth)** — encodes at the source's actual
    depth (8-bit gray or 16-bit `gray16le`), nothing thrown away. Files are
    much larger, and are written as `.mkv` (the MP4 container doesn't
    reliably support 16-bit/FFV1) — switching to this mode automatically
    changes a `.mp4` output path to `.mkv`, and back if you switch away.

## 4. Encoding parameters

- **Source FPS**: the true capture rate of the frames (auto-filled for
  hierarchical folders, see above).
- **Target FPS**: the output video's frame rate. If this differs from
  Source FPS, frames are interpolated to get there (see Interpolation
  below) rather than simply dropped/duplicated.
- **Scale width (px)**: resize the output to this width (height keeps
  aspect ratio, Lanczos scaling). `0` = **Native (slow)** — full source
  resolution, no resizing pass.
- **x264 preset** / **CRF**: only apply to Lossy H.264. Lower CRF = higher
  quality/bigger file, higher CRF = smaller/more compressed (0-51). Preset
  trades encode speed for compression efficiency (`ultrafast` fastest,
  `medium` slowest of the offered options).
- **Interpolation**: **blend (fast)** — simple frame blending to hit the
  target FPS — or **mci (slow, smoother)** — motion-compensated
  interpolation, much better motion smoothness but noticeably slower to
  encode.

## 5. Converting

Click **Convert**. Progress and estimated encode speed (images/s) are shown
in the status line and progress bar. **Cancel** stops the conversion
cleanly (the partial output is not treated as a finished video).

If the source needs global contrast scaling (non-8/16-bit source data), the
progress bar's first pass scans the whole stack once to find a single
consistent min/max — this prevents brightness flickering frame-to-frame,
which is what naively rescaling each frame to its own min/max would cause.

On success, the video opens automatically in the main editor window and the
dialog closes. On failure, check `ffmpeg.log` written next to the output
file for FFmpeg's own error output.

## 6. Skipping conversion

Click **Skip — open existing video instead** to bypass all of the above and
open any video file (`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`) directly in the
editor.

## 7. Metadata

When converting from DM4, a `<output>.metadata.json` file is written
alongside the video, containing pixel calibration (pixel size, field of
view) and whatever instrument/acquisition fields could be read from the
first frame's DM4 tags (voltage, magnification, operator, specimen,
acquisition date/time, binning). This is best-effort — a conversion never
fails just because some metadata field is missing — and it's what powers
the **SHOW METADATA OVERLAY** option in the video processor.

## 8. Troubleshooting

- **"ffmpeg not found"**: install FFmpeg and make sure it's on your PATH.
- **A frame is silently skipped during conversion**: a DM3/DM4 file that
  fails to read, or whose dimensions don't match the first frame, is
  skipped rather than aborting the whole conversion (it would otherwise
  desync every frame after it in the output).
- **Colors/brightness look truncated on a 16-bit source**: you likely chose
  Lossy H.264 — use Lossless FFV1 to keep full bit depth.
- **Source FPS looks wrong**: only auto-detected for the hierarchical
  hour/minute/second folder layout; for a flat folder of frames, set it by
  hand to match your actual capture rate.
