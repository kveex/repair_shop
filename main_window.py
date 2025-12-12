from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from src.database import init_db
import sys, asyncio
from qasync import QEventLoop

from src.ui.cashier_screen import CashierScreen
from src.ui.login_screen import LoginScreen
from src.ui.manager_screen import ManagerScreen
from src.ui.register_screen import RegisterScreen
from src.ui.storager_screen import StoragerScreen
from src.ui.tecnitian_screen import TechnicianScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервис ремонта — вход")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        login_screen = LoginScreen(self.stack)
        manager_screen = ManagerScreen(self.stack)
        technician_screen = TechnicianScreen(self.stack)
        storager_screen = StoragerScreen(self.stack)
        cashier_screen = CashierScreen(self.stack)
        register_screen = RegisterScreen(self.stack)

        self.stack.addWidget(login_screen)
        self.stack.addWidget(manager_screen)
        self.stack.addWidget(cashier_screen)
        self.stack.addWidget(technician_screen)
        self.stack.addWidget(storager_screen)
        self.stack.addWidget(register_screen)

        self.stack.setCurrentIndex(0)

        self.stack.currentChanged.connect(self.on_widget_change)

    def on_widget_change(self):
        index = self.stack.currentIndex()

        screen_to_name = {
            0: "Сервис ремонта - вход",
            1: "Панель управления менеджера",
            2: "Список заказов",
            3: "Выбор заказов",
        }

        if index in screen_to_name:
            self.setWindowTitle(screen_to_name[index])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    async def main():
        asyncio.create_task(init_db())
        await app_close_event.wait()

    asyncio.run(main(), loop_factory=QEventLoop)