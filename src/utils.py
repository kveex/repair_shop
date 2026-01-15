import re
from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import Optional

# from src.ui import Screens
from PySide6.QtCore import QObject, QEvent, QRect, QTimer, Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QDialog, QPushButton, QLabel, QHBoxLayout, \
    QStackedWidget


class PhoneValidationError(Exception): pass


class PhoneLengthError(PhoneValidationError): pass


class WrongPhoneCode(PhoneValidationError): pass


def format_phone_for_db(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone)

    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]

    if not cleaned.startswith('+'):
        cleaned = '+7' + cleaned

    return cleaned


def validate_phone(phone: str) -> str:
    normalized = format_phone_for_db(phone)

    if not normalized.startswith('+7'):
        raise WrongPhoneCode("Номер должен начинаться с +7 или 8")

    if len(normalized) != 12:
        raise PhoneLengthError(f"Номер должен содержать 10 цифр, после +7. Получено: {len(normalized) - 2}")

    if not normalized[2:].isdigit():
        raise PhoneValidationError("Номер содержит недопустимые символы")

    return normalized


def format_phone_for_display(phone: str) -> str:
    normalized = format_phone_for_db(phone)

    if len(normalized) < 12:
        return normalized

    return f"{normalized[:2]} ({normalized[2:5]}) {normalized[5:8]}-{normalized[8:10]}-{normalized[10:]}"

class NotificationType(IntEnum):
    SUCCESS = 0
    WARNING = 1
    ERROR = 2
    NOTIFY = 3


@dataclass(frozen=True, order=True)
class Notification:
    title: str
    description: str
    notification_type: NotificationType


class _NotificationWidget(QDialog):
    clicked = Signal()

    def __init__(self, notification: Notification, show_del_button: bool, parent: Optional[QWidget] = None):
        super().__init__(f=Qt.WindowType.Tool)
        if parent is not None:
            self.setParent(parent)

        self._notification = notification

        self.setMaximumSize(600, 70)
        self.installEventFilter(self)

        self.setObjectName("NotificationDialog")

        icon_path: str = "src/ui/icons/"
        notification_color: str = "ffffff"

        match notification.notification_type:
            case NotificationType.NOTIFY:
                icon_path += "notification_notice.svg"
                notification_color: str = "ffffff"
            case NotificationType.SUCCESS:
                icon_path += "notification_success.svg"
                notification_color: str = "8bc34a"
            case NotificationType.WARNING:
                icon_path += "notification_warning.svg"
                notification_color = "ffd740"
            case NotificationType.ERROR:
                icon_path += "notification_error.svg"
                notification_color = "ff1744"

        self.setStyleSheet(
            f"""
                QDialog#NotificationDialog {{
                    border: 2px solid #{notification_color};
                    border-radius: 5px;
                }}
            """
        )

        layout = QHBoxLayout(self)
        text_layout = QVBoxLayout()

        icon = QSvgWidget(icon_path)
        icon.setFixedSize(54, 54)

        title_label = QLabel(notification.title)
        title_label.setWordWrap(True)
        description_label = QLabel(notification.description)
        description_label.setWordWrap(True)

        self.del_button = None

        text_layout.addWidget(title_label)
        text_layout.addWidget(description_label)

        layout.addWidget(icon)
        layout.addLayout(text_layout)
        if show_del_button:
            self.del_button = QPushButton("Удалить")
            self.del_button.clicked.connect(lambda: self.clicked.emit())
            layout.addWidget(self.del_button)

        self.show()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and not self.del_button:
            self.clicked.emit()
            return True
        return super().eventFilter(obj, event)

    def get_notification(self) -> Notification:
        return self._notification


class _AllNotificationsDialog(QDialog):
    notification_deleted = Signal(object)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Все уведомления")

        self._notifications: list[Notification] = []
        self._widgets: list[_NotificationWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scrollAreaContainer = QWidget()
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaContainer)
        self.scrollArea.setWidget(self.scrollAreaContainer)

        layout.addWidget(self.scrollArea)

    def _delete_notification_widget(self, widget: _NotificationWidget):
        self.scrollAreaLayout.removeWidget(widget)
        widget.hide()
        widget.deleteLater()
        self.notification_deleted.emit(widget.get_notification())

    def clear_all_widgets(self):
        for widget in self._widgets:
            try:
                self.scrollAreaLayout.removeWidget(widget)
                widget.hide()
                widget.deleteLater()
            except RuntimeError:
                pass

        self._widgets.clear()

    def fill_notifications(self, notifications: list[Notification]) -> None:
        self.clear_all_widgets()

        self._notifications = notifications
        for notification in self._notifications:
            widget = _NotificationWidget(notification, True)
            widget.clicked.connect(lambda w=widget: self._delete_notification_widget(w))
            self._widgets.append(widget)
            self.scrollAreaLayout.addWidget(widget)


class NotificationManager(QObject):
    notification_amount_changed = Signal(object)
    def __init__(self, parent: QWidget):
        super().__init__()
        self.MARGIN = 5
        self.GAP = 7
        self.notification_parent = parent
        self.all_notifications: list[Notification] = []
        self.showed_notifications: list[_NotificationWidget] = []
        self.all_notifications_dialog: _AllNotificationsDialog = _AllNotificationsDialog()
        self.all_notifications_dialog.notification_deleted.connect(lambda n: self._delete_notification(n))
        self.notification_parent.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.notification_parent:
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                self.position_notifications()
        return False

    def position_notifications(self):
        if not self.showed_notifications:
            return

        parent_rect: QRect = self.notification_parent.geometry()

        x = parent_rect.right() - self.MARGIN
        y = parent_rect.bottom() - self.MARGIN

        for n in reversed(self.showed_notifications):
            n.adjustSize()

            new_x = x - n.width()
            y = y - n.height()
            n.move(new_x, y)

            y = y - self.GAP

    def _hide_notification(self, notification: _NotificationWidget):
        try:
            self.showed_notifications.remove(notification)
        except ValueError:
            pass
        notification.accept()
        self.position_notifications()

    def _delete_notification(self, notification: Notification):
        try:
            self.all_notifications.remove(notification)
        except ValueError:
            print(f"already deleted {notification}")
            pass
        self.notification_amount_changed.emit(len(self.all_notifications))

    def show_notification(self, title: str, description: str, notification_type: NotificationType):
        notification_type_to_duration = {
            NotificationType.SUCCESS: 3000,
            NotificationType.WARNING: 5000,
            NotificationType.ERROR: 7000,
            NotificationType.NOTIFY: 5000
        }

        notification: Notification = Notification(title, description, notification_type)
        notification_widget: _NotificationWidget = _NotificationWidget(notification, False, self.notification_parent)
        notification_widget.clicked.connect(lambda n=notification_widget: self._hide_notification(n))
        self.showed_notifications.append(notification_widget)
        self.all_notifications.append(notification)
        self.position_notifications()
        self.all_notifications_dialog.fill_notifications(self.all_notifications)
        self.notification_amount_changed.emit(len(self.all_notifications))
        notification_widget.show()
        QTimer.singleShot(notification_type_to_duration[notification_type],
                          lambda: self._hide_notification(notification_widget))

    def show_all_notifications(self):
        self.all_notifications_dialog.fill_notifications(self.all_notifications)
        self.all_notifications_dialog.show()

    def delete_all_notifications(self):
        for notification in list(self.all_notifications):
            self._delete_notification(notification)
        self.all_notifications_dialog.clear_all_widgets()