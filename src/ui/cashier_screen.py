import asyncio

from PySide6.QtWidgets import (QWidget, QStackedWidget,
                               QVBoxLayout, QPushButton, QLabel,
                               QComboBox, QDialog,
                               QHBoxLayout, QGridLayout)

from src.utils import validate_phone, format_phone_for_display, WrongPhoneCode, PhoneLengthError, PhoneValidationError
from src.ui import CardListWidget, InfoBox, InputBox, ServiceInfoBox, ServiceSelectBox
from PySide6.QtCore import Qt
from qasync import asyncSlot

from src.database import get_order_manager, get_service_manager
from src.database.services.order import Order, priority_to_name, priority_to_color
from src.database.services.client import ClientNotExistsError

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
        self.order_manager = None

        main_layout = QVBoxLayout(self)

        self.card_list = CardListWidget()

        self.new_order_screen = NewOrder(self)
        self.info_dialog = QDialog(self)

        new_order_button = QPushButton()
        new_order_button.setText("Новый заказ")
        new_order_button.clicked.connect(self.new_order_screen.open)

        main_layout.addWidget(self.card_list)
        main_layout.addWidget(new_order_button)

        self.setLayout(main_layout)

    def on_card_press(self, order: Order):
        self.info_dialog = FullOrderInfo(order)
        self.info_dialog.open()

    async def fill_cards(self):
        self.info: list[Order] = await self.order_manager.get_all_orders()
        for order in self.info:
            client_name = order.client.name
            service_name = order.get_service_names()
            service_price = order.get_full_price()
            service_price_str = f"{service_price}₽" if service_price else "Нет точной цены"
            self.card_list.sync_card(
                client_name, service_name, order,
                lambda _, o=order: self.on_card_press(o),
                service_price_str
            )

    @asyncSlot()
    async def on_show(self):
        self.order_manager = get_order_manager()
        await self.new_order_screen.fill_services_box()
        while self.isVisible():
            await self.fill_cards()
            await asyncio.sleep(30)

class FullOrderInfo(QDialog):
    def __init__(self, order: Order):
        super().__init__()
        self.order = order
        self.setMinimumWidth(500)
        self.setWindowTitle("Информация о заказе")
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)

        client_name_box = InfoBox("ФИО клиента:", order.client.name)
        phone: str = format_phone_for_display(order.client.phone)
        client_phone_box = InfoBox("Номер клиента:", phone)
        client_address_box = InfoBox("Адрес клиента:", order.client.address or "Не указан")
        services_box = ServiceInfoBox("Список услуг:", order.services)
        services_price = order.get_full_price()
        services_price_str: str = f"{services_price}₽" if services_price else "Нет точной цены"
        services_price_box = InfoBox("Общая цена услуг:", services_price_str)
        priority_name: str = priority_to_name[order.priority]
        priority_color: str = priority_to_color[order.priority]
        priority_box = InfoBox("Приоритет заказа:", priority_name, hex_color=priority_color)

        left_layout.addWidget(client_name_box)
        left_layout.addWidget(client_phone_box)
        left_layout.addWidget(client_address_box)
        left_layout.addWidget(services_box)
        left_layout.addWidget(services_price_box)
        left_layout.addWidget(priority_box)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        left_layout.addWidget(close_btn)

        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(15)
        middle_layout.setContentsMargins(20, 20, 20, 20)

        device_type_box = InfoBox("Тип устройства:", order.device_type)
        device_brand_box = InfoBox("Бренд устройства:", order.device_brand)
        device_model_box = InfoBox("Модель устройства:", order.device_model)
        accept_date_box = InfoBox("Дата принятия заказа:", order.accept_date)
        finish_date_box = InfoBox("Дата завершения заказа: ", order.finish_date)

        middle_layout.addWidget(device_type_box)
        middle_layout.addWidget(device_brand_box)
        middle_layout.addWidget(device_model_box)
        middle_layout.addWidget(accept_date_box)
        middle_layout.addWidget(finish_date_box)

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

        technician_notes_box = InfoBox("Заметки техника:", order.technician_notes, multi_line=True)
        trouble_description_box = InfoBox("Описание проблемы:", order.trouble_description, multi_line=True)

        right_layout.addLayout(right_grid_layout)
        right_layout.addWidget(technician_notes_box)
        right_layout.addWidget(trouble_description_box)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

class NewOrder(QDialog):
    def __init__(self, parent: CashierScreen):
        super().__init__()
        self.parent = parent
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        close_button = QPushButton()
        close_button.setText("Отмена")
        close_button.clicked.connect(self.close)
        self.create_button = QPushButton()
        self.create_button.setText("Создать")
        self.create_button.clicked.connect(self.create_order)
        self.create_button.setEnabled(False)

        self.setWindowTitle("Новый заказ")
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.client_name_box = InputBox("ФИО клиента:")
        self.client_name_box.hide()
        self.client_name_box.value_input.textChanged.connect(self.check_fields)

        self.client_address_box = InputBox("Адрес клиента (не обязательно):")
        self.client_address_box.hide()

        self.client_phone_box = InputBox("Номер телефона клиента:")
        self.client_phone_box.value_input.textChanged.connect(self.check_fields)

        self.trouble_description_box = InputBox("Описание проблемы:", multi_line=True)
        self.trouble_description_box.value_input.textChanged.connect(self.check_fields)

        left_layout.addWidget(self.error_label)
        left_layout.addWidget(self.client_name_box)
        left_layout.addWidget(self.client_phone_box)
        left_layout.addWidget(self.client_address_box)
        left_layout.addWidget(self.trouble_description_box)
        left_layout.addWidget(close_button)

        right_layout = QVBoxLayout()

        self.device_type_box = InputBox("Тип устройства:")
        self.device_brand_box = InputBox("Бренд устройства:")
        self.device_model_box = InputBox("Модель устройства:")
        priority_label = QLabel("Приоритет заказа: ")
        priority_label.setStyleSheet("font-size: 12px; color: #555; padding-bottom: 2px;")
        self.services_box = ServiceSelectBox("Возможные услуги для оказания:")
        self.priority_box = QComboBox()
        for priority, display_name in priority_to_name.items():
            self.priority_box.addItem(display_name, priority)
        self.priority_box.setCurrentIndex(0)

        right_layout.addWidget(self.device_type_box)
        right_layout.addWidget(self.device_brand_box)
        right_layout.addWidget(self.device_model_box)
        right_layout.addWidget(self.services_box)
        #TODO: Переделать priority в отдельный виджет
        right_layout.addWidget(priority_label)
        right_layout.addWidget(self.priority_box)
        right_layout.addWidget(self.create_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

    async def fill_services_box(self):
        service_manager = get_service_manager()
        services: list = await service_manager.get_all_services()

        for service in services:
            self.services_box.add_service(service, False, lambda: self.check_fields())

    def check_fields(self):
        client_phone = self.client_phone_box.get_value()
        trouble_desc = self.trouble_description_box.get_value()
        client_name = self.client_name_box.get_value()
        requested_services = self.services_box.get_checked_services()
        if self.client_name_box.isHidden():
            enabled = True if client_phone and trouble_desc and requested_services else False
        else:
            enabled = True if client_phone and client_name and trouble_desc and requested_services else False
        self.error_label.hide()
        self.create_button.setEnabled(enabled)

    @asyncSlot()
    async def create_order(self):
        order_manager = get_order_manager()
        error_msg: str = ""
        client_name: str = self.client_name_box.get_value()
        client_phone: str = self.client_phone_box.get_value()
        client_address: str = self.client_address_box.get_value()
        trouble_desc: str = self.trouble_description_box.get_value()
        device_type: str = self.device_type_box.get_value()
        device_brand: str = self.device_brand_box.get_value()
        device_model: str = self.device_model_box.get_value()
        requested_services: list = self.services_box.get_checked_services()
        order_priority: int = self.priority_box.currentData()

        try:
            client_phone = validate_phone(client_phone)
        except WrongPhoneCode and PhoneLengthError and PhoneValidationError as e:
            error_msg = str(e)

        if error_msg:
            self.error_label.setText(error_msg)
            self.error_label.show()
            return

        try:
            created: bool = await order_manager.make_order(
                client_phone=client_phone,
                trouble_description=trouble_desc,
                device_type=device_type,
                device_brand=device_brand,
                device_model=device_model,
                requested_services=requested_services,
                priority=order_priority,
            )
        except ClientNotExistsError as e:
            self.error_label.setText(str(e))
            self.client_name_box.show()
            self.client_address_box.show()
            result = await order_manager.make_order_new_client(
                client_name,
                client_phone,
                client_address,
                trouble_desc,
                device_type,
                device_brand,
                device_model,
                requested_services,
                order_priority
            )
            created = result[1]

        if created:
            self.error_label.setText("Заказ успешно создан!")
            self.client_name_box.clear_input()
            self.client_phone_box.clear_input()
            self.client_address_box.clear_input()
            self.trouble_description_box.clear_input()
            self.device_type_box.clear_input()
            self.device_brand_box.clear_input()
            self.device_model_box.clear_input()
            self.services_box.reset_checks()
            self.priority_box.setCurrentIndex(0)
            self.client_name_box.hide()
            self.client_address_box.hide()

        self.error_label.show()
        self.create_button.setEnabled(False)

        await self.parent.fill_cards()
