#!/usr/bin/env python3
"""
Logitech G502 Dynamic Customizable Hardware Macro Daemon
--------------------------------------------------------
Passive listener daemon (NO dev.grab()):
  - Leaves raw mouse cursor movement (REL_X, REL_Y), Left Click, Right Click,
    Middle Click, and Scroll Wheel 100% direct-to-kernel for 0ms input latency in games.
  - Dynamically reads macro settings & timings from ~/.config/g502_macros/config.json
  - Supports live reload on SIGHUP without dropping device connection.
"""

import sys
import os
import time
import signal
import threading
import select
import glob
import json
import logging
import subprocess
import evdev
from evdev import InputDevice, UInput, ecodes as e

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

CONFIG_PATH = os.path.expanduser('~/.config/g502_macros/config.json')
SETTINGS_PATH = os.path.expanduser('~/.config/g502_macros/settings.json')

# Hardware Event IDs
CODE_G7 = e.BTN_FORWARD   # 277 (Button 6 - DPI Down)
CODE_G8 = e.BTN_BACK      # 278 (Button 7 - DPI Up)
CODE_G9 = e.BTN_TASK      # 279 (Button 8 - Profile Select)
CODE_TILT_RIGHT = 280     # 280 (Button 9 - Wheel Tilt Right)
CODE_TILT_LEFT = 281      # 281 (Button 10 - Wheel Tilt Left)

DEFAULT_CONFIG = {
    "buttons": {
        "G8": {"name": "G8 (DPI Up)", "action_type": "LEFT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
        "TILT_LEFT": {"name": "Wheel Tilt Left", "action_type": "LEFT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
        "TILT_RIGHT": {"name": "Wheel Tilt Right", "action_type": "RIGHT_CLICK_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
        "G7": {"name": "G7 (DPI Down)", "action_type": "SPACE_LOOP", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"},
        "G9": {"name": "G9 (Profile Select)", "action_type": "CLIPBOARD_WIN_V", "hold_ms": 20, "delay_ms": 50, "custom_key": "KEY_SPACE"}
    }
}

class G502MacroDaemon:
    def __init__(self):
        self.running = True
        self.active_threads = {}  # key -> (Thread, Event, expiry_time_ref)
        self.lock = threading.Lock()
        self.config = self.load_config()

        # Initialize UInput virtual device with full mouse and keyboard capabilities
        cap = {
            e.EV_KEY: [
                e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE, e.BTN_SIDE, e.BTN_EXTRA,
                e.BTN_FORWARD, e.BTN_BACK, e.BTN_TASK,
                e.KEY_SPACE, e.KEY_LEFTMETA, e.KEY_V
            ] + list(range(1, 255)),
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL, e.REL_WHEEL_HI_RES, e.REL_HWHEEL_HI_RES],
        }
        try:
            self.ui = UInput(cap, name="G502-Macro-Virtual-Output")
            logging.info("Virtual UInput output device created successfully.")
        except Exception as ex:
            logging.error(f"Failed to create UInput device: {ex}")
            sys.exit(1)

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGHUP, self.reload_config)

    def load_config(self):
        """Loads JSON config file or falls back to default."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    cfg = json.load(f)
                    logging.info(f"Loaded macro configuration from {CONFIG_PATH}")
                    return cfg
        except Exception as ex:
            logging.error(f"Error loading config file: {ex}")
        return DEFAULT_CONFIG

    def reload_config(self, signum=None, frame=None):
        """Reloads configuration on SIGHUP signal."""
        logging.info("SIGHUP received. Reloading macro configuration...")
        with self.lock:
            self.config = self.load_config()

    def shutdown(self, signum=None, frame=None):
        logging.info("Shutting down G502 Macro Daemon...")
        self.running = False
        with self.lock:
            for key, (thread, stop_event, _) in list(self.active_threads.items()):
                stop_event.set()

    def find_g502_device(self):
        """Find Logitech G502 mouse event device."""
        for path in glob.glob('/dev/input/event*'):
            try:
                dev = InputDevice(path)
                name_lower = dev.name.lower()
                if ('g502' in name_lower or 'logitech' in name_lower) and dev.info.vendor == 0x046d and dev.info.product == 0xc332:
                    if 'keyboard' not in name_lower:
                        return dev
            except Exception:
                pass
        return None

    def trigger_clipboard(self):
        """Emits Win + V (Super + V) key combination in a non-blocking background thread."""
        def _do_clipboard():
            logging.info("Triggered Clipboard Macro (Win + V)")
            self.ui.write(e.EV_KEY, e.KEY_LEFTMETA, 1)
            self.ui.syn()
            time.sleep(0.015)
            self.ui.write(e.EV_KEY, e.KEY_V, 1)
            self.ui.syn()
            time.sleep(0.030)
            self.ui.write(e.EV_KEY, e.KEY_V, 0)
            self.ui.syn()
            time.sleep(0.015)
            self.ui.write(e.EV_KEY, e.KEY_LEFTMETA, 0)
            self.ui.syn()

        threading.Thread(target=_do_clipboard, daemon=True).start()

    def get_button_cfg(self, key_name):
        with self.lock:
            return self.config.get("buttons", {}).get(key_name, {})

    def trigger_button_action(self, key_name, is_pressed, timeout_based=False):
        btn_cfg = self.get_button_cfg(key_name)
        action_type = btn_cfg.get("action_type", "DISABLED")

        if action_type == "DISABLED":
            return

        if action_type == "CLIPBOARD_WIN_V":
            if is_pressed:
                self.trigger_clipboard()
            return

        # Loop-based macros
        if is_pressed:
            self.start_macro(key_name, btn_cfg, timeout_based=timeout_based)
        else:
            if not timeout_based:
                self.stop_macro(key_name)

    def ensure_g502_ratbag_buttons(self):
        """Ensure G502 ratbagctl Profile 0 is active and buttons 6..10 emit EV_KEY events."""
        try:
            res = subprocess.run(["ratbagctl", "list"], capture_output=True, text=True, timeout=2.0)
            dev_id = None
            for line in res.stdout.splitlines():
                if ":" in line and "G502" in line.upper():
                    dev_id = line.split(":")[0].strip()
                    break
            if not dev_id:
                return
            subprocess.run(["ratbagctl", dev_id, "profile", "active", "set", "0"], capture_output=True, timeout=2.0)
            for b in (6, 7, 8, 9, 10):
                subprocess.run(
                    ["ratbagctl", dev_id, "profile", "0", "button", str(b), "action", "set", "button", str(b)],
                    capture_output=True,
                    timeout=2.0
                )
            logging.info(f"Configured ratbagctl ({dev_id}) Profile 0 buttons 6..10 for EV_KEY macro capture.")
        except Exception as ex:
            logging.debug(f"Could not configure ratbagctl buttons automatically: {ex}")

    def start_macro(self, key_name, btn_cfg, timeout_based=False):
        with self.lock:
            current_time = time.time()
            if key_name in self.active_threads:
                thread, stop_event, ref_dict = self.active_threads[key_name]
                if thread.is_alive():
                    if timeout_based:
                        ref_dict['expiry'] = current_time + 0.550  # Extend tilt pulse window across initial repeat delay
                    return

            stop_event = threading.Event()
            ref_dict = {'expiry': current_time + 0.550 if timeout_based else None}
            thread = threading.Thread(
                target=self.run_macro_loop,
                args=(btn_cfg, stop_event, ref_dict, timeout_based),
                daemon=True
            )
            self.active_threads[key_name] = (thread, stop_event, ref_dict)
            thread.start()
            logging.info(f"Started macro '{btn_cfg.get('action_type')}' for key {key_name}")

    def stop_macro(self, key_name):
        with self.lock:
            if key_name in self.active_threads:
                thread, stop_event, _ = self.active_threads[key_name]
                stop_event.set()
                del self.active_threads[key_name]
                logging.info(f"Stopped macro for key {key_name}")

    def run_macro_loop(self, btn_cfg, stop_event, ref_dict, timeout_based):
        """Executes down > hold_ms > up > delay_ms loop with sub-ms cancellation."""
        action_type = btn_cfg.get("action_type", "LEFT_CLICK_LOOP")
        hold_s = btn_cfg.get("hold_ms", 20) / 1000.0
        delay_s = btn_cfg.get("delay_ms", 50) / 1000.0

        if action_type == 'LEFT_CLICK_LOOP':
            down_type, down_code = e.EV_KEY, e.BTN_LEFT
        elif action_type == 'RIGHT_CLICK_LOOP':
            down_type, down_code = e.EV_KEY, e.BTN_RIGHT
        elif action_type == 'MIDDLE_CLICK_LOOP':
            down_type, down_code = e.EV_KEY, e.BTN_MIDDLE
        elif action_type == 'SPACE_LOOP':
            down_type, down_code = e.EV_KEY, e.KEY_SPACE
        elif action_type == 'CUSTOM_KEY_LOOP':
            key_str = btn_cfg.get("custom_key", "KEY_SPACE")
            down_type, down_code = e.EV_KEY, getattr(e, key_str, e.KEY_SPACE)
        else:
            return

        try:
            while not stop_event.is_set() and self.running:
                if timeout_based:
                    if time.time() > ref_dict['expiry']:
                        break

                # 1. Key/Button Down
                self.ui.write(down_type, down_code, 1)
                self.ui.syn()

                # 2. Hold Duration
                if stop_event.wait(timeout=hold_s):
                    self.ui.write(down_type, down_code, 0)
                    self.ui.syn()
                    break

                # 3. Key/Button Up
                self.ui.write(down_type, down_code, 0)
                self.ui.syn()

                # 4. Repeat Delay
                if stop_event.wait(timeout=delay_s):
                    break
        finally:
            self.ui.write(down_type, down_code, 0)
            self.ui.syn()

    def find_g733_hidraw(self):
        for h in glob.glob('/sys/class/hidraw/hidraw*'):
            uevent = os.path.join(h, 'device', 'uevent')
            if os.path.exists(uevent):
                try:
                    with open(uevent, 'r') as f:
                        content = f.read().upper()
                        if '046D' in content and '0AB5' in content:
                            return f"/dev/{os.path.basename(h)}"
                except Exception:
                    pass
        return None

    def is_g733_online(self, dev_path):
        try:
            fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
            os.write(fd, bytes([0x11, 0xFF, 0x08, 0x00] + [0] * 16))
            online = False
            t0 = time.time()
            while time.time() - t0 < 0.12:
                try:
                    b = os.read(fd, 64)
                    if b and len(b) >= 7 and b[0] == 0x11:
                        if b[2] == 0x08:
                            mV = (b[4] << 8) | b[5]
                            online = (mV >= 2500)
                            break
                        elif b[2] == 0xFF and b[3] == 0x08:
                            online = False
                            break
                except BlockingIOError:
                    pass
                time.sleep(0.005)
            os.close(fd)
            return online
        except Exception:
            return False

    def apply_saved_g733_rgb(self):
        """Reads saved G733 RGB settings from settings.json and applies them via HID++ 0x8070."""
        dev_path = self.find_g733_hidraw()
        if not dev_path or not os.path.exists(SETTINGS_PATH):
            return False
        try:
            with open(SETTINGS_PATH, 'r') as f:
                settings = json.load(f)
            rgb = settings.get("headset_rgb", [0, 168, 252])
            r_raw = max(0, min(255, int(rgb[0])))
            g_raw = max(0, min(255, int(rgb[1])))
            b_raw = max(0, min(255, int(rgb[2])))
            brightness = max(0, min(100, int(settings.get("headset_brightness", 100))))
            mode = int(settings.get("headset_rgb_mode", 1))
            zone = settings.get("headset_rgb_zone", None)
            scale = brightness / 100.0
            sr = max(0, min(255, int(round(r_raw * scale))))
            sg = max(0, min(255, int(round(g_raw * scale))))
            sb = max(0, min(255, int(round(b_raw * scale))))

            fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
            os.write(fd, bytes([0x11, 0xFF, 0x04, 0x80, 0x01, 0x01, 0x00] + [0] * 13))
            time.sleep(0.01)
            target_zones = [0, 1] if zone is None else [int(zone)]
            for z in target_zones:
                if mode == 0 or brightness <= 0 or (r_raw == 0 and g_raw == 0 and b_raw == 0 and mode != 3):
                    cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x00] + [0] * 14)
                elif mode == 2:
                    cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x02, r_raw, g_raw, b_raw, 0x0B, 0xB8, 0x00, brightness] + [0] * 7)
                elif mode == 3:
                    cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x13, 0x88, brightness] + [0] * 6)
                else:
                    cmd = bytes([0x11, 0xFF, 0x04, 0x30, z, 0x01, sr, sg, sb, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, brightness] + [0] * 4)
                os.write(fd, cmd)
                time.sleep(0.01)
            os.close(fd)
            logging.info(f"Restored persistent G733 RGB effect (mode={mode}, brightness={brightness}%) after headset power-on.")
            return True
        except Exception as ex:
            logging.debug(f"Could not apply saved G733 RGB: {ex}")
            return False

    def g733_rgb_watchdog_loop(self):
        """Monitors G733 wireless power state and restores saved RGB effect whenever headset restarts."""
        was_online = False
        while self.running:
            dev_path = self.find_g733_hidraw()
            if dev_path:
                online = self.is_g733_online(dev_path)
                if online and not was_online:
                    was_online = True
                    # Apply immediately and across the G733 firmware boot animation window
                    self.apply_saved_g733_rgb()
                    for wait_s in (0.9, 1.2):
                        if not self.running:
                            break
                        time.sleep(wait_s)
                        self.apply_saved_g733_rgb()
                elif not online:
                    was_online = False
            time.sleep(1.5)

    def run(self):
        logging.info("G502 Dynamic Macro Daemon starting...")
        threading.Thread(target=self.g733_rgb_watchdog_loop, daemon=True).start()
        while self.running:
            dev = self.find_g502_device()
            if not dev:
                logging.warning("G502 mouse device not found. Retrying in 2 seconds...")
                time.sleep(2)
                continue

            self.ensure_g502_ratbag_buttons()
            logging.info(f"Monitoring hardware device (passive mode): {dev.path} ({dev.name})")

            try:
                while self.running:
                    r, _, _ = select.select([dev.fd], [], [], 1.0)
                    if not r:
                        continue

                    for event in dev.read():
                        # --- PASSIVE DYNAMIC MACRO INTERCEPTIONS ---
                        if event.type == e.EV_KEY and event.value in (0, 1):
                            if event.code == CODE_G7:             # G7 (Button 6 - DPI Down)
                                self.trigger_button_action('G7', event.value == 1)
                            elif event.code == CODE_G8:           # G8 (Button 7 - DPI Up)
                                self.trigger_button_action('G8', event.value == 1)
                            elif event.code == CODE_G9:           # G9 (Button 8 - Profile Select)
                                self.trigger_button_action('G9', event.value == 1)
                            elif event.code == CODE_TILT_RIGHT:   # Button 9 (Wheel Tilt Right)
                                self.trigger_button_action('TILT_RIGHT', event.value == 1)
                            elif event.code == CODE_TILT_LEFT:    # Button 10 (Wheel Tilt Left)
                                self.trigger_button_action('TILT_LEFT', event.value == 1)

                        elif event.type == e.EV_REL and event.code in (e.REL_HWHEEL, e.REL_HWHEEL_HI_RES):
                            if event.value < 0:                   # Tilt Left
                                self.trigger_button_action('TILT_LEFT', True, timeout_based=True)
                            elif event.value > 0:                 # Tilt Right
                                self.trigger_button_action('TILT_RIGHT', True, timeout_based=True)

            except (OSError, IOError) as io_err:
                logging.warning(f"Device read error or reconnected: {io_err}")
                time.sleep(1)

        self.ui.close()
        logging.info("G502 Macro Daemon stopped.")

if __name__ == "__main__":
    daemon = G502MacroDaemon()
    daemon.run()
