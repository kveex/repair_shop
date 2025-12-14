from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, \
    QTextEdit, QDialog, QGroupBox, QListWidget, QListWidgetItem, QHBoxLayout, QGridLayout

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
        self.info_dialog = _FullOrderInfo(order)
        self.info_dialog.open()

    @asyncSlot()
    async def on_show(self, worker: Worker):
        order_manager = get_order_manager()
        self.info: list[Order] = await order_manager.get_all_orders()
        for order in self.info:
            print(order)
            client_name = order.client.name
            services = order.services
            services_count = len(services) or 0
            service_name = services[0].name
            service_name += f"+{services_count - 1}" if services_count > 1 else ""
            service_price = order.full_price or "Нет точной"
            # self.card_list.create_card(client_name, service_name, str(service_price), order,
            #                            lambda _, o=order: self.on_card_press(o))
            self.card_list.create_card(client_name, service_name, order,
                                       lambda _, o=order: self.on_card_press(o),
                                       str(service_price))

class InfoBox(QWidget):  # Наследуемся от QWidget, не от QVBoxLayout
    def __init__(self, label_text: str, value_text: str, parent=None, hex_color: str = "#f0f0f0", multi_line=False):
        super().__init__(parent)

        # Создаём основной layout для этого виджета
        layout = QVBoxLayout(self)
        layout.setSpacing(3)  # Промежуток между label и field (3 пикселя)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы контейнера

        # Label
        self.label = QLabel(label_text)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #555;
                padding-bottom: 2px;
            }
        """)

        if multi_line:
            self.value = QTextEdit(value_text)
            self.value.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value = QLineEdit(value_text)
        # Value field (только для чтения, серый фон)

        self.value.setReadOnly(True)
        self.value.setStyleSheet(f"""
            QLineEdit {{
                background-color: {hex_color};
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #333;
            }}
            QTextEdit {{
                background-color: {hex_color};
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #333;
            }}
        """)

        layout.addWidget(self.label)
        layout.addWidget(self.value)


class _FullOrderInfo(QDialog):
    def __init__(self, order: Order):
        super().__init__()
        self.order = order
        self.setMinimumWidth(500)
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)  # Отступ между блоками
        left_layout.setContentsMargins(20, 20, 20, 20)

        client_name_box = InfoBox("ФИО клиента:", order.client.name)
        client_phone_box = InfoBox("Номер клиента:", order.client.phone)
        client_address_box = InfoBox("Адрес клиента:", order.client.address or "Не указан")
        service_list_label = QLabel("Список услуг:")
        services_list = QListWidget()
        services_list.setStyleSheet("background-color: #f0f0f0;")
        for service in order.services:
            item = QListWidgetItem(service.name)
            item.setToolTip(f"{service.price}₽" or "Нет точной")
            services_list.addItem(item)
        services_price = 0
        for service in order.services:
            services_price += service.price or 0
        services_price_box = InfoBox("Общая цена услуг:", str(services_price), hex_color="#0dbc5f")

        accept_date_box = InfoBox("Дата принятия заказа:", order.accept_date)
        finish_date_box = InfoBox("Дата завершения заказа: ", order.finish_date)

        left_layout.addWidget(client_name_box)
        left_layout.addWidget(client_phone_box)
        left_layout.addWidget(client_address_box)
        left_layout.addWidget(service_list_label)
        left_layout.addWidget(services_list)
        left_layout.addWidget(services_price_box)
        left_layout.addWidget(accept_date_box)
        left_layout.addWidget(finish_date_box)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        left_layout.addWidget(close_btn)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_grid_layout = QGridLayout()
        worker = order.worker
        worker_name = "Не назначен" if not worker else worker.name
        worker_name_box = InfoBox("Назначенный сотрудник:", worker_name)
        order_statue_box = InfoBox("Статус заказа:", order.status)
        right_grid_layout.addWidget(worker_name_box, 0, 0)
        right_grid_layout.addWidget(order_statue_box, 0, 1)
        trouble_description = InfoBox("Описание проблемы:", order.trouble_description, multi_line=True)
        right_layout.addLayout(right_grid_layout)
        right_layout.addWidget(trouble_description)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

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