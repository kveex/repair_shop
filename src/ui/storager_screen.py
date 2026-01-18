import asyncio
from functools import partial
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QHBoxLayout, QDialog, \
    QPushButton
from realtime import RealtimePostgresChangesListenEvent

from src.database import get_storage_manager, StorageManager
from src.database.services.storage import StorageRequest, NotExistingCellError, Cell
from src.ui import CardListWidget, InfoBox, InputBox
from qasync import asyncSlot
from src.utils import NotificationManager, NotificationType


class StoragerScreen(QWidget):
    def __init__(self, notification_manager: NotificationManager):
        super().__init__()
        self.notification_manager = notification_manager
        self.storage_manager: Optional[StorageManager] = None
        self.storage_requests: list[StorageRequest] = []
        tab = QTabWidget()
        self.info_dialog = QDialog(self)
        self.cells_list = CardListWidget()
        self.request_list = CardListWidget()

        tab.addTab(self.cells_list, "Ячейки")
        tab.addTab(self.request_list, "Запросы")

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(tab)

    def on_cell_card_press(self, cell_info: Cell):
        self.info_dialog = FullCellInfo(cell_info)
        self.info_dialog.open()

    def on_request_card_press(self, request: StorageRequest):
        self.info_dialog = FullRequestInfo(request)
        self.info_dialog.open()

    async def fill_cards(self):
        requests_list: list[StorageRequest] = await self.storage_manager.get_all_requests()
        cells_list: list[Cell] = await self.storage_manager.get_all_cells()

        for cell in cells_list:
            cell_id: str = f"Ячейка №{cell.id}"
            cell_item: str = "Пустая ячейка"
            if cell.order:
                cell_item = cell.order.device_type
            elif cell.item:
                cell_item = cell.item

            self.cells_list.create_card(
                card_name=cell_id,
                card_desc=cell_item,
                full_card_info=cell,
                func=partial(self.on_cell_card_press, cell)
            )

        for request in requests_list:
            card_name: str = request.order.device_type
            card_desc: str = f"Запрошенный предмет: {request.requested_item}"
            card_help: str = "Статус: "
            card_help += "Завершён" if request.finished else "Ожидает"
            cell_num: Optional[int] = request.cell_number
            card_help_desc = f"Номер ячейки: {cell_num}" if cell_num else "Нет на складе"

            self.request_list.create_card(
                card_name=card_name,
                card_desc=card_desc,
                card_help=card_help,
                card_help_desc=card_help_desc,
                func=partial(self.on_request_card_press, request),
                full_card_info=request
            )

    async def handle_request_cards(self, data: dict):
        request_id = data.get("old_record").get("id")
        answer_type: RealtimePostgresChangesListenEvent = data.get("type")
        request = await self.storage_manager.get_request(request_id)

        card_name: str = request.order.device_type
        card_desc: str = f"Запрошенный предмет: {request.requested_item}"
        card_help: str = "Статус: "
        card_help += "Завершён" if request.finished else "Ожидает"
        cell_num: Optional[int] = request.cell_number
        card_help_desc = f"Номер ячейки: {cell_num}" if cell_num else "Нет на складе"

        if answer_type == RealtimePostgresChangesListenEvent.Insert:
            self.request_list.create_card(
                card_name=card_name,
                card_desc=card_desc,
                card_help=card_help,
                card_help_desc=card_help_desc,
                func=partial(self.on_request_card_press, request),
                full_card_info=request
            )
            self.notification_manager.show_notification("Новый запрос", f"Поступил запрос на {request.requested_item}", NotificationType.NOTIFY)
        else:
            self.request_list.update_card(
                card_name=card_name,
                card_desc=card_desc,
                card_help=card_help,
                card_help_desc=card_help_desc,
                func=partial(self.on_request_card_press, request),
                full_card_info=request
            )

    async def handle_cell_cards(self, data: dict):
        cell_id: int = data.get("record").get("id")
        answer_type: RealtimePostgresChangesListenEvent = data.get("type")
        cell = await self.storage_manager.get_cell(cell_id)

        cell_id: str = f"Ячейка №{cell.id}"
        cell_item: str = "Пустая ячейка"
        if cell.order:
            cell_item = cell.order.device_type
        elif cell.item:
            cell_item = cell.item

        if answer_type == RealtimePostgresChangesListenEvent.Insert:
            self.cells_list.create_card(
                card_name=cell_id,
                card_desc=cell_item,
                full_card_info=cell,
                func=partial(self.on_cell_card_press, cell)
            )
        else:
            self.cells_list.update_card(
                card_name=cell_id,
                card_desc=cell_item,
                full_card_info=cell,
                func=partial(self.on_cell_card_press, cell)
            )
            self.notification_manager.show_notification("Изменение информации",
                                                        f"Информация о ячейке {cell_id} изменена",
                                                        NotificationType.NOTIFY)

    @asyncSlot()
    async def on_show(self):
        self.storage_manager = get_storage_manager()
        await self.fill_cards()
        await self.storage_manager.init_order_requests_realtime(self.handle_request_cards)
        await self.storage_manager.init_storage_realtime(self.handle_cell_cards)
        while self.isVisible():
            await asyncio.sleep(1)

class FullRequestInfo(QDialog):
    def __init__(self, request_info: StorageRequest):
        super().__init__()

        self.storage_manager = get_storage_manager()
        self.setWindowTitle("Полная информация по запросу")
        self.resize(500, 300)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.info_label.setWordWrap(True)
        self.info_label.hide()

        device_type_box = InfoBox("Тип устройства:", request_info.order.device_type)
        device_brand_box = InfoBox("Бренд устройства:", request_info.order.device_brand)
        device_model_box = InfoBox("Модель устройства:", request_info.order.device_model)
        self.cell_text: str = "" if not request_info.cell_number else str(request_info.cell_number)
        self.cell_number_box = InputBox("В какой ячейке:")
        self.cell_number_box.set_value(self.cell_text)
        self.cell_number_box.value_input.textChanged.connect(self.check_change)
        requested_item_box = InfoBox("Запрошенный предмет:", request_info.requested_item)
        finished_text: str = "Да" if request_info.finished else "Нет"
        item_taken_box = InfoBox("Забрали ли предмет:", finished_text)

        self.update_button = QPushButton("Обновить")
        self.update_button.clicked.connect(lambda: self.update_cell_num(request_info))
        self.update_button.setEnabled(False)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addWidget(self.info_label)
        left_layout.addWidget(device_type_box)
        left_layout.addWidget(device_brand_box)
        left_layout.addWidget(device_model_box)
        # left_layout.addWidget(order_status_box)
        left_layout.addWidget(self.update_button)

        right_layout.addWidget(requested_item_box)
        right_layout.addWidget(self.cell_number_box)
        right_layout.addWidget(item_taken_box)
        right_layout.addWidget(close_button)

        main_layout = QHBoxLayout(self)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

    def check_change(self):
        self.info_label.hide()
        if not self.cell_text and self.cell_number_box.get_value():
            self.update_button.setEnabled(True)

    @asyncSlot()
    async def update_cell_num(self, request):
        msg: str = ""
        try:
            storage_id: int = int(self.cell_number_box.get_value())
            await self.storage_manager.update_request_cell(request.id, storage_id)
            self.info_label.setText("Номер ячейки с запрашиваемым предметом установлен")
        except NotExistingCellError as e:
            msg = str(e)
        except ValueError:
            msg = "Введено что-то что не является числом!"

        if msg:
            self.info_label.setText(msg)

        self.info_label.show()

class FullCellInfo(QDialog):
    def __init__(self, cell_info: Cell):
        super().__init__()

        self.setWindowTitle("Полная информация о ячейке")
        self.resize(400, 200)

        if cell_info.order:
            cell_item = f"{cell_info.order.device_type}, {cell_info.order.device_brand}, {cell_info.order.device_model}"
        elif cell_info.item:
            cell_item = cell_info.item
        else:
            cell_item = "Ячейка пуста"

        cell_number_box = InfoBox("Номер ячейки:", str(cell_info.id))
        cell_item_box = InfoBox("Предмет в ячейке:", cell_item)

        layout = QVBoxLayout(self)
        layout.addWidget(cell_number_box)
        layout.addWidget(cell_item_box)