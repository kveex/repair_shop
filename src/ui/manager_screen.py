from PySide6.QtWidgets import QWidget, QStackedWidget, QLabel, QVBoxLayout, QPushButton
from src.ui import Screens
from qasync import asyncSlot

from utils import NotificationManager


class ManagerScreen(QWidget):
    def __init__(self, notification_manager: NotificationManager):
        super().__init__()
        self.layout = QVBoxLayout()

        self.label = QLabel("Менеджер")

        self.button = QPushButton()
        self.button.setText("Регистрация")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

