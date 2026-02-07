from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QPushButton,
    QLineEdit, QVBoxLayout, QSpacerItem,
    QSizePolicy, QHBoxLayout
)
from database.services.worker import LoginMatchError
from src.ui import InputBox
from src.database import get_worker_manager
from qasync import asyncSlot

from utils import NotificationManager, NotificationType


class RegisterScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget, notification_manager: NotificationManager):
        super().__init__()
        self.stack_widget = stack_widget
        self._notification_manager = notification_manager

        main_layout = QHBoxLayout(self)

        inner_layout = QVBoxLayout()

        self._name_input_box = InputBox("ФИО пользователя", on_change=self._validate_inputs)
        self._login_input_box = InputBox("Логин", on_change=self._validate_inputs)
        self._password_input_box = InputBox("Пароль", echo_mode=QLineEdit.EchoMode.Password, on_change=self._validate_inputs)
        self._password_validate_input_box = InputBox("Подтвердить пароль", echo_mode=QLineEdit.EchoMode.Password, on_change=self._validate_inputs)

        self._register_button = QPushButton("Создать аккаунт")
        self._register_button.clicked.connect(self.register)
        self._register_button.setEnabled(False)

        return_back_button = QPushButton("Назад")
        return_back_button.clicked.connect(lambda: self.stack_widget.setCurrentIndex(0))

        inner_layout.addStretch(1)
        inner_layout.addWidget(self._name_input_box)
        inner_layout.addWidget(self._login_input_box)
        inner_layout.addWidget(self._password_input_box)
        inner_layout.addWidget(self._password_validate_input_box)

        inner_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))

        inner_layout.addWidget(self._register_button)
        inner_layout.addWidget(return_back_button)
        inner_layout.addStretch(1)

        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))
        main_layout.addLayout(inner_layout)
        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))

    def _validate_inputs(self):
        name: str = self._name_input_box.get_value()
        login: str = self._login_input_box.get_value()
        password: str = self._password_input_box.get_value()
        password_validate: str = self._password_validate_input_box.get_value()

        enabled = True if name != "" and login != "" and password != "" and password_validate != "" else False

        self._register_button.setEnabled(enabled)

    @asyncSlot()
    async def register(self):
        name: str = self._name_input_box.get_value()
        login: str = self._login_input_box.get_value()
        password: str = self._password_input_box.get_value()
        password_validate: str = self._password_validate_input_box.get_value()

        worker_manager = get_worker_manager()

        if password != password_validate:
            self._notification_manager.show_notification("Ошибка", "Пароли не совпадают!", NotificationType.ERROR)
            self._password_input_box.clear_input()
            self._password_validate_input_box.clear_input()
            return

        try:
            worker = await worker_manager.register_worker(name, login, password)
        except LoginMatchError as e:
            self._notification_manager.show_notification("Ошибка", str(e), NotificationType.WARNING)
            return

        if worker:
            self._notification_manager.show_notification("Успех", f"Аккаунт {worker.name} создан!", NotificationType.SUCCESS)
            self.stack_widget.setCurrentIndex(0)
            return
        else:
            self._notification_manager.show_notification("Ошибка", "Что-то пошло не так во время создания аккаунта, попробуйте в другой раз", NotificationType.ERROR)
            return