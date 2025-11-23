from PySide6.QtWidgets import QWidget, QStackedWidget, QTableWidget, QVBoxLayout, QTableWidgetItem, QScrollArea
from PySide6.QtCore import Qt
from src.database import order_manager
from src.ui import CardWidget

class CashierScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Кассир")

        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        scroll.setWidget(self.container)

        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def on_show(self):
        self.fill_orders()

    def fill_orders(self):
        orders_data = order_manager.get_all_orders()

        for order in orders_data:
            card = CardWidget((order[0], order[3], order[5]), orders_data)
            self.layout.addWidget(card)
        for i in range(20):
            card = CardWidget(("Клиент " + str(i), "Услуга", 1000 + i), orders_data)
            self.layout.addWidget(card)