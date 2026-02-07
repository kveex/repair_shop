from enum import Enum, IntEnum
from typing import Callable, Optional

from PySide6.QtGui import QTextOption, QAction
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel,
                               QGridLayout, QVBoxLayout, QScrollArea,
                               QLineEdit, QTextEdit, QHBoxLayout,
                               QCheckBox, QMenuBar, QStackedWidget)

from PySide6.QtCore import Qt, Signal
from qt_material import QtStyleTools

from database.services.service import ServiceTypes
from src.database.services.order import Order
from src.database.services.service import Service
from src.database.services.worker import Worker
from src.database.services.client import Client
from utils import NotificationManager


class Screens(IntEnum):
    LOGIN_SCREEN = 0
    MANAGER_SCREEN = 1
    CASHIER_SCREEN = 2
    TECHNICIAN_SCREEN = 3
    STORAGER_SCREEN = 4
    REGISTER_SCREEN = 5
    NO_ROLE_SCREEN = 6


class Roles(Enum):
    MANAGER = "Менеджер"
    CASHIER = "Кассир"
    TECHNICIAN = "Техник"
    STORAGER = "Работник склада"
    NO_ROLE = "Не назначена"


class _CardWidget(QPushButton):
    def __init__(self, name: str, desc: str, full_info: Client | Worker | Service | Order, help_str: str | None = None,
                 help_desc: str | None = None):
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

    def update_card_info(self, name: str, desc: str, full_info: Client | Worker | Service | Order,
                         help_str: str | None = None, help_desc: str | None = None):
        self.info = full_info
        self.name_label.setText(name)
        self.desc_label.setText(desc)
        if help_str is not None:
            self.help_label.setText(help_str)
        if help_desc is not None:
            self.help_desc_label.setText(help_desc)


class CardListWidget(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        self.cards: dict[int, _CardWidget] = {}

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textChanged.connect(self.search_card)

        self.scrollArea.setWidget(self.container)

        main_layout.addWidget(self.search)
        main_layout.addWidget(self.scrollArea)

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

    def create_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None,
                    card_help_desc: str | None = None):
        card_id = full_card_info.id
        if card_id not in self.cards:
            card = _CardWidget(card_name, card_desc, full_card_info, card_help, card_help_desc)

            card.clicked.connect(func)
            self.cards[card_id] = card
            self.layout.addWidget(card)

    def update_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None,
                    card_help_desc: str | None = None):
        card_id = full_card_info.id
        if card_id in self.cards:
            self.cards[card_id].update_card_info(card_name, card_desc, full_card_info, card_help, card_help_desc)

            try:
                self.cards[card_id].clicked.disconnect()
            except (KeyError, RuntimeError, TypeError):
                pass

            self.cards[card_id].clicked.connect(func)

    def sync_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None,
                  card_help_desc: str | None = None):
        self.update_card(card_name, card_desc, full_card_info, func, card_help, card_help_desc)
        self.create_card(card_name, card_desc, full_card_info, func, card_help, card_help_desc)

    def remove_card(self, card_id: int) -> None:
        try:
            if card_id in self.cards:
                card = self.cards.pop(card_id)
                card.hide()
                card.deleteLater()
        except RuntimeError:
            print(f"Card already deleted")
            pass

    def clear_list(self):
        cards = self.scrollArea.findChildren(_CardWidget)
        for card in cards:
            card.deleteLater()
        self.cards.clear()

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

        self.layout.addWidget(label)

    def get_layout(self) -> QVBoxLayout:
        return self.layout


class ServiceInfoBox(BoxWidget):
    def __init__(self, label_text: str, service_list: list[Service]):
        super().__init__(label_text)
        self._empty_list_label = QLineEdit("Список пуст")
        self._empty_list_label.setReadOnly(True)
        self._empty_list_label.hide()
        layout = self.get_layout()
        self.services: dict[int, ServiceBoxItem] = {}
        container = QWidget()

        self.services_layout = QVBoxLayout(container)
        self.services_layout.setSpacing(5)
        self.services_layout.setContentsMargins(5, 5, 5, 5)

        self.update_list(service_list)

        layout.addWidget(self._empty_list_label)
        layout.addWidget(container)

    def update_list(self, service_list: list[Service]):
        self._remove_items()
        self._empty_list_label.hide()
        if not service_list:
            self._empty_list_label.show()
            return

        for service in service_list:
            item = ServiceBoxItem(service, True, False)
            self.services[service.id] = item
            self.services_layout.addWidget(item)

    def is_empty(self) -> bool:
        return self._empty_list_label.isVisible()

    def _remove_items(self):
        for service in self.services.values():
            try:
                service.deleteLater()
            except RuntimeError:
                pass
        self.services.clear()


class ServiceSelectBox(BoxWidget):
    item_checked = Signal()

    def __init__(self, label_text: str):
        super().__init__(label_text)
        self._is_provided: bool = False
        self._services: dict[int, ServiceBoxItem] = {}
        layout = self.get_layout()
        container = QWidget()

        self._services_layout = QVBoxLayout(container)
        self._services_layout.setSpacing(5)
        self._services_layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(container)

    def add_service(self, service: Service, uneditable_price: bool, is_provided: bool = False, clickable: bool = True):
        item = ServiceBoxItem(service, uneditable_price, clickable)
        item.item_checked.connect(lambda: self.item_checked.emit())
        self._is_provided = is_provided
        if service.id in self._services:
            self._services[service.id].hide()
            self._services[service.id].deleteLater()
        self._services[service.id] = item
        self._services_layout.addWidget(item)

    def get_checked_services(self) -> list[Service]:
        result: list[Service] = []

        for service in self._services.values():
            s = service.get_service_if_checked()

            if s is not None:
                s.price = service.get_service_price()
                if self._is_provided:
                    s.service_type = ServiceTypes.PROVIDED
                    result.append(s)
                else:
                    result.append(s)
        return result

    def reset_checks(self):
        for service_item in self._services.values():
            service_item.uncheck()

    def is_prices_set(self) -> bool:
        for service in self._services.values():
            if not service.get_service_price(): return False

        return True


class ServiceBoxItem(QWidget):
    item_checked = Signal()

    def __init__(self, service: Service, uneditable_price: bool, clickable: bool):
        super().__init__()
        self._service = service

        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self._check_box = None
        service_name = QLabel(service.name)
        service_name.setToolTip(f"Описание: {service.description}")
        self._service_price = QLineEdit()
        price: str = f"{service.price}₽" if service.price else ""
        self._service_price.setToolTip(f"Цена услуги: {price} | Тип услуги: {service.service_type}")
        self._service_price.setText(price)
        self._service_price.setMaxLength(15)
        self._service_price.setReadOnly(uneditable_price)

        if clickable:
            self._check_box = QCheckBox()
            # if on_check is not None:
            #     self.check_box.checkStateChanged.connect(on_check)
            self._check_box.checkStateChanged.connect(lambda: self.item_checked.emit())

        if self._check_box: layout.addWidget(self._check_box)
        layout.addWidget(service_name)
        layout.addWidget(self._service_price)

    def is_checked(self) -> bool:
        if self._check_box:
            return self._check_box.isChecked()
        return False

    def uncheck(self):
        if self._check_box:
            self._check_box.setChecked(False)

    def check(self):
        if self._check_box:
            self._check_box.setChecked(True)

    def get_service_if_checked(self) -> Service | None:
        if not self._check_box: return None
        if self._check_box.isChecked():
            return self._service
        return None

    def get_service_price(self) -> int | None:
        cleaned = self._service_price.text().removesuffix("₽")
        if cleaned == "":
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None

    def get_service(self) -> Service:
        return self._service


class InfoBox(BoxWidget):
    def __init__(self, label_text: str, value_text: str, hex_color: str = None, multi_line=False):
        super().__init__(label_text)

        layout = self.get_layout()

        if multi_line:
            self.value = QTextEdit(value_text)
            self.value.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value = QLineEdit(value_text)

        self.value.setReadOnly(True)
        if hex_color:
            self.value.setStyleSheet(f"QLineEdit, QTextEdit {{background-color: {hex_color}}}")

        layout.addWidget(self.value)

    def set_value(self, value: str):
        self.value.setText(value)


class InputBox(BoxWidget):
    def __init__(self, label_text: str, multi_line=False, echo_mode: QLineEdit.EchoMode = QLineEdit.EchoMode.Normal,
                 on_change: Optional[Callable[[], None]] = None):
        super().__init__(label_text)
        layout = self.get_layout()
        self._on_change = on_change

        if multi_line:
            self.value_input = QTextEdit()
            self.value_input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
            if self._on_change:
                self.value_input.textChanged.connect(self._on_change)
        else:
            self.value_input = QLineEdit()
            self.value_input.setEchoMode(echo_mode)
            if self._on_change:
                self.value_input.textChanged.connect(self._on_change)

        layout.addWidget(self.value_input)

    def get_value(self) -> str:
        if hasattr(self.value_input, "toPlainText"):
            text = self.value_input.toPlainText()
        else:
            text = self.value_input.text()
        return text

    def set_value(self, value: str):
        self.value_input.setText(value)

    def no_input(self) -> bool:
        if not self.get_value():
            self.value_input.setStyleSheet("border: 2px solid red; border-radius: 5px;")
            return True
        return False

    def clear_input(self):
        self.value_input.setText("")


class MenuBar(QMenuBar, QtStyleTools):
    def __init__(self, stack: QStackedWidget, notification_manager: NotificationManager):
        super().__init__()
        account_menu = self.addMenu("Аккаунт")

        self.logout_action = QAction("Выйти", self)
        self.logout_action.triggered.connect(lambda: stack.setCurrentIndex(0))
        self.logout_action.setEnabled(False)

        notifications_menu = self.addMenu("Уведомления (0)")
        notification_manager.notification_amount_changed.connect(
            lambda amount: notifications_menu.setTitle(f"Уведомлений ({amount})")
        )

        self._show_notifications_action = QAction("Все уведомления", self)
        self._show_notifications_action.triggered.connect(notification_manager.show_all_notifications)
        self._clear_notifications_action = QAction("Очистить уведомления", self)
        self._clear_notifications_action.triggered.connect(notification_manager.delete_all_notifications)

        account_menu.addAction(self.logout_action)
        notifications_menu.addAction(self._show_notifications_action)
        notifications_menu.addAction(self._clear_notifications_action)
