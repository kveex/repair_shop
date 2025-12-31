from enum import Enum, IntEnum
from typing import Callable

from PySide6.QtGui import QTextOption
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel,
                               QGridLayout, QVBoxLayout, QScrollArea,
                               QLineEdit, QTextEdit, QHBoxLayout, QCheckBox, QComboBox, QDialog, QSizePolicy, QFrame)
from PySide6.QtCore import Qt, QTimer, QRect, QEvent, QObject, Signal, QSize

from src.database.services.order import Order, priority_to_name
from src.database.services.service import Service
from src.database.services.worker import Worker
from src.database.services.client import Client

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

            try:
                self.cards[card_id].clicked.disconnect()
            except KeyError:
                pass

            card.clicked.connect(func)
            self.cards[card_id] = card
            self.layout.addWidget(card)

    def update_card(self, card_name: str, card_desc: str, full_card_info, func: Callable, card_help: str | None = None, card_help_desc: str | None = None):
        card_id = full_card_info.id
        if card_id in self.cards:
            self.cards[card_id].update_card_info(card_name, card_desc, full_card_info, card_help, card_help_desc)

            try:
                self.cards[card_id].clicked.disconnect()
            except KeyError:
                pass

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

        self.layout.addWidget(label)

    def get_layout(self) -> QVBoxLayout:
        return self.layout

class ServiceInfoBox(BoxWidget):
    def __init__(self, label_text: str, service_list: list[Service], on_check: Callable = None):
        super().__init__(label_text)
        layout = self.get_layout()
        container = QWidget()

        services_layout = QVBoxLayout(container)
        services_layout.setSpacing(5)
        services_layout.setContentsMargins(5, 5, 5, 5)

        for service in service_list:
            item = ServiceBoxItem(service, True, False, on_check)
            services_layout.addWidget(item)

        layout.addWidget(container)

class ServiceSelectBox(BoxWidget):
    def __init__(self, label_text: str):
        super().__init__(label_text)
        self.services: dict[int, ServiceBoxItem] = {}
        layout = self.get_layout()
        container = QWidget()

        self.services_layout = QVBoxLayout(container)
        self.services_layout.setSpacing(5)
        self.services_layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(container)

    def add_service(self, service: Service, uneditable_price: bool, on_check: Callable = None):
        item = ServiceBoxItem(service, uneditable_price, True, on_check)
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
    def __init__(self, service: Service, uneditable_price: bool, clickable: bool, on_check: Callable | None):
        super().__init__()

        self.service = service

        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self.check_box = None
        service_name = QLabel(service.name)
        # service_name.setStyleSheet("background-color: #f0f0f0; padding: 10px")
        service_name.setToolTip(f"Описание: {service.description}")
        service_price = QLineEdit()
        price: str = f"{service.price}₽" if service.price else "Нет начальной"
        service_price.setToolTip(f"Цена услуги: {price} | Тип услуги: {service.service_type}")
        service_price.setText(price)
        service_price.setMaxLength(15)
        service_price.setReadOnly(uneditable_price)

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

class InputBox(BoxWidget):
    def __init__(self, label_text: str, multi_line=False, echo_mode: QLineEdit.EchoMode = QLineEdit.EchoMode.Normal):
        super().__init__(label_text)
        layout = self.get_layout()

        if multi_line:
            self.value_input = QTextEdit()
            self.value_input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value_input = QLineEdit()
            self.value_input.setEchoMode(echo_mode)

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

class PriorityInputBox(BoxWidget):
    def __init__(self, label_text: str):
        super().__init__(label_text)
        layout = self.get_layout()
        self.priority_box = QComboBox()
        for priority, display_name in priority_to_name.items():
            self.priority_box.addItem(display_name, priority)
        self.priority_box.setCurrentIndex(0)

        layout.addWidget(self.priority_box)

    def get_data(self) -> int:
        return self.priority_box.currentData()

    def reset_index(self):
        self.priority_box.setCurrentIndex(0)


class NotificationType(IntEnum):
    SUCCESS = 0
    WARNING = 1
    ERROR = 2
    NOTIFY = 3

class _NotificationWidget(QDialog):
    clicked = Signal()

    def __init__(self, parent: QWidget, title: str, description: str, notification_type: NotificationType):
        super().__init__(f=Qt.WindowType.Tool)
        self.setParent(parent)
        self.setMaximumSize(600, 70)
        self.installEventFilter(self)

        self.setObjectName("NotificationDialog")
        self.setStyleSheet(
            """
                QDialog#NotificationDialog {
                    border: 2px solid #8bc34a;
                    border-radius: 5px;
                }
            """
        )

        icon_path: str = "src/ui/icons/"
        match notification_type:
            case NotificationType.NOTIFY:
                icon_path += "notification_notice.svg"
            case NotificationType.SUCCESS:
                icon_path += "notification_success.svg"
            case NotificationType.WARNING:
                icon_path += "notification_warning.svg"
            case NotificationType.ERROR:
                icon_path += "notification_error.svg"

        layout = QHBoxLayout(self)
        text_layout = QVBoxLayout()

        icon = QSvgWidget(icon_path)
        icon.setFixedSize(54, 54)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        description_label = QLabel(description)
        description_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(description_label)

        layout.addWidget(icon)
        layout.addLayout(text_layout)

        self.show()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            self.clicked.emit()
            return True
        return super().eventFilter(obj, event)


class NotificationManager(QObject):
    def __init__(self, parent: QWidget):
        super().__init__()
        self.MARGIN = 5
        self.GAP = 7
        self.notification_parent = parent
        self.notifications: list[_NotificationWidget] = []
        self.notification_parent.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.notification_parent:
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                self.position_notifications()
        return False

    def position_notifications(self):
        if not self.notifications:
            return

        parent_rect: QRect = self.notification_parent.geometry()

        x = parent_rect.right() - self.MARGIN
        y = parent_rect.bottom() - self.MARGIN

        for n in reversed(self.notifications):
            n.adjustSize()

            new_x = x - n.width()
            y = y - n.height()
            n.move(new_x, y)

            y = y - self.GAP

    def delete_notification(self, notification: _NotificationWidget):
        try:
            self.notifications.remove(notification)
        except ValueError:
            pass
        notification.accept()
        self.position_notifications()

    def show_notification(self, title: str, description: str, notification_type: NotificationType):
        notification_type_to_duration = {
            NotificationType.SUCCESS: 3000,
            NotificationType.WARNING: 5000,
            NotificationType.ERROR: 7000,
            NotificationType.NOTIFY: 5000
        }

        notification: _NotificationWidget = _NotificationWidget(self.notification_parent, title, description,
                                                                notification_type)
        notification.clicked.connect(lambda n=notification: self.delete_notification(n))
        self.notifications.append(notification)
        self.position_notifications()
        notification.show()
        QTimer.singleShot(notification_type_to_duration[notification_type],
                          lambda: self.delete_notification(notification))


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
