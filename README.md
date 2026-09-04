# 🖱️🎧 Logitech Linux Control Suite & Macro Studio (G502 Mouse & G733 Headset)

A zero-lag, native Linux control center for Logitech Gaming Gear featuring multi-device hardware macro daemons, DPI tuning, PipeWire audio controls, OpenRGB lighting integration, system tray minimization, and Piper interactive customization.

> [!NOTE]  
> **⚠️ Verified Hardware**: Tested and verified on **Logitech Gaming Mouse G502** (`usb:046d:c332` / `c539`) and **Logitech G733 LIGHTSPEED Wireless Gaming Headset** (`usb:046d:0ab5`).

---

## ✨ Features & Multi-Device Capabilities

### 🖱️ Gaming Mouse Studio (Logitech G502 & `libratbagd`)
- **Interactive Button Selector Studio**: Click to select physical mouse buttons (**G8**, **G7**, **G9**, **Wheel Tilt Left**, **Wheel Tilt Right**, etc.), set hold duration (ms), repeat delay (ms), and macro actions live.
- **Action Selectors**: Left Click Loop, Right Click Loop, Middle Click Loop, Space Key Loop, Win + V Clipboard History, Custom Key Loop, or Disabled.
- **Hardware DPI Controls**: Live sensor resolution adjustments (400 - 4000+ DPI, default 1200 DPI) synced across onboard mouse profiles via `ratbagctl`.
- **Pointer Acceleration & Speed**: Toggle between **Flat (1:1 Raw Linear)** and **Adaptive (Windows-style Curve)** with live KDE KWin DBus scaling.

### 🎧 Gaming Headset Studio (Logitech G733 & PipeWire / ALSA)
- **Sound & Equalizer**: Live Master Headphone Volume slider, output mute toggle, 5-Band EQ sliders (60Hz, 250Hz, 1kHz, 4kHz, 12kHz), and EQ Presets (*Flat 1:1, FPS Gaming, Bass Boost, Cinematic*).
- **Microphone Controls**: Live Mic Gain level slider, instant Mute/Unmute button, Hardware Sidetone Level slider (to naturally hear your own voice), and Live Mic Test Level bar.
- **RGB Lightstrip Effects**: Targeted HID++ 2.0 RGB controller for G733 front lightstrips, static colors, breathing pulse, spectrum cycle, stealth OFF, and quick color palettes.
- **Wireless Battery & Spoken Announcements**: Live voltage & smoothed G HUB 5% step battery level indicator. Hear remaining charge percentage spoken out loud (`spd-say`/`espeak`) by pressing the physical headset power button, clicking the header badge, or selecting from the tray menu.

### ⚙️ Settings Studio & 📌 System Tray Integration
- **Gear Icon Settings Page (⚙)**:
  - **18 Themes & Appearance**: *Dark Void (Default), Midnight Cyan, Cyberpunk Neon, Slate Dark, Nordic Frost, Dracula Dark, Emerald Forest, Sunset Crimson, Tokyo Night, Solar Gold, Synthwave 80s, Matrix Hacker, Deep Amethyst, Oceanic Abyss, Rose Gold Luxe, Vaporwave Pastel, Monochrome Stealth, Light Pristine*.
  - **System Health Audit / Diagnostics**: Live check of `g502-macros.service`, `ratbagd`, PipeWire audio daemon, OpenRGB, and input nodes.
  - **System Tray Options**: Minimize window to system tray on close when macro daemon is active.
  - **About & Repository**: Direct link to GitHub repository (`https://github.com/gaxkalik/Logitech-Linux-App`).
- **📌 System Tray Menu (`QSystemTrayIcon`)**:
  - Keep background macro service active when main window is closed.
  - Quick actions: Open Control Center, Hear Battery Charge %, Mute/Unmute Headset Mic, Toggle Macro Service, Settings, Quit.
- **☰ Hamburger Menu**: Quick device switcher to toggle between **🖱️ Logitech G502 Mouse** and **🎧 Logitech G733 Headset**.

---

## 🚀 Quick Start & Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:gaxkalik/Logitech-Linux-App.git
   cd Logitech-Linux-App
   ```

2. **Run the installer**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Launch the Control Center**:
   - Launch **"Logitech Control Center"** from your desktop Application Menu / Launcher.
   - Or execute in terminal:
     ```bash
     ./g502_gui.py
     ```

---

## 🔧 System Requirements

- Python 3.10+
- `python-evdev`
- `PyQt6`
- `libratbag` / `ratbagctl`
- `pipewire` / `wireplumber` / `pulseaudio-utils`
- `openrgb` (optional for lighting effects)
- `systemd` (user session)
