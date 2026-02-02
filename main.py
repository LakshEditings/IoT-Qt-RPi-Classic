import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from Screen1 import Screen1
from Screen2 import Screen2
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

        # Initialize screens
        self.screen1 = Screen1(self)
        self.screen2 = Screen2(self)
        
        self.stack.addWidget(self.screen1)
        self.stack.addWidget(self.screen2)

        # Initialize dial update variables
        self.fan_value = 0
        self.light_value = 0

    def keyPressEvent(self, event):
        index = self.stack.currentIndex()
        if event.key() == Qt.Key_Left and index > 0:
            self.stack.setCurrentIndex(index - 1)
        elif event.key() == Qt.Key_Right and index < self.stack.count() - 1:
            self.stack.setCurrentIndex(index + 1)
        else:
            super().keyPressEvent(event)

    def update_stylesheet(self):
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
                font-size: 10px;
            }}
            QPushButton:checked {{
                background-color: {theme["primary2"]};
            }}
            QComboBox {{
                background-color: {theme["secondary2"]};
                color: {theme["secondary3"]};
                font-size: 12px;
                padding: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme["secondary2"]};
                color: {theme["secondary3"]};
            }}
            QLabel {{
                color: {theme["secondary3"]};
            }}
        """)

    def change_theme(self):
        theme_name = self.screen1.theme_combo.currentText()
        theme_manager.set_theme(theme_name)
        self.update_stylesheet()
        self.screen1.fan_dial.update()
        self.screen1.light_dial.update()
        self.screen1.total_dial.update()
        self.screen2.update_graph()
        self.update()

    def mousePressEvent(self, event):
        self.start_pos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        if not self.start_pos:
            return
        dx = event.position().x() - self.start_pos.x()
        if abs(dx) > 50:
            index = self.stack.currentIndex()
            if dx < 0 and index < self.stack.count() - 1:
                self.stack.setCurrentIndex(index + 1)
            elif dx > 0 and index > 0:
                self.stack.setCurrentIndex(index - 1)
        self.start_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())