from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QStyleFactory

from database import WorkerManager
from src.database import init_db, get_worker_manager, get_supabase_sync
import sys
import asyncio
from qasync import QEventLoop
from qt_material import apply_stylesheet, QtStyleTools

from src.ui.cashier_screen import CashierScreen
from src.ui.login_screen import LoginScreen
from src.ui.manager_screen import ManagerScreen
from src.ui.register_screen import RegisterScreen
from src.ui.storager_screen import StoragerScreen
from src.ui.technician_screen import TechnicianScreen
from src.ui.no_role_screen import NoRoleScreen
from src.ui import MenuBar
from src.utils import NotificationManager


class MainWindow(QMainWindow, QtStyleTools):
    def __init__(self, shutdown_event: asyncio.Event):  # Добавляем параметр
        super().__init__()
        self.shutdown_event = shutdown_event  # Сохраняем событие
        self.setWindowTitle("Сервис ремонта — вход")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.notification_manager = NotificationManager(self)

        self.bar = MenuBar(self.stack, self.notification_manager)
        self.setMenuBar(self.bar)

        login_screen = LoginScreen(self.stack, self.notification_manager)
        manager_screen = ManagerScreen(self.notification_manager)
        technician_screen = TechnicianScreen(self.notification_manager)
        storager_screen = StoragerScreen(self.notification_manager)
        cashier_screen = CashierScreen(self.notification_manager)
        register_screen = RegisterScreen(self.stack, self.notification_manager)
        no_role_screen = NoRoleScreen()

        self.stack.addWidget(login_screen)
        self.stack.addWidget(manager_screen)
        self.stack.addWidget(cashier_screen)
        self.stack.addWidget(technician_screen)
        self.stack.addWidget(storager_screen)
        self.stack.addWidget(register_screen)
        self.stack.addWidget(no_role_screen)

        self.stack.setCurrentIndex(0)
        self.stack.currentChanged.connect(self.on_widget_change)

    def on_widget_change(self):
        index = self.stack.currentIndex()
        screen_to_name = {
            0: "Сервис ремонта - вход",
            1: "Панель управления менеджера",
            2: "Список заказов кассира",
            3: "Выбор заказов техника",
            4: "Список ячеек и запросов",
            5: "Создание аккаунта"
        }
        if index in screen_to_name:
            self.setWindowTitle(screen_to_name[index])

        if index == 0:
            self.bar.logout_action.setEnabled(False)
        else:
            self.bar.logout_action.setEnabled(True)

    def closeEvent(self, event):
        """Переопределяем закрытие окна"""
        event.accept()  # Разрешаем закрытие
        self.shutdown_event.set()  # Сигнализируем async_main о завершении


def main():
    # 1. Создаём QApplication
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="dark_lightgreen.xml")

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