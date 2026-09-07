# TEM Video Processor — User Guide

Practical guide to operating `tem_video_processor.py`, the post-processing
editor for videos produced by `dm4_converter.py` (or any other video file).
For architecture/implementation details, see [README.md](README.md). For
the DM4→video conversion step itself, see
[USER_GUIDE_DM4_CONVERTER.md](USER_GUIDE_DM4_CONVERTER.md).

## 1. Starting up

```bash
python tem_video_processor.py
```

This always opens the **DM4 to Video** dialog first (see the DM4 Converter
guide). Either convert a folder of DM3/DM4 frames there, or click
**Skip — open existing video instead** to jump straight to opening any
video file. Once that dialog closes, the main editor window opens — with
the resulting/chosen video already loaded.

You can also load a different video later from inside the editor with
**OPEN VIDEO**.

## 2. Bit depth

The video's bit depth is detected automatically (via `ffprobe`) when it's
opened, and shown in the header:

- **8-BIT** — decoded normally through OpenCV.
- **16-BIT NATIVE** — read through a dedicated raw FFmpeg pipe instead of
  OpenCV (which always decodes to 8-bit and would silently throw away the
  extra precision). The whole pipeline (drift, contrast, gamma, filters)
  then works at the source's native depth.

This matters directly for export (see [Export](#6-export)): a lossy export
of a 16-bit source always truncates to 8-bit, and the app will warn you
before doing that.

## 3. Playback

- **PLAY/PAUSE** or **Space**: toggle playback.
- **STOP**: pause and jump back to frame 0.
- **Left/Right arrow**: step one frame at a time.
- The timeline lets you scrub directly to any frame.

**Edge-strip drift correction only tracks motion during forward playback**,
not while scrubbing the timeline — see [Drift correction](#5-drift-correction).

## 4. Image processing

- **GAMMA**: slider + exact-value spin box (default 1.00, i.e. no
  adjustment).
- **CONTRAST**: **AUTOCONTRAST** (default) with adjustable LOW%/HIGH%
  percentile clipping (default 1.0/99.0), **CLAHE** with adjustable CLIP
  limit and TILE size (default 2.0/8) — both more tunable here than in the
  live viewer — or **NONE**, which passes the frame through with no
  contrast processing at all (useful for keeping raw intensities
  meaningful, e.g. diffraction patterns). Note that NONE only skips this
  step - GAMMA is still applied on top of it, so leave GAMMA at 1.00 too if
  you want a truly untouched frame.
- **FILTER**: NONE / GAUSSIAN / MEDIAN / BILATERAL / NLM, each with its own
  parameters (kernel size, sigma, etc.). NLM is a fast bilateral-filter
  approximation on both CPU and GPU (label-independent here), not true
  Non-Local Means (too slow for practical use on CPU).
- **FLAT FIELD CORRECTION**: click **LOAD FLAT FIELD** to browse for a dark
  reference image, then a gain/reference image. Unlike the live viewer,
  there's no fixed file path — you pick the images yourself, and they're
  automatically resized to match the loaded video's resolution if they
  don't already.

## 5. Drift correction

**METHOD** dropdown:

- **NONE (MANUAL)** — dial in a fixed X/Y pixel offset by hand, applied to
  every frame.
- **EDGE-STRIP (AUTO)** — tracks drift by correlating texture near the
  frame's edges, frame-to-frame. Needs actual **forward playback** to
  accumulate correctly, not timeline scrubbing. **MARGIN** and **WIDTH**
  spin boxes control where the sampled band sits: if your footage has a
  black vignette/circular border, sampling right at the true edge lands on
  blank vignette with nothing to track — raise MARGIN until it clears the
  vignette (this is the single most common reason edge-strip "reads as
  failure").
- **ROI (AUTO)** — click **SELECT ROI**, then drag a box on the video over
  a distinctive feature; tracking locks onto that feature via template
  matching. Works anywhere in frame, including a vignetted/circular border,
  since you choose the tracked region yourself.

**Important**: choosing a method only computes the shift. You must also
check **APPLY DRIFT CORRECTION** for it to actually be applied to the
image — this is a separate master switch, and it's easy to set up a method
and wonder why nothing changed because this box is still unchecked.

## 6. Segments and export

- **IN** / **OUT** (or `I` / `O`): mark the current frame as the start/end
  of a selection range on the timeline. **CLEAR** (or `X`) clears it.
- **ADD SEGMENT** (or `A`): saves the current IN/OUT range **together with
  the current processing settings** (gamma, contrast method and its
  parameters, filter and its parameters, drift offset/apply-flag) as a
  named segment (`SEG 1`, `SEG 2`, ...). This is how different parts of the
  same video can get different treatment — e.g. one segment autocontrast,
  another CLAHE with heavier denoising.
  - Note: the edge-strip MARGIN/WIDTH values are *not* saved per-segment
    (they're a single global setting), only what's listed above is.
- Clicking a segment in the list reloads its settings and jumps the
  timeline/selection to match it — useful for reviewing or tweaking it
  before re-exporting. **DELETE** removes the selected segment, **CLEAR
  ALL** removes every segment.
- **EXPORT**: if no segments are defined, asks whether to export the whole
  video with the current settings. If segments exist, exports each one to
  its own file. Choose the export mode first:
  - **LOSSY H.265** — small files, always 8-bit output. Exporting a 16-bit
    source through this truncates it — you'll get a confirmation dialog
    before it proceeds.
  - **LOSSLESS FFV1** — encodes at the source's actual bit depth (8- or
    16-bit), no compression loss, much larger files, written as `.mkv`
    (not `.mp4` — the MP4 container doesn't reliably support 16-bit/FFV1).

## 7. DM4 metadata overlay

**SHOW METADATA OVERLAY** is only selectable if the currently loaded video
has a `<video>.metadata.json` sidecar file next to it — which
`dm4_converter.py` writes automatically when it converts DM3/DM4 frames
(pixel size, field of view, voltage, magnification, operator, etc., pulled
from the first frame's DM4 tags). A plain video file opened directly won't
have this, and the checkbox stays disabled.

## 8. Other tools

- **HISTOGRAM** (button): opens a small window with a live intensity
  histogram of the current frame (mean/std in the title).
- **SCREENSHOT** (button or `C`): saves the current frame as a PNG.
- **RESET SETTINGS**: restores gamma, contrast method and its parameters,
  filter and its parameters, flat-field, and drift correction (including
  turning APPLY DRIFT CORRECTION back off) to their defaults. Does not
  touch the loaded video, segments, or theme.
- **THEME**: DARK / LIGHT.
- **FULLSCREEN** (checkbox or `F11`, `Esc` to exit).

## 9. Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `Left` / `Right` | Step one frame back / forward |
| `I` | Set IN point |
| `O` | Set OUT point |
| `X` | Clear IN/OUT selection |
| `A` | Add segment from current selection |
| `C` | Screenshot |
| `F11` | Toggle fullscreen |
| `Esc` | Exit fullscreen |
| `Q` | Quit |

## 10. Troubleshooting

- **Edge-strip drift correction doesn't seem to track anything**: make sure
  you're actually pressing **PLAY**, not just scrubbing the timeline — it
  needs sequential forward playback to accumulate frame-to-frame motion.
  If it's still not tracking, raise **MARGIN** (vignette/circular FOV
  footage almost always needs this above 0).
- **Drift correction method is set but the image doesn't move**: check
  **APPLY DRIFT CORRECTION** — the method dropdown only computes the shift,
  this checkbox is what actually applies it.
- **Exporting a 16-bit video looks washed out / lower quality than
  expected**: you likely exported with LOSSY H.265, which always truncates
  to 8-bit. Use LOSSLESS FFV1 to keep full precision (bigger file, `.mkv`).
- **Flat-field correction looks wrong after loading reference images**:
  check the status line under LOAD FLAT FIELD — if the dark and gain images
  weren't the same resolution as each other, or as the loaded video, they
  get resized automatically, which is logged there.
- **SHOW METADATA OVERLAY is greyed out**: the loaded video has no
  `<video>.metadata.json` sidecar — this only exists for videos produced by
  the DM4 converter, not videos opened directly.
