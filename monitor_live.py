#!/usr/bin/env python3
import evdev
import select
import time
import glob

log_file = "/home/bart/.gemini/antigravity/scratch/g502_macros/event_log.txt"
with open(log_file, "w") as f:
    f.write("=== LOG START ===\n")

devices = []
for path in glob.glob('/dev/input/event*'):
    try:
        dev = evdev.InputDevice(path)
        if 'g502' in dev.name.lower() or 'logitech' in dev.name.lower():
            devices.append(dev)
    except Exception:
        pass

print(f"Monitoring {len(devices)} devices:")
for d in devices:
    print(f"  {d.path}: {d.name}")

dev_map = {d.fd: d for d in devices}
start = time.time()

with open(log_file, "a") as f:
    f.write(f"Devices: {[(d.path, d.name) for d in devices]}\n")
    f.flush()
    while time.time() - start < 20:
        r, _, _ = select.select(list(dev_map.keys()), [], [], 0.5)
        for fd in r:
            dev = dev_map[fd]
            for ev in dev.read():
                if ev.type in (evdev.ecodes.EV_KEY, evdev.ecodes.EV_REL, evdev.ecodes.EV_ABS):
                    code_name = evdev.ecodes.KEY.get(ev.code, evdev.ecodes.BTN.get(ev.code, evdev.ecodes.REL.get(ev.code, str(ev.code))))
                    msg = f"[{time.strftime('%H:%M:%S')}] Device: {dev.name} ({dev.path}) | Type: {ev.type} | Code: {ev.code} ({code_name}) | Value: {ev.value}\n"
                    print(msg, end="")
                    f.write(msg)
                    f.flush()

print("Monitoring finished.")
