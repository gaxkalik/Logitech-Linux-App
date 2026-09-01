# 🖱️ Universal Gaming Mouse Hardware Macro & Control Suite

A zero-lag, native Linux multi-mouse macro daemon, hardware DPI tuner, and PyQt6 GUI Control Center powered by **libratbagd** & **Piper** engine integration.

> [!NOTE]  
> **⚠️ Testing Disclaimer**: This software is actively tested and verified exclusively on the **Logitech Gaming Mouse G502** (`usb:046d:c332`). While the `libratbagd` architecture supports multi-mouse discovery for other gaming mice (Razer, SteelSeries, Roccat, Corsair, etc.), hardware event timings and button mappings are currently benchmarked and confirmed working on the G502.

---

## ✨ Features & Multi-Mouse Capabilities

- **🐭 Universal Gaming Mouse Support (`libratbagd` / `piper`)**:
  - Dynamically discovers connected gaming mice supported by `libratbagd`.
  - **Mouse Device Selector**: Switch active mouse devices on-the-fly directly inside the GUI application.
- **⚡ Zero-Lag Passive Monitoring**: Passively reads hardware event nodes (`/dev/input/event*`) without calling `dev.grab()`. Cursor movement (`REL_X`, `REL_Y` at 1000Hz) and primary clicks pass directly to the kernel with **0.00ms input latency** in games.
- **🎨 PyQt6 GUI Control Center & Macro Studio (`g502_gui.py`)**:
  - **Interactive Button Selector Studio**: Click to select any physical button (**G8**, **G7**, **G9**, **Wheel Tilt Left**, **Wheel Tilt Right**, and Extra Mouse Buttons), customize hold duration (ms), and repeat delay (ms) live.
  - **Action Selectors**: Left Click Loop, Right Click Loop, Middle Click Loop, Space Key Loop, Win + V Clipboard History, Custom Key Loop, or Disabled.
  - **Custom Key Mapping**: Map any keyboard key (`E`, `F`, `Q`, `R`, `Shift`, `Ctrl`, `Alt`, `Enter`, `Tab`, numbers, etc.) to repeat when held.
  - **Auto-Apply on Save**: Clicking *Save & Apply All Macro Settings* automatically restarts `g502-macros.service` so changes take effect instantly.
  - **Hardware DPI Controls**: Live hardware sensor resolution adjustments (400 - 4000+ DPI, default 1200 DPI) synced across all onboard mouse memory profiles (`ratbagctl`).
  - **Pointer Acceleration Profile**: Toggle between **Flat (1:1 Raw Linear)** and **Adaptive (Windows-style Curve)**.
  - **Pointer Speed Slider**: Live KWin DBus + `kcminputrc` pointer acceleration scaling (`0.000` to `1.000`).
  - **OpenRGB & Piper Integration**: One-click launch for **Piper GTK App** and **OpenRGB**.
- **⚙️ Dynamic JSON Config (`~/.config/g502_macros/config.json`)**: Persistent configuration loaded at startup and reloaded live.
- **🖥️ Systemd Autostart**: User service unit files to run headlessly at boot.

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
   - Open **"Logitech G502 Control Center"** from your desktop Application Menu / Launcher.
   - Or run from terminal:
     ```bash
     ./g502_gui.py
     ```

---

## 🔧 Requirements

- Python 3.10+
- `python-evdev`
- `PyQt6`
- `libratbag` / `ratbagctl`
- `piper` (optional GTK frontend)
- `systemd` (user session)
- `openrgb` (optional)
