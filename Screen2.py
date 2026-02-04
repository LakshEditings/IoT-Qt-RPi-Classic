from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                                QLabel, QPushButton, QButtonGroup)
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QRadialGradient, QConicalGradient
from PySide6.QtCore import Qt, QRect, Slot, QTimer, QMetaObject, Q_ARG
import math
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from themes import theme_manager
from mqtt_client import mqtt_client
import datetime
import os


class DialGauge(QWidget):
    """Animated dial gauge for displaying current values"""
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

        # Background gradient
        bg_grad = QRadialGradient(cx, cy, radius + 30)
        bg_grad.setColorAt(0.0, QColor(26, 26, 46))
        bg_grad.setColorAt(1.0, QColor(15, 15, 30))
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_grad)
        painter.drawEllipse(cx - radius - 30, cy - radius - 30, 2 * (radius + 30), 2 * (radius + 30))

        # Animated rings for fan and total dials
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

        # Dial face
        face_grad = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius)
        face_grad.setColorAt(0.0, QColor(42, 42, 62))
        face_grad.setColorAt(1.0, QColor(26, 26, 46))
        painter.setPen(QPen(QColor(138, 43, 226, 100), 1))
        painter.setBrush(face_grad)
        painter.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)

        # Inner shadow
        shadow_grad = QRadialGradient(cx, cy, radius - 5)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        shadow_grad.setColorAt(0.8, QColor(0, 0, 0, 30))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 80))
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_grad)
        painter.drawEllipse(cx - radius + 5, cy - radius + 5, 2 * (radius - 5), 2 * (radius - 5))

        # Draw tick marks and labels
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

        # Motion trail effect
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

        # Draw needle
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

        # Needle hub
        hub_grad = QRadialGradient(cx, cy, 12)
        hub_grad.setColorAt(0.0, QColor(255, 100, 0))
        hub_grad.setColorAt(1.0, QColor(255, 69, 0))
        painter.setPen(QPen(QColor(255, 69, 0, 150), 2))
        painter.setBrush(hub_grad)
        painter.drawEllipse(cx - 12, cy - 12, 24, 24)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 50, 70))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # Display value text
        text_radius = radius * 0.55
        screen_width = radius * 0.7
        screen_height = 40
        screen_rect = QRect(
            int(cx - screen_width / 2),
            int(cy + text_radius - screen_height / 2),
            int(screen_width),
            int(screen_height)
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 20, 40, 200))
        painter.drawRoundedRect(screen_rect, 8, 8)

        painter.setFont(QFont("Courier New", 11, QFont.Bold))
        painter.setPen(QColor(0, 255, 100))
        text_height = 16
        painter.drawText(
            QRect(screen_rect.left(), screen_rect.top() + 5, screen_rect.width(), text_height),
            Qt.AlignCenter,
            self.display_text
        )

        unit_text = "Amps"
        unit_height = 14
        painter.setFont(QFont("Helvetica", 8, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 150))
        painter.drawText(
            QRect(screen_rect.left(), screen_rect.top() + text_height + 2, screen_rect.width(), unit_height),
            Qt.AlignCenter,
            unit_text
        )


class GraphWidget(QWidget):
    """Graph widget for historical data visualization"""
    def __init__(self, title, fan_data, light_data):
        super().__init__()
        self.title = title
        self.fan_data = fan_data
        self.light_data = light_data
        self.plot_type = "LIGHT,FAN"
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(plt.Figure(facecolor=theme_manager.get_theme()["secondary1"]))
        layout.addWidget(self.canvas)
        self.plot()

    def plot(self):
        self.canvas.figure.clear()
        theme = theme_manager.get_theme()
        ax = self.canvas.figure.add_subplot(111)
        self.canvas.figure.patch.set_facecolor(theme["secondary1"])
        ax.set_facecolor(theme["secondary1"])

        days = range(1, len(self.fan_data) + 1)
        bar_width = 0.35

        if self.plot_type == "FAN":
            ax.bar(days, self.fan_data, width=bar_width, color=theme["primary1"], label='Fan Current')
        elif self.plot_type == "LIGHT":
            ax.bar(days, self.light_data, width=bar_width, color=theme["primary2"], label='Light Current')
        elif self.plot_type == "LIGHT+FAN":
            total_data = [f + l for f, l in zip(self.fan_data, self.light_data)]
            ax.bar(days, total_data, width=bar_width, color=theme["accent"], label='Total Current')
        else:  # LIGHT,FAN (default, grouped bars)
            days = list(days)
            ax.bar([d - bar_width/2 for d in days], self.fan_data, width=bar_width, 
                   color=theme["primary1"], label='Fan Current')
            ax.bar([d + bar_width/2 for d in days], self.light_data, width=bar_width, 
                   color=theme["primary2"], label='Light Current')

        ax.set_title(self.title, color=theme["secondary3"], fontweight='bold', fontsize=10)
        ax.set_ylabel("Current (Amps)", color=theme["secondary3"], fontsize=8)
        ax.set_xlabel("Day", color=theme["secondary3"], fontsize=8)
        ax.tick_params(colors=theme["secondary3"], labelsize=6)
        ax.grid(True, linestyle="--", alpha=0.5, color=theme["secondary3"])
        ax.legend()

        ax.autoscale(enable=True, axis='y', tight=False)
        ax.margins(x=0.05)
        ax.autoscale(enable=True, axis='x', tight=False)

        ax.set_xticks(range(1, len(self.fan_data) + 1))
        ax.set_xticklabels(range(1, len(self.fan_data) + 1))

        self.canvas.draw()

    def update_data(self, fan_data, light_data, plot_type):
        self.fan_data = fan_data
        self.light_data = light_data
        self.plot_type = plot_type
        self.plot()


class Screen2(QWidget):
    """Live data monitoring screen with dials and graph view option"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.fan_value = 0.0
        self.light_value = 0.0
        self.view_mode = "live"  # 'live' or 'graph'
        self.setup_ui()
        self.load_initial_data()
        mqtt_client.current_callback = self.handle_current_update
        self.start_logging_timer()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(15)

        # Top controls row
        top_row = QHBoxLayout()
        
        title_label = QLabel("Live Monitoring")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_row.addWidget(title_label)
        
        top_row.addStretch()

        # View mode toggle buttons
        view_group = QButtonGroup(self)
        self.live_btn = QPushButton("Live View")
        self.live_btn.setCheckable(True)
        self.live_btn.setChecked(True)
        self.live_btn.setFixedSize(100, 35)
        self.live_btn.clicked.connect(lambda: self.switch_view("live"))
        
        self.graph_btn = QPushButton("Graph View")
        self.graph_btn.setCheckable(True)
        self.graph_btn.setFixedSize(100, 35)
        self.graph_btn.clicked.connect(lambda: self.switch_view("graph"))
        
        view_group.addButton(self.live_btn)
        view_group.addButton(self.graph_btn)
        
        top_row.addWidget(self.live_btn)
        top_row.addWidget(self.graph_btn)
        
        main_layout.addLayout(top_row)

        # Container for switchable content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create live view (dials)
        self.live_view = self.create_live_view()
        self.content_layout.addWidget(self.live_view)
        
        # Create graph view (initially hidden)
        self.graph_view = self.create_graph_view()
        self.graph_view.hide()
        self.content_layout.addWidget(self.graph_view)
        
        main_layout.addWidget(self.content_widget)

    def create_live_view(self):
        """Create the live data view with dials"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setSpacing(10)

        # Dial titles
        dial_titles = QHBoxLayout()
        for name in ["Fan", "Light", "Total"]:
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 12px; font-weight: bold;")
            dial_titles.addWidget(label)
        layout.addLayout(dial_titles)

        # Dials
        self.fan_dial = DialGauge("primary1")
        self.light_dial = DialGauge("primary2")
        self.total_dial = DialGauge("accent")

        dial_row = QHBoxLayout()
        dial_row.addWidget(self.fan_dial)
        dial_row.addWidget(self.light_dial)
        dial_row.addWidget(self.total_dial)
        layout.addLayout(dial_row)

        return view

    def create_graph_view(self):
        """Create the graph view for historical data"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setSpacing(10)

        # Graph controls
        controls = QHBoxLayout()
        controls.addStretch()

        # Time range dropdown
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Last 7 days", "Last 10 days", "Last 30 days", "Last 60 days"])
        self.time_combo.setCurrentText("Last 30 days")
        self.time_combo.currentIndexChanged.connect(self.update_graph_data)
        controls.addWidget(self.time_combo)

        # Data type dropdown
        self.data_combo = QComboBox()
        self.data_combo.addItems(["FAN", "LIGHT", "LIGHT+FAN", "LIGHT,FAN"])
        self.data_combo.setCurrentText("LIGHT,FAN")
        self.data_combo.currentIndexChanged.connect(self.update_graph_data)
        controls.addWidget(self.data_combo)

        layout.addLayout(controls)

        # Graph widget
        self.fan_data, self.light_data = self.load_log_data(30)
        self.graph_widget = GraphWidget("Current vs Day", self.fan_data, self.light_data)
        self.graph_widget.setMinimumHeight(300)
        layout.addWidget(self.graph_widget)

        return view

    def switch_view(self, mode):
        """Switch between live view and graph view"""
        self.view_mode = mode
        if mode == "live":
            self.graph_view.hide()
            self.live_view.show()
        else:
            self.live_view.hide()
            self.graph_view.show()
            self.update_graph_data()

    def load_initial_data(self):
        """Load last known values on startup"""
        log_file = "current_log.txt"
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if line.strip():
                            parts = line.split(" fan energy - ")
                            if len(parts) >= 2:
                                self.fan_value = float(parts[1].split(" - ")[0].strip())
                                self.light_value = float(parts[1].split(" - ")[2].strip())
                                break
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        self.fan_dial.setValue(self.fan_value)
        self.light_dial.setValue(self.light_value)
        self.total_dial.setValue(self.fan_value + self.light_value)

    def handle_current_update(self, data):
        """Handle incoming MQTT current data"""
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
        """Start periodic logging"""
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.log_current_reading)
        self.log_timer.start(60000)  # Every minute

    def log_current_reading(self):
        """Log current readings to file"""
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

    def load_log_data(self, days):
        """Load historical data from log file"""
        today = datetime.datetime.now()
        fan_data = []
        light_data = []
        log_file = "current_log.txt"
        date_values = {}

        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip():
                            try:
                                parts = line.split(" fan energy - ")
                                if len(parts) < 2:
                                    continue
                                date = parts[0].strip()
                                values = parts[1].split(" - ")
                                fan_value = float(values[0].strip())
                                light_value = float(values[2].strip())
                                date_values[date] = (fan_value, light_value)
                            except (IndexError, ValueError) as e:
                                print(f"Error parsing log line: {line.strip()}, {e}")
            except Exception as e:
                print(f"Error reading log file: {e}")

        for i in range(days - 1, -1, -1):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            fan_value, light_value = date_values.get(date, (0.0, 0.0))
            fan_data.append(fan_value)
            light_data.append(light_value)

        return fan_data, light_data

    def update_graph_data(self):
        """Update graph with new data based on controls"""
        selection = self.time_combo.currentText()
        if "7" in selection:
            count = 7
        elif "10" in selection:
            count = 10
        elif "30" in selection:
            count = 30
        else:
            count = 60
        
        self.fan_data, self.light_data = self.load_log_data(count)
        plot_type = self.data_combo.currentText()
        self.graph_widget.update_data(self.fan_data, self.light_data, plot_type)

    def update_graph(self):
        """Update graph when theme changes"""
        if hasattr(self, 'graph_widget'):
            self.update_graph_data()