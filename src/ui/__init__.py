from enum import Enum
from typing import Callable

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QScrollArea, QDialog, QLineEdit
from PySide6.QtCore import Qt

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

class _CardWidget(QPushButton):
    def __init__(self, name_index: int, desc_index: int, help_index: int, full_info: list[str]):
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

        client_name = QLabel(full_info[name_index])
        service_name = QLabel(full_info[desc_index])
        price = QLabel(f"{full_info[help_index]}, ₽")

        layout.addWidget(client_name, 0, 0)
        layout.addWidget(service_name, 1, 0)
        layout.addWidget(price, 0, 1, Qt.AlignmentFlag.AlignRight)
        self.info_dialog = QDialog(self)

        self.setLayout(layout)

        self.setMaximumHeight(70)
        self.setMinimumHeight(50)


class CardListWidget(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textChanged.connect(self.search_card)

        self.scroll.setWidget(self.container)

        main_layout.addWidget(self.search)
        main_layout.addWidget(self.scroll)

        self.setLayout(main_layout)

    def search_card(self, _=None):
        q = self.search.text().strip().lower()
        cards = self.scroll.findChildren(_CardWidget, "cardWidget", Qt.FindChildOption.FindChildrenRecursively)
        if not cards:
            return

        if q == "":
            for card in cards:
                card.show()
            return

        for card in cards:
            info_list = card.info
            visible = any(q in str(field).lower() for field in info_list)
            card.setVisible(visible)

    def create_cards(self, name_index: int, desc_index: int, help_index: int, info_list: list[list[str]], func: Callable):
        count = 0
        for _ in info_list:
            card = _CardWidget(name_index, desc_index, help_index, info_list[count])
            card.clicked.connect(func)
            self.layout.addWidget(card)
            count += 1

def check_errors(fields: list[QLineEdit], error_label: QLabel):
    has_error = False

    # if not error_label.isHidden():
    #     raise ValueError("Error label needs to be hidden first!")

    for field in fields:
        if hasattr(field, "toPlainText"):
            if not field.toPlainText().strip():
                field.setStyleSheet("border: 2px solid red; border-radius: 5px;")  # красная граница
                has_error = True

        elif not field.text().strip():
            field.setStyleSheet("border: 2px solid red; border-radius: 5px;")  # красная граница
            has_error = True
        else:
            field.setStyleSheet("")

    if has_error:
        error_label.setText("Все поля должны быть заполнены!")
        error_label.show()
        return
