from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QStackedWidget, QSpacerItem,
    QSizePolicy, QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt
from qasync import asyncSlot

from src.database.services.worker import WrongCredentialsError
from src.ui import Screens, Roles, check_empty_fields
from src.database import get_worker_manager

class LoginScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Вход")
        main_layout = QHBoxLayout()
        layout = QVBoxLayout()

        self.error_label = QLabel("Все поля должны быть заполнены!")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.login)

        layout.addWidget(self.error_label)
        layout.addSpacerItem(QSpacerItem(20, 200, QSizePolicy.Policy.Expanding))
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addSpacerItem(QSpacerItem(20, 200, QSizePolicy.Policy.Expanding))

        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))
        main_layout.addLayout(layout)
        main_layout.addSpacerItem(QSpacerItem(90, 40, QSizePolicy.Policy.MinimumExpanding))

        self.setLayout(main_layout)

    @asyncSlot()
    async def login(self):
        self.login_button.setEnabled(False)
        worker_manager = get_worker_manager()
        error: bool = await check_empty_fields([self.login_input, self.password_input], self.error_label)

        if error:
            self.login_button.setEnabled(True)
            return

        debug: bool = False
        role_to_screen = {
            Roles.MANAGER.value: Screens.MANAGER_SCREEN.value,
            Roles.CASHIER.value: Screens.CASHIER_SCREEN.value,
            Roles.TECHNICIAN.value: Screens.TECHNICIAN_SCREEN.value,
            Roles.STORAGER.value: Screens.STORAGER_SCREEN.value
        }

        if debug:
            role = "Кассир"
            screen_index = role_to_screen[role]
            target_screen = self.stack_widget.widget(screen_index)

            if hasattr(target_screen, "on_show"):
                target_screen.on_show()
            self.stack_widget.setCurrentIndex(screen_index)
            self.setWindowTitle(target_screen.windowTitle())
            return

        try:
            account = await worker_manager.login_worker(self.login_input.text(), self.password_input.text())
        except WrongCredentialsError:
            self.error_label.setText("Неверный логин или пароль!")
            self.login_button.setEnabled(True)
            return

        role: str = account.role

        if role in role_to_screen:
            screen_index = role_to_screen[role]
            target_screen = self.stack_widget.widget(screen_index)
            print(f"Role: {role}, Screen index: {screen_index}, Target screen: {target_screen}")

            if hasattr(target_screen, "on_show"):
                await target_screen.on_show(account)
            self.stack_widget.setCurrentIndex(screen_index)

        self.login_button.setEnabled(True)
