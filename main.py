import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from Screen1 import Screen1
from Screen2 import Screen2
from Screen3 import Screen3
from themes import theme_manager, THEMES


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home Control")
        self.start_pos = None
        self.setFixedSize(800, 480)
        self.update_stylesheet()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize all three screens
        self.screen1 = Screen1(self)
        self.screen2 = Screen2(self)
        self.screen3 = Screen3(self)
        
        self.stack.addWidget(self.screen1)
        self.stack.addWidget(self.screen2)
        self.stack.addWidget(self.screen3)

    def keyPressEvent(self, event):
        """Handle keyboard navigation between screens"""
        index = self.stack.currentIndex()
        if event.key() == Qt.Key_Left and index > 0:
            self.stack.setCurrentIndex(index - 1)
        elif event.key() == Qt.Key_Right and index < self.stack.count() - 1:
            self.stack.setCurrentIndex(index + 1)
        else:
            super().keyPressEvent(event)

    def update_stylesheet(self):
        """Update application-wide stylesheet based on current theme"""
        theme = theme_manager.get_theme()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme["secondary1"]};
                color: {theme["secondary3"]};
            }}
            QPushButton {{
                background-color: {theme["primary1"]};
                color: {theme["secondary3"]};
                border-radius: 15px;
                font-size: 12px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {theme["primary2"]};
            }}
            QPushButton:checked {{
                background-color: {theme["primary2"]};
            }}
            QComboBox {{
                background-color: {theme["secondary2"]};
                color: {theme["secondary3"]};
                font-size: 12px;
                padding: 6px;
                border-radius: 5px;
                border: 1px solid {theme["primary1"]};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme["secondary2"]};
                color: {theme["secondary3"]};
                selection-background-color: {theme["primary1"]};
            }}
            QLabel {{
                color: {theme["secondary3"]};
            }}
            QTimeEdit {{
                background-color: {theme["secondary2"]};
                color: {theme["secondary3"]};
                padding: 5px;
                border-radius: 5px;
                border: 1px solid {theme["primary1"]};
            }}
            QCheckBox {{
                color: {theme["secondary3"]};
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid {theme["primary1"]};
                background-color: {theme["secondary2"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme["primary1"]};
            }}
            QGroupBox {{
                border: 2px solid {theme["primary1"]};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: {theme["secondary3"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QScrollBar:vertical {{
                background: {theme["secondary2"]};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme["primary1"]};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def mousePressEvent(self, event):
        """Track mouse press position for swipe gestures"""
        self.start_pos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        """Handle swipe gestures for screen navigation"""
        if not self.start_pos:
            return
        dx = event.position().x() - self.start_pos.x()
        if abs(dx) > 50:  # Minimum swipe distance
            index = self.stack.currentIndex()
            if dx < 0 and index < self.stack.count() - 1:  # Swipe left
                self.stack.setCurrentIndex(index + 1)
            elif dx > 0 and index > 0:  # Swipe right
                self.stack.setCurrentIndex(index - 1)
        self.start_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())