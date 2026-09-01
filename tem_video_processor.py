#!/usr/bin/env python3
"""
TEM Video Processor
Professional video processing with UI and complete processing pipeline for OneView camera
"""

import os
import sys
import json
import time
import datetime
import subprocess
import io
import threading
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

import numpy as np
import cv2
from typing import Optional, List, Tuple, Dict, cast
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from dm4_converter import DM4ConverterDialog

# ============================================================
# FIXED STYLESHEET
# ============================================================

DARK_STYLESHEET = """
QMainWindow {
    background: #17181b;
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
    margin-top: 18px;
    padding-top: 12px;
    padding: 16px 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 3px 10px;
    color: #b6b7bc;
    font-weight: 600;
    font-size: 8.5pt;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: #2c2d33;
    border: 1px solid #42434a;
    border-radius: 4px;
}
QPushButton {
    background: #2a2b30;
    border: 1px solid #46474e;
    border-radius: 5px;
    padding: 7px 14px;
    color: #cfd0d4;
    font-weight: 500;
    font-size: 9pt;
    min-height: 26px;
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
QPushButton:checked {
    background: #33475c;
    border: 1px solid #4a7fb8;
    color: #eaf1f8;
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
QPushButton#danger {
    background: #6e3232;
    border: 1px solid #7c3a3a;
    color: #eccece;
}
QPushButton#danger:hover {
    background: #7c3838;
    border-color: #8c4242;
}
QPushButton#danger:pressed {
    background: #5c2a2a;
}
QPushButton#danger:disabled {
    background: #3a2a2a;
    border-color: #3a2a2a;
    color: #7a6060;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #1a1b1e;
    border: 1px solid #46474e;
    border-radius: 4px;
    padding: 5px 10px;
    color: #d8d9dc;
    font-size: 9pt;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #5b5c66;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #5b86ad;
    background: #1c1d21;
}
QComboBox {
    padding-right: 6px;
}
QComboBox::drop-down {
    border-left: 1px solid #46474e;
    width: 22px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #b6b7bc;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #26272c;
    border: 1px solid #46474e;
    border-radius: 4px;
    color: #d8d9dc;
    selection-background-color: #33475c;
    outline: none;
}
QSlider::groove:horizontal {
    height: 3px;
    background: #34353a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #5b86ad;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: none;
}
QSlider::handle:horizontal:hover {
    background: #6a97bc;
}
QCheckBox {
    spacing: 10px;
    padding: 4px 0;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    background: #1a1b1e;
    border: 1px solid #4a4b52;
    border-radius: 3px;
}
QCheckBox::indicator:checked {

    background: #3b6ea5;
    border-color: #5b86ad;
}
QCheckBox::indicator:hover {
    border-color: #6a97bc;
}
QRadioButton {
    spacing: 10px;
    padding: 4px 0;
}
QRadioButton::indicator {
    width: 17px;
    height: 17px;
    background: #1a1b1e;
    border: 1px solid #4a4b52;
    border-radius: 9px;
}
QRadioButton::indicator:checked {
    background: #3b6ea5;
    border-color: #5b86ad;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3a3b40;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #47484f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QWidget#toolbar_content {
    background: transparent;
}
QStatusBar {
    background: #1e1f23;
    border-top: 1px solid #2b2c30;
    padding: 4px 18px;
    font-size: 8pt;
    color: #8a8b90;
}
QLabel {
    color: #9a9ba2;
    font-size: 9pt;
}
QLabel#title {
    color: #cfd0d4;
    font-size: 13pt;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QLabel#frame_info {
    color: #9a9ba2;
    font-family: "Consolas", monospace;
    font-size: 9pt;
    font-weight: 500;
}
QLabel#status {
    font-size: 8.5pt;
    font-weight: 600;
    letter-spacing: 0.3px;
}
QListWidget {
    background: #1a1b1e;
    border: 1px solid #42434a;
    border-radius: 5px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px 12px;
    border-radius: 4px;
    color: #cfd0d4;
}
QListWidget::item:selected {
    background: #33475c;
    border: 1px solid #3d5872;
}
QListWidget::item:hover {
    background: #232428;
}
QProgressBar {
    background: #1a1b1e;
    border: 1px solid #2b2c30;
    border-radius: 2px;
    height: 4px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #3b6ea5;
    border-radius: 2px;
}
QMenuBar {
    background: #1e1f23;
    color: #cfd0d4;
    border-bottom: 1px solid #2b2c30;
}
QMenuBar::item:selected {
    background: #2a2b30;
}
QMenu {
    background: #232428;
    border: 1px solid #34353a;
    padding: 4px;
}
QMenu::item:selected {
    background: #33475c;
}
QToolTip {
    background: #26272c;
    color: #d8d9dc;
    border: 1px solid #46474e;
    border-radius: 5px;
    padding: 7px 12px;
    font-size: 8.5pt;
}
"""

# ============================================================
# LIGHT THEME STYLESHEET - mirrors DARK_STYLESHEET selector-for-selector
# ============================================================
LIGHT_STYLESHEET = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #eef2f9,
                                stop:0.5 #f4f7fb,
                                stop:1 #e8edf6);
}
QWidget {
    background: transparent;
    color: #2c3a56;
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 9pt;
}
QGroupBox {
    background: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(40, 90, 180, 0.12);
    border-radius: 12px;
    margin-top: 16px;
    padding-top: 12px;
    padding: 16px 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 10px;
    color: #2660c0;
    font-weight: 600;
    font-size: 8.5pt;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 4px;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255, 255, 255, 0.95),
                                stop:1 rgba(222, 232, 248, 0.95));
    color: #1a3a70;
    border: 1px solid rgba(40, 90, 180, 0.22);
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 500;
    font-size: 9pt;
    min-height: 32px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(220, 235, 255, 1.0),
                                stop:1 rgba(190, 215, 250, 1.0));
    border: 1px solid rgba(40, 100, 200, 0.5);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(190, 215, 250, 1.0),
                                stop:1 rgba(165, 195, 235, 1.0));
    border: 1px solid rgba(40, 100, 200, 0.3);
}
QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(80, 150, 255, 0.3),
                                stop:1 rgba(50, 120, 230, 0.35));
    border: 2px solid rgba(40, 100, 200, 0.6);
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2fa768,
                                stop:1 #1f8a52);
    border-color: #1f8a52;
    color: #ffffff;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3ec27c,
                                stop:1 #2aa062);
    border-color: #2aa062;
}
QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #d95a5a,
                                stop:1 #b83a3a);
    border-color: #b83a3a;
    color: #ffffff;
}
QPushButton#danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e57070,
                                stop:1 #c94a4a);
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(40, 90, 180, 0.2);
    border-radius: 6px;
    padding: 6px 12px;
    color: #1a2a45;
    font-size: 9pt;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: rgba(40, 100, 200, 0.55);
    background: rgba(255, 255, 255, 1.0);
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #2660c0;
    margin-right: 5px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid rgba(40, 90, 180, 0.15);
    border-radius: 6px;
    selection-background-color: rgba(40, 120, 230, 0.18);
}
QSlider::groove:horizontal {
    height: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(40, 100, 200, 0.18),
                                stop:1 rgba(40, 100, 200, 0.08));
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3a80e0,
                                stop:1 #2660c0);
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: none;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #5a9aff,
                                stop:1 #3a78d8);
}
QCheckBox {
    spacing: 10px;
    padding: 4px 0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid rgba(40, 90, 180, 0.3);
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    /* Solid filled square, same convention as the dark theme - no
       checkmark glyph, so this file has no external asset dependency. */
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3ec27c,
                                stop:1 #1f8a52);
    border-color: #1f8a52;
}
QCheckBox::indicator:hover {
    border-color: rgba(40, 100, 200, 0.5);
}
QRadioButton {
    spacing: 10px;
    padding: 4px 0;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid rgba(40, 90, 180, 0.3);
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3a80e0,
                                stop:1 #2660c0);
    border-color: #2660c0;
}
QScrollBar:vertical {
    background: rgba(40, 90, 180, 0.08);
    width: 3px;
    border-radius: 2px;
}
QScrollBar::handle:vertical {
    background: rgba(40, 100, 200, 0.3);
    border-radius: 2px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(40, 100, 200, 0.5);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QWidget#toolbar_content {
    background: transparent;
}
QStatusBar {
    background: rgba(255, 255, 255, 0.5);
    border-top: 1px solid rgba(40, 90, 180, 0.1);
    padding: 4px 18px;
    font-size: 8pt;
    color: #4a5878;
}
QLabel {
    color: #4a5878;
    font-size: 9pt;
}
QLabel#title {
    color: #2660c0;
    font-size: 14pt;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#frame_info {
    color: #2660c0;
    font-family: "Consolas", monospace;
    font-size: 9pt;
    font-weight: 500;
}
QLabel#status {
    font-size: 8.5pt;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QListWidget {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(40, 90, 180, 0.12);
    border-radius: 8px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px 12px;
    border-radius: 4px;
    color: #2c3a56;
}
QListWidget::item:selected {
    background: rgba(40, 120, 230, 0.16);
    border: 1px solid rgba(40, 100, 200, 0.25);
}
QListWidget::item:hover {
    background: rgba(40, 120, 230, 0.08);
}
QProgressBar {
    background: rgba(40, 90, 180, 0.1);
    border: none;
    border-radius: 2px;
    height: 2px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2660c0,
                                stop:0.5 #3a80e0,
                                stop:1 #2660c0);
    border-radius: 2px;
}
QMenuBar {
    background: rgba(255, 255, 255, 0.8);
    color: #2c3a56;
    border-bottom: 1px solid rgba(40, 90, 180, 0.1);
}
QMenuBar::item:selected {
    background: rgba(40, 120, 230, 0.12);
}
QMenu {
    background: #ffffff;
    border: 1px solid rgba(40, 90, 180, 0.15);
    padding: 4px;
}
QMenu::item:selected {
    background: rgba(40, 120, 230, 0.15);
}
QToolTip {
    background: rgba(255, 255, 255, 0.98);
    color: #1a2a45;
    border: 1px solid rgba(40, 90, 180, 0.25);
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 8.5pt;
}
"""

# Per-theme colors for the handful of widgets that set their own inline
# stylesheet (and so aren't reachable by the QSS above), plus the
# TimelineWidget's hand-painted canvas.
THEME_COLORS = {
    'dark': {
        'panel_bg': '#17181b',
        'header_bg': '#1e1f23',
        'header_border': '#2b2c30',
        'dim_text': '#8a8b90',
        'overlay_bg': 'rgba(23, 24, 27, 0.88)',
        'overlay_text': '#c8c9ce',
        'overlay_border': '#34353a',
        'toolbar_border': '#2b2c30',
        'toolbar_bg': '#1e1f23',
        'status_bg': '#26272b',
        'status_border': '#34353a',
        'timeline': {
            'bg': QColor(23, 24, 27), 'track': QColor(38, 39, 43), 'track_glow': QColor(59, 110, 165, 12),
            'selection': QColor(59, 110, 165, 30), 'selection_border': QColor(59, 110, 165, 60),
            'in_point': QColor(95, 150, 115), 'in_point_glow': QColor(95, 150, 115, 18),
            'out_point': QColor(181, 85, 90), 'out_point_glow': QColor(181, 85, 90, 18),
            'playhead': QColor(207, 208, 212), 'playhead_glow': QColor(207, 208, 212, 12),
            'text': QColor(122, 123, 128), 'text_highlight': QColor(180, 181, 186),
            'grid': QColor(52, 53, 58, 60),
        },
    },
    'light': {
        'panel_bg': '#f4f7fb',
        'header_bg': 'rgba(255, 255, 255, 0.85)',
        'header_border': 'rgba(40, 90, 180, 0.1)',
        'dim_text': '#5a6888',
        'overlay_bg': 'rgba(255, 255, 255, 0.85)',
        'overlay_text': '#1a3a70',
        'overlay_border': 'rgba(40, 90, 180, 0.3)',
        'toolbar_border': 'rgba(40, 90, 180, 0.1)',
        'toolbar_bg': 'rgba(255, 255, 255, 0.6)',
        'status_bg': 'rgba(40, 120, 230, 0.08)',
        'status_border': 'rgba(40, 90, 180, 0.08)',
        'timeline': {
            'bg': QColor(244, 247, 251), 'track': QColor(222, 232, 248), 'track_glow': QColor(40, 100, 200, 20),
            'selection': QColor(40, 120, 230, 30), 'selection_border': QColor(40, 120, 230, 70),
            'in_point': QColor(0, 160, 90), 'in_point_glow': QColor(0, 160, 90, 35),
            'out_point': QColor(210, 50, 50), 'out_point_glow': QColor(210, 50, 50, 35),
            'playhead': QColor(30, 40, 60), 'playhead_glow': QColor(30, 40, 60, 20),
            'text': QColor(90, 105, 135), 'text_highlight': QColor(30, 60, 110),
            'grid': QColor(40, 90, 180, 30),
        },
    },
}


# ============================================================
# DRIFT TRACKERS - COMPLETE (UNTOUCHED)
# ============================================================

class FrameToFrameTracker:
    """Tracks sample drift frame-to-frame via phase correlation on the four edge
    strips of the image, accumulating a running (dx, dy) correction offset."""

    def __init__(self, strip_width=40, margin=0):
        self.strip_width = strip_width
        # Distance the strip is inset from the true frame border. TEM
        # footage is frequently a circular illuminated field on a black
        # background (vignette), so a strip sampled right at pixel 0 can
        # be 100% black with zero texture to correlate on - margin lets
        # the sampled band start further inside the frame, past the
        # vignette, where real content actually exists.
        self.margin = margin
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
        print("Frame-to-frame tracker initialized")
        return True

    def _extract_strips(self, frame):
        h, w = frame.shape[:2]
        s = self.strip_width
        m = max(0, min(self.margin, min(h, w) // 2 - s))
        strips = {}
        top = frame[m:m+s, :]
        if top.size > 0:
            strips['top'] = self._normalize(top)
        bottom = frame[h-m-s:h-m, :]
        if bottom.size > 0:
            strips['bottom'] = self._normalize(bottom)
        left = frame[:, m:m+s]
        if left.size > 0:
            strips['left'] = self._normalize(left)
        right = frame[:, w-m-s:w-m]
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
            except cv2.error:
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
        m = max(0, min(self.margin, min(h, w) // 2 - s))
        cv2.rectangle(vis, (0, m), (w, m+s), color, 2)
        cv2.rectangle(vis, (0, h-m-s), (w, h-m), color, 2)
        cv2.rectangle(vis, (m, 0), (m+s, h), color, 2)
        cv2.rectangle(vis, (w-m-s, 0), (w-m, h), color, 2)
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
        print("ROI selection mode: Click and drag to select region")
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
            print(f"ROI too small ({w}x{h}), minimum is {self.min_size}x{self.min_size}")
            self.selecting = False
            self.selection_start = None
            self.selection_end = None
            return False

        if w > self.max_size or h > self.max_size:
            print(f"ROI too large ({w}x{h}), maximum is {self.max_size}x{self.max_size}")
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
            print(f"ROI too small after clamping ({w}x{h})")
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

        print(f"ROI locked: ({x1}, {y1}, {w}, {h}) | Template: {self.template.shape}")
        print(f"  Template center: ({self.template_center[0]:.1f}, {self.template_center[1]:.1f})")
        print(f"  Frame center: ({self.frame_center[0]:.1f}, {self.frame_center[1]:.1f})")
        print("ROI tracking ACTIVE")
        return True

    def compute_offset(self, frame):
        """Locates the locked template in frame and returns a damped correction shift.

        Args:
            frame: Current full-resolution frame to search.

        Returns:
            A (dx, dy, confidence) tuple. dx/dy are already the *correction*
            shift (i.e. the negated object displacement) - see
            `_compute_auto_drift_impl`'s sign-convention comment for how
            callers must apply this. confidence is the template match score
            in [0, 1]; below confidence_threshold, the last known (dx, dy)
            is returned unchanged.
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
            print(f"WARNING: Search region ({sw}x{sh}) smaller than template ({tw}x{th})")
            return self.last_dx, self.last_dy, 0.0

        if frame.dtype != np.uint8:
            frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        else:
            frame_u8 = frame

        search_region = frame_u8[sy1:sy2, sx1:sx2]

        try:
            result = cv2.matchTemplate(search_region, self.template, cv2.TM_CCOEFF_NORMED)
        except cv2.error as e:
            print(f"matchTemplate error: {e}")
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
        self.cumulative_dx = 0.0
        self.cumulative_dy = 0.0
        self.last_dx = 0.0
        self.last_dy = 0.0
        print("ROI tracker reset")

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


# ============================================================
# TEM PROCESSOR - COMPLETE (UNTOUCHED)
# ============================================================

class TEMProcessor:
    """Per-frame image processing helpers: drift correction, CLAHE/autocontrast
    (with caching), and fast gamma LUTs. Holds the cached state (LUTs, drift
    tracker, flat-field scratch buffers) between frames."""

    def __init__(self):
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.gamma_lut = None
        self.gamma_value = None
        self.duplicate_count = 0
        self.consecutive_dups = 0
        self.frame_count = 0
        self.last_drift_frame = 0
        self.drift_tracker = FrameToFrameTracker(strip_width=40)
        self.autocontrast_lut = None
        self.autocontrast_built = False
        self.ff_buffer = None
        self.ff_output = None

        self.autocontrast_build_interval = 5
        self.autocontrast_last_build_frame = 0
        self.autocontrast_last_mean = 0.0
        self.autocontrast_mean_threshold = 15.0
        self.autocontrast_low_pct = 1.0
        self.autocontrast_high_pct = 99.0
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

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
        return cv2.warpAffine(
            frame, M, (frame.shape[1], frame.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )

    def set_autocontrast_range(self, low_pct, high_pct):
        """Updates the autocontrast percentile clip range, invalidating the cached LUT if changed.

        Args:
            low_pct: Lower percentile (0-100) to clip to black.
            high_pct: Upper percentile (0-100) to clip to white.
        """
        if low_pct != self.autocontrast_low_pct or high_pct != self.autocontrast_high_pct:
            self.autocontrast_low_pct = low_pct
            self.autocontrast_high_pct = high_pct
            self.autocontrast_built = False

    def set_clahe_params(self, clip_limit, tile_size):
        """Updates the CLAHE clip limit and tile grid size.

        Args:
            clip_limit: Contrast clip limit passed to cv2's CLAHE.
            tile_size: Tile grid is (tile_size, tile_size).
        """
        self.clahe.setClipLimit(clip_limit)
        self.clahe.setTilesGridSize((tile_size, tile_size))

    def adaptive_autocontrast_cached(self, image):
        """Applies percentile-based autocontrast via a cached LUT.

        The LUT is rebuilt only when the cache is stale (interval elapsed or
        mean brightness shifted significantly), rather than every frame,
        since rebuilding it involves a percentile computation over the frame.

        Args:
            image: Grayscale input image.

        Returns:
            The contrast-stretched image.
        """
        current_mean = float(image.mean())
        frames_since_build = self.frame_count - self.autocontrast_last_build_frame
        mean_diff = abs(current_mean - self.autocontrast_last_mean)

        rebuild = (
            not self.autocontrast_built
            or frames_since_build >= self.autocontrast_build_interval
            or mean_diff >= self.autocontrast_mean_threshold
        )

        if rebuild:
            small = image
            low, high = np.percentile(small, [self.autocontrast_low_pct, self.autocontrast_high_pct])
            if high > low:
                self.autocontrast_lut = np.clip(
                    (np.arange(256, dtype=np.float32) - low) * 255.0 / (high - low),
                    0, 255
                ).astype(np.uint8)
            else:
                self.autocontrast_lut = np.arange(256, dtype=np.uint8)
            self.autocontrast_built = True
            self.autocontrast_last_build_frame = self.frame_count
            self.autocontrast_last_mean = current_mean

        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return cv2.LUT(image, self.autocontrast_lut)

    def apply_clahe(self, image):
        """Applies CLAHE (contrast-limited adaptive histogram equalization).

        Args:
            image: Grayscale input image.

        Returns:
            The equalized image.
        """
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return self.clahe.apply(image)

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


# ============================================================
# PROCESSING SEGMENT
# ============================================================

class ProcessingSegment:
    """A frame range with its own snapshot of processing settings, used by
    TEMVideoProcessor to apply different gamma/filter/contrast settings to
    different parts of a video on export."""

    def __init__(self, start_frame: int, end_frame: int, settings: Dict):
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.settings = settings.copy()
        self.enabled = True
        self.name = ""

    def contains(self, frame_num: int) -> bool:
        """Returns True if frame_num falls within [start_frame, end_frame]."""
        return self.start_frame <= frame_num <= self.end_frame


# ============================================================
# TIMELINE WIDGET
# ============================================================

class TimelineWidget(QWidget):
    """Custom-painted scrubber bar: shows the playhead, an optional IN/OUT
    selection range, and time markers, with mouse/wheel interaction to
    seek, drag the selection handles, or step frame-by-frame."""

    frame_changed = pyqtSignal(int)
    selection_changed = pyqtSignal(int, int)
    in_point_changed = pyqtSignal(int)
    out_point_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 25
        
        self.in_point = -1
        self.out_point = -1
        self.dragging = None
        
        self.colors = THEME_COLORS['dark']['timeline']

        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def set_theme(self, theme):
        """Switches the timeline's color palette ('dark' or 'light') and repaints."""
        self.colors = THEME_COLORS[theme]['timeline']
        self.update()

    def set_video_info(self, total_frames, fps):
        """Sets the total frame count and frame rate the timeline scales against."""
        self.total_frames = total_frames
        self.fps = fps
        self.update()

    def set_current_frame(self, frame):
        """Moves the playhead to frame (clamped to valid range) and emits frame_changed.

        Args:
            frame: Target frame index.
        """
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.update()
        self.frame_changed.emit(self.current_frame)

    def set_selection(self, in_point, out_point):
        """Sets the IN/OUT selection range, swapping the two if out of order.

        Args:
            in_point: Start frame, or a negative value to clear it.
            out_point: End frame, or a negative value to clear it.
        """
        self.in_point = in_point if in_point >= 0 else -1
        self.out_point = out_point if out_point >= 0 else -1
        if self.in_point >= 0 and self.out_point >= 0 and self.in_point > self.out_point:
            self.in_point, self.out_point = self.out_point, self.in_point
        self.update()
        self.selection_changed.emit(self.in_point, self.out_point)

    def clear_selection(self):
        """Clears the IN/OUT selection range."""
        self.in_point = -1
        self.out_point = -1
        self.update()
        self.selection_changed.emit(-1, -1)
        
    def _get_x_for_frame(self, frame):
        if self.total_frames <= 1:
            return 0
        width = self.width() - 60
        return 30 + int(frame / (self.total_frames - 1) * width)
        
    def _get_frame_for_x(self, x):
        if self.total_frames <= 1:
            return 0
        width = self.width() - 60
        if width <= 0:
            return 0
        return max(0, min(self.total_frames - 1, int((x - 30) / width * (self.total_frames - 1))))
        
    def paintEvent(self, event):
        """Custom-paints the track, grid, IN/OUT markers, and playhead."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        margin = 30
        track_y = height // 2 - 12
        track_h = 24
        
        # Background with subtle gradient
        painter.fillRect(self.rect(), self.colors['bg'])
        
        # Track with glow
        track_rect = QRect(margin, track_y, width - 2*margin, track_h)
        painter.fillRect(track_rect, self.colors['track'])
        
        # Track glow effect
        glow_rect = QRect(margin - 5, track_y - 5, width - 2*margin + 10, track_h + 10)
        painter.fillRect(glow_rect, self.colors['track_glow'])
        
        # Grid lines
        painter.setPen(QPen(self.colors['grid'], 1))
        step = max(1, self.total_frames // 20)
        for i in range(0, self.total_frames, step):
            x = self._get_x_for_frame(i)
            painter.drawLine(x, track_y, x, track_y + track_h)
        
        # Selection range
        if self.in_point >= 0 and self.out_point >= 0 and self.in_point <= self.out_point:
            x1 = self._get_x_for_frame(self.in_point)
            x2 = self._get_x_for_frame(self.out_point)
            sel_rect = QRect(x1, track_y, x2 - x1, track_h)
            painter.fillRect(sel_rect, self.colors['selection'])
            painter.setPen(QPen(self.colors['selection_border'], 1))
            painter.drawRect(sel_rect)
        
        # Time markers
        painter.setPen(QPen(self.colors['text'], 1))
        painter.setFont(QFont("Segoe UI", 7))
        for i in range(0, self.total_frames, step):
            x = self._get_x_for_frame(i)
            painter.drawLine(x, track_y + track_h, x, track_y + track_h + 6)
            if i % (step * 5) == 0 or i == 0 or i == self.total_frames - 1:
                time_sec = i / self.fps if self.fps > 0 else 0
                painter.drawText(x - 15, track_y + track_h + 20, f"{time_sec:.1f}s")
        
        # IN point with glow
        if self.in_point >= 0:
            x = self._get_x_for_frame(self.in_point)
            glow = QRadialGradient(x, track_y + track_h/2, 20)
            glow.setColorAt(0, self.colors['in_point_glow'])
            glow.setColorAt(1, Qt.transparent)
            painter.fillRect(x - 20, track_y - 10, 40, track_h + 20, glow)
            painter.setPen(QPen(self.colors['in_point'], 2))
            painter.drawLine(x, track_y - 6, x, track_y + track_h + 6)
            painter.setBrush(self.colors['in_point'])
            painter.setPen(Qt.NoPen)
            points = [QPoint(x - 6, track_y - 2), QPoint(x + 6, track_y - 2), QPoint(x, track_y - 9)]
            painter.drawPolygon(points)
            painter.setPen(self.colors['in_point'])
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.drawText(x - 10, track_y - 14, "I")
        
        # OUT point with glow
        if self.out_point >= 0:
            x = self._get_x_for_frame(self.out_point)
            glow = QRadialGradient(x, track_y + track_h/2, 20)
            glow.setColorAt(0, self.colors['out_point_glow'])
            glow.setColorAt(1, Qt.transparent)
            painter.fillRect(x - 20, track_y - 10, 40, track_h + 20, glow)
            painter.setPen(QPen(self.colors['out_point'], 2))
            painter.drawLine(x, track_y - 6, x, track_y + track_h + 6)
            painter.setBrush(self.colors['out_point'])
            painter.setPen(Qt.NoPen)
            points = [QPoint(x - 6, track_y + track_h + 2), QPoint(x + 6, track_y + track_h + 2), QPoint(x, track_y + track_h + 9)]
            painter.drawPolygon(points)
            painter.setPen(self.colors['out_point'])
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.drawText(x - 12, track_y + track_h + 22, "O")
        
        # Playhead with glow
        x = self._get_x_for_frame(self.current_frame)
        glow = QRadialGradient(x, track_y + track_h/2, 25)
        glow.setColorAt(0, self.colors['playhead_glow'])
        glow.setColorAt(1, Qt.transparent)
        painter.fillRect(x - 25, track_y - 15, 50, track_h + 30, glow)
        painter.setPen(QPen(self.colors['playhead'], 2))
        painter.drawLine(x, track_y - 10, x, track_y + track_h + 10)
        painter.setBrush(self.colors['playhead'])
        painter.setPen(QPen(self.colors['playhead'], 1))
        painter.drawEllipse(x - 4, track_y - 7, 8, 8)
        
        # Info text
        painter.setPen(self.colors['text'])
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(10, 20, f"FRAME {self.current_frame}/{self.total_frames}")
        
        if self.in_point >= 0 and self.out_point >= 0:
            duration = self.out_point - self.in_point + 1
            duration_sec = duration / self.fps if self.fps > 0 else 0
            info = f"SELECTION {self.in_point} → {self.out_point}  |  {duration} FRAMES  |  {duration_sec:.1f}S"
            painter.setPen(self.colors['text_highlight'])
        else:
            info = "RIGHT-CLICK: SET IN  |  DRAG: SELECT  |  SCROLL: STEP"
        painter.drawText(10, height - 8, info)
        
    def mousePressEvent(self, event):
        """Right-click sets the IN point; left-click starts dragging whichever
        handle (IN, OUT, or playhead) is nearest the click."""
        x = event.x()
        frame = self._get_frame_for_x(x)

        in_x = self._get_x_for_frame(self.in_point) if self.in_point >= 0 else -1
        out_x = self._get_x_for_frame(self.out_point) if self.out_point >= 0 else -1
        
        if event.button() == Qt.RightButton:
            self.in_point = frame
            if self.out_point >= 0 and self.in_point > self.out_point:
                self.in_point, self.out_point = self.out_point, self.in_point
            self.update()
            self.in_point_changed.emit(self.in_point)
            self.selection_changed.emit(self.in_point, self.out_point)
            
        elif event.button() == Qt.LeftButton:
            if self.in_point >= 0 and abs(x - in_x) < 12:
                self.dragging = 'in'
            elif self.out_point >= 0 and abs(x - out_x) < 12:
                self.dragging = 'out'
            else:
                self.dragging = 'playhead'
                self.set_current_frame(frame)
                
    def mouseMoveEvent(self, event):
        """Updates whichever handle is being dragged, and swaps the cursor to a
        resize icon when hovering an IN/OUT handle."""
        x = event.x()
        frame = self._get_frame_for_x(x)

        if self.dragging == 'in':
            self.in_point = frame
            if self.out_point >= 0 and self.in_point > self.out_point:
                self.in_point, self.out_point = self.out_point, self.in_point
            self.update()
            self.in_point_changed.emit(self.in_point)
            self.selection_changed.emit(self.in_point, self.out_point)
            
        elif self.dragging == 'out':
            self.out_point = frame
            if self.in_point >= 0 and self.in_point > self.out_point:
                self.in_point, self.out_point = self.out_point, self.in_point
            self.update()
            self.out_point_changed.emit(self.out_point)
            self.selection_changed.emit(self.in_point, self.out_point)
            
        elif self.dragging == 'playhead':
            self.set_current_frame(frame)
            
        in_x = self._get_x_for_frame(self.in_point) if self.in_point >= 0 else -1
        out_x = self._get_x_for_frame(self.out_point) if self.out_point >= 0 else -1
        
        if (self.in_point >= 0 and abs(x - in_x) < 12) or (self.out_point >= 0 and abs(x - out_x) < 12):
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.PointingHandCursor)
            
    def mouseReleaseEvent(self, event):
        """Ends the current drag, emitting a final changed signal for the handle that moved."""
        if self.dragging == 'in':
            self.in_point_changed.emit(self.in_point)
        elif self.dragging == 'out':
            self.out_point_changed.emit(self.out_point)
        self.dragging = None

    def wheelEvent(self, event):
        """Steps the playhead one frame per wheel notch."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.set_current_frame(self.current_frame - 1)
        else:
            self.set_current_frame(self.current_frame + 1)


# ============================================================
# MAIN APPLICATION - Futuristic UI
# ============================================================

class TEMVideoProcessor(QMainWindow):
    """Main window: loads a video (or DM4-converted one), plays/scrubs it, applies
    the processing pipeline (flat-field, drift correction, contrast, filters) live
    for preview, supports per-segment settings, and exports the result via ffmpeg."""

    # The handful of status colors used across the app (dim/info/warning/
    # error/success) are passed as literal hex "IDs" from ~30 call sites
    # throughout this file. Both theme's actual rendered colors are looked
    # up from these two tables, so no individual call site needs to know
    # about theming - and the dark palette can be desaturated to match the
    # rest of the restrained UI without touching any of those call sites.
    _STATUS_COLOR_DARK_REMAP = {
        '#4a6080': '#8a8b90',
        '#60b0ff': '#5b8ab8',
        '#ffa500': '#b8863f',
        '#ff5050': '#b5555a',
        '#2a9a5a': '#5a946e',
    }
    _STATUS_COLOR_LIGHT_REMAP = {
        '#4a6080': '#5a6888',
        '#60b0ff': '#2660c0',
        '#ffa500': '#c97a00',
        '#ff5050': '#d43a3a',
        '#2a9a5a': '#1f8a52',
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEM Video Processor")
        self.setGeometry(50, 50, 1500, 850)
        self.setWindowIcon(QIcon())

        # Video source
        self.vidcap = None
        self.video_path = None
        self.dm4_metadata = None
        self.fps = 25
        self.source_fps = 25
        self.source_frames = 0
        self.width = 1024
        self.height = 1024
        self.current_frame = 0
        self.video_loaded = False
        self._video_error = False
        self._loading_video = False
        self._frame_read_retries = 0
        self._last_read_ok = False
        self._last_drift_dx = 0.0
        self._last_drift_dy = 0.0
        self._drift_cache_frame = None
        self._drift_cache_method = None
        
        # Thread-safe frame storage
        self._frame_lock = threading.Lock()
        self._current_frame = None
        self._raw_gray_frame = None
        self._is_playing = False

        # Guards against playback restarting (via button, Space key, or the
        # playback timer) while an export is reading frames from the same
        # self.vidcap - see _export_video/_set_export_controls_enabled.
        self._exporting = False

        # Display mapping (label pixel <-> frame pixel), updated by _update_display
        self._display_scale = 1.0
        self._display_offset = (0, 0)

        # Flat field: D (dark reference) and G (gain map) stay None until the
        # user loads them via LOAD FLAT FIELD - correction is simply skipped
        # (see _process_frame's flat-field branch) while they're unset.
        self.D = None
        self.G = None
        self._flatfield_dark_name = None
        self._flatfield_ref_name = None

        # Processing objects
        self.processor = TEMProcessor()
        self.roi_tracker = ROITracker(min_size=32, max_size=512)
        self.tracker_initialized = False
        self._running = True
        self.enable_screenshot = False
        self.drift_interval = 1
        self._prev_drift_choice = 0
        self.gamma_value = 0.65

        # Counters
        self.frames_read = 0
        self.frames_queued = 0
        self.frames_dropped = 0
        self.frames_duplicate = 0
        self.frame_times = []
        self.last_frame_time = time.time()
        self.actual_fps = 0.0
        self.timing_stats = {k: [] for k in
                              ['read', 'grayscale', 'drift_detect', 'drift_correct', 'flatfield',
                               'autocontrast', 'gamma', 'blur', 'write', 'total']}

        self.csv_file = None
        self.csv_filename = None

        # Filter parameters
        self.gaussian_kernel = 3
        self.gaussian_sigma = 1.0
        self.median_kernel = 3
        self.bilateral_d = 9
        self.bilateral_sigmaColor = 75
        self.bilateral_sigmaSpace = 75
        
        # Segments
        self.segments: List[ProcessingSegment] = []

        # Histogram
        self.histogram_window = None
        self.hist_figure = None
        self.hist_ax = None
        self.hist_canvas = None

        # Theme - status text is tracked separately from its rendered
        # color so switching themes can re-render correctly
        self._theme = 'dark'
        self._status_text, self._status_color = "IDLE", "#4a6080"
        self._drift_status_text, self._drift_status_color = "○ INACTIVE", "#4a6080"

        # Playback timer - default interval until a video is loaded, at
        # which point it's set to match the source video's own fps
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._playback_step)
        self.playback_timer.setInterval(40)  # 40ms = 25fps default

        # FPS update timer
        self.fps_update_timer = QTimer()
        self.fps_update_timer.timeout.connect(self._update_fps_display)
        self.fps_update_timer.start(500)

        # Build UI
        self._build_layout()
        self._apply_theme('dark')

        # Start histogram update timer
        self.histogram_timer = QTimer()
        self.histogram_timer.timeout.connect(self._update_histogram)
        self.histogram_timer.start(100)

    # ------------------------------------------------------------
    # FLAT FIELD LOADING
    # ------------------------------------------------------------
    def _browse_flat_field(self):

        dark_path, _ = QFileDialog.getOpenFileName(
            self, "Load Dark Reference Image", "",
            "Images (*.png *.tif *.tiff *.bmp);;All Files (*.*)"
        )
        if not dark_path:
            return

        ref_path, _ = QFileDialog.getOpenFileName(
            self, "Load Gain/Reference Image", "",
            "Images (*.png *.tif *.tiff *.bmp);;All Files (*.*)"
        )
        if not ref_path:
            return

        try:
            D = cv2.imread(dark_path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_GRAYSCALE)
            F = cv2.imread(ref_path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_GRAYSCALE)
            if D is None or F is None:
                raise ValueError("could not decode one of the selected images")
            if D.shape != F.shape:
                raise ValueError(
                    f"dark reference is {D.shape[1]}x{D.shape[0]} but gain "
                    f"reference is {F.shape[1]}x{F.shape[0]} - they must match"
                )
            resized_note = ""
            target_w, target_h = cast(int, self.width), cast(int, self.height)
            if self.video_loaded and D.shape != (target_h, target_w):
                orig_w, orig_h = D.shape[1], D.shape[0]
                # INTER_AREA when shrinking (block-averages, correct for
                # sensor binning), INTER_LINEAR when enlarging.
                shrinking = target_w <= orig_w and target_h <= orig_h
                interp = cv2.INTER_AREA if shrinking else cv2.INTER_LINEAR
                D = cv2.resize(D, (target_w, target_h), interpolation=interp)
                F = cv2.resize(F, (target_w, target_h), interpolation=interp)
                resized_note = f" (resized from {orig_w}x{orig_h} to {target_w}x{target_h})"
            D = D.astype(np.float32)
            F = F.astype(np.float32)
            if F.max() > 255:
                F = F * 255.0 / F.max()
            FD = F - D
            mean_FD = np.mean(FD)
            # Per-pixel gain = (mean of F-D) / (that pixel's F-D), i.e. how
            # much a pixel needs to be scaled to match the average response.
            # Clamped to [0.5, 2.0] so a near-zero denominator (a dead or
            # saturated pixel) can't produce an extreme multiplier.
            G = np.clip(np.where(FD > 0, mean_FD / (FD + 1e-6), 1.0).astype(np.float32), 0.5, 2.0)
        except Exception as e:
            QMessageBox.critical(self, "Flat Field", f"Could not load flat-field images:\n{e}")
            return

        self.D = D
        self.G = G
        self._flatfield_dark_name = os.path.basename(dark_path)
        self._flatfield_ref_name = os.path.basename(ref_path)
        self.ff_status_label.setText(
            f"Flat field: {self._flatfield_dark_name} + {self._flatfield_ref_name}{resized_note}"
        )
        self.ff_status_label.setToolTip(f"Dark: {dark_path}\nReference: {ref_path}")

    # ------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------
    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left: Video display area
        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_panel")
        left = self.left_panel
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Header
        self._build_header(left_layout)
        
        # Video display
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.mousePressEvent = self._on_image_mouse_press
        self.image_label.mouseMoveEvent = self._on_image_mouse_move
        self.image_label.mouseReleaseEvent = self._on_image_mouse_release
        left_layout.addWidget(self.image_label)

        # DM4 metadata overlay - a small HUD in the corner of the video,
        # populated when the opened video has a metadata sidecar (written
        # by dm4_converter.py during DM4->video conversion).
        self.metadata_overlay = QLabel(self.image_label)
        self.metadata_overlay.setObjectName("metadata_overlay")
        self.metadata_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.metadata_overlay.move(10, 10)
        self.metadata_overlay.hide()
        
        # Timeline
        self.timeline = TimelineWidget()
        self.timeline.frame_changed.connect(self._on_timeline_frame_changed)
        self.timeline.selection_changed.connect(self._on_selection_changed)
        self.timeline.in_point_changed.connect(self._on_in_point_changed)
        self.timeline.out_point_changed.connect(self._on_out_point_changed)
        left_layout.addWidget(self.timeline)
        
        # Controls
        self._build_controls(left_layout)

        main_layout.addWidget(left, 2)

        # Right: Toolbar
        self._build_toolbar()
        main_layout.addWidget(self.toolbar_container, 1)

    def _build_header(self, layout):
        self.header_widget = QWidget()
        self.header_widget.setObjectName("header_widget")
        self.header_widget.setFixedHeight(50)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("TEM VIDEO PROCESSOR")
        title.setObjectName("title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.file_label = QLabel("NO VIDEO LOADED")
        self.file_label.setObjectName("file_label")
        header_layout.addWidget(self.file_label)

        self.frame_info_label = QLabel("")
        self.frame_info_label.setObjectName("frame_info")
        header_layout.addWidget(self.frame_info_label)

        header_layout.addStretch()

        self.status_label = QLabel("IDLE")
        self.status_label.setObjectName("status")
        header_layout.addWidget(self.status_label)

        self.fps_display = QLabel("0 FPS")
        self.fps_display.setObjectName("fps_display")
        header_layout.addWidget(self.fps_display)

        layout.addWidget(self.header_widget)

    def _build_controls(self, layout):
        self.controls_widget = QWidget()
        self.controls_widget.setObjectName("controls_widget")
        controls = self.controls_widget
        controls.setFixedHeight(50)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(20, 5, 20, 5)
        controls_layout.setSpacing(8)

        self.play_btn = QPushButton("PLAY")
        self.play_btn.setToolTip("Play/pause the video (Space)")
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setMinimumWidth(90)
        controls_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setToolTip("Pause and jump back to frame 0")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setMinimumWidth(80)
        controls_layout.addWidget(self.stop_btn)

        controls_layout.addSpacing(15)

        self.in_btn = QPushButton("IN")
        self.in_btn.setToolTip("Mark the current frame as the selection's start")
        self.in_btn.clicked.connect(self._set_in_point)
        self.in_btn.setMinimumWidth(70)
        controls_layout.addWidget(self.in_btn)

        self.out_btn = QPushButton("OUT")
        self.out_btn.setToolTip("Mark the current frame as the selection's end")
        self.out_btn.clicked.connect(self._set_out_point)
        self.out_btn.setMinimumWidth(70)
        controls_layout.addWidget(self.out_btn)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setToolTip("Clear the IN/OUT selection")
        self.clear_btn.clicked.connect(self._clear_selection)
        self.clear_btn.setMinimumWidth(80)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addSpacing(15)

        self.add_segment_btn = QPushButton("ADD SEGMENT")
        self.add_segment_btn.setToolTip(
            "Save the current IN/OUT range with the current processing settings\n"
            "as a segment - each segment can have its own gamma/filter/contrast."
        )
        self.add_segment_btn.clicked.connect(self._add_segment)
        self.add_segment_btn.setMinimumWidth(130)
        controls_layout.addWidget(self.add_segment_btn)

        controls_layout.addStretch()

        self.export_btn = QPushButton("EXPORT")
        self.export_btn.setObjectName("primary")
        self.export_btn.setToolTip("Render segments (or the full video) to a file with current processing settings baked in.")
        self.export_btn.clicked.connect(self._export_video)
        self.export_btn.setMinimumWidth(100)
        controls_layout.addWidget(self.export_btn)

        layout.addWidget(controls)

    def _build_toolbar(self):
        self.toolbar_container = QWidget()
        self.toolbar_container.setObjectName("toolbar_container")
        self.toolbar_container.setMaximumWidth(400)
        self.toolbar_container.setMinimumWidth(360)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content.setObjectName("toolbar_content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # --- FILE ---
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("THEME"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["DARK", "LIGHT"])
        self.theme_combo.setToolTip("Switch the interface between dark and light color themes.")
        self.theme_combo.currentIndexChanged.connect(
            lambda i: self._apply_theme('light' if i == 1 else 'dark')
        )
        theme_row.addWidget(self.theme_combo)
        file_layout.addLayout(theme_row)

        open_btn = QPushButton("OPEN VIDEO")
        open_btn.clicked.connect(self._open_video)
        file_layout.addWidget(open_btn)

        self.fullscreen_cb = QCheckBox("FULLSCREEN")
        self.fullscreen_cb.stateChanged.connect(lambda s: self._set_fullscreen(s == Qt.Checked))
        file_layout.addWidget(self.fullscreen_cb)

        self.metadata_overlay_cb = QCheckBox("SHOW METADATA OVERLAY")
        self.metadata_overlay_cb.setChecked(True)
        self.metadata_overlay_cb.setEnabled(False)
        self.metadata_overlay_cb.setToolTip(
            "Pixel size, field of view, voltage, magnification etc., read from the\n"
            "DM4 file's metadata at conversion time. Only available for videos\n"
            "converted from DM4 in this app - not plain opened video files."
        )
        self.metadata_overlay_cb.stateChanged.connect(self._update_metadata_overlay)
        file_layout.addWidget(self.metadata_overlay_cb)

        layout.addWidget(file_group)

        # --- PROCESSING ---
        proc_group = QGroupBox("Processing")
        proc_layout = QVBoxLayout(proc_group)

        # Gamma
        gamma_row = QHBoxLayout()
        gamma_row.addWidget(QLabel("GAMMA"))
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(10, 300)
        self.gamma_slider.setValue(65)
        self.gamma_slider.valueChanged.connect(self._on_gamma_slider_changed)
        gamma_row.addWidget(self.gamma_slider)
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.10, 3.00)
        self.gamma_spin.setSingleStep(0.01)
        self.gamma_spin.setDecimals(2)
        self.gamma_spin.setValue(0.65)
        self.gamma_spin.setFixedWidth(72)
        self.gamma_spin.setToolTip("Type an exact gamma value.")
        self.gamma_spin.valueChanged.connect(self._on_gamma_spin_changed)
        gamma_row.addWidget(self.gamma_spin)
        proc_layout.addLayout(gamma_row)

        # Contrast
        contrast_row = QHBoxLayout()
        contrast_row.addWidget(QLabel("CONTRAST"))
        self.contrast_combo = QComboBox()
        self.contrast_combo.addItems(["AUTOCONTRAST", "CLAHE"])
        self.contrast_combo.setCurrentIndex(0)
        self.contrast_combo.currentIndexChanged.connect(self._on_contrast_changed)
        contrast_row.addWidget(self.contrast_combo)
        proc_layout.addLayout(contrast_row)

        # Contrast parameters
        self.contrast_params = QWidget()
        cp_layout = QVBoxLayout(self.contrast_params)
        cp_layout.setContentsMargins(10, 0, 0, 0)

        # Autocontrast percentile clipping
        self.autocontrast_widget = QWidget()
        ac_layout = QHBoxLayout(self.autocontrast_widget)
        ac_layout.addWidget(QLabel("LOW%:"))
        self.ac_low_spin = QDoubleSpinBox()
        self.ac_low_spin.setRange(0.0, 25.0)
        self.ac_low_spin.setSingleStep(0.5)
        self.ac_low_spin.setValue(1.0)
        self.ac_low_spin.valueChanged.connect(self._on_settings_changed)
        ac_layout.addWidget(self.ac_low_spin)
        ac_layout.addWidget(QLabel("HIGH%:"))
        self.ac_high_spin = QDoubleSpinBox()
        self.ac_high_spin.setRange(75.0, 100.0)
        self.ac_high_spin.setSingleStep(0.5)
        self.ac_high_spin.setValue(99.0)
        self.ac_high_spin.valueChanged.connect(self._on_settings_changed)
        ac_layout.addWidget(self.ac_high_spin)
        cp_layout.addWidget(self.autocontrast_widget)

        # CLAHE clip limit / tile size
        self.clahe_widget = QWidget()
        cl_layout = QHBoxLayout(self.clahe_widget)
        cl_layout.addWidget(QLabel("CLIP:"))
        self.clahe_clip_spin = QDoubleSpinBox()
        self.clahe_clip_spin.setRange(0.5, 40.0)
        self.clahe_clip_spin.setSingleStep(0.5)
        self.clahe_clip_spin.setValue(2.0)
        self.clahe_clip_spin.valueChanged.connect(self._on_settings_changed)
        cl_layout.addWidget(self.clahe_clip_spin)
        cl_layout.addWidget(QLabel("TILE:"))
        self.clahe_tile_spin = QSpinBox()
        self.clahe_tile_spin.setRange(2, 32)
        self.clahe_tile_spin.setValue(8)
        self.clahe_tile_spin.valueChanged.connect(self._on_settings_changed)
        cl_layout.addWidget(self.clahe_tile_spin)
        cp_layout.addWidget(self.clahe_widget)

        self._update_contrast_visibility(0)
        proc_layout.addWidget(self.contrast_params)

        # Filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("FILTER"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["NONE", "GAUSSIAN", "MEDIAN", "BILATERAL"])
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.filter_combo)
        proc_layout.addLayout(filter_row)

        # Filter parameters
        self.filter_params = QWidget()
        fp_layout = QVBoxLayout(self.filter_params)
        fp_layout.setContentsMargins(10, 0, 0, 0)

        # Gaussian
        self.gaussian_widget = QWidget()
        gw_layout = QHBoxLayout(self.gaussian_widget)
        gw_layout.addWidget(QLabel("K:"))
        self.gk_spin = QSpinBox()
        self.gk_spin.setRange(1, 15)
        self.gk_spin.setSingleStep(2)
        self.gk_spin.setValue(3)
        self.gk_spin.valueChanged.connect(self._on_settings_changed)
        gw_layout.addWidget(self.gk_spin)
        gw_layout.addWidget(QLabel("S:"))
        self.gs_spin = QDoubleSpinBox()
        self.gs_spin.setRange(0.1, 10.0)
        self.gs_spin.setSingleStep(0.1)
        self.gs_spin.setValue(1.0)
        self.gs_spin.valueChanged.connect(self._on_settings_changed)
        gw_layout.addWidget(self.gs_spin)
        fp_layout.addWidget(self.gaussian_widget)

        # Median
        self.median_widget = QWidget()
        mw_layout = QHBoxLayout(self.median_widget)
        mw_layout.addWidget(QLabel("K:"))
        self.mk_spin = QSpinBox()
        self.mk_spin.setRange(1, 15)
        self.mk_spin.setSingleStep(2)
        self.mk_spin.setValue(3)
        self.mk_spin.valueChanged.connect(self._on_settings_changed)
        mw_layout.addWidget(self.mk_spin)
        fp_layout.addWidget(self.median_widget)

        # Bilateral
        self.bilateral_widget = QWidget()
        bw_layout = QHBoxLayout(self.bilateral_widget)
        bw_layout.addWidget(QLabel("D:"))
        self.bd_spin = QSpinBox()
        self.bd_spin.setRange(1, 15)
        self.bd_spin.setValue(9)
        self.bd_spin.valueChanged.connect(self._on_settings_changed)
        bw_layout.addWidget(self.bd_spin)
        bw_layout.addWidget(QLabel("SC:"))
        self.bsc_spin = QDoubleSpinBox()
        self.bsc_spin.setRange(1, 200)
        self.bsc_spin.setValue(75)
        self.bsc_spin.valueChanged.connect(self._on_settings_changed)
        bw_layout.addWidget(self.bsc_spin)
        bw_layout.addWidget(QLabel("SS:"))
        self.bss_spin = QDoubleSpinBox()
        self.bss_spin.setRange(1, 200)
        self.bss_spin.setValue(75)
        self.bss_spin.valueChanged.connect(self._on_settings_changed)
        bw_layout.addWidget(self.bss_spin)
        fp_layout.addWidget(self.bilateral_widget)

        self._update_filter_visibility(0)
        proc_layout.addWidget(self.filter_params)

        ff_row = QHBoxLayout()
        self.ff_cb = QCheckBox("FLAT FIELD CORRECTION")
        self.ff_cb.setToolTip("Subtract a dark reference and apply a gain map (see LOAD FLAT FIELD).")
        self.ff_cb.stateChanged.connect(self._on_settings_changed)
        ff_row.addWidget(self.ff_cb)

        self.ff_load_btn = QPushButton("LOAD FLAT FIELD")
        self.ff_load_btn.setToolTip("Pick a dark-reference image, then a gain/reference image, to compute the flat-field correction.")
        self.ff_load_btn.clicked.connect(self._browse_flat_field)
        ff_row.addWidget(self.ff_load_btn)
        proc_layout.addLayout(ff_row)

        self.ff_status_label = QLabel("Flat field: not loaded")
        self.ff_status_label.setStyleSheet("color: #8a8b90; font-size: 8pt;")
        proc_layout.addWidget(self.ff_status_label)

        layout.addWidget(proc_group)

        # --- DRIFT CORRECTION ---
        self._build_drift_group(layout)

        # --- SEGMENTS ---
        seg_group = QGroupBox("Segments")
        seg_layout = QVBoxLayout(seg_group)

        self.segments_list = QListWidget()
        self.segments_list.itemClicked.connect(self._on_segment_selected)
        self.segments_list.setMinimumHeight(80)
        seg_layout.addWidget(self.segments_list)

        seg_btn_layout = QHBoxLayout()
        self.del_seg_btn = QPushButton("DELETE")
        self.del_seg_btn.setObjectName("danger")
        self.del_seg_btn.clicked.connect(self._delete_segment)
        self.del_seg_btn.setEnabled(False)
        seg_btn_layout.addWidget(self.del_seg_btn)

        self.clear_seg_btn = QPushButton("CLEAR ALL")
        self.clear_seg_btn.clicked.connect(self._clear_segments)
        seg_btn_layout.addWidget(self.clear_seg_btn)

        seg_layout.addLayout(seg_btn_layout)

        layout.addWidget(seg_group)

        # --- TOOLS ---
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)

        hist_btn = QPushButton("HISTOGRAM")
        hist_btn.clicked.connect(self._open_histogram_window)
        tools_layout.addWidget(hist_btn)

        screenshot_btn = QPushButton("SCREENSHOT")
        screenshot_btn.clicked.connect(self._on_screenshot)
        tools_layout.addWidget(screenshot_btn)

        reset_btn = QPushButton("RESET SETTINGS")
        reset_btn.clicked.connect(self._reset_settings)
        tools_layout.addWidget(reset_btn)

        layout.addWidget(tools_group)

        layout.addStretch()

        quit_btn = QPushButton("QUIT")
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)

        scroll.setWidget(content)
        container = QVBoxLayout(self.toolbar_container)
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(scroll)

    def _themed_status_color(self, color):
        if self._theme == 'light':
            return self._STATUS_COLOR_LIGHT_REMAP.get(color, color)
        return self._STATUS_COLOR_DARK_REMAP.get(color, color)

    def _apply_theme(self, theme):
        self._theme = theme
        t = THEME_COLORS[theme]
        base = LIGHT_STYLESHEET if theme == 'light' else DARK_STYLESHEET
        extra = f"""
QWidget#header_widget {{
    border-bottom: 1px solid {t['header_border']};
    background: {t['header_bg']};
}}
QWidget#controls_widget {{
    border-top: 1px solid {t['header_border']};
    background: {t['toolbar_bg']};
}}
QWidget#left_panel, QLabel#image_label {{
    background: {t['panel_bg']};
}}
QWidget#toolbar_container {{
    border-left: 1px solid {t['toolbar_border']};
    background: {t['toolbar_bg']};
}}
QLabel#metadata_overlay {{
    background: {t['overlay_bg']};
    color: {t['overlay_text']};
    border: 1px solid {t['overlay_border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-family: "Consolas", monospace;
    font-size: 8pt;
}}
QLabel#file_label {{
    color: {t['dim_text']};
    font-size: 8pt;
    letter-spacing: 0.5px;
}}
QLabel#fps_display {{
    color: {t['dim_text']};
    font-size: 8pt;
    font-weight: 500;
    letter-spacing: 0.5px;
}}
"""
        self.setStyleSheet(base + extra)

        for gb in self.findChildren(QGroupBox):
            gb.style().unpolish(gb)
            gb.style().polish(gb)

        self.timeline.set_theme(theme)

        self._update_status(self._status_text, self._status_color)
        self._set_drift_status(self._drift_status_text, self._drift_status_color)

        if self.histogram_window is not None:
            self.histogram_window.setStyleSheet(LIGHT_STYLESHEET if theme == 'light' else DARK_STYLESHEET)

    def _build_drift_group(self, layout):
        drift_group = QGroupBox("Drift Correction")
        drift_layout = QVBoxLayout(drift_group)

        # a plain-language readout of what's actually happening right now.
        self.drift_status_label = QLabel("○ INACTIVE")
        self.drift_status_label.setStyleSheet("color: #4a6080; font-weight: 600; font-size: 8.5pt;")
        drift_layout.addWidget(self.drift_status_label)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("METHOD"))
        self.drift_combo = QComboBox()
        self.drift_combo.addItems(["NONE (MANUAL)", "EDGE-STRIP (AUTO)", "ROI (AUTO)"])
        self.drift_combo.setCurrentIndex(0)
        self.drift_combo.setToolTip(
            "NONE: dial in a fixed X/Y offset by hand.\n"
            "EDGE-STRIP: auto-tracks drift using texture at the frame's edges.\n"
            "  Needs playback (not scrubbing) and picture content reaching\n"
            "  near the border - a black vignette there will defeat it.\n"
            "ROI: auto-tracks a region you draw on the video. Works anywhere\n"
            "  in frame, including footage with a vignetted/circular border."
        )
        self.drift_combo.currentIndexChanged.connect(self._on_drift_method_changed)
        method_row.addWidget(self.drift_combo)
        drift_layout.addLayout(method_row)

        # --- NONE: manual offset ---
        self.manual_drift_widget = QWidget()
        manual_row = QHBoxLayout(self.manual_drift_widget)
        manual_row.setContentsMargins(0, 0, 0, 0)
        manual_row.addWidget(QLabel("X:"))
        self.drift_x_spin = QDoubleSpinBox()
        self.drift_x_spin.setRange(-500, 500)
        self.drift_x_spin.setSingleStep(0.1)
        self.drift_x_spin.setValue(0.0)
        self.drift_x_spin.setToolTip("Fixed horizontal shift applied every frame.")
        self.drift_x_spin.valueChanged.connect(self._on_settings_changed)
        manual_row.addWidget(self.drift_x_spin)
        manual_row.addWidget(QLabel("Y:"))
        self.drift_y_spin = QDoubleSpinBox()
        self.drift_y_spin.setRange(-500, 500)
        self.drift_y_spin.setSingleStep(0.1)
        self.drift_y_spin.setValue(0.0)
        self.drift_y_spin.setToolTip("Fixed vertical shift applied every frame.")
        self.drift_y_spin.valueChanged.connect(self._on_settings_changed)
        manual_row.addWidget(self.drift_y_spin)
        drift_layout.addWidget(self.manual_drift_widget)

        # --- EDGE-STRIP: sampling geometry ---
        self.edgestrip_widget = QWidget()
        es_layout = QVBoxLayout(self.edgestrip_widget)
        es_layout.setContentsMargins(0, 0, 0, 0)
        es_row = QHBoxLayout()
        es_row.addWidget(QLabel("MARGIN:"))
        self.edge_margin_spin = QSpinBox()
        self.edge_margin_spin.setRange(0, 400)
        self.edge_margin_spin.setValue(0)
        self.edge_margin_spin.setToolTip(
            "How far in from the true frame edge to sample for tracking texture.\n"
            "Raise this if your footage has a black vignette/circular border -\n"
            "sampling right at pixel 0 would land entirely on blank vignette\n"
            "with nothing to track, which is why 0/4 strips can read as failure."
        )
        self.edge_margin_spin.valueChanged.connect(self._on_edgestrip_params_changed)
        es_row.addWidget(self.edge_margin_spin)
        es_row.addWidget(QLabel("WIDTH:"))
        self.edge_width_spin = QSpinBox()
        self.edge_width_spin.setRange(8, 200)
        self.edge_width_spin.setValue(40)
        self.edge_width_spin.setToolTip("Thickness of the sampled band, in pixels.")
        self.edge_width_spin.valueChanged.connect(self._on_edgestrip_params_changed)
        es_row.addWidget(self.edge_width_spin)
        es_layout.addLayout(es_row)
        drift_layout.addWidget(self.edgestrip_widget)

        # --- ROI: select button ---
        self.select_roi_btn = QPushButton("SELECT ROI")
        self.select_roi_btn.setToolTip("Click, then drag a box on the video over a feature to track.")
        self.select_roi_btn.clicked.connect(self._select_roi)
        self.select_roi_btn.setVisible(False)
        drift_layout.addWidget(self.select_roi_btn)

        self.apply_drift_cb = QCheckBox("APPLY DRIFT CORRECTION")
        self.apply_drift_cb.setToolTip("Master on/off switch - the method above only computes a shift, this applies it.")
        self.apply_drift_cb.stateChanged.connect(self._on_settings_changed)
        drift_layout.addWidget(self.apply_drift_cb)

        self._update_drift_widget_visibility(0)
        layout.addWidget(drift_group)

    def _update_drift_widget_visibility(self, index):
        self.manual_drift_widget.setVisible(index == 0)
        self.edgestrip_widget.setVisible(index == 1)
        self.select_roi_btn.setVisible(index == 2)

    def _on_edgestrip_params_changed(self):
        self.processor.drift_tracker.strip_width = self.edge_width_spin.value()
        self.processor.drift_tracker.margin = self.edge_margin_spin.value()
        self.tracker_initialized = False
        self._drift_cache_frame = None
        self._on_settings_changed()

    def _update_filter_visibility(self, index):
        self.gaussian_widget.setVisible(index == 1)
        self.median_widget.setVisible(index == 2)
        self.bilateral_widget.setVisible(index == 3)

    def _on_filter_changed(self, index):
        self._update_filter_visibility(index)
        self._on_settings_changed()

    def _update_contrast_visibility(self, index):
        self.autocontrast_widget.setVisible(index == 0)
        self.clahe_widget.setVisible(index == 1)

    def _on_contrast_changed(self, index):
        self._update_contrast_visibility(index)
        self._on_settings_changed()

    def _set_drift_status(self, text, color="#4a6080"):
        self._drift_status_text, self._drift_status_color = text, color
        color = self._themed_status_color(color)
        self.drift_status_label.setText(text)
        self.drift_status_label.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 8.5pt;")

    def _on_drift_method_changed(self, index):
        """0 = NONE (manual dx/dy), 1 = EDGE-STRIP (auto), 2 = ROI (auto)."""
        self.processor.drift_tracker.reset()
        self.roi_tracker.reset()
        self.tracker_initialized = False
        self._drift_cache_frame = None

        self._update_drift_widget_visibility(index)

        if index == 0:
            self._set_drift_status("○ MANUAL OFFSET", "#4a6080")
        elif index == 1:
            self._set_drift_status("○ EDGE-STRIP ARMED - PRESS PLAY", "#60b0ff")
        elif index == 2:
            self._set_drift_status("○ ROI - CLICK 'SELECT ROI' THEN DRAG ON VIDEO", "#60b0ff")

        self._on_settings_changed()

    def _select_roi(self):
        if not self.video_loaded:
            QMessageBox.warning(self, "Warning", "No video loaded.")
            return
        self.roi_tracker.start_selection()
        self._drift_cache_frame = None
        self._set_drift_status("● DRAG ON VIDEO TO SELECT ROI", "#ffa500")

    # ------------------------------------------------------------
    # ROI SELECTION - mouse events on the video display
    # ------------------------------------------------------------
    def _label_to_display_coords(self, pos):
        """Map a mouse position on image_label to coords in the displayed
        (scaled) frame's own pixel space, i.e. with the centering
        letterbox offset removed."""
        return pos.x() - self._display_offset[0], pos.y() - self._display_offset[1]

    def _on_image_mouse_press(self, ev):
        if self.drift_combo.currentIndex() == 2 and self.roi_tracker.selecting:
            x, y = self._label_to_display_coords(ev.pos())
            self.roi_tracker.on_mouse_down(x, y)
            self._update_display()

    def _on_image_mouse_move(self, ev):
        if (self.drift_combo.currentIndex() == 2 and self.roi_tracker.selecting
                and self.roi_tracker.selection_start is not None):
            x, y = self._label_to_display_coords(ev.pos())
            self.roi_tracker.on_mouse_move(x, y)
            self._update_display()

    def _on_image_mouse_release(self, ev):
        if self.drift_combo.currentIndex() == 2 and self.roi_tracker.selecting:
            with self._frame_lock:
                raw = self._raw_gray_frame
            if raw is None or self._display_scale <= 0:
                self.roi_tracker.selecting = False
                self.roi_tracker.selection_start = None
                self.roi_tracker.selection_end = None
                return
            display_scale = 1.0 / self._display_scale
            success = self.roi_tracker.on_mouse_up(raw, display_scale, display_scale)
            self._drift_cache_frame = None
            if success:
                self._set_drift_status("● ROI LOCKED - TRACKING ACTIVE", "#2a9a5a")
                if self.apply_drift_cb.isChecked():
                    self._on_settings_changed()
            else:
                self._set_drift_status("○ ROI SELECTION FAILED - TRY AGAIN", "#ff5050")
            self._update_display()

    # ------------------------------------------------------------
    # VIDEO LOADING WITH ERROR HANDLING
    # ------------------------------------------------------------
    def _open_video(self):
        if self._loading_video:
            return
            
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv);;All Files (*.*)"
        )
        if path:
            self._load_video(path)

    def _load_video(self, path):
        if self._loading_video:
            return
            
        self._loading_video = True
        self._update_status("LOADING...", "#ffa500")
        QApplication.processEvents()
        
        try:
            if self.vidcap:
                self.vidcap.release()
                self.vidcap = None
            
            self.video_path = path
            self._load_dm4_metadata_sidecar(path)

            # Try with different backends
            backends = [cv2.CAP_ANY, cv2.CAP_FFMPEG]
            self.vidcap = None
            
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(path, backend)
                    if cap.isOpened():
                        self.vidcap = cap
                        break
                except:
                    continue
            
            if self.vidcap is None or not self.vidcap.isOpened():
                QMessageBox.critical(self, "Error", f"Could not open video:\n{path}")
                self.video_loaded = False
                self._loading_video = False
                self._update_status("FAILED", "#ff5050")
                return

            self.source_fps = self.vidcap.get(cv2.CAP_PROP_FPS)
            self.source_frames = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if self.source_frames <= 0 or self.width <= 0 or self.height <= 0:
                QMessageBox.critical(self, "Error", "Invalid video file. Could not read properties.")
                self.vidcap.release()
                self.vidcap = None
                self.video_loaded = False
                self._loading_video = False
                self._update_status("FAILED", "#ff5050")
                return
                
            self.fps = int(self.source_fps) if self.source_fps > 0 else 25
            self.video_loaded = True
            self._video_error = False
            self.current_frame = 0
            with self._frame_lock:
                self._current_frame = None
                self._raw_gray_frame = None
            self._last_read_ok = False

            # A new video invalidates any tracker state from the previous one
            self.processor.drift_tracker.reset()
            self.roi_tracker.reset()
            self.tracker_initialized = False

            self.setWindowTitle(f"TEM Video Processor - {os.path.basename(path)}")
            self.file_label.setText(os.path.basename(path).upper())
            self.frame_info_label.setText(f"{self.source_frames} FRAMES  {self.width}x{self.height}")

            self.segments = []
            self.segments_list.clear()
            
            self.timeline.set_video_info(self.source_frames, self.fps)
            self.timeline.clear_selection()

            # Match playback speed to the source video's own frame rate
            self.playback_timer.setInterval(max(1, round(1000 / self.fps)))

            # Load first frame
            self._go_to_frame(0)
            
            self._loading_video = False
            self._update_status("READY", "#60b0ff")
            
        except Exception as e:
            print(f"Error loading video: {e}")
            QMessageBox.critical(self, "Error", f"Error loading video:\n{str(e)}")
            self.video_loaded = False
            self.vidcap = None
            self._loading_video = False
            self._update_status("ERROR", "#ff5050")

    def _go_to_frame(self, frame_num, force=False):
        """Navigate to a specific frame with robust error handling.

        force=True re-runs the processing pipeline on the already-decoded
        frame with the current settings, without touching the decoder or
        the drift trackers - used when a slider/spinbox changes while
        paused, so edits are reflected immediately instead of being
        swallowed by the "already on this frame" short-circuit below.
        """
        if not self.video_loaded or self.vidcap is None or not self.vidcap.isOpened():
            return False

        try:
            frame_num = max(0, min(frame_num, self.source_frames - 1))

            reprocess_only = (
                force and frame_num == self.current_frame and self._raw_gray_frame is not None
            )

            # Only seek/decode if we're not already on this frame
            if not force and frame_num == self.current_frame and self._current_frame is not None:
                return True

            if reprocess_only:
                with self._frame_lock:
                    image = self._raw_gray_frame
                sequential = False
            else:
                # Sequential playback can just read the next frame off the decoder -
                # seeking (CAP_PROP_POS_FRAMES) forces a decode from the nearest
                # keyframe on compressed video and is dramatically slower.
                sequential = (
                    self._last_read_ok
                    and self._current_frame is not None
                    and frame_num == self.current_frame + 1
                )

                self.current_frame = frame_num

                # Try to read the frame with retries
                ret = False
                frame = None

                for attempt in range(3):
                    try:
                        if not sequential or attempt > 0:
                            self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                        ret, frame = self.vidcap.read()
                        if ret and frame is not None:
                            break
                        time.sleep(0.01)
                    except Exception as e:
                        print(f"Frame read attempt {attempt+1} failed: {e}")
                        if attempt == 2:
                            raise
                        time.sleep(0.01)
                        continue

                self._last_read_ok = bool(ret and frame is not None)
                if not ret or frame is None:
                    print(f"Failed to read frame {frame_num} after 3 attempts")
                    return False

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                with self._frame_lock:
                    self._raw_gray_frame = image

            # Process the frame
            try:
                settings = self._get_settings_for_frame(frame_num)

                drift_method = self.drift_combo.currentIndex()
                if drift_method != 0 and self.apply_drift_cb.isChecked():
                    # A cached value is only safe to reuse when it was computed
                    # for this exact frame under this exact method - otherwise
                    # re-running the (stateful) tracker would double-step it.
                    cache_valid = (
                        reprocess_only
                        and self._drift_cache_frame == frame_num
                        and self._drift_cache_method == drift_method
                    )
                    if cache_valid:
                        dx, dy = self._last_drift_dx, self._last_drift_dy
                    else:
                        dx, dy = self._compute_auto_drift(image, sequential)
                        self._last_drift_dx, self._last_drift_dy = dx, dy
                        self._drift_cache_frame = frame_num
                        self._drift_cache_method = drift_method
                    self._set_drift_display(dx, dy)
                    settings['apply_drift'] = True
                    settings['drift_dx'] = dx
                    settings['drift_dy'] = dy

                processed = self._process_frame(image, settings)

                with self._frame_lock:
                    self._current_frame = processed
            except Exception as e:
                print(f"Frame processing error: {e}")
                return False
            
            # Update UI
            self.timeline.set_current_frame(frame_num)
            self._update_display()
            self.frame_info_label.setText(f"FRAME {frame_num}/{self.source_frames}")
            
            # Clear error state
            self._video_error = False
            
            return True
            
        except Exception as e:
            print(f"Error going to frame {frame_num}: {e}")
            self._video_error = True
            self._update_status("ERROR", "#ff5050")
            return False

    def _compute_auto_drift(self, gray_frame, sequential):
        """Compute (dx, dy) drift correction for the current frame using the
        active automatic tracker. EDGE-STRIP accumulates drift frame-to-frame
        so it only advances on truly sequential frames (otherwise it
        re-anchors to the current frame); ROI matches a locked template
        within a search window so it tolerates jumps.

        A tracker failure (e.g. a degenerate frame) must not take down the
        whole frame update, so any exception here is swallowed and reported
        via the status bar instead of aborting _go_to_frame's try/except.
        """
        try:
            return self._compute_auto_drift_impl(gray_frame, sequential)
        except Exception as e:
            print(f"Drift tracking error: {e}")
            self._set_drift_status(f"○ TRACKING ERROR: {e}", "#ff5050")
            return 0.0, 0.0

    def _compute_auto_drift_impl(self, gray_frame, sequential):
        method = self.drift_combo.currentIndex()

        if method == 1:  # EDGE-STRIP
            if not sequential or not self.tracker_initialized:
                self.processor.drift_tracker.initialize(gray_frame)
                self.tracker_initialized = True
                self._set_drift_status("○ ANCHORED - WAITING FOR NEXT FRAME", "#60b0ff")
                return 0.0, 0.0
            dx, dy, reliability = self.processor.drift_tracker.compute_drift(gray_frame)
            strips_ok = round(reliability * 4)
            if strips_ok == 0:
                self._set_drift_status(
                    "● 0/4 EDGE STRIPS USABLE - NO TEXTURE AT BORDER. "
                    "TRY RAISING MARGIN, OR USE ROI INSTEAD", "#ff5050"
                )
            elif strips_ok < 2:
                self._set_drift_status(
                    f"● {strips_ok}/4 EDGE STRIPS - TOO FEW, HOLDING LAST POSITION "
                    f"(dx={dx:.1f} dy={dy:.1f})", "#ffa500"
                )
            else:
                self._set_drift_status(f"● TRACKING {strips_ok}/4 STRIPS  dx={dx:.1f} dy={dy:.1f}", "#2a9a5a")
            return dx, dy

        if method == 2:  # ROI
            if not self.roi_tracker.roi_locked:
                self._set_drift_status("○ NO ROI LOCKED - CLICK 'SELECT ROI'", "#ffa500")
                return 0.0, 0.0
            shift_x, shift_y, confidence = self.roi_tracker.compute_offset(gray_frame)
            # ROITracker.compute_offset already returns the correction shift
            # (i.e. -object_displacement), whereas apply_drift_correction(dx,dy)
            # expects the raw displacement and negates it internally - so this
            # value must be negated here or the correction doubles the drift
            # instead of cancelling it.
            dx, dy = -shift_x, -shift_y
            if confidence < self.roi_tracker.confidence_threshold:
                self._set_drift_status(
                    f"● WEAK MATCH ({confidence:.2f}) - HOLDING LAST POSITION "
                    f"(dx={dx:.1f} dy={dy:.1f})", "#ffa500"
                )
            else:
                self._set_drift_status(f"● TRACKING (confidence={confidence:.2f})  dx={dx:.1f} dy={dy:.1f}", "#2a9a5a")
            return dx, dy

        return 0.0, 0.0

    def _set_drift_display(self, dx, dy):
        for spin, val in ((self.drift_x_spin, dx), (self.drift_y_spin, dy)):
            spin.blockSignals(True)
            spin.setValue(max(spin.minimum(), min(spin.maximum(), val)))
            spin.blockSignals(False)

    def _get_settings_for_frame(self, frame_num):
        settings = {
            'gamma': self.gamma_value,
            'contrast_method': self.contrast_combo.currentIndex(),
            'autocontrast_low': self.ac_low_spin.value(),
            'autocontrast_high': self.ac_high_spin.value(),
            'clahe_clip': self.clahe_clip_spin.value(),
            'clahe_tile': self.clahe_tile_spin.value(),
            'filter_mode': self.filter_combo.currentIndex(),
            'gaussian_kernel': self.gk_spin.value(),
            'gaussian_sigma': self.gs_spin.value(),
            'median_kernel': self.mk_spin.value(),
            'bilateral_d': self.bd_spin.value(),
            'bilateral_sigmaColor': self.bsc_spin.value(),
            'bilateral_sigmaSpace': self.bss_spin.value(),
            'apply_drift': self.apply_drift_cb.isChecked(),
            'drift_dx': self.drift_x_spin.value(),
            'drift_dy': self.drift_y_spin.value(),
        }
        
        for seg in self.segments:
            if seg.enabled and seg.contains(frame_num):
                settings.update(seg.settings)
                break
        
        return settings

    def _process_frame(self, image, settings):
        processed = image.copy()
        
        if settings.get('apply_drift', False):
            dx = settings.get('drift_dx', 0.0)
            dy = settings.get('drift_dy', 0.0)
            if abs(dx) > 0.01 or abs(dy) > 0.01:
                processed = self.processor.apply_drift_correction(processed, dx, dy)
        
        if self.ff_cb.isChecked() and self.D is not None and self.D.shape == processed.shape:
            if self.processor.ff_buffer is None or self.processor.ff_buffer.shape != processed.shape:
                self.processor.ff_buffer = np.empty(processed.shape, dtype=np.float32)
                self.processor.ff_output = np.empty(processed.shape, dtype=np.uint8)
            self.processor.ff_buffer[:] = processed
            np.subtract(self.processor.ff_buffer, self.D, out=self.processor.ff_buffer)
            np.multiply(self.processor.ff_buffer, self.G, out=self.processor.ff_buffer)
            np.clip(self.processor.ff_buffer, 0, 255, out=self.processor.ff_buffer)
            np.round(self.processor.ff_buffer, out=self.processor.ff_buffer)
            self.processor.ff_output[:] = self.processor.ff_buffer.astype(np.uint8, copy=False)
            processed = self.processor.ff_output
        
        contrast_method = settings.get('contrast_method', 0)
        if contrast_method == 0:
            self.processor.set_autocontrast_range(
                settings.get('autocontrast_low', 1.0),
                settings.get('autocontrast_high', 99.0)
            )
            processed = self.processor.adaptive_autocontrast_cached(processed)
        elif contrast_method == 1:
            self.processor.set_clahe_params(
                settings.get('clahe_clip', 2.0),
                settings.get('clahe_tile', 8)
            )
            processed = self.processor.apply_clahe(processed)

        self.processor.frame_count += 1

        gamma = settings.get('gamma', 0.65)
        processed = self.processor.apply_gamma_fast(processed, gamma)
        
        filter_mode = settings.get('filter_mode', 0)
        if filter_mode == 1:
            k = settings.get('gaussian_kernel', 3)
            if k % 2 == 0: k += 1
            sigma = settings.get('gaussian_sigma', 1.0)
            processed = cv2.GaussianBlur(processed, (k, k), sigma)
        elif filter_mode == 2:
            k = settings.get('median_kernel', 3)
            if k % 2 == 0: k += 1
            processed = cv2.medianBlur(processed, k)
        elif filter_mode == 3:
            d = settings.get('bilateral_d', 9)
            sc = settings.get('bilateral_sigmaColor', 75)
            ss = settings.get('bilateral_sigmaSpace', 75)
            processed = cv2.bilateralFilter(processed, d, sc, ss)
        
        return processed

    # ------------------------------------------------------------
    # DM4 METADATA OVERLAY
    # ------------------------------------------------------------
    _UNIT_TO_NM = {'nm': 1.0, 'µm': 1000.0, 'um': 1000.0, 'mm': 1e6, 'pm': 1e-3, 'å': 0.1, 'angstrom': 0.1}

    def _format_length(self, value, unit):
        """Convert to nm (the canonical unit ncempy reports pixel calibration
        in) then pick whichever of pm/nm/um/mm reads most naturally, since a
        several-micron field of view in nm is unwieldy (e.g. '3007.5 nm')."""
        factor = self._UNIT_TO_NM.get((unit or '').strip().lower())
        if factor is None:
            return f"{value:.4g} {unit}"
        nm = value * factor
        if nm < 1.0:
            return f"{nm * 1000:.1f} pm"
        if nm < 1000.0:
            return f"{nm:.3f} nm"
        if nm < 1e6:
            return f"{nm / 1000.0:.3f} µm"
        return f"{nm / 1e6:.3f} mm"

    def _load_dm4_metadata_sidecar(self, video_path):
        self.dm4_metadata = None
        sidecar_path = video_path + ".metadata.json"
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    self.dm4_metadata = json.load(f)
            except (OSError, ValueError) as e:
                print(f"Could not load metadata sidecar: {e}")
        self._update_metadata_overlay()

    def _update_metadata_overlay(self):
        m = self.dm4_metadata
        self.metadata_overlay_cb.setEnabled(bool(m))
        if not m:
            self.metadata_overlay.hide()
            return

        lines = []
        if 'pixel_size_x' in m and 'pixel_unit' in m:
            lines.append(f"PIXEL SIZE: {self._format_length(m['pixel_size_x'], m['pixel_unit'])}/px")
        if 'fov_width' in m and 'pixel_unit' in m:
            fov_w = self._format_length(m['fov_width'], m['pixel_unit'])
            fov_h = self._format_length(m['fov_height'], m['pixel_unit'])
            lines.append(f"FOV: {fov_w} x {fov_h}")
        if m.get('voltage'):
            lines.append(f"VOLTAGE: {m['voltage']}")
        if m.get('magnification'):
            lines.append(f"MAG: {m['magnification']}")
        if m.get('exposure_s') is not None:
            lines.append(f"EXPOSURE: {m['exposure_s'] * 1000:.2f} ms")
        if m.get('binning'):
            lines.append(f"BINNING: {m['binning']}")
        if m.get('illumination_mode'):
            lines.append(f"MODE: {m['illumination_mode']}")
        if m.get('microscope'):
            lines.append(f"SCOPE: {m['microscope']}")
        if m.get('specimen'):
            lines.append(f"SPECIMEN: {m['specimen']}")
        if m.get('operator'):
            lines.append(f"OPERATOR: {m['operator']}")
        if m.get('acquisition_date'):
            when = m['acquisition_date']
            if m.get('acquisition_time'):
                when += f" {m['acquisition_time']}"
            lines.append(f"ACQUIRED: {when}")

        self.metadata_overlay.setText("\n".join(lines) if lines else "NO METADATA FIELDS FOUND")
        self.metadata_overlay.adjustSize()
        self.metadata_overlay.setVisible(self.metadata_overlay_cb.isChecked())

    def _update_display(self):
        with self._frame_lock:
            image = self._current_frame
            if image is None:
                return
        
        if len(image.shape) == 2:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        label_size = self.image_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return
        
        h, w = rgb.shape[:2]
        scale = min(label_size.width() / w, label_size.height() / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        self._display_scale = scale
        self._display_offset = (
            (label_size.width() - new_w) // 2,
            (label_size.height() - new_h) // 2,
        )

        drift_method = self.drift_combo.currentIndex()
        if drift_method == 1:
            rgb = self.processor.drift_tracker.draw_overlay(rgb, color=(0, 220, 130))
        elif drift_method == 2:
            if self.roi_tracker.roi_locked and self.roi_tracker.template_pos:
                x, y, tw, th = self.roi_tracker.template_pos
                cv2.rectangle(rgb, (x, y), (x + tw, y + th), (0, 220, 130), 2)
            elif self.roi_tracker.selecting and self.roi_tracker.selection_start is not None:
                rect = self.roi_tracker.get_selection_rect()
                if rect:
                    sx, sy, sw, sh = rect
                    x1 = int(sx / scale)
                    y1 = int(sy / scale)
                    x2 = int((sx + sw) / scale)
                    y2 = int((sy + sh) / scale)
                    cv2.rectangle(rgb, (x1, y1), (x2, y2), (255, 165, 0), 2)

        resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        h, w, ch = resized.shape
        bytes_per_line = ch * w
        qt_image = QImage(resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def _update_status(self, text, color="#4a6080"):
        self._status_text, self._status_color = text, color
        color = self._themed_status_color(color)
        theme = THEME_COLORS[self._theme]
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            color: {color};
            padding: 3px 16px;
            background: {theme['status_bg']};
            border-radius: 10px;
            border: 1px solid {theme['status_border']};
            letter-spacing: 0.5px;
        """)

    # ------------------------------------------------------------
    # TIMELINE CALLBACKS
    # ------------------------------------------------------------
    def _on_timeline_frame_changed(self, frame):
        if not self._video_error and self.video_loaded and not self._loading_video:
            self._go_to_frame(frame)

    def _on_selection_changed(self, in_point, out_point):
        if in_point >= 0 and out_point >= 0:
            self._update_status(f"SEL {in_point}->{out_point}", "#60b0ff")
        else:
            self._update_status("READY", "#4a6080")

    def _on_in_point_changed(self, frame):
        self.in_btn.setText(f"IN:{frame}" if frame >= 0 else "IN")

    def _on_out_point_changed(self, frame):
        self.out_btn.setText(f"OUT:{frame}" if frame >= 0 else "OUT")

    def _set_in_point(self):
        self.timeline.in_point = self.current_frame
        if self.timeline.out_point >= 0 and self.timeline.in_point > self.timeline.out_point:
            self.timeline.in_point, self.timeline.out_point = self.timeline.out_point, self.timeline.in_point
        self.timeline.update()
        self._on_in_point_changed(self.timeline.in_point)
        self._on_selection_changed(self.timeline.in_point, self.timeline.out_point)

    def _set_out_point(self):
        self.timeline.out_point = self.current_frame
        if self.timeline.in_point >= 0 and self.timeline.in_point > self.timeline.out_point:
            self.timeline.in_point, self.timeline.out_point = self.timeline.out_point, self.timeline.in_point
        self.timeline.update()
        self._on_out_point_changed(self.timeline.out_point)
        self._on_selection_changed(self.timeline.in_point, self.timeline.out_point)

    def _clear_selection(self):
        self.timeline.clear_selection()
        self.in_btn.setText("IN")
        self.out_btn.setText("OUT")
        self._update_status("READY", "#4a6080")

    # ------------------------------------------------------------
    # SEGMENTS
    # ------------------------------------------------------------
    def _add_segment(self):
        if not self.video_loaded:
            QMessageBox.warning(self, "Warning", "No video loaded.")
            return
        
        in_p = self.timeline.in_point
        out_p = self.timeline.out_point
        
        if in_p < 0 or out_p < 0:
            QMessageBox.warning(self, "Warning", 
                "Set IN and OUT points first.\nUse timeline or I/O keys.")
            return
        
        settings = self._get_current_settings()
        segment = ProcessingSegment(in_p, out_p, settings)
        segment.name = f"SEG {len(self.segments) + 1}"
        self.segments.append(segment)
        
        item = QListWidgetItem(f"{segment.name}  {in_p}->{out_p}  ({out_p-in_p+1} FRAMES)")
        self.segments_list.addItem(item)
        self._update_status(f"ADDED {segment.name}", "#2a9a5a")

    def _get_current_settings(self):
        return {
            'gamma': self.gamma_value,
            'contrast_method': self.contrast_combo.currentIndex(),
            'autocontrast_low': self.ac_low_spin.value(),
            'autocontrast_high': self.ac_high_spin.value(),
            'clahe_clip': self.clahe_clip_spin.value(),
            'clahe_tile': self.clahe_tile_spin.value(),
            'filter_mode': self.filter_combo.currentIndex(),
            'gaussian_kernel': self.gk_spin.value(),
            'gaussian_sigma': self.gs_spin.value(),
            'median_kernel': self.mk_spin.value(),
            'bilateral_d': self.bd_spin.value(),
            'bilateral_sigmaColor': self.bsc_spin.value(),
            'bilateral_sigmaSpace': self.bss_spin.value(),
            'apply_drift': self.apply_drift_cb.isChecked(),
            'drift_dx': self.drift_x_spin.value(),
            'drift_dy': self.drift_y_spin.value(),
        }

    def _on_segment_selected(self, item):
        idx = self.segments_list.currentRow()
        if idx >= 0 and idx < len(self.segments):
            self.del_seg_btn.setEnabled(True)
            seg = self.segments[idx]
            
            self.gamma_slider.setValue(int(seg.settings.get('gamma', 0.65) * 100))
            self.contrast_combo.setCurrentIndex(seg.settings.get('contrast_method', 0))
            self.ac_low_spin.setValue(seg.settings.get('autocontrast_low', 1.0))
            self.ac_high_spin.setValue(seg.settings.get('autocontrast_high', 99.0))
            self.clahe_clip_spin.setValue(seg.settings.get('clahe_clip', 2.0))
            self.clahe_tile_spin.setValue(seg.settings.get('clahe_tile', 8))
            self.filter_combo.setCurrentIndex(seg.settings.get('filter_mode', 0))
            self.gk_spin.setValue(seg.settings.get('gaussian_kernel', 3))
            self.gs_spin.setValue(seg.settings.get('gaussian_sigma', 1.0))
            self.mk_spin.setValue(seg.settings.get('median_kernel', 3))
            self.bd_spin.setValue(seg.settings.get('bilateral_d', 9))
            self.bsc_spin.setValue(seg.settings.get('bilateral_sigmaColor', 75))
            self.bss_spin.setValue(seg.settings.get('bilateral_sigmaSpace', 75))
            self.drift_x_spin.setValue(seg.settings.get('drift_dx', 0.0))
            self.drift_y_spin.setValue(seg.settings.get('drift_dy', 0.0))
            self.apply_drift_cb.setChecked(seg.settings.get('apply_drift', False))
            
            self.timeline.set_selection(seg.start_frame, seg.end_frame)
            self._go_to_frame(seg.start_frame)
            self._update_status(f"LOADED {seg.name}", "#60b0ff")

    def _delete_segment(self):
        idx = self.segments_list.currentRow()
        if idx >= 0:
            self.segments.pop(idx)
            self.segments_list.takeItem(idx)
            self.del_seg_btn.setEnabled(False)
            self._update_status("SEGMENT DELETED", "#ff5050")

    def _clear_segments(self):
        self.segments = []
        self.segments_list.clear()
        self.del_seg_btn.setEnabled(False)
        self._update_status("ALL SEGMENTS CLEARED", "#ff5050")

    # ------------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------------
    def _on_gamma_slider_changed(self, value):
        self.gamma_value = value / 100.0
        self.gamma_spin.blockSignals(True)
        self.gamma_spin.setValue(self.gamma_value)
        self.gamma_spin.blockSignals(False)
        self._on_settings_changed()

    def _on_gamma_spin_changed(self, value):
        self.gamma_value = value
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(round(value * 100))
        self.gamma_slider.blockSignals(False)
        self._on_settings_changed()

    def _on_settings_changed(self):
        if self.video_loaded and not self._video_error and not self._loading_video:
            self._go_to_frame(self.current_frame, force=True)

    def _reset_settings(self):
        self.gamma_slider.setValue(65)
        self.contrast_combo.setCurrentIndex(0)
        self.ac_low_spin.setValue(1.0)
        self.ac_high_spin.setValue(99.0)
        self.clahe_clip_spin.setValue(2.0)
        self.clahe_tile_spin.setValue(8)
        self.filter_combo.setCurrentIndex(0)
        self.gk_spin.setValue(3)
        self.gs_spin.setValue(1.0)
        self.mk_spin.setValue(3)
        self.bd_spin.setValue(9)
        self.bsc_spin.setValue(75)
        self.bss_spin.setValue(75)
        self.drift_x_spin.setValue(0.0)
        self.drift_y_spin.setValue(0.0)
        self.edge_margin_spin.setValue(0)
        self.edge_width_spin.setValue(40)
        self.apply_drift_cb.setChecked(False)
        self.ff_cb.setChecked(False)
        self.drift_combo.setCurrentIndex(0)
        self._on_settings_changed()

    # ------------------------------------------------------------
    # PLAYBACK
    # ------------------------------------------------------------
    def _toggle_play(self):
        if not self.video_loaded:
            return
            
        if self._is_playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        """Start playback."""
        if not self.video_loaded or self.vidcap is None or self._loading_video:
            return
        if self._exporting:
            # Export reads self.vidcap sequentially in its own loop; letting
            # playback restart here (e.g. via the Space shortcut, which
            # doesn't go through play_btn's disabled state) would race both
            # loops against the same VideoCapture object.
            return
        
        if self.current_frame >= self.source_frames - 1:
            self.current_frame = 0
            self._go_to_frame(0)
        
        self._is_playing = True
        self.play_btn.setText("PAUSE")
        self.playback_timer.start(self.playback_timer.interval())
        self._update_status("PLAYING", "#2a9a5a")

    def _pause(self):
        """Pause playback."""
        self._is_playing = False
        self.play_btn.setText("PLAY")
        self.playback_timer.stop()
        self._update_status("PAUSED", "#ffa500")

    def _stop(self):
        self._pause()
        self._go_to_frame(0)

    @pyqtSlot()
    def _playback_step(self):
        """Timer callback for playback - simplified and robust."""
        if not self._is_playing or self._loading_video:
            return
        
        # If we had an error, try to recover
        if self._video_error:
            self._video_error = False
            self._update_status("RECOVERING...", "#ffa500")
            # Try to reload current frame
            if self._go_to_frame(self.current_frame):
                self._update_status("PLAYING", "#2a9a5a")
            return
        
        next_frame = self.current_frame + 1
        if next_frame >= self.source_frames:
            self._pause()
            self._update_status("END", "#4a6080")
            return
        
        # Try to go to next frame
        success = self._go_to_frame(next_frame)
        if success:
            now = time.time()
            dt = now - self.last_frame_time
            self.last_frame_time = now
            if dt > 0:
                self.frame_times.append(dt)
                if len(self.frame_times) > 30:
                    self.frame_times.pop(0)
                self.actual_fps = len(self.frame_times) / sum(self.frame_times)
        if not success and self._is_playing:
            # If we failed, try again after a short delay
            self._video_error = True
            self._update_status("RETRYING...", "#ffa500")

    # ------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------
    def _export_video(self):
        if self._is_playing:
            self._pause()

        if not self.video_loaded:
            QMessageBox.warning(self, "Warning", "No video loaded.")
            return

        if not self.segments:
            reply = QMessageBox.question(
                self, "Export",
                "No segments defined. Export entire video with current settings?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            self._set_export_controls_enabled(False)
            try:
                self._export_range(0, self.source_frames - 1, "full")
            finally:
                self._set_export_controls_enabled(True)
            return

        self._set_export_controls_enabled(False)
        try:
            self._export_segments()
        finally:
            self._set_export_controls_enabled(True)

    def _set_export_controls_enabled(self, enabled):
        """Toggle playback-affecting controls around an export.

        Disabling play_btn/stop_btn/timeline blocks mouse interaction; the
        self._exporting flag additionally blocks _play() itself, since the
        Space-bar shortcut calls it directly and doesn't go through
        play_btn's enabled state.
        """
        self._exporting = not enabled
        self.play_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.timeline.setEnabled(enabled)

    def _export_range(self, start, end, name):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Video",
            f"{name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mkv",
            "Video Files (*.mkv *.mp4 *.avi)"
        )
        if not path:
            return
        
        total = end - start + 1
        progress = QProgressDialog("Exporting video...", "Cancel", 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}',
            '-pix_fmt', 'gray',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx265',
            '-crf', '22',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            path
        ]
        
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )

        drift_method = self.drift_combo.currentIndex()
        drift_active = drift_method != 0 and self.apply_drift_cb.isChecked()
        if drift_active:
            # Fresh reference for this export pass: EDGE-STRIP re-anchors to
            # the range's first frame, ROI keeps its locked template but
            # restarts accumulated drift from zero.
            self.processor.drift_tracker.reset()
            self.roi_tracker.cumulative_dx = 0.0
            self.roi_tracker.cumulative_dy = 0.0
            self.roi_tracker.last_dx = 0.0
            self.roi_tracker.last_dy = 0.0

        try:
            for i, frame_num in enumerate(range(start, end + 1)):
                if progress.wasCanceled():
                    break

                if self.vidcap is None:
                    break

                if i == 0:
                    # Only the first frame needs an explicit seek - the loop
                    # then reads sequentially, which is far faster than
                    # seeking (CAP_PROP_POS_FRAMES) on every single frame.
                    self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = self.vidcap.read()

                if not ret:
                    continue

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                settings = self._get_settings_for_frame(frame_num)

                if drift_active:
                    dx, dy = self._compute_auto_drift(image, sequential=(i > 0))
                    settings['apply_drift'] = True
                    settings['drift_dx'] = dx
                    settings['drift_dy'] = dy

                processed = self._process_frame(image, settings)

                proc.stdin.write(processed.tobytes())
                progress.setValue(i + 1)
                QApplication.processEvents()
            
            proc.stdin.close()
            proc.wait(timeout=300)
            
        except Exception as e:
            print(f"Export error: {e}")
            proc.kill()

        # Exporting reads the shared vidcap independently of _go_to_frame's
        # sequential-read bookkeeping, so force the next preview navigation
        # to reseek rather than trusting a stale decoder position.
        self._last_read_ok = False

        progress.close()

        if os.path.exists(path):
            size = os.path.getsize(path) / (1024 * 1024)
            QMessageBox.information(self, "Export Complete", 
                f"Video exported successfully!\n\n{os.path.basename(path)}\n{size:.1f} MB")

    def _export_segments(self):
        for i, seg in enumerate(self.segments):
            if seg.enabled:
                self._export_range(
                    seg.start_frame,
                    seg.end_frame,
                    f"segment_{i+1:03d}"
                )

    # ------------------------------------------------------------
    # SCREENSHOT
    # ------------------------------------------------------------
    def _on_screenshot(self):
        with self._frame_lock:
            image = self._current_frame
            if image is not None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}_frame{self.current_frame:06d}.png"
                cv2.imwrite(filename, image)
                self._update_status(f"SCREENSHOT SAVED", "#60b0ff")

    # ------------------------------------------------------------
    # HISTOGRAM
    # ------------------------------------------------------------
    def _open_histogram_window(self):
        if self.histogram_window is None or not self.histogram_window.isVisible():
            self.histogram_window = QMainWindow(self)
            self.histogram_window.setWindowTitle("Histogram")
            self.histogram_window.setGeometry(100, 100, 400, 300)
            self.histogram_window.setStyleSheet(LIGHT_STYLESHEET if self._theme == 'light' else DARK_STYLESHEET)

            self.hist_figure = Figure(figsize=(4, 3), dpi=100, facecolor='#1a1b1e')
            self.hist_ax = self.hist_figure.add_subplot(111)
            self.hist_ax.set_xlabel("Intensity", color='#8a8b90')
            self.hist_ax.set_ylabel("Frequency", color='#8a8b90')
            self.hist_ax.grid(True, alpha=0.15, color='#3a3b40')
            self.hist_ax.set_facecolor('#1a1b1e')
            self.hist_ax.tick_params(colors='#8a8b90')

            self.hist_ax.bar(range(256), [0]*256, color='#5b86ad', alpha=0.85, width=1.0)
            self.hist_ax.set_xlim(0, 255)
            
            self.hist_canvas = FigureCanvas(self.hist_figure)
            self.histogram_window.setCentralWidget(self.hist_canvas)
            self.histogram_window.show()
        else:
            self.histogram_window.raise_()

    def _update_histogram(self):
        if self.histogram_window is None or not self.histogram_window.isVisible():
            return
        
        with self._frame_lock:
            img = self._current_frame
            if img is None:
                return
        
        try:
            hist = np.histogram(img.flatten(), bins=256, range=(0, 255))[0]
            self.hist_ax.clear()
            self.hist_ax.bar(range(256), hist, color='#5b86ad', alpha=0.85, width=1.0)
            self.hist_ax.set_xlabel("Intensity", color='#8a8b90')
            self.hist_ax.set_ylabel("Frequency", color='#8a8b90')
            self.hist_ax.grid(True, alpha=0.15, color='#3a3b40')
            self.hist_ax.set_facecolor('#1a1b1e')
            self.hist_ax.tick_params(colors='#8a8b90')
            self.hist_ax.set_xlim(0, 255)

            mean_val = np.mean(img)
            std_val = np.std(img)
            self.hist_ax.set_title(f"MEAN: {mean_val:.1f}  STD: {std_val:.1f}", color='#cfd0d4')
            
            self.hist_canvas.draw()
        except Exception as e:
            pass

    # ------------------------------------------------------------
    # FPS UPDATE
    # ------------------------------------------------------------
    def _update_fps_display(self):
        if hasattr(self, 'actual_fps'):
            self.fps_display.setText(f"{self.actual_fps:.1f} FPS")

    # ------------------------------------------------------------
    # FULLSCREEN
    # ------------------------------------------------------------
    def _set_fullscreen(self, on):
        if on:
            self.showFullScreen()
        else:
            self.showNormal()

    # ------------------------------------------------------------
    # KEYBOARD SHORTCUTS
    # ------------------------------------------------------------
    def keyPressEvent(self, event):
        """Global keyboard shortcuts: Space play/pause, Q quit, F11 fullscreen,
        Escape exits fullscreen, Left/Right step a frame, I/O set IN/OUT,
        X clear selection, A add segment, C screenshot."""
        key = event.key()
        if key == Qt.Key_Space:
            self._toggle_play()
        elif key == Qt.Key_Q:
            self.close()
        elif key == Qt.Key_F11:
            self.fullscreen_cb.setChecked(not self.fullscreen_cb.isChecked())
        elif key == Qt.Key_Escape and self.isFullScreen():
            self.fullscreen_cb.setChecked(False)
        elif key == Qt.Key_Right:
            self._go_to_frame(self.current_frame + 1)
        elif key == Qt.Key_Left:
            self._go_to_frame(self.current_frame - 1)
        elif key == Qt.Key_I:
            self._set_in_point()
        elif key == Qt.Key_O:
            self._set_out_point()
        elif key == Qt.Key_X:
            self._clear_selection()
        elif key == Qt.Key_A:
            self._add_segment()
        elif key == Qt.Key_C:
            self._on_screenshot()
        super().keyPressEvent(event)

    # ------------------------------------------------------------
    # SHUTDOWN
    # ------------------------------------------------------------
    def closeEvent(self, event):
        """Shuts down cleanly: stops playback, saves the drift log, and releases
        the video capture. Safe to call more than once."""
        if getattr(self, '_shutdown_done', False):
            event.accept()
            return
        self._shutdown_done = True
        self._running = False
        self._is_playing = False
        self.playback_timer.stop()

        print("\nShutting down...")

        if self.csv_file:
            self.csv_file.close()
            print(f"Drift log saved: {self.csv_filename}")

        if self.vidcap is not None:
            self.vidcap.release()

        print(f"\n{'=' * 60}\nFINAL REPORT\n{'=' * 60}")
        if self.video_path:
            print(f"Source: {os.path.basename(self.video_path)}  ({self.source_frames} frames)")
        else:
            print("Source: none loaded")
        print(f"Segments defined: {len(self.segments)}")

        event.accept()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_STYLESHEET)

    window = TEMVideoProcessor()
    launcher = DM4ConverterDialog()
    launcher.video_ready.connect(window._load_video)
    launcher.exec_()

    window.show()

    sys.exit(app.exec_())
