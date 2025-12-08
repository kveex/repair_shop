from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QPushButton,
    QLineEdit, QVBoxLayout, QLabel, QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt
from src.database import worker_manager
from src.ui import Screens

class RegisterScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget

        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ФИО")

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.validate_password_input = QLineEdit()
        self.validate_password_input.setPlaceholderText("Подтвердите пароль")
        self.validate_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # 🟥 Метка ошибки
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()  # по умолчанию скрыта

        register_button = QPushButton("Создать аккаунт")
        register_button.clicked.connect(self.register)

        # 🔗 Подключаем события ввода для всех полей
        self.name_input.textChanged.connect(self.reset_error_state)
        self.login_input.textChanged.connect(self.reset_error_state)
        self.password_input.textChanged.connect(self.reset_error_state)
        self.validate_password_input.textChanged.connect(self.reset_error_state)

        # 📦 Добавляем элементы
        layout.addWidget(self.name_input)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.validate_password_input)
        layout.addWidget(self.error_label)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding)
        layout.addSpacerItem(spacer)

        layout.addWidget(register_button)

    # 🔍 Проверка на пустые поля
    def validate_inputs(self) -> bool:
        inputs = [self.name_input, self.login_input, self.password_input, self.validate_password_input]
        valid = True

        for inp in inputs:
            if not inp.text().strip():
                inp.setStyleSheet("border: 2px solid red; border-radius: 6px;")
                valid = False
            else:
                inp.setStyleSheet("")  # убираем рамку если поле ок

        if not valid:
            self.error_label.setText("❌ Заполните все поля")
            self.error_label.show()

        return valid

    # ⚙️ Основной метод регистрации
    def register(self):
        if not self.validate_inputs():
            return

        if self.password_input.text() != self.validate_password_input.text():
            self.error_label.setText("❌ Пароли не совпадают")
            self.error_label.show()
            self.password_input.setStyleSheet("border: 2px solid red; border-radius: 6px;")
            self.validate_password_input.setStyleSheet("border: 2px solid red; border-radius: 6px;")
            return

        # ✅ Если всё ок — пробуем создать аккаунт
        worker_manager.register_worker(
            self.name_input.text(),
            self.login_input.text(),
            self.password_input.text()
        )

        self.error_label.setText("✅ Аккаунт успешно создан!")
        self.error_label.setStyleSheet("color: green; font-size: 14px;")
        self.error_label.show()
        self.stack_widget.setCurrentIndex(Screens.LOGIN_SCREEN.value)

    # 🔄 Убирает ошибки при вводе
    def reset_error_state(self):
        sender = self.sender()
        sender.setStyleSheet("")  # убираем красную рамку

        # Если все поля заполнены — скрываем ошибку
        if all([self.name_input.text().strip(),
                self.login_input.text().strip(),
                self.password_input.text().strip(),
                self.validate_password_input.text().strip()]):
            self.error_label.hide()
