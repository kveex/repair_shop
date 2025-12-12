from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, \
    QTextEdit, QDialog, QGroupBox, QListWidget, QListWidgetItem, QHBoxLayout

from src.database.services.service import Service
from src.database.services.worker import Worker
from src.ui import CardListWidget
from PySide6.QtCore import Qt
from qasync import asyncSlot

from src.database import get_order_manager, get_service_manager
from src.database.services.order import Order
from src.database.services.client import ClientNotExistsError
from src.ui import check_errors, check_empty_fields

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
        new_order_button.clicked.connect(self.on_new_order_button_press)

        self.new_order_screen = NewOrderScreen()
        self.info_dialog = QDialog(self)

        main_layout.addWidget(self.card_list)
        main_layout.addWidget(new_order_button)

        self.setLayout(main_layout)

    @asyncSlot()
    async def on_new_order_button_press(self):
        # await self.new_order_screen.on_show()
        self.new_order_screen.show()

    def on_card_press(self, order: Order):
        self.info_dialog = _FullOrderInfoOld(order)
        self.info_dialog.open()

    @asyncSlot()
    async def on_show(self, worker: Worker):
        order_manager = get_order_manager()
        self.info: list[Order] = await order_manager.get_all_orders()
        for order in self.info:
            client_name = order.client.name
            services = order.services
            services_count = len(services)
            service_name = services[0].name
            service_name += f"+{services_count - 1}" if services_count > 1 else ""
            service_price = order.full_price or "Нет точной"
            # self.card_list.create_card(client_name, service_name, str(service_price), order,
            #                            lambda _, o=order: self.on_card_press(o))
            self.card_list.create_card(client_name, service_name, order,
                                       lambda _, o=order: self.on_card_press(o),
                                       str(service_price))

class _FullOrderInfoOld(QDialog):
    def __init__(self, order: Order):
        super().__init__()
        #TODO: Сделать расчёт стоимости в зависимости от добавленных услуг
        self.setWindowTitle("Иформация о заказе")

        layout = QVBoxLayout()

        client_name_label = QLabel(f"Фио клиента: {order.client.name}")
        client_phone_label = QLabel(f"Номер клиента: {order.client.phone}")
        client_address = order.client.address or "не выдан"
        client_address_label = QLabel(f"Адресс клиента: {client_address}")

        # service_name_label = QLabel(f"Услуга: {order.service.name}")
        # service_desc_label = QLabel(f"Описание услуги: {order.service.description}")
        service_price = order.full_price or "нет точной, до завершения заказа"
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

        # layout.addWidget(service_name_label)
        # layout.addWidget(service_desc_label)
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
        self.layout.addWidget(self.trouble_description)
        self.layout.addWidget(create_button)

        self.setLayout(self.layout)

    @asyncSlot()
    async def create_order(self):
        order_manager = get_order_manager()
        created: bool = False

        try:
            # errors = await acheck_errors([self.client_phone, self.trouble_description], self.error_label)
            # if errors:
            #     return
            created = await order_manager.make_order(self.client_phone.text(), self.trouble_description.toPlainText())

        except ClientNotExistsError:
            self.error_label.setText("Клиент не найден, давайте добавим нового")
            self.error_label.show()
            self.client_name.show()
            self.client_address.show()
            if self.client_name.text():
                result = await order_manager.make_order_new_client(self.client_name.text(), self.client_phone.text(), self.client_address.text(), self.trouble_description.toPlainText())
                created = result[1]

        except ValueError:
            self.error_label.setText("Номер телефона слишком длинный или короткий!")
            self.error_label.show()
            return
        if created:
            self.error_label.setText("Заказ создан!")
            self.error_label.show()