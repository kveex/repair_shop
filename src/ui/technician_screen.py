import asyncio
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QDialog
from PySide6.QtCore import Qt
import src.database as db
from qasync import asyncSlot

from src.database.services.order import Order
from src.database.services.worker import Worker
from src.ui import CardListWidget, ServiceSelectBox

class TechnicianScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.order_manager = None
        self.worker = None
        self.order = None
        self.not_taken_orders: list = []
        self.not_taken_orders_card_list = None

    def init_order_list_ui(self):
        layout = QVBoxLayout(self)

        self.not_taken_orders_card_list = CardListWidget()

        layout.addWidget(self.not_taken_orders_card_list)

    def init_selected_order_ui(self, order: Order):
        layout = QVBoxLayout(self)

        device_type = QLabel(order.device_type)
        services_box = ServiceSelectBox("Оказанные услуги:")
        if order.services:
            for service in order.services:
                services_box.add_service(service, True)

        layout.addWidget(device_type, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(services_box)

    @asyncSlot()
    async def on_show(self, worker: Worker):
        self.worker = worker
        self.order_manager = db.get_order_manager()
        worker_orders: list[Order] = await self.order_manager.get_workers_orders(worker)

        if not worker_orders:
            self.init_order_list_ui()
            while self.isVisible():
                await self.get_not_taken_orders()
                await asyncio.sleep(30)
        else:
            for order in worker_orders:
                if order.is_finished(): continue
                self.init_selected_order_ui(order)
                return

    async def get_not_taken_orders(self):
        self.not_taken_orders = await self.order_manager.get_not_taken_orders()
        for order in self.not_taken_orders:
            if order.is_finished():
                self.not_taken_orders_card_list.sync_card(
                    card_name=order.get_service_names(False),
                    card_desc=order.trouble_description,
                    full_card_info=order,
                    func=lambda _, o=order: print(o)
                )


class GetOrderDialog(QDialog):
    def __init__(self, order: Order):
        super().__init__()

        service_name  = QLabel("Услуга")
        trouble_desc = QLabel(f"Описание проблемы: {order.trouble_description}")


