# 🖱️ Logitech G502 Linux Hardware Macro & Control Suite

A zero-lag, native Linux macro daemon, hardware DPI tuner, and PyQt6 GUI control panel for the **Logitech Gaming Mouse G502**.

---

## ✨ Features

- **Zero-Lag Passive Monitoring**: Passively reads `/dev/input/event*` hardware events without calling `dev.grab()`. Cursor movement (`REL_X`, `REL_Y`) and primary clicks remain 100% direct-to-kernel at 1000Hz with zero input latency.
- **Hardware Button Macros**:
  - **G8 (DPI Up) & Wheel Tilt Left**: Left Click down (20ms) \(\rightarrow\) Left Click up (50ms) repeat loop while held (stops instantly on release).
  - **Wheel Tilt Right**: Right Click down (20ms) \(\rightarrow\) Right Click up (50ms) repeat loop while held (stops instantly on release).
  - **G7 (DPI Down)**: Space Key down (20ms) \(\rightarrow\) Space Key up (50ms) repeat loop while held (stops instantly on release).
  - **G9 (Profile Select)**: Opens Clipboard History (`Win + V`) in a non-blocking background thread.
- **PyQt6 GUI Control Center (`g502_gui.py`)**:
  - Live hardware DPI slider & presets (400 - 4000+ DPI, default 1200 DPI).
  - Live KDE KWin pointer acceleration toggle (**Flat 1:1 Raw Linear** vs **Adaptive**).
  - Live pointer speed slider (`0.000` to `1.000`).
  - One-click OpenRGB profile preset loading (`ALL Black`).
  - Integrated live `journalctl` service log viewer.
  - Interactive live macro testing box.
- **Systemd Autostart**: Service unit files to run headlessly at boot.

---

## 📂 Repository Structure

```text
├── g502_macro_daemon.py       # Zero-lag passive evdev + uinput macro daemon
├── g502_gui.py                # PyQt6 Control Center desktop application
├── install.sh                 # One-click installation and mouse profile setup script
├── g502-macros.service        # Systemd user service unit for macro daemon
├── openrgb-apply.service      # Systemd user service unit for OpenRGB preset
├── g502-control-center.desktop # Desktop launcher for application menu
└── README.md                  # Documentation
```

---

## 🚀 Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd g502_macros
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
