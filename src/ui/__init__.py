from enum import Enum
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QScrollArea, QDialog
from PySide6.QtCore import Qt
from logger_config import logger

class Screens(Enum):
    LOGIN_SCREEN = 0
    MANAGER_SCREEN = 1
    CASHIER_SCREEN = 2
    TECHNICIAN_SCREEN = 3
    STORAGER_SCREEN = 4
    REGISTER_SCREEN = 5

class Roles(Enum):
    MANAGER = "Менеджер"
    CASHIER = "Кассир"
    TECHNICIAN = "Техник"
    STORAGER = "Работник склада"

class CardWidget(QPushButton):
    def __init__(self, start_info: tuple[str, str, int], full_info: list[str]):
        super().__init__()

        self.info = full_info

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
        self.info_dialog = QDialog(self)

        self.setLayout(layout)

        self.setMaximumHeight(70)
        self.setMinimumHeight(50)

        self.clicked.connect(self.on_press)

    def on_press(self):
        self.info_dialog.setWindowTitle("Full Info")
        i = 0
        names = [
            "Фио клиента: ",
            "Номер клиента: ",
            "Адрес клиента: ",
            "Услуга: ",
            "Описание услуги: ",
            "Цена: ",
            "Назначенный техник: ",
            "Описание проблемы: ",
            "Статус: ",
            "Время принятия: ",
            "Время завершения: "
        ]

        layout = QVBoxLayout()

        for text in self.info:
            label = QLabel(names[i] + str(text))
            layout.addWidget(label)
            i += 1

        self.info_dialog.setLayout(layout)
        self.info_dialog.open()

class CardListWidget(QWidget):
    def __init__(self, info: list, name_id: int, description_id: int, result_id: int):
        super().__init__()

        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        scroll.setWidget(self.container)

        main_layout.addWidget(scroll)

        self.setLayout(main_layout)
        self.fill_list(info, name_id, description_id, result_id)

    def add_item(self):
        pass

    def fill_list(self, info: list, name_id: int, description_id: int, result_id: int):

        for inf in info:
            card = CardWidget((inf[name_id], inf[description_id], inf[result_id]), info)
            self.layout.addWidget(card)

