from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QLinearGradient, QConicalGradient
from PySide6.QtCore import Qt, QRect, Slot, QTimer, QMetaObject, Q_ARG, QPointF
import math
from themes import theme_manager, THEMES
from mqtt_client import mqtt_client
import datetime
import os

# ────────────────────────────────────────────────
#   DialGauge class remains 100% unchanged
# ────────────────────────────────────────────────
class DialGauge(QWidget):
    def __init__(self, color_key="primary1"):
        super().__init__()
        self._value = 0.0
        self.display_text = "0.000000"
        self.color_key = color_key
        self.setMinimumSize(200, 200)
        self.previous_value = 0.0
        self.rotation_angle = 0.0
        self.rotation_angle_2 = 0.0
        self.rotation_angle_3 = 0.0
        self.trail_opacity = 0.0
        self.trail_start_angle = 0.0
        self.trail_end_angle = 0.0
        
        if self.color_key != "primary2":
            self.rotation_timer = QTimer(self)
            self.rotation_timer.timeout.connect(self.update_rotation)
            self.rotation_timer.start(50)
            
            self.trail_timer = QTimer(self)
            self.trail_timer.timeout.connect(self.fade_trail)
            self.trail_timer.start(50)

    @Slot()
    def update_rotation(self):
        self.rotation_angle = (self.rotation_angle + 1.0) % 360
        self.rotation_angle_2 = (self.rotation_angle_2 - 0.7) % 360
        self.rotation_angle_3 = (self.rotation_angle_3 + 0.5) % 360
        self.update()

    @Slot()
    def fade_trail(self):
        if self.trail_opacity > 0:
            self.trail_opacity -= 0.02
            if self.trail_opacity < 0:
                self.trail_opacity = 0
            self.update()

    @Slot(float)
    def setValue(self, val):
        self.previous_value = self._value
        self._value = max(0.0, min(val, 200.0))
        self.display_text = f"{val:.6f}"
        
        start_angle = 225
        span_angle = 270
        prev_angle = start_angle - (span_angle * (min(max(self.previous_value, 0), 100) / 100.0))
        curr_angle = start_angle - (span_angle * (min(max(self._value, 0), 100) / 100.0))
        
        self.trail_start_angle = min(prev_angle, curr_angle)
        self.trail_end_angle = max(prev_angle, curr_angle)
        self.trail_opacity = 1.0
        
        self.update()

    def value(self):
        return self._value

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        radius = min(rect.width(), rect.height()) / 2 - 20
        theme = theme_manager.get_theme()

        bg_grad = QRadialGradient(cx, cy, radius + 30)
        bg_grad.setColorAt(0.0, QColor(26, 26, 46))
        bg_grad.setColorAt(1.0, QColor(15, 15, 30))
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_grad)
        painter.drawEllipse(cx - radius - 30, cy - radius - 30, 2 * (radius + 30), 2 * (radius + 30))

        if self.color_key != "primary2":
            ring1_radius = radius + 15
            painter.setPen(QPen(QColor(138, 43, 226, 80), 2))
            painter.setBrush(Qt.NoBrush)
            for i in range(3):
                arc_angle = (self.rotation_angle + i * 120) % 360
                painter.drawArc(cx - ring1_radius, cy - ring1_radius, 2 * ring1_radius, 2 * ring1_radius,
                                int(arc_angle * 16), int(60 * 16))
            
            ring2_radius = radius + 10
            painter.setPen(QPen(QColor(255, 69, 0, 100), 1.5))
            for i in range(4):
                arc_angle = (self.rotation_angle_2 + i * 90) % 360
                painter.drawArc(cx - ring2_radius, cy - ring2_radius, 2 * ring2_radius, 2 * ring2_radius,
                                int(arc_angle * 16), int(45 * 16))
            
            ring3_radius = radius + 5
            painter.setPen(QPen(QColor(0, 191, 255, 60), 1))
            for i in range(6):
                arc_angle = (self.rotation_angle_3 + i * 60) % 360
                painter.drawArc(cx - ring1_radius, cy - ring1_radius, 2 * ring1_radius, 2 * ring1_radius,
                                int(arc_angle * 16), int(30 * 16))

        face_grad = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius)
        face_grad.setColorAt(0.0, QColor(42, 42, 62))
        face_grad.setColorAt(1.0, QColor(26, 26, 46))
        painter.setPen(QPen(QColor(138, 43, 226, 100), 1))
        painter.setBrush(face_grad)
        painter.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)

        shadow_grad = QRadialGradient(cx, cy, radius - 5)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        shadow_grad.setColorAt(0.8, QColor(0, 0, 0, 30))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 80))
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_grad)
        painter.drawEllipse(cx - radius + 5, cy - radius + 5, 2 * (radius - 5), 2 * (radius - 5))

        start_angle = 225
        span_angle = 270
        tick_length_major = 15
        tick_length_minor = 8

        for i in range(51):
            angle = start_angle - (span_angle * (i / 50.0))
            angle_rad = math.radians(angle)
            is_major = (i % 5 == 0)

            outer_x = cx + (radius * math.cos(angle_rad))
            outer_y = cy - (radius * math.sin(angle_rad))
            tick_length = tick_length_major if is_major else tick_length_minor
            inner_x = cx + ((radius - tick_length) * math.cos(angle_rad))
            inner_y = cy - ((radius - tick_length) * math.sin(angle_rad))

            if is_major:
                painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
            painter.drawLine(outer_x, outer_y, inner_x, inner_y)

            if is_major:
                label = str(i * 2)
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                label_radius = radius - 25
                label_x = cx + (label_radius * math.cos(angle_rad)) - 8
                label_y = cy - (label_radius * math.sin(angle_rad)) + 4
                painter.setPen(QColor(255, 255, 255, 180))
                painter.drawText(QRect(label_x, label_y, 16, 12), Qt.AlignCenter, label)

        if self.trail_opacity > 0 and abs(self.trail_end_angle - self.trail_start_angle) > 0.1:
            trail_span = self.trail_end_angle - self.trail_start_angle
            
            trail_grad = QConicalGradient(cx, cy, self.trail_start_angle + 90)
            trail_grad.setColorAt(0.0, QColor(255, 69, 0, 0))
            trail_grad.setColorAt(0.3, QColor(255, 69, 0, int(200 * self.trail_opacity)))
            trail_grad.setColorAt(0.7, QColor(255, 140, 0, int(150 * self.trail_opacity)))
            trail_grad.setColorAt(1.0, QColor(255, 69, 0, 0))
            
            painter.setPen(QPen(trail_grad, 8))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(cx - radius + 10, cy - radius + 10, 2 * (radius - 10), 2 * (radius - 10),
                            int(self.trail_start_angle * 16), int(trail_span * 16))
            
            painter.setPen(QPen(QColor(255, 69, 0, int(80 * self.trail_opacity)), 12))
            painter.drawArc(cx - radius + 10, cy - radius + 10, 2 * (radius - 10), 2 * (radius - 10),
                            int(self.trail_start_angle * 16), int(trail_span * 16))

        value = min(max(self._value, 0), 100)
        needle_angle = start_angle - (span_angle * (value / 100.0))
        needle_rad = math.radians(needle_angle)
        needle_length = radius - 20

        tip_x = cx + (needle_length * math.cos(needle_rad))
        tip_y = cy - (needle_length * math.sin(needle_rad))

        painter.setPen(QPen(QColor(255, 69, 0, 100), 8))
        painter.drawLine(cx, cy, tip_x, tip_y)

        painter.setPen(QPen(QColor(255, 100, 0), 3))
        painter.drawLine(cx, cy, tip_x, tip_y)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 69, 0))
        painter.drawEllipse(tip_x - 3, tip_y - 3, 6, 6)

        hub_grad = QRadialGradient(cx, cy, 12)
        hub_grad.setColorAt(0.0, QColor(255, 100, 0))
        hub_grad.setColorAt(1.0, QColor(255, 69, 0))
        painter.setPen(QPen(QColor(255, 69, 0, 150), 2))
        painter.setBrush(hub_grad)
        painter.drawEllipse(cx - 8, cy - 8, 16, 16)

        painter.setFont(QFont("Helvetica", 10, QFont.Bold))
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.display_text)
        text_height = metrics.height()

        unit_text = "A" if self.color_key == "primary2" else "kW"
        painter.setFont(QFont("Helvetica", 8, QFont.Bold))
        unit_metrics = painter.fontMetrics()
        unit_width = unit_metrics.horizontalAdvance(unit_text)
        unit_height = unit_metrics.height()

        text_color = QColor(0, 191, 255)
        screen_rect = QRect(
            cx - text_width // 2,
            cy + 30,
            text_width,
            text_height + unit_height
        )

        painter.setFont(QFont("Helvetica", 10, QFont.Bold))
        painter.setPen(text_color)
        painter.drawText(
            QRect(screen_rect.left(), screen_rect.top(), screen_rect.width(), text_height),
            Qt.AlignCenter,
            self.display_text
        )

        painter.setFont(QFont("Helvetica", 8, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 150))
        painter.drawText(
            QRect(screen_rect.left(), screen_rect.top() + text_height + 2, screen_rect.width(), unit_height),
            Qt.AlignCenter,
            unit_text
        )


# ────────────────────────────────────────────────
#   Screen1 – only changed: added Light 2 handler
# ────────────────────────────────────────────────
class Screen1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.fan_value = self.load_last_fan_value()
        self.light_value = 0.0
        self.fan_dial.setValue(self.fan_value)
        self.start_logging_timer()
        mqtt_client.current_callback = self.handle_current_update

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(15)

        theme_row = QHBoxLayout()
        theme_row.addStretch()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Obsidian", "Titanium", "Neon", "Aurora"])
        self.theme_combo.setCurrentText(theme_manager.current_theme)
        self.theme_combo.currentIndexChanged.connect(self.main_window.change_theme)
        theme_row.addWidget(self.theme_combo)
        main_layout.addLayout(theme_row)

        title_label = QLabel("Smart Home Control Panel")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        dial_titles = QHBoxLayout()
        for name in ["Fan", "Light", "Total"]:
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 12px; font-weight: bold;")
            dial_titles.addWidget(label)
        main_layout.addLayout(dial_titles)

        self.fan_dial = DialGauge("primary1")
        self.light_dial = DialGauge("primary2")
        self.total_dial = DialGauge("accent")

        dial_row = QHBoxLayout()
        dial_row.addWidget(self.fan_dial)
        dial_row.addWidget(self.light_dial)
        dial_row.addWidget(self.total_dial)
        main_layout.addLayout(dial_row)

        main_layout.addSpacing(20)

        fan_row = QHBoxLayout()
        for i in range(6):
            btn = QPushButton(f"Fan {i+1}")
            btn.setFixedSize(60, 40)
            btn.setCheckable(True)
            fan_row.addWidget(btn)
        main_layout.addLayout(fan_row)

        light_row = QHBoxLayout()
        self.light_buttons = []
        for i in range(6):
            btn = QPushButton(f"Light {i+1}")
            btn.setFixedSize(60, 40)
            btn.setCheckable(True)

            if i == 0:
                btn.clicked.connect(self.handle_light1)
            elif i == 1:
                btn.clicked.connect(self.handle_light2)
            elif i == 2:
                btn.clicked.connect(self.handle_light3)   # NEW
            elif i == 3:
                btn.clicked.connect(self.handle_light4)   # NEW

            # ──────────────────────────────────────────

            light_row.addWidget(btn)
            self.light_buttons.append(btn)
        main_layout.addLayout(light_row)

    # ─── These two methods are what make Light 2 work ───
    def handle_light1(self):
        btn = self.light_buttons[0]
        if btn.isChecked():
            mqtt_client.send_light1("ON")
        else:
            mqtt_client.send_light1("OFF")

    def handle_light2(self):
        btn = self.light_buttons[1]
        if btn.isChecked():
            mqtt_client.send_light2("ON")
        else:
            mqtt_client.send_light2("OFF")

    def handle_light3(self):
        btn = self.light_buttons[2]
        if btn.isChecked():
            mqtt_client.send_light3("ON")
        else:
            mqtt_client.send_light3("OFF")


    def handle_light4(self):
        btn = self.light_buttons[3]
        if btn.isChecked():
            mqtt_client.send_light4("ON")
        else:
            mqtt_client.send_light4("OFF")
    # ───────────────────────────────────────────────────

    def handle_current_update(self, data):
        current = float(data.get("current", 0.0))
        self.light_value = current
        print(f"[DEBUG {datetime.datetime.now()}] MQTT received: current={current:.6f}")
        QMetaObject.invokeMethod(
            self.light_dial, "setValue", Qt.QueuedConnection, Q_ARG(float, current)
        )
        total_sum = self.fan_value + self.light_value
        QMetaObject.invokeMethod(
            self.total_dial, "setValue", Qt.QueuedConnection, Q_ARG(float, total_sum)
        )
        self.log_current_reading()

    def start_logging_timer(self):
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.log_current_reading)
        self.log_timer.start(60000)

    def load_last_fan_value(self):
        log_file = "current_log.txt"
        last_fan_value = 0.0
        last_date = None

        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if line.strip():
                            parts = line.split(" fan energy - ")
                            if len(parts) >= 2:
                                date = parts[0].strip()
                                if date and (last_date is None or date > last_date):
                                    last_date = date
                                    last_fan_value = float(parts[1].split(" - ")[0].strip())
                                    break
            except Exception as e:
                print(f"Error reading log file: {e}")
        return last_fan_value

    def log_current_reading(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        log_file = "current_log.txt"
        fan_energy = f"{self.fan_value:.6f}"
        light_energy = f"{self.light_value:.6f}"
        total_energy = f"{self.fan_value + self.light_value:.6f}"
        log_line = f"{date_str} fan energy - {fan_energy} - light energy - {light_energy} - total energy - {total_energy}\n"

        lines = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"Error reading log file: {e}")

        found_today = False
        for i, line in enumerate(lines):
            if line.startswith(date_str):
                lines[i] = log_line
                found_today = True
                break
        if not found_today:
            lines.append(log_line)

        try:
            with open(log_file, "w") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Error writing to log file: {e}")

print("Current working directory:", os.getcwd())