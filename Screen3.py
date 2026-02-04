from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QComboBox, QPushButton, QTimeEdit, QGridLayout,
                                QGroupBox, QCheckBox, QScrollArea, QFrame, QSpinBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QTime, QTimer, QDate, QDateTime
from PySide6.QtGui import QFont
from themes import theme_manager, THEMES
from mqtt_client import mqtt_client
import json
import os
import datetime


class TimerWidget(QFrame):
    """Modern timer control widget"""
    def __init__(self, appliance_name, appliance_id, parent_screen):
        super().__init__()
        self.appliance_name = appliance_name
        self.appliance_id = appliance_id
        self.parent_screen = parent_screen
        self.timer_enabled = False
        self.timer_obj = None
        self.is_one_time = False
        self.setup_ui()
        self.update_next_action()

    def setup_ui(self):
        theme = theme_manager.get_theme()
        
        # Card styling with shadow effect
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme["secondary2"]}, 
                    stop:1 rgba(20, 20, 30, 255));
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("⏰ Set Automatic Schedule")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet(f"color: {theme['primary1']}; background: transparent;")
        main_layout.addWidget(header)

        # Timer Controls Section
        controls_card = QFrame()
        controls_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 50, 200);
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setSpacing(12)

        # ON Time Picker
        on_time_layout = QHBoxLayout()
        on_icon = QLabel("🌅")
        on_icon.setFont(QFont("Segoe UI", 20))
        on_icon.setStyleSheet("background: transparent;")
        on_time_layout.addWidget(on_icon)
        
        on_label = QLabel("Turn ON Time:")
        on_label.setFont(QFont("Segoe UI", 11))
        on_label.setStyleSheet("background: transparent;")
        on_time_layout.addWidget(on_label)
        
        self.on_time = QTimeEdit()
        self.on_time.setDisplayFormat("hh:mm AP")
        self.on_time.setTime(QTime(18, 0))
        self.on_time.setFixedHeight(40)
        self.on_time.setStyleSheet(f"""
            QTimeEdit {{
                background-color: {theme["secondary1"]};
                border: 2px solid {theme["primary1"]};
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
                color: white;
            }}
        """)
        self.on_time.timeChanged.connect(self.update_next_action)
        on_time_layout.addWidget(self.on_time)
        on_time_layout.addStretch()
        controls_layout.addLayout(on_time_layout)

        # OFF Time Picker
        off_time_layout = QHBoxLayout()
        off_icon = QLabel("🌙")
        off_icon.setFont(QFont("Segoe UI", 20))
        off_icon.setStyleSheet("background: transparent;")
        off_time_layout.addWidget(off_icon)
        
        off_label = QLabel("Turn OFF Time:")
        off_label.setFont(QFont("Segoe UI", 11))
        off_label.setStyleSheet("background: transparent;")
        off_time_layout.addWidget(off_label)
        
        self.off_time = QTimeEdit()
        self.off_time.setDisplayFormat("hh:mm AP")
        self.off_time.setTime(QTime(22, 0))
        self.off_time.setFixedHeight(40)
        self.off_time.setStyleSheet(f"""
            QTimeEdit {{
                background-color: {theme["secondary1"]};
                border: 2px solid {theme["primary2"]};
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
                color: white;
            }}
        """)
        self.off_time.timeChanged.connect(self.update_next_action)
        off_time_layout.addWidget(self.off_time)
        off_time_layout.addStretch()
        controls_layout.addLayout(off_time_layout)

        main_layout.addWidget(controls_card)

        # Schedule Mode Options
        mode_card = QFrame()
        mode_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 50, 200);
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setSpacing(10)

        mode_title = QLabel("🔄 Schedule Mode")
        mode_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        mode_title.setStyleSheet("background: transparent;")
        mode_layout.addWidget(mode_title)

        # Radio buttons for mode
        self.mode_group = QButtonGroup()
        
        self.repeat_daily = QRadioButton("♻️  Repeat Daily")
        self.repeat_daily.setChecked(True)
        self.repeat_daily.setFont(QFont("Segoe UI", 10))
        self.repeat_daily.setStyleSheet("""
            QRadioButton { 
                background: transparent; 
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.repeat_daily.toggled.connect(self.mode_changed)
        self.mode_group.addButton(self.repeat_daily)
        mode_layout.addWidget(self.repeat_daily)

        self.one_time = QRadioButton("📅  One-Time Only")
        self.one_time.setFont(QFont("Segoe UI", 10))
        self.one_time.setStyleSheet("""
            QRadioButton { 
                background: transparent;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.one_time.toggled.connect(self.mode_changed)
        self.mode_group.addButton(self.one_time)
        mode_layout.addWidget(self.one_time)

        main_layout.addWidget(mode_card)

        # Advanced Options
        advanced_card = QFrame()
        advanced_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 50, 200);
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        advanced_layout = QVBoxLayout(advanced_card)
        advanced_layout.setSpacing(10)

        advanced_title = QLabel("⚙️ Advanced Options")
        advanced_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        advanced_title.setStyleSheet("background: transparent;")
        advanced_layout.addWidget(advanced_title)

        # Duration Mode
        duration_layout = QHBoxLayout()
        duration_label = QLabel("⏱️  Turn OFF after:")
        duration_label.setFont(QFont("Segoe UI", 10))
        duration_label.setStyleSheet("background: transparent;")
        duration_layout.addWidget(duration_label)
        
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(0, 240)
        self.duration_spinbox.setValue(0)
        self.duration_spinbox.setSuffix(" minutes")
        self.duration_spinbox.setFixedHeight(35)
        self.duration_spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {theme["secondary1"]};
                border: 1px solid {theme["primary1"]};
                border-radius: 5px;
                padding: 3px;
                color: white;
            }}
        """)
        duration_layout.addWidget(self.duration_spinbox)
        duration_layout.addStretch()
        advanced_layout.addLayout(duration_layout)

        # Power Saving Mode
        power_layout = QHBoxLayout()
        power_icon = QLabel("🔋")
        power_icon.setFont(QFont("Segoe UI", 16))
        power_icon.setStyleSheet("background: transparent;")
        power_layout.addWidget(power_icon)
        
        self.power_saving = QCheckBox("Power Saving Mode")
        self.power_saving.setFont(QFont("Segoe UI", 10))
        self.power_saving.setStyleSheet("""
            QCheckBox { 
                background: transparent;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        power_layout.addWidget(self.power_saving)
        power_layout.addStretch()
        advanced_layout.addLayout(power_layout)

        main_layout.addWidget(advanced_card)

        # ═══════════════════════════════════════════════
        # 🚶 MOTION SENSOR
        # ═══════════════════════════════════════════════
        motion_card = QFrame()
        motion_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(60, 40, 80, 150);
                border: 2px solid rgba(150, 100, 200, 80);
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        motion_layout = QVBoxLayout(motion_card)
        motion_layout.setSpacing(8)

        # Motion Sensor Header
        motion_header = QLabel("🚶 Motion Sensor Control")
        motion_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        motion_header.setStyleSheet(f"color: {theme['primary2']}; background: transparent;")
        motion_layout.addWidget(motion_header)

        motion_desc = QLabel("When enabled, device turns ON for 5 minutes when motion is detected")
        motion_desc.setFont(QFont("Segoe UI", 9))
        motion_desc.setStyleSheet("color: #aaa; background: transparent;")
        motion_desc.setWordWrap(True)
        motion_layout.addWidget(motion_desc)

        # Enable Motion Sensor Checkbox
        self.motion_enabled = QCheckBox("✓ Enable Motion Sensor")
        self.motion_enabled.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.motion_enabled.setStyleSheet(f"""
            QCheckBox {{
                background: transparent;
                color: {theme['primary2']};
                padding: 5px;
            }}
        """)
        self.motion_enabled.setChecked(False)
        motion_layout.addWidget(self.motion_enabled)

        # Motion Status Label (shows when motion detected)
        self.motion_status_label = QLabel("")
        self.motion_status_label.setFont(QFont("Segoe UI", 9))
        self.motion_status_label.setStyleSheet("""
            background-color: rgba(255, 140, 0, 30);
            border-radius: 6px;
            padding: 8px;
            color: orange;
        """)
        self.motion_status_label.hide()  # Hidden by default
        motion_layout.addWidget(self.motion_status_label)

        main_layout.addWidget(motion_card)

        # Next Action Display
        self.next_action_label = QLabel()
        self.next_action_label.setFont(QFont("Segoe UI", 10))
        self.next_action_label.setStyleSheet(f"""
            background-color: rgba(0, 120, 215, 30);
            border-radius: 8px;
            padding: 10px;
            color: {theme['primary1']};
        """)
        self.next_action_label.setWordWrap(True)
        main_layout.addWidget(self.next_action_label)

        # Countdown Display
        self.countdown_label = QLabel()
        self.countdown_label.setFont(QFont("Segoe UI", 9))
        self.countdown_label.setStyleSheet("""
            background: transparent;
            color: #888;
        """)
        main_layout.addWidget(self.countdown_label)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = QPushButton("💾 Save Timer")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 200, 50, 255), 
                    stop:1 rgba(30, 160, 30, 255));
                border: none;
                border-radius: 10px;
                color: white;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 220, 60, 255), 
                    stop:1 rgba(40, 180, 40, 255));
            }}
            QPushButton:pressed {{
                background: rgba(30, 140, 30, 255);
            }}
        """)
        self.save_btn.clicked.connect(self.save_timer)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setFont(QFont("Segoe UI", 11))
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(100, 100, 110, 200);
                border: 1px solid rgba(150, 150, 160, 100);
                border-radius: 10px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: rgba(120, 120, 130, 220);
            }}
            QPushButton:pressed {{
                background-color: rgba(80, 80, 90, 200);
            }}
        """)
        self.cancel_btn.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(button_layout)

        # Start countdown update timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # Update every second

    def mode_changed(self):
        """Handle schedule mode change"""
        self.is_one_time = self.one_time.isChecked()
        self.update_next_action()

    def update_next_action(self):
        """Update the next scheduled action display"""
        if not self.timer_enabled:
            self.next_action_label.setText("📢 Timer is inactive. Click 'Save Timer' to activate.")
            self.next_action_label.setStyleSheet("""
                background-color: rgba(100, 100, 110, 100);
                border-radius: 8px;
                padding: 10px;
                color: #888;
            """)
            return

        current_time = QTime.currentTime()
        on_time = self.on_time.time()
        off_time = self.off_time.time()

        # Determine next action
        if current_time < on_time:
            next_action = "ON"
            next_time = on_time
        elif current_time < off_time:
            next_action = "OFF"
            next_time = off_time
        else:
            next_action = "ON"
            next_time = on_time

        mode_text = "today" if not self.is_one_time else "once"
        self.next_action_label.setText(
            f"📢 Next Scheduled Action: {next_action} at {next_time.toString('hh:mm AP')} ({mode_text})"
        )
        
        theme = theme_manager.get_theme()
        self.next_action_label.setStyleSheet(f"""
            background-color: rgba(0, 120, 215, 30);
            border-radius: 8px;
            padding: 10px;
            color: {theme['primary1']};
        """)

    def update_countdown(self):
        """Update countdown timer display"""
        if not self.timer_enabled:
            self.countdown_label.setText("")
            return

        current_time = QTime.currentTime()
        on_time = self.on_time.time()
        off_time = self.off_time.time()

        # Calculate seconds until next action
        if current_time < on_time:
            target_time = on_time
            action = "ON"
        elif current_time < off_time:
            target_time = off_time
            action = "OFF"
        else:
            target_time = on_time
            action = "ON"

        seconds_until = current_time.secsTo(target_time)
        if seconds_until < 0:
            seconds_until += 86400  # Add 24 hours

        hours = seconds_until // 3600
        minutes = (seconds_until % 3600) // 60
        seconds = seconds_until % 60

        if hours > 0:
            countdown_text = f"⏳ Countdown: {hours}h {minutes}m {seconds}s until {action}"
        elif minutes > 0:
            countdown_text = f"⏳ Countdown: {minutes}m {seconds}s until {action}"
        else:
            countdown_text = f"⏳ Countdown: {seconds}s until {action}"

        self.countdown_label.setText(countdown_text)

    def save_timer(self):
        """Save and activate timer"""
        self.timer_enabled = True
        self.start_timer()
        self.update_next_action()
        self.parent_screen.save_timer_settings()
        print(f"✓ Timer activated for {self.appliance_name}")

    def reset_timer(self):
        """Reset and deactivate timer"""
        self.timer_enabled = False
        self.stop_timer()
        self.on_time.setTime(QTime(18, 0))
        self.off_time.setTime(QTime(22, 0))
        self.duration_spinbox.setValue(0)
        self.power_saving.setChecked(False)
        self.repeat_daily.setChecked(True)
        self.update_next_action()
        self.countdown_label.setText("")
        print(f"✓ Timer reset for {self.appliance_name}")

    def start_timer(self):
        """Start the timer checking loop"""
        if not self.timer_obj:
            self.timer_obj = QTimer(self)
            self.timer_obj.timeout.connect(self.check_timer)
            self.timer_obj.start(60000)  # Check every minute
        self.check_timer()

    def stop_timer(self):
        """Stop the timer"""
        if self.timer_obj:
            self.timer_obj.stop()
            self.timer_obj = None

    def check_timer(self):
        """Check if it's time to execute the timer action"""
        if not self.timer_enabled:
            return

        current_time = QTime.currentTime()
        on_time = self.on_time.time()
        off_time = self.off_time.time()

        # Check ON time
        if current_time.hour() == on_time.hour() and current_time.minute() == on_time.minute():
            self.execute_action("ON")
            if self.is_one_time:
                self.timer_enabled = False
                self.update_next_action()

        # Check OFF time
        elif current_time.hour() == off_time.hour() and current_time.minute() == off_time.minute():
            self.execute_action("OFF")
            if self.is_one_time:
                self.timer_enabled = False
                self.update_next_action()

    def execute_action(self, state):
        """Execute timer action (turn on/off appliance)"""
        mqtt_mapping = {
            "living_light_1": mqtt_client.send_light1,
            "living_light_2": mqtt_client.send_light2,
            "living_plug_1": mqtt_client.send_light3,
            "living_plug_2": mqtt_client.send_light4,
        }

        if self.appliance_id in mqtt_mapping:
            mqtt_mapping[self.appliance_id](state)
            print(f"[TIMER] {self.appliance_name} turned {state}")

    def get_settings(self):
        """Get timer settings as dictionary"""
        return {
            "enabled": self.timer_enabled,
            "on_time": self.on_time.time().toString("hh:mm"),
            "off_time": self.off_time.time().toString("hh:mm"),
            "is_one_time": self.is_one_time,
            "duration_minutes": self.duration_spinbox.value(),
            "power_saving": self.power_saving.isChecked(),
            # Sleep timer settings
            "sleep_enabled": self.sleep_enabled.isChecked(),
            "sleep_start": self.sleep_start.time().toString("hh:mm"),
            "sleep_end": self.sleep_end.time().toString("hh:mm"),
            "sleep_duration": self.sleep_duration.value()
        }

    def load_settings(self, settings):
        """Load timer settings from dictionary"""
        self.timer_enabled = settings.get("enabled", False)
        
        if "on_time" in settings:
            self.on_time.setTime(QTime.fromString(settings["on_time"], "hh:mm"))
        
        if "off_time" in settings:
            self.off_time.setTime(QTime.fromString(settings["off_time"], "hh:mm"))
        
        if settings.get("is_one_time"):
            self.one_time.setChecked(True)
        else:
            self.repeat_daily.setChecked(True)
        
        if "duration_minutes" in settings:
            self.duration_spinbox.setValue(settings["duration_minutes"])
        
        if "power_saving" in settings:
            self.power_saving.setChecked(settings["power_saving"])
        
        # Load sleep timer settings
        if "sleep_enabled" in settings:
            self.sleep_enabled.setChecked(settings["sleep_enabled"])
        
        if "sleep_start" in settings:
            self.sleep_start.setTime(QTime.fromString(settings["sleep_start"], "hh:mm"))
        
        if "sleep_end" in settings:
            self.sleep_end.setTime(QTime.fromString(settings["sleep_end"], "hh:mm"))
        
        if "sleep_duration" in settings:
            self.sleep_duration.setValue(settings["sleep_duration"])
        
        if self.timer_enabled:
            self.start_timer()
        
        self.update_next_action()


class Screen3(QWidget):
    """Settings screen with cascading room/appliance selectors and timer"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.timer_widgets = {}
        self.current_timer = None
        
        # Room and appliance definitions
        self.rooms = {
            "Living Room": {
                "enabled": True,
                "appliances": [
                    {"name": "Light 1", "id": "living_light_1", "enabled": True},
                    {"name": "Light 2", "id": "living_light_2", "enabled": True},
                    {"name": "Light 3", "id": "living_light_3", "enabled": False},
                    {"name": "Light 4", "id": "living_light_4", "enabled": False},
                    {"name": "Fan 1", "id": "living_fan_1", "enabled": False},
                    {"name": "Fan 2", "id": "living_fan_2", "enabled": False},
                    {"name": "Plug 1", "id": "living_plug_1", "enabled": True},
                    {"name": "Plug 2", "id": "living_plug_2", "enabled": True},
                ]
            },
            "Master Bed Room": {"enabled": False, "appliances": []},
            "Kids Room": {"enabled": False, "appliances": []},
            "Guest Room": {"enabled": False, "appliances": []},
            "Kitchen": {"enabled": False, "appliances": []},
        }
        
        self.setup_ui()
        self.load_timer_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("⚙️ Settings & Timer")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        main_layout.addWidget(title_label)

        # Theme Settings (compact)
        theme_layout = QHBoxLayout()
        theme_label = QLabel("🎨 Theme:")
        theme_label.setFont(QFont("Segoe UI", 11))
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Obsidian", "Titanium", "Neon", "Aurora"])
        self.theme_combo.setCurrentText(theme_manager.current_theme)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        self.theme_combo.setFixedWidth(130)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)

        # Room Selector
        room_layout = QHBoxLayout()
        room_icon = QLabel("🏠")
        room_icon.setFont(QFont("Segoe UI", 16))
        room_layout.addWidget(room_icon)
        
        room_label = QLabel("Select Room:")
        room_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        room_layout.addWidget(room_label)
        
        self.room_combo = QComboBox()
        self.room_combo.setFixedHeight(40)
        self.room_combo.setFont(QFont("Segoe UI", 10))
        for room_name, room_data in self.rooms.items():
            self.room_combo.addItem(room_name)
            # Disable non-Living Room options
            if not room_data["enabled"]:
                model = self.room_combo.model()
                item = model.item(self.room_combo.count() - 1)
                item.setEnabled(False)
        
        self.room_combo.currentIndexChanged.connect(self.room_changed)
        room_layout.addWidget(self.room_combo)
        room_layout.addStretch()
        main_layout.addLayout(room_layout)

        # Appliance Selector
        appliance_layout = QHBoxLayout()
        appliance_icon = QLabel("💡")
        appliance_icon.setFont(QFont("Segoe UI", 16))
        appliance_layout.addWidget(appliance_icon)
        
        appliance_label = QLabel("Select Appliance:")
        appliance_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        appliance_layout.addWidget(appliance_label)
        
        self.appliance_combo = QComboBox()
        self.appliance_combo.setFixedHeight(40)
        self.appliance_combo.setFont(QFont("Segoe UI", 10))
        self.appliance_combo.currentIndexChanged.connect(self.appliance_changed)
        appliance_layout.addWidget(self.appliance_combo)
        appliance_layout.addStretch()
        main_layout.addLayout(appliance_layout)

        # Timer Container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.timer_container = QWidget()
        self.timer_layout = QVBoxLayout(self.timer_container)
        self.timer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.timer_container)
        main_layout.addWidget(scroll)

        # Initialize first room
        self.room_changed()

    def room_changed(self):
        """Handle room selection change"""
        room_name = self.room_combo.currentText()
        room_data = self.rooms.get(room_name, {})
        
        # Update appliance dropdown
        self.appliance_combo.clear()
        
        if room_data.get("enabled"):
            for appliance in room_data.get("appliances", []):
                self.appliance_combo.addItem(appliance["name"])
                # Disable non-MQTT appliances
                if not appliance["enabled"]:
                    model = self.appliance_combo.model()
                    item = model.item(self.appliance_combo.count() - 1)
                    item.setEnabled(False)
        
        # Trigger appliance selection
        if self.appliance_combo.count() > 0:
            self.appliance_changed()

    def appliance_changed(self):
        """Handle appliance selection change"""
        room_name = self.room_combo.currentText()
        appliance_index = self.appliance_combo.currentIndex()
        
        room_data = self.rooms.get(room_name, {})
        appliances = room_data.get("appliances", [])
        
        if 0 <= appliance_index < len(appliances):
            appliance = appliances[appliance_index]
            
            if not appliance["enabled"]:
                # Show disabled message
                self.show_disabled_message()
                return
            
            appliance_id = appliance["id"]
            
            # Create timer widget if not exists
            if appliance_id not in self.timer_widgets:
                timer_widget = TimerWidget(
                    f"{room_name} - {appliance['name']}",
                    appliance_id,
                    self
                )
                self.timer_widgets[appliance_id] = timer_widget
            
            # Hide all timers
            for widget in self.timer_widgets.values():
                widget.hide()
            
            # Show selected timer
            if appliance_id in self.timer_widgets:
                # Clear layout
                while self.timer_layout.count():
                    item = self.timer_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                
                # Add selected timer
                self.timer_layout.addWidget(self.timer_widgets[appliance_id])
                self.timer_widgets[appliance_id].show()
                self.current_timer = self.timer_widgets[appliance_id]

    def show_disabled_message(self):
        """Show message for disabled appliances"""
        # Clear layout
        while self.timer_layout.count():
            item = self.timer_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Show message
        message = QLabel("🚫 This appliance is not connected to MQTT.\nTimer unavailable.")
        message.setAlignment(Qt.AlignCenter)
        message.setFont(QFont("Segoe UI", 12))
        message.setStyleSheet("""
            background-color: rgba(100, 100, 110, 100);
            border-radius: 10px;
            padding: 40px;
            color: #888;
        """)
        self.timer_layout.addWidget(message)

    def change_theme(self):
        """Change application theme"""
        theme_name = self.theme_combo.currentText()
        theme_manager.set_theme(theme_name)
        self.main_window.update_stylesheet()
        
        if hasattr(self.main_window, 'screen1'):
            self.main_window.screen1.update_theme()
        
        if hasattr(self.main_window, 'screen2'):
            if hasattr(self.main_window.screen2, 'fan_dial'):
                self.main_window.screen2.fan_dial.update()
                self.main_window.screen2.light_dial.update()
                self.main_window.screen2.total_dial.update()
        
        self.update()

    def save_timer_settings(self):
        """Save all timer settings"""
        settings = {}
        for appliance_id, widget in self.timer_widgets.items():
            settings[appliance_id] = widget.get_settings()
        
        try:
            with open("timer_settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            print("✓ Timer settings saved")
        except Exception as e:
            print(f"✗ Error saving: {e}")

    def load_timer_settings(self):
        """Load timer settings"""
        if os.path.exists("timer_settings.json"):
            try:
                with open("timer_settings.json", "r") as f:
                    settings = json.load(f)
                
                for appliance_id, widget in self.timer_widgets.items():
                    if appliance_id in settings:
                        widget.load_settings(settings[appliance_id])
                
                print("✓ Timer settings loaded")
            except Exception as e:
                print(f"✗ Error loading: {e}")

    def disable_timer_for_appliance(self, appliance_id):
        """Disable timer for an appliance when manual override occurs"""
        if appliance_id in self.timer_widgets:
            widget = self.timer_widgets[appliance_id]
            if widget.timer_enabled:
                # Disable the timer
                widget.timer_enabled = False
                widget.stop_timer()
                
                # Update UI indicators
                widget.status_indicator.setStyleSheet("""
                    background-color: rgba(200, 100, 50, 200);
                    border-radius: 8px;
                    padding: 8px;
                    color: white;
                    font-weight: bold;
                """)
                widget.status_indicator.setText("⚠️ TIMER DISABLED - Manual Control Active")
                
                # Save the disabled state
                self.save_timer_settings()
                
                print(f"⚠️ Timer disabled for {appliance_id} due to manual override")