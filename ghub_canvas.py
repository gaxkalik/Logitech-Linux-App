#!/usr/bin/env python3
"""
Logitech G HUB Hardware Stage Canvas & Vector SVG Icon Renderer
"""

import os
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage, QPainterPath, QPolygonF
)
from PyQt6.QtWidgets import QWidget


def write_ghub_svgs(cache_dir, accent_hex, text_main_hex, text_sub_hex, bg_main_hex):
    """Generates strict, non-emoji geometric vector SVGs matching text weight (1.75px-2.0px)."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = {}

    def _save(name, svg_body):
        p = os.path.join(cache_dir, name)
        with open(p, "w") as f:
            f.write(svg_body)
        paths[name] = p

    _save(
        "chevron_down.svg",
        f'<svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M1.5 1.75L6 6.25L10.5 1.75" stroke="{accent_hex}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    )
    _save(
        "chevron_up.svg",
        f'<svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M1.5 6.25L6 1.75L10.5 6.25" stroke="{accent_hex}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    )
    _save(
        "check.svg",
        f'<svg width="12" height="10" viewBox="0 0 12 10" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M1.5 5.25L4.5 8.25L10.5 1.75" stroke="{bg_main_hex}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    )
    # Rail Icon 1: Assignments ([+] square)
    for state, col in [("idle", text_sub_hex), ("active", "#FFFFFF")]:
        _save(
            f"rail_assign_{state}.svg",
            f'<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="2.5" y="2.5" width="15" height="15" rx="2" stroke="{col}" stroke-width="1.75"/>'
            f'<path d="M10 6.5V13.5M6.5 10H13.5" stroke="{col}" stroke-width="1.75" stroke-linecap="round"/></svg>',
        )
        # Rail Icon 2: Sensitivity / Audio Sliders (Crosshair / Diamond)
        _save(
            f"rail_dpi_{state}.svg",
            f'<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M10 2.5L17.5 10L10 17.5L2.5 10L10 2.5Z" stroke="{col}" stroke-width="1.75"/>'
            f'<circle cx="10" cy="10" r="2" fill="{col}"/></svg>',
        )
        # Rail Icon 3: LIGHTSYNC (Sun / Rays)
        _save(
            f"rail_lightsync_{state}.svg",
            f'<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="10" cy="10" r="3.5" stroke="{col}" stroke-width="1.75"/>'
            f'<path d="M10 2V4.2M10 15.8V18M2 10H4.2M15.8 10H18M4.3 4.3L5.9 5.9M14.1 14.1L15.7 15.7M15.7 4.3L14.1 5.9M5.9 14.1L4.3 15.7" stroke="{col}" stroke-width="1.75" stroke-linecap="round"/></svg>',
        )
        # Rail Icon 4: Telemetry / Logs / Acoustics
        _save(
            f"rail_logs_{state}.svg",
            f'<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M3 14L7 9L11 12L17 5" stroke="{col}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M3 17H17" stroke="{col}" stroke-width="1.75" stroke-linecap="round"/></svg>',
        )

    _save(
        "nav_back.svg",
        f'<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="M14.5 9H3.5M3.5 9L8 4.5M3.5 9L8 13.5" stroke="{text_main_hex}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    )
    _save(
        "nav_gear.svg",
        f'<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="9" cy="9" r="2.6" stroke="{text_main_hex}" stroke-width="1.75"/>'
        f'<path d="M9 2V3.8M9 14.2V16M2 9H3.8M14.2 9H16M4.1 4.1L5.4 5.4M12.6 12.6L13.9 13.9M13.9 4.1L12.6 5.4M5.4 12.6L4.1 13.9" stroke="{text_main_hex}" stroke-width="1.75" stroke-linecap="round"/></svg>',
    )
    return paths


def build_dark_g502_pixmap(diagram_path):
    """Extracts the G502 mouse silhouette from g502_diagram.png and renders it as dark anodized charcoal."""
    if not os.path.exists(diagram_path):
        return None
    img = QImage(diagram_path).convertToFormat(QImage.Format.Format_ARGB32)
    crop = img.copy(240, 105, 215, 345)
    w, h = crop.width(), crop.height()

    clean = QImage(crop)
    for y in range(3, h - 3):
        for x in range(w):
            c = crop.pixelColor(x, y)
            lum = (c.red() + c.green() + c.blue()) // 3
            if x < 62 and y < 50 and lum < 175:
                clean.setPixelColor(x, y, QColor(30, 34, 51))
                continue
            if lum < 95 and ((45 <= x <= 68 and 40 <= y <= 110) or (26 <= x <= 48 and 120 <= y <= 145)):
                clean.setPixelColor(x, y, QColor(238, 238, 236))
                continue
            if 92 <= y <= 104 or 129 <= y <= 141:
                c_up = crop.pixelColor(x, y - 3)
                c_dn = crop.pixelColor(x, y + 3)
                lum_up = (c_up.red() + c_up.green() + c_up.blue()) // 3
                lum_dn = (c_dn.red() + c_dn.green() + c_dn.blue()) // 3
                if abs(lum_up - lum_dn) < 28 and lum < lum_up - 14:
                    clean.setPixelColor(x, y, c_up)

    out = QImage(w, h, QImage.Format.Format_ARGB32)
    out.fill(QColor(0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            c = clean.pixelColor(x, y)
            r, g, b = c.red(), c.green(), c.blue()
            if r < 65 and g < 65 and b < 80:
                continue
            if (x < 34 or x > 184) and 85 < r < 175:
                continue
            lum = (r + g + b) // 3
            if lum > 225:
                v = 62
                out.setPixelColor(x, y, QColor(v, v + 2, v + 5, 255))
            elif lum > 195:
                v = int(32 + (lum - 195) * 0.8)
                out.setPixelColor(x, y, QColor(v, v + 2, v + 5, 255))
            elif lum > 160:
                v = int(15 + (lum - 160) * 0.38)
                out.setPixelColor(x, y, QColor(v, v + 1, v + 3, 255))
            else:
                out.setPixelColor(x, y, QColor(14, 15, 18, 255))
    return QPixmap.fromImage(out)


class HardwareStageWidget(QWidget):
    """
    Pure #000000 Logitech G HUB Right Interactive Stage:
      - Renders G502 dark anodized hardware with interactive [M] callout lines & G-SHIFT toggle
      - Renders DPI sensitivity track & 1:1 calibration telemetry when in DPI mode
      - Renders G733 LIGHTSPEED headset with live LIGHTSYNC RGB zone preview & 10-band EQ curve
      - Renders bottom G502 / G733 device selector tiles
    """

    button_callout_clicked = pyqtSignal(str)
    device_tile_clicked = pyqtSignal(int)
    buttonClicked = button_callout_clicked
    deviceTileClicked = device_tile_clicked

    def set_device_mode(self, mode):
        if isinstance(mode, str):
            self.device_mode = 0 if mode.upper() == "MOUSE" else 1
        else:
            self.device_mode = int(mode)
        self.update()

    def set_mouse_state(self, active_button_key, buttons_cfg, dpi=800):
        self.set_stage_state(
            active_button_key=active_button_key,
            buttons_cfg=buttons_cfg,
            dpi=dpi
        )

    def set_battery_info(self, pct, status_str, mV):
        self.set_stage_state(battery_tuple=(pct, status_str, mV))

    def set_eq_bands(self, v):
        if len(v) == 5:
            bands_10 = [
                v[0], v[0], (v[0] + v[1]) // 2, v[1], (v[1] + v[2]) // 2,
                v[2], (v[2] + v[3]) // 2, v[3], (v[3] + v[4]) // 2, v[4]
            ]
        else:
            bands_10 = list(v)
        self.set_stage_state(eq_bands_10=bands_10)

    def set_audio_telemetry(self, vol_pct, mic_gain_pct, sidetone_pct, is_muted=False):
        self.set_stage_state(sidetone=sidetone_pct, mic_gain=0 if is_muted else mic_gain_pct)

    def set_headset_rgb(self, r, g, b):
        self.set_stage_state(rgb_tuple=(r, g, b))

    def __init__(self, diagram_path, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(520)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.mouse_pixmap = build_dark_g502_pixmap(diagram_path)

        self.device_mode = 0  # 0 = G502 Mouse, 1 = G733 Headset
        self.sub_tab_index = 0
        self.active_button_key = "G8"
        self.buttons_cfg = {}
        self.current_dpi = 800
        self.current_px_cm = 265.72
        self.current_speed_scale = 0.600
        self.accent_color = QColor("#00A8FC")
        self.rgb_color = QColor("#00A8FC")
        self.eq_bands_10 = [0] * 10
        self.battery_pct = 85
        self.battery_mv = 3950
        self.battery_status = "Discharging"
        self.sidetone_pct = 30
        self.mic_gain_pct = 100
        self.mic_level_pct = 0

        self._callout_hitboxes = {}
        self._device_tile_hitboxes = {}

    def set_stage_state(
        self,
        device_mode=None,
        sub_tab_index=None,
        active_button_key=None,
        buttons_cfg=None,
        dpi=None,
        px_cm=None,
        speed_scale=None,
        accent_hex=None,
        rgb_tuple=None,
        eq_bands_10=None,
        battery_tuple=None,
        sidetone=None,
        mic_gain=None,
        mic_level=None,
    ):
        if device_mode is not None:
            self.device_mode = device_mode
        if sub_tab_index is not None:
            self.sub_tab_index = sub_tab_index
        if active_button_key is not None:
            self.active_button_key = active_button_key
        if buttons_cfg is not None:
            self.buttons_cfg = buttons_cfg
        if dpi is not None:
            self.current_dpi = dpi
        if px_cm is not None:
            self.current_px_cm = px_cm
        if speed_scale is not None:
            self.current_speed_scale = speed_scale
        if accent_hex is not None:
            self.accent_color = QColor(accent_hex)
        if rgb_tuple is not None:
            self.rgb_color = QColor(*rgb_tuple)
        if eq_bands_10 is not None:
            self.eq_bands_10 = list(eq_bands_10)
        if battery_tuple is not None:
            pct, st, mv = battery_tuple
            if pct is not None:
                self.battery_pct = pct
                self.battery_status = st
                self.battery_mv = mv
        if sidetone is not None:
            self.sidetone_pct = sidetone
        if mic_gain is not None:
            self.mic_gain_pct = mic_gain
        if mic_level is not None:
            self.mic_level_pct = mic_level
        self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        for key, rect in self._callout_hitboxes.items():
            if rect.contains(pos):
                self.button_callout_clicked.emit(key)
                return
        for dev_idx, rect in self._device_tile_hitboxes.items():
            if rect.contains(pos):
                self.device_tile_clicked.emit(dev_idx)
                return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w, h = self.width(), self.height()
        # Pure Obsidian #000000 Stage Background
        p.fillRect(0, 0, w, h, QColor("#000000"))

        self._callout_hitboxes.clear()
        self._device_tile_hitboxes.clear()

        if self.device_mode == 0:
            self._paint_mouse_stage(p, w, h)
        else:
            self._paint_headset_stage(p, w, h)

        self._paint_bottom_device_dock(p, w, h)
        p.end()

    def _paint_mouse_stage(self, p, w, h):
        cx, cy = w * 0.52, h * 0.43

        # Subtle background model watermark ("G502") like G HUB carousel
        p.setFont(QFont("Inter", 68, QFont.Weight.Black))
        p.setPen(QColor(22, 22, 25))
        p.drawText(QRectF(0, 18, w, 90), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "G502")

        # Draw dark metallic G502 mouse centered
        mw, mh = 215, 345
        mx, my = int(cx - mw / 2), int(cy - mh / 2)
        if self.mouse_pixmap:
            p.drawPixmap(mx, my, self.mouse_pixmap)

        # Draw G logo RGB accent inside mouse shell
        p.setPen(Qt.PenStyle.NoPen)
        g_col = self.rgb_color if self.rgb_color.lightness() > 15 else self.accent_color
        p.setBrush(QBrush(g_col))
        p.drawEllipse(QPointF(mx + 82, my + 225), 5, 5)

        # Interactive Callouts (exact G HUB style: white dot on button + leader line + [M] label)
        action_short = {
            "LEFT_CLICK_LOOP": "Left Click Loop",
            "RIGHT_CLICK_LOOP": "Right Click Loop",
            "MIDDLE_CLICK_LOOP": "Middle Click Loop",
            "SPACE_LOOP": "Space Key Loop",
            "CLIPBOARD_WIN_V": "Win + V Clipboard",
            "CUSTOM_KEY_LOOP": "Custom Key Loop",
            "DISABLED": "Disabled",
        }

        callouts = [
            # (btn_key, title, dot_dx, dot_dy, line_end_x, line_end_y, align_left)
            ("G8", "G8 (DPI Up)", 56, 52, mx - 155, my + 32, True),
            ("G7", "G7 (DPI Down)", 56, 98, mx - 155, my + 98, True),
            ("TILT_LEFT", "Tilt Left", 94, 98, mx - 155, my + 162, True),
            ("G9", "G9 (Profile)", 120, 162, mx - 155, my + 226, True),
            ("TILT_RIGHT", "Tilt Right", 142, 98, mx + mw + 145, my + 98, False),
        ]

        # Also draw static reference callouts like Image 3 (Primary Click, Secondary Click, Middle Click)
        static_refs = [
            ("Primary Click", mx + 82, my + 48, mx - 155, my - 18, True),
            ("Middle Click", mx + 120, my + 68, mx + 120, my - 38, None),
            ("Secondary Click", mx + 158, my + 48, mx + mw + 145, my - 18, False),
        ]
        for label, sx, sy, ex, ey, is_left in static_refs:
            p.setPen(QPen(QColor("#52525B"), 1.0))
            if is_left is None:
                p.drawLine(QPointF(sx, sy), QPointF(ex, ey))
                p.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                p.setPen(QColor("#D4D4D8"))
                p.drawText(QRectF(ex - 60, ey - 22, 120, 18), Qt.AlignmentFlag.AlignCenter, label)
            else:
                knee_x = sx - 20 if is_left else sx + 20
                p.drawLine(QPointF(sx, sy), QPointF(knee_x, ey))
                p.drawLine(QPointF(knee_x, ey), QPointF(ex, ey))
                p.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                p.setPen(QColor("#D4D4D8"))
                t_rect = QRectF(ex, ey - 18, 130, 16) if is_left else QRectF(ex - 130, ey - 18, 130, 16)
                align = Qt.AlignmentFlag.AlignLeft if is_left else Qt.AlignmentFlag.AlignRight
                p.drawText(t_rect, align | Qt.AlignmentFlag.AlignVCenter, label)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#E4E4E7"))
            p.drawEllipse(QPointF(sx, sy), 3.5, 3.5)

        for key, title, dx, dy, ex, ey, is_left in callouts:
            sx, sy = mx + dx, my + dy
            is_selected = (key == self.active_button_key)
            cfg = self.buttons_cfg.get(key, {})
            act_code = cfg.get("action_type", "LEFT_CLICK_LOOP")
            act_label = action_short.get(act_code, act_code)
            if act_code == "CUSTOM_KEY_LOOP":
                act_label = cfg.get("custom_key", "KEY_SPACE").replace("KEY_", "Key ")

            line_col = self.accent_color if is_selected else QColor("#71717A")
            p.setPen(QPen(line_col, 1.4 if is_selected else 1.0))
            knee_x = sx - 24 if is_left else sx + 24
            p.drawLine(QPointF(sx, sy), QPointF(knee_x, ey))
            p.drawLine(QPointF(knee_x, ey), QPointF(ex, ey))

            # Target dot on physical mouse button
            p.setPen(QPen(QColor("#000000"), 1.5))
            p.setBrush(self.accent_color if is_selected else QColor("#FFFFFF"))
            p.drawEllipse(QPointF(sx, sy), 5.0 if is_selected else 4.0, 5.0 if is_selected else 4.0)

            # [M] Badge + Label above the leader line
            bx = ex if is_left else ex - 185
            by = ey - 24
            hit_rect = QRectF(bx - 2, by - 2, 195, 24)
            self._callout_hitboxes[key] = hit_rect

            # [M] square icon
            m_rect = QRectF(bx, by + 1, 16, 16)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.accent_color if is_selected else QColor("#52525B"))
            p.drawRoundedRect(m_rect, 2, 2)
            p.setFont(QFont("JetBrains Mono", 8, QFont.Weight.Bold))
            p.setPen(QColor("#000000") if is_selected else QColor("#FFFFFF"))
            p.drawText(m_rect, Qt.AlignmentFlag.AlignCenter, "M")

            # Callout text
            p.setFont(QFont("Inter", 9, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            p.setPen(self.accent_color if is_selected else QColor("#F4F4F5"))
            p.drawText(
                QRectF(bx + 22, by, 175, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{key}: {act_label}",
            )

        # If on DPI & Calibration tab (sub_tab_index == 1), draw live DPI ruler bar above bottom dock
        if self.sub_tab_index == 1:
            bar_y = h - 135
            p.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            p.setPen(QColor("#A1A1AA"))
            p.drawText(
                QRectF(40, bar_y - 22, w - 80, 18),
                Qt.AlignmentFlag.AlignCenter,
                f"ACTIVE SENSOR: {self.current_dpi} DPI   |   CALIBRATED RATIO: {self.current_px_cm:.2f} PX/CM   |   KWIN FLAT SCALE: {self.current_speed_scale:+.3f}",
            )
            track_l, track_r = 80, w - 80
            p.setPen(QPen(QColor("#27272A"), 2))
            p.drawLine(QPointF(track_l, bar_y), QPointF(track_r, bar_y))
            ratio = max(0.0, min(1.0, (self.current_dpi - 400) / 3600.0))
            dx = track_l + ratio * (track_r - track_l)
            p.setPen(QPen(self.accent_color, 2))
            p.drawLine(QPointF(track_l, bar_y), QPointF(dx, bar_y))
            # Diamond marker
            diamond = QPolygonF([
                QPointF(dx, bar_y - 6),
                QPointF(dx + 6, bar_y),
                QPointF(dx, bar_y + 6),
                QPointF(dx - 6, bar_y),
            ])
            p.setBrush(self.accent_color)
            p.drawPolygon(diamond)
        else:
            # DEFAULT / G-SHIFT pill indicator (like Image 3)
            gs_y = h - 125
            p.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(cx - 110, gs_y, 70, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "DEFAULT")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#3F3F46"))
            p.drawRoundedRect(QRectF(cx - 32, gs_y + 3, 28, 14), 7, 7)
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(cx - 25, gs_y + 10), 5, 5)
            p.setPen(QColor("#71717A"))
            p.drawText(QRectF(cx + 4, gs_y, 70, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "G-SHIFT")

    def _paint_headset_stage(self, p, w, h):
        cx, cy = w * 0.50, h * 0.34

        # Background model watermark ("G733")
        p.setFont(QFont("Inter", 68, QFont.Weight.Black))
        p.setPen(QColor(22, 22, 25))
        p.drawText(QRectF(0, 16, w, 90), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "G733")

        # Technical Vector Illustration of G733 Headset
        p.save()
        p.translate(cx, cy)
        # Outer headband arc
        band_path = QPainterPath()
        band_path.moveTo(-78, 10)
        band_path.cubicTo(-78, -95, 78, -95, 78, 10)
        p.setPen(QPen(QColor("#27272A"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(band_path)
        # Suspension strap
        strap_path = QPainterPath()
        strap_path.moveTo(-64, -8)
        strap_path.cubicTo(-45, -62, 45, -62, 64, -8)
        p.setPen(QPen(self.accent_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(strap_path)

        # Left & Right Earcups
        for sign in (-1, 1):
            p.save()
            p.translate(sign * 76, 32)
            p.rotate(sign * -8)
            p.setPen(QPen(QColor("#3F3F46"), 1.5))
            p.setBrush(QColor("#18181B"))
            p.drawRoundedRect(QRectF(-24, -42, 48, 84), 14, 14)
            # Dual-zone LIGHTSYNC front RGB lightstrips
            rgb_col = self.rgb_color
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(rgb_col)
            strip_x = -20 if sign == -1 else 14
            p.drawRoundedRect(QRectF(strip_x, -28, 6, 24), 3, 3)
            p.drawRoundedRect(QRectF(strip_x, 4, 6, 24), 3, 3)
            p.restore()

        # Detachable Boom Mic on left earcup
        p.setPen(QPen(QColor("#52525B"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(-88, 62), QPointF(-42, 86))
        p.setBrush(self.accent_color)
        p.drawEllipse(QPointF(-40, 87), 4, 4)
        p.restore()

        # Live 10-Band Hardware Equalizer Graph below headset
        graph_rect = QRectF(56, h * 0.56, w - 112, 110)
        p.setPen(QPen(QColor("#1F1F23"), 1))
        p.setBrush(QColor("#09090B"))
        p.drawRoundedRect(graph_rect, 4, 4)

        # Horizontal dB gridlines (+12, 0, -12 dB)
        for frac, lbl in [(0.15, "+12 dB"), (0.50, "0 dB"), (0.85, "-12 dB")]:
            gy = graph_rect.top() + frac * graph_rect.height()
            p.setPen(QPen(QColor("#1E1E22"), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(graph_rect.left() + 42, gy), QPointF(graph_rect.right() - 12, gy))
            p.setFont(QFont("JetBrains Mono", 8))
            p.setPen(QColor("#71717A"))
            p.drawText(QRectF(graph_rect.left() + 4, gy - 8, 36, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, lbl)

        # Plot 10 bands (32Hz..16kHz)
        freqs = ["32", "64", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
        pts = []
        plot_l = graph_rect.left() + 52
        plot_r = graph_rect.right() - 20
        mid_y = graph_rect.top() + 0.50 * graph_rect.height()
        amp_h = 0.35 * graph_rect.height()
        for i, val in enumerate(self.eq_bands_10):
            px = plot_l + (i / 9.0) * (plot_r - plot_l)
            py = mid_y - (max(-12, min(12, val)) / 12.0) * amp_h
            pts.append(QPointF(px, py))
            p.setFont(QFont("JetBrains Mono", 8))
            p.setPen(QColor("#71717A"))
            p.drawText(QRectF(px - 16, graph_rect.bottom() - 16, 32, 14), Qt.AlignmentFlag.AlignCenter, freqs[i])

        if len(pts) >= 2:
            curve = QPainterPath(pts[0])
            for pt in pts[1:]:
                curve.lineTo(pt)
            p.setPen(QPen(self.accent_color, 2.0))
            p.drawPath(curve)
            for pt in pts:
                p.setPen(QPen(QColor("#000000"), 1.5))
                p.setBrush(self.accent_color)
                p.drawEllipse(pt, 3.5, 3.5)

        # Telemetry readout row
        p.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        p.setPen(QColor("#A1A1AA"))
        p.drawText(
            QRectF(40, graph_rect.bottom() + 8, w - 80, 18),
            Qt.AlignmentFlag.AlignCenter,
            f"BATTERY: {self.battery_pct}% ({self.battery_mv} mV)   |   SIDETONE: {self.sidetone_pct}%   |   MIC GAIN: {self.mic_gain_pct}%",
        )

    def _paint_bottom_device_dock(self, p, w, h):
        """Draws the bottom G HUB device selector strip (G502 HERO | G733 LIGHTSPEED)."""
        dock_y = h - 78
        tile_w, tile_h = 128, 44
        gap = 14
        start_x = (w - (tile_w * 2 + gap)) / 2

        devices = [
            (0, "G502 HERO", "OPTICAL MOUSE"),
            (1, "G733", f"{self.battery_pct}% LIGHTSPEED"),
        ]
        for idx, title, sub in devices:
            tx = start_x + idx * (tile_w + gap)
            rect = QRectF(tx, dock_y, tile_w, tile_h)
            self._device_tile_hitboxes[idx] = rect
            active = (self.device_mode == idx)
            p.setPen(QPen(self.accent_color if active else QColor("#27272A"), 1.5 if active else 1.0))
            p.setBrush(QColor("#141417") if active else QColor("#0B0B0D"))
            p.drawRoundedRect(rect, 4, 4)

            p.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            p.setPen(QColor("#FFFFFF") if active else QColor("#A1A1AA"))
            p.drawText(QRectF(tx + 10, dock_y + 6, tile_w - 20, 16), Qt.AlignmentFlag.AlignCenter, title)

            p.setFont(QFont("JetBrains Mono", 8))
            p.setPen(self.accent_color if active else QColor("#71717A"))
            p.drawText(QRectF(tx + 6, dock_y + 22, tile_w - 12, 14), Qt.AlignmentFlag.AlignCenter, sub)

        p.setFont(QFont("Inter", 8, QFont.Weight.DemiBold))
        p.setPen(QColor("#71717A"))
        p.drawText(
            QRectF(0, h - 24, w, 16),
            Qt.AlignmentFlag.AlignCenter,
            "Select active hardware device to configure assignments, acoustics, or LIGHTSYNC.",
        )
