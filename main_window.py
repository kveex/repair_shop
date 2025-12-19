from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from src.database import init_db
import sys
import asyncio
from qasync import QEventLoop

from src.ui import GLOBAL_STYLES
from src.ui.cashier_screen import CashierScreen
from src.ui.login_screen import LoginScreen
from src.ui.manager_screen import ManagerScreen
from src.ui.register_screen import RegisterScreen
from src.ui.storager_screen import StoragerScreen
from src.ui.technician_screen import TechnicianScreen


class MainWindow(QMainWindow):
    def __init__(self, shutdown_event: asyncio.Event):  # Добавляем параметр
        super().__init__()
        self.shutdown_event = shutdown_event  # Сохраняем событие
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

    def closeEvent(self, event):
        """Переопределяем закрытие окна"""
        event.accept()  # Разрешаем закрытие
        self.shutdown_event.set()  # Сигнализируем async_main о завершении


def main():
    # 1. Создаём QApplication
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLES)

    # 2. Создаём Qt-совместимый event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Создаём событие для сигнализации о закрытии
    shutdown_event = asyncio.Event()

    # 4. Передаём событие в MainWindow
    window = MainWindow(shutdown_event)
    window.show()

    async def async_main():
        # 5. Инициализируем БД
        await init_db()

        # 6. Ждём сигнала закрытия окна
        await shutdown_event.wait()

    # 7. Запускаем с корректной очисткой
    try:
        with loop:
            loop.run_until_complete(async_main())
    finally:
        loop.close()


if __name__ == "__main__":
    main()