#!/bin/bash
set -e

echo "=== 1. Programming Logitech G502 Onboard Hardware Buttons via ratbagctl ==="
DEVICE="hollering-marmot"

for p in 0 1 2; do
  echo "Configuring Profile $p..."
  ratbagctl $DEVICE profile $p button 6 action set key KEY_F13 || true # G7 (DPI Down) -> KEY_F13
  ratbagctl $DEVICE profile $p button 7 action set key KEY_F14 || true # G8 (DPI Up)   -> KEY_F14
  ratbagctl $DEVICE profile $p button 8 action set key KEY_F15 || true # G9 (Profile)  -> KEY_F15
  ratbagctl $DEVICE profile $p button 9 action set key KEY_F16 || true # Wheel Right   -> KEY_F16
  ratbagctl $DEVICE profile $p button 10 action set key KEY_F17 || true # Wheel Left   -> KEY_F17
done

echo "=== 2. Installing systemd user service ==="
mkdir -p ~/.config/systemd/user
cp /home/bart/.gemini/antigravity/scratch/g502_macros/g502-macros.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable g502-macros.service
systemctl --user restart g502-macros.service

echo "=== 3. Checking systemd service status ==="
systemctl --user status g502-macros.service --no-pager

echo "=== Logitech G502 Macros Setup Complete! ==="
