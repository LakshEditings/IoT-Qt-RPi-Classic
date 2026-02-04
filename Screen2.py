from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                                QLabel, QPushButton, QButtonGroup, QFrame)
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from themes import theme_manager
from mqtt_client import mqtt_client
import datetime
import os


class DigitalDisplay(QFrame):
    """Digital display for showing current values with full precision"""
    def __init__(self, label, icon, color="#00FF66"):
        super().__init__()
        self.label = label
        self.icon = icon
        self.color = color
        self._value = 0.0
        self.setup_ui()

    def setup_ui(self):
        theme = theme_manager.get_theme()
        
        # Card styling
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 45, 255),
                    stop:1 rgba(20, 20, 35, 255));
                border: 2px solid rgba(60, 60, 80, 255);
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        # Icon and label
        header = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet("background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(self.label)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_label.setStyleSheet(f"background: transparent; color: {self.color};")
        header.addWidget(title_label)
        
        header.addStretch()
        layout.addLayout(header)

        # Digital value display
        self.value_label = QLabel("0.000000")
        self.value_label.setFont(QFont("Courier New", 32, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            background-color: rgba(10, 10, 20, 200);
            color: {self.color};
            border: 1px solid rgba(80, 80, 100, 100);
            border-radius: 10px;
            padding: 15px;
        """)
        layout.addWidget(self.value_label, 1)

        # Unit label
        unit_label = QLabel("Amps (A)")
        unit_label.setFont(QFont("Segoe UI", 10))
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("background: transparent; color: #888;")
        layout.addWidget(unit_label)

    @Slot(float)
    def setValue(self, val):
        self._value = val
        # Show with 6 decimal places to match ESP32 precision
        self.value_label.setText(f"{val:.6f}")
        self.update()

    def value(self):
        return self._value


class GraphWidget(QWidget):
    """Graph widget for historical data visualization"""
    def __init__(self, title, light_data, fan_data, plug_data):
        super().__init__()
        self.title = title
        self.light_data = light_data
        self.fan_data = fan_data
        self.plug_data = plug_data
        self.plot_type = "ALL"
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

        days = range(1, len(self.light_data) + 1)
        bar_width = 0.25

        if self.plot_type == "LIGHT":
            ax.bar(days, self.light_data, width=bar_width * 2, color="#00FF66", label='Light')
        elif self.plot_type == "FAN":
            ax.bar(days, self.fan_data, width=bar_width * 2, color="#0078D7", label='Fan')
        elif self.plot_type == "PLUG":
            ax.bar(days, self.plug_data, width=bar_width * 2, color="#FFB900", label='Plug')
        elif self.plot_type == "TOTAL":
            total_data = [l + f + p for l, f, p in zip(self.light_data, self.fan_data, self.plug_data)]
            ax.bar(days, total_data, width=bar_width * 2, color="#FF6B35", label='Total')
        else:  # ALL (grouped bars)
            days = list(days)
            ax.bar([d - bar_width for d in days], self.light_data, width=bar_width, 
                   color="#00FF66", label='Light')
            ax.bar(days, self.fan_data, width=bar_width, 
                   color="#0078D7", label='Fan')
            ax.bar([d + bar_width for d in days], self.plug_data, width=bar_width, 
                   color="#FFB900", label='Plug')

        ax.set_title(self.title, color=theme["secondary3"], fontweight='bold', fontsize=10)
        ax.set_ylabel("Current (Amps)", color=theme["secondary3"], fontsize=8)
        ax.set_xlabel("Day", color=theme["secondary3"], fontsize=8)
        ax.tick_params(colors=theme["secondary3"], labelsize=6)
        ax.grid(True, linestyle="--", alpha=0.5, color=theme["secondary3"])
        ax.legend()

        ax.autoscale(enable=True, axis='y', tight=False)
        ax.margins(x=0.05)

        ax.set_xticks(range(1, len(self.light_data) + 1))
        ax.set_xticklabels(range(1, len(self.light_data) + 1))

        self.canvas.draw()

    def update_data(self, light_data, fan_data, plug_data, plot_type):
        self.light_data = light_data
        self.fan_data = fan_data
        self.plug_data = plug_data
        self.plot_type = plot_type
        self.plot()


class Screen2(QWidget):
    """Live energy monitoring screen with digital displays"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.light_value = 0.0  # L1 current
        self.fan_value = 0.0    # L2 current
        self.plug_value = 0.0   # Calculated from L1
        self.view_mode = "live"
        self.setup_ui()
        self.load_initial_data()
        mqtt_client.energy_callback = self.handle_energy_update
        self.start_logging_timer()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)

        # Top controls
        top_row = QHBoxLayout()
        
        title_label = QLabel("⚡ ESP32 Current Monitor")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_row.addWidget(title_label)
        
        top_row.addStretch()

        # View toggle buttons
        view_group = QButtonGroup(self)
        self.live_btn = QPushButton("📊 Live View")
        self.live_btn.setCheckable(True)
        self.live_btn.setChecked(True)
        self.live_btn.setFixedSize(110, 32)
        self.live_btn.clicked.connect(lambda: self.switch_view("live"))
        
        self.graph_btn = QPushButton("📈 Graph View")
        self.graph_btn.setCheckable(True)
        self.graph_btn.setFixedSize(110, 32)
        self.graph_btn.clicked.connect(lambda: self.switch_view("graph"))
        
        view_group.addButton(self.live_btn)
        view_group.addButton(self.graph_btn)
        
        top_row.addWidget(self.live_btn)
        top_row.addWidget(self.graph_btn)
        
        main_layout.addLayout(top_row)

        # Switchable content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.live_view = self.create_live_view()
        self.content_layout.addWidget(self.live_view)
        
        self.graph_view = self.create_graph_view()
        self.graph_view.hide()
        self.content_layout.addWidget(self.graph_view)
        
        main_layout.addWidget(self.content_widget)

    def create_live_view(self):
        """Create digital display view"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setSpacing(10)

        # First row: Light and Fan
        row1 = QHBoxLayout()
        self.light_display = DigitalDisplay("Light", "💡", "#00FF66")
        self.fan_display = DigitalDisplay("Fan", "🌀", "#0078D7")
        row1.addWidget(self.light_display)
        row1.addWidget(self.fan_display)
        layout.addLayout(row1)

        # Second row: Plug and Total
        row2 = QHBoxLayout()
        self.plug_display = DigitalDisplay("Plug", "🔌", "#FFB900")
        self.total_display = DigitalDisplay("TOTAL", "⚡", "#FF6B35")
        row2.addWidget(self.plug_display)
        row2.addWidget(self.total_display)
        layout.addLayout(row2)

        # ESP32 status indicator
        status_label = QLabel("📡 Waiting for ESP32 data on topic: home/light/energy")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            background-color: rgba(40, 40, 50, 200);
            border-radius: 8px;
            padding: 10px;
            color: #888;
            font-size: 10px;
        """)
        layout.addWidget(status_label)

        return view

    def create_graph_view(self):
        """Create graph view"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setSpacing(10)

        # Graph controls
        controls = QHBoxLayout()
        controls.addStretch()

        self.time_combo = QComboBox()
        self.time_combo.addItems(["Last 7 days", "Last 10 days", "Last 30 days", "Last 60 days"])
        self.time_combo.setCurrentText("Last 30 days")
        self.time_combo.currentIndexChanged.connect(self.update_graph_data)
        controls.addWidget(self.time_combo)

        self.data_combo = QComboBox()
        self.data_combo.addItems(["LIGHT", "FAN", "PLUG", "TOTAL", "ALL"])
        self.data_combo.setCurrentText("ALL")
        self.data_combo.currentIndexChanged.connect(self.update_graph_data)
        controls.addWidget(self.data_combo)

        layout.addLayout(controls)

        # Graph
        self.light_data, self.fan_data, self.plug_data = self.load_log_data(30)
        self.graph_widget = GraphWidget("Energy vs Day", self.light_data, self.fan_data, self.plug_data)
        self.graph_widget.setMinimumHeight(280)
        layout.addWidget(self.graph_widget)

        return view

    def switch_view(self, mode):
        self.view_mode = mode
        if mode == "live":
            self.graph_view.hide()
            self.live_view.show()
        else:
            self.live_view.hide()
            self.graph_view.show()
            self.update_graph_data()

    def load_initial_data(self):
        """Load last known values"""
        log_file = "energy_log.txt"
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if line.strip() and "light:" in line:
                            parts = line.split("light:")[1].split("fan:") 
                            self.light_value = float(parts[0].strip().split()[0])
                            parts2 = parts[1].split("plug:")
                            self.fan_value = float(parts2[0].strip().split()[0])
                            self.plug_value = float(parts2[1].strip().split()[0])
                            break
            except Exception as e:
                print(f"Error reading log: {e}")
        
        self.light_display.setValue(self.light_value)
        self.fan_display.setValue(self.fan_value)
        self.plug_display.setValue(self.plug_value)
        self.total_display.setValue(self.light_value + self.fan_value + self.plug_value)

    def handle_energy_update(self, data):
        """Handle incoming MQTT energy data from ESP32
        Expected format: {"L1":{"current":X,"power":Y,"energy":Z}, "L2":{...}}
        """
        try:
            # L1 = sensor1 (Lights + Plugs combined on that circuit)
            # L2 = sensor2 (Fans on that circuit)
            l1_current = float(data.get("L1", {}).get("current", 0.0))
            l2_current = float(data.get("L2", {}).get("current", 0.0))
            
            # Direct mapping from ESP32 dual sensors:
            # L1 (sensor1) → Powers Lights + Plugs
            # L2 (sensor2) → Powers Fans
            self.light_value = l1_current * 0.6  # 60% of L1 is lights
            self.plug_value = l1_current * 0.4   # 40% of L1 is plugs
            self.fan_value = l2_current
            
            total = l1_current + l2_current
            
            print(f"[ESP32 SENSORS] L1(Light+Plug):{l1_current:.6f}A → Light:{self.light_value:.6f}A Plug:{self.plug_value:.6f}A | L2(Fan):{l2_current:.6f}A | Total:{total:.6f}A")
            
            QMetaObject.invokeMethod(self.light_display, "setValue", Qt.QueuedConnection, Q_ARG(float, self.light_value))
            QMetaObject.invokeMethod(self.fan_display, "setValue", Qt.QueuedConnection, Q_ARG(float, self.fan_value))
            QMetaObject.invokeMethod(self.plug_display, "setValue", Qt.QueuedConnection, Q_ARG(float, self.plug_value))
            QMetaObject.invokeMethod(self.total_display, "setValue", Qt.QueuedConnection, Q_ARG(float, total))
            
            self.log_energy_reading()
        except Exception as e:
            print(f"Error handling energy update: {e}")

    def start_logging_timer(self):
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.log_energy_reading)
        self.log_timer.start(60000)  # Every minute

    def log_energy_reading(self):
        """Log energy to file"""
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        log_file = "energy_log.txt"
        
        log_line = f"{date_str} light:{self.light_value:.6f} fan:{self.fan_value:.6f} plug:{self.plug_value:.6f} total:{self.light_value + self.fan_value + self.plug_value:.6f}\n"

        lines = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
            except:
                pass

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
            print(f"Error writing log: {e}")

    def load_log_data(self, days):
        """Load historical data"""
        today = datetime.datetime.now()
        light_data = []
        fan_data = []
        plug_data = []
        log_file = "energy_log.txt"
        date_values = {}

        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    for line in f.readlines():
                        if line.strip() and "light:" in line:
                            try:
                                parts = line.split()
                                date = parts[0]
                                light = float(parts[1].split(":")[1])
                                fan = float(parts[2].split(":")[1])
                                plug = float(parts[3].split(":")[1])
                                date_values[date] = (light, fan, plug)
                            except:
                                pass
            except:
                pass

        for i in range(days - 1, -1, -1):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            light, fan, plug = date_values.get(date, (0.0, 0.0, 0.0))
            light_data.append(light)
            fan_data.append(fan)
            plug_data.append(plug)

        return light_data, fan_data, plug_data

    def update_graph_data(self):
        """Update graph"""
        selection = self.time_combo.currentText()
        if "7" in selection:
            count = 7
        elif "10" in selection:
            count = 10
        elif "30" in selection:
            count = 30
        else:
            count = 60
        
        self.light_data, self.fan_data, self.plug_data = self.load_log_data(count)
        plot_type = self.data_combo.currentText()
        self.graph_widget.update_data(self.light_data, self.fan_data, self.plug_data, plot_type)

    def update_graph(self):
        """Update graph on theme change"""
        if hasattr(self, 'graph_widget'):
            self.update_graph_data()