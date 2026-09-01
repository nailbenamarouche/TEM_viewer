import cv2
import numpy as np
import time
import datetime
import ctypes
import subprocess
import io
import threading
import queue
import os
import re
import xxhash
import sys
import traceback
import warnings
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ximea import xiapi
import shutil

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Windows timer - only on Windows
if sys.platform == 'win32':
    ctypes.windll.winmm.timeBeginPeriod(1)

# MODE SELECTION
RECORD_MODE = "raw"
AUTO_FLUSH_EVERY = 1200
RAM_CAP_MB = 8000  # 8GB safety limit

# Set True to log per-frame CLAHE timing to console (diagnostic only).
DEBUG_CLAHE_TIMING = True

# ==========================================
# THEME STYLESHEETS
# Visual language ported from pr_gui_ds_final.py: layered palette (window ->
# chrome -> panel -> recessed input -> button), one muted accent color
# reserved for primary actions, bordered panels/buttons/inputs throughout,
# and checkbox/radio "checked" states drawn as a solid QSS fill - no
# external image assets anywhere in this file.
# ==========================================
DARK_STYLESHEET = """
QMainWindow { background: #17181b; }
QWidget { background: transparent; color: #cfd0d4; font-family: "Segoe UI", "Inter", "Arial", sans-serif; font-size: 9pt; }
QGroupBox {
    background: #26272c; border: 1px solid #42434a; border-radius: 6px;
    margin-top: 12px; padding-top: 6px; padding: 6px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 10px; padding: 1px 8px; color: #b6b7bc;
    font-weight: 600; font-size: 8pt; letter-spacing: 1px; text-transform: uppercase;
    background: #2c2d33; border: 1px solid #42434a; border-radius: 4px;
}
QLabel { color: #9a9ba2; font-size: 9pt; }
QPushButton {
    background: #2a2b30; border: 1px solid #46474e; border-radius: 5px;
    padding: 4px 10px; color: #cfd0d4; font-weight: 500; font-size: 9pt; min-height: 20px;
}
QPushButton:hover { background: #34353c; border-color: #5b5c66; }
QPushButton:pressed { background: #222327; border-color: #46474e; }
QPushButton:disabled { color: #5f6066; background: #232428; border-color: #2c2d31; }
QPushButton:checked { background: #33475c; border: 1px solid #4a7fb8; color: #eaf1f8; }
QPushButton#primary { background: #3b6ea5; border: 1px solid #4a7fb8; color: #eef4fa; font-weight: 600; }
QPushButton#primary:hover { background: #4478ae; border-color: #5689c1; }
QPushButton#primary:pressed { background: #335f8f; }
QLineEdit, QComboBox {
    background: #1a1b1e; border: 1px solid #46474e; border-radius: 4px;
    padding: 3px 8px; color: #d8d9dc; font-size: 9pt;
}
QLineEdit:hover, QComboBox:hover { border-color: #5b5c66; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #5b86ad; background: #1c1d21; }
QComboBox::drop-down { border-left: 1px solid #46474e; width: 22px; }
QComboBox::down-arrow {
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #b6b7bc; margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #26272c; border: 1px solid #46474e; border-radius: 4px;
    color: #d8d9dc; selection-background-color: #33475c; outline: none;
}
QSlider::groove:horizontal { height: 3px; background: #34353a; border-radius: 2px; }
QSlider::handle:horizontal { background: #5b86ad; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; border: none; }
QSlider::handle:horizontal:hover { background: #6a97bc; }
QCheckBox { spacing: 6px; padding: 2px 0; color: #cfd0d4; }
QCheckBox::indicator { width: 15px; height: 15px; background: #1a1b1e; border: 1px solid #4a4b52; border-radius: 3px; }
QCheckBox::indicator:checked { background: #3b6ea5; border-color: #5b86ad; }
QCheckBox::indicator:hover { border-color: #6a97bc; }
QRadioButton { spacing: 6px; padding: 2px 0; color: #cfd0d4; }
QRadioButton::indicator { width: 15px; height: 15px; background: #1a1b1e; border: 1px solid #4a4b52; border-radius: 8px; }
QRadioButton::indicator:checked { background: #3b6ea5; border-color: #5b86ad; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #3a3b40; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #47484f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollArea { border: none; background: transparent; }
QTextEdit {
    background: #0d0d0d; color: #d4d4d4; border: 1px solid #46474e; border-radius: 4px;
    font-family: Consolas, monospace; font-size: 9pt;
}
QToolTip {
    background: #26272c; color: #d8d9dc; border: 1px solid #46474e; border-radius: 5px;
    padding: 7px 12px; font-size: 8.5pt;
}
"""

LIGHT_STYLESHEET = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eef2f9, stop:0.5 #f4f7fb, stop:1 #e8edf6);
}
QWidget { background: transparent; color: #2c3a56; font-family: "Segoe UI", "Inter", "Arial", sans-serif; font-size: 9pt; }
QGroupBox {
    background: rgba(255, 255, 255, 0.55); border: 1px solid rgba(40, 90, 180, 0.12); border-radius: 12px;
    margin-top: 12px; padding-top: 6px; padding: 6px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 8px; color: #2660c0;
    font-weight: 600; font-size: 8pt; letter-spacing: 1.5px; text-transform: uppercase;
    background: rgba(255, 255, 255, 0.85); border-radius: 4px;
}
QLabel { color: #4a5878; font-size: 9pt; }
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(222, 232, 248, 0.95));
    color: #1a3a70; border: 1px solid rgba(40, 90, 180, 0.22); border-radius: 8px;
    padding: 4px 10px; font-weight: 500; font-size: 9pt; min-height: 24px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(220, 235, 255, 1.0), stop:1 rgba(190, 215, 250, 1.0));
    border: 1px solid rgba(40, 100, 200, 0.5);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(190, 215, 250, 1.0), stop:1 rgba(165, 195, 235, 1.0));
    border: 1px solid rgba(40, 100, 200, 0.3);
}
QPushButton:disabled { color: #9aa5bd; background: rgba(240, 244, 250, 0.6); border-color: rgba(40, 90, 180, 0.08); }
QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(80, 150, 255, 0.3), stop:1 rgba(50, 120, 230, 0.35));
    border: 2px solid rgba(40, 100, 200, 0.6);
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2fa768, stop:1 #1f8a52);
    border-color: #1f8a52; color: #ffffff;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3ec27c, stop:1 #2aa062);
    border-color: #2aa062;
}
QLineEdit, QComboBox {
    background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(40, 90, 180, 0.2); border-radius: 6px;
    padding: 3px 8px; color: #1a2a45; font-size: 9pt;
}
QLineEdit:focus, QComboBox:focus { border-color: rgba(40, 100, 200, 0.55); background: rgba(255, 255, 255, 1.0); }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #2660c0; margin-right: 5px;
}
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid rgba(40, 90, 180, 0.15); border-radius: 6px;
    selection-background-color: rgba(40, 120, 230, 0.18);
}
QSlider::groove:horizontal {
    height: 3px; border-radius: 2px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(40, 100, 200, 0.18), stop:1 rgba(40, 100, 200, 0.08));
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a80e0, stop:1 #2660c0);
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; border: none;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a9aff, stop:1 #3a78d8);
}
QCheckBox { spacing: 6px; padding: 2px 0; color: #2c3a56; }
QCheckBox::indicator { width: 14px; height: 14px; background: rgba(255, 255, 255, 0.9); border: 2px solid rgba(40, 90, 180, 0.3); border-radius: 4px; }
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3ec27c, stop:1 #1f8a52);
    border-color: #1f8a52;
}
QCheckBox::indicator:hover { border-color: rgba(40, 100, 200, 0.5); }
QRadioButton { spacing: 6px; padding: 2px 0; color: #2c3a56; }
QRadioButton::indicator { width: 14px; height: 14px; background: rgba(255, 255, 255, 0.9); border: 2px solid rgba(40, 90, 180, 0.3); border-radius: 7px; }
QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a80e0, stop:1 #2660c0);
    border-color: #2660c0;
}
QScrollBar:vertical { background: rgba(40, 90, 180, 0.08); width: 3px; border-radius: 2px; }
QScrollBar::handle:vertical { background: rgba(40, 100, 200, 0.3); border-radius: 2px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(40, 100, 200, 0.5); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollArea { border: none; background: transparent; }
QTextEdit {
    background: rgba(255, 255, 255, 0.9); color: #1a2a45; border: 1px solid rgba(40, 90, 180, 0.2); border-radius: 4px;
    font-family: Consolas, monospace; font-size: 9pt;
}
QToolTip {
    background: rgba(255, 255, 255, 0.98); color: #1a2a45; border: 1px solid rgba(40, 90, 180, 0.25);
    border-radius: 6px; padding: 8px 14px; font-size: 8.5pt;
}
"""

# Colors for the handful of widgets that set their own inline stylesheet and
# so aren't reachable by the QSS above (panel/toolbar chrome, dim labels,
# camera status text) - kept out of the QSS strings themselves so both the
# stylesheet and these call sites stay theme-aware from one source of truth.
THEME_COLORS = {
    'dark': {
        'panel_bg': '#17181b',
        'toolbar_bg': '#1e1f23',
        'toolbar_border': '#2b2c30',
        'dim_text': '#8a8b90',
        'success': '#5a946e',
        'error': '#b5555a',
        'warning': '#b8863f',
        'info': '#5b8ab8',
    },
    'light': {
        'panel_bg': '#f4f7fb',
        'toolbar_bg': 'rgba(255, 255, 255, 0.6)',
        'toolbar_border': 'rgba(40, 90, 180, 0.1)',
        'dim_text': '#5a6888',
        'success': '#1f8a52',
        'error': '#d43a3a',
        'warning': '#c97a00',
        'info': '#2660c0',
    },
}


def build_theme_stylesheet(theme):
    """Full QSS for the given theme: the generic widget rules plus colors for
    the few objectName-targeted panels (video display, toolbar chrome, status
    bar, dim labels) shared by the main window and its Histogram/Log windows."""
    t = THEME_COLORS[theme]
    base = LIGHT_STYLESHEET if theme == 'light' else DARK_STYLESHEET
    extra = f"""
QLabel#image_label {{ background: {t['panel_bg']}; }}
QWidget#toolbar_container {{ border-left: 1px solid {t['toolbar_border']}; background: {t['toolbar_bg']}; }}
QWidget#status_bar_widget {{ border-top: 1px solid {t['toolbar_border']}; background: {t['toolbar_bg']}; }}
QLabel#path_label {{ color: {t['dim_text']}; font-size: 8pt; }}
"""
    return base + extra


# ==========================================
# IMAGE PROCESSING WORKER THREAD
# ==========================================
class ImageProcessingWorker(threading.Thread):
    """Background thread that runs the image processing pipeline (flat-field,
    gamma/contrast, filters, NLM, CLAHE/autocontrast) on GPU when available,
    decoupling it from the camera acquisition loop."""

    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self._running = True

        # UI Sync variables (Set by Main Thread)
        self.brightness = 0.0
        self.contrast = 1.0
        self.gamma = 1.0

        # Filter variables (NEW: Wired for Gaussian, Median, Bilateral)
        self.filter_type = 0  # 0: None, 1: Gaussian, 2: Median, 3: Bilateral
        self.gaussian_kernel = 3
        self.gaussian_sigma = 1.0
        self.median_kernel = 3
        self.bilateral_d = 9
        self.bilateral_sigmaColor = 75
        self.bilateral_sigmaSpace = 75

        self.contrast_method = 1  # 0: Autocontrast, 1: CLAHE, 2: None
        self.enable_flatfield = True
        self.D = None
        self.G = None
        self.enable_nlm = False  # NLM toggle, default OFF
        self.debug_timing = DEBUG_CLAHE_TIMING

        try:
            self.use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        except (AttributeError, cv2.error):
            self.use_gpu = False
        print(f"Worker using GPU: {self.use_gpu}")

        self.gpu_frame = cv2.cuda_GpuMat() if self.use_gpu else None
        self.gpu_result = cv2.cuda_GpuMat() if self.use_gpu else None
        
        # CLAHE parameters
        if self.use_gpu:
            self.gpu_clahe = cv2.cuda.createCLAHE(clipLimit=1.5, tileGridSize=(16, 16))
            self.clahe = None
        else:
            self.clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(16, 16))
            self.gpu_clahe = None

    def run(self):
        """Thread entry point: pulls raw frames from input_queue, runs apply_pipeline
        on each, and pushes the result to output_queue (dropping a stale queued
        result first if the consumer hasn't kept up)."""
        while self._running:
            try:
                frame = self.input_queue.get(timeout=0.1)
                processed = self.apply_pipeline(frame)

                if self.output_queue.qsize() > 1:
                    try:
                        self.output_queue.get_nowait()
                    except Exception as e:
                        print(f"Queue cleanup error: {e}")
                        pass
                self.output_queue.put(processed)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing Worker Error: {e}")
                traceback.print_exc()

    def apply_pipeline(self, frame):
        """Runs the full per-frame processing chain: flat-field correction, gamma/
        brightness/contrast, the selected denoise filter (Gaussian/median/bilateral),
        optional NLM denoising, then CLAHE or autocontrast - using the GPU path for
        CLAHE/NLM when available.

        Args:
            frame: Raw grayscale frame from the camera.

        Returns:
            The fully processed frame, same shape as input.
        """
        # 1. Flat-field correction
        if self.enable_flatfield and self.D is not None and self.G is not None:
            if frame.shape == self.D.shape:
                frame = np.clip((frame.astype(np.float32) - self.D) * self.G, 0, 255).astype(np.uint8)

        # 2. Gamma & Brightness/Contrast
        if self.gamma != 1.0:
            lut = np.array([((i / 255.0) ** self.gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            frame = cv2.LUT(frame, lut)
        
        if self.brightness != 0.0 or self.contrast != 1.0:
            frame = np.clip(frame.astype(np.float32) * self.contrast + self.brightness, 0, 255).astype(np.uint8)

        # 3. NEW: Apply Gaussian, Median, or Bilateral filters
        if self.filter_type == 1:  # Gaussian
            k = self.gaussian_kernel if self.gaussian_kernel % 2 == 1 else self.gaussian_kernel + 1
            frame = cv2.GaussianBlur(frame, (k, k), self.gaussian_sigma)
        elif self.filter_type == 2:  # Median
            k = self.median_kernel if self.median_kernel % 2 == 1 else self.median_kernel + 1
            frame = cv2.medianBlur(frame, k)
        elif self.filter_type == 3:  # Bilateral
            d = self.bilateral_d if self.bilateral_d % 2 == 1 else self.bilateral_d + 1
            frame = cv2.bilateralFilter(frame, d, self.bilateral_sigmaColor, self.bilateral_sigmaSpace)

        # 4. NLM Denoising
        if self.enable_nlm:
            if self.use_gpu and self.gpu_frame is not None and self.gpu_result is not None:
                self.gpu_frame.upload(frame)
                cv2.cuda.bilateralFilter(self.gpu_frame, self.gpu_result, d=5, sigmaColor=25, sigmaSpace=25)
                processed = self.gpu_result  # left on the GPU in case CLAHE runs next too
            else:
                processed = cv2.fastNlMeansDenoising(frame, None, h=15, templateWindowSize=7, searchWindowSize=21)
        else:
            processed = frame

        # 5. CLAHE or Autocontrast
        if self.contrast_method == 1:  # CLAHE
            t0 = time.perf_counter() if self.debug_timing else None
            if self.use_gpu and self.gpu_clahe is not None and self.gpu_frame is not None and self.gpu_result is not None:
                if isinstance(processed, cv2.cuda_GpuMat):
                    # NLM's output is already resident on the GPU - chain straight into
                    # CLAHE instead of downloading to CPU and re-uploading, which would
                    # cost an extra PCIe round trip every frame. Always target the other
                    # buffer so CLAHE never reads and writes the same GpuMat.
                    src, dst = self.gpu_result, self.gpu_frame
                else:
                    self.gpu_frame.upload(processed)
                    src, dst = self.gpu_frame, self.gpu_result
                self.gpu_clahe.apply(src, dst)
                processed = dst
            elif self.clahe is not None:
                if isinstance(processed, cv2.cuda_GpuMat):
                    processed = processed.download()
                processed = self.clahe.apply(processed)
            if t0 is not None:
                print(f"[CLAHE] {'GPU' if self.use_gpu else 'CPU'} took {(time.perf_counter() - t0) * 1000:.2f}ms")
        elif self.contrast_method == 0:  # Autocontrast
            if isinstance(processed, cv2.cuda_GpuMat):
                processed = processed.download()
            low, high = np.percentile(processed, [2, 98])
            if high > low:
                processed = np.clip((processed - low) * 255.0 / (high - low), 0, 255).astype(np.uint8)

        if isinstance(processed, cv2.cuda_GpuMat):
            processed = processed.download()
        return processed

    def stop(self):
        """Signals the run() loop to exit and releases any GPU buffers."""
        self._running = False
        if self.gpu_frame is not None:
            self.gpu_frame.release()
        if self.gpu_result is not None:
            self.gpu_result.release()


# ==========================================
# TEM PROCESSOR
# ==========================================
class TEMProcessor:
    """Per-frame image processing helpers: drift correction, brightness/contrast,
    adaptive autocontrast (with caching), fast gamma LUTs, and duplicate-frame
    detection. Holds the cached state (LUTs, last hash) between frames."""

    def __init__(self):
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.gamma_lut = None
        self.gamma_value = None
        self.last_frame_hash = None
        self.duplicate_count = 0
        self.consecutive_dups = 0
        self.frame_count = 0
        self.last_drift_frame = 0
        self.autocontrast_lut = None
        self.autocontrast_built = False
        self.autocontrast_build_interval = 5
        self.autocontrast_last_build_frame = 0
        self.autocontrast_last_mean = 0.0
        self.autocontrast_mean_threshold = 15.0
        self.brightness = 0.0
        self.contrast = 1.0
        self._center_fraction = 0.8

    def apply_drift_correction(self, frame, dx, dy):
        """Corrects sample drift using an affine translation.

        Args:
            frame: Grayscale input frame.
            dx: Horizontal correction shift in pixels.
            dy: Vertical correction shift in pixels.

        Returns:
            The shifted frame, same shape as input.
        """
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    def apply_brightness_contrast(self, image, brightness=0, contrast=1.0):
        """Applies a linear brightness/contrast adjustment.

        Args:
            image: Input image array.
            brightness: Additive offset applied after the contrast scale.
            contrast: Multiplicative scale factor.

        Returns:
            The adjusted image, clipped to the valid uint8 range.
        """
        if brightness == 0 and contrast == 1.0:
            return image
        img_float = image.astype(np.float32)
        adjusted = np.clip(img_float * contrast + brightness, 0, 255).astype(np.uint8)
        return adjusted

    def adaptive_autocontrast_cached(self, image):
        """Applies percentile-based autocontrast via a cached LUT.

        The LUT is rebuilt from the image's center ROI only when the cache is
        stale (interval elapsed or mean brightness shifted significantly),
        rather than every frame, since rebuilding it involves a percentile
        computation over the frame.

        Args:
            image: Grayscale input image.

        Returns:
            The contrast-stretched image.
        """
        if self.autocontrast_lut is None:
            self.autocontrast_built = False
        
        current_mean = float(image.mean())
        frames_since_build = self.frame_count - self.autocontrast_last_build_frame
        mean_diff = abs(current_mean - self.autocontrast_last_mean)
        
        rebuild = (not self.autocontrast_built or 
                   frames_since_build >= self.autocontrast_build_interval or 
                   mean_diff >= self.autocontrast_mean_threshold)
        
        if rebuild:
            h, w = image.shape[:2]
            margin_x = int(w * (1 - self._center_fraction) / 2)
            margin_y = int(h * (1 - self._center_fraction) / 2)
            margin_x = max(0, margin_x)
            margin_y = max(0, margin_y)
            
            if margin_y < h - margin_y and margin_x < w - margin_x:
                roi = image[margin_y:h - margin_y, margin_x:w - margin_x]
            else:
                roi = image
                
            if roi.size > 0:
                low, high = np.percentile(roi, [1, 99])
            else:
                low, high = np.percentile(image, [1, 99])
                
            if high > low:
                self.autocontrast_lut = np.clip((np.arange(256, dtype=np.float32) - low) * 255.0 / (high - low), 0, 255).astype(np.uint8)
            else:
                self.autocontrast_lut = np.arange(256, dtype=np.uint8)
                
            self.autocontrast_built = True
            self.autocontrast_last_build_frame = self.frame_count
            self.autocontrast_last_mean = current_mean
        
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        
        if self.autocontrast_lut is None:
            self.autocontrast_lut = np.arange(256, dtype=np.uint8)
        
        return cv2.LUT(image, self.autocontrast_lut)

    def apply_gamma_fast(self, image, gamma=1.0):
        """Applies gamma correction via a cached LUT (rebuilt only when gamma changes).

        Args:
            image: Grayscale input image.
            gamma: Gamma exponent; 1.0 is a no-op.

        Returns:
            The gamma-corrected image.
        """
        if gamma == 1.0:
            return image.astype(np.uint8) if image.dtype != np.uint8 else image.copy()
        if self.gamma_lut is None or self.gamma_value != gamma:
            self.gamma_value = gamma
            self.gamma_lut = np.array([(i / 255.0) ** gamma * 255 for i in np.arange(0, 256)]).astype("uint8")
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return cv2.LUT(image, self.gamma_lut)

    def is_duplicate(self, frame):
        """Checks whether frame is identical to the previously seen frame.

        Compares a hash of a downscaled 128x128 version rather than the full
        frame, so the check stays cheap at full sensor resolution.

        Args:
            frame: Grayscale input frame.

        Returns:
            True if frame hashes the same as the last frame passed in.
        """
        small = cv2.resize(frame, (128, 128), interpolation=cv2.INTER_AREA)
        current_hash = xxhash.xxh64(small.tobytes()).hexdigest()
        is_dup = (self.last_frame_hash == current_hash)
        self.last_frame_hash = current_hash
        return is_dup

    def reset(self):
        """Clears cached autocontrast/duplicate-detection state (e.g. on reconnect)."""
        self.autocontrast_built = False
        self.autocontrast_lut = None
        self.autocontrast_last_build_frame = 0
        self.autocontrast_last_mean = 0.0
        self.last_frame_hash = None


# ==========================================
# VIDEO WRITERS
# ==========================================
class RawBufferWriter:
    """Buffers raw frames in RAM and encodes them to disk via ffmpeg in one batch.
    A single recording segment; DoubleBufferedWriter swaps between two of these
    so acquisition can keep writing to a fresh instance while the previous one
    encodes in the background."""

    def __init__(self, audio_device=None, record_audio=False, encoder_choice="GPU (hevc_nvenc) - Fast", encoding_mode="High Quality (CQ)", cq_value="12", bitrate_value="8M"):
        self.buffer = []
        self.frame_count = 0
        self._running = False
        self.total_frames_all_segments = 0
        self.current_buffer_bytes = 0
        self.audio_device = audio_device or "audio=Desktop Microphone (RØDE NT-USB+)"
        self.record_audio = record_audio
        self.encoder_choice = encoder_choice
        self.encoding_mode = encoding_mode
        self.cq_value = cq_value
        self.bitrate_value = bitrate_value
        self.log_callback = None
        self._logging = False
        self.paused = False
        self._log_lock = threading.Lock()

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, message):
        with self._log_lock:
            if self._logging:
                return
            self._logging = True
            try:
                print(message)
                if self.log_callback:
                    self.log_callback(message)
            finally:
                self._logging = False

    def start(self):
        """Resets the buffer and marks this writer as accepting frames.

        Returns:
            True (always succeeds).
        """
        self.buffer = []
        self.frame_count = 0
        self.current_buffer_bytes = 0
        self._running = True
        return True

    def write(self, frame):
        """Appends a frame to the in-RAM buffer, unless paused or over the RAM cap.

        Args:
            frame: Frame array to buffer (copied internally).

        Returns:
            True if the frame was buffered, False if it was rejected (not
            running, paused, or the buffer exceeded RAM_CAP_MB).
        """
        if not self._running or self.paused:
            return False

        if self.get_ram_usage_mb() > RAM_CAP_MB:
            self._log(f"WARNING: Buffer exceeded {RAM_CAP_MB}MB, forcing flush!")
            return False

        self.buffer.append(frame.copy())
        self.frame_count += 1
        self.total_frames_all_segments += 1
        self.current_buffer_bytes += frame.nbytes
        return True

    def set_pause(self, paused):
        self.paused = paused

    def get_ram_usage_mb(self):
        """Returns the current buffer's memory footprint in megabytes."""
        return self.current_buffer_bytes / (1024 * 1024)

    def flush_to_disk(self, output_path, width, height, fps=25):
        """Encodes the buffered frames to output_path via ffmpeg, in one batch.

        Picks the ffmpeg codec/settings based on encoder_choice/encoding_mode
        (GPU hevc_nvenc, CPU libx265, or lossless ffv1), optionally muxing in
        audio, and blocks until ffmpeg finishes.

        Args:
            output_path: Destination video file path.
            width: Frame width in pixels.
            height: Frame height in pixels.
            fps: Output frame rate.

        Returns:
            True if the file was written successfully, False otherwise
            (empty buffer, insufficient disk space, or an ffmpeg failure).
        """
        if not self.buffer:
            self._log("No frames to encode")
            return False

        self._log(f"\n{'='*60}")
        self._log(f"OFFLINE ENCODING: {self.frame_count} frames")
        self._log(f"{'='*60}")

        try:
            free_space = shutil.disk_usage(os.path.dirname(output_path)).free
            estimated_size = len(self.buffer) * width * height
            if free_space < estimated_size * 2:
                self._log(f"ERROR: Not enough disk space! Need {estimated_size/1e9:.1f}GB, have {free_space/1e9:.1f}GB")
                return False
        except Exception as e:
            self._log(f"Warning: Could not check disk space: {e}")

        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'gray',
            '-r', str(fps),
            '-i', '-',
        ]

        if self.record_audio and self.audio_device:
            cmd.extend([
                '-f', 'dshow', '-i', self.audio_device,
                '-shortest', '-fflags', '+genpts',
                '-map', '0:v', '-map', '1:a',
            ])
        else:
            cmd.extend(['-map', '0:v'])

        # === DYNAMIC ENCODER SETTINGS ===
        if "Lossless" in self.encoder_choice:
            # FFV1 (CPU-only, no NVENC involved) - "-g 1" makes every frame a
            # keyframe (no inter-frame prediction), matching the lossless/
            # archival intent of this mode rather than trading robustness for
            # the marginal size savings inter-frame FFV1 would give here.
            cmd.extend(['-c:v', 'ffv1', '-level', '3', '-g', '1', '-pix_fmt', 'gray16le'])
        elif "GPU" in self.encoder_choice:
            if "Long Duration" in self.encoding_mode:
                cmd.extend([
                    '-c:v', 'hevc_nvenc',
                    '-b:v', self.bitrate_value,
                    '-maxrate', self.bitrate_value,
                    '-bufsize', str(int(self.bitrate_value.replace('M', '')) * 2) + 'M',
                    '-cq', '20',
                    '-preset', 'p4',
                    '-pix_fmt', 'yuv420p',
                ])
            else:
                cmd.extend([
                    '-c:v', 'hevc_nvenc',
                    '-cq', '12',
                    '-preset', 'p4',
                    '-pix_fmt', 'yuv420p',
                ])
        else:  # CPU (libx265)
            if "Long Duration" in self.encoding_mode:
                cmd.extend([
                    '-c:v', 'libx265',
                    '-b:v', self.bitrate_value,
                    '-maxrate', self.bitrate_value,
                    '-bufsize', str(int(self.bitrate_value.replace('M', '')) * 2) + 'M',
                    '-preset', 'veryfast',
                    '-pix_fmt', 'yuv420p',
                ])
            else:
                cmd.extend([
                    '-c:v', 'libx265',
                    '-crf', '12',
                    '-preset', 'veryfast',
                    '-pix_fmt', 'yuv420p',
                ])
        
        cmd.append(output_path)

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10*1024*1024
        )

        stderr_lines = []

        def _drain_stderr():
            try:
                for line in proc.stderr:
                    stderr_lines.append(line)
            except Exception as e:
                print(f"Stderr drain error: {e}")

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        total = len(self.buffer)
        start_time = time.time()
        write_failed = False

        # Batch write for speed
        try:
            all_frames = []
            for i, frame in enumerate(self.buffer):
                if len(frame.shape) == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                all_frames.append(frame.tobytes())
                
                if (i + 1) % max(1, total // 10) == 0 or i == total - 1:
                    pct = 100 * (i + 1) / total
                    elapsed = time.time() - start_time
                    eta = elapsed * (total - i - 1) / (i + 1) if i > 0 else 0
                    self._log(f"  Preparing: {pct:.0f}% ({i+1}/{total}) | ETA: {eta:.1f}s")

            self._log(f"  Piping {total} frames to FFmpeg...")
            proc.stdin.write(b''.join(all_frames))
            proc.stdin.close()
            
        except (BrokenPipeError, IOError) as e:
            self._log(f"Write error: {e}")
            write_failed = True
        finally:
            try:
                if not proc.stdin.closed:
                    proc.stdin.close()
            except:
                pass

        if write_failed:
            proc.kill()
            stderr_thread.join(timeout=1)
            self._log("Encoding stopped due to error")
            return False

        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            self._log("WARNING: FFmpeg timed out after 120 seconds")
            proc.kill()
            stderr_thread.join(timeout=1)
            return False

        stderr_thread.join(timeout=2)

        if proc.returncode != 0:
            stderr_text = b''.join(stderr_lines).decode('utf-8', errors='ignore')[:500]
            self._log(f"FFmpeg error (code {proc.returncode}): {stderr_text}")
            return False

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            self._log("ERROR: Output file is empty or missing")
            return False

        file_size = os.path.getsize(output_path) / (1024*1024)
        self._log(f"\n  Saved: {output_path}")
        self._log(f"  Size: {file_size:.1f} MB")
        self._log(f"  Duration: {time.time() - start_time:.1f}s")
        self._log(f"{'='*60}")
        return True

    def set_audio(self, record_audio, audio_device=None):
        """Updates audio recording settings; audio_device is left unchanged if omitted."""
        self.record_audio = record_audio
        if audio_device:
            self.audio_device = audio_device

    def close(self):
        """Stops accepting frames and drops the buffer without flushing to disk."""
        self._running = False
        self.buffer = []
        self.current_buffer_bytes = 0


class DoubleBufferedWriter:
    """Wraps two RawBufferWriter instances so recording can continue into a
    fresh buffer while the previous segment encodes to disk in the background
    (auto-flushing every auto_flush_every frames, or on explicit pause/quit)."""

    def __init__(self, auto_flush_every=100, audio_device=None, record_audio=False, encoder_choice="GPU (hevc_nvenc) - Fast", encoding_mode="High Quality (CQ)", cq_value="12", bitrate_value="8M"):
        self.auto_flush_every = auto_flush_every
        self.audio_device = audio_device or "audio=Desktop Microphone (RØDE NT-USB+)"
        self.record_audio = record_audio
        self.encoder_choice = encoder_choice
        self.encoding_mode = encoding_mode
        self.cq_value = cq_value
        self.bitrate_value = bitrate_value
        self._active = RawBufferWriter(
            audio_device=self.audio_device,
            record_audio=self.record_audio,
            encoder_choice=self.encoder_choice,
            encoding_mode=self.encoding_mode,
            cq_value=self.cq_value,
            bitrate_value=self.bitrate_value
        )
        self._flushing = None
        self._lock = threading.Lock()
        self._active.start()
        self._frame_count = 0
        self._total_frames_all_segments = 0
        self._output_files = []
        self._flush_thread = None
        self.log_callback = None
        self._logging = False
        self.paused = False

    def set_log_callback(self, callback):
        self.log_callback = callback
        if self._active:
            self._active.set_log_callback(callback)

    def _log(self, message):
        if self._logging:
            return
        self._logging = True
        try:
            print(message)
            if self.log_callback:
                self.log_callback(message)
        finally:
            self._logging = False

    @property
    def frame_count(self):
        """Frame count of the currently active (not-yet-flushed) buffer."""
        with self._lock:
            return self._active.frame_count if self._active else 0

    def write(self, frame):
        """Writes a frame to the active buffer.

        Args:
            frame: Frame array to buffer.

        Returns:
            True if the frame was buffered, False if paused or rejected.
        """
        with self._lock:
            if self._active is None or self.paused:
                return False
            success = self._active.write(frame)
            if success:
                self._frame_count += 1
            return success

    def set_pause(self, paused):
        self.paused = paused
        with self._lock:
            if self._active:
                self._active.set_pause(paused)

    def should_flush(self):
        """Returns True once the active buffer has reached auto_flush_every frames."""
        with self._lock:
            if self._active is None or self.paused:
                return False
            frame_count = self._active.frame_count
            should = (self.auto_flush_every > 0 and frame_count > 0 and frame_count % self.auto_flush_every == 0)
            return should

    def pause_and_flush(self, output_path, width, height, fps=25):
        """Pauses recording and asynchronously flushes the active buffer to disk.

        Args:
            output_path: Destination path for the segment being flushed.
            width: Frame width in pixels.
            height: Frame height in pixels.
            fps: Output frame rate.

        Returns:
            True if a flush was started (there were buffered frames), False otherwise.
        """
        if self._flush_thread and self._flush_thread.is_alive():
            self._log("Waiting for background flush to complete...")
            self._flush_thread.join(timeout=60)

        self.paused = True
        with self._lock:
            if self._active:
                self._active.set_pause(True)
            has_frames = self._active is not None and self._active.frame_count > 0

        if has_frames:
            return self.swap_and_flush(output_path, width, height, fps)
        return False

    def swap_and_flush(self, output_path, width, height, fps=25):
        """Swaps in a fresh active buffer and flushes the old one to disk in the background.

        This is what lets recording continue uninterrupted: a new RawBufferWriter
        takes over as `_active` immediately, while the previous one encodes on a
        daemon thread and appends itself to `_output_files` on success.

        Args:
            output_path: Destination path for the segment being flushed.
            width: Frame width in pixels.
            height: Frame height in pixels.
            fps: Output frame rate.

        Returns:
            The filename generated for the *next* segment (not the one just flushed).
        """
        with self._lock:
            writer_to_flush = self._active
            frame_count = writer_to_flush.frame_count
            
            self._active = RawBufferWriter(
                audio_device=self.audio_device,
                record_audio=self.record_audio,
                encoder_choice=self.encoder_choice,
                encoding_mode=self.encoding_mode,
                cq_value=self.cq_value,
                bitrate_value=self.bitrate_value
            )
            self._active.set_log_callback(self.log_callback)
            self._active.start()
            
            self._flushing = writer_to_flush

        def _do_flush():
            self._log(f"\n[ASYNC FLUSH] Starting: {output_path} ({frame_count} frames)")
            t0 = time.time()
            try:
                success = writer_to_flush.flush_to_disk(output_path, width, height, fps)
                elapsed = time.time() - t0
                if success:
                    self._output_files.append(output_path)
                    self._log(f"[ASYNC FLUSH] Done: {output_path} in {elapsed:.1f}s")
                else:
                    self._log(f"[ASYNC FLUSH] FAILED: {output_path}")
            except Exception as e:
                self._log(f"[ASYNC FLUSH] ERROR: {e}")
            finally:
                with self._lock:
                    if self._flushing is writer_to_flush:
                        self._flushing = None

        self._flush_thread = threading.Thread(target=_do_flush, daemon=True)
        self._flush_thread.start()

        now = datetime.datetime.now()
        return now.strftime("%Y%m%d_%H%M%S") + "_output.mkv"

    def set_audio(self, record_audio, audio_device=None):
        """Updates audio recording settings on this writer and its active buffer."""
        self.record_audio = record_audio
        if audio_device:
            self.audio_device = audio_device
        with self._lock:
            if self._active:
                self._active.set_audio(record_audio, audio_device)

    def get_ram_usage_mb(self):
        """Returns total buffered memory in megabytes, across both the active and any in-flight flushing buffer."""
        with self._lock:
            total = 0
            if self._active:
                total += self._active.get_ram_usage_mb()
            if self._flushing:
                total += self._flushing.get_ram_usage_mb()
            return total

    def final_flush(self, output_path, width, height, fps=25):
        """Synchronously flushes the active buffer to disk (used at shutdown).

        Waits for any in-progress background flush to finish first.

        Args:
            output_path: Destination path for the final segment.
            width: Frame width in pixels.
            height: Frame height in pixels.
            fps: Output frame rate.

        Returns:
            True if the segment was written, False if there were no buffered frames.
        """
        if self._flush_thread and self._flush_thread.is_alive():
            self._log("Waiting for background flush to complete...")
            self._flush_thread.join(timeout=60)
        with self._lock:
            if self._active and self._active.frame_count > 0:
                return self._active.flush_to_disk(output_path, width, height, fps)
            return False

    def close(self):
        """Stops both the active and any in-flight buffer without flushing to disk."""
        with self._lock:
            if self._active:
                self._active.close()
            if self._flushing:
                self._flushing.close()


# ==========================================
# DRIFT TRACKERS
# ==========================================
class FrameToFrameTracker:
    """Tracks sample drift frame-to-frame via phase correlation on the four edge
    strips of the image, accumulating a running (dx, dy) correction offset."""

    def __init__(self, strip_width=40):
        self.strip_width = strip_width
        self.prev_strips = {}
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0

    def initialize(self, frame):
        """Anchors the tracker on frame, resetting accumulated drift to zero.

        Args:
            frame: Grayscale frame to use as the initial reference.

        Returns:
            True (always succeeds).
        """
        self.prev_strips = self._extract_strips(frame)
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        return True

    def _extract_strips(self, frame):
        h, w = frame.shape[:2]
        s = self.strip_width
        strips = {}
        top = frame[0:s, :]
        if top.size > 0:
            strips['top'] = self._normalize(top)
        bottom = frame[h-s:h, :]
        if bottom.size > 0:
            strips['bottom'] = self._normalize(bottom)
        left = frame[:, 0:s]
        if left.size > 0:
            strips['left'] = self._normalize(left)
        right = frame[:, w-s:w]
        if right.size > 0:
            strips['right'] = self._normalize(right)
        return strips

    def _normalize(self, img):
        f = img.astype(np.float32)
        return (f - f.mean()) / (f.std() + 1e-6)

    def compute_drift(self, frame):
        """Estimates drift since the last call by correlating edge strips against the previous frame.

        Args:
            frame: Current grayscale frame.

        Returns:
            A (cumulative_dx, cumulative_dy, reliability) tuple, where
            reliability is the fraction (0-1) of the four edge strips that
            produced a usable correlation this call.
        """
        curr_strips = self._extract_strips(frame)
        shifts = []
        for name, prev_strip in self.prev_strips.items():
            if name not in curr_strips or curr_strips[name] is None:
                continue
            if prev_strip.shape != curr_strips[name].shape:
                continue
            try: 
                (dx, dy), conf = cv2.phaseCorrelate(prev_strip, curr_strips[name])
            except cv2.error as e:
                print(f"Phase correlate error: {e}")
                continue
            if conf < 0.001:
                continue            
            if abs(dx) > 20 or abs(dy) > 20:
                continue
            shifts.append((dx, dy, conf))
        reliability = len(shifts) / 4.0
        self.prev_strips = curr_strips
        if len(shifts) < 2:
            return self.cumulative_dx, self.cumulative_dy, reliability
        if len(shifts) >= 3:
            median_dx = float(np.median([s[0] for s in shifts]))
            median_dy = float(np.median([s[1] for s in shifts]))
            deviations = [(s[0]-median_dx)**2 + (s[1]-median_dy)**2 for s in shifts]
            best_indices = np.argsort(deviations)[:2]
            best_shifts = [shifts[i] for i in best_indices]
            frame_dx = float(np.mean([s[0] for s in best_shifts]))
            frame_dy = float(np.mean([s[1] for s in best_shifts]))
        else:
            frame_dx = float(np.mean([s[0] for s in shifts]))
            frame_dy = float(np.mean([s[1] for s in shifts]))
        self.cumulative_dx += frame_dx
        self.cumulative_dy += frame_dy
        return self.cumulative_dx, self.cumulative_dy, reliability

    def draw_overlay(self, image, color=(0, 255, 0)):
        """Draws rectangles marking the four tracked edge strips, for visual debugging.

        Args:
            image: Image to draw on (grayscale or BGR); not modified in place.
            color: BGR rectangle color.

        Returns:
            A BGR copy of image with the strip outlines drawn.
        """
        if len(image.shape) == 2:
            vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis = image.copy()
        h, w = vis.shape[:2]
        s = self.strip_width
        cv2.rectangle(vis, (0, 0), (w, s), color, 2)
        cv2.rectangle(vis, (0, h-s), (w, h), color, 2)
        cv2.rectangle(vis, (0, 0), (s, h), color, 2)
        cv2.rectangle(vis, (w-s, 0), (w, h), color, 2)
        return vis

    def reset(self):
        """Clears the reference strips and accumulated drift."""
        self.prev_strips = {}
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0


class ROITracker:
    """Tracks a user-selected region of interest via template matching, so
    drift correction can lock onto a specific feature rather than the whole
    frame's edges (works even with a vignetted/circular field of view)."""

    def __init__(self, min_size=32, max_size=512):
        self.min_size = min_size
        self.max_size = max_size
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.roi_locked = False
        self.template = None
        self.template_pos = None
        self.template_center = None
        self.frame_center = None
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        self.last_dx = 0.0
        self.last_dy = 0.0
        self.search_margin = 80
        self.confidence_threshold = 0.15
        self.damping = 0.6

    def start_selection(self):
        """Enters ROI-selection mode, clearing any previously locked template.

        Returns:
            True (always succeeds).
        """
        self.selecting = True
        self.selection_start = None
        self.selection_end = None
        self.roi_locked = False
        self.template = None
        self.template_pos = None
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        self.last_dx = 0.0
        self.last_dy = 0.0
        return True

    def on_mouse_down(self, x, y):
        """Starts a selection drag at (x, y), in display coordinates.

        Returns:
            True if a selection was started, False if not in selecting mode.
        """
        if not self.selecting:
            return False
        self.selection_start = (x, y)
        self.selection_end = (x, y)
        return True

    def on_mouse_move(self, x, y):
        """Updates the in-progress selection's end point to (x, y).

        Returns:
            True if the selection was updated, False if no drag is in progress.
        """
        if not self.selecting or self.selection_start is None:
            return False
        self.selection_end = (x, y)
        return True

    def on_mouse_up(self, frame, display_scale_x, display_scale_y):
        """Finalizes the drag as the tracked ROI template, if it's a valid size.

        Args:
            frame: Full-resolution frame to crop the template from.
            display_scale_x: Ratio of frame width to displayed width.
            display_scale_y: Ratio of frame height to displayed height.

        Returns:
            True if the ROI was locked, False if the selection was too small,
            too large, or no drag was in progress.
        """
        if not self.selecting or self.selection_start is None:
            return False

        x1_disp = min(self.selection_start[0], self.selection_end[0])
        y1_disp = min(self.selection_start[1], self.selection_end[1])
        x2_disp = max(self.selection_start[0], self.selection_end[0])
        y2_disp = max(self.selection_start[1], self.selection_end[1])

        x1 = int(x1_disp * display_scale_x)
        y1 = int(y1_disp * display_scale_y)
        x2 = int(x2_disp * display_scale_x)
        y2 = int(y2_disp * display_scale_y)

        w = x2 - x1
        h = y2 - y1

        if w < self.min_size or h < self.min_size:
            self.selecting = False
            self.selection_start = None
            self.selection_end = None
            return False

        if w > self.max_size or h > self.max_size:
            self.selecting = False
            self.selection_start = None
            self.selection_end = None
            return False

        h_frame, w_frame = frame.shape[:2]
        x1 = max(0, min(x1, w_frame - w))
        y1 = max(0, min(y1, h_frame - h))
        x2 = min(w_frame, x1 + w)
        y2 = min(h_frame, y1 + h)
        w = x2 - x1
        h = y2 - y1

        if w < self.min_size or h < self.min_size:
            self.selecting = False
            self.selection_start = None
            self.selection_end = None
            return False

        if frame.dtype != np.uint8:
            self.template = np.clip(frame[y1:y2, x1:x2], 0, 255).astype(np.uint8)
        else:
            self.template = frame[y1:y2, x1:x2].copy()

        self.template_pos = (x1, y1, w, h)
        self.template_center = (x1 + w / 2.0, y1 + h / 2.0)
        self.frame_center = (w_frame / 2.0, h_frame / 2.0)

        self.selecting = False
        self.roi_locked = True
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        return True

    def compute_offset(self, frame):
        """Locates the locked template in frame and returns a damped correction shift.

        Args:
            frame: Current full-resolution frame to search.

        Returns:
            A (dx, dy, confidence) tuple. dx/dy are already the *correction*
            shift (i.e. the negated object displacement) - callers should not
            negate them again before applying, only once more if their own
            apply-correction convention expects a raw displacement (see the
            call site's sign-convention comment). confidence is the template
            match score in [0, 1]; below confidence_threshold, the last known
            (dx, dy) is returned unchanged.
        """
        if not self.roi_locked or self.template is None:
            return 0.0, 0.0, 0.0
        h_frame, w_frame = frame.shape[:2]
        tx, ty, tw, th = self.template_pos

        sx1 = max(0, tx - self.search_margin)
        sy1 = max(0, ty - self.search_margin)
        sx2 = min(w_frame, tx + tw + self.search_margin)
        sy2 = min(h_frame, ty + th + self.search_margin)

        sw = sx2 - sx1
        sh = sy2 - sy1

        if sw < tw or sh < th:
            return self.last_dx, self.last_dy, 0.0

        if frame.dtype != np.uint8:
            frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        else:
            frame_u8 = frame

        search_region = frame_u8[sy1:sy2, sx1:sx2]

        try:
            result = cv2.matchTemplate(search_region, self.template, cv2.TM_CCOEFF_NORMED)
        except cv2.error as e:
            print(f"Match template error: {e}")
            return self.last_dx, self.last_dy, 0.0

        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < self.confidence_threshold:
            return self.last_dx, self.last_dy, max_val

        match_x = sx1 + max_loc[0]
        match_y = sy1 + max_loc[1]

        current_cx = match_x + tw / 2.0
        current_cy = match_y + th / 2.0

        object_dx = current_cx - self.template_center[0]
        object_dy = current_cy - self.template_center[1]

        target_shift_x = -object_dx
        target_shift_y = -object_dy

        self.cumulative_dx = self.cumulative_dx * (1 - self.damping) + target_shift_x * self.damping
        self.cumulative_dy = self.cumulative_dy * (1 - self.damping) + target_shift_y * self.damping

        max_shift = min(w_frame, h_frame) / 3.0
        self.cumulative_dx = max(-max_shift, min(max_shift, self.cumulative_dx))
        self.cumulative_dy = max(-max_shift, min(max_shift, self.cumulative_dy))

        self.last_dx = self.cumulative_dx
        self.last_dy = self.cumulative_dy

        return self.cumulative_dx, self.cumulative_dy, max_val

    def reset(self):
        """Clears the tracked ROI and any in-progress selection."""
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        self.roi_locked = False
        self.template = None
        self.template_pos = None
        self.template_center = None
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        self.last_dx = 0.0
        self.last_dy = 0.0

    def get_selection_rect(self):
        """Returns the in-progress selection as (x, y, width, height) in display
        coordinates, or None if no selection is active."""
        if not self.selecting or self.selection_start is None:
            return None
        x1 = min(self.selection_start[0], self.selection_end[0])
        y1 = min(self.selection_start[1], self.selection_end[1])
        x2 = max(self.selection_start[0], self.selection_end[0])
        y2 = max(self.selection_start[1], self.selection_end[1])
        return (x1, y1, x2 - x1, y2 - y1)


# ==========================================
# HISTOGRAM WINDOW
# ==========================================
class HistogramWindow(QMainWindow):
    """Secondary window showing the live camera image alongside its intensity
    histogram, CDF, image statistics, and an optional equalized preview."""

    def __init__(self, camera_source):
        super().__init__()
        self.camera_source = camera_source
        self.setWindowTitle("Histogram Mode")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(build_theme_stylesheet(camera_source._theme))
        self._running = True
        self._last_image = None
        self.hist_bins = 256
        self.show_cdf = False
        self.show_equalized = False
        self.histogram_type = "Full"
        self.region_fraction = 0.3
        self._build_layout()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(50)

    def _build_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        image_group = QGroupBox("Image with Histogram Overlay")
        image_layout = QVBoxLayout(image_group)
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(500, 500)
        image_layout.addWidget(self.image_label)
        main_layout.addWidget(image_group, 2)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(5)

        controls_group = QGroupBox("Histogram Controls")
        controls_layout = QVBoxLayout(controls_group)

        controls_layout.addWidget(QLabel("Histogram Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Full Image", "Region", "Center"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        controls_layout.addWidget(self.type_combo)

        controls_layout.addWidget(QLabel("Region Size (% of image):"))
        self.region_slider = QSlider(Qt.Horizontal)
        self.region_slider.setRange(5, 80)
        self.region_slider.setValue(30)
        self.region_slider.valueChanged.connect(self._on_region_changed)
        controls_layout.addWidget(self.region_slider)
        self.region_label = QLabel("30%")
        self.region_slider.valueChanged.connect(lambda v: self.region_label.setText(f"{v}%"))
        controls_layout.addWidget(self.region_label)

        controls_layout.addWidget(QLabel("Number of Bins:"))
        self.bins_slider = QSlider(Qt.Horizontal)
        self.bins_slider.setRange(32, 512)
        self.bins_slider.setValue(256)
        self.bins_slider.valueChanged.connect(lambda v: setattr(self, 'hist_bins', v))
        controls_layout.addWidget(self.bins_slider)
        self.bins_label = QLabel("256")
        self.bins_slider.valueChanged.connect(self.bins_label.setText)
        controls_layout.addWidget(self.bins_label)

        self.show_cdf_cb = QCheckBox("Show Cumulative Distribution (CDF)")
        self.show_cdf_cb.toggled.connect(lambda v: setattr(self, 'show_cdf', v))
        controls_layout.addWidget(self.show_cdf_cb)

        self.show_equalized_cb = QCheckBox("Show Histogram Equalized Image")
        self.show_equalized_cb.toggled.connect(lambda v: setattr(self, 'show_equalized', v))
        controls_layout.addWidget(self.show_equalized_cb)

        scroll_layout.addWidget(controls_group)

        stats_group = QGroupBox("Image Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Mean: --\nStd Dev: --\nMin: --\nMax: --\nMedian: --")
        stats_layout.addWidget(self.stats_label)
        scroll_layout.addWidget(stats_group)

        plt.style.use('dark_background')
        self.figure = Figure(figsize=(4, 3), dpi=100, facecolor='#1e1e1e')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Pixel Intensity", color='#d4d4d4')
        self.ax.set_ylabel("Frequency", color='#d4d4d4')
        self.ax.grid(True, alpha=0.3, color='#3a3a3a')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='#d4d4d4')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(250)
        scroll_layout.addWidget(self.canvas)

        self.figure2 = Figure(figsize=(4, 2), dpi=100, facecolor='#1e1e1e')
        self.ax2 = self.figure2.add_subplot(111)
        self.ax2.set_xlabel("Pixel Intensity", color='#d4d4d4')
        self.ax2.set_ylabel("Cumulative Probability", color='#d4d4d4')
        self.ax2.grid(True, alpha=0.3, color='#3a3a3a')
        self.ax2.set_facecolor('#1e1e1e')
        self.ax2.tick_params(colors='#d4d4d4')
        self.canvas2 = FigureCanvas(self.figure2)
        self.canvas2.setMinimumHeight(150)
        scroll_layout.addWidget(self.canvas2)

        eq_group = QGroupBox("Equalized Image Preview")
        eq_layout = QVBoxLayout(eq_group)
        self.eq_label = QLabel()
        self.eq_label.setObjectName("image_label")
        self.eq_label.setAlignment(Qt.AlignCenter)
        self.eq_label.setMinimumHeight(100)
        eq_layout.addWidget(self.eq_label)
        scroll_layout.addWidget(eq_group)

        export_btn = QPushButton("Export Histogram Data")
        export_btn.clicked.connect(self._export_histogram)
        scroll_layout.addWidget(export_btn)

        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        main_layout.addWidget(right_panel, 1)

    def _on_type_changed(self, text):
        self.histogram_type = text.replace(" ", "")
        self.region_slider.setEnabled(text != "Full Image")

    def _on_region_changed(self, value):
        self.region_fraction = value / 100.0

    def _update(self):
        if not self._running:
            return
        image = self.camera_source.get_current_image()
        if image is None:
            return
        self._last_image = image
        if self.histogram_type == "Full":
            roi = image
        elif self.histogram_type == "Region":
            h, w = image.shape[:2]
            margin_x = int(w * (1 - self.region_fraction) / 2)
            margin_y = int(h * (1 - self.region_fraction) / 2)
            roi = image[margin_y:h - margin_y, margin_x:w - margin_x]
        else:
            h, w = image.shape[:2]
            crop_size = int(min(h, w) * self.region_fraction)
            margin_x = (w - crop_size) // 2
            margin_y = (h - crop_size) // 2
            roi = image[margin_y:margin_y + crop_size, margin_x:margin_x + crop_size]

        hist = cv2.calcHist([roi], [0], None, [self.hist_bins], [0, 256])
        hist = hist / hist.sum()
        cdf = hist.cumsum()

        display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        self._draw_roi_overlay(display)
        self._render_image(display)

        self._update_histogram_plot(hist)
        self._update_cdf_plot(cdf)
        self._update_stats(roi)

        if self.show_equalized:
            self._update_equalized(roi)

    def _draw_roi_overlay(self, display):
        h, w = display.shape[:2]
        if self.histogram_type == "Full":
            cv2.rectangle(display, (0, 0), (w, h), (0, 255, 0), 2)
            return
        if self.histogram_type == "Region":
            margin_x = int(w * (1 - self.region_fraction) / 2)
            margin_y = int(h * (1 - self.region_fraction) / 2)
            cv2.rectangle(display, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 255, 255), 2)
        else:
            crop_size = int(min(h, w) * self.region_fraction)
            margin_x = (w - crop_size) // 2
            margin_y = (h - crop_size) // 2
            cv2.rectangle(display, (margin_x, margin_y), (margin_x + crop_size, margin_y + crop_size), (0, 255, 255), 2)

    def _update_histogram_plot(self, hist):
        self.ax.clear()
        bin_edges = np.linspace(0, 256, self.hist_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        self.ax.bar(bin_centers, hist, width=256/self.hist_bins, color='#4a9eff', alpha=0.7, edgecolor='#4a9eff', linewidth=0.5)
        if self._last_image is not None:
            mean_val = self._last_image.mean()
            self.ax.axvline(mean_val, color='#ff6b6b', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
            self.ax.legend()
        self.ax.set_xlabel("Pixel Intensity", color='#d4d4d4')
        self.ax.set_ylabel("Probability", color='#d4d4d4')
        self.ax.grid(True, alpha=0.3, color='#3a3a3a')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='#d4d4d4')
        self.ax.set_title("Intensity Distribution", color='#d4d4d4')
        self.canvas.draw()

    def _update_cdf_plot(self, cdf):
        if not self.show_cdf:
            self.figure2.clear()
            self.ax2 = self.figure2.add_subplot(111)
            self.ax2.set_xlabel("Pixel Intensity", color='#d4d4d4')
            self.ax2.set_ylabel("Cumulative Probability", color='#d4d4d4')
            self.ax2.grid(True, alpha=0.3, color='#3a3a3a')
            self.ax2.set_facecolor('#1e1e1e')
            self.ax2.tick_params(colors='#d4d4d4')
            self.canvas2.draw()
            return
        self.ax2.clear()
        bin_edges = np.linspace(0, 256, self.hist_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        self.ax2.plot(bin_centers, cdf, 'g-', linewidth=2, color='#00ff88')
        self.ax2.fill_between(bin_centers, 0, cdf, alpha=0.3, color='#00ff88')
        self.ax2.set_xlabel("Pixel Intensity", color='#d4d4d4')
        self.ax2.set_ylabel("Cumulative Probability", color='#d4d4d4')
        self.ax2.grid(True, alpha=0.3, color='#3a3a3a')
        self.ax2.set_facecolor('#1e1e1e')
        self.ax2.tick_params(colors='#d4d4d4')
        self.ax2.set_title("Cumulative Distribution", color='#d4d4d4')
        self.ax2.set_ylim(0, 1.05)
        self.canvas2.draw()

    def _update_stats(self, roi):
        mean = roi.mean()
        std = roi.std()
        min_val = roi.min()
        max_val = roi.max()
        median = np.median(roi)
        self.stats_label.setText(f"Mean: {mean:.2f}\nStd Dev: {std:.2f}\nMin: {min_val}\nMax: {max_val}\nMedian: {median:.2f}")

    def _update_equalized(self, roi):
        if roi.size == 0:
            return
        eq = cv2.equalizeHist(roi)
        h, w = eq.shape[:2]
        display_h = self.eq_label.height()
        if display_h > 10:
            scale = display_h / h
            new_w = int(w * scale)
            if new_w > 0:
                eq_resized = cv2.resize(eq, (new_w, display_h))
                self._render_image_to_label(eq_resized, self.eq_label)

    def _render_image(self, bgr_image):
        label_size = self.image_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return
        h, w = bgr_image.shape[:2]
        if w > 0 and h > 0:
            scale = min(label_size.width() / w, label_size.height() / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(bgr_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                self._render_image_to_label(resized, self.image_label)

    def _render_image_to_label(self, image, label):
        if len(image.shape) == 2:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb = image
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap)

    def _export_histogram(self):
        if self._last_image is None:
            return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"histogram_data_{timestamp}.txt"
        if self.histogram_type == "Full":
            roi = self._last_image
        elif self.histogram_type == "Region":
            h, w = self._last_image.shape[:2]
            margin_x = int(w * (1 - self.region_fraction) / 2)
            margin_y = int(h * (1 - self.region_fraction) / 2)
            roi = self._last_image[margin_y:h - margin_y, margin_x:w - margin_x]
        else:
            h, w = self._last_image.shape[:2]
            crop_size = int(min(h, w) * self.region_fraction)
            margin_x = (w - crop_size) // 2
            margin_y = (h - crop_size) // 2
            roi = self._last_image[margin_y:margin_y + crop_size, margin_x:margin_x + crop_size]
        hist = cv2.calcHist([roi], [0], None, [self.hist_bins], [0, 256])
        with open(filename, 'w') as f:
            f.write("# Histogram data\n")
            f.write(f"# Timestamp: {timestamp}\n")
            f.write(f"# Type: {self.histogram_type}\n")
            f.write(f"# Bins: {self.hist_bins}\n")
            f.write(f"# Region fraction: {self.region_fraction:.2f}\n")
            f.write("# Intensity\tFrequency\n")
            bin_edges = np.linspace(0, 256, self.hist_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            for i, (center, freq) in enumerate(zip(bin_centers, hist.flatten())):
                f.write(f"{center:.2f}\t{freq:.0f}\n")

    def closeEvent(self, event):
        """Stops the refresh timer so the window doesn't keep polling after it's closed."""
        self._running = False
        self.timer.stop()
        event.accept()


# ==========================================
# OUTPUT LOG WINDOW
# ==========================================
class OutputLogWindow(QMainWindow):
    """Floating, always-on-top scrollback window mirroring the app's log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Output Log")
        self.setGeometry(200, 200, 800, 500)
        self.setStyleSheet(build_theme_stylesheet(parent._theme if parent is not None else 'dark'))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Output Log"))
        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_btn)

        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        header_layout.addWidget(self.auto_scroll_cb)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide_window)
        header_layout.addWidget(close_btn)

        layout.addLayout(header_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        self.setMinimumSize(600, 300)
        self._updating = False

    def append_log(self, message):
        """Appends a timestamped message to the log view and updates the line-count status.

        Args:
            message: Text to append (a "[HH:MM:SS]" prefix is added automatically).
        """
        if self._updating:
            return
        self._updating = True
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted = f"[{timestamp}] {message}"
            self.log_text.append(formatted)
            if self.auto_scroll_cb.isChecked():
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            self.status_label.setText(f"Lines: {self.log_text.document().lineCount()}")
        finally:
            self._updating = False

    def clear_log(self):
        """Clears all log text."""
        self.log_text.clear()
        self.status_label.setText("Log cleared")

    def hide_window(self):
        """Hides the window and clears the main app's log_window_visible flag."""
        self.hide()
        if self.parent:
            self.parent.log_window_visible = False


# ==========================================
# MAIN APP
# ==========================================
class TEMViewerApp(QMainWindow):
    """Main window: live Ximea camera view, acquisition/processing/recording
    pipeline wiring, drift correction, and all toolbar controls."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEM Live Viewer")
        self.setGeometry(50, 50, 1400, 800)
        self._theme = 'dark'
        self._camera_status_kind = 'disconnected'

        # Camera state
        self.cam = None
        self.img = None
        self.width = 1024
        self.height = 1024
        self.fps = 25
        self.camera_connected = False
        self._camera_lock = threading.Lock()
        self._current_image = None
        self._last_frame_time = time.time()
        self._fps_counter = 0
        self._fps_timer = time.time()

        # Video output path
        self.video_output_path = os.getcwd()
        self.output_file = None
        self._update_output_filename()

        # Audio settings
        self.audio_device = "audio=Desktop Microphone (RØDE NT-USB+)"
        self.record_audio = True

        # Log window
        self.log_window = None
        self.log_window_visible = False

        # Writer
        self.writer = None
        self._writer_started = False
        self.output_files = []

        # Flat field reference frames
        self.D = None
        self.G = None
        self._load_flat_field()

        # Processing objects
        self.processor = TEMProcessor()
        self.roi_tracker = ROITracker(min_size=32, max_size=512)
        self.drift_tracker = FrameToFrameTracker(strip_width=40)
        self.drift_log = []
        self.tracker_initialized = False
        self.paused = False
        self._running = True
        self.enable_screenshot = False
        self.drift_interval = 1
        self._prev_drift_choice = 0
        self.toolbar_visible = True
        self._last_display_size = None

        # Counters
        self.frames_read = 0
        self.frames_queued = 0
        self.frames_dropped = 0
        self.frames_duplicate = 0
        self.frame_times = []
        self.actual_fps = 0.0
        self.csv_file = None
        self.csv_filename = None

        # Filter parameters
        self.gaussian_kernel = 3
        self.gaussian_sigma = 1.0
        self.median_kernel = 3
        self.bilateral_d = 9
        self.bilateral_sigmaColor = 75
        self.bilateral_sigmaSpace = 75

        # Brightness and contrast
        self.brightness = 0.0
        self.contrast = 1.0
        # CHANGED: Gamma default is now 1.00
        self.gamma = 1.00 
        self.exposure = 40.0
        self.histogram_window = None
        self.concat_on_quit = True
        self.current_binning = "1x1"
        self.microscope_mode = "Image Mode"

        # Encoding settings
        self.encoder_choice = "GPU (hevc_nvenc) - Fast"
        self.encoding_mode = "High Quality (CQ)"
        self.cq_value = "12"
        self.bitrate_value = "8M"
        self.manual_gain = 6.0

        # UI Update flag to prevent unwanted parameter triggering
        self._updating_param_ui = False

        # Worker Queues
        self.raw_queue = queue.Queue(maxsize=5)
        self.display_queue = queue.Queue(maxsize=2)
        self.processing_worker = ImageProcessingWorker(self.raw_queue, self.display_queue)
        self.processing_worker.start()
        self._log_message(
            f"GPU acceleration (CLAHE/NLM): {'ENABLED' if self.processing_worker.use_gpu else 'DISABLED - using CPU'}"
        )

        self._build_layout()
        self._apply_theme('dark')
        self._acq_thread = None
        self._acq_running = False
        self._start_acquisition_thread()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(16)

    def _update_output_filename(self):
        now = datetime.datetime.now()
        self.output_file = os.path.join(self.video_output_path, now.strftime("%Y%m%d_%H%M%S") + "_output.mkv")

    def _apply_theme(self, theme):
        """Switch between the dark and light QSS themes and refresh the handful
        of widgets that set their own inline stylesheet, which the global QSS
        below can't reach (camera status text), plus any open child windows."""
        self._theme = theme
        self.setStyleSheet(build_theme_stylesheet(theme))

        for gb in self.findChildren(QGroupBox):
            gb.style().unpolish(gb)
            gb.style().polish(gb)

        self._refresh_camera_status()

        if self.histogram_window is not None:
            self.histogram_window.setStyleSheet(build_theme_stylesheet(theme))
        if self.log_window is not None:
            self.log_window.setStyleSheet(build_theme_stylesheet(theme))

    def _set_camera_status(self, text, kind):
        """kind is 'connected', 'disconnected', or 'failed' - drives the status label's color."""
        self._camera_status_kind = kind
        self.camera_status_label.setText(text)
        self._refresh_camera_status()

    def _refresh_camera_status(self):
        color = THEME_COLORS[self._theme]['success'] if self._camera_status_kind == 'connected' else THEME_COLORS[self._theme]['error']
        self.camera_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _choose_output_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.video_output_path)
        if directory:
            self.video_output_path = directory
            self._update_output_filename()
            self.path_label.setText(f" {directory}")
            self._log_message(f"Output directory set to: {directory}")

    def get_current_image(self):
        return self._current_image

    def _log_message(self, message):
        print(message)
        if hasattr(self, 'log_window') and self.log_window and self.log_window_visible:
            self.log_window.append_log(message)

    def _toggle_log_window(self):
        if self.log_window is None:
            self.log_window = OutputLogWindow(self)
            self.log_window.destroyed.connect(self._on_log_window_destroyed)
        if self.log_window_visible:
            self.log_window.hide()
            self.log_window_visible = False
        else:
            self.log_window.show()
            self.log_window.raise_()
            self.log_window_visible = True

    def _on_log_window_destroyed(self):
        self.log_window_visible = False
        self.log_window = None

    def _load_flat_field(self):
        try:
            self._log_message("Loading flat-field correction...")
            self.D = cv2.imread('C:/Users/admin-monchoux/Desktop/nail_TEM/micro2/Noir_25fps.png', cv2.IMREAD_ANYDEPTH).astype(np.float32)
            F = cv2.imread('C:/Users/admin-monchoux/Desktop/nail_TEM/micro2/tialwc_bb837_2_800_7_e4_j388_rad_24_80000x.tif', cv2.IMREAD_ANYDEPTH).astype(np.float32)
            if F.max() > 255:
                F = F * 255.0 / F.max()
            FD = F - self.D
            mean_FD = np.mean(FD)
            self.G = np.clip(np.where(FD > 0, mean_FD / (FD + 1e-6), 1.0).astype(np.float32), 0.8, 1.2)
            self._log_message("Flat-field correction loaded successfully")
        except Exception as e:
            self._log_message(f"WARNING: Could not load flat-field correction: {e}")
            self.D = None
            self.G = None

    def _try_connect_camera(self):
        with self._camera_lock:
            if self.camera_connected:
                return True
            try:
                self._log_message("Attempting to connect to Ximea camera...")

                if self.writer is not None:
                    self._log_message("Finalizing previous recording segment (async) before reconnect...")
                    self.writer.pause_and_flush(self.output_file, self.width, self.height, fps=self.fps)
                    self.writer = None

                cam = xiapi.Camera()
                cam.open_device()
                cam.set_acq_timing_mode('XI_ACQ_TIMING_MODE_FREE_RUN')
                cam.set_sensor_taps('XI_TAP_CNT_4')
                cam.set_downsampling_type('XI_BINNING')
                cam.set_downsampling('XI_DWN_1x1')
                cam.disable_aeag()
                cam.set_gain(self.manual_gain)
                cam.set_exposure(int(self.exposure * 1000))
                actual_ms = float(cam.get_exposure()) / 1000.0
                self.fps = int(1000 / self.exposure) if self.exposure > 0 else 25
                self.img = xiapi.Image()
                cam.start_acquisition()
                self.width = int(cam.get_width())
                self.height = int(cam.get_height())
                self.cam = cam
                self.camera_connected = True
                self.processor.reset()
                self._log_message(f"Camera connected! Resolution: {self.width}x{self.height} | Gain: {self.manual_gain} dB")
                self._log_message(f"Exposure requested {self.exposure:.1f}ms, camera reports {actual_ms:.1f}ms")
                self._log_message("Display live. Press Record to start saving to disk.")
                return True
            except Exception as e:
                self._log_message(f"Camera connection failed: {e}")
                self.cam = None
                self.img = None
                self.camera_connected = False
                return False

    def _disconnect_camera(self):
        with self._camera_lock:
            if self.cam is not None:
                try:
                    self._log_message("Disconnecting camera...")
                    try:
                        self.cam.stop_acquisition()
                    except Exception as e:
                        self._log_message(f"Error stopping acquisition: {e}")
                    try:
                        self.cam.close_device()
                    except Exception as e:
                        self._log_message(f"Error closing device: {e}")
                except Exception as e:
                    self._log_message(f"Error during camera disconnect: {e}")
                finally:
                    self.cam = None
                    self.img = None
                    self.camera_connected = False
                    self._log_message("Camera disconnected")

    def _init_writer(self):
        if RECORD_MODE == "raw":
            self.writer = DoubleBufferedWriter(
                auto_flush_every=AUTO_FLUSH_EVERY,
                audio_device=self.audio_device,
                record_audio=self.record_audio,
                encoder_choice=self.encoder_choice,
                encoding_mode=self.encoding_mode,
                cq_value=self.cq_value,
                bitrate_value=self.bitrate_value
            )
            self.writer.set_log_callback(self._log_message)
            self._writer_started = True
        self._log_message(f"Recording STARTED [{RECORD_MODE}]: {self.output_file}")

    def _apply_exposure(self):
        """Apply the exposure field to the camera. AEAG drives exposure itself, so a
        manual set_exposure() while it's active is unreliable - it may be ignored or
        silently overwritten on AEAG's next update cycle - which is why exposure changes
        "sometimes don't apply". AEAG is therefore auto-disabled first when active."""
        if not self.camera_connected or self.cam is None:
            return
        try:
            self.exposure = max(0.1, min(1000, self.exposure))

            if self.cam.is_aeag():
                self._log_message("AEAG is active - disabling it to allow manual exposure control")
                self._disable_aeag()
                self._apply_manual_gain()

            self.cam.set_exposure(int(self.exposure * 1000))
            actual_ms = float(self.cam.get_exposure()) / 1000.0
            self.fps = int(1000 / self.exposure) if self.exposure > 0 else 25
            self._log_message(
                f"Exposure requested {self.exposure:.1f}ms, camera reports {actual_ms:.1f}ms ({self.fps}fps)"
            )
        except Exception as e:
            self._log_message(f"Error setting exposure: {e}")

    def _on_binning_changed(self, text):
        if not self.camera_connected:
            return
        self.current_binning = text
        self._log_message(f"Changing binning to {text}...")
        was_recording = self.writer is not None
        try:
            # 1. Force pause to stop recording and flush the buffer safely
            if self.writer is not None and not self.paused:
                self._log_message("Auto-pausing and flushing current segment before binning change...")
                self._on_pause_toggle()  # Triggers background flush and prevents new frames

            # 2. Wait for the background encoding to completely finish
            # Prevents crashes from trying to overwrite RAM while FFmpeg is reading it
            if self.writer and self.writer._flush_thread and self.writer._flush_thread.is_alive():
                self._log_message("Waiting for encoding to finish...")
                self.writer._flush_thread.join(timeout=120)
                self._log_message("Encoding finished successfully.")

            # 3. Stop camera, change binning
            self.cam.stop_acquisition()
            if text == "2x2":
                self.cam.set_downsampling('XI_DWN_2x2')
            else:
                self.cam.set_downsampling('XI_DWN_1x1')

            # 4. Restart camera and update resolution
            self.cam.start_acquisition()
            self.width = int(self.cam.get_width())
            self.height = int(self.cam.get_height())
            self._log_message(f"Binning changed to {text}. New resolution: {self.width}x{self.height}")

            # 5. If a recording was in progress, prepare a fresh writer at the new
            # resolution - otherwise leave recording off, matching the pre-change state.
            if was_recording:
                self._update_output_filename()
                self._init_writer()
                self._log_message("Binning change complete. Click 'Resume' when ready to start recording.")
            else:
                self._log_message("Binning change complete.")

        except Exception as e:
            self._log_message(f"Error changing binning: {e}")
            self._disconnect_camera()

    def _on_gain_toggle(self):
        if not self.camera_connected or self.cam is None:
            return
        if self.gain_btn.isChecked():
            try:
                # FIX: Limit AEAG's exposure to your current manual exposure (e.g., 40ms)
                # This prevents AEAG from using 100ms+ and dropping FPS to 10.
                self.cam.set_param('ae_max_limit', int(self.exposure * 1000))
                self.cam.set_param('ag_max_limit', 40.0)

                # FIX: Switch to Frame Rate Limit mode to lock it at 25 FPS
                self.cam.set_param('acq_timing_mode', 'XI_ACQ_TIMING_MODE_FRAME_RATE_LIMIT')
                self.cam.set_param('framerate', 25.0)

                # Enable AEAG
                self.cam.enable_aeag()
                self.gain_btn.setText("Auto Exposure/Gain (AEAG): ON")
                self.gain_input.setEnabled(False)
                self.apply_gain_btn.setEnabled(False)
                self._log_message("Camera AEAG (Auto Exposure/Gain) ENABLED: Capped at 25 FPS")
            except Exception as e:
                self._log_message(f"Error enabling AEAG: {e}")
        else:
            try:
                self._disable_aeag()
                self._apply_manual_gain()
            except Exception as e:
                self._log_message(f"Error disabling AEAG: {e}")

    def _disable_aeag(self):
        """Turn off AEAG and restore Free Run timing/manual-gain UI state. Does not touch exposure or gain values themselves."""
        if not self.camera_connected or self.cam is None:
            return
        self.cam.set_param('acq_timing_mode', 'XI_ACQ_TIMING_MODE_FREE_RUN')
        self.cam.disable_aeag()
        self.gain_btn.setChecked(False)
        self.gain_btn.setText("Auto Exposure/Gain (AEAG): OFF")
        self.gain_input.setEnabled(True)
        self.apply_gain_btn.setEnabled(True)
        self._log_message("Camera AEAG (Auto Exposure/Gain) DISABLED (Fixed FPS)")

    def _apply_manual_gain(self):
        if not self.camera_connected or self.cam is None:
            return
        try:
            val = float(self.gain_input.text())
            val = max(0.0, min(40.0, val))
            self.manual_gain = val
            self.cam.set_gain(val)
            self._log_message(f"Manual gain set to {val:.1f} dB")
        except ValueError:
            self._log_message("Error: Please enter a valid number for gain")
        except Exception as e:
            self._log_message(f"Error applying gain: {e}")

    def _on_microscope_mode_changed(self, text):
        self.microscope_mode = text
        self.processor.reset()
        if text == "Diffraction Mode":
            self.processing_worker.contrast_method = 2
            self.processing_worker.enable_flatfield = False
            self.processing_worker.enable_nlm = False
            self.contrast_method_group.button(2).setChecked(True)
            self.ff_cb.setChecked(False)
            self.nlm_cb.setChecked(False)
            if self.binning_combo.currentText() != "1x1":
                self.binning_combo.setCurrentText("1x1")
            self.encoder_combo.setCurrentText("Lossless (ffv1) - Scientific")
            
            # CHANGED: Diffraction mode settings
            self.gamma = 1.00 # Reset gamma to 1.00 for unbiased diffraction data
            self.gamma_slider.setValue(100)
            
            self.exposure = 200.0
            self.manual_gain = 20.0
            
            if self.camera_connected and self.cam is not None:
                if self.cam.is_aeag():
                    self._log_message("AEAG is active - disabling it to apply Diffraction Mode's fixed gain/exposure")
                    self._disable_aeag()
                self.cam.set_gain(20.0)
                self.cam.set_exposure(int(200.0 * 1000))
                actual_ms = float(self.cam.get_exposure()) / 1000.0
                self._log_message("Diffraction Mode: Gain=20dB, Exposure=200ms, Processing OFF, Lossless Recording.")
                self._log_message(f"Exposure requested 200.0ms, camera reports {actual_ms:.1f}ms")
            else:
                self.gain_input.setText("20.0")
                self.exposure_input.setText("200.0")
                self._log_message("Diffraction Mode (No Camera): Software settings changed.")
        else:
            self.processing_worker.contrast_method = 1
            self.processing_worker.enable_flatfield = True
            self.contrast_method_group.button(1).setChecked(True)
            self.ff_cb.setChecked(True)
            self.encoder_combo.setCurrentText("GPU (hevc_nvenc) - Fast")
            
            # CHANGED: Image mode settings
            self.gamma = 1.00 
            self.gamma_slider.setValue(100)
            
            self.exposure = 40.0
            self.manual_gain = 6.0
            
            if self.camera_connected and self.cam is not None:
                if self.cam.is_aeag():
                    self._log_message("AEAG is active - disabling it to apply Image Mode's fixed gain/exposure")
                    self._disable_aeag()
                self.cam.set_gain(6.0)
                self.cam.set_exposure(int(40.0 * 1000))
                actual_ms = float(self.cam.get_exposure()) / 1000.0
                self._log_message(f"Image Mode: Gain={6.0}dB, Exposure=40ms, CLAHE ON, Flat-field ON, GPU Recording.")
                self._log_message(f"Exposure requested 40.0ms, camera reports {actual_ms:.1f}ms")
            else:
                self.gain_input.setText("6.0")
                self.exposure_input.setText("40.0")
                self._log_message("Image Mode (No Camera): Software settings changed.")

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar_container.show()
            self.fullscreen_btn.hide()
            self.toolbar_visible = True
        else:
            self.showFullScreen()
            self.toolbar_container.hide()
            self.fullscreen_btn.show()
            self.fullscreen_btn.raise_()
            self.toolbar_visible = False

    def _fade_fullscreen_button(self):
        if self.isFullScreen() and self.fullscreen_btn.isVisible():
            self.fullscreen_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 30, 30, 80);
                    color: rgba(200, 200, 200, 100);
                    border: 1px solid rgba(60, 60, 60, 50);
                    border-radius: 4px;
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(60, 60, 60, 200);
                    color: white;
                    border: 1px solid rgba(100, 100, 100, 150);
                }
                QPushButton:pressed {
                    background-color: rgba(0, 122, 204, 200);
                }
            """)

    def _unfade_fullscreen_button(self):
        if self.isFullScreen() and self.fullscreen_btn.isVisible():
            self.fullscreen_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 30, 30, 150);
                    color: rgba(200, 200, 200, 180);
                    border: 1px solid rgba(60, 60, 60, 100);
                    border-radius: 4px;
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(60, 60, 60, 200);
                    color: white;
                    border: 1px solid rgba(100, 100, 100, 150);
                }
                QPushButton:pressed {
                    background-color: rgba(0, 122, 204, 200);
                }
            """)
            QTimer.singleShot(3000, self._fade_fullscreen_button)

    def _show_toolbar_in_fullscreen(self):
        if self.isFullScreen():
            self.toolbar_container.show()
            self.toolbar_visible = True
            QTimer.singleShot(5000, self._hide_toolbar_after_timeout)

    def _hide_toolbar_after_timeout(self):
        if self.isFullScreen() and self.toolbar_visible:
            cursor_pos = QCursor.pos()
            widget_at_cursor = QApplication.widgetAt(cursor_pos)
            if widget_at_cursor:
                parent = widget_at_cursor
                while parent:
                    if parent == self.toolbar_container:
                        QTimer.singleShot(3000, self._hide_toolbar_after_timeout)
                        return
                    parent = parent.parent()
            self.toolbar_container.hide()
            self.toolbar_visible = False

    def _on_encoder_changed(self, text):
        self.encoder_choice = text
        self._update_param_label()
        if self.writer:
            self.writer.encoder_choice = self.encoder_choice
            self.writer._active.encoder_choice = self.encoder_choice
        self._log_message(f"Encoder set to: {text}")

    def _on_encoding_changed(self, text):
        self.encoding_mode = text
        self._update_param_label()
        if self.writer:
            self.writer.encoding_mode = self.encoding_mode
            self.writer._active.encoding_mode = self.encoding_mode
        self._log_message(f"Encoding mode set to: {text}")

    def _update_param_label(self):
        self._updating_param_ui = True
        if "Lossless" in self.encoder_choice:
            self.param_value_input.setEnabled(False)
            self.param_unit_label.setText("(N/A)")
        elif "Long Duration" in self.encoding_mode:
            self.param_value_input.setEnabled(True)
            self.param_unit_label.setText("(Mbps)")
            self.param_value_input.setText(self.bitrate_value)
        elif "libx265" in self.encoder_choice:
            self.param_value_input.setEnabled(True)
            self.param_unit_label.setText("(CRF)")
            self.param_value_input.setText(self.cq_value)
        else:
            self.param_value_input.setEnabled(True)
            self.param_unit_label.setText("(CQ)")
            self.param_value_input.setText(self.cq_value)
        self._updating_param_ui = False

    def _on_param_value_changed(self, text):
        if self._updating_param_ui:
            return
        if "Long Duration" in self.encoding_mode and "Lossless" not in self.encoder_choice:
            if not re.fullmatch(r'\d+[M]', text):
                print(f"Invalid Bitrate format: '{text}'. Defaulting to '8M'.")
                self.bitrate_value = "8M"
                self._updating_param_ui = True
                self.param_value_input.setText("8M")
                self._updating_param_ui = False
            else:
                self.bitrate_value = text
        elif "Lossless" not in self.encoder_choice:
            self.cq_value = text
        if self.writer:
            self.writer.cq_value = self.cq_value
            self.writer.bitrate_value = self.bitrate_value
            self.writer._active.cq_value = self.cq_value
            self.writer._active.bitrate_value = self.bitrate_value

    def _on_gamma_changed(self, value):
        val = value / 100.0
        self.gamma = max(0.1, min(3.0, val))
        self.gamma_input.setText(f"{self.gamma:.2f}")

    def _on_gamma_input_changed(self, text):
        try:
            val = float(text)
            val = max(0.1, min(3.0, val))
            self.gamma = val
            self.gamma_slider.setValue(int(val * 100))
        except ValueError as e:
            print(f"Gamma input error: {e}")

    def _on_brightness_changed(self, value):
        self.brightness = value
        self.brightness_input.setText(str(value))

    def _on_brightness_input_changed(self, text):
        try:
            val = float(text)
            val = max(-100, min(100, val))
            self.brightness = val
            self.brightness_slider.setValue(int(val))
        except ValueError as e:
            print(f"Brightness input error: {e}")

    def _on_contrast_changed(self, value):
        val = value / 100.0
        self.contrast = max(0.1, min(3.0, val))
        self.contrast_input.setText(f"{self.contrast:.2f}")

    def _on_contrast_input_changed(self, text):
        try:
            val = float(text)
            val = max(0.1, min(3.0, val))
            self.contrast = val
            self.contrast_slider.setValue(int(val * 100))
        except ValueError as e:
            print(f"Contrast input error: {e}")

    def _on_exposure_changed(self, text):
        try:
            self.exposure = float(text)
            fps = int(1000 / self.exposure) if self.exposure > 0 else 25
            self.fps_display.setText(f"FPS: {fps} (based on {self.exposure:.1f}ms exposure)")
        except ValueError as e:
            print(f"Exposure input error: {e}")

    def _open_histogram_window(self):
        if not self.camera_connected:
            return
        if self.histogram_window is None or not self.histogram_window._running:
            self.histogram_window = HistogramWindow(self)
            self.histogram_window.show()
            self._log_message("Histogram mode opened")
        else:
            self.histogram_window.raise_()
            self.histogram_window.activateWindow()

    def _on_connect_camera(self):
        if self.camera_connected:
            was_recording = self.writer is not None
            self._disconnect_camera()
            if was_recording:
                self._log_message("Force-flushing recording before disconnect...")
                self._stop_recording()
            self._set_camera_status("Camera: DISCONNECTED", "disconnected")
            self.connect_btn.setText("Connect Camera")
            self._reset_recording_ui()
            self._render_black_screen()
            self._log_message("Camera disconnected")
        else:
            success = self._try_connect_camera()
            if success:
                self._set_camera_status("Camera: CONNECTED", "connected")
                self.connect_btn.setText("Disconnect Camera")
                self._reset_recording_ui()
                self._log_message("Camera connected successfully")
            else:
                self._set_camera_status("Camera: CONNECTION FAILED", "failed")

    def _reset_recording_ui(self):
        """Reflect that no recording is in progress - connect/disconnect both leave
        self.writer as None (see _try_connect_camera), so Record/Pause reset here."""
        self.record_btn.setChecked(False)
        self.record_btn.setText("Record: OFF")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause (P)")

    def _on_record_toggle(self):
        """Start/stop recording independently of the camera connection - connecting
        only starts the live display, recording to disk is a separate explicit action."""
        if not self.camera_connected:
            self.record_btn.setChecked(False)
            return
        if self.writer is None:
            self._update_output_filename()
            self._init_writer()
            self.paused = False
            self.record_btn.setChecked(True)
            self.record_btn.setText("Record: ON")
            self.pause_btn.setEnabled(True)
            self.pause_btn.setText("Pause (P)")
        else:
            self._stop_recording()
            self._reset_recording_ui()
            self._log_message("Recording STOPPED")

    def _stop_recording(self):
        """Flush and close the active writer if a recording is in progress, collecting
        any finished segments into self.output_files. Shared by the Record button and
        manual disconnect, so disconnecting doesn't leave a recording pending an
        eventual reconnect/quit to actually save it."""
        if self.writer is None:
            return
        try:
            success = self.writer.final_flush(self.output_file, self.width, self.height, fps=self.fps)
            if success:
                self.output_files.append(self.output_file)
            self.output_files.extend(self.writer._output_files)
            self.writer.close()
        except Exception as e:
            self._log_message(f"Error stopping recording: {e}")
        self.writer = None
        self.paused = False

    def _on_pause_toggle(self):
        if self.writer is None:
            return
        if not self.paused:
            self.paused = True
            self.pause_btn.setText("Resume (P)")
            self._log_message("\nRecording PAUSED -- flushing segment to disk...")
            if self.writer:
                self.writer.pause_and_flush(self.output_file, self.width, self.height, fps=self.fps)
                self._update_output_filename()
            self._log_message("Segment saved (async). Display continues - you can move the sample")
        else:
            self.paused = False
            self.pause_btn.setText("Pause (P)")
            if self.writer:
                self.writer.set_pause(False)
            self._log_message(f"\nRecording RESUMED -- New segment: {self.output_file}")
            self.tracker_initialized = False

    def _on_screenshot(self):
        self.enable_screenshot = True
        self._log_message("Screenshot capture triggered for next frame...")

    def _start_acquisition_thread(self):
        self._acq_running = True
        self._acq_thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self._acq_thread.start()

    def _acquisition_loop(self):
        while self._acq_running:
            if not self.camera_connected or self.cam is None:
                time.sleep(0.1)
                continue
            try:
                self._process_single_frame()
            except Exception as e:
                self._log_message(f"Frame processing error: {e}")
                traceback.print_exc()
                if "device" in str(e).lower() or "xiapi" in str(e).lower():
                    self._disconnect_camera()
                    QMetaObject.invokeMethod(self, "_update_camera_status_disconnected")

    @pyqtSlot()
    def _update_camera_status_disconnected(self):
        self._set_camera_status("Camera: DISCONNECTED", "disconnected")
        self.connect_btn.setText("Connect Camera")
        self._reset_recording_ui()

    def _process_single_frame(self):
        if self.cam is None or self.img is None:
            return
        
        try:
            self.cam.get_image(self.img)
        except Exception as e:
            self._log_message(f"Error getting image: {e}")
            self._disconnect_camera()
            QMetaObject.invokeMethod(self, "_update_camera_status_disconnected")
            return
        
        raw_image = cv2.flip(self.img.get_image_data_numpy(), -1)

        is_duplicate = self.processor.is_duplicate(raw_image)
        if is_duplicate:
            self.frames_duplicate += 1
            if self.frames_duplicate % 50 == 0:
                self._log_message(f"Duplicate frames detected: {self.frames_duplicate}")

        # Drift correction: compute a per-frame (dx, dy) shift from whichever
        # tracker is active, then warp raw_image before it reaches the queue -
        # the display, processing pipeline, and recorder all read from the
        # same corrected frame instead of drifting relative to each other.
        drift_dx = drift_dy = drift_reliability = 0.0
        roi_dx = roi_dy = roi_confidence = 0.0
        drift_method = self._prev_drift_choice
        if drift_method == 1:
            if not self.tracker_initialized:
                self.drift_tracker.initialize(raw_image)
                self.tracker_initialized = True
            else:
                drift_dx, drift_dy, drift_reliability = self.drift_tracker.compute_drift(raw_image)
        elif drift_method == 2:
            shift_x, shift_y, roi_confidence = self.roi_tracker.compute_offset(raw_image)
            # compute_offset() already returns the correction shift (i.e.
            # -displacement internally) - negate it again here, or the
            # correction doubles the drift instead of cancelling it.
            roi_dx, roi_dy = -shift_x, -shift_y

        dx = drift_dx if drift_method == 1 else roi_dx
        dy = drift_dy if drift_method == 1 else roi_dy
        if drift_method != 0 and (abs(dx) > 0.01 or abs(dy) > 0.01):
            raw_image = self.processor.apply_drift_correction(raw_image, dx, dy)

        with self._camera_lock:
            self._current_image = raw_image

        self.frames_read += 1
        self.processor.frame_count += 1

        if drift_method == 1 and self.csv_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            self.csv_file.write(f"{self.frames_read},{drift_dx},{drift_dy},{drift_reliability},{timestamp}\n")

        # Pass UI settings to worker
        self.processing_worker.brightness = self.brightness
        self.processing_worker.contrast = self.contrast
        self.processing_worker.gamma = self.gamma

        # NEW: Pass filter settings and type to worker
        self.processing_worker.filter_type = self.filter_group.checkedId()
        self.processing_worker.gaussian_kernel = self.gaussian_kernel
        self.processing_worker.gaussian_sigma = self.gaussian_sigma
        self.processing_worker.median_kernel = self.median_kernel
        self.processing_worker.bilateral_d = self.bilateral_d
        self.processing_worker.bilateral_sigmaColor = self.bilateral_sigmaColor
        self.processing_worker.bilateral_sigmaSpace = self.bilateral_sigmaSpace

        if self.raw_queue.full():
            try:
                self.raw_queue.get_nowait()
                self.frames_dropped += 1
            except Exception as e:
                print(f"Queue cleanup error: {e}")
                pass
        self.raw_queue.put(raw_image.copy())

        # Wait for worker to process
        try:
            processed_for_display = self.display_queue.get(timeout=0.2)
        except queue.Empty:
            processed_for_display = raw_image

        record_image = processed_for_display
        if record_image.dtype != np.uint8:
            record_image = np.clip(record_image, 0, 255).astype(np.uint8)

        if self.writer is not None and not self.paused and not is_duplicate:
            success = self.writer.write(record_image)
            if success:
                self.frames_queued += 1
            else:
                self.frames_dropped += 1

        if self.enable_screenshot:
            self.enable_screenshot = False
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            capture_filename = os.path.join(
                self.video_output_path,
                f"capture_{timestamp}_frame{self.processor.frame_count:06d}.png"
            )
            cv2.imwrite(capture_filename, record_image)
            self._log_message(f"[CAPTURE] Saved: {capture_filename}")

        current_time = time.time()
        self._fps_counter += 1
        if current_time - self._fps_timer >= 0.5:
            self.actual_fps = self._fps_counter / (current_time - self._fps_timer)
            self._fps_counter = 0
            self._fps_timer = current_time

        display_bgr = cv2.cvtColor(processed_for_display, cv2.COLOR_GRAY2BGR)
        self._last_display_image = display_bgr
        self._last_stats = {
            'fps': self.actual_fps,
            'frame': self.frames_read,
            'dups': self.frames_duplicate,
            'drift_x': drift_dx,
            'drift_y': drift_dy,
            'drift_reliability': drift_reliability,
            'roi_dx': roi_dx,
            'roi_dy': roi_dy,
            'roi_confidence': roi_confidence,
        }

        if RECORD_MODE == "raw" and self.writer is not None and self.writer.should_flush():
            self._log_message(f"\n[AUTO-FLUSH] Swapping writers at frame {self.frames_read}...")
            self._update_output_filename()
            self.output_file = self.writer.swap_and_flush(self.output_file, self.width, self.height, fps=self.fps)
            self._log_message(f"[AUTO-FLUSH] New segment: {self.output_file}")

    def _build_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.main_container = QWidget()
        main_container_layout = QHBoxLayout(self.main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)

        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.setSpacing(0)

        overlay_widget = QWidget()
        overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        overlay_layout = QGridLayout(overlay_widget)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        overlay_layout.addWidget(self.image_label, 0, 0, 1, 1)

        self.fullscreen_btn = QPushButton("☰")
        self.fullscreen_btn.setFixedSize(30, 30)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 30, 30, 150);
                color: rgba(200, 200, 200, 180);
                border: 1px solid rgba(60, 60, 60, 100);
                border-radius: 4px;
                font-size: 14pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(60, 60, 60, 200);
                color: white;
                border: 1px solid rgba(100, 100, 100, 150);
            }
            QPushButton:pressed {
                background-color: rgba(0, 122, 204, 200);
            }
        """)
        self.fullscreen_btn.clicked.connect(self._show_toolbar_in_fullscreen)
        self.fullscreen_btn.hide()
        self.fullscreen_btn.enterEvent = lambda e: self._unfade_fullscreen_button()
        self.fullscreen_btn.leaveEvent = lambda e: QTimer.singleShot(3000, self._fade_fullscreen_button)

        button_container = QWidget()
        button_container.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(0)
        button_layout.addStretch()
        button_layout.addWidget(self.fullscreen_btn)
        overlay_layout.addWidget(button_container, 0, 0, 1, 1, alignment=Qt.AlignTop | Qt.AlignRight)

        image_layout.addWidget(overlay_widget)

        status_widget = QWidget()
        status_widget.setObjectName("status_bar_widget")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 5, 5, 5)

        self.fps_label = QLabel("FPS: --")
        self.frame_label = QLabel("Frame: 0")
        self.dups_label = QLabel("Dups: 0")
        self.drift_label = QLabel("")
        self.roi_label = QLabel("")
        self.buffer_label = QLabel("")

        status_layout.addWidget(self.fps_label)
        status_layout.addWidget(self.frame_label)
        status_layout.addWidget(self.dups_label)
        status_layout.addWidget(self.drift_label)
        status_layout.addWidget(self.roi_label)
        status_layout.addWidget(self.buffer_label)
        status_layout.addStretch()

        image_layout.addWidget(status_widget)
        main_container_layout.addWidget(image_widget, 2)

        self.toolbar_container = QWidget()
        self.toolbar_container.setObjectName("toolbar_container")
        self.toolbar_container.setMaximumWidth(380)
        self.toolbar_container.setMinimumWidth(320)
        toolbar_container_layout = QVBoxLayout(self.toolbar_container)
        toolbar_container_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_container_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        toolbar_content = QWidget()
        self.toolbar_layout = QVBoxLayout(toolbar_content)
        self.toolbar_layout.setContentsMargins(4, 4, 4, 4)
        self.toolbar_layout.setSpacing(3)

        self._build_toolbar()

        self.scroll_area.setWidget(toolbar_content)
        toolbar_container_layout.addWidget(self.scroll_area)

        main_container_layout.addWidget(self.toolbar_container, 1)
        main_layout.addWidget(self.main_container)

    def _tighten(self, layout):
        """Compact margins/spacing for a group box's outer layout - QGroupBox's own
        QSS padding plus a layout's platform-default margins doubles up the inset,
        which is what makes toolbar boxes look oversized without this."""
        layout.setContentsMargins(8, 4, 8, 6)
        layout.setSpacing(3)

    def _build_toolbar(self):
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QHBoxLayout(appearance_group)
        self._tighten(appearance_layout)
        appearance_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentIndexChanged.connect(lambda i: self._apply_theme('light' if i == 1 else 'dark'))
        appearance_layout.addWidget(self.theme_combo)
        self.toolbar_layout.addWidget(appearance_group)

        # VIDEO OUTPUT
        path_group = QGroupBox("Video Output")
        path_layout = QVBoxLayout(path_group)
        self._tighten(path_layout)
        path_btn_layout = QHBoxLayout()
        self.path_label = QLabel(f"📁 {self.video_output_path}")
        self.path_label.setObjectName("path_label")
        self.path_label.setWordWrap(True)
        path_btn_layout.addWidget(self.path_label)
        path_btn = QPushButton("Choose Folder")
        path_btn.clicked.connect(self._choose_output_path)
        path_btn.setFixedWidth(100)
        path_btn_layout.addWidget(path_btn)
        path_layout.addLayout(path_btn_layout)
        self.toolbar_layout.addWidget(path_group)

        # CAMERA
        status_group = QGroupBox("Camera")
        status_layout = QVBoxLayout(status_group)
        self._tighten(status_layout)
        self.camera_status_label = QLabel("Camera: DISCONNECTED")
        status_layout.addWidget(self.camera_status_label)

        self.connect_btn = QPushButton("Connect Camera")
        self.connect_btn.setObjectName("primary")
        self.connect_btn.clicked.connect(self._on_connect_camera)

        self.record_btn = QPushButton("Record: OFF")
        self.record_btn.setCheckable(True)
        self.record_btn.setToolTip("Start/stop saving the live feed to disk. Connecting the camera only starts the display - recording is separate.")
        self.record_btn.clicked.connect(self._on_record_toggle)

        self.pause_btn = QPushButton("Pause (P)")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause_toggle)

        reset_btn = QPushButton("Reset (R)")
        reset_btn.setToolTip("Restore gamma, brightness/contrast, contrast method, filters, flat-field, NLM, and drift correction to their defaults.")
        reset_btn.clicked.connect(self._on_reset)

        fullscreen_btn_toolbar = QPushButton("Fullscreen (F11)")
        fullscreen_btn_toolbar.clicked.connect(self._toggle_fullscreen)

        hist_btn = QPushButton("Open Histogram (H)")
        hist_btn.clicked.connect(self._open_histogram_window)

        screenshot_btn = QPushButton("Screenshot (C)")
        screenshot_btn.clicked.connect(self._on_screenshot)

        quit_btn = QPushButton("Quit (Q)")
        quit_btn.clicked.connect(self.on_quit)

        session_grid = QGridLayout()
        session_grid.setSpacing(3)
        session_grid.addWidget(self.connect_btn, 0, 0)
        session_grid.addWidget(self.record_btn, 0, 1)
        session_grid.addWidget(self.pause_btn, 1, 0)
        session_grid.addWidget(reset_btn, 1, 1)
        session_grid.addWidget(fullscreen_btn_toolbar, 2, 0)
        session_grid.addWidget(hist_btn, 2, 1)
        session_grid.addWidget(screenshot_btn, 3, 0)
        session_grid.addWidget(quit_btn, 3, 1)
        status_layout.addLayout(session_grid)

        self.toolbar_layout.addWidget(status_group)

        checkbox_row = QHBoxLayout()
        self.ff_cb = QCheckBox("Flat-field correction")
        self.ff_cb.setChecked(True)
        self.ff_cb.stateChanged.connect(self._on_ff_toggle)
        checkbox_row.addWidget(self.ff_cb)
        self.concat_cb = QCheckBox("Concatenate videos on quit")
        self.concat_cb.setChecked(True)
        self.concat_cb.stateChanged.connect(lambda state: setattr(self, 'concat_on_quit', state == Qt.Checked))
        checkbox_row.addWidget(self.concat_cb)
        self.toolbar_layout.addLayout(checkbox_row)

        # MODE SELECTION
        mode_group = QGroupBox("Microscope Mode")
        mode_layout = QVBoxLayout(mode_group)
        self._tighten(mode_layout)
        mode_layout.addWidget(QLabel("Current Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Image Mode", "Diffraction Mode"])
        self.mode_combo.currentTextChanged.connect(self._on_microscope_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        self.toolbar_layout.addWidget(mode_group)

        # HARDWARE CONTROLS
        hw_group = QGroupBox("Hardware Controls")
        hw_layout = QVBoxLayout(hw_group)
        self._tighten(hw_layout)

        exp_layout = QHBoxLayout()
        exp_layout.addWidget(QLabel("Exposure (ms):"))
        self.exposure_input = QLineEdit()
        self.exposure_input.setText("40.0")
        self.exposure_input.setFixedWidth(60)
        self.exposure_input.textChanged.connect(self._on_exposure_changed)
        exp_layout.addWidget(self.exposure_input)
        self.apply_exp_btn = QPushButton("Apply")
        self.apply_exp_btn.clicked.connect(self._apply_exposure)
        exp_layout.addWidget(self.apply_exp_btn)
        exp_layout.addStretch()
        hw_layout.addLayout(exp_layout)
        self.fps_display = QLabel("FPS: 25")
        hw_layout.addWidget(self.fps_display)

        binning_layout = QHBoxLayout()
        binning_layout.addWidget(QLabel("Binning:"))
        self.binning_combo = QComboBox()
        self.binning_combo.addItems(["1x1", "2x2"])
        self.binning_combo.currentTextChanged.connect(self._on_binning_changed)
        binning_layout.addWidget(self.binning_combo)
        binning_layout.addStretch()
        hw_layout.addLayout(binning_layout)

        self.gain_btn = QPushButton("Auto Exposure/Gain (AEAG): OFF")
        self.gain_btn.setCheckable(True)
        self.gain_btn.setChecked(False)
        self.gain_btn.setToolTip(
            "Ximea AEAG controls exposure AND gain together - there is no gain-only\n"
            "auto mode. While this is ON, manual exposure changes are auto-disabled\n"
            "AEAG first (see Apply next to Exposure)."
        )
        self.gain_btn.clicked.connect(self._on_gain_toggle)
        hw_layout.addWidget(self.gain_btn)

        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Manual Gain (dB):"))
        self.gain_input = QLineEdit()
        self.gain_input.setText("6.0")
        self.gain_input.setFixedWidth(60)
        self.gain_input.textChanged.connect(lambda text: None)
        gain_layout.addWidget(self.gain_input)
        gain_layout.addStretch()
        hw_layout.addLayout(gain_layout)

        self.apply_gain_btn = QPushButton("Apply Gain")
        self.apply_gain_btn.clicked.connect(self._apply_manual_gain)
        hw_layout.addWidget(self.apply_gain_btn)

        self.toolbar_layout.addWidget(hw_group)

        # ADVANCED ENCODING SETTINGS
        enc_group = QGroupBox("Advanced Encoder Settings")
        enc_layout = QVBoxLayout(enc_group)
        self._tighten(enc_layout)
        enc_layout.addWidget(QLabel("Encoder:"))
        self.encoder_combo = QComboBox()
        self.encoder_combo.addItems([
            "GPU (hevc_nvenc) - Fast",
            "CPU (libx265) - Smallest",
            "Lossless (ffv1) - Scientific"
        ])
        self.encoder_combo.currentTextChanged.connect(self._on_encoder_changed)
        enc_layout.addWidget(self.encoder_combo)
        enc_layout.addWidget(QLabel("Encoding Mode:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["High Quality (CQ)", "Long Duration (Max Bitrate)"])
        self.encoding_combo.currentTextChanged.connect(self._on_encoding_changed)
        enc_layout.addWidget(self.encoding_combo)
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("Value:"))
        self.param_value_input = QLineEdit()
        self.param_value_input.setText("12")
        self.param_value_input.setFixedWidth(60)
        self.param_value_input.textChanged.connect(self._on_param_value_changed)
        param_layout.addWidget(self.param_value_input)
        self.param_unit_label = QLabel("(CQ)")
        param_layout.addWidget(self.param_unit_label)
        param_layout.addStretch()
        enc_layout.addLayout(param_layout)
        self.toolbar_layout.addWidget(enc_group)

        log_btn = QPushButton("📋 Output Log")
        log_btn.clicked.connect(self._toggle_log_window)
        self.toolbar_layout.addWidget(log_btn)

        # AUDIO
        audio_group = QGroupBox("Audio Recording")
        audio_layout = QVBoxLayout(audio_group)
        self._tighten(audio_layout)
        self.audio_cb = QCheckBox("Record Audio")
        self.audio_cb.setChecked(True)
        self.audio_cb.stateChanged.connect(self._on_audio_toggle)
        audio_layout.addWidget(self.audio_cb)
        audio_device_layout = QHBoxLayout()
        audio_device_layout.addWidget(QLabel("Device:"))
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.addItems([
            "Desktop Microphone (RØDE NT-USB+)",
            "Microphone (Realtek High Definition Audio)",
            "Microphone (USB Audio Device)"
        ])
        self.audio_device_combo.setCurrentIndex(0)
        self.audio_device_combo.currentTextChanged.connect(self._on_audio_device_changed)
        audio_device_layout.addWidget(self.audio_device_combo)
        audio_layout.addLayout(audio_device_layout)
        self.toolbar_layout.addWidget(audio_group)

        # IMAGE ADJUSTMENTS
        adjust_group = QGroupBox("Gamma / Brightness / Contrast")
        adjust_layout = QVBoxLayout(adjust_group)
        self._tighten(adjust_layout)

        adjust_layout.addWidget(QLabel("Gamma:"))
        gamma_slider_layout = QHBoxLayout()
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(10, 300)
        self.gamma_slider.setValue(100)
        self.gamma_slider.valueChanged.connect(self._on_gamma_changed)
        gamma_slider_layout.addWidget(self.gamma_slider)
        self.gamma_input = QLineEdit()
        self.gamma_input.setText("1.00")
        self.gamma_input.setFixedWidth(60)
        self.gamma_input.textChanged.connect(self._on_gamma_input_changed)
        gamma_slider_layout.addWidget(self.gamma_input)
        adjust_layout.addLayout(gamma_slider_layout)
        adjust_layout.addWidget(QLabel("(0.1 - 3.0)"))

        adjust_layout.addWidget(QLabel("Brightness:"))
        br_layout = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        br_layout.addWidget(self.brightness_slider)
        self.brightness_input = QLineEdit()
        self.brightness_input.setText("0")
        self.brightness_input.setFixedWidth(60)
        self.brightness_input.textChanged.connect(self._on_brightness_input_changed)
        br_layout.addWidget(self.brightness_input)
        adjust_layout.addLayout(br_layout)
        adjust_layout.addWidget(QLabel("(-100 to 100)"))

        adjust_layout.addWidget(QLabel("Contrast:"))
        co_layout = QHBoxLayout()
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(10, 300)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        co_layout.addWidget(self.contrast_slider)
        self.contrast_input = QLineEdit()
        self.contrast_input.setText("1.0")
        self.contrast_input.setFixedWidth(60)
        self.contrast_input.textChanged.connect(self._on_contrast_input_changed)
        co_layout.addWidget(self.contrast_input)
        adjust_layout.addLayout(co_layout)
        adjust_layout.addWidget(QLabel("(0.1 to 3.0)"))
        self.toolbar_layout.addWidget(adjust_group)

        # CONTRAST METHOD
        contrast_method_group = QGroupBox("Contrast method")
        contrast_method_layout = QVBoxLayout(contrast_method_group)
        self._tighten(contrast_method_layout)
        self.contrast_method_group = QButtonGroup()
        rb_auto = QRadioButton("Autocontrast")
        rb_auto.setChecked(False)
        self.contrast_method_group.addButton(rb_auto, 0)
        contrast_method_layout.addWidget(rb_auto)
        rb_clahe = QRadioButton("CLAHE (Recommended)")
        rb_clahe.setChecked(True)
        self.contrast_method_group.addButton(rb_clahe, 1)
        contrast_method_layout.addWidget(rb_clahe)
        rb_none = QRadioButton("None")
        self.contrast_method_group.addButton(rb_none, 2)
        contrast_method_layout.addWidget(rb_none)
        self.contrast_method_group.buttonClicked.connect(self._on_contrast_method_changed)
        self.toolbar_layout.addWidget(contrast_method_group)

        # FILTER - NOW WITH WIRED GAUSSIAN, MEDIAN, BILATERAL
        filter_group = QGroupBox("Filter")
        filter_layout = QVBoxLayout(filter_group)
        self._tighten(filter_layout)
        self.filter_group = QButtonGroup()
        for val, label in [(0, "None"), (1, "Gaussian"), (2, "Median"), (3, "Bilateral")]:
            rb = QRadioButton(label)
            rb.setChecked(val == 0)
            self.filter_group.addButton(rb, val)
            filter_layout.addWidget(rb)

        self.nlm_cb = QCheckBox("NLM Denoising")
        self.nlm_cb.setChecked(False)
        self.nlm_cb.stateChanged.connect(self._on_nlm_toggle)
        filter_layout.addWidget(self.nlm_cb)

        self.toolbar_layout.addWidget(filter_group)

        self._build_filter_settings()

        # DRIFT
        drift_group = QGroupBox("Drift correction")
        drift_layout = QVBoxLayout(drift_group)
        self._tighten(drift_layout)
        self.drift_group = QButtonGroup()
        for val, label in [(0, "None"), (1, "Edge-strip"), (2, "ROI (click+drag on preview)")]:
            rb = QRadioButton(label)
            rb.setChecked(val == 0)
            self.drift_group.addButton(rb, val)
            drift_layout.addWidget(rb)
        self.drift_group.buttonClicked.connect(self._on_drift_change)
        self.toolbar_layout.addWidget(drift_group)

        self.toolbar_layout.addStretch()

    def _build_filter_settings(self):
        filter_settings_group = QGroupBox("Filter settings")
        filter_settings_layout = QVBoxLayout(filter_settings_group)
        self._tighten(filter_settings_layout)

        gk_layout = QHBoxLayout()
        gk_layout.addWidget(QLabel("Gaussian kernel (odd):"))
        self.gaussian_kernel_input = QLineEdit()
        self.gaussian_kernel_input.setText("3")
        self.gaussian_kernel_input.setFixedWidth(50)
        self.gaussian_kernel_input.textChanged.connect(lambda: self._update_filter_param('gaussian_kernel', self.gaussian_kernel_input))
        gk_layout.addWidget(self.gaussian_kernel_input)
        gk_layout.addStretch()
        filter_settings_layout.addLayout(gk_layout)

        gs_layout = QHBoxLayout()
        gs_layout.addWidget(QLabel("Sigma:"))
        self.gaussian_sigma_input = QLineEdit()
        self.gaussian_sigma_input.setText("1.0")
        self.gaussian_sigma_input.setFixedWidth(50)
        self.gaussian_sigma_input.textChanged.connect(lambda: self._update_filter_param('gaussian_sigma', self.gaussian_sigma_input))
        gs_layout.addWidget(self.gaussian_sigma_input)
        gs_layout.addStretch()
        filter_settings_layout.addLayout(gs_layout)

        mk_layout = QHBoxLayout()
        mk_layout.addWidget(QLabel("Median kernel (odd):"))
        self.median_kernel_input = QLineEdit()
        self.median_kernel_input.setText("3")
        self.median_kernel_input.setFixedWidth(50)
        self.median_kernel_input.textChanged.connect(lambda: self._update_filter_param('median_kernel', self.median_kernel_input))
        mk_layout.addWidget(self.median_kernel_input)
        mk_layout.addStretch()
        filter_settings_layout.addLayout(mk_layout)

        bd_layout = QHBoxLayout()
        bd_layout.addWidget(QLabel("Bilateral diameter:"))
        self.bilateral_d_input = QLineEdit()
        self.bilateral_d_input.setText("9")
        self.bilateral_d_input.setFixedWidth(50)
        self.bilateral_d_input.textChanged.connect(lambda: self._update_filter_param('bilateral_d', self.bilateral_d_input))
        bd_layout.addWidget(self.bilateral_d_input)
        bd_layout.addStretch()
        filter_settings_layout.addLayout(bd_layout)

        bsc_layout = QHBoxLayout()
        bsc_layout.addWidget(QLabel("Sigma color:"))
        self.bilateral_sc_input = QLineEdit()
        self.bilateral_sc_input.setText("75")
        self.bilateral_sc_input.setFixedWidth(50)
        self.bilateral_sc_input.textChanged.connect(lambda: self._update_filter_param('bilateral_sigmaColor', self.bilateral_sc_input))
        bsc_layout.addWidget(self.bilateral_sc_input)
        bsc_layout.addStretch()
        filter_settings_layout.addLayout(bsc_layout)

        bss_layout = QHBoxLayout()
        bss_layout.addWidget(QLabel("Sigma space:"))
        self.bilateral_ss_input = QLineEdit()
        self.bilateral_ss_input.setText("75")
        self.bilateral_ss_input.setFixedWidth(50)
        self.bilateral_ss_input.textChanged.connect(lambda: self._update_filter_param('bilateral_sigmaSpace', self.bilateral_ss_input))
        bss_layout.addWidget(self.bilateral_ss_input)
        bss_layout.addStretch()
        filter_settings_layout.addLayout(bss_layout)
        self.toolbar_layout.addWidget(filter_settings_group)

    def _update_filter_param(self, param, input_widget):
        try:
            val = float(input_widget.text())
            if param in ['gaussian_kernel', 'median_kernel', 'bilateral_d']: 
                val = int(val)
            setattr(self, param, val)
        except ValueError as e:
            print(f"Filter param error: {e}")

    def _on_ff_toggle(self, state):
        self.processing_worker.enable_flatfield = (state == Qt.Checked)
        self.processing_worker.D = self.D
        self.processing_worker.G = self.G
        self._log_message(f"Flat-field correction {'ENABLED' if state == Qt.Checked else 'DISABLED'}")

    def _on_nlm_toggle(self, state):
        self.processing_worker.enable_nlm = (state == Qt.Checked)
        self._log_message(f"NLM Denoising {'ENABLED' if state == Qt.Checked else 'DISABLED'}")

    def _on_contrast_method_changed(self, button):
        method_id = self.contrast_method_group.id(button)
        self.processing_worker.contrast_method = method_id
        self._log_message(f"Contrast method set to: {button.text()}")

    def _on_audio_toggle(self, state):
        self.record_audio = (state == Qt.Checked)
        if self.writer: 
            self.writer.set_audio(self.record_audio, self.audio_device)
        self._log_message(f"Audio recording {'ENABLED' if self.record_audio else 'DISABLED'}")

    def _on_audio_device_changed(self, device_name):
        self.audio_device = f"audio={device_name}"
        if self.writer and self.record_audio: 
            self.writer.set_audio(self.record_audio, self.audio_device)
        self._log_message(f"Audio device set to: {self.audio_device}")

    def _on_drift_change(self, button):
        new_val = self.drift_group.id(button)
        old_val = self._prev_drift_choice
        if new_val == old_val:
            return
        if old_val == 1 and new_val != 1:
            if self.csv_file:
                self.csv_file.close()
                self._log_message(f"Drift log saved: {self.csv_filename}")
            self.csv_file = None
        if new_val == 1:
            self.tracker_initialized = False
            self.csv_filename = f"drift_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.csv_file = open(self.csv_filename, 'w')
            self.csv_file.write("frame,drift_x,drift_y,reliability,timestamp\n")
            self._log_message(f"Drift log: {self.csv_filename} | Edge-strip drift ENABLED")
        if old_val == 2 and new_val != 2:
            if self.roi_tracker.selecting:
                self.roi_tracker.selecting = False
                self.roi_tracker.selection_start = None
                self.roi_tracker.selection_end = None
        if new_val == 2:
            if not self.roi_tracker.roi_locked and not self.roi_tracker.selecting:
                self.roi_tracker.start_selection()
                self._log_message("ROI selection started - click and drag on the preview")
        self._prev_drift_choice = new_val

    def _on_reset(self):
        """Restore every processing/display setting to its startup default. Camera
        hardware (exposure/gain), microscope mode, encoder, and audio settings are
        left untouched - those are session configuration, not display tweaks."""
        if self._prev_drift_choice == 1 and self.csv_file:
            self.csv_file.close()
            self._log_message(f"Drift log saved: {self.csv_filename}")
            self.csv_file = None
        self.roi_tracker.reset()
        self.drift_tracker.reset()
        self.tracker_initialized = False
        for btn in self.drift_group.buttons():
            if self.drift_group.id(btn) == 0:
                btn.setChecked(True)
        self._prev_drift_choice = 0

        self.gamma_slider.setValue(100)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)

        self.contrast_method_group.button(1).setChecked(True)  # CLAHE
        self.processing_worker.contrast_method = 1

        self.filter_group.button(0).setChecked(True)  # None
        self.gaussian_kernel_input.setText("3")
        self.gaussian_sigma_input.setText("1.0")
        self.median_kernel_input.setText("3")
        self.bilateral_d_input.setText("9")
        self.bilateral_sc_input.setText("75")
        self.bilateral_ss_input.setText("75")
        self.nlm_cb.setChecked(False)
        self.ff_cb.setChecked(True)

        self.processor.reset()
        self._log_message("Reset: all processing/display settings restored to defaults")

    def mousePressEvent(self, event):
        """During ROI selection, maps the click from label pixels to frame pixels
        (accounting for the letterboxed pixmap) and starts the ROI drag."""
        if self.roi_tracker.selecting:
            pos = event.pos()
            label_pos = self.image_label.pos()
            if label_pos.x() <= pos.x() < label_pos.x() + self.image_label.width():
                if label_pos.y() <= pos.y() < label_pos.y() + self.image_label.height():
                    pixmap = self.image_label.pixmap()
                    if pixmap and not pixmap.isNull():
                        img_w = pixmap.width()
                        img_h = pixmap.height()
                        label_w = self.image_label.width()
                        label_h = self.image_label.height()
                        x = pos.x() - label_pos.x()
                        y = pos.y() - label_pos.y()
                        offset_x = (label_w - img_w) // 2
                        offset_y = (label_h - img_h) // 2
                        fx = (x - offset_x) / img_w * self.width
                        fy = (y - offset_y) / img_h * self.height
                        self.roi_tracker.on_mouse_down(int(fx), int(fy))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Un-fades the fullscreen button on movement, and during ROI selection
        maps the cursor to frame pixels to update the in-progress drag."""
        if self.isFullScreen():
            self._unfade_fullscreen_button()
        if self.roi_tracker.selecting:
            pos = event.pos()
            label_pos = self.image_label.pos()
            if label_pos.x() <= pos.x() < label_pos.x() + self.image_label.width():
                if label_pos.y() <= pos.y() < label_pos.y() + self.image_label.height():
                    pixmap = self.image_label.pixmap()
                    if pixmap and not pixmap.isNull():
                        img_w = pixmap.width()
                        img_h = pixmap.height()
                        label_w = self.image_label.width()
                        label_h = self.image_label.height()
                        x = pos.x() - label_pos.x()
                        y = pos.y() - label_pos.y()
                        offset_x = (label_w - img_w) // 2
                        offset_y = (label_h - img_h) // 2
                        fx = (x - offset_x) / img_w * self.width
                        fy = (y - offset_y) / img_h * self.height
                        self.roi_tracker.on_mouse_move(int(fx), int(fy))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """During ROI selection, maps the release point to frame pixels and
        locks in the dragged region as the tracked ROI template."""
        if self.roi_tracker.selecting:
            pos = event.pos()
            label_pos = self.image_label.pos()
            if label_pos.x() <= pos.x() < label_pos.x() + self.image_label.width():
                if label_pos.y() <= pos.y() < label_pos.y() + self.image_label.height():
                    pixmap = self.image_label.pixmap()
                    if pixmap and not pixmap.isNull():
                        img_w = pixmap.width()
                        img_h = pixmap.height()
                        label_w = self.image_label.width()
                        label_h = self.image_label.height()
                        x = pos.x() - label_pos.x()
                        y = pos.y() - label_pos.y()
                        offset_x = (label_w - img_w) // 2
                        offset_y = (label_h - img_h) // 2
                        fx = (x - offset_x) / img_w * self.width
                        fy = (y - offset_y) / img_h * self.height
                        self.roi_tracker.on_mouse_move(int(fx), int(fy))
                        if self._current_image is not None:
                            self.roi_tracker.on_mouse_up(self._current_image, 1.0, 1.0)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Global keyboard shortcuts: P pause, C screenshot, Q quit, R reset,
        H histogram, F11 fullscreen, Escape exits fullscreen."""
        key = event.key()
        if key == Qt.Key_P:
            self._on_pause_toggle()
            event.accept()
            return
        elif key == Qt.Key_C:
            self._on_screenshot()
            event.accept()
            return
        elif key == Qt.Key_Q:
            self.on_quit()
            event.accept()
            return
        elif key == Qt.Key_R:
            self._on_reset()
            event.accept()
            return
        elif key == Qt.Key_H:
            self._open_histogram_window()
            event.accept()
            return
        elif key == Qt.Key_F11:
            self._toggle_fullscreen()
            event.accept()
            return
        elif key == Qt.Key_Escape and self.isFullScreen():
            self._toggle_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def _update_ui(self):
        if not self._running:
            return
        if self.camera_connected and hasattr(self, '_last_display_image') and self._last_display_image is not None:
            self._render_to_label(self._last_display_image)
            self._update_status_labels()
        else:
            self._render_black_screen()

    def _render_to_label(self, bgr_image):
        h, w = bgr_image.shape[:2]
        label_size = self.image_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return
        if w > 0 and h > 0:
            scale = min(label_size.width() / w, label_size.height() / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(bgr_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.image_label.setPixmap(pixmap)

    def _render_black_screen(self):
        label_size = self.image_label.size()
        w = max(1, label_size.width())
        h = max(1, label_size.height())
        black = np.zeros((h, w, 3), dtype=np.uint8)
        text = "Camera not connected"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (w - text_size[0]) // 2
        text_y = (h + text_size[1]) // 2
        cv2.putText(black, text, (text_x, text_y), font, font_scale, (200, 200, 200), thickness)
        text2 = "Click 'Connect Camera' to start"
        text2_size = cv2.getTextSize(text2, font, 0.6, 1)[0]
        text2_x = (w - text2_size[0]) // 2
        text2_y = text_y + 40
        cv2.putText(black, text2, (text2_x, text2_y), font, 0.6, (150, 150, 150), 1)
        rgb = cv2.cvtColor(black, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)

    def _update_status_labels(self):
        if not hasattr(self, '_last_stats'):
            return
        stats = self._last_stats
        self.fps_label.setText(f"FPS: {stats['fps']:.1f}")
        self.frame_label.setText(f"Frame: {stats['frame']}")
        self.dups_label.setText(f"Dups: {stats['dups']}")
        if self._prev_drift_choice == 1:
            self.drift_label.setText(
                f"Drift: dx={stats['drift_x']:.1f} dy={stats['drift_y']:.1f} rel={stats['drift_reliability']:.2f}"
            )
        else:
            self.drift_label.setText("")
        if self._prev_drift_choice == 2:
            self.roi_label.setText(
                f"ROI: dx={stats['roi_dx']:.1f} dy={stats['roi_dy']:.1f} conf={stats['roi_confidence']:.2f}"
            )
        else:
            self.roi_label.setText("")

        if RECORD_MODE == "raw" and self.writer is not None:
            active_frames = self.writer._active.frame_count if self.writer._active else 0
            flushing = "YES" if self.writer._flushing else "NO"
            self.buffer_label.setText(f"Buffer: {self.writer.get_ram_usage_mb():.1f}MB  A:{active_frames}  Flush:{flushing}")
        else:
            self.buffer_label.setText("")

    def _concatenate_videos(self, output_files, final_output_path):
        if len(output_files) <= 1:
            if len(output_files) == 1:
                try:
                    os.rename(output_files[0], final_output_path)
                    self._log_message(f"✓ Single segment saved as: {final_output_path}")
                    return True
                except Exception as e:
                    self._log_message(f"✗ Error renaming file: {e}")
                    return False
            return False
        try:
            concat_file = os.path.join(self.video_output_path, "concat_list.txt")
            with open(concat_file, 'w') as f:
                for video_file in output_files:
                    abs_path = os.path.abspath(video_file).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-fflags', '+genpts', '-avoid_negative_ts', 'make_zero', final_output_path]
            self._log_message(f"\n{'='*60}")
            self._log_message(f"CONCATENATING {len(output_files)} VIDEO SEGMENTS")
            self._log_message(f"{'='*60}")
            self._log_message(f"  ✓ Video: Lossless copy")
            self._log_message(f"  ✓ Audio: Re-encoded for smooth playback")
            self._log_message(f"  Output: {os.path.basename(final_output_path)}")
            total_size = sum(os.path.getsize(f) for f in output_files) / (1024*1024)
            self._log_message(f"  Total size: {total_size:.1f} MB")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if os.path.exists(concat_file): 
                os.remove(concat_file)
            if result.returncode == 0:
                final_size = os.path.getsize(final_output_path) / (1024*1024)
                self._log_message(f"\n✓ Successfully concatenated: {final_size:.1f} MB")
                self._log_message(f"  Saved as: {final_output_path}")
                for video_file in output_files:
                    try:
                        if os.path.exists(video_file) and video_file != final_output_path:
                            os.remove(video_file)
                            self._log_message(f"  Removed: {os.path.basename(video_file)}")
                    except Exception as e:
                        self._log_message(f"  Warning: Could not remove {os.path.basename(video_file)}: {e}")
                return True
            else:
                self._log_message(f"✗ FFmpeg concat failed: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            self._log_message("✗ Concatenation timed out (300s)")
            return False
        except Exception as e:
            self._log_message(f"✗ Concatenation error: {e}")
            return False

    def on_quit(self):
        """Shuts down cleanly: stops acquisition/processing threads, flushes any
        pending recording to disk, closes the camera, and (if enabled) concatenates
        the session's video segments into one file. Safe to call more than once."""
        if getattr(self, '_shutdown_done', False):
            return
        self._shutdown_done = True
        
        self._log_message("\nShutting down...")
        
        self._acq_running = False
        
        if self._acq_thread and self._acq_thread.is_alive():
            self._log_message("Waiting for acquisition thread to stop...")
            self._acq_thread.join(timeout=2.0)
            if self._acq_thread.is_alive():
                self._log_message("WARNING: Acquisition thread didn't stop, continuing shutdown...")
        
        self.processing_worker.stop()
        
        if self.histogram_window is not None:
            try:
                self.histogram_window.close()
            except Exception as e:
                print(f"Error closing histogram: {e}")
            self.histogram_window = None
        
        if not self.paused and self.writer is not None:
            self._update_output_filename()
            try:
                success = self.writer.final_flush(self.output_file, self.width, self.height, fps=self.fps)
                if success:
                    self.output_files.append(self.output_file)
            except Exception as e:
                self._log_message(f"Error during final flush: {e}")
        
        if self.writer is not None:
            try:
                self.output_files.extend(self.writer._output_files)
            except Exception as e:
                print(f"Error collecting output files: {e}")
        
        if self.csv_file:
            try:
                self.csv_file.close()
                self._log_message(f"Drift log saved: {self.csv_filename}")
            except Exception as e:
                print(f"Error closing drift log: {e}")
        
        if self.writer is not None:
            try:
                self.writer.close()
            except Exception as e:
                print(f"Error closing writer: {e}")
        
        try:
            if self.cam is not None:
                self._log_message("Disconnecting camera...")
                try:
                    self.cam.stop_acquisition()
                except Exception as e:
                    print(f"Error stopping acquisition: {e}")
                try:
                    self.cam.close_device()
                except Exception as e:
                    print(f"Error closing device: {e}")
                self.cam = None
                self.img = None
                self.camera_connected = False
                self._log_message("Camera disconnected")
        except Exception as e:
            self._log_message(f"Error disconnecting camera: {e}")
        
        if self.concat_on_quit and len(self.output_files) > 1:
            self._log_message(f"\n{'='*60}")
            self._log_message(f"Found {len(self.output_files)} video segments")
            self._log_message(f"{'='*60}")
            session_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            final_output = os.path.join(self.video_output_path, f"session_{session_time}_concat.mkv")
            success = self._concatenate_videos(self.output_files, final_output)
            if success:
                self._log_message(f"\n✓ All segments concatenated into: {final_output}")
            else:
                self._log_message(f"⚠ Concatenation failed - segments kept separately")
        
        self._log_message(f"\n{'=' * 60}\nFINAL REPORT\n{'=' * 60}")
        self._log_message(f"Frames read: {self.frames_read}  Stored: {self.frames_queued}  Dropped: {self.frames_dropped}")
        
        try:
            if sys.platform == 'win32':
                ctypes.windll.winmm.timeEndPeriod(1)
        except Exception as e:
            print(f"Error ending timer period: {e}")
        
        self._running = False
        QApplication.quit()

    def closeEvent(self, event):
        self.on_quit()
        event.accept()


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    def excepthook(exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        print("An unhandled exception was caught, preventing app crash.")

    sys.excepthook = excepthook

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TEMViewerApp()
    window.show()
    sys.exit(app.exec_())