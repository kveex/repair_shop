from PySide6.QtWidgets import QApplication, QStackedWidget, QMainWindow
from screens.login_screen import LoginScreen
from screens.test_screen import TestScreen
from screens.register_screen import RegisterScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервис ремонта — вход")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen(self.stack)
        self.test_screen = TestScreen(self.stack)
        self.register_screen = RegisterScreen(self.stack)

        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.test_screen)
        self.stack.addWidget(self.register_screen)

        self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())