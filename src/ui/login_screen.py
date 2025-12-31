from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QStackedWidget, QSpacerItem,
    QSizePolicy, QHBoxLayout
)
from qasync import asyncSlot

from src.database.services.worker import WrongCredentialsError, Worker
from src.ui import Screens, Roles, NotificationManager, NotificationType, InputBox
from src.database import get_worker_manager

class LoginScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Вход")
        self.notification_manager = NotificationManager(self)
        main_layout = QHBoxLayout()
        layout = QVBoxLayout()

        self.login_input_box = InputBox("Логин")
        self.login_input_box.value_input.textChanged.connect(self.check_fields)

        self.password_input_box = InputBox("Пароль", echo_mode=QLineEdit.EchoMode.Password)
        self.password_input_box.value_input.textChanged.connect(self.check_fields)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.login)
        self.login_button.setEnabled(False)

        layout.addStretch(1)
        layout.addWidget(self.login_input_box)
        layout.addWidget(self.password_input_box)
        layout.addWidget(self.login_button)
        layout.addStretch(1)

        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))
        main_layout.addLayout(layout)
        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))

        self.setLayout(main_layout)

    def check_fields(self):
        if self.login_input_box.get_value() and self.password_input_box.get_value():
            self.login_button.setEnabled(True)

    @asyncSlot()
    async def login(self):
        role_to_screen = {
            Roles.MANAGER.value: Screens.MANAGER_SCREEN.value,
            Roles.CASHIER.value: Screens.CASHIER_SCREEN.value,
            Roles.TECHNICIAN.value: Screens.TECHNICIAN_SCREEN.value,
            Roles.STORAGER.value: Screens.STORAGER_SCREEN.value
        }

        debug: bool = False
        if debug:
            role = "Техник"
            screen_index = role_to_screen[role]
            target_screen = self.stack_widget.widget(screen_index)

            if hasattr(target_screen, "on_show"):
                target_screen.on_show(Worker("a", role, 1))
            self.stack_widget.setCurrentIndex(screen_index)
            self.setWindowTitle(target_screen.windowTitle())
            return

        worker_manager = get_worker_manager()

        login = self.login_input_box.get_value()
        password = self.password_input_box.get_value()

        try:
            account = await worker_manager.login_worker(login, password)
        except WrongCredentialsError:
            self.notification_manager.show_notification("Ошибка!", "Неверный логин или пароль", NotificationType.ERROR)
            return

        role: str = account.role

        if role in role_to_screen:
            screen_index = role_to_screen[role]
            target_screen = self.stack_widget.widget(screen_index)

            self.stack_widget.setCurrentIndex(screen_index)

            if hasattr(target_screen, "on_show"):
                await target_screen.on_show(account)
