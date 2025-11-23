from PySide6.QtWidgets import QApplication, QStackedWidget, QMainWindow
from screens.login_screen import LoginScreen
from screens.test_screen import TestScreen
from screens.register_screen import RegisterScreen
from screens.cashier_screen import CashierScreen
from screens.manager_screen import ManagerScreen
from screens.storager_screen import StoragerScreen
from screens.tecnitian_screen import TechnicianScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервис ремонта — вход")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        login_screen = LoginScreen(self.stack)
        test_screen = TestScreen(self.stack)
        manager_screen = ManagerScreen(self.stack)
        technician_screen = TechnicianScreen(self.stack)
        storager_screen = StoragerScreen(self.stack)
        cashier_screen = CashierScreen(self.stack)
        register_screen = RegisterScreen(self.stack)

        self.stack.addWidget(login_screen)
        self.stack.addWidget(test_screen)
        self.stack.addWidget(manager_screen)
        self.stack.addWidget(cashier_screen)
        self.stack.addWidget(technician_screen)
        self.stack.addWidget(storager_screen)
        self.stack.addWidget(register_screen)

        self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())