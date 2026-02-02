import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from themes import theme_manager
import os
import datetime

class GraphWidget(QWidget):
    def __init__(self, title, fan_data, light_data):
        super().__init__()
        self.title = title
        self.fan_data = fan_data
        self.light_data = light_data
        self.plot_type = "LIGHT,FAN"  # Default plot type
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
            ax.bar([d - bar_width/2 for d in days], self.fan_data, width=bar_width, color=theme["primary1"], label='Fan Current')
            ax.bar([d + bar_width/2 for d in days], self.light_data, width=bar_width, color=theme["primary2"], label='Light Current')

        ax.set_title(self.title, color=theme["secondary3"], fontweight='bold', fontsize=10)
        ax.set_ylabel("Current (Amps)", color=theme["secondary3"], fontsize=8)
        ax.set_xlabel("Day", color=theme["secondary3"], fontsize=8)
        ax.tick_params(colors=theme["secondary3"], labelsize=6)
        ax.grid(True, linestyle="--", alpha=0.5, color=theme["secondary3"])
        ax.legend()

        # Enable autoscaling for Y-axis
        ax.autoscale(enable=True, axis='y', tight=False)
        # Enable autoscaling for X-axis with slight padding
        ax.margins(x=0.05)  # 5% margin on X-axis for better visibility
        ax.autoscale(enable=True, axis='x', tight=False)

        # Ensure integer ticks on X-axis
        ax.set_xticks(range(1, len(self.fan_data) + 1))
        ax.set_xticklabels(range(1, len(self.fan_data) + 1))

        self.canvas.draw()

    def update_data(self, fan_data, light_data, plot_type):
        self.fan_data = fan_data
        self.light_data = light_data
        self.plot_type = plot_type
        self.plot()

class Screen2(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        title = QLabel("Fan and Light Current vs Day")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        top_controls = QHBoxLayout()
        top_controls.addStretch()

        # Time range dropdown
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Last 7 days", "Last 10 days", "Last 30 days", "Last 60 days"])
        self.time_combo.setCurrentText("Last 30 days")
        self.time_combo.currentIndexChanged.connect(self.update_graph)
        top_controls.addWidget(self.time_combo)

        # Data type dropdown
        self.data_combo = QComboBox()
        self.data_combo.addItems(["FAN", "LIGHT", "LIGHT+FAN", "LIGHT,FAN"])
        self.data_combo.setCurrentText("LIGHT,FAN")
        self.data_combo.currentIndexChanged.connect(self.update_graph)
        top_controls.addWidget(self.data_combo)

        self.fan_data, self.light_data = self.load_log_data(30)
        self.graph_widget = GraphWidget("Fan and Light Current vs Day", self.fan_data, self.light_data)
        self.graph_widget.setMinimumHeight(300)

        layout.addLayout(top_controls)
        layout.addWidget(self.graph_widget)

    def load_log_data(self, days):
        today = datetime.datetime.now()
        fan_data = []
        light_data = []
        log_file = "current_log.txt"
        date_values = {}

        # Read log file
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

        # Collect data for the last 'days' days
        for i in range(days - 1, -1, -1):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            fan_value, light_value = date_values.get(date, (0.0, 0.0))
            fan_data.append(fan_value)
            light_data.append(light_value)

        return fan_data, light_data

    def update_graph(self):
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