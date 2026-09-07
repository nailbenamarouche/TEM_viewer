# TEM Live Viewer — User Guide

Practical guide to operating `tem_main.py`, the real-time acquisition
software for the Ximea Megaview camera. For architecture/implementation
details, see [README.md](README.md).

## 1. Starting up

```bash
python tem_main.py
```

The window opens with the display showing "Camera not connected". Click
**Connect Camera** to start the live feed — this only starts *displaying*
frames; recording to disk is a separate step (see [Recording](#6-recording)).

## 2. Microscope Mode

The **Microscope Mode** dropdown switches between two presets. Selecting one
overwrites exposure, gain, contrast method, flat-field, denoising, binning,
and encoder — treat it as a starting point, not a lock.

| Setting | Image Mode (default) | Diffraction Mode |
|---|---|---|
| Exposure | 40 ms | 40 ms |
| Gain | 20 dB | 20 dB |
| Contrast method | Autocontrast | None |
| Flat-field | ON | OFF |
| NLM/Bilateral denoising | OFF | OFF |
| Binning | unchanged | forced to 1x1 |
| Encoder | CPU (libx265) | Lossless (FFV1) |
| Gamma | reset to 1.00 | reset to 1.00 |

Diffraction Mode turns image processing off and switches to lossless
recording, since diffraction patterns need to stay quantitatively
untouched — don't re-enable CLAHE/autocontrast/flat-field there if you need
the raw intensities to mean something.

## 3. Exposure & Gain

- **Exposure (ms)** and **Manual Gain (dB)** fields: type a value and press
  **Enter**, or use the **Up/Down arrow keys** while the field is focused —
  both apply immediately, no need to click Apply with the mouse. The Apply
  buttons still work if you prefer the mouse.
- **Auto Exposure/Gain (AEAG)**: toggles the camera's automatic exposure/gain
  algorithm. While ON, the exposure/gain fields are disabled (the camera is
  driving them) and exposure is allowed to range up to 80 ms (capped there so
  a dark scene can't tank the frame rate into single digits). Turning AEAG
  OFF restores manual control at whatever gain is currently set.
- Changing exposure changes the camera's native frame rate (roughly
  1000/exposure ms) — the **FPS** readout in the status bar is the actual
  measured rate, which should track this unless CLAHE/NLM/disk I/O are the
  bottleneck (see [Troubleshooting](#9-troubleshooting)).

## 4. Image processing

- **Gamma / Brightness / Contrast** sliders: manual tone adjustments,
  applied *last* in the pipeline (after CLAHE/autocontrast) so they always
  have a visible effect regardless of contrast method.
- **Contrast method** (radio buttons):
  - **Autocontrast (Recommended)** — default. Percentile-based auto-stretch.
  - **CLAHE** — local adaptive contrast enhancement. Costs meaningfully more
    CPU/GPU time per frame than Autocontrast.
  - **None** — raw values pass through untouched (used by Diffraction Mode).
- **Filter** (radio buttons): None / Gaussian / Median / Bilateral, with
  their own kernel-size/sigma fields.
- **NLM Denoising** (or **Bilateral Denoising (GPU)** if a CUDA GPU is
  detected) checkbox: an extra denoise pass before contrast enhancement.
  This is a fast bilateral-filter approximation on both CPU and GPU, not
  true Non-Local Means — real NLM is too slow for a live view (routinely
  150-250ms/frame, i.e. 4-6 FPS).
- **Flat-field correction** checkbox: corrects fixed-pattern sensor
  response using reference dark/flat images. If you see "WARNING: Could not
  load flat-field correction" in the log, the reference files aren't at the
  expected path on this machine — flat-field will silently do nothing until
  that's fixed.

## 5. Drift correction

Three modes (radio buttons in **Drift correction**):

- **None** — no correction.
- **Edge-strip** — tracks sample drift by correlating four strips sampled
  near the frame's edges, frame-to-frame. Two tuning controls:
  - **Margin**: how far in from the true edge to sample, in pixels (also
    trims each strip's ends inward, keeping it clear of the corners too).
    **TEM footage with a circular/vignetted field of view needs this raised
    above 0** — sampling right at the edge (and through the corners) lands
    on blank vignette with nothing to track, which looks like the
    correction "does nothing" no matter how much the sample actually
    drifts. Raise it until the drawn strip boxes sit inside the illuminated
    circle.
  - **Width**: thickness of the sampled band, in pixels.
  - Enabling this mode creates a `drift_log_<timestamp>.csv` in the working
    directory, logging every frame's measured (dx, dy, reliability). It's
    closed automatically when you switch drift mode or quit.
- **ROI (click+drag on preview)** — click and drag a box on the live image
  over a distinctive feature; drift correction locks onto that feature via
  template matching instead of the frame's edges (works even with a
  vignetted field of view, since you pick the tracked region yourself).
  Selection needs to be between 32 and 512 px on a side. Tracking
  re-acquires the feature automatically if it's briefly lost (fast motion,
  occlusion) rather than staying stuck.

With either mode active, the corrected image is shown with an overlay (green
strip boxes, or the ROI lock box) so you can visually confirm tracking is
holding.

## 6. Recording

- **Record: OFF/ON** button: starts/stops saving the live feed to disk,
  independent of the camera connection (connecting only starts the
  display). Turning recording off flushes the buffered segment to disk in
  the background — the display keeps running while that happens.
- **Pause/Resume**: pauses recording and flushes the current segment
  without disconnecting or stopping the display; resuming starts a new
  segment.
- Segments auto-flush every 1200 frames, or if the in-RAM buffer exceeds
  8 GB, whichever comes first.
- **Encoder**: GPU (hevc_nvenc) - Fast / **CPU (libx265) - Smallest**
  (default) / Lossless (FFV1) - Scientific.
- **Encoding Mode**: **High Quality (CQ)** — a single quality parameter
  (CQ for GPU, CRF for CPU libx265), lower = higher quality/bigger file,
  higher = smaller/more compressed, valid range 0-51. Or **Long Duration**
  — a target bitrate in Mbps instead, for predictable file sizes on long
  recordings.
- **Concatenate videos on quit** checkbox: on exit, joins all of this
  session's segments into one `session_<timestamp>_concat.mkv`, in the
  order they were actually recorded (tracked in a
  `<timestamp>_segments.json` manifest alongside the video files — this is
  what keeps concatenation order correct even if segments finish encoding
  out of sequence in the background).

## 7. Histogram, screenshots, log

- **H** or **Open Histogram**: opens a small window with a live intensity
  histogram (mean/std in the title), refreshed a few times a second.
- **C** or **Screenshot**: saves the next frame as a timestamped PNG in the
  output folder.
- The log window mirrors everything printed to the console (connection
  status, exposure/gain changes, encoding progress, errors).

## 8. Keyboard shortcuts

| Key | Action |
|---|---|
| `P` | Pause / Resume recording |
| `C` | Screenshot |
| `H` | Open histogram window |
| `R` | Reset processing/display settings to defaults |
| `F11` | Toggle fullscreen |
| `Esc` | Exit fullscreen |
| `Q` | Quit |
| `Up` / `Down` (in Exposure/Gain field) | Nudge value and apply immediately |
| `Enter` (in Exposure/Gain field) | Apply typed value |

**Reset (R)** restores gamma, brightness/contrast, contrast method, filters,
flat-field, denoising, and drift correction to their defaults. It does
**not** touch camera hardware settings (exposure/gain), microscope mode,
encoder, or audio — those are session configuration, not display tweaks.

## 9. Troubleshooting

- **FPS lower than expected / doesn't track exposure changes**: CLAHE and
  denoising both cost real per-frame time. If FPS doesn't move when you
  change exposure, check whether CLAHE or denoising is on — with GPU
  unavailable, both fall back to CPU, which is slower. FPS should track
  exposure closely with both off (contrast method: None, denoising off).
- **Edge-strip drift correction doesn't seem to do anything**: raise
  **Margin** (see [Drift correction](#5-drift-correction)) — this is almost
  always a vignette issue on circular-FOV footage, not a broken tracker.
- **ROI tracking loses the feature during fast motion**: this recovers on
  its own within a few frames by widening its search; if it's consistently
  losing lock, pick a higher-contrast/more distinctive feature for the ROI.
- **AEAG doesn't seem to change anything**: it's capped at 80 ms exposure
  (to protect frame rate) — in a genuinely dark scene it may still not be
  enough headroom; raise gain manually with AEAG off instead.
- **A recorded segment took a long time to encode**: check the CQ/CRF value
  under Encoding Mode — a low number (e.g. 12) is close to lossless and is
  legitimately slow on CPU even at a fast preset. Raise it (e.g. 20-28) for
  much faster encodes at a modest quality cost.
- **Concatenated video segments are in the wrong order**: shouldn't happen
  as of the segment-manifest fix — if it does, check that the
  `<timestamp>_segments.json` file next to the video segments matches the
  recording order; report it if it doesn't.
