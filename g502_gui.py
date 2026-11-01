#!/usr/bin/env python3
"""
AGY Logitech Linux Control Suite & Macro Studio v2.6
--------------------------------------------------
A unified, feature-packed Linux control application for Logitech Gaming Gear:
  - Logitech Gaming Mouse (G502 Hero/LIGHTSPEED, etc.) via libratbagd & Piper interactive button macro customization.
  - Logitech Gaming Headset (G733 Wireless) via direct HID++ 2.0 driver, PipeWire/ALSA & OpenRGB.
  - Targeted G733 RGB Lightstrip Control (Feature 0x8070 over hidraw) & 10-band Hardware Equalizer (Feature 0x8310).
  - Smooth, Hysteresis-Filtered Battery Indication (5% G HUB steps, no voltage bouncing).
  - Physical Power Button Press Listener for G733 (evdev hardware reports).
  - Expanded 18 Custom Visual Themes with better-ui concentric radii, optical alignment, and crisp SVG icons.
  - System Tray Integration (QSystemTrayIcon) with minimize-on-close behavior.
  - Comprehensive Settings Page (⚙ Gear icon) with Appearance themes, live System Diagnostics, and GitHub link.
  - Hamburger Menu (☰) for quick device switching and app controls.
"""

import sys
import os
import time
import glob
import subprocess
import json
import logging
import threading
import struct

import evdev
import select

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl, QPoint
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QCursor, QPixmap, QDesktopServices, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QCheckBox, QGroupBox,
    QTabWidget, QTextEdit, QFrame, QSpinBox, QDoubleSpinBox, QStackedWidget,
    QGraphicsDropShadowEffect, QMessageBox, QScrollArea, QGridLayout, QButtonGroup,
    QDialog, QSystemTrayIcon, QMenu, QProgressBar, QColorDialog
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

CONFIG_PATH = os.path.expanduser('~/.config/g502_macros/config.json')
SETTINGS_PATH = os.path.expanduser('~/.config/g502_macros/settings.json')
ICONS_CACHE_DIR = os.path.expanduser('~/.config/g502_macros/icons')
DIAGRAM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'g502_diagram.png')
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
GITHUB_URL = "https://github.com/gaxkalik/Logitech-Linux-App"

from ghub_canvas import write_ghub_svgs, HardwareStageWidget, GHubHomeWidget

THEMES = {
    "Dark Void (Default)": {
        "bg_main": "#000000",
        "bg_card": "#18181B",
        "bg_input": "#222226",
        "accent": "#00A8FC",
        "text_main": "#F4F4F5",
        "text_sub": "#8E8E93",
        "border": "#2E2E32"
    },
    "Midnight Cyan": {
        "bg_main": "#05070A",
        "bg_card": "#12161F",
        "bg_input": "#1C222E",
        "accent": "#00B8D9",
        "text_main": "#F1F5F9",
        "text_sub": "#94A3B8",
        "border": "#283142"
    },
    "Cyberpunk Neon": {
        "bg_main": "#09090B",
        "bg_card": "#18181B",
        "bg_input": "#27272A",
        "accent": "#F59E0B",
        "text_main": "#FAFAFA",
        "text_sub": "#A1A1AA",
        "border": "#3F3F46"
    },
    "Slate Dark": {
        "bg_main": "#090B0E",
        "bg_card": "#14181F",
        "bg_input": "#1F242D",
        "accent": "#3B82F6",
        "text_main": "#F3F4F6",
        "text_sub": "#9CA3AF",
        "border": "#2D3542"
    },
    "Nordic Frost": {
        "bg_main": "#181C22",
        "bg_card": "#232831",
        "bg_input": "#2E3440",
        "accent": "#88C0D0",
        "text_main": "#ECEFF4",
        "text_sub": "#9EA9B8",
        "border": "#3B4252"
    },
    "Dracula Dark": {
        "bg_main": "#111217",
        "bg_card": "#1C1E26",
        "bg_input": "#282A36",
        "accent": "#8B5CF6",
        "text_main": "#F8F8F2",
        "text_sub": "#9499B3",
        "border": "#343746"
    },
    "Emerald Forest": {
        "bg_main": "#050B09",
        "bg_card": "#101C18",
        "bg_input": "#182923",
        "accent": "#10B981",
        "text_main": "#ECFDF5",
        "text_sub": "#86A89D",
        "border": "#233B33"
    },
    "Sunset Crimson": {
        "bg_main": "#0C0707",
        "bg_card": "#1A1111",
        "bg_input": "#261919",
        "accent": "#E11D48",
        "text_main": "#F5F5F5",
        "text_sub": "#A38F8F",
        "border": "#382424"
    },
    "Tokyo Night": {
        "bg_main": "#0D0E14",
        "bg_card": "#161822",
        "bg_input": "#212433",
        "accent": "#60A5FA",
        "text_main": "#E2E8F0",
        "text_sub": "#8B95B0",
        "border": "#2E3348"
    },
    "Solar Gold": {
        "bg_main": "#0A0A0A",
        "bg_card": "#171717",
        "bg_input": "#242424",
        "accent": "#D97706",
        "text_main": "#F5F5F4",
        "text_sub": "#A8A29E",
        "border": "#333333"
    },
    "Synthwave 80s": {
        "bg_main": "#09090D",
        "bg_card": "#15151E",
        "bg_input": "#222230",
        "accent": "#06B6D4",
        "text_main": "#F4F4F6",
        "text_sub": "#9494A6",
        "border": "#2E2E40"
    },
    "Matrix Hacker": {
        "bg_main": "#060807",
        "bg_card": "#111613",
        "bg_input": "#1A221D",
        "accent": "#22C55E",
        "text_main": "#E6EDF3",
        "text_sub": "#7D9184",
        "border": "#26332B"
    },
    "Deep Amethyst": {
        "bg_main": "#0B0910",
        "bg_card": "#171320",
        "bg_input": "#231D30",
        "accent": "#9333EA",
        "text_main": "#F3E8FF",
        "text_sub": "#9C8FAD",
        "border": "#322945"
    },
    "Oceanic Abyss": {
        "bg_main": "#04080E",
        "bg_card": "#0D1520",
        "bg_input": "#162233",
        "accent": "#0EA5E9",
        "text_main": "#E0F2FE",
        "text_sub": "#8298B0",
        "border": "#21324A"
    },
    "Rose Gold Luxe": {
        "bg_main": "#0C0C0E",
        "bg_card": "#18181B",
        "bg_input": "#27272A",
        "accent": "#F43F5E",
        "text_main": "#FAFAFA",
        "text_sub": "#A1A1AA",
        "border": "#3F3F46"
    },
    "Vaporwave Pastel": {
        "bg_main": "#101016",
        "bg_card": "#1B1B24",
        "bg_input": "#272733",
        "accent": "#818CF8",
        "text_main": "#F4F4F6",
        "text_sub": "#9B9BB0",
        "border": "#363647"
    },
    "Monochrome Stealth": {
        "bg_main": "#000000",
        "bg_card": "#141414",
        "bg_input": "#222222",
        "accent": "#FFFFFF",
        "text_main": "#FAFAFA",
        "text_sub": "#8E8E93",
        "border": "#2E2E2E"
    },
    "Light Pristine": {
        "bg_main": "#F4F4F5",
        "bg_card": "#FFFFFF",
        "bg_input": "#E4E4E7",
        "accent": "#0284C7",
        "text_main": "#09090B",
        "text_sub": "#52525B",
        "border": "#D4D4D8"
    }
}


def adjust_hex_color(hex_str, factor=1.12):
    """Lightens or darkens a #RRGGBB color string cleanly for hover/pressed states."""
    h = hex_str.lstrip('#')
    if len(h) != 6:
        return hex_str
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02X}{g:02X}{b:02X}"


def is_light_theme(theme_name):
    return theme_name == "Light Pristine"


def apply_card_elevation(widget, theme_name="Dark Void (Default)"):
    """No ambient radial glows; uses crisp high-contrast structural planes per strict G HUB spec."""
    widget.setGraphicsEffect(None)


def generate_qss(theme_name="Dark Void (Default)"):
    t = THEMES.get(theme_name, THEMES["Dark Void (Default)"])
    light = is_light_theme(theme_name)
    accent_hover = adjust_hex_color(t['accent'], 0.90 if light else 1.12)
    accent_pressed = adjust_hex_color(t['accent'], 0.82 if light else 0.86)
    input_hover = adjust_hex_color(t['bg_input'], 0.94 if light else 1.16)
    input_pressed = adjust_hex_color(t['bg_input'], 0.88 if light else 0.88)

    # Pure black/white 10% alpha outline for content images per better-ui
    img_outline = "rgba(0, 0, 0, 0.10)" if light else "rgba(255, 255, 255, 0.10)"

    svg_paths = write_ghub_svgs(
        ICONS_CACHE_DIR, t["accent"], t["text_main"], t["text_sub"], t["bg_main"]
    )
    chevron_down_path = svg_paths["chevron_down.svg"]
    chevron_up_path = svg_paths["chevron_up.svg"]
    check_path = svg_paths["check.svg"]

    return f"""
QMainWindow, QDialog {{
    background-color: {t['bg_main']};
    color: {t['text_main']};
}}

QWidget {{
    font-family: 'Inter', 'Segoe UI', 'Roboto', 'Noto Sans', sans-serif;
    color: {t['text_main']};
}}

QLabel {{
    border: none;
    background: transparent;
    color: {t['text_main']};
    padding: 0px;
}}

QLabel#headerTitle {{
    color: {t['text_main']};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
    border: none;
    background: transparent;
}}

QLabel#headerSubtitle {{
    color: {t['accent']};
    font-size: 12px;
    font-weight: 600;
    border: none;
    background: transparent;
}}

QLabel#drawerTitle {{
    color: {t['text_main']};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.2px;
    padding-bottom: 4px;
}}

QLabel#sectionHeader {{
    color: {t['text_sub']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
    background: transparent;
}}

QLabel#accentTitle {{
    color: {t['text_main']};
    font-size: 12px;
    font-weight: 700;
    border: none;
    background: transparent;
}}

QLabel#valueBadge {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11px;
    font-weight: 700;
}}

QLabel#subText {{
    color: {t['text_sub']};
    font-size: 11px;
    border: none;
    background: transparent;
}}

QLabel#diagramImage {{
    background-color: #000000;
    border: 1px solid {img_outline};
    border-radius: 4px;
    padding: 4px;
}}

/* Top Bar: Flat G HUB dark bar with 1px bottom structural divider */
.QFrame#headerBar {{
    background-color: {t['bg_main']};
    border: none;
    border-bottom: 1px solid {t['border']};
    border-radius: 0px;
}}

/* Left Vertical 48px Icon Rail */
.QFrame#leftRail {{
    background-color: {t['bg_card']};
    border: none;
    border-right: 1px solid {t['border']};
    border-radius: 0px;
}}

/* Left Inspector Panel (380px opaque matte drawer) */
.QFrame#inspectorDrawer {{
    background-color: {t['bg_card']};
    border: none;
    border-right: 1px solid {t['border']};
    border-radius: 0px;
}}

/* 1px Structural Horizontal Divider */
.QFrame#dividerLine {{
    background-color: {t['border']};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

.QFrame#summaryBox {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 8px 10px;
}}

.QFrame#guideBox {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 8px 12px;
}}

/* G HUB Underline Sub-Tabs */
QTabWidget::pane {{
    border: none;
    background: transparent;
    margin-top: 6px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {t['text_sub']};
    padding: 6px 10px 6px 0px;
    margin-right: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.6px;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
}}

QTabBar::tab:hover:!selected {{
    color: {t['text_main']};
}}

QTabBar::tab:selected {{
    color: {t['text_main']};
    border-bottom: 2px solid {t['text_main']};
    font-weight: 700;
}}

/* Unboxed structural sections inside drawer */
QGroupBox {{
    font-weight: 700;
    font-size: 10px;
    border: none;
    border-top: 1px solid {t['border']};
    border-radius: 0px;
    margin-top: 6px;
    padding-top: 22px;
    padding-bottom: 6px;
    padding-left: 0px;
    padding-right: 0px;
    background-color: transparent;
}}

QGroupBox::title {{
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 0px;
    top: 6px;
    padding: 0px;
    color: {t['text_sub']};
    background-color: transparent;
}}

QPushButton {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 7px 14px 7px 12px;
    font-weight: 600;
    font-size: 12px;
}}

QPushButton:!disabled:hover {{
    background-color: {input_hover};
    border-color: {t['accent']};
    color: {t['text_main']};
}}

QPushButton:!disabled:pressed {{
    background-color: {input_pressed};
}}

QPushButton:disabled {{
    background-color: {t['bg_main']};
    color: {t['text_sub']};
    border-color: {t['border']};
}}

QPushButton#btnIcon {{
    padding: 0px;
    font-size: 13px;
    border-radius: 4px;
    background-color: transparent;
    border: 1px solid transparent;
}}

QPushButton#btnIcon:!disabled:hover {{
    background-color: {t['bg_input']};
    border-color: {t['border']};
}}

/* Left Vertical Rail 48x48 Square Icon Buttons */
QPushButton#railBtn {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {t['border']};
    border-radius: 0px;
    padding: 0px;
}}

QPushButton#railBtn:!disabled:hover:!checked {{
    background-color: {t['bg_input']};
}}

QPushButton#railBtn:checked {{
    background-color: {t['accent']};
    border: none;
}}

/* Editorial Divider List Rows (Assignments list in G HUB) */
QPushButton#btnSelector {{
    background-color: transparent;
    color: {t['text_sub']};
    border: none;
    border-bottom: 1px solid {t['border']};
    border-radius: 0px;
    padding: 10px 8px;
    font-size: 12px;
    font-weight: 500;
    text-align: left;
}}

QPushButton#btnSelector:!disabled:hover {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
}}

QPushButton#btnSelector:checked {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
    border-left: 3px solid {t['accent']};
    border-bottom: 1px solid {t['border']};
    padding-left: 9px;
    font-weight: 700;
}}

QPushButton#accentBtn {{
    background-color: {t['accent']};
    color: #000000;
    border: 1px solid {t['accent']};
    border-radius: 4px;
    padding: 7px 14px 7px 12px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.4px;
}}

QPushButton#accentBtn:!disabled:hover {{
    background-color: {accent_hover};
    border-color: {accent_hover};
    color: #000000;
}}

QPushButton#accentBtn:!disabled:pressed {{
    background-color: {accent_pressed};
    border-color: {accent_pressed};
}}

QPushButton#stopBtn {{
    background-color: #27272A;
    color: #F87171;
    border: 1px solid #52525B;
    border-radius: 4px;
    padding: 7px 14px 7px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QPushButton#stopBtn:!disabled:hover {{
    background-color: #3F3F46;
    border-color: #F87171;
    color: #FCA5A5;
}}

/* Horizontal & Vertical Sliders */
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {t['bg_input']};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {t['text_main']};
    border: 2px solid {t['accent']};
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {t['accent']};
}}

QSlider::groove:vertical {{
    border: none;
    width: 4px;
    background: {t['bg_input']};
    border-radius: 2px;
}}

QSlider::add-page:vertical {{
    background: {t['accent']};
    border-radius: 2px;
}}

QSlider::sub-page:vertical {{
    background: {t['bg_input']};
    border-radius: 2px;
}}

QSlider::handle:vertical {{
    background: {t['text_main']};
    border: 2px solid {t['accent']};
    width: 12px;
    height: 12px;
    margin: 0 -5px;
    border-radius: 7px;
}}

QSlider::handle:vertical:hover {{
    background: {t['accent']};
}}

/* Form Inputs: 4px functional radius + custom SVG indicators */
QComboBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 6px 30px 6px 10px;
    color: {t['text_main']};
    font-size: 12px;
    font-weight: 600;
}}

QComboBox:hover {{
    border-color: {t['accent']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: url({chevron_down_path});
    width: 10px;
    height: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {t['bg_card']};
    color: {t['text_main']};
    selection-background-color: {t['accent']};
    selection-color: #000000;
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 2px;
    outline: none;
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 6px 28px 6px 10px;
    color: {t['text_main']};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    font-weight: 600;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {t['accent']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid {t['border']};
    border-bottom: 1px solid {t['border']};
    border-top-right-radius: 4px;
    background: transparent;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border-left: 1px solid {t['border']};
    border-bottom-right-radius: 4px;
    background: transparent;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {input_hover};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url({chevron_up_path});
    width: 10px;
    height: 6px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url({chevron_down_path});
    width: 10px;
    height: 6px;
}}

QCheckBox {{
    spacing: 8px;
    font-size: 12px;
    color: {t['text_main']};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {t['border']};
    background-color: {t['bg_input']};
}}

QCheckBox::indicator:hover {{
    border-color: {t['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {t['accent']};
    border-color: {t['accent']};
    image: url({check_path});
}}

/* Concentric Menu: outer 6px = inner 4px + 2px padding */
QMenu {{
    background-color: {t['bg_card']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 2px;
}}

QMenu::item {{
    padding: 7px 16px 7px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
}}

QMenu::item:selected {{
    background-color: {t['accent']};
    color: #000000;
    font-weight: 700;
}}

QMenu::separator {{
    height: 1px;
    background: {t['border']};
    margin: 4px 6px;
}}

QTextEdit {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 8px;
    color: {t['text_main']};
    font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
    font-size: 11px;
}}

QProgressBar {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 3px;
    height: 10px;
    text-align: center;
    color: {t['text_main']};
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 10px;
}}

QProgressBar::chunk {{
    background-color: {t['accent']};
    border-radius: 2px;
}}

QLabel#statusBadgeActive {{
    background-color: {t['bg_input']};
    color: #10B981;
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 0px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#statusBadgeInactive {{
    background-color: {t['bg_input']};
    color: #F59E0B;
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 0px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#batteryBadge {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 0px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 11px;
}}
"""

ACTION_TYPES = [
    ("Left Click Repeat Loop", "LEFT_CLICK_LOOP"),
    ("Right Click Repeat Loop", "RIGHT_CLICK_LOOP"),
    ("Middle Click Repeat Loop", "MIDDLE_CLICK_LOOP"),
    ("Space Key Repeat Loop", "SPACE_LOOP"),
    ("Win + V Clipboard History", "CLIPBOARD_WIN_V"),
    ("Custom Key Repeat Loop", "CUSTOM_KEY_LOOP"),
    ("Disabled / No Macro", "DISABLED"),
]

CUSTOM_KEYS = [
    ("Space Bar", "KEY_SPACE"),
    ("Key E", "KEY_E"),
    ("Key F", "KEY_F"),
    ("Key Q", "KEY_Q"),
    ("Key R", "KEY_R"),
    ("Key C", "KEY_C"),
    ("Key V", "KEY_V"),
    ("Key X", "KEY_X"),
    ("Key Z", "KEY_Z"),
    ("Left Shift", "KEY_LEFTSHIFT"),
    ("Left Ctrl", "KEY_LEFTCTRL"),
    ("Left Alt", "KEY_LEFTALT"),
    ("Enter", "KEY_ENTER"),
    ("Tab", "KEY_TAB"),
    ("Number 1", "KEY_1"),
    ("Number 2", "KEY_2"),
    ("Number 3", "KEY_3"),
    ("Number 4", "KEY_4"),
    ("Number 5", "KEY_5"),
]

# ------------------ Native Logitech G733 Hardware Driver & Battery Filter ------------------

_last_battery_pct = None
_is_app_querying = False

def find_g733_hidraw():
    for h in glob.glob('/sys/class/hidraw/hidraw*'):
        uevent = os.path.join(h, 'device', 'uevent')
        if os.path.exists(uevent):
            try:
                with open(uevent, 'r') as f:
                    content = f.read()
                    if '046D' in content.upper() and '0AB5' in content.upper():
                        return f"/dev/{os.path.basename(h)}"
            except Exception:
                pass
    return None

def get_g733_battery_info():
    global _last_battery_pct, _is_app_querying
    dev_path = find_g733_hidraw()
    if not dev_path:
        return None, "Disconnected", 0
    
    _is_app_querying = True
    try:
        fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
        req = bytes([0x11, 0xFF, 0x08, 0x00] + [0x00]*16)
        os.write(fd, req)
        
        res = None
        t0 = time.time()
        while time.time() - t0 < 0.15:
            try:
                b = os.read(fd, 64)
                if b and len(b) >= 7 and b[0] == 0x11 and b[2] == 0x08:
                    res = b
                    break
            except BlockingIOError:
                pass
            time.sleep(0.005)

        os.close(fd)
        _is_app_querying = False

        if res:
            mV = (res[4] << 8) | res[5]
            status_code = res[6]
            status_str = "Charging" if status_code == 3 else ("Full" if status_code == 2 else "Discharging")
            
            # Logitech G733 Li-Po discharge curve mapped to 5% G HUB steps
            if mV >= 4120:
                raw_pct = 100
            elif mV >= 4050:
                raw_pct = 95
            elif mV >= 3980:
                raw_pct = 90
            elif mV >= 3920:
                raw_pct = 85
            elif mV >= 3860:
                raw_pct = 80
            elif mV >= 3800:
                raw_pct = 75
            elif mV >= 3750:
                raw_pct = 70
            elif mV >= 3700:
                raw_pct = 60
            elif mV >= 3650:
                raw_pct = 50
            elif mV >= 3600:
                raw_pct = 35
            elif mV >= 3550:
                raw_pct = 20
            else:
                raw_pct = 10

            # Hysteresis Filter: Prevent bouncing up/down from micro voltage drops under load
            if status_str != "Charging":
                if _last_battery_pct is None:
                    _last_battery_pct = raw_pct
                else:
                    if abs(raw_pct - _last_battery_pct) <= 5:
                        pass
                    elif raw_pct < _last_battery_pct:
                        _last_battery_pct = raw_pct
                    elif raw_pct > _last_battery_pct + 5:
                        _last_battery_pct = raw_pct
            else:
                _last_battery_pct = raw_pct

            return _last_battery_pct, status_str, mV
    except Exception as e:
        _is_app_querying = False
        logging.error(f"Error querying G733 battery: {e}")
    return None, "Unknown", 0

def find_ratbag_device_id(keyword="G502"):
    """Dynamically resolves the current ratbagd mammal ID (e.g. 'hooting-chinchilla' or 'thundering-gerbil')."""
    try:
        out = subprocess.check_output(['ratbagctl', 'list'], stderr=subprocess.DEVNULL, timeout=2).decode()
        for line in out.splitlines():
            if ':' in line:
                dev_id, dev_name = [x.strip() for x in line.split(':', 1)]
                if keyword.lower() in dev_name.lower():
                    return dev_id
    except Exception:
        pass
    return None


def set_device_rgb_via_ratbag(keyword, r, g, b, mode=1, brightness=100, zone=None):
    """Applies RGB color, brightness (0-100%), and effect mode to a Logitech device via ratbagctl."""
    dev_id = find_ratbag_device_id(keyword)
    if not dev_id:
        return False
    scale = max(0.0, min(1.0, brightness / 100.0))
    sr = max(0, min(255, int(round(r * scale))))
    sg = max(0, min(255, int(round(g * scale))))
    sb = max(0, min(255, int(round(b * scale))))
    hex_col = f"{sr:02x}{sg:02x}{sb:02x}"
    raw_hex = f"{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"
    zones = [0, 1] if zone is None else [int(zone)]

    try:
        if keyword.upper() == "G502":
            subprocess.run(['ratbagctl', dev_id, 'profile', 'active', 'set', '0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        for z in zones:
            if mode == 0 or brightness <= 0 or (r == 0 and g == 0 and b == 0 and mode != 3):
                cmd = ['ratbagctl', dev_id, 'led', str(z), 'set', 'mode', 'off']
            elif mode == 2:
                cmd = ['ratbagctl', dev_id, 'led', str(z), 'set', 'mode', 'breathing', 'color', raw_hex, 'brightness', str(int(brightness)), 'rate', '2000']
            elif mode == 3:
                cmd = ['ratbagctl', dev_id, 'led', str(z), 'set', 'mode', 'cycle', 'brightness', str(int(brightness)), 'rate', '5000']
            else:
                cmd = ['ratbagctl', dev_id, 'led', str(z), 'set', 'mode', 'on', 'color', hex_col]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return True
    except Exception as e:
        logging.error(f"ratbagctl LED update failed for {keyword}: {e}")
        return False


def set_g502_rgb(r, g, b, mode=1, brightness=100, zone=None):
    """Sets G502 HERO RGB zones (Primary & Logo) with color and brightness."""
    return set_device_rgb_via_ratbag("G502", r, g, b, mode=mode, brightness=brightness, zone=zone)


def set_g733_rgb(r, g, b, mode=1, brightness=100, zone=None):
    """Sets G733 LIGHTSPEED dual-zone RGB via native HID++ 2.0 Feature 0x8070 (COLOR_LED_EFFECTS)."""
    scale = max(0.0, min(1.0, brightness / 100.0))
    r_raw = max(0, min(255, int(r)))
    g_raw = max(0, min(255, int(g)))
    b_raw = max(0, min(255, int(b)))
    sr = max(0, min(255, int(round(r_raw * scale))))
    sg = max(0, min(255, int(round(g_raw * scale))))
    sb = max(0, min(255, int(round(b_raw * scale))))
    bright_byte = max(0, min(100, int(brightness)))

    dev_path = find_g733_hidraw()
    if not dev_path:
        logging.warning("Cannot set G733 RGB via hidraw: device not found")
        return False
    try:
        fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
        # 1. Enable Software RGB Control on Feature 0x8070 (index 0x04, func 8 = 0x80)
        sw_cmd = bytes([0x11, 0xFF, 0x04, 0x80, 0x01, 0x01, 0x00] + [0x00] * 13)
        os.write(fd, sw_cmd)
        time.sleep(0.01)

        # 2. Send setZoneEffect (index 0x04, func 3 = 0x30) to Zones 0 (Upper) and 1 (Lower)
        target_zones = [0, 1] if zone is None else [int(zone)]
        for z in target_zones:
            if mode == 0 or bright_byte <= 0 or (r_raw == 0 and g_raw == 0 and b_raw == 0 and mode != 3):
                cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x00] + [0x00] * 14)
            elif mode == 2:
                # Breathing Pulse: [zone, 0x02, R, G, B, period_hi(0x0B), period_lo(0xB8=3000ms), 0x00, brightness]
                cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x02, r_raw, g_raw, b_raw, 0x0B, 0xB8, 0x00, bright_byte] + [0x00] * 7)
            elif mode == 3:
                # Spectrum Cycle: [zone, 0x03, 0, 0, 0, 0, 0, period_hi(0x13), period_lo(0x88=5000ms), brightness]
                cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x13, 0x88, bright_byte] + [0x00] * 6)
            else:
                # Static Color: [zone, 0x01, sr, sg, sb, 0x02, 0, 0, 0, 0, 0, brightness]
                cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x01, sr, sg, sb, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, bright_byte] + [0x00] * 4)
            os.write(fd, cmd)
            time.sleep(0.01)
        os.close(fd)
        logging.info(f"Targeted G733 Headset RGB set to R={sr} G={sg} B={sb} Brightness={bright_byte}% (Mode {mode})")
        return True
    except Exception as ex:
        logging.error(f"Error setting G733 RGB: {ex}")
        return False

def set_g733_sidetone(val):
    """Sets G733 native hardware sidetone volume percentage (0 - 100%)."""
    dev_path = find_g733_hidraw()
    if not dev_path:
        logging.warning("Cannot set G733 sidetone: hidraw device not found")
        return False
    try:
        # Scale 0-100% to G733 hardware firmware max range (0 - 128 / 0x80)
        hw_val = int((val / 100.0) * 128)
        fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
        cmd = bytes([0x11, 0xFF, 0x07, 0x10, hw_val] + [0x00]*15)
        os.write(fd, cmd)
        os.close(fd)
        logging.info(f"Targeted G733 Native Hardware Sidetone set to {val}% (HW Byte: {hw_val})")
        return True
    except Exception as ex:
        logging.error(f"Error setting G733 Sidetone: {ex}")
        return False

def speak_text(text):
    def _speak():
        try:
            res = subprocess.run(['spd-say', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            if res.returncode != 0:
                subprocess.run(['espeak', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        except Exception:
            try:
                subprocess.run(['espeak', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass
    threading.Thread(target=_speak, daemon=True).start()


class G733PowerButtonListenerThread(QThread):
    speak_battery_signal = pyqtSignal()

    def run(self):
        evdev_devs = []
        for p in evdev.list_devices():
            try:
                d = evdev.InputDevice(p)
                if 'G733' in d.name:
                    evdev_devs.append(d)
            except Exception:
                pass

        epoll = select.epoll()
        dev_map = {}
        for d in evdev_devs:
            epoll.register(d.fd, select.EPOLLIN)
            dev_map[d.fd] = d  # Store actual InputDevice object

        last_speak_time = 0
        while not self.isInterruptionRequested():
            try:
                events = epoll.poll(0.2)
                for fd, event in events:
                    if isinstance(dev_map.get(fd), evdev.InputDevice):
                        try:
                            dev = dev_map[fd]
                            for ev in dev.read():
                                if ev.type == evdev.ecodes.EV_KEY and ev.value == 1:
                                    if time.time() - last_speak_time > 2.0:
                                        last_speak_time = time.time()
                                        self.speak_battery_signal.emit()
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(0.05)


class MicMeterThread(QThread):
    level_signal = pyqtSignal(int)

    def run(self):
        while not self.isInterruptionRequested():
            try:
                source_arg = []
                try:
                    # Prefer G733 microphone source if present, otherwise default source
                    res_list = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True, timeout=1)
                    g733_src = None
                    for line in res_list.stdout.splitlines():
                        parts = line.split()
                        if len(parts) >= 2 and 'G733' in parts[1] and 'input' in parts[1]:
                            g733_src = parts[1]
                            break
                    if g733_src:
                        source_arg = [f'--device={g733_src}']
                    else:
                        res = subprocess.run(['pactl', 'get-default-source'], capture_output=True, text=True, timeout=1)
                        src = res.stdout.strip()
                        if src:
                            source_arg = [f'--device={src}']
                except Exception:
                    pass

                p = subprocess.Popen(
                    ['parec'] + source_arg + ['--latency-msec=20', '--channels=1', '--rate=16000', '--format=s16le', '--raw'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                
                while not self.isInterruptionRequested():
                    raw = p.stdout.read(640)  # 20ms low-latency chunk (320 samples * 2 bytes)
                    if raw:
                        num_samples = len(raw) // 2
                        if num_samples > 0:
                            samples = struct.unpack(f'<{num_samples}h', raw[:num_samples * 2])
                            peak = max(abs(s) for s in samples) if samples else 0
                        else:
                            peak = 0
                        if peak > 25:
                            import math
                            db = 20 * math.log10(peak / 32768.0)
                            pct = max(0, min(100, int((db + 52) * 2.15)))
                        else:
                            pct = 0
                        self.level_signal.emit(pct)
                    else:
                        if p.poll() is not None:
                            break  # parecord died, break to restart
                        time.sleep(0.02)
                try:
                    p.terminate()
                    p.wait(timeout=1)
                except Exception:
                    p.kill()
            except Exception as e:
                logging.error(f"Error in MicMeterThread: {e}")
            
            # If it broke or threw an error, wait a bit before restarting to avoid spin lock
            time.sleep(0.5)


AUTOSTART_DESKTOP_PATH = os.path.expanduser("~/.config/autostart/logitech-control-center.desktop")


def configure_xdg_autostart(enabled, start_minimized=False):
    """Creates or removes the XDG autostart .desktop entry for the application."""
    try:
        if enabled:
            os.makedirs(os.path.dirname(AUTOSTART_DESKTOP_PATH), exist_ok=True)
            script_path = os.path.abspath(__file__)
            exec_cmd = f"/usr/bin/python3 {script_path}" + (" --minimized" if start_minimized else "")
            desktop_content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Logitech G HUB Linux Control Suite\n"
                "Comment=Logitech G502 Mouse & G733 Headset Control Center\n"
                f"Exec={exec_cmd}\n"
                f"Icon={ICON_PATH}\n"
                "Terminal=false\n"
                "Categories=Settings;HardwareSettings;Utility;\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            with open(AUTOSTART_DESKTOP_PATH, "w") as f:
                f.write(desktop_content)
        else:
            if os.path.exists(AUTOSTART_DESKTOP_PATH):
                os.remove(AUTOSTART_DESKTOP_PATH)
        return True
    except Exception as e:
        logging.error(f"Failed to configure XDG autostart: {e}")
        return False


def load_app_settings():
    defaults = {
        "theme": "Dark Void (Default)",
        "minimize_to_tray": True,
        "show_notifications": True,
        "autostart_enabled": os.path.exists(AUTOSTART_DESKTOP_PATH),
        "autostart_minimized": False,
        "active_profile": "Desktop: Default",
        "mouse_rgb": [0, 168, 252],
        "mouse_brightness": 100,
        "mouse_rgb_mode": 1,
        "headset_rgb": [0, 168, 252],
        "headset_brightness": 100,
        "headset_rgb_mode": 1
    }
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except Exception:
            pass
    return defaults

def save_app_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)

def get_all_ratbag_mice():
    mice = []
    try:
        out = subprocess.check_output(['ratbagctl', 'list'], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if ':' in line:
                dev_id, dev_name = [x.strip() for x in line.split(':', 1)]
                try:
                    info = subprocess.check_output(['ratbagctl', dev_id, 'info'], stderr=subprocess.DEVNULL).decode()
                    if 'Number of Buttons: 0' in info:
                        continue
                    buttons = 0
                    profiles = 1
                    for il in info.splitlines():
                        if 'Number of Buttons:' in il:
                            buttons = int(il.split(':')[1].strip())
                        elif 'Number of Profiles:' in il:
                            profiles = int(il.split(':')[1].strip())
                    mice.append({'id': dev_id, 'name': dev_name, 'buttons': buttons, 'profiles': profiles})
                except Exception:
                    pass
    except Exception:
        pass
    return mice


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("G HUB System Settings & Diagnostics")
        self.resize(780, 540)
        self.parent_app = parent
        self.settings = load_app_settings()
        self.setStyleSheet(generate_qss(self.settings.get("theme", "Dark Void (Default)")))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("SETTINGS & SYSTEM DIAGNOSTICS")
        title.setObjectName("drawerTitle")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.tabBar().setUsesScrollButtons(False)
        tabs.addTab(self.create_appearance_tab(), "APPEARANCE")
        tabs.addTab(self.create_diagnostics_tab(), "DIAGNOSTICS")
        tabs.addTab(self.create_tray_tab(), "BEHAVIOR")
        tabs.addTab(self.create_about_tab(), "ABOUT")
        layout.addWidget(tabs)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("CLOSE")
        btn_close.setObjectName("accentBtn")
        btn_close.setFixedHeight(34)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def create_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 12, 4, 4)

        grp = QGroupBox("COLOR PALETTE && SURFACE TOKENS")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        glayout.addWidget(QLabel(f"ACTIVE WORKSPACE PALETTE ({len(THEMES)} PROFILES):"))
        self.combo_theme = QComboBox()
        for tname in THEMES.keys():
            self.combo_theme.addItem(tname)
        
        current_theme = self.settings.get("theme", "Dark Void (Default)")
        idx = self.combo_theme.findText(current_theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)

        self.combo_theme.currentIndexChanged.connect(self.on_theme_changed)
        glayout.addWidget(self.combo_theme)

        theme_info = QLabel("Applies high-contrast monochrome surfaces and single sharp accent tokens across all panels.")
        theme_info.setObjectName("subText")
        glayout.addWidget(theme_info)

        grid_lbl = QLabel("QUICK PRESETS")
        grid_lbl.setObjectName("sectionHeader")
        glayout.addWidget(grid_lbl)

        grid = QGridLayout()
        grid.setSpacing(8)
        featured_themes = [
            "Dark Void (Default)", "Midnight Cyan", "Cyberpunk Neon",
            "Emerald Forest", "Dracula Dark", "Tokyo Night",
            "Nordic Frost", "Synthwave 80s", "Light Pristine"
        ]
        for i, tname in enumerate(featured_themes):
            btn = QPushButton(tname)
            btn.clicked.connect(lambda _, tn=tname: self.combo_theme.setCurrentText(tn))
            grid.addWidget(btn, i // 3, i % 3)
        glayout.addLayout(grid)

        layout.addWidget(grp)
        layout.addStretch()
        return tab

    def on_theme_changed(self, idx):
        theme_name = self.combo_theme.currentText()
        self.settings["theme"] = theme_name
        save_app_settings(self.settings)
        qss = generate_qss(theme_name)
        if self.parent_app:
            self.parent_app.setStyleSheet(qss)
            self.parent_app.refresh_elevation_shadows(theme_name)
        self.setStyleSheet(qss)

    def create_diagnostics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(4, 12, 4, 4)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("SUBSYSTEM TELEMETRY & DRIVER AUDIT:"))
        top_row.addStretch()
        btn_run_diag = QPushButton("RUN HEALTH AUDIT")
        btn_run_diag.clicked.connect(self.run_diagnostics)
        top_row.addWidget(btn_run_diag)
        layout.addLayout(top_row)

        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        layout.addWidget(self.diag_text)

        self.run_diagnostics()
        return tab

    def run_diagnostics(self):
        report = []
        report.append("==================================================")
        report.append(" LOGITECH LINUX CONTROL SUITE HEALTH AUDIT")
        report.append(f" Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("==================================================\n")

        res = subprocess.run(['systemctl', '--user', 'is-active', 'g502-macros.service'], capture_output=True, text=True)
        m_status = res.stdout.strip()
        report.append(f"[Macro Service] g502-macros.service: {'[ACTIVE]' if m_status == 'active' else '[INACTIVE: '+m_status+']'}")

        res = subprocess.run(['systemctl', 'is-active', 'ratbagd.service'], capture_output=True, text=True)
        r_status = res.stdout.strip()
        report.append(f"[Mouse Daemon] ratbagd.service: {'[ACTIVE]' if r_status == 'active' else '[INACTIVE: '+r_status+']'}")

        res = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
        pw_ok = res.returncode == 0
        report.append(f"[Audio Daemon] PipeWire / WirePlumber: {'[ONLINE]' if pw_ok else '[OFFLINE]'}")

        dev_path = find_g733_hidraw()
        pct, b_status, mV = get_g733_battery_info()
        report.append(f"[G733 HID++ Hardware]: {'[CONNECTED: '+dev_path+']' if dev_path else '[DISCONNECTED]'}")
        report.append(f"  - Battery Level: {pct}% ({b_status}, {mV} mV)")

        self.diag_text.setText("\n".join(report))

    def create_tray_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 12, 4, 4)

        grp = QGroupBox("SYSTEM TRAY && BACKGROUND EXECUTION")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        self.chk_tray = QCheckBox("Minimize to System Tray on close when Macro Daemon is active")
        self.chk_tray.setChecked(self.settings.get("minimize_to_tray", True))
        self.chk_tray.toggled.connect(self.on_tray_setting_changed)
        glayout.addWidget(self.chk_tray)

        self.chk_notif = QCheckBox("Show desktop notifications on background state transitions")
        self.chk_notif.setChecked(self.settings.get("show_notifications", True))
        self.chk_notif.toggled.connect(self.on_tray_setting_changed)
        glayout.addWidget(self.chk_notif)

        layout.addWidget(grp)

        auto_grp = QGroupBox("STARTUP && XDG AUTOSTART")
        alayout = QVBoxLayout(auto_grp)
        alayout.setSpacing(12)

        self.chk_autostart = QCheckBox("Launch Logitech G HUB Control Suite automatically on system login")
        self.chk_autostart.setChecked(self.settings.get("autostart_enabled", os.path.exists(AUTOSTART_DESKTOP_PATH)))
        self.chk_autostart.toggled.connect(self.on_tray_setting_changed)
        alayout.addWidget(self.chk_autostart)

        self.chk_autostart_min = QCheckBox("Start minimized in System Tray on login")
        self.chk_autostart_min.setChecked(self.settings.get("autostart_minimized", False))
        self.chk_autostart_min.toggled.connect(self.on_tray_setting_changed)
        alayout.addWidget(self.chk_autostart_min)

        layout.addWidget(auto_grp)
        layout.addStretch()
        return tab

    def on_tray_setting_changed(self):
        self.settings["minimize_to_tray"] = self.chk_tray.isChecked()
        self.settings["show_notifications"] = self.chk_notif.isChecked()
        if hasattr(self, 'chk_autostart'):
            self.settings["autostart_enabled"] = self.chk_autostart.isChecked()
            self.settings["autostart_minimized"] = self.chk_autostart_min.isChecked()
            configure_xdg_autostart(self.chk_autostart.isChecked(), self.chk_autostart_min.isChecked())
        save_app_settings(self.settings)

    def create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 12, 4, 4)

        grp = QGroupBox("APPLICATION SPECIFICATION")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        lbl_app = QLabel("LOGITECH G HUB LINUX CONTROL SUITE v2.7")
        lbl_app.setObjectName("accentTitle")
        glayout.addWidget(lbl_app)

        lbl_desc = QLabel(
            "Native Linux hardware configuration and telemetry interface for Logitech G peripherals:\n"
            "- Evdev/UInput low-latency macro daemon, libratbag onboard DPI & KWin 1:1 px/cm calibration.\n"
            "- G733 LIGHTSPEED 10-band hardware DSP equalizer, microphone gain, and zero-latency sidetone.\n"
            "- Direct HID++ 2.0 dual-zone LIGHTSYNC RGB controller and Li-Po discharge curve telemetry."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setObjectName("subText")
        glayout.addWidget(lbl_desc)

        btn_github = QPushButton("OPEN REPOSITORY (gaxkalik/Logitech-Linux-App)")
        btn_github.setObjectName("accentBtn")
        btn_github.setFixedHeight(36)
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        glayout.addWidget(btn_github)

        layout.addWidget(grp)
        layout.addStretch()
        return tab


class G502ControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logitech G HUB — Linux Control Suite")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1180, 780)

        self.app_settings = load_app_settings()
        current_theme = self.app_settings.get("theme", "Dark Void (Default)")
        self.setStyleSheet(generate_qss(current_theme))

        self.mice_list = get_all_ratbag_mice()
        self.active_button_key = "G8"
        self.gshift_active = False
        self.elevated_cards = []
        self.mouse_rgb_color = tuple(self.app_settings.get("mouse_rgb", [0, 168, 252]))
        self.mouse_brightness = int(self.app_settings.get("mouse_brightness", 100))
        self.headset_rgb_color = tuple(self.app_settings.get("headset_rgb", [0, 168, 252]))
        self.headset_brightness = int(self.app_settings.get("headset_brightness", 100))

        # Create Interactive Hardware Stage & G HUB Home Page early
        self.stage_widget = HardwareStageWidget(DIAGRAM_PATH)
        self.stage_widget.buttonClicked.connect(self.select_button)
        self.stage_widget.deviceTileClicked.connect(lambda idx: self.combo_main_device.setCurrentIndex(idx))
        self.stage_widget.gshiftToggled.connect(self.on_gshift_toggled)
        self.stage_widget.set_mouse_rgb(*self.mouse_rgb_color)
        self.stage_widget.set_headset_rgb(*self.headset_rgb_color)

        self.home_widget = GHubHomeWidget(DIAGRAM_PATH)
        self.home_widget.deviceCardClicked.connect(self.on_home_device_card_clicked)
        self.home_widget.set_mouse_rgb(*self.mouse_rgb_color)
        self.home_widget.set_headset_rgb(*self.headset_rgb_color)

        # Root container (0px margin G HUB full-bleed layout)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top G HUB Header Bar (48px height, 1px bottom structural divider)
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 14, 0)
        header_layout.setSpacing(12)

        self.btn_nav_back = QPushButton()
        self.btn_nav_back.setObjectName("btnIcon")
        self.btn_nav_back.setFixedSize(32, 32)
        nav_back_svg = os.path.join(ICONS_CACHE_DIR, "nav_back.svg")
        if os.path.exists(nav_back_svg):
            self.btn_nav_back.setIcon(QIcon(nav_back_svg))
        else:
            self.btn_nav_back.setText("<")
        self.btn_nav_back.setToolTip("Return to G HUB Home Screen")
        self.btn_nav_back.clicked.connect(self.on_back_button_clicked)
        header_layout.addWidget(self.btn_nav_back)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        subtitle_label = QLabel("ACTIVE PROFILE:")
        subtitle_label.setObjectName("headerSubtitle")
        title_layout.addWidget(subtitle_label)

        self.combo_app_profile = QComboBox()
        self.combo_app_profile.setMinimumWidth(195)
        self.combo_app_profile.setFixedHeight(30)
        self.combo_app_profile.addItems([
            "Desktop: Default",
            "FPS Competitive",
            "MOBA / Action RPG",
            "Media & Productivity"
        ])
        saved_prof = self.app_settings.get("active_profile", "Desktop: Default")
        p_idx = self.combo_app_profile.findText(saved_prof)
        if p_idx >= 0:
            self.combo_app_profile.setCurrentIndex(p_idx)
        self.combo_app_profile.currentIndexChanged.connect(self.on_app_profile_switched)
        title_layout.addWidget(self.combo_app_profile)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Device Selector Dropdown
        self.combo_main_device = QComboBox()
        self.combo_main_device.setMinimumWidth(220)
        self.combo_main_device.setFixedHeight(30)
        self.combo_main_device.addItem("Logitech G502 HERO", "MOUSE")
        self.combo_main_device.addItem("Logitech G733 LIGHTSPEED", "HEADSET")
        self.combo_main_device.currentIndexChanged.connect(self.on_main_device_switched)
        header_layout.addWidget(self.combo_main_device)

        # Wireless Battery Telemetry Badge
        self.lbl_header_battery = QLabel("G733: --%")
        self.lbl_header_battery.setObjectName("batteryBadge")
        self.lbl_header_battery.setFixedHeight(28)
        self.lbl_header_battery.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header_battery.setToolTip("Click to announce battery telemetry via speech synthesis")
        self.lbl_header_battery.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_header_battery.mousePressEvent = lambda ev: self.speak_current_battery()
        header_layout.addWidget(self.lbl_header_battery)

        # Daemon Status Badge + Action Button
        self.status_badge = QLabel("DAEMON: CHECKING")
        self.status_badge.setObjectName("statusBadgeInactive")
        self.status_badge.setFixedHeight(28)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_badge)

        self.btn_toggle_service = QPushButton("START DAEMON")
        self.btn_toggle_service.setObjectName("accentBtn")
        self.btn_toggle_service.setFixedHeight(28)
        self.btn_toggle_service.clicked.connect(self.toggle_service)
        header_layout.addWidget(self.btn_toggle_service)

        btn_settings = QPushButton()
        btn_settings.setObjectName("btnIcon")
        btn_settings.setFixedSize(32, 32)
        nav_gear_svg = os.path.join(ICONS_CACHE_DIR, "nav_gear.svg")
        if os.path.exists(nav_gear_svg):
            btn_settings.setIcon(QIcon(nav_gear_svg))
        else:
            btn_settings.setText("CFG")
        btn_settings.setToolTip("Settings & System Diagnostics")
        btn_settings.clicked.connect(self.open_settings_dialog)
        header_layout.addWidget(btn_settings)

        main_layout.addWidget(header)

        # 2. Root Stack: Page 0 = G HUB Home Screen (Device Grid), Page 1 = Split-View Device Studio
        self.root_stack = QStackedWidget()
        self.root_stack.addWidget(self.home_widget)  # index 0: G HUB Home Page

        self.studio_container = QWidget()
        workspace_layout = QHBoxLayout(self.studio_container)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # 2A. Left Vertical Icon Rail (48px wide)
        self.left_rail = QFrame()
        self.left_rail.setObjectName("leftRail")
        self.left_rail.setFixedWidth(48)
        rail_layout = QVBoxLayout(self.left_rail)
        rail_layout.setContentsMargins(0, 8, 0, 12)
        rail_layout.setSpacing(4)

        self.rail_group = QButtonGroup(self)
        self.rail_group.setExclusive(True)
        self.rail_buttons = []
        self.rail_svg_Prefixes = ["rail_assign", "rail_dpi", "rail_lightsync", "rail_logs"]
        rail_tooltips = [
            "Assignments / Acoustics",
            "Sensitivity (DPI) / Microphone",
            "LIGHTSYNC RGB",
            "Service Telemetry / Hardware Status"
        ]
        for r_idx, (prefix, tip) in enumerate(zip(self.rail_svg_Prefixes, rail_tooltips)):
            rb = QPushButton()
            rb.setObjectName("railBtn")
            rb.setCheckable(True)
            rb.setFixedSize(48, 48)
            rb.setToolTip(tip)
            rb.clicked.connect(lambda _, i=r_idx: self.on_rail_button_clicked(i))
            self.rail_group.addButton(rb, r_idx)
            rail_layout.addWidget(rb)
            self.rail_buttons.append(rb)

        rail_layout.addStretch()
        workspace_layout.addWidget(self.left_rail)

        # 2B. Left Inspector Drawer (405px wide, matte #18181B, no redundant top tab bar)
        self.inspector_drawer = QFrame()
        self.inspector_drawer.setObjectName("inspectorDrawer")
        self.inspector_drawer.setFixedWidth(405)
        drawer_layout = QVBoxLayout(self.inspector_drawer)
        drawer_layout.setContentsMargins(18, 16, 18, 14)
        drawer_layout.setSpacing(10)

        self.lbl_drawer_title = QLabel("Assignments")
        self.lbl_drawer_title.setObjectName("drawerTitle")
        drawer_layout.addWidget(self.lbl_drawer_title)

        self.device_stack = QStackedWidget()

        # Mouse Inspector Tabs (TabBar hidden because left icon rail handles navigation)
        self.mouse_tabs = QTabWidget()
        self.mouse_tabs.tabBar().setUsesScrollButtons(False)
        self.mouse_tabs.tabBar().hide()
        self.mouse_tabs.addTab(self.create_interactive_macro_tab(), "MACROS")
        self.mouse_tabs.addTab(self.create_dashboard_tab(), "SENSITIVITY")
        self.mouse_tabs.addTab(self.create_rgb_tab(), "LIGHTSYNC")
        self.mouse_tabs.addTab(self.create_logs_tab(), "TELEMETRY")
        self.mouse_tabs.currentChanged.connect(self.on_inspector_tab_changed)
        self.device_stack.addWidget(self.mouse_tabs)

        # Headset Inspector Tabs (TabBar hidden because left icon rail handles navigation)
        self.headset_tabs = QTabWidget()
        self.headset_tabs.tabBar().setUsesScrollButtons(False)
        self.headset_tabs.tabBar().hide()
        self.headset_tabs.addTab(self.create_headset_sound_tab(), "ACOUSTICS")
        self.headset_tabs.addTab(self.create_headset_mic_tab(), "MICROPHONE")
        self.headset_tabs.addTab(self.create_headset_rgb_tab(), "LIGHTSYNC")
        self.headset_tabs.addTab(self.create_headset_info_tab(), "HARDWARE")
        self.headset_tabs.currentChanged.connect(self.on_inspector_tab_changed)
        self.device_stack.addWidget(self.headset_tabs)

        drawer_layout.addWidget(self.device_stack)
        workspace_layout.addWidget(self.inspector_drawer)

        # 2C. Right Interactive Hardware Stage (Pure #000000 Obsidian Canvas)
        workspace_layout.addWidget(self.stage_widget, stretch=1)

        self.root_stack.addWidget(self.studio_container)  # index 1: Split-View Device Studio
        self.root_stack.setCurrentIndex(1)  # Start in Device Studio; clicking '<-' opens G HUB Home Page

        main_layout.addWidget(self.root_stack, stretch=1)

        self.sync_rail_and_drawer()
        self.refresh_elevation_shadows(current_theme)

        # System Tray Integration
        self.init_system_tray()

        # Start G733 Power Button Press Listener Thread
        self.listener_thread = G733PowerButtonListenerThread()
        self.listener_thread.speak_battery_signal.connect(self.speak_current_battery)
        self.listener_thread.start()

        # Start Live Microphone Level Meter Thread
        self.mic_meter_thread = MicMeterThread()
        self.mic_meter_thread.level_signal.connect(self.update_mic_meter_level)
        self.mic_meter_thread.start()

        # Status & Battery Refresh Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_refresh)
        self.timer.start(5000)
        self.periodic_refresh()

    def on_back_button_clicked(self):
        """Navigates between the Split-View Device Studio and the Logitech G HUB Home Page."""
        if self.root_stack.currentIndex() == 1:
            self.show_home_page()
        else:
            self.root_stack.setCurrentIndex(1)

    def show_home_page(self):
        """Shows the Logitech G HUB Home Screen with vertical device cards."""
        self.root_stack.setCurrentIndex(0)

    def on_home_device_card_clicked(self, dev_idx, tab_idx=0):
        """Opens the selected device from the G HUB Home Page into the Split-View Studio."""
        self.root_stack.setCurrentIndex(1)
        self.combo_main_device.setCurrentIndex(dev_idx)
        active_tabs = self.mouse_tabs if dev_idx == 0 else self.headset_tabs
        if 0 <= tab_idx < active_tabs.count():
            active_tabs.setCurrentIndex(tab_idx)
        self.sync_rail_and_drawer()

    def on_app_profile_switched(self, idx):
        """Applies the selected persistent profile across DPI, EQ, and LIGHTSYNC."""
        profile_name = self.combo_app_profile.currentText()
        self.app_settings["active_profile"] = profile_name
        save_app_settings(self.app_settings)

        presets = {
            "Desktop: Default": {"dpi": 800, "eq": "Flat 1:1", "rgb": (0, 168, 252)},
            "FPS Competitive": {"dpi": 1200, "eq": "FPS Gaming", "rgb": (239, 68, 68)},
            "MOBA / Action RPG": {"dpi": 1600, "eq": "Bass Boost", "rgb": (16, 185, 129)},
            "Media & Productivity": {"dpi": 1000, "eq": "Cinematic", "rgb": (59, 130, 246)},
        }
        p = presets.get(profile_name, presets["Desktop: Default"])
        if hasattr(self, 'dpi_slider'):
            self.set_dpi(p["dpi"])
        if hasattr(self, 'eq_sliders'):
            self.apply_eq_preset(p["eq"])
        r, g, b = p["rgb"]
        self.apply_mouse_swatch(r, g, b)
        self.apply_headset_swatch(r, g, b)

    def on_rail_button_clicked(self, idx):
        active_tabs = self.mouse_tabs if self.device_stack.currentIndex() == 0 else self.headset_tabs
        if 0 <= idx < active_tabs.count():
            active_tabs.setCurrentIndex(idx)
        self.sync_rail_and_drawer()

    def on_inspector_tab_changed(self, idx):
        self.sync_rail_and_drawer()

    def sync_rail_and_drawer(self):
        dev_idx = self.device_stack.currentIndex()
        active_tabs = self.mouse_tabs if dev_idx == 0 else self.headset_tabs
        tab_idx = active_tabs.currentIndex()

        gshift_suffix = " (G-SHIFT)" if (dev_idx == 0 and getattr(self, 'gshift_active', False)) else ""
        mouse_titles = [f"Assignments{gshift_suffix}", "Sensitivity (DPI)", "LIGHTSYNC", "System Telemetry"]
        headset_titles = ["Acoustics", "Microphone", "LIGHTSYNC", "Hardware Telemetry"]
        titles = mouse_titles if dev_idx == 0 else headset_titles
        if 0 <= tab_idx < len(titles):
            self.lbl_drawer_title.setText(titles[tab_idx])

        for i, rb in enumerate(self.rail_buttons):
            is_active = (i == tab_idx)
            rb.blockSignals(True)
            rb.setChecked(is_active)
            rb.blockSignals(False)
            prefix = self.rail_svg_Prefixes[i]
            svg_name = f"{prefix}_{'active' if is_active else 'idle'}.svg"
            svg_path = os.path.join(ICONS_CACHE_DIR, svg_name)
            if os.path.exists(svg_path):
                rb.setIcon(QIcon(svg_path))

        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_stage_state(
                device_mode=0 if dev_idx == 0 else 1,
                sub_tab_index=tab_idx
            )

    def register_card(self, card_widget):
        self.elevated_cards.append(card_widget)
        return card_widget

    def refresh_elevation_shadows(self, theme_name=None):
        if theme_name is None:
            theme_name = load_app_settings().get("theme", "Dark Void (Default)")
        for card in self.elevated_cards:
            apply_card_elevation(card, theme_name)

    def update_mic_meter_level(self, level):
        if hasattr(self, 'mic_meter'):
            self.mic_meter.setValue(level)

    def periodic_refresh(self):
        self.update_daemon_status()
        self.refresh_battery_status()

    def refresh_battery_status(self):
        pct, status_str, mV = get_g733_battery_info()
        if pct is not None:
            self.lbl_header_battery.setText(f"G733: {pct}% ({status_str.split()[0].upper()})")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText(f"{pct}% ({status_str})")
                self.bar_hs_battery.setValue(pct)
                self.lbl_hs_mv.setText(f"CELL VOLTAGE: {mV} mV (HYSTERESIS 5% STEP)")
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_battery_info(pct, status_str, mV)
            if hasattr(self, 'home_widget'):
                self.home_widget.set_battery_info(pct, status_str)
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip(f"Logitech Linux Control Suite — G733: {pct}% ({status_str})")
        else:
            self.lbl_header_battery.setText("G733: OFFLINE")

    def speak_current_battery(self):
        """Speaks the current battery percentage out loud."""
        pct, status_str, mV = get_g733_battery_info()
        if pct is not None:
            speak_text(f"Battery {pct} percent")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText(f"{pct}% ({status_str}) — ANNOUNCED")
            if hasattr(self, 'lbl_header_battery'):
                self.lbl_header_battery.setText(f"G733: {pct}% (TTS)")
            logging.info(f"Spoken battery announcement triggered: {pct}%")
        else:
            speak_text("Headset disconnected")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText("DISCONNECTED")
            logging.warning("Spoken battery check requested, but G733 headset is offline")

    # ------------------ System Tray Integration ------------------
    def init_system_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            if os.path.exists(ICON_PATH):
                self.tray_icon.setIcon(QIcon(ICON_PATH))
            else:
                self.tray_icon.setIcon(self.windowIcon())

            tray_menu = QMenu(self)

            action_show = QAction("Open G HUB Control Suite", self)
            action_show.triggered.connect(self.restore_from_tray)
            tray_menu.addAction(action_show)

            action_speak_bat = QAction("Announce Battery Charge (%)", self)
            action_speak_bat.triggered.connect(self.speak_current_battery)
            tray_menu.addAction(action_speak_bat)

            self.action_toggle_mic = QAction("Toggle Microphone Mute", self)
            self.action_toggle_mic.triggered.connect(self.toggle_headset_mic)
            tray_menu.addAction(self.action_toggle_mic)

            self.action_toggle_daemon = QAction("Toggle Macro Service", self)
            self.action_toggle_daemon.triggered.connect(self.toggle_service)
            tray_menu.addAction(self.action_toggle_daemon)

            tray_menu.addSeparator()

            action_settings = QAction("Settings & Diagnostics", self)
            action_settings.triggered.connect(self.open_settings_dialog)
            tray_menu.addAction(action_settings)

            action_quit = QAction("Quit Application", self)
            action_quit.triggered.connect(QApplication.quit)
            tray_menu.addAction(action_quit)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.restore_from_tray()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        settings = load_app_settings()
        minimize_pref = settings.get("minimize_to_tray", True)
        res = subprocess.run(['systemctl', '--user', 'is-active', 'g502-macros.service'], capture_output=True, text=True)
        service_active = res.stdout.strip() == 'active'

        if minimize_pref and service_active:
            event.ignore()
            self.hide()
            if settings.get("show_notifications", True) and hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    "Logitech Control Suite",
                    "Application minimized to system tray. Macro daemon remains active in background.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
        else:
            if hasattr(self, 'listener_thread'):
                self.listener_thread.requestInterruption()
                self.listener_thread.wait(500)
            if hasattr(self, 'mic_meter_thread'):
                self.mic_meter_thread.requestInterruption()
                self.mic_meter_thread.wait(500)
            event.accept()

    def show_hamburger_menu(self):
        menu = QMenu(self)
        
        act_mouse = menu.addAction("Switch to G502 HERO Gaming Mouse")
        act_mouse.triggered.connect(lambda: self.combo_main_device.setCurrentIndex(0))
        
        act_headset = menu.addAction("Switch to G733 LIGHTSPEED Headset")
        act_headset.triggered.connect(lambda: self.combo_main_device.setCurrentIndex(1))
        
        menu.addSeparator()
        act_settings = menu.addAction("Settings & System Diagnostics")
        act_settings.triggered.connect(self.open_settings_dialog)

        menu.addSeparator()
        act_speak = menu.addAction("Announce Remaining Battery (%)")
        act_speak.triggered.connect(self.speak_current_battery)

        act_mic = menu.addAction("Toggle Microphone Mute")
        act_mic.triggered.connect(self.toggle_headset_mic)

        act_toggle = menu.addAction("Toggle Background Macro Daemon")
        act_toggle.triggered.connect(self.toggle_service)

        menu.addSeparator()
        act_github = menu.addAction("Open GitHub Repository")
        act_github.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))

        act_quit = menu.addAction("Quit Control Suite")
        act_quit.triggered.connect(QApplication.instance().quit)

        btn = self.sender()
        if btn and isinstance(btn, QWidget):
            menu.exec(btn.mapToGlobal(QPoint(0, btn.height() + 4)))
        else:
            menu.exec(QCursor.pos())

    def open_settings_dialog(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def on_main_device_switched(self, idx):
        self.device_stack.setCurrentIndex(idx)
        self.sync_rail_and_drawer()

    # ------------------ Mouse Customization Tabs ------------------
    def get_selected_ratbag_dev_id(self):
        return find_ratbag_device_id("G502") or "hooting-chinchilla"

    def load_macro_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
        except Exception as ex:
            logging.error(f"Error loading config: {ex}")
        return {
            "buttons": {
                "G8": {"name": "G8 (DPI Up)", "action_type": "LEFT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
                "TILT_LEFT": {"name": "Wheel Tilt Left", "action_type": "LEFT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
                "TILT_RIGHT": {"name": "Wheel Tilt Right", "action_type": "RIGHT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
                "G7": {"name": "G7 (DPI Down)", "action_type": "SPACE_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
                "G9": {"name": "G9 (Profile Select)", "action_type": "CLIPBOARD_WIN_V", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"}
            }
        }

    def create_interactive_macro_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 8, 0, 0)

        config_data = self.load_macro_config()
        self.default_buttons_cfg = config_data.get("buttons", {})
        self.gshift_buttons_cfg = config_data.get("gshift_buttons", {
            "G8": {"name": "G8 (DPI Up)", "action_type": "SPACE_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
            "TILT_LEFT": {"name": "Wheel Tilt Left", "action_type": "MIDDLE_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
            "TILT_RIGHT": {"name": "Wheel Tilt Right", "action_type": "CLIPBOARD_WIN_V", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
            "G7": {"name": "G7 (DPI Down)", "action_type": "CUSTOM_KEY_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_E"},
            "G9": {"name": "G9 (Profile Select)", "action_type": "DISABLED", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"}
        })
        self.buttons_cfg = self.default_buttons_cfg

        # Section 1: Physical Button Selection List (1px structural divider rows)
        hdr_select = QLabel("PHYSICAL INPUT CHANNELS")
        hdr_select.setObjectName("sectionHeader")
        layout.addWidget(hdr_select)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        buttons_list_info = [
            ("G8", "[M]  G8  —  Resolution Up (Top)"),
            ("TILT_LEFT", "[M]  TILT LEFT  —  Wheel Scroll Left"),
            ("TILT_RIGHT", "[M]  TILT RIGHT  —  Wheel Scroll Right"),
            ("G7", "[M]  G7  —  Resolution Down (Index)"),
            ("G9", "[M]  G9  —  Profile Cycle (Center)")
        ]

        self.selector_buttons = {}
        for btn_key, btn_label in buttons_list_info:
            b = QPushButton(btn_label)
            b.setObjectName("btnSelector")
            b.setCheckable(True)
            b.setFixedHeight(32)
            if btn_key == self.active_button_key:
                b.setChecked(True)
            b.clicked.connect(lambda _, k=btn_key: self.select_button(k))
            self.btn_group.addButton(b)
            layout.addWidget(b)
            self.selector_buttons[btn_key] = b

        # Section 2: Macro Action & Timing Parameters
        self.customizer_box = self.register_card(QGroupBox("MACRO SEQUENCE PARAMETERS"))
        customizer_layout = QVBoxLayout(self.customizer_box)
        customizer_layout.setSpacing(8)
        customizer_layout.setContentsMargins(0, 8, 0, 4)

        self.selected_title_lbl = QLabel("CHANNEL: G8 — RESOLUTION UP")
        self.selected_title_lbl.setObjectName("accentTitle")
        customizer_layout.addWidget(self.selected_title_lbl)

        customizer_layout.addWidget(QLabel("ASSIGNED MACRO BEHAVIOR"))
        self.combo_action = QComboBox()
        for label, code in ACTION_TYPES:
            self.combo_action.addItem(label, code)
        self.combo_action.currentIndexChanged.connect(self.on_active_action_changed)
        customizer_layout.addWidget(self.combo_action)

        self.lbl_custom_key = QLabel("KEYCODE BINDING")
        customizer_layout.addWidget(self.lbl_custom_key)
        self.combo_key = QComboBox()
        for label, code in CUSTOM_KEYS:
            self.combo_key.addItem(label, code)
        self.combo_key.currentIndexChanged.connect(self.on_active_field_changed)
        customizer_layout.addWidget(self.combo_key)

        timing_row = QHBoxLayout()
        timing_row.setSpacing(10)

        hold_col = QVBoxLayout()
        hold_col.setSpacing(4)
        hold_col.addWidget(QLabel("HOLD DURATION"))
        self.spin_hold = QSpinBox()
        self.spin_hold.setRange(5, 500)
        self.spin_hold.setSingleStep(5)
        self.spin_hold.setSuffix(" ms")
        self.spin_hold.valueChanged.connect(self.on_active_field_changed)
        hold_col.addWidget(self.spin_hold)
        timing_row.addLayout(hold_col)

        delay_col = QVBoxLayout()
        delay_col.setSpacing(4)
        delay_col.addWidget(QLabel("REPEAT INTERVAL"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(5, 1000)
        self.spin_delay.setSingleStep(5)
        self.spin_delay.setSuffix(" ms")
        self.spin_delay.valueChanged.connect(self.on_active_field_changed)
        delay_col.addWidget(self.spin_delay)
        timing_row.addLayout(delay_col)

        customizer_layout.addLayout(timing_row)

        summary_frame = QFrame()
        summary_frame.setObjectName("summaryBox")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        self.summary_lbl = QLabel("Summary: Holding G8 will repeat Left Click.")
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setObjectName("subText")
        summary_layout.addWidget(self.summary_lbl)
        customizer_layout.addWidget(summary_frame)

        layout.addWidget(self.customizer_box)
        layout.addStretch()

        btn_save = QPushButton("SAVE && COMMIT TO DAEMON")
        btn_save.setObjectName("accentBtn")
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self.save_macro_config)
        layout.addWidget(btn_save)

        self.select_button("G8")
        return tab

    def select_button(self, btn_key):
        self.active_button_key = btn_key
        if hasattr(self, 'selector_buttons') and btn_key in self.selector_buttons:
            self.selector_buttons[btn_key].blockSignals(True)
            self.selector_buttons[btn_key].setChecked(True)
            self.selector_buttons[btn_key].blockSignals(False)

        btn_titles = {
            "G8": "G8 — RESOLUTION UP",
            "TILT_LEFT": "TILT LEFT — SCROLL LEFT",
            "TILT_RIGHT": "TILT RIGHT — SCROLL RIGHT",
            "G7": "G7 — RESOLUTION DOWN",
            "G9": "G9 — PROFILE CYCLE"
        }
        layer_tag = " [G-SHIFT]" if getattr(self, "gshift_active", False) else ""
        self.selected_title_lbl.setText(f"CHANNEL: {btn_titles.get(btn_key, btn_key)}{layer_tag}")

        btn_data = self.buttons_cfg.get(btn_key, {})
        action_type = btn_data.get("action_type", "LEFT_CLICK_LOOP")
        custom_key = btn_data.get("custom_key", "KEY_SPACE")
        hold_ms = btn_data.get("hold_ms", 20)
        delay_ms = btn_data.get("delay_ms", 50)

        self.combo_action.blockSignals(True)
        self.combo_key.blockSignals(True)
        self.spin_hold.blockSignals(True)
        self.spin_delay.blockSignals(True)

        for idx in range(self.combo_action.count()):
            if self.combo_action.itemData(idx) == action_type:
                self.combo_action.setCurrentIndex(idx)
                break

        for idx in range(self.combo_key.count()):
            if self.combo_key.itemData(idx) == custom_key:
                self.combo_key.setCurrentIndex(idx)
                break

        self.spin_hold.setValue(hold_ms)
        self.spin_delay.setValue(delay_ms)

        self.combo_action.blockSignals(False)
        self.combo_key.blockSignals(False)
        self.spin_hold.blockSignals(False)
        self.spin_delay.blockSignals(False)

        self.on_active_action_changed()

    def on_active_action_changed(self):
        is_custom = (self.combo_action.currentData() == "CUSTOM_KEY_LOOP")
        self.lbl_custom_key.setVisible(is_custom)
        self.combo_key.setVisible(is_custom)
        self.on_active_field_changed()

    def on_active_field_changed(self):
        btn_key = self.active_button_key
        action_code = self.combo_action.currentData()
        action_text = self.combo_action.currentText()
        key_code = self.combo_key.currentData()
        key_text = self.combo_key.currentText()
        hold_ms = self.spin_hold.value()
        delay_ms = self.spin_delay.value()

        self.buttons_cfg[btn_key] = {
            "name": btn_key,
            "action_type": action_code,
            "hold_ms": hold_ms,
            "delay_ms": delay_ms,
            "custom_key": key_code
        }

        if action_code == "CUSTOM_KEY_LOOP":
            self.summary_lbl.setText(f"Summary: Holding {btn_key} will repeat key [{key_text}] ({hold_ms}ms hold / {delay_ms}ms delay).")
        elif action_code == "CLIPBOARD_WIN_V":
            self.summary_lbl.setText(f"Summary: Pressing {btn_key} will open Win + V Clipboard History.")
        elif action_code == "DISABLED":
            self.summary_lbl.setText(f"Summary: {btn_key} macro is disabled.")
        else:
            self.summary_lbl.setText(f"Summary: Holding {btn_key} will repeat {action_text} ({hold_ms}ms hold / {delay_ms}ms delay).")

        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_state(
                self.active_button_key,
                self.buttons_cfg,
                getattr(self, 'dpi_slider', None).value() if hasattr(self, 'dpi_slider') else 800
            )

    def on_gshift_toggled(self, active):
        """Switches active macro mapping layer between DEFAULT and G-SHIFT."""
        self.gshift_active = bool(active)
        self.buttons_cfg = self.gshift_buttons_cfg if self.gshift_active else self.default_buttons_cfg
        self.sync_rail_and_drawer()
        self.select_button(self.active_button_key)

    def save_macro_config(self):
        new_cfg = {
            "buttons": self.default_buttons_cfg,
            "gshift_buttons": getattr(self, 'gshift_buttons_cfg', {}),
            "active_layer": "G-SHIFT" if getattr(self, 'gshift_active', False) else "DEFAULT"
        }
        if getattr(self, 'gshift_active', False):
            # When G-SHIFT is active and saved, deploy G-SHIFT bindings to active daemon buttons
            new_cfg["buttons"] = self.gshift_buttons_cfg
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(new_cfg, f, indent=4)

        subprocess.run(['systemctl', '--user', 'restart', 'g502-macros.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.update_daemon_status()
        self.refresh_logs()
        QMessageBox.information(self, "Macro Studio", "Macro settings saved! Service automatically restarted.")

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        dpi_group = self.register_card(QGroupBox("ONBOARD SENSOR RESOLUTION (DPI)"))
        dpi_layout = QVBoxLayout(dpi_group)
        dpi_layout.setSpacing(8)
        dpi_layout.setContentsMargins(0, 8, 0, 6)

        dpi_top_layout = QHBoxLayout()
        dpi_label = QLabel("ACTIVE SENSOR DPI")
        self.dpi_val_label = QLabel("800 DPI")
        self.dpi_val_label.setObjectName("valueBadge")
        dpi_top_layout.addWidget(dpi_label)
        dpi_top_layout.addStretch()
        dpi_top_layout.addWidget(self.dpi_val_label)
        dpi_layout.addLayout(dpi_top_layout)

        self.dpi_slider = QSlider(Qt.Orientation.Horizontal)
        self.dpi_slider.setRange(400, 4000)
        self.dpi_slider.setSingleStep(50)
        self.dpi_slider.setValue(800)
        self.dpi_slider.valueChanged.connect(self.on_dpi_slider_changed)
        dpi_layout.addWidget(self.dpi_slider)

        preset_grid = QGridLayout()
        preset_grid.setSpacing(6)
        for i, dpi in enumerate([400, 800, 1000, 1200, 1600, 2400, 3200]):
            btn = QPushButton(f"{dpi}")
            btn.clicked.connect(lambda _, d=dpi: self.set_dpi(d))
            preset_grid.addWidget(btn, i // 4, i % 4)
        dpi_layout.addLayout(preset_grid)

        layout.addWidget(dpi_group)

        speed_group = self.register_card(QGroupBox("LIBINPUT / KWIN POINTER SCALING"))
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.setSpacing(8)
        speed_layout.setContentsMargins(0, 8, 0, 6)

        speed_layout.addWidget(QLabel("ACCELERATION PROFILE"))
        self.combo_profile = QComboBox()
        self.combo_profile.addItems(["Flat (1:1 Raw Linear)", "Adaptive (Velocity Curve)"])
        self.combo_profile.currentIndexChanged.connect(self.on_accel_profile_changed)
        speed_layout.addWidget(self.combo_profile)

        speed_slider_layout = QHBoxLayout()
        speed_slider_layout.addWidget(QLabel("SCALING MULTIPLIER"))
        speed_slider_layout.addStretch()
        self.speed_val_label = QLabel("0.600")
        self.speed_val_label.setObjectName("valueBadge")
        speed_slider_layout.addWidget(self.speed_val_label)
        speed_layout.addLayout(speed_slider_layout)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(-100, 100)
        self.speed_slider.setValue(60)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)

        layout.addWidget(speed_group)
        
        calib_group = self.register_card(QGroupBox("1:1 PHYSICAL DISPLACEMENT CALIBRATION"))
        calib_layout = QVBoxLayout(calib_group)
        calib_layout.setSpacing(8)
        calib_layout.setContentsMargins(0, 8, 0, 6)

        calib_row = QHBoxLayout()
        calib_row.addWidget(QLabel("TARGET RATIO:"))
        self.spin_px_cm = QDoubleSpinBox()
        self.spin_px_cm.setRange(10.0, 5000.0)
        self.spin_px_cm.setDecimals(2)
        self.spin_px_cm.setValue(265.72)
        self.spin_px_cm.setSuffix(" px/cm")
        calib_row.addWidget(self.spin_px_cm)
        calib_layout.addLayout(calib_row)
        
        btn_calib = QPushButton("APPLY EXACT 1:1 CALIBRATION")
        btn_calib.setObjectName("accentBtn")
        btn_calib.setFixedHeight(34)
        btn_calib.clicked.connect(self.apply_exact_calibration)
        calib_layout.addWidget(btn_calib)
        
        calib_help = QLabel("Sets sensor to 1000 DPI and computes the exact flat libinput scalar to match physical Windows displacement.")
        calib_help.setObjectName("subText")
        calib_help.setWordWrap(True)
        calib_layout.addWidget(calib_help)
        
        layout.addWidget(calib_group)
        layout.addStretch()
        return tab

    def create_rgb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        rgb_group = self.register_card(QGroupBox("G502 LIGHTSYNC CALIBRATION && ZONES"))
        rgb_layout = QVBoxLayout(rgb_group)
        rgb_layout.setSpacing(10)
        rgb_layout.setContentsMargins(0, 8, 0, 6)

        lbl_info = QLabel("Direct hardware RGB color and brightness calibration for G502 DPI & G-Logo zones:")
        lbl_info.setWordWrap(True)
        lbl_info.setObjectName("subText")
        rgb_layout.addWidget(lbl_info)

        rgb_layout.addWidget(QLabel("TARGET LIGHTING ZONE"))
        self.combo_mouse_zone = QComboBox()
        self.combo_mouse_zone.addItem("All Zones (DPI + G Logo)", None)
        self.combo_mouse_zone.addItem("Zone 0 — DPI Indicator", 0)
        self.combo_mouse_zone.addItem("Zone 1 — G502 Emblem Logo", 1)
        self.combo_mouse_zone.currentIndexChanged.connect(self.on_mouse_rgb_params_changed)
        rgb_layout.addWidget(self.combo_mouse_zone)

        rgb_layout.addWidget(QLabel("LIGHTING EFFECT MODE"))
        self.combo_mouse_effect = QComboBox()
        self.combo_mouse_effect.addItem("Static Color", 1)
        self.combo_mouse_effect.addItem("Breathing Pulse", 2)
        self.combo_mouse_effect.addItem("Spectrum Cycle", 3)
        self.combo_mouse_effect.addItem("Stealth (LEDs OFF)", 0)
        self.combo_mouse_effect.currentIndexChanged.connect(self.on_mouse_rgb_params_changed)
        rgb_layout.addWidget(self.combo_mouse_effect)

        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("LED BRIGHTNESS"))
        r, g, b = self.mouse_rgb_color
        self.lbl_mouse_brightness = QLabel(f"{self.mouse_brightness}%")
        self.lbl_mouse_brightness.setObjectName("valueBadge")
        b_row.addStretch()
        b_row.addWidget(self.lbl_mouse_brightness)
        rgb_layout.addLayout(b_row)

        self.mouse_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.mouse_brightness_slider.setRange(0, 100)
        self.mouse_brightness_slider.setValue(self.mouse_brightness)
        self.mouse_brightness_slider.valueChanged.connect(self.on_mouse_brightness_changed)
        rgb_layout.addWidget(self.mouse_brightness_slider)

        col_row = QHBoxLayout()
        self.lbl_mouse_color_hex = QLabel(f"COLOR: #{r:02X}{g:02X}{b:02X}")
        self.lbl_mouse_color_hex.setObjectName("valueBadge")
        col_row.addWidget(self.lbl_mouse_color_hex)
        btn_pick_mouse = QPushButton("CHOOSE CUSTOM COLOR...")
        btn_pick_mouse.setObjectName("accentBtn")
        btn_pick_mouse.setFixedHeight(34)
        btn_pick_mouse.clicked.connect(self.choose_mouse_rgb_color)
        col_row.addWidget(btn_pick_mouse, stretch=1)
        rgb_layout.addLayout(col_row)

        rgb_layout.addWidget(QLabel("PRESET SWATCHES"))
        m_grid = QGridLayout()
        m_grid.setSpacing(6)
        m_swatches = [
            ("Cyan", 0, 168, 252),
            ("Cobalt", 59, 130, 246),
            ("Emerald", 16, 185, 129),
            ("Crimson", 239, 68, 68),
            ("Amber", 245, 158, 11),
            ("Stealth OFF", 0, 0, 0)
        ]
        for idx_c, (cname, cr, cg, cb) in enumerate(m_swatches):
            btn = QPushButton(cname)
            btn.clicked.connect(lambda _, r0=cr, g0=cg, b0=cb: self.apply_mouse_swatch(r0, g0, b0))
            m_grid.addWidget(btn, idx_c // 3, idx_c % 3)
        rgb_layout.addLayout(m_grid)

        btn_apply_black = QPushButton("APPLY GLOBAL STEALTH (ALL LEDS OFF)")
        btn_apply_black.setFixedHeight(34)
        btn_apply_black.clicked.connect(self.apply_all_black_rgb)
        rgb_layout.addWidget(btn_apply_black)

        layout.addWidget(rgb_group)
        layout.addStretch()
        return tab

    def apply_mouse_swatch(self, r, g, b):
        self.mouse_rgb_color = (r, g, b)
        if hasattr(self, 'lbl_mouse_color_hex'):
            self.lbl_mouse_color_hex.setText(f"COLOR: #{r:02X}{g:02X}{b:02X}")
        mode = 0 if (r == 0 and g == 0 and b == 0) else (self.combo_mouse_effect.currentData() if hasattr(self, 'combo_mouse_effect') else 1)
        if mode == 0 and (r or g or b):
            mode = 1
        zone = self.combo_mouse_zone.currentData() if hasattr(self, 'combo_mouse_zone') else None
        set_g502_rgb(r, g, b, mode=mode, brightness=self.mouse_brightness, zone=zone)
        scale = self.mouse_brightness / 100.0
        vr, vg, vb = int(r * scale), int(g * scale), int(b * scale)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_rgb(vr, vg, vb)
        if hasattr(self, 'home_widget'):
            self.home_widget.set_mouse_rgb(vr, vg, vb)
        self.app_settings["mouse_rgb"] = [r, g, b]
        save_app_settings(self.app_settings)

    def on_mouse_brightness_changed(self, val):
        self.mouse_brightness = int(val)
        self.lbl_mouse_brightness.setText(f"{val}%")
        self.app_settings["mouse_brightness"] = self.mouse_brightness
        r, g, b = self.mouse_rgb_color
        scale = self.mouse_brightness / 100.0
        vr, vg, vb = int(r * scale), int(g * scale), int(b * scale)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_rgb(vr, vg, vb)
        if hasattr(self, 'home_widget'):
            self.home_widget.set_mouse_rgb(vr, vg, vb)
        if not hasattr(self, '_mouse_rgb_timer'):
            self._mouse_rgb_timer = QTimer(self)
            self._mouse_rgb_timer.setSingleShot(True)
            self._mouse_rgb_timer.timeout.connect(self.on_mouse_rgb_params_changed)
        self._mouse_rgb_timer.start(80)

    def on_mouse_rgb_params_changed(self, *_):
        r, g, b = self.mouse_rgb_color
        mode = self.combo_mouse_effect.currentData() if hasattr(self, 'combo_mouse_effect') else 1
        zone = self.combo_mouse_zone.currentData() if hasattr(self, 'combo_mouse_zone') else None
        if mode == 0:
            set_g502_rgb(0, 0, 0, mode=0, brightness=0, zone=zone)
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_mouse_rgb(0, 0, 0)
        else:
            set_g502_rgb(r, g, b, mode=mode, brightness=self.mouse_brightness, zone=zone)
            scale = self.mouse_brightness / 100.0
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_mouse_rgb(int(r * scale), int(g * scale), int(b * scale))
        save_app_settings(self.app_settings)

    def choose_mouse_rgb_color(self):
        r, g, b = self.mouse_rgb_color
        color = QColorDialog.getColor(QColor(r, g, b), self, "Select G502 LIGHTSYNC RGB Color")
        if color.isValid():
            self.apply_mouse_swatch(color.red(), color.green(), color.blue())

    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 8, 0, 0)

        top_layout = QHBoxLayout()
        lbl_hdr = QLabel("SYSTEMD DAEMON JOURNAL")
        lbl_hdr.setObjectName("sectionHeader")
        top_layout.addWidget(lbl_hdr)
        top_layout.addStretch()

        btn_refresh = QPushButton("REFRESH")
        btn_refresh.clicked.connect(self.refresh_logs)
        top_layout.addWidget(btn_refresh)
        layout.addLayout(top_layout)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.refresh_logs()
        return tab

    # ------------------ Headset Customization Tabs ------------------
    def create_headset_sound_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        vol_group = self.register_card(QGroupBox("MASTER ACOUSTIC OUTPUT"))
        vlayout = QVBoxLayout(vol_group)
        vlayout.setSpacing(8)
        vlayout.setContentsMargins(0, 8, 0, 6)

        v_top = QHBoxLayout()
        v_top.addWidget(QLabel("OUTPUT GAIN"))
        self.lbl_hs_vol = QLabel("56%")
        self.lbl_hs_vol.setObjectName("valueBadge")
        v_top.addWidget(self.lbl_hs_vol)
        v_top.addStretch()
        
        self.btn_hs_mute = QPushButton("MUTE OUTPUT")
        self.btn_hs_mute.clicked.connect(self.toggle_headset_audio_mute)
        v_top.addWidget(self.btn_hs_mute)

        vlayout.addLayout(v_top)

        self.hs_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.hs_vol_slider.setRange(0, 100)
        self.hs_vol_slider.setValue(56)
        self.hs_vol_slider.valueChanged.connect(self.on_hs_vol_changed)
        vlayout.addWidget(self.hs_vol_slider)

        layout.addWidget(vol_group)

        eq_group = self.register_card(QGroupBox("10-BAND HARDWARE DSP EQUALIZER"))
        eq_layout = QVBoxLayout(eq_group)
        eq_layout.setSpacing(10)
        eq_layout.setContentsMargins(0, 8, 0, 6)

        preset_grid = QGridLayout()
        preset_grid.setSpacing(6)
        for idx_p, preset_name in enumerate(["Flat 1:1", "FPS Gaming", "Bass Boost", "Cinematic"]):
            btn = QPushButton(preset_name)
            btn.clicked.connect(lambda _, p=preset_name: self.apply_eq_preset(p))
            preset_grid.addWidget(btn, idx_p // 2, idx_p % 2)
        eq_layout.addLayout(preset_grid)

        bands_layout = QHBoxLayout()
        bands = [("60Hz\nSUB", 0), ("250Hz\nLOW", 0), ("1kHz\nMID", 0), ("4kHz\nHIGH", 0), ("12kHz\nAIR", 0)]
        self.eq_sliders = []
        for name, def_val in bands:
            bcol = QVBoxLayout()
            bcol.setSpacing(6)
            lbl_name = QLabel(name)
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_name.setObjectName("subText")
            bcol.addWidget(lbl_name, alignment=Qt.AlignmentFlag.AlignCenter)
            sl = QSlider(Qt.Orientation.Vertical)
            sl.setRange(-12, 12)
            sl.setValue(def_val)
            sl.setFixedHeight(140)
            bcol.addWidget(sl, alignment=Qt.AlignmentFlag.AlignCenter)
            lbl_val = QLabel("0 dB")
            lbl_val.setObjectName("valueBadge")
            sl.valueChanged.connect(lambda v, l=lbl_val: l.setText(f"{v:+d} dB"))
            sl.valueChanged.connect(self.on_eq_changed)
            bcol.addWidget(lbl_val, alignment=Qt.AlignmentFlag.AlignCenter)
            bands_layout.addLayout(bcol)
            self.eq_sliders.append(sl)

        eq_layout.addLayout(bands_layout)
        layout.addWidget(eq_group)
        layout.addStretch()
        
        QTimer.singleShot(500, self.on_eq_changed)
        return tab

    def on_eq_changed(self):
        try:
            v = [sl.value() for sl in self.eq_sliders]
            if len(v) != 5:
                return

            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_eq_bands(v)

            bands_10 = [
                v[0],
                v[0],
                (v[0]+v[1])//2,
                v[1],
                (v[1]+v[2])//2,
                v[2],
                (v[2]+v[3])//2,
                v[3],
                (v[3]+v[4])//2,
                v[4],
            ]
            bands_10_bytes = [(x + 256) % 256 for x in bands_10]
            
            def _send_eq():
                dev_path = find_g733_hidraw()
                if not dev_path:
                    return
                try:
                    fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
                    os.write(fd, bytes([0x11, 0xFF, 0x00, 0x10, 0x83, 0x10] + [0]*14))
                    import select
                    r, _, _ = select.select([fd], [], [], 0.5)
                    eq_idx = 0
                    if r:
                        while True:
                            try:
                                res = os.read(fd, 20)
                                if res and res[0] == 0x11 and res[2] == 0x00 and res[3] == 0x10:
                                    eq_idx = res[4]
                                    break
                            except BlockingIOError:
                                break
                    if eq_idx != 0:
                        cmd = bytes([0x11, 0xFF, eq_idx, 0x20] + bands_10_bytes + [0]*(16 - len(bands_10_bytes)))
                        os.write(fd, cmd)
                        logging.info(f"Set G733 native hardware Equalizer: {bands_10}")
                    os.close(fd)
                except Exception as e:
                    logging.error(f"Error setting EQ: {e}")
            
            threading.Thread(target=_send_eq, daemon=True).start()
        except Exception as ex:
            logging.error(f"Failed to process eq changed: {ex}")

    def on_hs_vol_changed(self, val):
        self.lbl_hs_vol.setText(f"{val}%")
        vol_float = val / 100.0
        subprocess.run(['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f"{vol_float:.2f}"], stdout=subprocess.DEVNULL)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_audio_telemetry(
                val,
                self.mic_vol_slider.value() if hasattr(self, 'mic_vol_slider') else 100,
                self.side_slider.value() if hasattr(self, 'side_slider') else 30,
                "MUTED" in self.btn_mic_mute.text() if hasattr(self, 'btn_mic_mute') else False
            )

    def toggle_headset_audio_mute(self):
        subprocess.run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle'], stdout=subprocess.DEVNULL)

    def apply_eq_preset(self, preset):
        values = {
            "Flat 1:1": [0, 0, 0, 0, 0],
            "FPS Gaming": [-2, 3, 5, 4, 2],
            "Bass Boost": [6, 4, 1, 0, 1],
            "Cinematic": [4, 2, -1, 3, 5]
        }
        vals = values.get(preset, [0, 0, 0, 0, 0])
        for sl, v in zip(self.eq_sliders, vals):
            sl.setValue(v)

    def create_headset_mic_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        mic_group = self.register_card(QGroupBox("MICROPHONE INPUT GAIN && STATE"))
        mlayout = QVBoxLayout(mic_group)
        mlayout.setSpacing(8)
        mlayout.setContentsMargins(0, 8, 0, 6)

        m_top = QHBoxLayout()
        m_top.addWidget(QLabel("INPUT GAIN"))
        self.lbl_mic_vol = QLabel("100%")
        self.lbl_mic_vol.setObjectName("valueBadge")
        m_top.addWidget(self.lbl_mic_vol)
        m_top.addStretch()

        self.btn_mic_mute = QPushButton("MIC: LIVE")
        self.btn_mic_mute.setObjectName("accentBtn")
        self.btn_mic_mute.clicked.connect(self.toggle_headset_mic)
        m_top.addWidget(self.btn_mic_mute)

        mlayout.addLayout(m_top)

        self.mic_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.mic_vol_slider.setRange(0, 100)
        self.mic_vol_slider.setValue(100)
        self.mic_vol_slider.valueChanged.connect(self.on_mic_vol_changed)
        mlayout.addWidget(self.mic_vol_slider)

        layout.addWidget(mic_group)

        side_group = self.register_card(QGroupBox("HARDWARE SIDETONE MONITORING"))
        slayout = QVBoxLayout(side_group)
        slayout.setSpacing(8)
        slayout.setContentsMargins(0, 8, 0, 6)

        s_top = QHBoxLayout()
        s_top.addWidget(QLabel("SIDETONE LEVEL"))
        self.lbl_sidetone = QLabel("30%")
        self.lbl_sidetone.setObjectName("valueBadge")
        s_top.addWidget(self.lbl_sidetone)
        s_top.addStretch()
        slayout.addLayout(s_top)

        self.side_slider = QSlider(Qt.Orientation.Horizontal)
        self.side_slider.setRange(0, 100)
        self.side_slider.setValue(30)
        self.side_slider.valueChanged.connect(self.on_sidetone_changed)
        slayout.addWidget(self.side_slider)

        side_hint = QLabel("Zero-latency hardware loopback routed directly inside the G733 DSP.")
        side_hint.setWordWrap(True)
        side_hint.setObjectName("subText")
        slayout.addWidget(side_hint)
        layout.addWidget(side_group)

        meter_group = self.register_card(QGroupBox("REAL-TIME INPUT PEAK METER (dBFS)"))
        meter_layout = QVBoxLayout(meter_group)
        meter_layout.setSpacing(8)
        meter_layout.setContentsMargins(0, 8, 0, 6)
        self.mic_meter = QProgressBar()
        self.mic_meter.setRange(0, 100)
        self.mic_meter.setValue(0)
        self.mic_meter.setTextVisible(False)
        self.mic_meter.setObjectName("micMeter")
        meter_layout.addWidget(self.mic_meter)
        layout.addWidget(meter_group)

        layout.addStretch()
        return tab

    def on_mic_vol_changed(self, val):
        self.lbl_mic_vol.setText(f"{val}%")
        vol_float = val / 100.0
        subprocess.run(['wpctl', 'set-volume', '@DEFAULT_AUDIO_SOURCE@', f"{vol_float:.2f}"], stdout=subprocess.DEVNULL)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_audio_telemetry(
                self.hs_vol_slider.value() if hasattr(self, 'hs_vol_slider') else 56,
                val,
                self.side_slider.value() if hasattr(self, 'side_slider') else 30,
                "MUTED" in self.btn_mic_mute.text() if hasattr(self, 'btn_mic_mute') else False
            )

    def toggle_headset_mic(self):
        subprocess.run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SOURCE@', 'toggle'], stdout=subprocess.DEVNULL)
        res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], capture_output=True, text=True)
        is_muted = '[MUTED]' in res.stdout
        if is_muted:
            self.btn_mic_mute.setText("MIC: MUTED")
            self.btn_mic_mute.setObjectName("stopBtn")
        else:
            self.btn_mic_mute.setText("MIC: LIVE")
            self.btn_mic_mute.setObjectName("accentBtn")
        self.btn_mic_mute.setStyle(self.btn_mic_mute.style())
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_audio_telemetry(
                self.hs_vol_slider.value() if hasattr(self, 'hs_vol_slider') else 56,
                self.mic_vol_slider.value() if hasattr(self, 'mic_vol_slider') else 100,
                self.side_slider.value() if hasattr(self, 'side_slider') else 30,
                is_muted
            )

    def on_sidetone_changed(self, val):
        self.lbl_sidetone.setText(f"{val}%")
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_audio_telemetry(
                self.hs_vol_slider.value() if hasattr(self, 'hs_vol_slider') else 56,
                self.mic_vol_slider.value() if hasattr(self, 'mic_vol_slider') else 100,
                val,
                "MUTED" in self.btn_mic_mute.text() if hasattr(self, 'btn_mic_mute') else False
            )
        try:
            if not hasattr(self, 'sidetone_timer'):
                self.sidetone_timer = QTimer(self)
                self.sidetone_timer.setSingleShot(True)
                self.sidetone_timer.timeout.connect(lambda: set_g733_sidetone(self.side_slider.value()))
            self.sidetone_timer.start(50)
        except Exception as e:
            logging.error(f"Error in on_sidetone_changed: {e}")

    # ------------------ Targeted Headset RGB Tab ------------------
    def create_headset_rgb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        rgb_group = self.register_card(QGroupBox("DUAL-ZONE LIGHTSYNC CONTROLLER (HID++ / RATBAG)"))
        rlayout = QVBoxLayout(rgb_group)
        rlayout.setSpacing(10)
        rlayout.setContentsMargins(0, 8, 0, 6)

        lbl_rgb_desc = QLabel("Standalone color and brightness calibration for upper and lower G733 front lightstrips:")
        lbl_rgb_desc.setWordWrap(True)
        lbl_rgb_desc.setObjectName("subText")
        rlayout.addWidget(lbl_rgb_desc)

        rlayout.addWidget(QLabel("TARGET LIGHTSTRIP ZONE"))
        self.combo_hs_zone = QComboBox()
        self.combo_hs_zone.addItem("All Zones (Upper + Lower Strips)", None)
        self.combo_hs_zone.addItem("Zone 0 — Upper Lightstrip", 0)
        self.combo_hs_zone.addItem("Zone 1 — Lower Lightstrip", 1)
        self.combo_hs_zone.currentIndexChanged.connect(self.on_hs_effect_changed)
        rlayout.addWidget(self.combo_hs_zone)

        rlayout.addWidget(QLabel("LIGHTING EFFECT MODE"))
        self.combo_hs_effect = QComboBox()
        self.combo_hs_effect.addItem("Static Color", 1)
        self.combo_hs_effect.addItem("Breathing Pulse", 2)
        self.combo_hs_effect.addItem("Spectrum Cycle", 3)
        self.combo_hs_effect.addItem("Stealth (LEDs OFF)", 0)
        self.combo_hs_effect.currentIndexChanged.connect(self.on_hs_effect_changed)
        rlayout.addWidget(self.combo_hs_effect)

        hb_row = QHBoxLayout()
        hb_row.addWidget(QLabel("LIGHTSTRIP BRIGHTNESS"))
        hr, hg, hb = self.headset_rgb_color
        self.lbl_hs_brightness = QLabel(f"{self.headset_brightness}%")
        self.lbl_hs_brightness.setObjectName("valueBadge")
        hb_row.addStretch()
        hb_row.addWidget(self.lbl_hs_brightness)
        rlayout.addLayout(hb_row)

        self.hs_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.hs_brightness_slider.setRange(0, 100)
        self.hs_brightness_slider.setValue(self.headset_brightness)
        self.hs_brightness_slider.valueChanged.connect(self.on_hs_brightness_changed)
        rlayout.addWidget(self.hs_brightness_slider)

        hcol_row = QHBoxLayout()
        self.lbl_hs_color_hex = QLabel(f"COLOR: #{hr:02X}{hg:02X}{hb:02X}")
        self.lbl_hs_color_hex.setObjectName("valueBadge")
        hcol_row.addWidget(self.lbl_hs_color_hex)
        btn_color = QPushButton("SELECT CUSTOM RGB COLOR...")
        btn_color.setObjectName("accentBtn")
        btn_color.setFixedHeight(34)
        btn_color.clicked.connect(self.choose_headset_rgb_color)
        hcol_row.addWidget(btn_color, stretch=1)
        rlayout.addLayout(hcol_row)

        rlayout.addWidget(QLabel("PRESET SWATCHES"))
        palette_grid = QGridLayout()
        palette_grid.setSpacing(6)
        colors = [
            ("Cyan", 0, 168, 252),
            ("Cobalt", 59, 130, 246),
            ("Emerald", 16, 185, 129),
            ("Crimson", 239, 68, 68),
            ("Amber", 245, 158, 11),
            ("Stealth OFF", 0, 0, 0)
        ]
        for idx_c, (cname, r, g, b) in enumerate(colors):
            btn = QPushButton(cname)
            btn.clicked.connect(lambda _, cr=r, cg=g, cb=b: self.apply_headset_swatch(cr, cg, cb))
            palette_grid.addWidget(btn, idx_c // 3, idx_c % 3)
        rlayout.addLayout(palette_grid)

        layout.addWidget(rgb_group)
        layout.addStretch()
        return tab

    def apply_headset_swatch(self, r, g, b):
        self.headset_rgb_color = (r, g, b)
        if hasattr(self, 'lbl_hs_color_hex'):
            self.lbl_hs_color_hex.setText(f"COLOR: #{r:02X}{g:02X}{b:02X}")
        cur_mode = self.combo_hs_effect.currentData() if hasattr(self, 'combo_hs_effect') else 1
        if r == 0 and g == 0 and b == 0:
            mode = 0
        else:
            mode = cur_mode if cur_mode in (1, 2) else 1
            if hasattr(self, 'combo_hs_effect') and cur_mode not in (1, 2):
                self.combo_hs_effect.blockSignals(True)
                self.combo_hs_effect.setCurrentIndex(0)  # Static Color
                self.combo_hs_effect.blockSignals(False)
        zone = self.combo_hs_zone.currentData() if hasattr(self, 'combo_hs_zone') else None
        set_g733_rgb(r, g, b, mode=mode, brightness=self.headset_brightness, zone=zone)
        scale = self.headset_brightness / 100.0
        vr, vg, vb = int(r * scale), int(g * scale), int(b * scale)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_headset_rgb(vr, vg, vb)
        if hasattr(self, 'home_widget'):
            self.home_widget.set_headset_rgb(vr, vg, vb)
        self.app_settings["headset_rgb"] = [r, g, b]
        save_app_settings(self.app_settings)

    def on_hs_brightness_changed(self, val):
        self.headset_brightness = int(val)
        self.lbl_hs_brightness.setText(f"{val}%")
        self.app_settings["headset_brightness"] = self.headset_brightness
        r, g, b = self.headset_rgb_color
        scale = self.headset_brightness / 100.0
        vr, vg, vb = int(r * scale), int(g * scale), int(b * scale)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_headset_rgb(vr, vg, vb)
        if hasattr(self, 'home_widget'):
            self.home_widget.set_headset_rgb(vr, vg, vb)
        if not hasattr(self, '_hs_rgb_timer'):
            self._hs_rgb_timer = QTimer(self)
            self._hs_rgb_timer.setSingleShot(True)
            self._hs_rgb_timer.timeout.connect(lambda: self.on_hs_effect_changed(0))
        self._hs_rgb_timer.start(80)

    def on_hs_effect_changed(self, idx):
        mode = self.combo_hs_effect.currentData() if hasattr(self, 'combo_hs_effect') else 1
        zone = self.combo_hs_zone.currentData() if hasattr(self, 'combo_hs_zone') else None
        r, g, b = self.headset_rgb_color
        if mode == 0:
            set_g733_rgb(0, 0, 0, mode=0, brightness=0, zone=zone)
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_headset_rgb(0, 0, 0)
        elif mode == 3:
            set_g733_rgb(0, 255, 255, mode=3, brightness=self.headset_brightness, zone=zone)
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_headset_rgb(0, 255, 255)
        else:
            if r == 0 and g == 0 and b == 0:
                r, g, b = 56, 189, 248
                self.headset_rgb_color = (r, g, b)
            set_g733_rgb(r, g, b, mode=mode, brightness=self.headset_brightness, zone=zone)
            scale = self.headset_brightness / 100.0
            if hasattr(self, 'stage_widget'):
                self.stage_widget.set_headset_rgb(int(r * scale), int(g * scale), int(b * scale))
        save_app_settings(self.app_settings)

    def choose_headset_rgb_color(self):
        r, g, b = self.headset_rgb_color
        color = QColorDialog.getColor(QColor(r, g, b), self, "Select G733 LIGHTSYNC RGB Color")
        if color.isValid():
            self.apply_headset_swatch(color.red(), color.green(), color.blue())

    # ------------------ Battery & Info Tab ------------------
    def create_headset_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)

        bat_group = self.register_card(QGroupBox("LI-PO BATTERY TELEMETRY && TTS"))
        blayout = QVBoxLayout(bat_group)
        blayout.setSpacing(8)
        blayout.setContentsMargins(0, 8, 0, 6)

        b_top = QHBoxLayout()
        b_top.addWidget(QLabel("CHARGE STATE"))
        self.lbl_hs_battery_pct = QLabel("85% (Discharging)")
        self.lbl_hs_battery_pct.setObjectName("valueBadge")
        b_top.addWidget(self.lbl_hs_battery_pct)
        b_top.addStretch()
        blayout.addLayout(b_top)

        self.bar_hs_battery = QProgressBar()
        self.bar_hs_battery.setRange(0, 100)
        self.bar_hs_battery.setValue(85)
        blayout.addWidget(self.bar_hs_battery)

        self.lbl_hs_mv = QLabel("CELL VOLTAGE: 3958 mV (HYSTERESIS 5% STEP)")
        self.lbl_hs_mv.setObjectName("subText")
        blayout.addWidget(self.lbl_hs_mv)

        btn_speak = QPushButton("ANNOUNCE BATTERY PERCENTAGE (TTS)")
        btn_speak.setObjectName("accentBtn")
        btn_speak.setFixedHeight(34)
        btn_speak.clicked.connect(self.speak_current_battery)
        blayout.addWidget(btn_speak)

        note_label = QLabel("Physical G733 power button press triggers automatic TTS battery readout.")
        note_label.setWordWrap(True)
        note_label.setObjectName("subText")
        blayout.addWidget(note_label)

        layout.addWidget(bat_group)

        grp = self.register_card(QGroupBox("HARDWARE SPECIFICATION"))
        glayout = QVBoxLayout(grp)
        glayout.setContentsMargins(0, 8, 0, 6)

        info_text = QLabel(
            "MODEL:       Logitech G733 LIGHTSPEED Wireless\n"
            "USB ID:      046d:0ab5\n"
            "TRANSPORT:   2.4 GHz LIGHTSPEED Receiver\n"
            "PROTOCOL:    HID++ 2.0 / PipeWire / ALSA"
        )
        info_text.setFont(QFont("JetBrains Mono", 9))
        info_text.setObjectName("subText")
        glayout.addWidget(info_text)

        layout.addWidget(grp)
        layout.addStretch()

        self.refresh_battery_status()
        return tab

    # ------------------ Service & Helper Logic ------------------
    def update_daemon_status(self):
        try:
            res = subprocess.run(['systemctl', '--user', 'is-active', 'g502-macros.service'], capture_output=True, text=True)
            active = res.stdout.strip() == 'active'
            if active:
                self.status_badge.setText("DAEMON: ACTIVE")
                self.status_badge.setObjectName("statusBadgeActive")
                self.btn_toggle_service.setText("STOP DAEMON")
                self.btn_toggle_service.setObjectName("stopBtn")
            else:
                self.status_badge.setText("DAEMON: INACTIVE")
                self.status_badge.setObjectName("statusBadgeInactive")
                self.btn_toggle_service.setText("START DAEMON")
                self.btn_toggle_service.setObjectName("accentBtn")
            self.status_badge.setStyle(self.status_badge.style())
            self.btn_toggle_service.setStyle(self.btn_toggle_service.style())
        except Exception:
            pass

    def toggle_service(self):
        res = subprocess.run(['systemctl', '--user', 'is-active', 'g502-macros.service'], capture_output=True, text=True)
        if res.stdout.strip() == 'active':
            subprocess.run(['systemctl', '--user', 'stop', 'g502-macros.service'])
        else:
            subprocess.run(['systemctl', '--user', 'start', 'g502-macros.service'])
        self.update_daemon_status()
        self.refresh_logs()

    def on_dpi_slider_changed(self, val):
        snapped = max(400, min(4000, int(round(val / 50.0) * 50)))
        self.dpi_val_label.setText(f"{snapped} DPI")
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_state(self.active_button_key, self.buttons_cfg, snapped)
        if not hasattr(self, '_dpi_debounce_timer'):
            self._dpi_debounce_timer = QTimer(self)
            self._dpi_debounce_timer.setSingleShot(True)
            self._dpi_debounce_timer.timeout.connect(lambda: self.set_dpi(int(round(self.dpi_slider.value() / 50.0) * 50)))
        self._dpi_debounce_timer.start(80)

    def set_dpi(self, dpi):
        dpi = max(400, min(4000, int(round(dpi / 50.0) * 50)))
        self.dpi_slider.blockSignals(True)
        self.dpi_slider.setValue(dpi)
        self.dpi_slider.blockSignals(False)
        self.dpi_val_label.setText(f"{dpi} DPI")

        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_state(self.active_button_key, self.buttons_cfg, dpi)
        if hasattr(self, 'home_widget'):
            self.home_widget.set_mouse_dpi(dpi)

        dev_id = self.get_selected_ratbag_dev_id()
        if dev_id:
            subprocess.run(['ratbagctl', dev_id, 'profile', 'active', 'set', '0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_id, 'dpi', 'set', str(dpi)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for p in [0, 1, 2]:
                subprocess.run(['ratbagctl', dev_id, 'profile', str(p), 'resolution', '0', 'dpi', 'set', str(dpi)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['ratbagctl', dev_id, 'profile', str(p), 'resolution', 'active', 'set', '0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_kwin_mouse_paths(self):
        paths = []
        try:
            import re
            tree = subprocess.check_output(['busctl', '--user', 'tree', 'org.kde.KWin'], text=True)
            all_paths = re.findall(r'/org/kde/KWin/InputDevice/event\d+', tree)
            for p in all_paths:
                try:
                    name = subprocess.check_output(['busctl', '--user', 'get-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'name'], text=True)
                    if 'G502' in name or 'Mouse' in name:
                        paths.append(p)
                except Exception:
                    pass
        except Exception:
            pass
        if not paths:
            paths = ['/org/kde/KWin/InputDevice/event8']
        return paths

    def on_accel_profile_changed(self, idx):
        profile_num = 2 if idx == 0 else 1
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Libinput', '--group', '1133', '--group', '49970', '--group', 'Logitech Gaming Mouse G502', '--key', 'PointerAccelerationProfile', str(profile_num)])
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Mouse', '--key', 'PointerAccelerationProfile', str(profile_num)])
        is_flat = (profile_num == 2)
        for p in self.get_kwin_mouse_paths():
            subprocess.run(['busctl', '--user', 'set-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'pointerAccelerationProfileFlat', 'b', 'true' if is_flat else 'false'], stdout=subprocess.DEVNULL)

    def on_speed_slider_changed(self, val):
        speed_float = val / 100.0
        self.speed_val_label.setText(f"{speed_float:.3f}")
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Libinput', '--group', '1133', '--group', '49970', '--group', 'Logitech Gaming Mouse G502', '--key', 'PointerAcceleration', f"{speed_float:.3f}"])
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Mouse', '--key', 'PointerAcceleration', f"{speed_float:.3f}"])
        for p in self.get_kwin_mouse_paths():
            subprocess.run(['busctl', '--user', 'set-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'pointerAcceleration', 'd', str(speed_float)], stdout=subprocess.DEVNULL)

    def apply_exact_calibration(self):
        px_per_cm = self.spin_px_cm.value()
        target_dpi = px_per_cm * 2.54
        
        hardware_dpi = 1000
        self.set_dpi(hardware_dpi)
        
        # Disable acceleration (Flat profile = 2 in KDE)
        self.combo_profile.setCurrentIndex(0)
        self.on_accel_profile_changed(0)
        
        # Scale factor formula for libinput flat: Factor = 1.0 + accel_setting
        scale_factor = target_dpi / hardware_dpi
        accel_setting = scale_factor - 1.0
        
        self.speed_val_label.setText(f"{accel_setting:.5f}")
        
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Libinput', '--group', '1133', '--group', '49970', '--group', 'Logitech Gaming Mouse G502', '--key', 'PointerAcceleration', f"{accel_setting:.5f}"])
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Mouse', '--key', 'PointerAcceleration', f"{accel_setting:.5f}"])
        for p in self.get_kwin_mouse_paths():
            subprocess.run(['busctl', '--user', 'set-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'pointerAcceleration', 'd', str(accel_setting)], stdout=subprocess.DEVNULL)
        
        QMessageBox.information(self, "Calibration Applied", f"Successfully calibrated!\n\nTarget: {px_per_cm} px/cm (~{target_dpi:.2f} DPI)\nHardware DPI set to {hardware_dpi}\nKWin Multiplier set to {scale_factor:.5f}\n(Libinput setting: {accel_setting:.5f})\n\nAcceleration curve disabled (Flat/1:1).")

    def apply_all_black_rgb(self):
        subprocess.run(['openrgb', '--profile', 'ALL Black'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        set_g502_rgb(0, 0, 0, mode=0, brightness=0)
        set_g733_rgb(0, 0, 0, mode=0, brightness=0)
        if hasattr(self, 'stage_widget'):
            self.stage_widget.set_mouse_rgb(0, 0, 0)
            self.stage_widget.set_headset_rgb(0, 0, 0)
        QMessageBox.information(self, "OpenRGB & HID++", "Applied 'ALL Black' profile successfully!")

    def refresh_logs(self):
        try:
            out = subprocess.check_output(['journalctl', '--user', '-u', 'g502-macros.service', '-n', '50', '--no-pager']).decode()
            self.log_view.setText(out)
        except Exception as e:
            self.log_view.setText(f"Error fetching logs: {e}")


def main():
    app = QApplication(sys.argv)
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    window = G502ControlApp()
    if "--minimized" in sys.argv or window.app_settings.get("autostart_minimized", False):
        window.hide()
    else:
        window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
