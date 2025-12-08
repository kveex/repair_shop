from dataclasses import asdict
import json
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, \
    QTextEdit, QDialog
from src.ui import CardListWidget
from PySide6.QtCore import Qt

from src.database import order_manager, service_manager, Order, Service
from src.database.services.client import ClientNotExistsError
from src.ui import check_errors

class CashierScreen(QWidget):
    names = [
        "Фио клиента: ",
        "Номер клиента: ",
        "Адрес клиента: ",
        "Услуга: ",
        "Описание услуги: ",
        "Цена: ",
        "Назначенный техник: ",
        "Описание проблемы: ",
        "Статус: ",
        "Время принятия: ",
        "Время завершения: "
    ]

    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()

        self.info = []
        self.stack_widget = stack_widget

        main_layout = QVBoxLayout(self)

        self.card_list = CardListWidget()

        new_order_button = QPushButton()
        new_order_button.setText("Новый заказ")
        new_order_button.clicked.connect(self.on_button_press)

        self.new_order_screen = NewOrderScreen()
        self.info_dialog = QDialog(self)

        main_layout.addWidget(self.card_list)
        main_layout.addWidget(new_order_button)

        self.setLayout(main_layout)

    def on_button_press(self):
        self.new_order_screen.on_show()
        self.new_order_screen.show()

    def on_card_press(self):
        self.info_dialog.setWindowTitle("Full Info")

        layout = QVBoxLayout()

        flat_info = [item for sub in self.info for item in asdict(sub).items()]

        for name, value in zip(self.names, flat_info):
            label = QLabel(f"{name}{value}")
            label.setWordWrap(True)
            layout.addWidget(label)

        self.info_dialog.setLayout(layout)
        self.info_dialog.open()

    def ocp(self, order: Order):
        self.info_dialog = _FullOrderInfo(order)
        self.info_dialog.open()

    def on_show(self):
        self.info: list[Order] = order_manager.get_all_orders()
        for order in self.info:
            # self.card_list.create_cards(order.client.name, order.service.name, str(order.service.price), order, self.on_card_press)
            self.card_list.create_cards(order.client.name, order.service.name, str(order.service.price), order,
                                        lambda: self.ocp(order))
class _FullOrderInfo(QDialog):
    def __init__(self, order: Order):
        super().__init__()

        self.setWindowTitle("Иформация о заказе")

        layout = QVBoxLayout()

        client_name_label = QLabel(f"Фио клиента: {order.client.name}")
        client_phone_label = QLabel(f"Номер клиента: {order.client.phone}")
        client_address = order.client.address or "не выдан"
        client_address_label = QLabel(f"Адресс клиента: {client_address}")

        service_name_label = QLabel(f"Услуга: {order.service.name}")
        service_desc_label = QLabel(f"Описание услуги: {order.service.description}")
        service_price = order.service.price or "нет точной, до завершения заказа"
        service_price_label = QLabel(f"Цена услуги: {service_price}")
        worker_name = order.worker.name if order.worker is not None else "не назначен"
        worker_name_label = QLabel(f"Имя наначенного сотрудника: {worker_name}")
        trouble_desc_label = QLabel(f"Описание проблемы: {order.trouble_description}")
        status_label = QLabel(f"Статус: {order.status}")
        accept_time_label = QLabel(f"Время принятия: {order.accept_date}")
        finish_time_label = QLabel(f"Время завершения: {order.finish_date}")

        layout.addWidget(client_name_label)
        layout.addWidget(client_phone_label)
        layout.addWidget(client_address_label)

        layout.addWidget(service_name_label)
        layout.addWidget(service_desc_label)
        layout.addWidget(service_price_label)
        layout.addWidget(worker_name_label)
        layout.addWidget(trouble_desc_label)
        layout.addWidget(status_label)
        layout.addWidget(accept_time_label)
        layout.addWidget(finish_time_label)

        self.setLayout(layout)

class NewOrderScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Новый заказ")

        self.layout = QVBoxLayout()

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()

        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("Имя клиента")
        self.client_name.hide()

        self.client_phone = QLineEdit()
        self.client_phone.setPlaceholderText("Номер телефона клиента")

        self.client_address = QLineEdit()
        self.client_address.setPlaceholderText("Адрес доставки клиента (не обязательно)")
        self.client_address.hide()

        self.services = QComboBox()

        self.trouble_description = QTextEdit()
        self.trouble_description.setPlaceholderText("Описание проблемы")

        create_button = QPushButton()
        create_button.setText("Создать заказ")
        create_button.clicked.connect(self.create_order)

        cancel_button = QPushButton()
        cancel_button.setText("Отмена")

        self.layout.addWidget(self.error_label)
        self.layout.addWidget(self.client_name)
        self.layout.addWidget(self.client_phone)
        self.layout.addWidget(self.client_address)
        self.layout.addWidget(self.services)
        self.layout.addWidget(self.trouble_description)
        self.layout.addWidget(create_button)

        self.setLayout(self.layout)

    def on_show(self):
        services_list: list = service_manager.get_all_services()
        for service in services_list:
            self.services.addItem(service[0])

    def create_order(self):
        created: bool = False

        try:
            check_errors([self.client_phone, self.trouble_description], self.error_label)
            created = order_manager.make_order(self.client_phone.text(), self.services.currentText(), self.trouble_description.toPlainText())

        except ClientNotExistsError:
            self.error_label.setText("Клиент не найден, давайте добавим нвоого")
            self.client_name.show()
            self.client_address.show()
            if self.client_name.text():
                created = order_manager.make_order_new_client(self.client_name.text(), self.client_phone.text(), self.client_address.text(), self.services.currentText(), self.trouble_description.toPlainText())[1]

        if created:
            self.error_label.setText("Заказ создан!")
            self.error_label.show()