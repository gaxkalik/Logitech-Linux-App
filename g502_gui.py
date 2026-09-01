#!/usr/bin/env python3
"""
AGY Logitech G502 Control Center & Macro Customization Studio
--------------------------------------------------------------
A modern PyQt6 GUI application to configure:
  - Customizable G502 Macros (Actions, Custom Keys, Hold & Delay Timings)
  - Live reload via ~/.config/g502_macros/config.json + SIGHUP
  - Hardware DPI & Onboard Profiles via ratbagctl
  - KDE KWin Pointer Acceleration Profile (Flat vs Adaptive) & Pointer Speed live
  - OpenRGB Profile presets (ALL Black)
  - Systemd User Service autostart controls
"""

import sys
import os
import time
import subprocess
import json
import logging

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QCheckBox, QGroupBox,
    QTabWidget, QTextEdit, QFrame, QSpinBox, QDoubleSpinBox, QStackedWidget,
    QGraphicsDropShadowEffect, QMessageBox, QScrollArea, QGridLayout
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

CONFIG_PATH = os.path.expanduser('~/.config/g502_macros/config.json')

QSS_STYLE = """
QMainWindow {
    background-color: #0F1015;
    color: #E2E8F0;
}

QWidget {
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    color: #E2E8F0;
}

QTabWidget::pane {
    border: 1px solid #1E293B;
    background-color: #161922;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #0F1015;
    color: #94A3B8;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #161922;
    color: #38BDF8;
    border-bottom: 2px solid #38BDF8;
}

QTabBar::tab:hover {
    color: #F1F5F9;
    background-color: #1E293B;
}

QGroupBox {
    font-weight: bold;
    font-size: 14px;
    border: 1px solid #1E293B;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: #161922;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #38BDF8;
}

QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #38BDF8;
    color: #38BDF8;
}

QPushButton:pressed {
    background-color: #0F172A;
}

QPushButton#accentBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #06B6D4);
    color: #FFFFFF;
    border: none;
}

QPushButton#accentBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:1 #0891B2);
}

QPushButton#stopBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
    color: #FFFFFF;
    border: none;
}

QPushButton#stopBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #1E293B;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38BDF8, stop:1 #818CF8);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #F8FAFC;
    border: 2px solid #38BDF8;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #38BDF8;
    border-color: #FFFFFF;
}

QComboBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F8FAFC;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #38BDF8;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    color: #F8FAFC;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
    border: 1px solid #334155;
}

QSpinBox, QDoubleSpinBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F8FAFC;
    font-size: 13px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #38BDF8;
}

QTextEdit {
    background-color: #090A0F;
    border: 1px solid #1E293B;
    border-radius: 6px;
    color: #38BDF8;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}

QLabel#statusBadgeActive {
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}

QLabel#statusBadgeInactive {
    background-color: #451A03;
    color: #FDBA74;
    border: 1px solid #D97706;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}
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

def get_g502_ratbag_device():
    try:
        out = subprocess.check_output(['ratbagctl', 'list'], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if 'G502' in line:
                return line.split(':')[0].strip()
    except Exception:
        pass
    return None

class G502ControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGY Logitech G502 Control Center & Macro Studio")
        self.resize(920, 680)
        self.setStyleSheet(QSS_STYLE)

        self.ratbag_dev = get_g502_ratbag_device()
        self.macro_widgets = {}  # btn_key -> dict of controls

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header Bar
        header = QFrame()
        header.setStyleSheet("background-color: #161922; border-radius: 10px; border: 1px solid #1E293B;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_layout = QVBoxLayout()
        title_label = QLabel("Logitech G502 Control Center")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #F8FAFC;")
        subtitle_label = QLabel("Customizable Macro Studio, Hardware DPI & Pointer Speed Tuning")
        subtitle_label.setStyleSheet("color: #64748B; font-size: 12px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Daemon Status Indicator
        self.status_badge = QLabel("CHECKING...")
        self.status_badge.setObjectName("statusBadgeInactive")
        header_layout.addWidget(self.status_badge)

        self.btn_toggle_service = QPushButton("Start Service")
        self.btn_toggle_service.setObjectName("accentBtn")
        self.btn_toggle_service.clicked.connect(self.toggle_service)
        header_layout.addWidget(self.btn_toggle_service)

        main_layout.addWidget(header)

        # Tab Navigation
        tabs = QTabWidget()
        tabs.addTab(self.create_macro_studio_tab(), "Macro Customization Studio")
        tabs.addTab(self.create_dashboard_tab(), "DPI & Pointer Speed")
        tabs.addTab(self.create_rgb_tab(), "RGB Lighting")
        tabs.addTab(self.create_logs_tab(), "Service Logs")
        main_layout.addWidget(tabs)

        # Status Update Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_daemon_status)
        self.timer.start(2000)
        self.update_daemon_status()

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

    def create_macro_studio_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        config_data = self.load_macro_config()
        buttons_cfg = config_data.get("buttons", {})

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        buttons_info = [
            ("G8", "G8 Button (DPI Up)"),
            ("TILT_LEFT", "Wheel Tilt Left"),
            ("TILT_RIGHT", "Wheel Tilt Right"),
            ("G7", "G7 Button (DPI Down)"),
            ("G9", "G9 Button (Profile Select)")
        ]

        for btn_key, btn_title in buttons_info:
            btn_data = buttons_cfg.get(btn_key, {})

            box = QGroupBox(btn_title)
            box_layout = QGridLayout(box)
            box_layout.setSpacing(10)

            # Action Selector
            box_layout.addWidget(QLabel("Macro Action:"), 0, 0)
            combo_action = QComboBox()
            for label, code in ACTION_TYPES:
                combo_action.addItem(label, code)

            # Set current action index
            current_action = btn_data.get("action_type", "LEFT_CLICK_LOOP")
            for idx in range(combo_action.count()):
                if combo_action.itemData(idx) == current_action:
                    combo_action.setCurrentIndex(idx)
                    break
            box_layout.addWidget(combo_action, 0, 1)

            # Custom Key Selector
            lbl_custom_key = QLabel("Custom Key:")
            box_layout.addWidget(lbl_custom_key, 0, 2)
            combo_key = QComboBox()
            for label, code in CUSTOM_KEYS:
                combo_key.addItem(label, code)

            current_key = btn_data.get("custom_key", "KEY_SPACE")
            for idx in range(combo_key.count()):
                if combo_key.itemData(idx) == current_key:
                    combo_key.setCurrentIndex(idx)
                    break
            box_layout.addWidget(combo_key, 0, 3)

            # Hold Duration (ms)
            box_layout.addWidget(QLabel("Hold (ms):"), 1, 0)
            spin_hold = QSpinBox()
            spin_hold.setRange(5, 500)
            spin_hold.setSingleStep(5)
            spin_hold.setValue(btn_data.get("hold_ms", 20))
            box_layout.addWidget(spin_hold, 1, 1)

            # Repeat Delay (ms)
            box_layout.addWidget(QLabel("Delay (ms):"), 1, 2)
            spin_delay = QSpinBox()
            spin_delay.setRange(5, 1000)
            spin_delay.setSingleStep(5)
            spin_delay.setValue(btn_data.get("delay_ms", 50))
            box_layout.addWidget(spin_delay, 1, 3)

            # Visibility toggle for custom key box
            def update_key_vis(idx=0, c_lbl=lbl_custom_key, c_key=combo_key, c_act=combo_action):
                is_custom = (c_act.currentData() == "CUSTOM_KEY_LOOP")
                c_lbl.setVisible(is_custom)
                c_key.setVisible(is_custom)

            combo_action.currentIndexChanged.connect(update_key_vis)
            update_key_vis()

            scroll_layout.addWidget(box)

            self.macro_widgets[btn_key] = {
                "combo_action": combo_action,
                "combo_key": combo_key,
                "spin_hold": spin_hold,
                "spin_delay": spin_delay
            }

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Save Button Bar
        btn_bar = QHBoxLayout()

        btn_save = QPushButton("Save & Apply All Macro Settings")
        btn_save.setObjectName("accentBtn")
        btn_save.setFixedHeight(40)
        btn_save.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_save.clicked.connect(self.save_macro_config)
        btn_bar.addWidget(btn_save)

        layout.addLayout(btn_bar)
        return tab

    def save_macro_config(self):
        new_cfg = {"buttons": {}}
        for btn_key, widgets in self.macro_widgets.items():
            action_code = widgets["combo_action"].currentData()
            custom_key = widgets["combo_key"].currentData()
            hold_ms = widgets["spin_hold"].value()
            delay_ms = widgets["spin_delay"].value()

            new_cfg["buttons"][btn_key] = {
                "name": btn_key,
                "action_type": action_code,
                "hold_ms": hold_ms,
                "delay_ms": delay_ms,
                "custom_key": custom_key
            }

        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(new_cfg, f, indent=4)

        # Send SIGHUP signal to macro daemon to reload config dynamically
        subprocess.run(['pkill', '-HUP', '-f', 'g502_macro_daemon.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        QMessageBox.information(self, "Macro Studio", "Macro settings saved & applied live to G502 daemon!")

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        # DPI Settings Group
        dpi_group = QGroupBox("Hardware DPI Settings (Onboard Profiles 0, 1, 2)")
        dpi_layout = QVBoxLayout(dpi_group)

        dpi_top_layout = QHBoxLayout()
        dpi_label = QLabel("Active Hardware DPI:")
        dpi_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.dpi_val_label = QLabel("1200 DPI")
        self.dpi_val_label.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 15px;")
        dpi_top_layout.addWidget(dpi_label)
        dpi_top_layout.addWidget(self.dpi_val_label)
        dpi_top_layout.addStretch()

        dpi_layout.addLayout(dpi_top_layout)

        # DPI Slider
        self.dpi_slider = QSlider(Qt.Orientation.Horizontal)
        self.dpi_slider.setRange(400, 4000)
        self.dpi_slider.setSingleStep(50)
        self.dpi_slider.setValue(1200)
        self.dpi_slider.valueChanged.connect(self.on_dpi_slider_changed)
        dpi_layout.addWidget(self.dpi_slider)

        # Quick Preset Buttons
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick Presets:"))
        for dpi in [400, 800, 1000, 1200, 1600, 2400, 3200]:
            btn = QPushButton(f"{dpi}")
            btn.setFixedWidth(64)
            btn.clicked.connect(lambda _, d=dpi: self.set_dpi(d))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        dpi_layout.addLayout(preset_layout)

        layout.addWidget(dpi_group)

        # Pointer Speed Group
        speed_group = QGroupBox("Desktop Pointer Speed & Acceleration (KDE KWin / libinput)")
        speed_layout = QVBoxLayout(speed_group)

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
        self.speed_val_label.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 14px;")
        speed_slider_layout.addWidget(self.speed_val_label)
        speed_slider_layout.addStretch()
        speed_layout.addLayout(speed_slider_layout)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(-100, 100)
        self.speed_slider.setValue(60)  # 0.600
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)

        layout.addWidget(speed_group)
        layout.addStretch()
        return tab

    def create_rgb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        rgb_group = QGroupBox("OpenRGB Lighting Control")
        rgb_layout = QVBoxLayout(rgb_group)

        rgb_layout.addWidget(QLabel("Manage OpenRGB lighting profiles for your system and RAM/Motherboard LEDs:"))

        btn_apply_black = QPushButton("Apply 'ALL Black' Preset Now")
        btn_apply_black.setObjectName("accentBtn")
        btn_apply_black.clicked.connect(self.apply_all_black_rgb)
        rgb_layout.addWidget(btn_apply_black)

        btn_openrgb_gui = QPushButton("Launch Full OpenRGB GUI")
        btn_openrgb_gui.clicked.connect(lambda: subprocess.Popen(['openrgb', '--gui']))
        rgb_layout.addWidget(btn_openrgb_gui)

        layout.addWidget(rgb_group)
        layout.addStretch()
        return tab

    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Systemd Macro Service Journal Logs:"))
        top_layout.addStretch()

        btn_refresh = QPushButton("Refresh Logs")
        btn_refresh.clicked.connect(self.refresh_logs)
        top_layout.addWidget(btn_refresh)

        layout.addLayout(top_layout)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.refresh_logs()
        return tab

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

        dev = get_g502_ratbag_device()
        if dev:
            for p in [0, 1, 2]:
                subprocess.run(['ratbagctl', dev, 'profile', str(p), 'resolution', '0', 'dpi', 'set', str(dpi)], stdout=subprocess.DEVNULL)
                subprocess.run(['ratbagctl', dev, 'profile', str(p), 'resolution', 'active', 'set', '0'], stdout=subprocess.DEVNULL)

    def on_accel_profile_changed(self, idx):
        profile_num = 2 if idx == 0 else 1  # 2 = Flat, 1 = Adaptive
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Libinput', '--group', '1133', '--group', '49970', '--group', 'Logitech Gaming Mouse G502', '--key', 'PointerAccelerationProfile', str(profile_num)])
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Mouse', '--key', 'PointerAccelerationProfile', str(profile_num)])

        is_flat = (profile_num == 2)
        subprocess.run(['python3', '-c', f"import subprocess; [subprocess.run(['busctl', '--user', 'set-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'pointerAccelerationProfileFlat', 'b', '{str(is_flat).lower()}']) for p in ['/org/kde/KWin/InputDevice/event8']]"], stdout=subprocess.DEVNULL)

    def on_speed_slider_changed(self, val):
        speed_float = val / 100.0
        self.speed_val_label.setText(f"{speed_float:.3f}")

        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Libinput', '--group', '1133', '--group', '49970', '--group', 'Logitech Gaming Mouse G502', '--key', 'PointerAcceleration', f"{speed_float:.3f}"])
        subprocess.run(['kwriteconfig6', '--file', os.path.expanduser('~/.config/kcminputrc'), '--group', 'Mouse', '--key', 'PointerAcceleration', f"{speed_float:.3f}"])

        subprocess.run(['python3', '-c', f"import subprocess; [subprocess.run(['busctl', '--user', 'set-property', 'org.kde.KWin', p, 'org.kde.KWin.InputDevice', 'pointerAcceleration', 'd', '{speed_float}']) for p in ['/org/kde/KWin/InputDevice/event8']]"], stdout=subprocess.DEVNULL)

    def apply_all_black_rgb(self):
        subprocess.run(['openrgb', '--profile', 'ALL Black'], stdout=subprocess.DEVNULL)
        QMessageBox.information(self, "OpenRGB", "Applied 'ALL Black' profile successfully!")

    def refresh_logs(self):
        try:
            out = subprocess.check_output(['journalctl', '--user', '-u', 'g502-macros.service', '-n', '50', '--no-pager']).decode()
            self.log_view.setText(out)
        except Exception as e:
            self.log_view.setText(f"Error fetching logs: {e}")

def main():
    app = QApplication(sys.argv)
    window = G502ControlApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
