import asyncio

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout,
                               QPushButton, QLabel, QComboBox,
                               QLineEdit, QTextEdit, QDialog,
                               QListWidget, QListWidgetItem,
                               QHBoxLayout, QGridLayout)

from src.utils import validate_phone, format_phone_for_display, WrongPhoneCode, PhoneLengthError, PhoneValidationError
from src.ui import CardListWidget
from PySide6.QtCore import Qt
from qasync import asyncSlot

from src.database import get_order_manager
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
        order_manager = get_order_manager()
        self.info: list[Order] = await order_manager.get_all_orders()
        for order in self.info:
            client_name = order.client.name
            service_name = order.get_service_names()
            service_price = order.get_full_price() or "Нет точной"
            self.card_list.create_card(client_name, service_name, order,
                                       lambda _, o=order: self.on_card_press(o),
                                       str(service_price))

    @asyncSlot()
    async def on_show(self):
        while self.isVisible():
            await self.fill_cards()
            await asyncio.sleep(30)

class InfoBox(QWidget):
    def __init__(self, label_text: str, value_text: str, parent=None, hex_color: str = "#f0f0f0", multi_line=False):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

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

class InputBox(QWidget):
    def __init__(self, label_text, hex_color: str = "#ffffff", multi_line=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        color: #555;
                        padding-bottom: 2px;
                    }
                """)

        if multi_line:
            self.value_input = QTextEdit()
            self.value_input.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.value_input = QLineEdit()

        self.value_input.setStyleSheet(f"""
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
        layout.addWidget(self.value_input)

    def get_value(self) -> str:
        if hasattr(self.value_input, "toPlainText"):
            text = self.value_input.toPlainText()
        else:
            text = self.value_input.text()
        return text

    def no_input(self) -> bool:
        if not self.get_value():
            self.value_input.setStyleSheet("border: 2px solid red; border-radius: 5px;")
            return True
        return False

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
        service_list_label = QLabel("Список услуг:")
        service_list_label.setStyleSheet("font-size: 12px; color: #555; padding-bottom: 2px;")
        services_list = QListWidget()
        for service in order.services:
            item = QListWidgetItem(service.name)
            item.setToolTip(f"{service.price}₽" or "Нет точной")
            services_list.addItem(item)
        services_price = 0
        for service in order.services:
            services_price += service.price or 0
        services_price_box = InfoBox("Общая цена услуг:", str(services_price))
        priority_name: str = priority_to_name[order.priority]
        priority_color: str = priority_to_color[order.priority]
        priority_box = InfoBox("Приоритет заказа:", priority_name, hex_color=priority_color)

        left_layout.addWidget(client_name_box)
        left_layout.addWidget(client_phone_box)
        left_layout.addWidget(client_address_box)
        left_layout.addWidget(service_list_label)
        left_layout.addWidget(services_list)
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
        self.priority_box = QComboBox()
        for priority, display_name in priority_to_name.items():
            self.priority_box.addItem(display_name, priority)
        self.priority_box.setCurrentIndex(0)

        right_layout.addWidget(self.device_type_box)
        right_layout.addWidget(self.device_brand_box)
        right_layout.addWidget(self.device_model_box)
        right_layout.addWidget(priority_label)
        right_layout.addWidget(self.priority_box)
        right_layout.addWidget(self.create_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

    def check_fields(self):
        client_phone = self.client_phone_box.get_value()
        trouble_desc = self.trouble_description_box.get_value()
        client_name = self.client_name_box.get_value()
        if self.client_name_box.isHidden():
            enabled = True if client_phone and trouble_desc else False
        else:
            enabled = True if client_phone and client_name and trouble_desc else False
        self.error_label.hide()
        self.create_button.setEnabled(enabled)

    @asyncSlot()
    async def create_order(self):
        error_msg: str = ""
        order_manager = get_order_manager()
        client_name: str = self.client_name_box.get_value()
        client_phone: str = self.client_phone_box.get_value()
        client_address: str = self.client_address_box.get_value()
        trouble_desc: str = self.trouble_description_box.get_value()
        device_type: str = self.device_type_box.get_value()
        device_brand: str = self.device_brand_box.get_value()
        device_model: str = self.device_model_box.get_value()
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
                client_phone,
                trouble_desc,
                device_type,
                device_brand,
                device_model,
                order_priority
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
                order_priority
            )
            created = result[1]

        if created:
            self.error_label.setText("Заказ успешно создан!")

        self.error_label.show()
        self.create_button.setEnabled(False)

        await self.parent.fill_cards()
