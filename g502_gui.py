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

THEMES = {
    "Dark Void (Default)": {
        "bg_main": "#0B0D13",
        "bg_card": "#131722",
        "bg_input": "#1C2230",
        "accent": "#38BDF8",
        "text_main": "#F1F5F9",
        "text_sub": "#94A3B8",
        "border": "#262F40"
    },
    "Midnight Cyan": {
        "bg_main": "#0A192F",
        "bg_card": "#112240",
        "bg_input": "#1D3557",
        "accent": "#64FFDA",
        "text_main": "#CCD6F6",
        "text_sub": "#8892B0",
        "border": "#233554"
    },
    "Cyberpunk Neon": {
        "bg_main": "#0D0221",
        "bg_card": "#190535",
        "bg_input": "#2C0B4D",
        "accent": "#FF007F",
        "text_main": "#F1E3F8",
        "text_sub": "#B593C3",
        "border": "#3A105C"
    },
    "Slate Dark": {
        "bg_main": "#0F172A",
        "bg_card": "#1E293B",
        "bg_input": "#334155",
        "accent": "#38BDF8",
        "text_main": "#F8FAFC",
        "text_sub": "#94A3B8",
        "border": "#334155"
    },
    "Nordic Frost": {
        "bg_main": "#2E3440",
        "bg_card": "#3B4252",
        "bg_input": "#4C566A",
        "accent": "#88C0D0",
        "text_main": "#ECEFF4",
        "text_sub": "#D8DEE9",
        "border": "#434C5E"
    },
    "Dracula Dark": {
        "bg_main": "#282A36",
        "bg_card": "#343746",
        "bg_input": "#44475A",
        "accent": "#FF79C6",
        "text_main": "#F8F8F2",
        "text_sub": "#BD93F9",
        "border": "#6272A4"
    },
    "Emerald Forest": {
        "bg_main": "#061412",
        "bg_card": "#0C2320",
        "bg_input": "#143833",
        "accent": "#34D399",
        "text_main": "#ECFDF5",
        "text_sub": "#6EE7B7",
        "border": "#164E63"
    },
    "Sunset Crimson": {
        "bg_main": "#180A0A",
        "bg_card": "#2A1212",
        "bg_input": "#3F1B1B",
        "accent": "#FB7185",
        "text_main": "#FFF1F2",
        "text_sub": "#FDA4AF",
        "border": "#881337"
    },
    "Tokyo Night": {
        "bg_main": "#1A1B26",
        "bg_card": "#24283B",
        "bg_input": "#414868",
        "accent": "#7AA2F7",
        "text_main": "#A9B1D6",
        "text_sub": "#7DCFFF",
        "border": "#565F89"
    },
    "Solar Gold": {
        "bg_main": "#121212",
        "bg_card": "#1E1E1E",
        "bg_input": "#2C2C2C",
        "accent": "#FBBF24",
        "text_main": "#FEF3C7",
        "text_sub": "#FCD34D",
        "border": "#383838"
    },
    "Synthwave 80s": {
        "bg_main": "#120A2A",
        "bg_card": "#1B103C",
        "bg_input": "#2D1B5E",
        "accent": "#FF71CE",
        "text_main": "#FDFEFE",
        "text_sub": "#01CDFE",
        "border": "#432888"
    },
    "Matrix Hacker": {
        "bg_main": "#0D1117",
        "bg_card": "#161B22",
        "bg_input": "#21262D",
        "accent": "#00FF66",
        "text_main": "#E6EDF3",
        "text_sub": "#7EE787",
        "border": "#30363D"
    },
    "Deep Amethyst": {
        "bg_main": "#150C22",
        "bg_card": "#221435",
        "bg_input": "#321E4B",
        "accent": "#C084FC",
        "text_main": "#F3E8FF",
        "text_sub": "#A855F7",
        "border": "#4C2875"
    },
    "Oceanic Abyss": {
        "bg_main": "#050E18",
        "bg_card": "#0B192C",
        "bg_input": "#1E3A8A",
        "accent": "#00F5D4",
        "text_main": "#E0F2FE",
        "text_sub": "#38BDF8",
        "border": "#1E293B"
    },
    "Rose Gold Luxe": {
        "bg_main": "#18181B",
        "bg_card": "#27272A",
        "bg_input": "#3F3F46",
        "accent": "#FB7185",
        "text_main": "#FAFAFA",
        "text_sub": "#F472B6",
        "border": "#52525B"
    },
    "Vaporwave Pastel": {
        "bg_main": "#1E1B2E",
        "bg_card": "#28243D",
        "bg_input": "#3A3556",
        "accent": "#F472B6",
        "text_main": "#F3E8FF",
        "text_sub": "#A78BFA",
        "border": "#4C456B"
    },
    "Monochrome Stealth": {
        "bg_main": "#121212",
        "bg_card": "#1E1E1E",
        "bg_input": "#2A2A2A",
        "accent": "#FFFFFF",
        "text_main": "#FAFAFA",
        "text_sub": "#A1A1AA",
        "border": "#333333"
    },
    "Light Pristine": {
        "bg_main": "#F1F5F9",
        "bg_card": "#FFFFFF",
        "bg_input": "#E2E8F0",
        "accent": "#0284C7",
        "text_main": "#0F172A",
        "text_sub": "#475569",
        "border": "#CBD5E1"
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
    """Applies subtle elevation shadow to cards while preserving structural borders."""
    shadow = QGraphicsDropShadowEffect(widget)
    if is_light_theme(theme_name):
        shadow.setColor(QColor(15, 23, 42, 22))
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
    else:
        shadow.setColor(QColor(0, 0, 0, 85))
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 5)
    widget.setGraphicsEffect(shadow)


def generate_qss(theme_name="Dark Void (Default)"):
    t = THEMES.get(theme_name, THEMES["Dark Void (Default)"])
    light = is_light_theme(theme_name)
    accent_hover = adjust_hex_color(t['accent'], 0.90 if light else 1.14)
    accent_pressed = adjust_hex_color(t['accent'], 0.80 if light else 0.86)
    input_hover = adjust_hex_color(t['bg_input'], 0.95 if light else 1.18)
    input_pressed = adjust_hex_color(t['bg_input'], 0.88 if light else 0.88)

    # Pure black/white 10% alpha outline for content images per better-ui
    img_outline = "rgba(0, 0, 0, 0.10)" if light else "rgba(255, 255, 255, 0.10)"

    # Generate crisp vector SVGs matching text weight (1.75px - 2.0px stroke)
    os.makedirs(ICONS_CACHE_DIR, exist_ok=True)
    chevron_down_path = os.path.join(ICONS_CACHE_DIR, 'chevron_down.svg')
    chevron_up_path = os.path.join(ICONS_CACHE_DIR, 'chevron_up.svg')
    check_path = os.path.join(ICONS_CACHE_DIR, 'check.svg')

    with open(chevron_down_path, 'w') as f:
        f.write(
            f'<svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M1.5 1.75L6 6.25L10.5 1.75" stroke="{t["accent"]}" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        )
    with open(chevron_up_path, 'w') as f:
        f.write(
            f'<svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M1.5 6.25L6 1.75L10.5 6.25" stroke="{t["accent"]}" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        )
    with open(check_path, 'w') as f:
        f.write(
            f'<svg width="12" height="10" viewBox="0 0 12 10" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M1.5 5.25L4.5 8.25L10.5 1.75" stroke="{t["bg_main"]}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        )

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
    font-size: 16px;
    font-weight: 700;
    border: none;
    background: transparent;
}}

QLabel#headerSubtitle {{
    color: {t['text_sub']};
    font-size: 11px;
    font-weight: 500;
    border: none;
    background: transparent;
}}

QLabel#sectionHeader {{
    color: {t['accent']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    border: none;
    background: transparent;
}}

QLabel#accentTitle {{
    color: {t['accent']};
    font-weight: 700;
    border: none;
    background: transparent;
}}

QLabel#valueBadge {{
    background-color: {t['bg_input']};
    color: {t['accent']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    font-weight: 700;
}}

QLabel#subText {{
    color: {t['text_sub']};
    font-size: 12px;
    border: none;
    background: transparent;
}}

QLabel#diagramImage {{
    background-color: #1A222D;
    border: 1px solid {img_outline};
    border-radius: 8px;
    padding: 6px;
}}

/* Concentric Radii: Header Bar outer radius 18px = inner controls 8px + 10px padding */
.QFrame#headerBar {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 18px;
}}

.QFrame#summaryBox {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 10px 12px;
}}

.QFrame#guideBox {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 14px;
    padding: 10px 14px;
}}

/* Detached modern pill TabBar with unboxed pane to eliminate corner overlaps */
QTabWidget::pane {{
    border: none;
    background: transparent;
    margin-top: 8px;
}}

QTabBar::tab {{
    background-color: {t['bg_card']};
    color: {t['text_sub']};
    /* Optical alignment: 2px less padding on leading icon side (14px left vs 16px right) */
    padding: 9px 16px 9px 14px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid {t['border']};
    border-radius: 8px;
    margin-right: 6px;
}}

QTabBar::tab:hover:!selected {{
    color: {t['text_main']};
    background-color: {t['bg_input']};
    border-color: {t['accent']};
}}

QTabBar::tab:selected {{
    background-color: {t['accent']};
    color: {t['bg_main']};
    border: 1px solid {t['accent']};
    font-weight: 700;
}}

QGroupBox {{
    font-weight: 700;
    font-size: 13px;
    border: 1px solid {t['border']};
    border-radius: 14px;
    margin-top: 0px;
    padding-top: 34px;
    padding-bottom: 12px;
    padding-left: 12px;
    padding-right: 12px;
    background-color: {t['bg_card']};
}}

QGroupBox::title {{
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 14px;
    top: 10px;
    padding: 0px;
    color: {t['accent']};
    background-color: transparent;
}}

QPushButton {{
    background-color: {t['bg_input']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    /* Optical alignment: 14px left, 16px right */
    padding: 8px 16px 8px 14px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:!disabled:hover {{
    background-color: {input_hover};
    border-color: {t['accent']};
    color: {t['accent']};
}}

QPushButton:!disabled:pressed {{
    background-color: {input_pressed};
    padding-top: 9px;
    padding-bottom: 7px;
}}

QPushButton:disabled {{
    background-color: {t['bg_main']};
    color: {t['text_sub']};
    border-color: {t['border']};
}}

QPushButton#btnIcon {{
    padding: 0px;
    font-size: 16px;
    border-radius: 8px;
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
}}

QPushButton#btnIcon:!disabled:hover {{
    background-color: {input_hover};
    border-color: {t['accent']};
    color: {t['accent']};
}}

QPushButton#btnSelector {{
    background-color: {t['bg_main']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 9px 14px 9px 12px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
}}

QPushButton#btnSelector:!disabled:hover {{
    background-color: {t['bg_input']};
    color: {t['accent']};
    border-color: {t['accent']};
}}

QPushButton#btnSelector:checked {{
    background-color: {t['accent']};
    color: {t['bg_main']};
    border: 1px solid {t['accent']};
    font-weight: 700;
}}

QPushButton#accentBtn {{
    background-color: {t['accent']};
    color: {t['bg_main']};
    border: 1px solid {t['accent']};
    border-radius: 8px;
    padding: 8px 16px 8px 14px;
    font-weight: 700;
}}

QPushButton#accentBtn:!disabled:hover {{
    background-color: {accent_hover};
    border-color: {accent_hover};
    color: {t['bg_main']};
}}

QPushButton#accentBtn:!disabled:pressed {{
    background-color: {accent_pressed};
    border-color: {accent_pressed};
    padding-top: 9px;
    padding-bottom: 7px;
}}

QPushButton#stopBtn {{
    background-color: #DC2626;
    color: #FFFFFF;
    border: 1px solid #EF4444;
    border-radius: 8px;
    padding: 8px 16px 8px 14px;
    font-weight: 700;
}}

QPushButton#stopBtn:!disabled:hover {{
    background-color: #EF4444;
    border-color: #F87171;
    color: #FFFFFF;
}}

QPushButton#stopBtn:!disabled:pressed {{
    background-color: #B91C1C;
    padding-top: 9px;
    padding-bottom: 7px;
}}

/* Horizontal & Vertical Sliders */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {t['bg_input']};
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {t['bg_card']};
    border: 2px solid {t['accent']};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {t['accent']};
}}

QSlider::groove:vertical {{
    border: none;
    width: 6px;
    background: {t['bg_input']};
    border-radius: 3px;
}}

QSlider::add-page:vertical {{
    background: {t['accent']};
    border-radius: 3px;
}}

QSlider::sub-page:vertical {{
    background: {t['bg_input']};
    border-radius: 3px;
}}

QSlider::handle:vertical {{
    background: {t['bg_card']};
    border: 2px solid {t['accent']};
    width: 16px;
    height: 16px;
    margin: 0 -6px;
    border-radius: 9px;
}}

QSlider::handle:vertical:hover {{
    background: {t['accent']};
}}

/* Form Inputs: 3:1 contrast boundary + custom SVG indicators */
QComboBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 7px 34px 7px 12px;
    color: {t['text_main']};
    font-size: 13px;
    font-weight: 500;
}}

QComboBox:hover {{
    border-color: {t['accent']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {t['border']};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: url({chevron_down_path});
    width: 12px;
    height: 8px;
}}

QComboBox::down-arrow:on {{
    margin-top: 2px;
}}

QComboBox QAbstractItemView {{
    background-color: {t['bg_card']};
    color: {t['text_main']};
    selection-background-color: {t['accent']};
    selection-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 7px 32px 7px 12px;
    color: {t['text_main']};
    font-size: 13px;
    font-weight: 600;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {t['accent']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid {t['border']};
    border-bottom: 1px solid {t['border']};
    border-top-right-radius: 8px;
    background: transparent;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 26px;
    border-left: 1px solid {t['border']};
    border-bottom-right-radius: 8px;
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
    spacing: 10px;
    font-size: 13px;
    color: {t['text_main']};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
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

/* Concentric Menu: outer 12px = inner 6px + 6px padding */
QMenu {{
    background-color: {t['bg_card']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 18px 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}}

QMenu::item:selected {{
    background-color: {t['accent']};
    color: {t['bg_main']};
    font-weight: 700;
}}

QMenu::separator {{
    height: 1px;
    background: {t['border']};
    margin: 5px 8px;
}}

QTextEdit {{
    background-color: {t['bg_main']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 8px;
    color: {t['text_main']};
    font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}}

QProgressBar {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    height: 18px;
    text-align: center;
    color: {t['text_main']};
    font-weight: 700;
    font-size: 11px;
}}

QProgressBar::chunk {{
    background-color: {t['accent']};
    border-radius: 7px;
}}

QLabel#statusBadgeActive {{
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #059669;
    border-radius: 8px;
    padding: 0px 12px;
    font-weight: 700;
    font-size: 12px;
}}

QLabel#statusBadgeInactive {{
    background-color: #451A03;
    color: #FDBA74;
    border: 1px solid #D97706;
    border-radius: 8px;
    padding: 0px 12px;
    font-weight: 700;
    font-size: 12px;
}}

QLabel#batteryBadge {{
    background-color: {t['bg_input']};
    color: {t['accent']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 0px 12px;
    font-weight: 700;
    font-size: 12px;
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

def set_g733_rgb(r, g, b, mode=1):
    dev_path = find_g733_hidraw()
    if not dev_path:
        logging.warning("Cannot set G733 RGB: hidraw device not found")
        return False
    try:
        fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
        for zone in [0, 1, 0xFF]:
            cmd = bytes([0x11, 0xFF, 0x04, 0x10, zone, mode, r, g, b, 0x00, 0x00, 0x64] + [0x00]*8)
            os.write(fd, cmd)
            time.sleep(0.01)
        os.close(fd)
        logging.info(f"Targeted G733 Headset RGB set to R={r} G={g} B={b} (Mode {mode})")
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
                    res = subprocess.run(['pactl', 'get-default-source'], capture_output=True, text=True, timeout=1)
                    src = res.stdout.strip()
                    if src:
                        source_arg = [f'--device={src}']
                except Exception:
                    pass

                p = subprocess.Popen(
                    ['parec'] + source_arg + ['--channels=1', '--rate=16000', '--format=s16le', '--raw'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                
                while not self.isInterruptionRequested():
                    raw = p.stdout.read(1600)  # 50ms chunk
                    if raw:
                        num_samples = len(raw) // 2
                        samples = struct.unpack(f'<{num_samples}h', raw)
                        peak = max(abs(s) for s in samples) if samples else 0
                        if peak > 50:
                            import math
                            db = 20 * math.log10(peak / 32768.0)
                            pct = max(0, min(100, int((db + 45) * 2.2)))
                        else:
                            pct = 0
                        self.level_signal.emit(pct)
                    else:
                        if p.poll() is not None:
                            break  # parecord died, break to restart
                        time.sleep(0.05)
                try:
                    p.terminate()
                    p.wait(timeout=1)
                except Exception:
                    p.kill()
            except Exception as e:
                logging.error(f"Error in MicMeterThread: {e}")
            
            # If it broke or threw an error, wait a bit before restarting to avoid spin lock
            time.sleep(1.0)


def load_app_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "theme": "Dark Void (Default)",
        "minimize_to_tray": True,
        "show_notifications": True,
        "autostart_minimized": False
    }

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
        self.setWindowTitle("Application Settings & System Diagnostics")
        self.resize(780, 540)
        self.parent_app = parent
        self.settings = load_app_settings()
        self.setStyleSheet(generate_qss(self.settings.get("theme", "Dark Void (Default)")))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("⚙ Settings & Diagnostics Studio")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setObjectName("accentTitle")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.tabBar().setUsesScrollButtons(False)
        tabs.addTab(self.create_appearance_tab(), "🎨 Appearance && Theme")
        tabs.addTab(self.create_diagnostics_tab(), "🩺 System Diagnostics")
        tabs.addTab(self.create_tray_tab(), "📌 System Tray && Behavior")
        tabs.addTab(self.create_about_tab(), "ℹ️ About && GitHub")
        layout.addWidget(tabs)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("✓  Done")
        btn_close.setObjectName("accentBtn")
        btn_close.setFixedHeight(36)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def create_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 8, 4, 4)

        grp = QGroupBox("Theme Selection && Live Color Tokens")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        glayout.addWidget(QLabel(f"Select Visual Accent Theme ({len(THEMES)} Curated Themes Available):"))
        self.combo_theme = QComboBox()
        for tname in THEMES.keys():
            self.combo_theme.addItem(tname)
        
        current_theme = self.settings.get("theme", "Dark Void (Default)")
        idx = self.combo_theme.findText(current_theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)

        self.combo_theme.currentIndexChanged.connect(self.on_theme_changed)
        glayout.addWidget(self.combo_theme)

        theme_info = QLabel("Theme changes apply live across all window surfaces, SVG icons, and elevation shadows.")
        theme_info.setObjectName("subText")
        glayout.addWidget(theme_info)

        # Quick Theme Grid for 1-click previewing
        grid_lbl = QLabel("Quick Theme Presets:")
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
        layout.setContentsMargins(4, 8, 4, 4)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Live System Subsystem Health Check:"))
        top_row.addStretch()
        btn_run_diag = QPushButton("🔄  Run Health Audit")
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
        report.append(" 🩺 LOGITECH LINUX CONTROL SUITE HEALTH AUDIT")
        report.append(f" Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("==================================================\n")

        res = subprocess.run(['systemctl', '--user', 'is-active', 'g502-macros.service'], capture_output=True, text=True)
        m_status = res.stdout.strip()
        report.append(f"[Macro Service] g502-macros.service: {'✅ ACTIVE' if m_status == 'active' else '❌ INACTIVE ('+m_status+')'}")

        res = subprocess.run(['systemctl', 'is-active', 'ratbagd.service'], capture_output=True, text=True)
        r_status = res.stdout.strip()
        report.append(f"[Mouse Daemon] ratbagd.service: {'✅ ACTIVE' if r_status == 'active' else '⚠️ INACTIVE ('+r_status+')'}")

        res = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
        pw_ok = res.returncode == 0
        report.append(f"[Audio Daemon] PipeWire / WirePlumber: {'✅ ONLINE' if pw_ok else '❌ OFFLINE'}")

        dev_path = find_g733_hidraw()
        pct, b_status, mV = get_g733_battery_info()
        report.append(f"[G733 HID++ Hardware]: {'✅ CONNECTED ('+dev_path+')' if dev_path else '⚠️ DISCONNECTED'}")
        report.append(f"  • Battery Level: {pct}% ({b_status}, {mV} mV)")

        self.diag_text.setText("\n".join(report))

    def create_tray_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 8, 4, 4)

        grp = QGroupBox("System Tray && Closing Behavior")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        self.chk_tray = QCheckBox("Minimize application to System Tray on window close when Macro Daemon is active")
        self.chk_tray.setChecked(self.settings.get("minimize_to_tray", True))
        self.chk_tray.toggled.connect(self.on_tray_setting_changed)
        glayout.addWidget(self.chk_tray)

        self.chk_notif = QCheckBox("Show System Tray Notifications on background state changes")
        self.chk_notif.setChecked(self.settings.get("show_notifications", True))
        self.chk_notif.toggled.connect(self.on_tray_setting_changed)
        glayout.addWidget(self.chk_notif)

        layout.addWidget(grp)
        layout.addStretch()
        return tab

    def on_tray_setting_changed(self):
        self.settings["minimize_to_tray"] = self.chk_tray.isChecked()
        self.settings["show_notifications"] = self.chk_notif.isChecked()
        save_app_settings(self.settings)

    def create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 8, 4, 4)

        grp = QGroupBox("About Logitech Linux Control Suite")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(12)

        lbl_app = QLabel("Logitech Linux Control Suite & Macro Studio v2.6")
        lbl_app.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_app.setObjectName("accentTitle")
        glayout.addWidget(lbl_app)

        lbl_desc = QLabel(
            "An open-source native Linux control suite providing G HUB functionality for Logitech hardware:\n"
            "• Zero-lag mouse button macros, hardware DPI tuner & exact 1:1 px/cm calibration.\n"
            "• Headset master volume, 10-band hardware equalizer, microphone gain/mute, and sidetone.\n"
            "• Targeted G733 HID++ RGB lighting controller.\n"
            "• Spoken battery percentage announcements on physical power button press."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setObjectName("subText")
        glayout.addWidget(lbl_desc)

        btn_github = QPushButton("🌐  Open GitHub Repository (gaxkalik/Logitech-Linux-App)")
        btn_github.setObjectName("accentBtn")
        btn_github.setFixedHeight(38)
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        glayout.addWidget(btn_github)

        layout.addWidget(grp)
        layout.addStretch()
        return tab


class G502ControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logitech Linux Control Center (Mouse & Headset)")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1040, 780)

        self.app_settings = load_app_settings()
        current_theme = self.app_settings.get("theme", "Dark Void (Default)")
        self.setStyleSheet(generate_qss(current_theme))

        self.mice_list = get_all_ratbag_mice()
        self.active_button_key = "G8"
        self.elevated_cards = []

        # Setup Main UI Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # Header Bar (Concentric Radius: 18px outer = 8px inner + 10px inset)
        header = QFrame()
        header.setObjectName("headerBar")
        self.elevated_cards.append(header)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)

        # Hamburger Menu Button (☰)
        btn_hamburger = QPushButton("☰")
        btn_hamburger.setObjectName("btnIcon")
        btn_hamburger.setFixedSize(36, 36)
        btn_hamburger.setToolTip("Quick Menu & Device Switcher")
        btn_hamburger.clicked.connect(self.show_hamburger_menu)
        header_layout.addWidget(btn_hamburger)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        title_label = QLabel("Logitech Linux Control Suite")
        title_label.setObjectName("headerTitle")
        subtitle_label = QLabel("G502 Mouse Macros & G733 Wireless Headset Studio")
        subtitle_label.setObjectName("headerSubtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Wireless Battery Indicator Badge in Header
        self.lbl_header_battery = QLabel("🔋 G733: --%")
        self.lbl_header_battery.setObjectName("batteryBadge")
        self.lbl_header_battery.setFixedHeight(36)
        self.lbl_header_battery.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header_battery.setToolTip("Click to announce remaining battery charge out loud")
        self.lbl_header_battery.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_header_battery.mousePressEvent = lambda ev: self.speak_current_battery()
        header_layout.addWidget(self.lbl_header_battery)

        # Device Selector Dropdown (Mouse vs Headset)
        self.combo_main_device = QComboBox()
        self.combo_main_device.setMinimumWidth(275)
        self.combo_main_device.setFixedHeight(36)
        self.combo_main_device.addItem("🖱️ Logitech G502 Gaming Mouse", "MOUSE")
        self.combo_main_device.addItem("🎧 Logitech G733 Gaming Headset", "HEADSET")
        self.combo_main_device.currentIndexChanged.connect(self.on_main_device_switched)
        header_layout.addWidget(self.combo_main_device)

        # Daemon Status Indicator + Toggle Service Button aligned horizontally
        self.status_badge = QLabel("● CHECKING...")
        self.status_badge.setObjectName("statusBadgeInactive")
        self.status_badge.setFixedHeight(36)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_badge)

        self.btn_toggle_service = QPushButton("Start Service")
        self.btn_toggle_service.setObjectName("accentBtn")
        self.btn_toggle_service.setFixedHeight(36)
        self.btn_toggle_service.clicked.connect(self.toggle_service)
        header_layout.addWidget(self.btn_toggle_service)

        # Dedicated Settings Gear Button (⚙)
        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("btnIcon")
        btn_settings.setFixedSize(36, 36)
        btn_settings.setToolTip("Open Appearance Themes & System Diagnostics")
        btn_settings.clicked.connect(self.open_settings_dialog)
        header_layout.addWidget(btn_settings)

        main_layout.addWidget(header)

        # Stacked Widget for Device Views (0 = Mouse View, 1 = Headset View)
        self.device_stack = QStackedWidget()
        
        # 1. Mouse View Container
        self.mouse_tabs = QTabWidget()
        self.mouse_tabs.addTab(self.create_interactive_macro_tab(), "🎮  Interactive Button Studio")
        self.mouse_tabs.addTab(self.create_dashboard_tab(), "⚙️  DPI && Pointer Speed")
        self.mouse_tabs.addTab(self.create_rgb_tab(), "💡  RGB Lighting")
        self.mouse_tabs.addTab(self.create_logs_tab(), "📜  Service Logs")
        self.device_stack.addWidget(self.mouse_tabs)

        # 2. Headset View Container
        self.headset_tabs = QTabWidget()
        self.headset_tabs.addTab(self.create_headset_sound_tab(), "🔊  Sound && Equalizer")
        self.headset_tabs.addTab(self.create_headset_mic_tab(), "🎙️  Microphone Controls")
        self.headset_tabs.addTab(self.create_headset_rgb_tab(), "🌈  Targeted RGB Lightstrip")
        self.headset_tabs.addTab(self.create_headset_info_tab(), "🔋  Battery && Headset Status")
        self.device_stack.addWidget(self.headset_tabs)

        main_layout.addWidget(self.device_stack)

        # Apply subtle elevation shadows to all cards
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

        # Status & Battery Refresh Timer (Updates UI silently, NEVER speaks)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_refresh)
        self.timer.start(5000)
        self.periodic_refresh()

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
            self.lbl_header_battery.setText(f"🔋 G733: {pct}% ({status_str.split()[0]})")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText(f"{pct}% ({status_str})")
                self.bar_hs_battery.setValue(pct)
                self.lbl_hs_mv.setText(f"Voltage: {mV} mV (Smoothed G HUB 5% steps)")
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip(f"Logitech Linux Control Suite — G733: {pct}% ({status_str})")
        else:
            self.lbl_header_battery.setText("🔋 G733: Offline")

    def speak_current_battery(self):
        """Speaks the current battery percentage out loud."""
        pct, status_str, mV = get_g733_battery_info()
        if pct is not None:
            speak_text(f"Battery {pct} percent")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText(f"{pct}% ({status_str}) — 🔊 Announced!")
            if hasattr(self, 'lbl_header_battery'):
                self.lbl_header_battery.setText(f"🔊 G733: {pct}% ({status_str.split()[0]})")
            logging.info(f"Spoken battery announcement triggered: {pct}%")
        else:
            speak_text("Headset disconnected")
            if hasattr(self, 'lbl_hs_battery_pct'):
                self.lbl_hs_battery_pct.setText("Disconnected")
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

            action_show = QAction("🖥️ Open Control Center", self)
            action_show.triggered.connect(self.restore_from_tray)
            tray_menu.addAction(action_show)

            action_speak_bat = QAction("🔊 Hear Battery Charge %", self)
            action_speak_bat.triggered.connect(self.speak_current_battery)
            tray_menu.addAction(action_speak_bat)

            self.action_toggle_mic = QAction("🎙️ Mute/Unmute Mic", self)
            self.action_toggle_mic.triggered.connect(self.toggle_headset_mic)
            tray_menu.addAction(self.action_toggle_mic)

            self.action_toggle_daemon = QAction("⚡ Toggle Macro Service", self)
            self.action_toggle_daemon.triggered.connect(self.toggle_service)
            tray_menu.addAction(self.action_toggle_daemon)

            tray_menu.addSeparator()

            action_settings = QAction("⚙️ Settings", self)
            action_settings.triggered.connect(self.open_settings_dialog)
            tray_menu.addAction(action_settings)

            action_quit = QAction("🚪 Quit App", self)
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
            if settings.get("show_notifications", True):
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
            event.accept()

    def show_hamburger_menu(self):
        menu = QMenu(self)
        
        act_mouse = menu.addAction("🖱️ Switch to G502 Gaming Mouse")
        act_mouse.triggered.connect(lambda: self.combo_main_device.setCurrentIndex(0))
        
        act_headset = menu.addAction("🎧 Switch to G733 Gaming Headset")
        act_headset.triggered.connect(lambda: self.combo_main_device.setCurrentIndex(1))
        
        menu.addSeparator()
        act_settings = menu.addAction("⚙️ Settings && Diagnostics Studio")
        act_settings.triggered.connect(self.open_settings_dialog)

        menu.addSeparator()
        act_speak = menu.addAction("🔊 Hear Remaining Battery Charge %")
        act_speak.triggered.connect(self.speak_current_battery)

        act_mic = menu.addAction("🎙️ Toggle Headset Mic Mute")
        act_mic.triggered.connect(self.toggle_headset_mic)

        act_toggle = menu.addAction("⚡ Toggle Background Macro Service")
        act_toggle.triggered.connect(self.toggle_service)

        menu.addSeparator()
        act_github = menu.addAction("🌐 Open GitHub Repository")
        act_github.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))

        act_quit = menu.addAction("❌ Quit Control Center")
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

    # ------------------ Mouse Customization Tabs ------------------
    def get_selected_ratbag_dev_id(self):
        return "cheering-viscacha"

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
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        config_data = self.load_macro_config()
        self.buttons_cfg = config_data.get("buttons", {})

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left Card: Physical Mouse Button Map + Hardware Diagram
        left_card = self.register_card(QGroupBox("Select Mouse Button to Customize"))
        model_column = QVBoxLayout(left_card)
        model_column.setSpacing(8)
        model_column.setContentsMargins(12, 10, 12, 12)

        if os.path.exists(DIAGRAM_PATH):
            lbl_diag = QLabel()
            lbl_diag.setObjectName("diagramImage")
            pix = QPixmap(DIAGRAM_PATH).scaledToHeight(165, Qt.TransformationMode.SmoothTransformation)
            lbl_diag.setPixmap(pix)
            lbl_diag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            model_column.addWidget(lbl_diag)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        buttons_list_info = [
            ("G8", "G8 — Resolution Up (Top Button)"),
            ("TILT_LEFT", "Wheel Tilt Left (Scroll Left)"),
            ("TILT_RIGHT", "Wheel Tilt Right (Scroll Right)"),
            ("G7", "G7 — Resolution Down (Thumb/Side)"),
            ("G9", "G9 — Resolution Switch (Profile)")
        ]

        self.selector_buttons = {}
        for btn_key, btn_label in buttons_list_info:
            b = QPushButton(f"●   {btn_label}")
            b.setObjectName("btnSelector")
            b.setCheckable(True)
            b.setFixedHeight(38)
            if btn_key == self.active_button_key:
                b.setChecked(True)
            b.clicked.connect(lambda _, k=btn_key: self.select_button(k))
            self.btn_group.addButton(b)
            model_column.addWidget(b)
            self.selector_buttons[btn_key] = b

        model_column.addStretch()
        content_layout.addWidget(left_card, stretch=4)

        # Right Card: Macro Action & Timing Customizer
        self.customizer_box = self.register_card(QGroupBox("Customize Selected Button Macro"))
        customizer_layout = QVBoxLayout(self.customizer_box)
        customizer_layout.setSpacing(12)
        customizer_layout.setContentsMargins(14, 10, 14, 14)

        self.selected_title_lbl = QLabel("Editing: G8 — Resolution Up")
        self.selected_title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.selected_title_lbl.setObjectName("accentTitle")
        customizer_layout.addWidget(self.selected_title_lbl)

        customizer_layout.addWidget(QLabel("Assigned Macro Behavior:"))
        self.combo_action = QComboBox()
        for label, code in ACTION_TYPES:
            self.combo_action.addItem(label, code)
        self.combo_action.currentIndexChanged.connect(self.on_active_action_changed)
        customizer_layout.addWidget(self.combo_action)

        self.lbl_custom_key = QLabel("Custom Key to Repeat:")
        customizer_layout.addWidget(self.lbl_custom_key)
        self.combo_key = QComboBox()
        for label, code in CUSTOM_KEYS:
            self.combo_key.addItem(label, code)
        self.combo_key.currentIndexChanged.connect(self.on_active_field_changed)
        customizer_layout.addWidget(self.combo_key)

        customizer_layout.addWidget(QLabel("Key / Click Hold Duration (ms):"))
        self.spin_hold = QSpinBox()
        self.spin_hold.setRange(5, 500)
        self.spin_hold.setSingleStep(5)
        self.spin_hold.setSuffix(" ms")
        self.spin_hold.valueChanged.connect(self.on_active_field_changed)
        customizer_layout.addWidget(self.spin_hold)

        customizer_layout.addWidget(QLabel("Loop Repeat Interval Delay (ms):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(5, 1000)
        self.spin_delay.setSingleStep(5)
        self.spin_delay.setSuffix(" ms")
        self.spin_delay.valueChanged.connect(self.on_active_field_changed)
        customizer_layout.addWidget(self.spin_delay)

        summary_frame = QFrame()
        summary_frame.setObjectName("summaryBox")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        self.summary_lbl = QLabel("Summary: Holding G8 will repeat Left Click.")
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setObjectName("subText")
        summary_layout.addWidget(self.summary_lbl)
        customizer_layout.addWidget(summary_frame)

        customizer_layout.addStretch()
        content_layout.addWidget(self.customizer_box, stretch=5)

        layout.addLayout(content_layout)

        btn_bar = QHBoxLayout()
        btn_save = QPushButton("💾   Save && Apply All Macro Settings (Auto-Restarts Service)")
        btn_save.setObjectName("accentBtn")
        btn_save.setFixedHeight(42)
        btn_save.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_save.clicked.connect(self.save_macro_config)
        btn_bar.addWidget(btn_save)

        layout.addLayout(btn_bar)

        self.select_button("G8")
        return tab

    def select_button(self, btn_key):
        self.active_button_key = btn_key
        btn_titles = {
            "G8": "G8 — Resolution Up (Top Button)",
            "TILT_LEFT": "Wheel Tilt Left (Scroll Left)",
            "TILT_RIGHT": "Wheel Tilt Right (Scroll Right)",
            "G7": "G7 — Resolution Down (Thumb/Side)",
            "G9": "G9 — Resolution Switch (Profile)"
        }
        self.selected_title_lbl.setText(f"Editing Macro: {btn_titles.get(btn_key, btn_key)}")

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

    def save_macro_config(self):
        new_cfg = {"buttons": self.buttons_cfg}
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
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        guide = self.register_card(QFrame())
        guide.setObjectName("guideBox")
        guide_layout = QVBoxLayout(guide)
        guide_layout.setContentsMargins(12, 10, 12, 10)
        guide_title = QLabel("💡 DPI & Pointer Speed Reference Guide")
        guide_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        guide_title.setObjectName("accentTitle")
        guide_text = QLabel(
            "• Hardware DPI: Optical sensor resolution stored on mouse onboard memory via libratbagd.\n"
            "• Flat Acceleration (1:1): Raw linear input matching Windows 6/11 with Enhance Pointer Precision OFF.\n"
            "• Perfect 1:1 Calibration: Computes the exact sub-decimal KWin multiplier for your target physical px/cm."
        )
        guide_text.setObjectName("subText")
        guide_layout.addWidget(guide_title)
        guide_layout.addWidget(guide_text)
        layout.addWidget(guide)

        dpi_group = self.register_card(QGroupBox("Hardware DPI Settings (Onboard Profiles)"))
        dpi_layout = QVBoxLayout(dpi_group)
        dpi_layout.setSpacing(10)

        dpi_top_layout = QHBoxLayout()
        dpi_label = QLabel("Active Hardware Sensor DPI:")
        dpi_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.dpi_val_label = QLabel("800 DPI")
        self.dpi_val_label.setObjectName("valueBadge")
        dpi_top_layout.addWidget(dpi_label)
        dpi_top_layout.addWidget(self.dpi_val_label)
        dpi_top_layout.addStretch()

        dpi_layout.addLayout(dpi_top_layout)

        self.dpi_slider = QSlider(Qt.Orientation.Horizontal)
        self.dpi_slider.setRange(400, 4000)
        self.dpi_slider.setSingleStep(50)
        self.dpi_slider.setValue(800)
        self.dpi_slider.valueChanged.connect(self.on_dpi_slider_changed)
        dpi_layout.addWidget(self.dpi_slider)

        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick Presets:"))
        for dpi in [400, 800, 1000, 1200, 1600, 2400, 3200]:
            btn = QPushButton(f"{dpi}")
            btn.setFixedWidth(68)
            btn.clicked.connect(lambda _, d=dpi: self.set_dpi(d))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        dpi_layout.addLayout(preset_layout)

        layout.addWidget(dpi_group)

        speed_group = self.register_card(QGroupBox("Desktop Pointer Speed && Acceleration (KDE KWin / libinput)"))
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.setSpacing(10)

        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Acceleration Profile:"))
        self.combo_profile = QComboBox()
        self.combo_profile.addItems(["Flat (1:1 Raw Linear - Recommended)", "Adaptive (Windows-style Curve)"])
        self.combo_profile.currentIndexChanged.connect(self.on_accel_profile_changed)
        profile_layout.addWidget(self.combo_profile)
        profile_layout.addStretch()
        speed_layout.addLayout(profile_layout)

        speed_slider_layout = QHBoxLayout()
        speed_slider_layout.addWidget(QLabel("Pointer Speed Scale:"))
        self.speed_val_label = QLabel("0.600")
        self.speed_val_label.setObjectName("valueBadge")
        speed_slider_layout.addWidget(self.speed_val_label)
        speed_slider_layout.addStretch()
        speed_layout.addLayout(speed_slider_layout)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(-100, 100)
        self.speed_slider.setValue(60)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)

        layout.addWidget(speed_group)
        
        calib_group = self.register_card(QGroupBox("Perfect 1:1 Pixel-per-Centimeter Calibration"))
        calib_layout = QVBoxLayout(calib_group)
        calib_layout.setSpacing(10)
        calib_row = QHBoxLayout()
        calib_row.addWidget(QLabel("Target Pixels per cm:"))
        self.spin_px_cm = QDoubleSpinBox()
        self.spin_px_cm.setRange(10.0, 5000.0)
        self.spin_px_cm.setDecimals(2)
        self.spin_px_cm.setValue(265.72)
        self.spin_px_cm.setSuffix(" px/cm")
        self.spin_px_cm.setMinimumWidth(140)
        calib_row.addWidget(self.spin_px_cm)
        
        btn_calib = QPushButton("🎯  Calibrate Exact 1:1 Mapping")
        btn_calib.setObjectName("accentBtn")
        btn_calib.clicked.connect(self.apply_exact_calibration)
        calib_row.addWidget(btn_calib)
        calib_row.addStretch()
        calib_layout.addLayout(calib_row)
        
        calib_help = QLabel("Locks hardware DPI to 1000 and calculates the exact floating-point KWin pointer multiplier (flat profile) to physically match your Windows px/cm sensitivity.")
        calib_help.setObjectName("subText")
        calib_help.setWordWrap(True)
        calib_layout.addWidget(calib_help)
        
        layout.addWidget(calib_group)
        
        layout.addStretch()
        return tab

    def create_rgb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        rgb_group = self.register_card(QGroupBox("OpenRGB && Mouse Lighting Integration"))
        rgb_layout = QVBoxLayout(rgb_group)
        rgb_layout.setSpacing(12)

        rgb_layout.addWidget(QLabel("Manage OpenRGB lighting profiles and official Piper hardware configuration:"))

        btn_apply_black = QPushButton("🌑  Apply 'ALL Black' Stealth Preset Now")
        btn_apply_black.setObjectName("accentBtn")
        btn_apply_black.setFixedHeight(38)
        btn_apply_black.clicked.connect(self.apply_all_black_rgb)
        rgb_layout.addWidget(btn_apply_black)

        btn_piper_gui = QPushButton("🖱️  Launch Official Piper GTK App")
        btn_piper_gui.setFixedHeight(38)
        btn_piper_gui.clicked.connect(lambda: subprocess.Popen(['piper']))
        rgb_layout.addWidget(btn_piper_gui)

        btn_openrgb_gui = QPushButton("🌈  Launch Full OpenRGB Studio GUI")
        btn_openrgb_gui.setFixedHeight(38)
        btn_openrgb_gui.clicked.connect(lambda: subprocess.Popen(['openrgb', '--gui']))
        rgb_layout.addWidget(btn_openrgb_gui)

        layout.addWidget(rgb_group)
        layout.addStretch()
        return tab

    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(2, 4, 2, 2)

        log_group = self.register_card(QGroupBox("Systemd Macro Service Journal Logs"))
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(10)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Live stream from g502-macros.service:"))
        top_layout.addStretch()

        btn_refresh = QPushButton("🔄  Refresh Logs")
        btn_refresh.clicked.connect(self.refresh_logs)
        top_layout.addWidget(btn_refresh)

        log_layout.addLayout(top_layout)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)

        layout.addWidget(log_group)

        self.refresh_logs()
        return tab

    # ------------------ Headset Customization Tabs ------------------
    def create_headset_sound_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        vol_group = self.register_card(QGroupBox("Master Headphone Audio Volume && Output Sink"))
        vlayout = QVBoxLayout(vol_group)
        vlayout.setSpacing(10)

        v_top = QHBoxLayout()
        v_top.addWidget(QLabel("Headset Master Volume:"))
        self.lbl_hs_vol = QLabel("56%")
        self.lbl_hs_vol.setObjectName("valueBadge")
        v_top.addWidget(self.lbl_hs_vol)
        v_top.addStretch()
        
        self.btn_hs_mute = QPushButton("🔊  Mute Audio")
        self.btn_hs_mute.clicked.connect(self.toggle_headset_audio_mute)
        v_top.addWidget(self.btn_hs_mute)

        vlayout.addLayout(v_top)

        self.hs_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.hs_vol_slider.setRange(0, 100)
        self.hs_vol_slider.setValue(56)
        self.hs_vol_slider.valueChanged.connect(self.on_hs_vol_changed)
        vlayout.addWidget(self.hs_vol_slider)

        layout.addWidget(vol_group)

        eq_group = self.register_card(QGroupBox("Headphone 10-Band Hardware Equalizer && Audio Presets"))
        eq_layout = QVBoxLayout(eq_group)
        eq_layout.setSpacing(14)

        preset_box = QHBoxLayout()
        preset_box.addWidget(QLabel("Audio Profile Presets:"))
        for preset_name in ["Flat 1:1", "FPS Gaming", "Bass Boost", "Cinematic"]:
            btn = QPushButton(preset_name)
            btn.clicked.connect(lambda _, p=preset_name: self.apply_eq_preset(p))
            preset_box.addWidget(btn)
        preset_box.addStretch()
        eq_layout.addLayout(preset_box)

        bands_layout = QHBoxLayout()
        bands = [("60Hz\nLow Bass", 0), ("250Hz\nBass", 0), ("1kHz\nMids", 0), ("4kHz\nHighs", 0), ("12kHz\nTreble", 0)]
        self.eq_sliders = []
        for name, def_val in bands:
            bcol = QVBoxLayout()
            bcol.setSpacing(8)
            lbl_name = QLabel(name)
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_name.setObjectName("subText")
            bcol.addWidget(lbl_name, alignment=Qt.AlignmentFlag.AlignCenter)
            sl = QSlider(Qt.Orientation.Vertical)
            sl.setRange(-12, 12)
            sl.setValue(def_val)
            sl.setFixedHeight(135)
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
        
        # Try to initialize EQ on start
        QTimer.singleShot(500, self.on_eq_changed)
        
        return tab

    def on_eq_changed(self):
        try:
            # Get the 5 slider values
            v = [sl.value() for sl in self.eq_sliders]
            if len(v) != 5: return
            
            # Map 5 bands to G733's 10 bands (32, 64, 125, 250, 500, 1k, 2k, 4k, 8k, 16k)
            bands_10 = [
                v[0],            # 32Hz  (Low Bass)
                v[0],            # 64Hz  
                (v[0]+v[1])//2,  # 125Hz 
                v[1],            # 250Hz (Bass)
                (v[1]+v[2])//2,  # 500Hz
                v[2],            # 1kHz  (Mids)
                (v[2]+v[3])//2,  # 2kHz
                v[3],            # 4kHz  (Highs)
                (v[3]+v[4])//2,  # 8kHz
                v[4],            # 16kHz (Treble)
            ]
            
            # Ensure signed bytes (8-bit two's complement)
            bands_10_bytes = [ (x + 256) % 256 for x in bands_10 ]
            
            # Send to hidraw asynchronously
            def _send_eq():
                dev_path = find_g733_hidraw()
                if not dev_path: return
                try:
                    fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
                    
                    # 1. Ask Root feature 0x0000 for Equalizer feature index (0x8310)
                    os.write(fd, bytes([0x11, 0xFF, 0x00, 0x10, 0x83, 0x10] + [0]*14))
                    
                    # Wait and read response
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
                                
                    # 2. If feature index found, SET EQUALIZER (Command 0x20)
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
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        mic_group = self.register_card(QGroupBox("Microphone Gain && Mute Controls"))
        mlayout = QVBoxLayout(mic_group)
        mlayout.setSpacing(10)

        m_top = QHBoxLayout()
        m_top.addWidget(QLabel("Mic Gain Level:"))
        self.lbl_mic_vol = QLabel("100%")
        self.lbl_mic_vol.setObjectName("valueBadge")
        m_top.addWidget(self.lbl_mic_vol)
        m_top.addStretch()

        self.btn_mic_mute = QPushButton("🎙️  Mic LIVE (Click to Mute)")
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

        side_group = self.register_card(QGroupBox("Sidetone (Hardware Microphone Monitoring)"))
        slayout = QVBoxLayout(side_group)
        slayout.setSpacing(10)

        s_top = QHBoxLayout()
        s_top.addWidget(QLabel("Sidetone Feedback Volume:"))
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

        side_hint = QLabel("Sidetone routes your voice directly in hardware with zero latency so you can speak naturally.")
        side_hint.setObjectName("subText")
        slayout.addWidget(side_hint)
        layout.addWidget(side_group)

        meter_group = self.register_card(QGroupBox("Live Mic Level Monitor"))
        meter_layout = QVBoxLayout(meter_group)
        meter_layout.setSpacing(8)
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

    def toggle_headset_mic(self):
        subprocess.run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SOURCE@', 'toggle'], stdout=subprocess.DEVNULL)
        res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], capture_output=True, text=True)
        if '[MUTED]' in res.stdout:
            self.btn_mic_mute.setText("🔇  Mic MUTED")
            self.btn_mic_mute.setObjectName("stopBtn")
        else:
            self.btn_mic_mute.setText("🎙️  Mic LIVE (Click to Mute)")
            self.btn_mic_mute.setObjectName("accentBtn")
        self.btn_mic_mute.setStyle(self.btn_mic_mute.style())

    def on_sidetone_changed(self, val):
        self.lbl_sidetone.setText(f"{val}%")
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
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        rgb_group = self.register_card(QGroupBox("Targeted G733 Headset RGB Lightstrip Customizer (HID++)"))
        rlayout = QVBoxLayout(rgb_group)
        rlayout.setSpacing(12)

        rlayout.addWidget(QLabel("Directly controls the G733 dual-zone front lightstrips without affecting other devices:"))

        eff_layout = QHBoxLayout()
        eff_layout.addWidget(QLabel("Lighting Effect Mode:"))
        self.combo_hs_effect = QComboBox()
        self.combo_hs_effect.addItem("Static Color", 1)
        self.combo_hs_effect.addItem("Breathing Pulse", 2)
        self.combo_hs_effect.addItem("Spectrum Cycle", 3)
        self.combo_hs_effect.addItem("Stealth (LEDs OFF)", 0)
        self.combo_hs_effect.currentIndexChanged.connect(self.on_hs_effect_changed)
        eff_layout.addWidget(self.combo_hs_effect)
        eff_layout.addStretch()
        rlayout.addLayout(eff_layout)

        btn_color = QPushButton("🎨  Pick Headset Color (Opens Color Picker)...")
        btn_color.setObjectName("accentBtn")
        btn_color.setFixedHeight(38)
        btn_color.clicked.connect(self.choose_headset_rgb_color)
        rlayout.addWidget(btn_color)

        palette_box = QHBoxLayout()
        palette_box.addWidget(QLabel("Quick Color Palettes:"))
        colors = [
            ("Cyan", 0, 255, 255),
            ("Purple", 180, 0, 255),
            ("Emerald", 0, 255, 102),
            ("Red", 255, 0, 51),
            ("Solar", 255, 200, 0),
            ("Stealth OFF", 0, 0, 0)
        ]
        for cname, r, g, b in colors:
            btn = QPushButton(cname)
            btn.clicked.connect(lambda _, cr=r, cg=g, cb=b: set_g733_rgb(cr, cg, cb, mode=1 if (cr or cg or cb) else 0))
            palette_box.addWidget(btn)
        palette_box.addStretch()
        rlayout.addLayout(palette_box)

        layout.addWidget(rgb_group)
        layout.addStretch()
        return tab

    def on_hs_effect_changed(self, idx):
        mode = self.combo_hs_effect.currentData()
        if mode == 0:
            set_g733_rgb(0, 0, 0, mode=0)
        elif mode == 3:
            set_g733_rgb(0, 255, 255, mode=3)
        else:
            set_g733_rgb(56, 189, 248, mode=mode)

    def choose_headset_rgb_color(self):
        color = QColorDialog.getColor(QColor("#38BDF8"), self, "Pick G733 Headset RGB Color")
        if color.isValid():
            set_g733_rgb(color.red(), color.green(), color.blue(), mode=1)

    # ------------------ Battery & Info Tab ------------------
    def create_headset_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(2, 4, 2, 2)

        bat_group = self.register_card(QGroupBox("Wireless Battery Indication && Voice Announcement"))
        blayout = QVBoxLayout(bat_group)
        blayout.setSpacing(10)

        b_top = QHBoxLayout()
        b_top.addWidget(QLabel("Battery Charge Level:"))
        self.lbl_hs_battery_pct = QLabel("85% (Discharging)")
        self.lbl_hs_battery_pct.setObjectName("valueBadge")
        b_top.addWidget(self.lbl_hs_battery_pct)
        b_top.addStretch()

        btn_speak = QPushButton("🔊  Hear Battery Charge % (Voice)")
        btn_speak.setObjectName("accentBtn")
        btn_speak.clicked.connect(self.speak_current_battery)
        b_top.addWidget(btn_speak)

        blayout.addLayout(b_top)

        self.bar_hs_battery = QProgressBar()
        self.bar_hs_battery.setRange(0, 100)
        self.bar_hs_battery.setValue(85)
        blayout.addWidget(self.bar_hs_battery)

        self.lbl_hs_mv = QLabel("Voltage: 3958 mV (Smoothed G HUB 5% steps)")
        self.lbl_hs_mv.setObjectName("subText")
        blayout.addWidget(self.lbl_hs_mv)

        note_label = QLabel("💡 Pressing the power button on your headset (or clicking above) speaks the remaining battery charge out loud.")
        note_label.setObjectName("accentTitle")
        blayout.addWidget(note_label)

        layout.addWidget(bat_group)

        grp = self.register_card(QGroupBox("G733 Hardware Information && Connection"))
        glayout = QVBoxLayout(grp)

        info_text = QLabel(
            "• Model: Logitech G733 LIGHTSPEED Wireless Gaming Headset\n"
            "• USB Product ID: 046d:0ab5\n"
            "• Driver Backend: Native HID++ 2.0 + PipeWire / WirePlumber + ALSA\n"
            "• Connection Type: 2.4GHz LIGHTSPEED Wireless Dongle\n"
            "• Status: ONLINE & Connected"
        )
        info_text.setFont(QFont("Segoe UI", 11))
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
                self.status_badge.setText("● MACROS ACTIVE")
                self.status_badge.setObjectName("statusBadgeActive")
                self.btn_toggle_service.setText("Stop Service")
                self.btn_toggle_service.setObjectName("stopBtn")
            else:
                self.status_badge.setText("● MACROS INACTIVE")
                self.status_badge.setObjectName("statusBadgeInactive")
                self.btn_toggle_service.setText("Start Service")
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
        self.dpi_val_label.setText(f"{val} DPI")
        self.set_dpi(val)

    def set_dpi(self, dpi):
        self.dpi_slider.blockSignals(True)
        self.dpi_slider.setValue(dpi)
        self.dpi_slider.blockSignals(False)
        self.dpi_val_label.setText(f"{dpi} DPI")

        dev_id = self.get_selected_ratbag_dev_id()
        if dev_id:
            for p in [0, 1, 2]:
                subprocess.run(['ratbagctl', dev_id, 'profile', str(p), 'resolution', '0', 'dpi', 'set', str(dpi)], stdout=subprocess.DEVNULL)
                subprocess.run(['ratbagctl', dev_id, 'profile', str(p), 'resolution', 'active', 'set', '0'], stdout=subprocess.DEVNULL)

    def get_kwin_mouse_paths(self):
        paths = []
        try:
            import re
            tree = subprocess.check_output(['busctl', '--user', 'tree', 'org.kde.KWin'], text=True)
            all_paths = re.findall(r'/org/kde/KWin/InputDevice/event\d+', tree)
            for p in all_paths:
                try:
                    name = subprocess.check_output(['busctl', '--user', 'get-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'name'], text=True)
                    if 'G502' in name:
                        paths.append(p)
                except:
                    pass
        except:
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
        subprocess.run(['openrgb', '--profile', 'ALL Black'], stdout=subprocess.DEVNULL)
        set_g733_rgb(0, 0, 0, mode=0)
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
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
