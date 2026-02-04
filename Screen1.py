from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                                QPushButton, QLabel, QFrame, QStackedWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from themes import theme_manager
from mqtt_client import mqtt_client


class ApplianceCard(QFrame):
    """Individual appliance toggle card"""
    def __init__(self, name, icon, mqtt_method, parent=None):
        super().__init__(parent)
        self.name = name
        self.icon = icon
        self.mqtt_method = mqtt_method
        self.is_on = False
        self.icon_label = None
        self.name_label = None
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(170, 110)
        self.update_card_background()
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # Appliance name at top - with transparent background
        self.name_label = QLabel(self.name)
        self.name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("background: transparent; color: white;")
        layout.addWidget(self.name_label)

        # Icon in center - larger and clickable
        self.icon_label = QLabel(self.icon)
        self.icon_label.setFont(QFont("Segoe UI", 48))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        self.update_icon_color()
        layout.addWidget(self.icon_label, 1)

    def update_card_background(self):
        """Update card background based on state and connection"""
        if self.mqtt_method is None:
            # Grey for unconnected appliances
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(60, 60, 60, 255), 
                        stop:1 rgba(40, 40, 40, 255));
                    border: none;
                    border-radius: 15px;
                }}
            """)
        elif self.is_on:
            # Green when ON
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(50, 180, 50, 255), 
                        stop:1 rgba(30, 140, 30, 255));
                    border: none;
                    border-radius: 15px;
                }}
            """)
        else:
            # Red when OFF (but connected)
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(180, 50, 50, 255), 
                        stop:1 rgba(140, 30, 30, 255));
                    border: none;
                    border-radius: 15px;
                }}
            """)

    def update_icon_color(self):
        """Update icon color based on state"""
        if self.mqtt_method is None:
            # Grey icon for unconnected
            self.icon_label.setStyleSheet("""
                QLabel {
                    color: rgba(150, 150, 150, 255);
                    background: transparent;
                }
            """)
        elif self.is_on:
            # White icon when ON
            self.icon_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 255);
                    background: transparent;
                }
            """)
        else:
            # Light yellow/orange when OFF
            self.icon_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 220, 150, 255);
                    background: transparent;
                }
            """)

    def mousePressEvent(self, event):
        """Handle card click - toggle state"""
        # Only toggle if MQTT is connected
        if self.mqtt_method is None:
            return
            
        self.is_on = not self.is_on
        state = "ON" if self.is_on else "OFF"
        
        # Update visuals
        self.update_card_background()
        self.update_icon_color()
        
        # Send MQTT command
        self.mqtt_method(state)
        print(f"[MQTT] {self.name} - {state}")
        
        super().mousePressEvent(event)

    def update_theme(self):
        """Update card styling when theme changes"""
        self.update_card_background()
        self.update_icon_color()



class RoomCard(QFrame):
    """Room selection card"""
    def __init__(self, room_name, icon, callback, parent=None):
        super().__init__(parent)
        self.room_name = room_name
        self.icon = icon
        self.callback = callback
        self.setup_ui()

    def setup_ui(self):
        theme = theme_manager.get_theme()
        
        self.setFixedSize(170, 110)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 40, 255), 
                    stop:1 rgba(26, 26, 36, 255));
                border: none;
                border-radius: 15px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 50, 60, 255), 
                    stop:1 rgba(40, 40, 50, 255));
                border: none;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Room icon
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI", 42))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, 1)

        # Room name
        name_label = QLabel(self.room_name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

    def mousePressEvent(self, event):
        """Handle room card click"""
        self.callback(self.room_name)
        super().mousePressEvent(event)


class Screen1(QWidget):
    """Main control screen with room navigation"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.appliance_cards = []
        self.room_cards = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title with back button
        title_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedSize(80, 35)
        self.back_btn.clicked.connect(self.show_rooms)
        self.back_btn.hide()  # Hidden initially
        title_layout.addWidget(self.back_btn)
        
        title_layout.addStretch()
        
        self.title_label = QLabel("Smart Home Control")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # Spacer for symmetry
        spacer = QLabel("")
        spacer.setFixedSize(80, 35)
        title_layout.addWidget(spacer)
        
        main_layout.addLayout(title_layout)

        # Stacked widget for room selection and appliance views
        self.stack = QStackedWidget()
        
        # Page 0: Room selection
        self.rooms_page = self.create_rooms_page()
        self.stack.addWidget(self.rooms_page)
        
        # Page 1: Living Room appliances
        self.living_room_page = self.create_living_room_page()
        self.stack.addWidget(self.living_room_page)
        
        # Pages for other rooms (empty for now)
        for room_name in ["Master Bed Room", "Kids Room", "Guest Room", "Kitchen"]:
            empty_page = self.create_empty_room_page(room_name)
            self.stack.addWidget(empty_page)
        
        main_layout.addWidget(self.stack)

    def create_rooms_page(self):
        """Create the room selection page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        # Subtitle
        subtitle = QLabel("Select a Room")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {theme_manager.get_theme()['secondary3']};")
        layout.addWidget(subtitle)
        
        # Grid of room cards
        grid = QGridLayout()
        grid.setSpacing(15)
        
        rooms = [
            ("Living Room", "🏠", 0, 0),
            ("Master Bed Room", "🛏️", 0, 1),
            ("Kids Room", "🧸", 0, 2),
            ("Guest Room", "🚪", 1, 0),
            ("Kitchen", "🍳", 1, 1),
        ]
        
        for room_name, icon, row, col in rooms:
            card = RoomCard(room_name, icon, self.open_room)
            self.room_cards.append(card)
            grid.addWidget(card, row, col)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return page

    def create_living_room_page(self):
        """Create Living Room appliances page (2 Fans, 4 Lights, 2 Plugs)"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        
        # Room subtitle
        subtitle = QLabel("Living Room")
        subtitle.setFont(QFont("Segoe UI", 14, QFont.Bold))
        subtitle.setStyleSheet(f"color: {theme_manager.get_theme()['primary1']};")
        layout.addWidget(subtitle)
        
        # Grid of appliance cards (2 rows × 4 columns)
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Living Room: 4 Lights (row 1), 2 Fans + 2 Plugs (row 2)
        # MQTT mapping: Light1→Light1, Light2→Light2, Light3→Plug1, Light4→Plug2
        appliances = [
            # Row 1: 4 Lights
            ("Light 1", "💡", mqtt_client.send_light1, 0, 0),
            ("Light 2", "💡", mqtt_client.send_light2, 0, 1),
            ("Light 3", "💡", None, 0, 2),
            ("Light 4", "💡", None, 0, 3),
            # Row 2: 2 Fans, 2 Plugs
            ("Fan 1", "🌀", None, 1, 0),
            ("Fan 2", "🌀", None, 1, 1),
            ("Plug 1", "🔌", mqtt_client.send_light3, 1, 2),
            ("Plug 2", "🔌", mqtt_client.send_light4, 1, 3),
        ]
        
        for name, icon, mqtt_method, row, col in appliances:
            card = ApplianceCard(name, icon, mqtt_method)
            self.appliance_cards.append(card)
            grid.addWidget(card, row, col)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return page

    def create_empty_room_page(self, room_name):
        """Create placeholder page for other rooms"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        subtitle = QLabel(room_name)
        subtitle.setFont(QFont("Segoe UI", 14, QFont.Bold))
        subtitle.setStyleSheet(f"color: {theme_manager.get_theme()['primary1']};")
        layout.addWidget(subtitle)
        
        info = QLabel("No appliances configured yet")
        info.setFont(QFont("Segoe UI", 12))
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #888;")
        layout.addWidget(info, 1, Qt.AlignCenter)
        
        return page

    def open_room(self, room_name):
        """Open the selected room's appliance page"""
        room_index = {
            "Living Room": 1,
            "Master Bed Room": 2,
            "Kids Room": 3,
            "Guest Room": 4,
            "Kitchen": 5
        }
        
        self.stack.setCurrentIndex(room_index.get(room_name, 0))
        self.title_label.setText(f"Smart Home - {room_name}")
        self.back_btn.show()

    def show_rooms(self):
        """Return to room selection page"""
        self.stack.setCurrentIndex(0)
        self.title_label.setText("Smart Home Control")
        self.back_btn.hide()

    def update_theme(self):
        """Update theme for all cards"""
        for card in self.appliance_cards:
            card.update_theme()
        self.update()