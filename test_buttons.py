#!/usr/bin/env python3
import evdev
import select
import time

dev = evdev.InputDevice('/dev/input/event8')
print("=== EXACT BUTTON IDENTIFIER ===")
print("Please press each button ONE AT A TIME:")
print("1. G7 (DPI Down)")
print("2. G8 (DPI Up)")
print("3. G9 (Profile Select)")
print("4. Wheel Tilt Left")
print("5. Wheel Tilt Right")

dev_map = {dev.fd: dev}
start = time.time()

while time.time() - start < 15:
    r, _, _ = select.select([dev.fd], [], [], 0.5)
    if r:
        for ev in dev.read():
            if ev.type == evdev.ecodes.EV_KEY:
                code_name = evdev.ecodes.BTN.get(ev.code, evdev.ecodes.KEY.get(ev.code, str(ev.code)))
                print(f"EV_KEY -> Code: {ev.code} ({code_name}) | Value: {ev.value}", flush=True)
            elif ev.type == evdev.ecodes.EV_REL and ev.code in (evdev.ecodes.REL_HWHEEL, evdev.ecodes.REL_HWHEEL_HI_RES):
                code_name = evdev.ecodes.REL.get(ev.code, str(ev.code))
                print(f"EV_REL -> Code: {ev.code} ({code_name}) | Value: {ev.value}", flush=True)
