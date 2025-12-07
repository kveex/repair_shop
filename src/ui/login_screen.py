from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QStackedWidget, QSpacerItem,
    QSizePolicy, QLabel
)
from PySide6.QtCore import Qt

from src.database import account_manager
from src.ui import Screens, Roles, check_errors


class LoginScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Вход")
        layout = QVBoxLayout()

        self.error_label = QLabel("Все поля должны быть заполнены!")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)

        layout.addWidget(self.error_label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding))
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        check_errors([self.login_input, self.password_input], self.error_label)
        debug: bool = True
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

        account = account_manager.login_worker(self.login_input.text(), self.password_input.text())

        role: str = account.role

        if role in role_to_screen:
            screen_index = role_to_screen[role]
            target_screen = self.stack_widget.widget(screen_index)

            if hasattr(target_screen, "on_show"):
                target_screen.on_show()
            self.stack_widget.setCurrentIndex(screen_index)
