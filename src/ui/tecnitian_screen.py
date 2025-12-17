import asyncio

from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QDialog, QGridLayout, QHBoxLayout, QTabWidget
import src.database as db
from qasync import asyncSlot

from src.database.services.order import Order
from src.database.services.worker import Worker
from src.ui import CardListWidget

class TechnicianScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.order_manager = None
        self.worker = None
        self.layout = QVBoxLayout()
        self.orders = []

        self.tab = QTabWidget()

        self.not_taken_orders: list = []
        self.worker_orders: list = []

        self.worker_orders_card_list: CardListWidget = CardListWidget()
        self.not_taken_orders_card_list: CardListWidget = CardListWidget()

        self.tab.addTab(self.not_taken_orders_card_list, "Все заказы")
        self.tab.addTab(self.worker_orders_card_list, "Ваши заказы")

        self.layout.addWidget(self.tab)
        self.setLayout(self.layout)

    @asyncSlot()
    async def on_show(self, worker: Worker):
        self.worker = worker
        self.order_manager = db.get_order_manager()
        while self.isVisible():
            await self.get_not_taken_orders()
            await self.get_worker_orders()
            await asyncio.sleep(30)

    async def get_worker_orders(self):
        self.worker_orders = await self.order_manager.get_workers_orders(self.worker)
        for order in self.worker_orders:
            self.worker_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=order,
                func=lambda: print("a"),
            )

    async def get_not_taken_orders(self):
        self.not_taken_orders = await self.order_manager.get_not_taken_orders()
        for order in self.not_taken_orders:
            self.not_taken_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=order,
                func=lambda: print("a"),
            )
class GetOrderDialog(QDialog):
    def __init__(self, order: Order):
        super().__init__()

        service_name  = QLabel("Услуга")
        trouble_desc = QLabel(f"Описание проблемы: {order.trouble_description}")


