from dataclasses import asdict
from enum import Enum
from typing import Callable
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QScrollArea, QLineEdit
from PySide6.QtCore import Qt

from src.database.services.order import Order
from src.database.services.service import Service
from src.database.services.worker import Worker
from src.database.services.client import Client


GLOBAL_STYLES = """
* {
    background-color: #f8f9fa;
    color: #212529;
    font-family: "Segoe UI", "Roboto", "Ubuntu", sans-serif;
    font-size: 13px;
    selection-background-color: #339af0;
    selection-color: white;
}

QWidget#cardWidget {
                border: 2px solid #1E90FF;   /* синяя рамка */
                border-radius: 8px;
                background-color: #ffffff;
            }

QMainWindow, QDialog, QWidget {
    background-color: #ffffff;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #339af0;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #339af0;
}

QPushButton {
    background-color: #339af0;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #228be6;
}

QPushButton:pressed {
    background-color: #1c7ed6;
}

QPushButton:disabled {
    background-color: #adb5bd;
    color: #6c757d;
}

QPushButton[objectName*="cancel"], QPushButton[objectName*="delete"] {
    background-color: #ff6b6b;
}

QPushButton[objectName*="cancel"]:hover, QPushButton[objectName*="delete"]:hover {
    background-color: #fa5252;
}

QListWidget, QTreeWidget, QTableWidget {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 5px;
}

QListWidget::item:hover, QTableWidget::item:hover {
    background-color: #e7f5ff;
}

QGroupBox {
    border: 2px solid #e9ecef;
    border-radius: 8px;
    margin-top: 15px;
    padding: 15px;
    font-weight: 600;
    color: #495057;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 15px;
    background-color: #ffffff;
    color: #212529;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #adb5bd;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #339af0;
    border-color: #339af0;
    image: url(:/icons/check.svg);  /* Можно добавить иконку */
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
}

QMenuBar::item:selected {
    background-color: #e7f5ff;
}

QStatusBar {
    background-color: #f8f9fa;
    color: #6c757d;
}
"""

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
    def __init__(self, name: str, desc: str, full_info: Client | Worker | Service | Order, help: str | None = None, help_desc: str | None = None):
        super().__init__()

        self.info = full_info

        self.setObjectName("cardWidget")

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QGridLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        name_label = QLabel(name)
        desc_label = QLabel(desc)
        help_label = QLabel(help)
        help_desc_label = QLabel(help_desc)

        layout.addWidget(name_label, 0, 0)
        layout.addWidget(desc_label, 1, 0)
        layout.addWidget(help_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(help_desc_label, 1, 1, Qt.AlignmentFlag.AlignRight)
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
            visible = any(q in str(field).lower() for field in asdict(info_list).items())
            card.setVisible(visible)

    def create_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None, card_help_desc: str | None = None):
        card = _CardWidget(card_name, card_desc, full_card_info, card_help, card_help_desc)
        card.clicked.connect(func)
        self.layout.addWidget(card)

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

async def check_empty_fields(fields: list[QLineEdit], error_label: QLabel):
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
    return has_error
