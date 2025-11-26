from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QScrollArea, QLineEdit
from PySide6.QtCore import Qt
from src.database import order_manager
from src.ui import CardWidget

class CashierScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.setWindowTitle("Кассир")
        self.stack_widget = stack_widget

        main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.search = QLineEdit()
        self.search.textChanged.connect(self.search_card)

        self.scroll.setWidget(self.container)

        main_layout.addWidget(self.search)
        main_layout.addWidget(self.scroll)

        self.setLayout(main_layout)

    def on_show(self):
        self.fill_orders()

    def search_card(self, _=None):
        q = self.search.text().strip().lower()
        cards = self.scroll.findChildren(CardWidget, "cardWidget", Qt.FindChildOption.FindChildrenRecursively)
        if not cards:
            return

        if q == "":
            for card in cards:
                card.show()
            return

        for card in cards:
            info_list = card.info
            visible = any(q in str(field).lower() for field in info_list)
            card.setVisible(visible)

    def fill_orders(self):
        orders_data = order_manager.get_all_orders()
        count = 0

        for order in orders_data:
            card = CardWidget((order[0], order[3], order[5]), orders_data[count])
            self.layout.addWidget(card)
            count += 1
        for i in range(20):
            card = CardWidget(("Клиент " + str(i), "Услуга", 1000 + i), [str(count)])
            self.layout.addWidget(card)
            count += 1