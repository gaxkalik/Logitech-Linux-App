#!/usr/bin/env python3
"""
Logitech G502 Zero-Lag Native Hardware Macro Daemon
---------------------------------------------------
Passive listener daemon (NO dev.grab()):
  - Leaves raw mouse cursor movement (REL_X, REL_Y), Left Click, Right Click,
    Middle Click, and Scroll Wheel 100% direct-to-kernel for 0ms input latency in games.
  - Passively monitors event node for macro triggers:
      * G8 (DPI Up - BTN_BACK / 278): Left Click Down (20ms) -> Up (50ms) repeat loop
      * Wheel Tilt Left (REL_HWHEEL < 0): Left Click Down (20ms) -> Up (50ms) repeat loop
      * Wheel Tilt Right (REL_HWHEEL > 0): Right Click Down (20ms) -> Up (50ms) repeat loop
      * G7 (DPI Down - BTN_FORWARD / 277): Space Key Down (20ms) -> Up (50ms) repeat loop
      * G9 (Profile Select - BTN_TASK / 279): Win + V (Opens Clipboard)
"""

import sys
import os
import time
import signal
import threading
import select
import glob
import logging
import evdev
from evdev import InputDevice, UInput, ecodes as e

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Hardware Event IDs
CODE_G7 = e.BTN_FORWARD   # 277 (DPI Down)
CODE_G8 = e.BTN_BACK      # 278 (DPI Up)
CODE_G9 = e.BTN_TASK      # 279 (Profile Select)

class G502MacroDaemon:
    def __init__(self):
        self.running = True
        self.active_threads = {}  # key -> (Thread, Event, expiry_time_ref)
        self.lock = threading.Lock()

        # Initialize UInput virtual device for emitting macro outputs only
        cap = {
            e.EV_KEY: [
                e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE,
                e.KEY_SPACE, e.KEY_LEFTMETA, e.KEY_V
            ],
        }
        try:
            self.ui = UInput(cap, name="G502-Macro-Virtual-Output")
            logging.info("Virtual UInput output device created successfully.")
        except Exception as ex:
            logging.error(f"Failed to create UInput device: {ex}")
            sys.exit(1)

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

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

    def start_macro(self, key, macro_type, timeout_based=False):
        with self.lock:
            current_time = time.time()
            if key in self.active_threads:
                thread, stop_event, ref_dict = self.active_threads[key]
                if thread.is_alive():
                    if timeout_based:
                        ref_dict['expiry'] = current_time + 0.180  # Extend tilt pulse window
                    return

            stop_event = threading.Event()
            ref_dict = {'expiry': current_time + 0.180 if timeout_based else None}
            thread = threading.Thread(
                target=self.run_macro_loop,
                args=(macro_type, stop_event, ref_dict, timeout_based),
                daemon=True
            )
            self.active_threads[key] = (thread, stop_event, ref_dict)
            thread.start()
            logging.info(f"Started macro '{macro_type}' for key {key}")

    def stop_macro(self, key):
        with self.lock:
            if key in self.active_threads:
                thread, stop_event, _ = self.active_threads[key]
                stop_event.set()
                del self.active_threads[key]
                logging.info(f"Stopped macro for key {key}")

    def run_macro_loop(self, macro_type, stop_event, ref_dict, timeout_based):
        """Executes down > 20ms > up > 50ms loop with sub-ms cancellation."""
        if macro_type == 'LEFT_CLICK_MACRO':
            down_type, down_code = e.EV_KEY, e.BTN_LEFT
        elif macro_type == 'RIGHT_CLICK_MACRO':
            down_type, down_code = e.EV_KEY, e.BTN_RIGHT
        elif macro_type == 'SPACE_MACRO':
            down_type, down_code = e.EV_KEY, e.KEY_SPACE
        else:
            return

        try:
            while not stop_event.is_set() and self.running:
                if timeout_based:
                    if time.time() > ref_dict['expiry']:
                        break

                # 1. Action Down
                self.ui.write(down_type, down_code, 1)
                self.ui.syn()

                # 2. Wait 20ms
                if stop_event.wait(timeout=0.020):
                    self.ui.write(down_type, down_code, 0)
                    self.ui.syn()
                    break

                # 3. Action Up
                self.ui.write(down_type, down_code, 0)
                self.ui.syn()

                # 4. Wait 50ms
                if stop_event.wait(timeout=0.050):
                    break
        finally:
            self.ui.write(down_type, down_code, 0)
            self.ui.syn()

    def run(self):
        logging.info("G502 Zero-Lag Passive Macro Daemon starting...")
        while self.running:
            dev = self.find_g502_device()
            if not dev:
                logging.warning("G502 mouse device not found. Retrying in 2 seconds...")
                time.sleep(2)
                continue

            logging.info(f"Monitoring hardware device (passive mode): {dev.path} ({dev.name})")

            try:
                while self.running:
                    r, _, _ = select.select([dev.fd], [], [], 1.0)
                    if not r:
                        continue

                    for event in dev.read():
                        # --- PASSIVE MACRO INTERCEPTIONS ---
                        if event.type == e.EV_KEY:
                            if event.code == CODE_G7:  # G7 (DPI Down) -> Space Macro
                                if event.value == 1:
                                    self.start_macro('G7', 'SPACE_MACRO')
                                elif event.value == 0:
                                    self.stop_macro('G7')
                            elif event.code == CODE_G8:  # G8 (DPI Up) -> Left Click Macro
                                if event.value == 1:
                                    self.start_macro('G8', 'LEFT_CLICK_MACRO')
                                elif event.value == 0:
                                    self.stop_macro('G8')
                            elif event.code == CODE_G9:  # G9 (Profile Select) -> Win + V
                                if event.value == 1:
                                    self.trigger_clipboard()

                        elif event.type == e.EV_REL and event.code in (e.REL_HWHEEL, e.REL_HWHEEL_HI_RES):
                            if event.code == e.REL_HWHEEL:
                                if event.value < 0:  # Tilt Left
                                    self.start_macro('TILT_LEFT', 'LEFT_CLICK_MACRO', timeout_based=True)
                                elif event.value > 0:  # Tilt Right
                                    self.start_macro('TILT_RIGHT', 'RIGHT_CLICK_MACRO', timeout_based=True)

            except (OSError, IOError) as io_err:
                logging.warning(f"Device read error or reconnected: {io_err}")
                time.sleep(1)

        self.ui.close()
        logging.info("G502 Macro Daemon stopped.")

if __name__ == "__main__":
    daemon = G502MacroDaemon()
    daemon.run()
