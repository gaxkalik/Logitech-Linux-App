#!/usr/bin/env bash
# ==============================================================================
# Logitech G502 Linux Macro & Control Suite Installer
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing Logitech G502 Linux Control Suite ==="

# 1. Ensure systemd user service directory exists
mkdir -p ~/.config/systemd/user
mkdir -p ~/.local/share/applications

# 2. Copy systemd user service files
cp "$SCRIPT_DIR/g502-macros.service" ~/.config/systemd/user/
cp "$SCRIPT_DIR/openrgb-apply.service" ~/.config/systemd/user/

# 3. Copy desktop launcher entry
cp "$SCRIPT_DIR/g502-control-center.desktop" ~/.local/share/applications/

# 4. Set executable permissions
chmod +x "$SCRIPT_DIR/g502_macro_daemon.py"
chmod +x "$SCRIPT_DIR/g502_gui.py"
chmod +x ~/.local/share/applications/g502-control-center.desktop

# 5. Reload systemd daemon & enable services
systemctl --user daemon-reload
systemctl --user enable --now g502-macros.service
systemctl --user enable openrgb-apply.service 2>/dev/null || true

# 6. Program G502 onboard profiles via ratbagctl
echo "=== Programming G502 Onboard Mouse Hardware Profiles ==="
python3 -c "
import subprocess
try:
    out = subprocess.check_output(['ratbagctl', 'list'], stderr=subprocess.DEVNULL).decode()
    dev_name = None
    for line in out.splitlines():
        if 'G502' in line:
            dev_name = line.split(':')[0].strip()
            break
    if dev_name:
        for p in [0, 1, 2]:
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'button', '6', 'action', 'set', 'button', '6'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'button', '7', 'action', 'set', 'button', '7'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'button', '8', 'action', 'set', 'button', '8'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'button', '9', 'action', 'set', 'special', 'wheel-right'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'button', '10', 'action', 'set', 'special', 'wheel-left'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'resolution', '0', 'dpi', 'set', '1200'], stdout=subprocess.DEVNULL)
            subprocess.run(['ratbagctl', dev_name, 'profile', str(p), 'resolution', 'active', 'set', '0'], stdout=subprocess.DEVNULL)
        print(f'Successfully programmed all hardware profiles on {dev_name} at 1200 DPI!')
    else:
        print('ratbagd daemon running, but G502 device not active yet.')
except Exception as e:
        print('Ratbagctl setup skipped or ratbagd not running:', e)
"

echo "=== Setup Complete! Launcher created in Application Menu. ==="
