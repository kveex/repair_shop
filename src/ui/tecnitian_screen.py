from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QDialog, QGridLayout, QHBoxLayout, QTabWidget
from src.database import order_manager
from src.ui import CardListWidget


class TechnicianScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.layout = QVBoxLayout()

        self.tab = QTabWidget()

        self.not_taken_orders: list = []
        self.worker_orders: list = []

        self.card_list: CardListWidget = CardListWidget()

        self.setLayout(self.layout)

    def on_show(self):
        self._get_not_taken_orders()

    def _get_not_taken_orders(self):
        orders = order_manager.get_all_orders()

        for order in orders:
            if not order[6]:
                self.not_taken_orders.append(order)

    def _get_workers_orders(self):
        pass

class _OrderInfo(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()



        self.setLayout(self.layout)