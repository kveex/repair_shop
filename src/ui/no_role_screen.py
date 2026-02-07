from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class NoRoleScreen(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        info_label = QLabel("У вас нет назначенной роли. Ожидайте, пока один из Менеджеров вам её назначит. Вам придётся перезайти в аккаунт для обновления страницы", wordWrap=True)
        main_layout.addWidget(info_label)