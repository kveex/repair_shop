from PySide6.QtWidgets import QWidget, QStackedWidget, QLabel, QVBoxLayout, QPushButton
from src.ui import Screens

class ManagerScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.layout = QVBoxLayout()

        self.label = QLabel("Менеджер")

        self.button = QPushButton()
        self.button.setText("Регистрация")

        self.button.clicked.connect(self.open_register_screen)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

    def open_register_screen(self):
        self.stack_widget.setCurrentIndex(Screens.REGISTER_SCREEN.value)
