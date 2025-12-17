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
        order_manager = db.get_order_manager()
        self.worker_orders = await order_manager.get_workers_orders(worker)
        self.not_taken_orders = await order_manager.get_not_taken_orders()
        for order in self.not_taken_orders:
            self.not_taken_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=self.not_taken_orders,
                func=lambda: print("a"),
            )
        for order in self.worker_orders:
            self.worker_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=self.not_taken_orders,
                func=lambda: print("a"),
            )

class GetOrderDialog(QDialog):
    def __init__(self, order: Order):
        super().__init__()

        service_name  = QLabel("Услуга")
        trouble_desc = QLabel(f"Описание проблемы: {order.trouble_description}")


