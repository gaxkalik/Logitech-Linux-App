#!/usr/bin/env python3
"""
Comprehensive Unit & Integration Test Suite for Logitech Linux Control Suite (G502 & G733)
Covers:
  1. Theme & Styling Engine (18 themes, QSS generation, SVG icons, color math, elevation shadows)
  2. Native G733 HID++ 2.0 Hardware Driver (hidraw discovery, battery discharge curve & hysteresis, RGB, sidetone, TTS)
  3. Background Hardware Threads (G733PowerButtonListenerThread evdev debounce, MicMeterThread PCM dB calculation)
  4. Settings & Device Discovery (JSON persistence, ratbagctl mouse parsing)
  5. GUI Main Window & All Tabs (Mouse Button Studio, DPI & 1:1 Calibration, KWin DBus paths, Headset EQ, Mic/Sidetone, RGB, Tray closeEvent, Service toggle, Logs)
  6. Settings & Diagnostics Studio Dialog (Theme switching, health audit diagnostics, tray toggles)
  7. G502 Hardware Macro Daemon (Device discovery, UInput virtual output, Win+V clipboard, hold/delay repeat loops, wheel tilt pulse expiry extension, SIGHUP reload)
"""

import os
import sys
import time
import json
import struct
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Configure headless Qt platform before importing PyQt6
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox
import g502_gui
import g502_macro_daemon

# Single global QApplication instance for GUI tests
_qapp = QApplication.instance() or QApplication(sys.argv)


class TestThemeAndStylingEngine(unittest.TestCase):
    def test_adjust_hex_color(self):
        self.assertEqual(g502_gui.adjust_hex_color("#000000", 1.2), "#000000")
        self.assertEqual(g502_gui.adjust_hex_color("#FFFFFF", 1.5), "#FFFFFF")
        darkened = g502_gui.adjust_hex_color("#38BDF8", 0.5)
        self.assertEqual(darkened, "#1C5E7C")
        self.assertEqual(g502_gui.adjust_hex_color("invalid", 1.1), "invalid")

    def test_all_18_themes_generate_valid_qss_and_svgs(self):
        self.assertEqual(len(g502_gui.THEMES), 18)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(g502_gui, "ICONS_CACHE_DIR", tmpdir):
                for theme_name, tokens in g502_gui.THEMES.items():
                    qss = g502_gui.generate_qss(theme_name)
                    self.assertIn(tokens["bg_main"], qss)
                    self.assertIn(tokens["bg_card"], qss)
                    self.assertIn(tokens["accent"], qss)
                    # Check pure black/white 10% alpha image outline rule
                    if theme_name == "Light Pristine":
                        self.assertIn("rgba(0, 0, 0, 0.10)", qss)
                    else:
                        self.assertIn("rgba(255, 255, 255, 0.10)", qss)

                    # Verify SVG files were generated with theme colors
                    down_svg = os.path.join(tmpdir, "chevron_down.svg")
                    up_svg = os.path.join(tmpdir, "chevron_up.svg")
                    check_svg = os.path.join(tmpdir, "check.svg")
                    self.assertTrue(os.path.exists(down_svg))
                    self.assertTrue(os.path.exists(up_svg))
                    self.assertTrue(os.path.exists(check_svg))
                    with open(down_svg, "r") as f:
                        self.assertIn(tokens["accent"], f.read())


class TestG733HardwareDriver(unittest.TestCase):
    def setUp(self):
        g502_gui._last_battery_pct = None
        g502_gui._is_app_querying = False

    @patch("glob.glob")
    @patch("os.path.exists")
    def test_find_g733_hidraw_found_and_not_found(self, mock_exists, mock_glob):
        mock_glob.return_value = ["/sys/class/hidraw/hidraw0", "/sys/class/hidraw/hidraw3"]
        mock_exists.return_value = True

        def fake_open(path, *args, **kwargs):
            if "hidraw3" in path:
                return mock_open(read_data="HID_ID=0003:0000046D:00000AB5\n")()
            return mock_open(read_data="HID_ID=0003:0000046D:0000C332\n")()

        with patch("builtins.open", side_effect=fake_open):
            self.assertEqual(g502_gui.find_g733_hidraw(), "/dev/hidraw3")

        mock_glob.return_value = []
        self.assertIsNone(g502_gui.find_g733_hidraw())

    @patch("g502_gui.find_g733_hidraw")
    @patch("os.open")
    @patch("os.write")
    @patch("os.read")
    @patch("os.close")
    def test_get_g733_battery_info_curve_and_hysteresis(
        self, mock_close, mock_read, mock_write, mock_open_fd, mock_find
    ):
        mock_find.return_value = "/dev/hidraw3"
        mock_open_fd.return_value = 99

        # 3950 mV (0x0F6E), status=1 (Discharging) -> 85%
        mock_read.return_value = bytes([0x11, 0xFF, 0x08, 0x00, 0x0F, 0x6E, 0x01])
        pct, status, mv = g502_gui.get_g733_battery_info()
        self.assertEqual(pct, 85)
        self.assertEqual(status, "Discharging")
        self.assertEqual(mv, 3950)

        # Hysteresis test: minor bounce up to 3990 mV (90%, within 5% step) while discharging stays at 85%
        mock_read.return_value = bytes([0x11, 0xFF, 0x08, 0x00, 0x0F, 0x96, 0x01])
        pct2, _, _ = g502_gui.get_g733_battery_info()
        self.assertEqual(pct2, 85)

        # Significant drop to 3660 mV (0x0E4C) updates downward to 50%
        mock_read.return_value = bytes([0x11, 0xFF, 0x08, 0x00, 0x0E, 0x4C, 0x01])
        pct_drop, _, _ = g502_gui.get_g733_battery_info()
        self.assertEqual(pct_drop, 50)

        # Charging status (3) bypasses discharge hysteresis -> 4130 mV (0x1022) = 100%
        mock_read.return_value = bytes([0x11, 0xFF, 0x08, 0x00, 0x10, 0x22, 0x03])
        pct3, status3, mv3 = g502_gui.get_g733_battery_info()
        self.assertEqual(pct3, 100)
        self.assertEqual(status3, "Charging")
        self.assertEqual(mv3, 4130)

    @patch("g502_gui.find_g733_hidraw")
    @patch("os.open")
    @patch("os.write")
    @patch("os.close")
    @patch("time.sleep")
    def test_set_g733_rgb_and_sidetone(self, mock_sleep, mock_close, mock_write, mock_open_fd, mock_find):
        mock_find.return_value = "/dev/hidraw3"
        mock_open_fd.return_value = 42

        ok_rgb = g502_gui.set_g733_rgb(56, 189, 248, mode=1)
        self.assertTrue(ok_rgb)
        self.assertEqual(mock_write.call_count, 3)  # Zones 0, 1, 0xFF

        mock_write.reset_mock()
        ok_side = g502_gui.set_g733_sidetone(50)
        self.assertTrue(ok_side)
        written_pkt = mock_write.call_args[0][1]
        self.assertEqual(written_pkt[:5], bytes([0x11, 0xFF, 0x07, 0x10, 64]))  # 50% of 128 = 64

    @patch("subprocess.run")
    def test_speak_text_fallback(self, mock_run):
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]
        g502_gui.speak_text("Battery 85 percent")
        time.sleep(0.05)
        self.assertGreaterEqual(mock_run.call_count, 2)


class TestBackgroundHardwareThreads(unittest.TestCase):
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_mic_meter_thread_pcm_db_calculation(self, mock_popen, mock_run):
        mock_run.return_value = MagicMock(stdout="alsa_input.usb-Logitech_G733\n")
        fake_proc = MagicMock()
        # Generate 800 samples (1600 bytes) of amplitude 16384 (~ -6 dB -> ~85%)
        pcm_chunk = struct.pack("<800h", *([16384] * 800))

        thread = g502_gui.MicMeterThread()
        received = []
        stop_flag = {"stop": False}
        thread.isInterruptionRequested = MagicMock(side_effect=lambda: stop_flag["stop"])
        thread.level_signal = MagicMock()
        thread.level_signal.emit.side_effect = lambda lvl: (received.append(lvl), stop_flag.update({"stop": True}))

        fake_proc.stdout.read.return_value = pcm_chunk
        mock_popen.return_value = fake_proc

        with patch("time.sleep"):
            thread.run()

        self.assertEqual(len(received), 1)
        self.assertGreater(received[0], 70)

    @patch("evdev.list_devices")
    @patch("select.epoll")
    def test_g733_power_button_listener_thread(self, mock_epoll_cls, mock_list_devs):
        mock_list_devs.return_value = ["/dev/input/event9"]
        fake_ev = MagicMock(type=g502_gui.evdev.ecodes.EV_KEY, value=1)

        class FakeInputDevice:
            def __init__(self, path):
                self.path = path
                self.name = "Logitech G733 Gaming Headset"
                self.fd = 99

            def read(self):
                return [fake_ev]

        fake_epoll = MagicMock()
        fake_epoll.poll.return_value = [(99, 1)]
        mock_epoll_cls.return_value = fake_epoll

        thread = g502_gui.G733PowerButtonListenerThread()
        emitted = []
        stop_flag = {"stop": False}
        thread.isInterruptionRequested = MagicMock(side_effect=lambda: stop_flag["stop"])
        thread.speak_battery_signal = MagicMock()
        thread.speak_battery_signal.emit.side_effect = lambda: (emitted.append(True), stop_flag.update({"stop": True}))

        with patch.object(g502_gui.evdev, "InputDevice", FakeInputDevice), patch("time.sleep"):
            thread.run()

        self.assertEqual(len(emitted), 1)


class TestSettingsAndRatbagDiscovery(unittest.TestCase):
    def test_save_and_load_app_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings_path = os.path.join(tmpdir, "settings.json")
            with patch.object(g502_gui, "SETTINGS_PATH", test_settings_path):
                defaults = g502_gui.load_app_settings()
                self.assertEqual(defaults["theme"], "Dark Void (Default)")

                custom = {"theme": "Tokyo Night", "minimize_to_tray": False, "show_notifications": True}
                g502_gui.save_app_settings(custom)
                loaded = g502_gui.load_app_settings()
                self.assertEqual(loaded["theme"], "Tokyo Night")
                self.assertFalse(loaded["minimize_to_tray"])

    @patch("subprocess.check_output")
    def test_get_all_ratbag_mice(self, mock_co):
        def fake_ratbag(cmd, **kwargs):
            if cmd == ["ratbagctl", "list"]:
                return b"cheering-viscacha: Logitech Gaming Mouse G502\ndummy-kbd: Virtual Keyboard\n"
            if "cheering-viscacha" in cmd:
                return b"Number of Buttons: 11\nNumber of Profiles: 3\n"
            return b"Number of Buttons: 0\n"

        mock_co.side_effect = fake_ratbag
        mice = g502_gui.get_all_ratbag_mice()
        self.assertEqual(len(mice), 1)
        self.assertEqual(mice[0]["id"], "cheering-viscacha")
        self.assertEqual(mice[0]["buttons"], 11)
        self.assertEqual(mice[0]["profiles"], 3)


class TestGUIWindowAndTabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.cfg_path = os.path.join(cls.tmpdir.name, "config.json")
        cls.settings_path = os.path.join(cls.tmpdir.name, "settings.json")
        cls.icons_dir = os.path.join(cls.tmpdir.name, "icons")

        cls.p_cfg = patch.object(g502_gui, "CONFIG_PATH", cls.cfg_path)
        cls.p_set = patch.object(g502_gui, "SETTINGS_PATH", cls.settings_path)
        cls.p_ico = patch.object(g502_gui, "ICONS_CACHE_DIR", cls.icons_dir)
        cls.p_lt = patch.object(g502_gui.G733PowerButtonListenerThread, "start", MagicMock())
        cls.p_mt = patch.object(g502_gui.MicMeterThread, "start", MagicMock())
        cls.p_sub_run = patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="active\n"))
        cls.p_sub_co = patch("subprocess.check_output", return_value=b"mock log output\n")

        cls.p_cfg.start()
        cls.p_set.start()
        cls.p_ico.start()
        cls.p_lt.start()
        cls.p_mt.start()
        cls.mock_run = cls.p_sub_run.start()
        cls.mock_co = cls.p_sub_co.start()

        cls.win = g502_gui.G502ControlApp()

    @classmethod
    def tearDownClass(cls):
        cls.p_cfg.stop()
        cls.p_set.stop()
        cls.p_ico.stop()
        cls.p_lt.stop()
        cls.p_mt.stop()
        cls.p_sub_run.stop()
        cls.p_sub_co.stop()
        cls.tmpdir.cleanup()

    def test_device_switcher_and_default_dpi(self):
        self.assertEqual(self.win.dpi_slider.value(), 800)
        self.assertEqual(self.win.dpi_val_label.text(), "800 DPI")

        self.win.combo_main_device.setCurrentIndex(1)
        self.assertEqual(self.win.device_stack.currentIndex(), 1)
        self.win.combo_main_device.setCurrentIndex(0)
        self.assertEqual(self.win.device_stack.currentIndex(), 0)

    @patch.object(QMessageBox, "information")
    def test_interactive_button_studio_and_save(self, mock_msg):
        self.win.select_button("G7")
        self.assertEqual(self.win.active_button_key, "G7")
        self.assertIn("G7", self.win.selected_title_lbl.text())

        # Switch to CUSTOM_KEY_LOOP and verify custom key dropdown visibility
        for i in range(self.win.combo_action.count()):
            if self.win.combo_action.itemData(i) == "CUSTOM_KEY_LOOP":
                self.win.combo_action.setCurrentIndex(i)
                break
        self.assertFalse(self.win.combo_key.isHidden())
        self.win.spin_hold.setValue(35)
        self.win.spin_delay.setValue(75)
        self.assertEqual(self.win.buttons_cfg["G7"]["hold_ms"], 35)
        self.assertEqual(self.win.buttons_cfg["G7"]["delay_ms"], 75)

        self.win.save_macro_config()
        self.assertTrue(os.path.exists(self.cfg_path))
        with open(self.cfg_path, "r") as f:
            saved = json.load(f)
        self.assertEqual(saved["buttons"]["G7"]["hold_ms"], 35)
        mock_msg.assert_called_once()

    @patch.object(QMessageBox, "information")
    def test_dpi_kwin_paths_and_exact_1_to_1_calibration(self, mock_msg):
        with patch("subprocess.check_output") as mock_co:
            mock_co.side_effect = [
                "/org/kde/KWin/InputDevice/event5\n/org/kde/KWin/InputDevice/event19\n",
                's "Generic Keyboard"',
                's "Logitech Gaming Mouse G502"',
            ]
            paths = self.win.get_kwin_mouse_paths()
            self.assertEqual(paths, ["/org/kde/KWin/InputDevice/event19"])

        self.win.set_dpi(1600)
        self.assertEqual(self.win.dpi_slider.value(), 1600)
        self.assertEqual(self.win.dpi_val_label.text(), "1600 DPI")

        self.win.spin_px_cm.setValue(265.72)
        self.win.apply_exact_calibration()
        # Calibration locks hardware DPI to 1000 and sets flat accel (-0.32507)
        self.assertEqual(self.win.dpi_slider.value(), 1000)
        self.assertEqual(self.win.combo_profile.currentIndex(), 0)
        self.assertEqual(self.win.speed_val_label.text(), "-0.32507")
        mock_msg.assert_called_once()

    def test_headset_equalizer_interpolation_and_hidpp_write(self):
        with patch("g502_gui.find_g733_hidraw", return_value="/dev/hidraw3"), \
             patch("os.open", return_value=77), \
             patch("os.write") as mock_write, \
             patch("os.read", return_value=bytes([0x11, 0xFF, 0x00, 0x10, 0x09] + [0]*15)), \
             patch("os.close"), \
             patch("select.select", return_value=([77], [], [])):

            self.win.apply_eq_preset("FPS Gaming")
            slider_vals = [sl.value() for sl in self.win.eq_sliders]
            self.assertEqual(slider_vals, [-2, 3, 5, 4, 2])
            time.sleep(0.08)  # Allow async _send_eq thread to complete
            self.assertTrue(mock_write.called)

    def test_headset_mic_sidetone_rgb_and_battery_announcement(self):
        self.win.on_hs_vol_changed(72)
        self.assertEqual(self.win.lbl_hs_vol.text(), "72%")

        self.win.on_mic_vol_changed(88)
        self.assertEqual(self.win.lbl_mic_vol.text(), "88%")

        # Test mic mute toggle (MUTED vs LIVE)
        with patch("subprocess.run", return_value=MagicMock(stdout="Volume: 0.88 [MUTED]\n")):
            self.win.toggle_headset_mic()
            self.assertIn("MUTED", self.win.btn_mic_mute.text())
        with patch("subprocess.run", return_value=MagicMock(stdout="Volume: 0.88\n")):
            self.win.toggle_headset_mic()
            self.assertIn("LIVE", self.win.btn_mic_mute.text())

        self.win.on_sidetone_changed(45)
        self.assertEqual(self.win.lbl_sidetone.text(), "45%")

        self.win.update_mic_meter_level(64)
        self.assertEqual(self.win.mic_meter.value(), 64)

        with patch("g502_gui.set_g733_rgb") as mock_rgb:
            self.win.combo_hs_effect.setCurrentIndex(2)  # Spectrum Cycle (mode 3)
            mock_rgb.assert_called_with(0, 255, 255, mode=3)

        with patch("g502_gui.get_g733_battery_info", return_value=(90, "Discharging", 3990)), \
             patch("g502_gui.speak_text") as mock_speak:
            self.win.refresh_battery_status()
            self.assertIn("90%", self.win.lbl_header_battery.text())
            self.win.speak_current_battery()
            mock_speak.assert_called_with("Battery 90 percent")

    @patch.object(QMessageBox, "information")
    def test_service_toggle_openrgb_and_close_event(self, mock_msg):
        with patch("g502_gui.set_g733_rgb") as mock_rgb:
            self.win.apply_all_black_rgb()
            mock_rgb.assert_called_with(0, 0, 0, mode=0)
            mock_msg.assert_called_once()

        # Test service status toggle
        with patch("subprocess.run", return_value=MagicMock(stdout="inactive\n")):
            self.win.update_daemon_status()
            self.assertIn("INACTIVE", self.win.status_badge.text())
        with patch("subprocess.run", return_value=MagicMock(stdout="active\n")):
            self.win.update_daemon_status()
            self.assertIn("ACTIVE", self.win.status_badge.text())
            self.win.toggle_service()

        # Test closeEvent minimizing to tray when minimize_to_tray=True and service is active
        g502_gui.save_app_settings({"theme": "Dark Void (Default)", "minimize_to_tray": True, "show_notifications": False})
        ev_ignore = QCloseEvent()
        with patch("subprocess.run", return_value=MagicMock(stdout="active\n")):
            self.win.closeEvent(ev_ignore)
            self.assertFalse(ev_ignore.isAccepted())

        # Test closeEvent accepting close when service is inactive
        ev_accept = QCloseEvent()
        with patch("subprocess.run", return_value=MagicMock(stdout="inactive\n")):
            self.win.closeEvent(ev_accept)
            self.assertTrue(ev_accept.isAccepted())

    def test_settings_dialog_and_diagnostics(self):
        dlg = g502_gui.SettingsDialog(self.win)
        dlg.combo_theme.setCurrentText("Emerald Forest")
        self.assertEqual(dlg.settings["theme"], "Emerald Forest")

        dlg.chk_tray.setChecked(False)
        self.assertFalse(dlg.settings["minimize_to_tray"])

        dlg.run_diagnostics()
        self.assertIn("LOGITECH LINUX CONTROL SUITE HEALTH AUDIT", dlg.diag_text.toPlainText())
        dlg.close()


class TestG502MacroDaemon(unittest.TestCase):
    @patch("glob.glob")
    @patch("g502_macro_daemon.InputDevice")
    @patch("g502_macro_daemon.UInput")
    def test_find_g502_device(self, mock_uinput, mock_input_dev, mock_glob):
        mock_glob.return_value = ["/dev/input/event2", "/dev/input/event8"]
        dev_kbd = MagicMock()
        dev_kbd.name = "Logitech Gaming Mouse G502 Keyboard"
        dev_kbd.info.vendor = 0x046D
        dev_kbd.info.product = 0xC332

        dev_mouse = MagicMock()
        dev_mouse.name = "Logitech Gaming Mouse G502"
        dev_mouse.info.vendor = 0x046D
        dev_mouse.info.product = 0xC332

        mock_input_dev.side_effect = [dev_kbd, dev_mouse]
        daemon = g502_macro_daemon.G502MacroDaemon()
        found = daemon.find_g502_device()
        self.assertEqual(found, dev_mouse)
        daemon.shutdown()

    @patch("g502_macro_daemon.UInput")
    def test_daemon_actions_loops_tilt_expiry_and_clipboard(self, mock_uinput_cls):
        mock_ui = MagicMock()
        mock_uinput_cls.return_value = mock_ui

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = os.path.join(tmpdir, "config.json")
            test_cfg = {
                "buttons": {
                    "G8": {"name": "G8", "action_type": "LEFT_CLICK_LOOP", "hold_ms": 10, "delay_ms": 10, "custom_key": "KEY_SPACE"},
                    "G9": {"name": "G9", "action_type": "CLIPBOARD_WIN_V", "hold_ms": 10, "delay_ms": 10, "custom_key": "KEY_SPACE"},
                    "G7": {"name": "G7", "action_type": "CUSTOM_KEY_LOOP", "hold_ms": 10, "delay_ms": 10, "custom_key": "KEY_E"},
                    "TILT_LEFT": {"name": "Tilt Left", "action_type": "DISABLED", "hold_ms": 10, "delay_ms": 10, "custom_key": "KEY_SPACE"},
                    "TILT_RIGHT": {"name": "Tilt Right", "action_type": "RIGHT_CLICK_LOOP", "hold_ms": 10, "delay_ms": 10, "custom_key": "KEY_SPACE"},
                }
            }
            with open(cfg_file, "w") as f:
                json.dump(test_cfg, f)

            with patch.object(g502_macro_daemon, "CONFIG_PATH", cfg_file):
                daemon = g502_macro_daemon.G502MacroDaemon()

                # 1. Test DISABLED button does nothing
                daemon.trigger_button_action("TILT_LEFT", True)
                self.assertNotIn("TILT_LEFT", daemon.active_threads)

                # 2. Test Win + V Clipboard macro
                daemon.trigger_button_action("G9", True)
                time.sleep(0.08)
                self.assertTrue(mock_ui.write.called)

                # 3. Test Hold/Repeat Loop start and stop
                mock_ui.write.reset_mock()
                daemon.trigger_button_action("G8", True)
                self.assertIn("G8", daemon.active_threads)
                time.sleep(0.035)
                daemon.trigger_button_action("G8", False)
                self.assertNotIn("G8", daemon.active_threads)
                self.assertTrue(mock_ui.write.called)

                # 4. Test timeout_based wheel tilt pulse extension
                daemon.trigger_button_action("TILT_RIGHT", True, timeout_based=True)
                self.assertIn("TILT_RIGHT", daemon.active_threads)
                old_expiry = daemon.active_threads["TILT_RIGHT"][2]["expiry"]
                time.sleep(0.02)
                daemon.trigger_button_action("TILT_RIGHT", True, timeout_based=True)
                new_expiry = daemon.active_threads["TILT_RIGHT"][2]["expiry"]
                self.assertGreater(new_expiry, old_expiry)

                # 5. Test Custom Key Loop & SIGHUP reload
                daemon.trigger_button_action("G7", True)
                time.sleep(0.025)
                daemon.reload_config()
                daemon.shutdown()
                self.assertFalse(daemon.running)


if __name__ == "__main__":
    unittest.main(verbosity=2)
