from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QStackedWidget, QSpacerItem,
    QSizePolicy
)

from src.database import account_manager
from src.ui import Screens

class LoginScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Вход")
        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)

        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding))
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        if account_manager.login_account(self.login_input.text(), self.password_input.text()):
            self.stack_widget.setCurrentIndex(Screens.REGISTER_SCREEN.value)
