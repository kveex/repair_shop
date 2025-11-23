from enum import Enum
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout
from PySide6.QtCore import Qt

class Screens(Enum):
    LOGIN_SCREEN = 0
    TEST_SCREEN = 1
    MANAGER_SCREEN = 2
    CASHIER_SCREEN = 3
    TECHNICIAN_SCREEN = 4
    STORAGER_SCREEN = 5
    REGISTER_SCREEN = 6

class Roles(Enum):
    MANAGER = "Менеджер"
    CASHIER = "Кассир"
    TECHNICIAN = "Техник"
    STORAGER = "Работник склада"

class CardWidget(QPushButton):
    def __init__(self, start_info: tuple[str, str, int], full_info: list[str]):
        super().__init__()

        self.setObjectName("cardWidget")

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QWidget#cardWidget {
                border: 2px solid #1E90FF;   /* синяя рамка */
                border-radius: 8px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        client_name = QLabel(start_info[0])
        service_name = QLabel(start_info[1])
        price = QLabel(f"{start_info[2]}, ₽")

        layout.addWidget(client_name, 0, 0)
        layout.addWidget(service_name, 1, 0)
        layout.addWidget(price, 0, 1, Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

        self.setMaximumHeight(70)
        self.setMinimumHeight(50)

        self.clicked.connect(self.on_press)

    def on_press(self):
        print("Aboba")

