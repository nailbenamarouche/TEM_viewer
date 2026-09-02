#!/usr/bin/env python3
"""
DM4 -> MP4 Converter / Launcher
--------------------------------
Standalone replacement for conversion.py: reads Gatan DM3/DM4 frame stacks
using ncempy (pure Python, no Digital Micrograph installation required) and
encodes them to an MP4 via ffmpeg, then hands the resulting file straight to
TEMVideoProcessor (pr_gui_ds.py).

Install the one new dependency with:
    pip install ncempy
"""

import os
import re
import json
import glob
import subprocess
import time
import numpy as np

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSpinBox, QComboBox, QProgressBar,
    QMessageBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import QThread, pyqtSignal

from ncempy.io import dm


# ============================================================
# Hierarchical hour/minute/second folder discovery
# ============================================================
# Capture sessions are laid out as:
#   <hour folder>/minute_00/second_00/*.dm4
#                 /minute_00/second_01/*.dm4
#                 /minute_01/second_00/*.dm4
#                 ...
# The prefix casing/spacing varies ("Minute_00", "minute00", ...), so
# matching is case-insensitive with an optional separator.
_MINUTE_RE = re.compile(r'^minute[_\s]?(\d+)$', re.IGNORECASE)
_SECOND_RE = re.compile(r'^second[_\s]?(\d+)$', re.IGNORECASE)
_DIGIT_RUN_RE = re.compile(r'(\d+)')


def _natural_key(path):
    """Sort key that orders embedded numbers numerically (frame2 < frame10),
    unlike a plain string sort where '10' sorts before '2'."""
    name = os.path.basename(path)
    return [int(tok) if tok.isdigit() else tok.lower() for tok in _DIGIT_RUN_RE.split(name)]


def _find_numbered_subdirs(root_dir, name_re):
    """Subdirectories of root_dir whose name matches name_re, sorted by the
    numeric suffix captured in the name (not alphabetically)."""
    matches = []
    try:
        entries = os.listdir(root_dir)
    except OSError:
        return matches
    for entry in entries:
        full = os.path.join(root_dir, entry)
        if not os.path.isdir(full):
            continue
        m = name_re.match(entry)
        if m:
            matches.append((int(m.group(1)), full))
    matches.sort(key=lambda t: t[0])
    return matches


def discover_dm4_files(root_dir, pattern):
    """Return an ordered list of frame files matching `pattern`.

    If `root_dir` is an "hour" folder containing minute_XX subfolders (each
    holding second_XX subfolders of frames), walk that hierarchy in numeric
    minute -> second -> filename order so concatenation stays in the correct
    chronological sequence. Otherwise, fall back to treating `root_dir` as a
    flat folder of frames (the original single-folder behavior), still with
    a natural numeric sort instead of a plain alphabetical one.
    """
    minute_dirs = _find_numbered_subdirs(root_dir, _MINUTE_RE)
    if not minute_dirs:
        return sorted(glob.glob(os.path.join(root_dir, pattern)), key=_natural_key)

    files = []
    for _, minute_path in minute_dirs:
        second_dirs = _find_numbered_subdirs(minute_path, _SECOND_RE)
        if not second_dirs:
            # Frames sitting directly in the minute folder (no second_XX level)
            files.extend(sorted(glob.glob(os.path.join(minute_path, pattern)), key=_natural_key))
            continue
        for _, second_path in second_dirs:
            files.extend(sorted(glob.glob(os.path.join(second_path, pattern)), key=_natural_key))
    return files


def scan_hierarchy_stats(root_dir, pattern):
    """Summarize a hierarchical folder for UI feedback: (num_minutes,
    num_seconds, num_files) - or None if root_dir isn't hierarchical."""
    minute_dirs = _find_numbered_subdirs(root_dir, _MINUTE_RE)
    if not minute_dirs:
        return None
    num_seconds = 0
    num_files = 0
    for _, minute_path in minute_dirs:
        second_dirs = _find_numbered_subdirs(minute_path, _SECOND_RE)
        if not second_dirs:
            num_files += len(glob.glob(os.path.join(minute_path, pattern)))
            continue
        for _, second_path in second_dirs:
            num_seconds += 1
            num_files += len(glob.glob(os.path.join(second_path, pattern)))
    return len(minute_dirs), num_seconds, num_files


# ============================================================
# DM4 metadata extraction
# ============================================================
# Field names below were verified against a real OneView/JEOL DM4 file's
# actual fileDM.getMetadata(0) output. Real files from other instruments/
# DigitalMicrograph versions may use different tag names, so every lookup
# has fallbacks and simply omits a field if none of its candidates exist -
# this must never fail a conversion just because metadata is incomplete.

def _first_present(tags, keys):
    for k in keys:
        v = tags.get(k)
        if v is not None and v != '':
            return v
    return None


def _jsonable(v):
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def extract_dm4_metadata(path):
    """Pull pixel calibration plus a curated set of instrument/acquisition
    fields from a single DM3/DM4 file. Returns a JSON-serializable dict,
    or None if the file couldn't be read - metadata is a nice-to-have and
    must never be allowed to fail a conversion."""
    try:
        with dm.fileDM(path) as f:
            ds = f.getDataset(0)
            tags = f.getMetadata(0)
    except Exception as e:
        print(f"Could not read DM4 metadata from {path}: {e}")
        return None

    info = {'source_file': os.path.basename(path)}

    pixel_size = ds.get('pixelSize')
    pixel_unit = ds.get('pixelUnit')
    data = ds.get('data')
    if pixel_size is not None and pixel_unit is not None and len(pixel_size) >= 2 and data is not None:
        py, px = float(pixel_size[0]), float(pixel_size[1])
        h, w = data.shape[:2]
        info['pixel_size_x'] = px
        info['pixel_size_y'] = py
        info['pixel_unit'] = str(pixel_unit[-1])
        info['image_width_px'] = int(w)
        info['image_height_px'] = int(h)
        info['fov_width'] = px * w
        info['fov_height'] = py * h

    fields = {
        'voltage': _first_present(tags, ['Microscope Info Formatted Voltage']),
        'magnification': _first_present(tags, [
            'Microscope Info Formatted Actual Mag',
            'Microscope Info Formatted Indicated Mag',
        ]),
        'illumination_mode': _first_present(tags, ['Microscope Info Illumination Mode']),
        'exposure_s': _first_present(tags, [
            'DataBar Exposure Time (s)',
            'Acquisition Parameters High Level Exposure (s)',
        ]),
        'binning': _first_present(tags, ['DataBar Binning']),
        'microscope': _first_present(tags, ['Session Info Microscope', 'Microscope Info Name']),
        'operator': _first_present(tags, ['Session Info Operator']),
        'specimen': _first_present(tags, ['Session Info Specimen']),
        'acquisition_date': _first_present(tags, ['DataBar Acquisition Date']),
        'acquisition_time': _first_present(tags, ['DataBar Acquisition Time']),
    }
    for k, v in fields.items():
        v = _jsonable(v)
        if v is not None:
            info[k] = v

    return info


def save_metadata_sidecar(output_path, metadata):
    """Write metadata next to the converted video as <output_path>.metadata.json."""
    if not metadata:
        return
    try:
        with open(output_path + ".metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    except OSError as e:
        print(f"Could not write metadata sidecar: {e}")


# ============================================================
# DIALOG STYLESHEET
# ============================================================
# Self-contained: this dialog does not rely on (or affect) whatever
# stylesheet the main app applies at the QApplication level. Palette is
# built from a small set of neutral layers - dialog background, panel,
# recessed input, raised button - each a step apart in brightness, so
# hierarchy reads from contrast rather than color. Slate-blue (#3b6ea5)
# is the one accent, reserved for the single primary action, the focus
# ring, and progress. Nothing else is tinted.
DIALOG_STYLESHEET = """
QDialog {
    background: #1e1f23;
}
QWidget {
    background: transparent;
    color: #cfd0d4;
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 9pt;
}
QGroupBox {
    background: #26272c;
    border: 1px solid #42434a;
    border-radius: 6px;
    margin-top: 16px;
    padding: 16px 14px 14px 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 3px 8px;
    color: #b6b7bc;
    font-weight: 600;
    font-size: 8.5pt;
    background: #2c2d33;
    border: 1px solid #42434a;
    border-radius: 4px;
}
QLabel {
    color: #a9aab0;
    background: transparent;
}
QLineEdit, QSpinBox, QComboBox {
    background: #1a1b1e;
    border: 1px solid #46474e;
    border-radius: 4px;
    padding: 5px 8px;
    color: #d8d9dc;
    selection-background-color: #3b6ea5;
}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
    border-color: #5b5c66;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #5b86ad;
    background: #1c1d21;
}
QComboBox::drop-down {
    border-left: 1px solid #46474e;
    width: 22px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #b6b7bc;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #26272c;
    border: 1px solid #46474e;
    color: #d8d9dc;
    selection-background-color: #33475c;
    outline: none;
}
QPushButton {
    background: #2a2b30;
    border: 1px solid #46474e;
    border-radius: 5px;
    padding: 7px 16px;
    color: #cfd0d4;
    min-height: 20px;
}
QPushButton:hover {
    background: #34353c;
    border-color: #5b5c66;
}
QPushButton:pressed {
    background: #222327;
    border-color: #46474e;
}
QPushButton:disabled {
    color: #5f6066;
    background: #232428;
    border-color: #2c2d31;
}
QPushButton#primary {
    background: #3b6ea5;
    border: 1px solid #4a7fb8;
    color: #eef4fa;
    font-weight: 600;
}
QPushButton#primary:hover {
    background: #4478ae;
    border-color: #5689c1;
}
QPushButton#primary:pressed {
    background: #335f8f;
}
QPushButton#primary:disabled {
    background: #2b3d4d;
    border-color: #2f4152;
    color: #6d7f8f;
}
QPushButton#browse {
    padding: 5px 12px;
    min-height: 0px;
    color: #a9aab0;
}
QPushButton#ghost {
    background: transparent;
    border: 1px solid transparent;
    color: #9a9ba2;
    padding: 7px 10px;
}
QPushButton#ghost:hover {
    color: #d8d9dc;
    background: #26272b;
    border-color: #34353a;
}
QPushButton#ghost:pressed {
    background: #1e1f23;
}
QProgressBar {
    background: #1a1b1e;
    border: 1px solid #42434a;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #3b6ea5;
    border-radius: 3px;
}
"""


class ConversionWorker(QThread):
    """Runs the DM4->MP4 conversion off the GUI thread."""

    progress = pyqtSignal(int, int, float)   # current, total, encode fps
    finished_ok = pyqtSignal(str)            # output path
    failed = pyqtSignal(str)                 # error message
    warning = pyqtSignal(str)                # non-fatal heads-up (e.g. bit-depth truncation)

    def __init__(self, input_dir, output_path, pattern, source_fps, target_fps,
                 preset, crf, scale_width, interp_mode, lossless=False, parent=None):
        super().__init__(parent)
        self.input_dir = input_dir
        self.output_path = output_path
        self.pattern = pattern
        self.source_fps = source_fps
        self.target_fps = target_fps
        self.preset = preset
        self.crf = crf
        self.scale_width = scale_width
        self.interp_mode = interp_mode
        self.lossless = lossless
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        """Thread entry point: runs the conversion, emitting failed(message) instead
        of raising if anything goes wrong."""
        try:
            self._convert()
        except Exception as e:
            self.failed.emit(str(e))

    def _convert(self):
        files = discover_dm4_files(self.input_dir, self.pattern)
        if not files:
            self.failed.emit(f"No files matching '{self.pattern}' in {self.input_dir}")
            return

        # ---- Metadata: pixel calibration + instrument info, best-effort ----
        # Saved once encoding parameters are known below, so the sidecar also
        # records the bit depth/codec actually used - the processor reads
        # this back to decide how to open the file.
        metadata = extract_dm4_metadata(files[0])

        # ---- Inspect the first frame to fix resolution / dtype ----
        first = dm.dmReader(files[0])['data']
        if first.ndim != 2:
            self.failed.emit("Expected single-frame 2D DM3/DM4 images.")
            return
        height, width = first.shape
        dtype = first.dtype

        needs_global_scaling = dtype.kind == 'f' or dtype not in (np.uint8, np.uint16)
        global_min, global_max = None, None

        if needs_global_scaling:
            # Fix for the original script's contrast-flicker bug: it rescaled
            # every frame independently to its own min/max, so brightness
            # jumped around from frame to frame. Here we scan once and use a
            # single min/max for the whole stack.
            global_min, global_max = np.inf, -np.inf
            for i, f in enumerate(files):
                if self._abort:
                    return
                arr = dm.dmReader(f)['data']
                global_min = min(global_min, float(arr.min()))
                global_max = max(global_max, float(arr.max()))
                if i % 25 == 0:
                    self.progress.emit(i, len(files) * 2, 0.0)
            if global_max <= global_min:
                global_max = global_min + 1.0

        pix_fmt = "gray" if dtype == np.uint8 else "gray16le"

        if not self.lossless and pix_fmt != "gray":
            # Flag: the lossy path always forces 8-bit yuv420p below, so a
            # 16-bit source's extra precision is thrown away right here -
            # this is the truncation the caller should be warned about.
            self.warning.emit(
                f"Source frames are {pix_fmt} (16-bit), but Lossy mode encodes "
                "to 8-bit H.264 - this truncates bit depth. Use Lossless FFV1 "
                "to keep the full precision."
            )

        vf_parts = []
        if self.scale_width > 0:
            vf_parts.append(f"scale={self.scale_width}:-1:flags=lanczos")
        if self.interp_mode == "mci":
            vf_parts.append(
                f"minterpolate=fps={self.target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
            )
        else:
            vf_parts.append(f"minterpolate=fps={self.target_fps}:mi_mode=blend")
        if not self.lossless:
            # Truncation point: forces 8-bit chroma-subsampled yuv420p even
            # when pix_fmt above is gray16le, i.e. this is where a 16-bit
            # source silently loses its lower 8 bits in the lossy path.
            vf_parts.append("format=yuv420p")
        vf_string = ",".join(vf_parts)

        out_dir = os.path.dirname(self.output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)
        log_path = os.path.join(out_dir or ".", "ffmpeg.log")

        if self.lossless:
            # FFV1: lossless, intra-only (every frame is a keyframe, so the
            # processor can seek to any frame cheaply and exactly), and
            # encodes gray/gray16le directly - no forced 8-bit conversion.
            codec = "ffv1"
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pixel_format", pix_fmt,
                "-video_size", f"{width}x{height}",
                "-framerate", str(self.source_fps),
                "-i", "-",
                "-vf", vf_string,
                "-c:v", "ffv1",
                "-level", "3",
                "-g", "1",
                "-slicecrc", "1",
                "-pix_fmt", pix_fmt,
                "-r", str(self.target_fps),
                "-threads", "0",
                self.output_path,
            ]
        else:
            codec = "libx264"
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pixel_format", pix_fmt,
                "-video_size", f"{width}x{height}",
                "-framerate", str(self.source_fps),
                "-i", "-",
                "-vf", vf_string,
                "-c:v", "libx264",
                "-preset", self.preset,
                "-crf", str(self.crf),
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-r", str(self.target_fps),
                "-threads", "0",
                self.output_path,
            ]

        if metadata is not None:
            metadata['video_mode'] = "lossless" if self.lossless else "lossy"
            metadata['video_pixel_format'] = pix_fmt
            metadata['video_codec'] = codec
            metadata['video_bit_depth'] = 8 if pix_fmt == "gray" else 16
        save_metadata_sidecar(self.output_path, metadata)

        try:
            log_file = open(log_path, "wb")
        except OSError as e:
            self.failed.emit(f"Could not open log file: {e}")
            return

        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log_file, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            log_file.close()
            self.failed.emit("ffmpeg not found. Install it and add it to PATH.")
            return

        start = time.time()
        sent = 0
        skipped = 0
        base = len(files) if needs_global_scaling else 0  # offset progress bar past the scan pass

        for i, f in enumerate(files):
            if self._abort:
                break
            try:
                arr = dm.dmReader(f)['data']
            except Exception:
                skipped += 1
                continue

            if arr.shape != (height, width):
                # Fix: original script never checked this. One mismatched
                # frame silently desyncs every frame after it in the raw pipe.
                skipped += 1
                continue

            if needs_global_scaling:
                arr = ((arr.astype(np.float64) - global_min) / (global_max - global_min) * 65535.0)
                arr = np.clip(arr, 0, 65535).astype(np.uint16)
            elif arr.dtype != dtype:
                skipped += 1
                continue

            arr = np.ascontiguousarray(arr)
            try:
                proc.stdin.write(arr.tobytes())
            except (BrokenPipeError, OSError):
                # Fix: original script kept looping and printed one error per
                # remaining frame once ffmpeg had already died. Stop cleanly.
                self.failed.emit("ffmpeg exited unexpectedly while receiving frames — see ffmpeg.log")
                proc.kill()
                log_file.close()
                return

            sent += 1
            elapsed = time.time() - start
            fps = sent / elapsed if elapsed > 0 else 0.0
            self.progress.emit(base + i, base + len(files), fps)

        proc.stdin.close()
        ret = proc.wait()
        log_file.close()

        if self._abort:
            self.failed.emit("Conversion cancelled.")
            return
        if ret != 0:
            self.failed.emit(f"ffmpeg exited with code {ret}. See {log_path}")
            return

        try:
            os.remove(log_path)
        except OSError:
            pass

        if not os.path.exists(self.output_path) or sent == 0:
            self.failed.emit("No video was produced.")
            return

        self.finished_ok.emit(self.output_path)


class DM4ConverterDialog(QDialog):
    """
    First-run launcher: convert a folder of DM3/DM4 frames into an MP4
    (no Gatan Digital Micrograph installation needed), or skip straight to
    opening an existing video. Emits video_ready(path) either way.
    """
    video_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TEM Video Processor — DM4 to Video")
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.resize(560, 480)
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        io_group = QGroupBox("Source / Output")
        io_form = QFormLayout()
        io_form.setVerticalSpacing(10)
        io_form.setHorizontalSpacing(12)

        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self.input_edit = QLineEdit()
        self.input_edit.setToolTip(
            "A flat folder of DM3/DM4 frames, OR an 'hour' folder containing\n"
            "minute_XX subfolders, each containing second_XX subfolders of frames.\n"
            "The hierarchical layout is auto-detected and walked in the correct order."
        )
        in_browse = QPushButton("Browse…")
        in_browse.setObjectName("browse")
        in_browse.clicked.connect(self._browse_input)
        in_row.addWidget(self.input_edit)
        in_row.addWidget(in_browse)
        io_form.addRow("DM4/DM3 folder:", in_row)

        self.pattern_edit = QLineEdit("*.dm4")
        self.pattern_edit.editingFinished.connect(self._rescan_current_input)
        io_form.addRow("File pattern:", self.pattern_edit)

        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.output_edit = QLineEdit()
        out_browse = QPushButton("Browse…")
        out_browse.setObjectName("browse")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_edit)
        out_row.addWidget(out_browse)
        io_form.addRow("Output video:", out_row)

        io_group.setLayout(io_form)
        layout.addWidget(io_group)

        enc_group = QGroupBox("Encoding")
        enc_form = QFormLayout()
        enc_form.setVerticalSpacing(10)
        enc_form.setHorizontalSpacing(12)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Lossy H.264 (8-bit, smaller files)",
            "Lossless FFV1 (native bit depth)",
        ])
        self.quality_combo.setToolTip(
            "Lossy: always encodes to 8-bit yuv420p via H.264 - if the source\n"
            "DM3/DM4 frames are 16-bit, this truncates them to 8 bits.\n"
            "Lossless: encodes with FFV1 at the source's native bit depth\n"
            "(8-bit gray or 16-bit gray16le), so nothing is thrown away. Files\n"
            "are much larger and are written as .mkv (not .mp4)."
        )
        self.quality_combo.currentIndexChanged.connect(self._on_quality_changed)
        enc_form.addRow("Quality:", self.quality_combo)

        self.source_fps_spin = QSpinBox()
        self.source_fps_spin.setRange(1, 240)
        self.source_fps_spin.setValue(25)
        enc_form.addRow("Source FPS:", self.source_fps_spin)

        self.target_fps_spin = QSpinBox()
        self.target_fps_spin.setRange(1, 240)
        self.target_fps_spin.setValue(60)
        enc_form.addRow("Target FPS:", self.target_fps_spin)

        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(0, 7680)
        self.scale_spin.setValue(1920)
        self.scale_spin.setSpecialValueText("Native (slow)")
        enc_form.addRow("Scale width (px):", self.scale_spin)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "fast", "medium"])
        enc_form.addRow("x264 preset:", self.preset_combo)

        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(23)
        enc_form.addRow("CRF:", self.crf_spin)

        self.interp_combo = QComboBox()
        self.interp_combo.addItems(["blend (fast)", "mci (slow, smoother)"])
        enc_form.addRow("Interpolation:", self.interp_combo)

        enc_group.setLayout(enc_form)
        layout.addWidget(enc_group)

        layout.addStretch()

        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setObjectName("primary")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        self.skip_btn = QPushButton("Skip — open existing video instead")
        self.skip_btn.setObjectName("ghost")
        self.skip_btn.clicked.connect(self._skip_to_open_video)
        btn_row.addWidget(self.convert_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.skip_btn)
        layout.addLayout(btn_row)

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select folder with DM3/DM4 frames (or an 'hour' folder)"
        )
        if path:
            self.input_edit.setText(path)
            if not self.output_edit.text():
                ext = ".mkv" if self.quality_combo.currentIndex() == 1 else ".mp4"
                self.output_edit.setText(os.path.join(path, "video" + ext))
            self._scan_input_folder(path)

    def _rescan_current_input(self):
        path = self.input_edit.text().strip()
        if path and os.path.isdir(path):
            self._scan_input_folder(path)

    def _scan_input_folder(self, path):
        """If `path` is a hierarchical hour folder, report what was found and
        auto-suggest a source FPS derived from the real capture timing: each
        second_XX folder represents exactly one recorded second, so total
        frames / total second-folders is the true average capture rate."""
        pattern = self.pattern_edit.text().strip() or "*.dm4"
        stats = scan_hierarchy_stats(path, pattern)
        if stats is None:
            return
        num_minutes, num_seconds, num_files = stats
        if num_seconds > 0 and num_files > 0:
            avg_fps = num_files / num_seconds
            self.source_fps_spin.setValue(max(1, round(avg_fps)))
            self.status_label.setText(
                f"Hierarchical folder detected: {num_minutes} minute(s), {num_seconds} second(s), "
                f"{num_files} frame(s). Source FPS auto-set to {round(avg_fps)}."
            )
        else:
            self.status_label.setText(
                f"Hierarchical folder detected ({num_minutes} minute(s)) but no frames found "
                f"matching '{pattern}'."
            )

    def _on_quality_changed(self, index):
        """index 1 = lossless FFV1. Presets/CRF are x264-only, so grey them
        out; and since FFV1 (and 16-bit gray16le) isn't reliably supported by
        the MP4 muxer, switch the suggested output extension to .mkv."""
        lossless = index == 1
        self.preset_combo.setEnabled(not lossless)
        self.crf_spin.setEnabled(not lossless)

        current = self.output_edit.text().strip()
        if current:
            root, ext = os.path.splitext(current)
            if lossless and ext.lower() == ".mp4":
                self.output_edit.setText(root + ".mkv")
            elif not lossless and ext.lower() == ".mkv":
                self.output_edit.setText(root + ".mp4")

    def _browse_output(self):
        lossless = self.quality_combo.currentIndex() == 1
        filter_str = "MKV Video (*.mkv)" if lossless else "MP4 Video (*.mp4)"
        path, _ = QFileDialog.getSaveFileName(self, "Save video as", "", filter_str)
        if path:
            self.output_edit.setText(path)

    def _skip_to_open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv);;All Files (*.*)"
        )
        if path:
            self.video_ready.emit(path)
            self.accept()

    def _start_conversion(self):
        input_dir = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not input_dir or not os.path.isdir(input_dir):
            QMessageBox.warning(self, "Invalid input", "Please choose a valid folder of DM3/DM4 files.")
            return
        if not output_path:
            QMessageBox.warning(self, "Invalid output", "Please choose an output video path.")
            return

        lossless = self.quality_combo.currentIndex() == 1
        if lossless and os.path.splitext(output_path)[1].lower() == ".mp4":
            # FFV1/gray16le isn't reliably supported by the MP4 muxer -
            # catches the case where the user typed the path by hand instead
            # of using Browse (which keeps the extension in sync).
            root, _ = os.path.splitext(output_path)
            output_path = root + ".mkv"
            self.output_edit.setText(output_path)

        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.skip_btn.setEnabled(False)
        self.status_label.setText("Scanning files…")

        self.worker = ConversionWorker(
            input_dir=input_dir,
            output_path=output_path,
            pattern=self.pattern_edit.text().strip() or "*.dm4",
            source_fps=self.source_fps_spin.value(),
            target_fps=self.target_fps_spin.value(),
            preset=self.preset_combo.currentText(),
            crf=self.crf_spin.value(),
            scale_width=self.scale_spin.value(),
            interp_mode="mci" if self.interp_combo.currentIndex() == 1 else "blend",
            lossless=self.quality_combo.currentIndex() == 1,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.warning.connect(self._on_warning)
        self.worker.start()

    def _cancel_conversion(self):
        if self.worker:
            self.worker.abort()
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling…")

    def _on_progress(self, current, total, fps):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        self.status_label.setText(f"Encoding… {current}/{total}  ({fps:.1f} img/s)")

    def _on_finished(self, output_path):
        self.status_label.setText(f"Done: {output_path}")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.skip_btn.setEnabled(True)
        QMessageBox.information(self, "Conversion complete", f"Video created:\n{output_path}")
        self.video_ready.emit(output_path)
        self.accept()

    def _on_warning(self, message):
        QMessageBox.warning(self, "Bit-depth warning", message)

    def _on_failed(self, message):
        self.status_label.setText("Failed.")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.skip_btn.setEnabled(True)
        QMessageBox.critical(self, "Conversion failed", message)
