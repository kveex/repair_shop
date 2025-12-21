from enum import Enum
from typing import Callable

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel,
                               QGridLayout, QVBoxLayout, QScrollArea,
                               QLineEdit, QTextEdit, QHBoxLayout, QCheckBox, QComboBox)
from PySide6.QtCore import Qt

from src.database.services.order import Order, priority_to_name
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

QComboBox {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 12px 8px 12px;  /* Симметричный padding как у QLineEdit */
    font-size: 13px;
    color: #212529;
    min-height: 32px;  /* Оптимальная высота, не слишком большая */
}

/* Кнопка выпадающего списка (стрелка) */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 30px;
    border: none;  /* Убираем левую рамку */
    background: transparent;
    padding-right: 5px;
}

/* Иконка стрелки — используем символ Unicode для кроссплатформенности */
QComboBox::down-arrow {
    image: none;  /* Убираем стандартную иконку */
    border: none;
}

/* Выпадающий список */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #339af0;  /* Акцентный цвет как у selection */
    selection-color: white;
    outline: none;
    margin-top: 2px;  /* Небольшой отступ от основного поля */
}

/* Элементы внутри списка */
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 4px;
    min-height: 28px;  /* Компактные элементы */
}

/* Эффект при наведении */
QComboBox QAbstractItemView::item:hover {
    background-color: #e7f5ff;  /* Светло-синий как у QLineEdit:focus */
}

QListWidget {
    background-color: #f0f0f0;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    color: #333;
    outline: none;
}

QListWidget::item {
    padding: 8px 10px;
    margin: 2px 0;
    border-radius: 4px;
}

QListWidget::item:selected {
    border: 2px solid #d1d1d1;
    color: #333;
}

QListWidget::item:hover {
    background-color: #d1d1d1;
}

QListWidget QScrollBar:vertical {
        border: none;
        background: #f0f0f0;
        width: 12px;
        margin: 0;
}
    
/* Ползунок (thumb) */
QListWidget QScrollBar::handle:vertical {
    background: #d0d0d0;
    border-radius: 6px;
    min-height: 30px;
}

/* Убираем СТРЕЛКИ (квадратные кнопки) */
QListWidget QScrollBar::add-line:vertical,
QListWidget QScrollBar::sub-line:vertical {
    height: 0px;
    border: none;
    background: none;
}

/* Убираем области между ползунком и стрелками */
QListWidget QScrollBar::add-page:vertical,
QListWidget QScrollBar::sub-page:vertical {
    background: none;
}

QTreeWidget, QTableWidget {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 5px;
}

QTableWidget::item:hover {
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
    background-color: #f0f0f0;
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
    def __init__(self, name: str, desc: str, full_info: Client | Worker | Service | Order, help_str: str | None = None, help_desc: str | None = None):
        super().__init__()

        self.info = full_info

        self.setObjectName("cardWidget")

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QGridLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        self.name_label = QLabel(name)
        self.desc_label = QLabel(desc)
        self.help_label = QLabel(help_str)
        self.help_desc_label = QLabel(help_desc)

        layout.addWidget(self.name_label, 0, 0)
        layout.addWidget(self.desc_label, 1, 0)
        layout.addWidget(self.help_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.help_desc_label, 1, 1, Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

        self.setMaximumHeight(70)
        self.setMinimumHeight(50)

    def update_card_info(self, name: str, desc: str, full_info: Client | Worker | Service | Order, help_str: str | None = None, help_desc: str | None = None):
        self.info = full_info
        self.name_label.setText(name)
        self.desc_label.setText(desc)
        if help is not None:
            self.help_label.setText(help_str)
        if help_desc is not None:
            self.help_desc_label.setText(help_desc)

class CardListWidget(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        self.cards: dict[int, _CardWidget] = {}

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
        if not q:
            for card in self.cards.values():
                card.show()
            return

        from dataclasses import asdict
        for card_id, card in self.cards.items():
            info_dict = asdict(card.info)
            visible = any(q in str(value).lower() for value in info_dict.values())
            card.setVisible(visible)

    def create_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None, card_help_desc: str | None = None):
        card_id = full_card_info.id
        if not card_id in self.cards:
            card = _CardWidget(card_name, card_desc, full_card_info, card_help, card_help_desc)
            card.clicked.connect(func)
            self.cards[card_id] = card
            self.layout.addWidget(card)

    def update_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None, card_help_desc: str | None = None):
        card_id = full_card_info.id
        if card_id in self.cards:
            self.cards[card_id].update_card_info(card_name, card_desc, full_card_info, card_help, card_help_desc)
            self.cards[card_id].clicked.connect(func)

    def sync_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None, card_help_desc: str | None = None):
        self.update_card(card_name, card_desc, full_card_info, func, card_help, card_help_desc)
        self.create_card(card_name, card_desc, full_card_info, func, card_help, card_help_desc)

    def clear_list(self):
        cards = self.scroll.findChildren(_CardWidget)
        for card in cards:
            card.deleteLater()

    def get_card_full_info(self, card_id: int):
        for card in self.cards.values():
            if card.info.id == card_id:
                return card.info
        return None
class BoxWidget(QWidget):
    def __init__(self, label_text: str):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setStyleSheet("""
                            QLabel {
                                font-size: 12px;
                                color: #555;
                                padding-bottom: 2px;
                            }
                        """)

        self.layout.addWidget(label)

    def get_layout(self) -> QVBoxLayout:
        return self.layout

class ServiceInfoBox(BoxWidget):
    def __init__(self, label_text: str, service_list: list[Service], on_check: Callable = None):
        super().__init__(label_text)
        layout = self.get_layout()
        container = QWidget()
        container.setObjectName("servicesContainer")
        container.setStyleSheet("""
                    QWidget#servicesContainer {
                        background-color: #f0f0f0;
                        border: 1px solid #d0d0d0;
                        border-radius: 8px;
                        padding: 10px;
                    }
                """)

        services_layout = QVBoxLayout(container)
        services_layout.setSpacing(5)
        services_layout.setContentsMargins(5, 5, 5, 5)

        for service in service_list:
            item = ServiceBoxItem(service, False, False, on_check)
            services_layout.addWidget(item)

        layout.addWidget(container)

class ServiceSelectBox(BoxWidget):
    def __init__(self, label_text: str):
        super().__init__(label_text)
        self.services: dict[int, ServiceBoxItem] = {}
        layout = self.get_layout()
        container = QWidget()
        container.setObjectName("servicesContainer")
        container.setStyleSheet("""
                            QWidget#servicesContainer {
                                background-color: #f0f0f0;
                                border: 1px solid #d0d0d0;
                                border-radius: 8px;
                                padding: 10px;
                            }
                        """)

        self.services_layout = QVBoxLayout(container)
        self.services_layout.setSpacing(5)
        self.services_layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(container)

    def add_service(self, service: Service, editable_price: bool, on_check: Callable = None):
        item = ServiceBoxItem(service, editable_price, True, on_check)
        self.services[service.id] = item
        self.services_layout.addWidget(item)

    def get_checked_services(self) -> list[Service]:
        result: list[Service] = []

        for service in self.services.values():
            s = service.get_service_if_checked()
            if not s is None:
                result.append(s)
        return result

    def reset_checks(self):
        for service_item in self.services.values():
            if not service_item.service.name == "Диагностика":
                service_item.uncheck()

class ServiceBoxItem(QWidget):
    def __init__(self, service: Service, editable_price: bool, clickable: bool, on_check: Callable | None):
        super().__init__()

        self.service = service

        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self.check_box = None
        service_name = QLabel(service.name)
        service_name.setStyleSheet("background-color: #f0f0f0; padding: 10px")
        service_name.setToolTip(f"Описание: {service.description}")
        service_price = QLineEdit()
        price: str = f"{service.price}₽" if service.price else "Нет начальной"
        service_price.setToolTip(f"Цена услуги: {price} | Тип услуги: {service.service_type}")
        service_price.setText(price)
        service_price.setMaxLength(15)
        service_price.setEnabled(editable_price)

        if clickable:
            self.check_box = QCheckBox()
            if not on_check is None:
                self.check_box.checkStateChanged.connect(on_check)

        if self.check_box: layout.addWidget(self.check_box)
        layout.addWidget(service_name)
        layout.addWidget(service_price)

    def is_checked(self) -> bool:
        if self.check_box:
            return self.check_box.isChecked()
        return False

    def uncheck(self):
        if self.check_box:
            self.check_box.setChecked(False)

    def get_service_if_checked(self) -> Service | None:
        if self.check_box.isChecked():
            return self.service
        return None

class InfoBox(BoxWidget):
    def __init__(self, label_text: str, value_text: str, hex_color: str = "#f0f0f0", multi_line=False):
        super().__init__(label_text)

        layout = self.get_layout()

        if multi_line:
            self.value = QTextEdit(value_text)
            self.value.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value = QLineEdit(value_text)

        self.value.setReadOnly(True)
        self.value.setStyleSheet(f"""
            QLineEdit, QTextEdit {{
                background-color: {hex_color};
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #333;
            }}
        """)

        layout.addWidget(self.value)

class InputBox(BoxWidget):
    def __init__(self, label_text: str, hex_color: str = "#ffffff", multi_line=False):
        super().__init__(label_text)
        layout = self.get_layout()

        if multi_line:
            self.value_input = QTextEdit()
            self.value_input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value_input = QLineEdit()

        self.value_input.setStyleSheet(f"""
                    QLineEdit, QTextEdit {{
                        background-color: {hex_color};
                        border: 1px solid #d0d0d0;
                        border-radius: 6px;
                        padding: 8px 10px;
                        font-size: 13px;
                        color: #333;
                    }}
                """)

        layout.addWidget(self.value_input)

    def get_value(self) -> str:
        if hasattr(self.value_input, "toPlainText"):
            text = self.value_input.toPlainText()
        else:
            text = self.value_input.text()
        return text

    def no_input(self) -> bool:
        if not self.get_value():
            self.value_input.setStyleSheet("border: 2px solid red; border-radius: 5px;")
            return True
        return False

    def clear_input(self):
        self.value_input.setText("")

class PriorityInputBox(BoxWidget):
    def __init__(self, label_text: str):
        super().__init__(label_text)
        self.priority_box = QComboBox()
        for priority, display_name in priority_to_name.items():
            self.priority_box.addItem(display_name, priority)
        self.priority_box.setCurrentIndex(0)

    def get_data(self) -> int:
        return self.priority_box.currentData()

def check_errors(fields: list[QLineEdit], error_label: QLabel):
    has_error = False

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

#Переделать этот метод полностью
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
            error_label.setStyleSheet("")

    if has_error:
        error_label.setText("Эти поля должны быть заполнены!")
        error_label.setStyleSheet("color: red")
        error_label.show()
    return has_error
