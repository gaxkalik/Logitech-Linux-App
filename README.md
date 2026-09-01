# 🖱️ Logitech G502 Linux Hardware Macro & Control Suite

A zero-lag, native Linux macro daemon, hardware DPI tuner, and PyQt6 GUI Control Center & Macro Customization Studio for the **Logitech Gaming Mouse G502**.

---

## ✨ Features

- **⚡ Zero-Lag Passive Monitoring**: Passively reads hardware event nodes (`/dev/input/event*`) without calling `dev.grab()`. Cursor movement (`REL_X`, `REL_Y` at 1000Hz) and primary clicks pass directly to the kernel with **0.00ms input latency** in games.
- **🎨 PyQt6 GUI Control Center & Macro Studio (`g502_gui.py`)**:
  - **Macro Customization Studio**: Customize button functions (**G7**, **G8**, **G9**, **Wheel Tilt Left**, **Wheel Tilt Right**), hold duration (ms), and repeat delay (ms) live.
  - **Action Selectors**: Left Click Loop, Right Click Loop, Middle Click Loop, Space Key Loop, Win + V Clipboard History, Custom Key Loop, or Disabled.
  - **Custom Key Mapping**: Map any keyboard key (`E`, `F`, `Q`, `R`, `Shift`, `Ctrl`, `Alt`, `Enter`, `Tab`, numbers, etc.) to repeat when held.
  - **Auto-Apply on Save**: Clicking *Save & Apply All Macro Settings* automatically restarts `g502-macros.service` so changes take effect instantly.
  - **Field Guide & Tooltips**: Built-in visual guides and hover tooltips explaining what each setting does.
  - **Hardware DPI Controls**: Live hardware sensor resolution adjustments (400 - 4000+ DPI, default 1200 DPI) synced across all onboard mouse memory profiles (`ratbagctl`).
  - **Pointer Acceleration Profile**: Toggle between **Flat (1:1 Raw Linear)** and **Adaptive (Windows-style Curve)**.
  - **Pointer Speed Slider**: Live KWin DBus + `kcminputrc` pointer acceleration scaling (`0.000` to `1.000`).
  - **OpenRGB Control**: One-click button to re-apply the **`ALL Black`** OpenRGB preset.
  - **Integrated Log Viewer**: Live `journalctl` service log output built directly into the app.
- **⚙️ Dynamic JSON Config (`~/.config/g502_macros/config.json`)**: Persistent configuration loaded at startup and reloaded live.
- **🖥️ Systemd Autostart**: User service unit files to run headlessly at boot.

---

## 📂 Repository Structure

```text
├── g502_macro_daemon.py       # Zero-lag passive evdev + uinput macro daemon
├── g502_gui.py                # PyQt6 Control Center & Macro Customization Studio desktop app
├── install.sh                 # One-click installation and mouse profile setup script
├── g502-macros.service        # Systemd user service unit for macro daemon
├── openrgb-apply.service      # Systemd user service unit for OpenRGB preset
├── g502-control-center.desktop # Desktop launcher for application menu
└── README.md                  # Comprehensive documentation
```

---

## 🚀 Quick Start & Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:gaxkalik/Logitech-G502-Linux-App.git
   cd Logitech-G502-Linux-App
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
- `systemd` (user session)
- `openrgb` (optional)
