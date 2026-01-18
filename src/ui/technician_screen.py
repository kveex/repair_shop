import asyncio
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QDialog,
                               QHBoxLayout, QPushButton, QStackedWidget)
from realtime import RealtimePostgresChangesListenEvent

import src.database as db
from qasync import asyncSlot

from database import StorageManager
from src.database.services.order import Order, OrderManager
from src.database.services.worker import Worker
from src.ui import CardListWidget, ServiceSelectBox, ServiceInfoBox, InfoBox, InputBox
from utils import NotificationManager, NotificationType


class _OrderSelectionListWidget(QWidget):
    order_selected = Signal(Order)
    def __init__(self):
        super().__init__()
        self._worker: Optional[Worker] = None
        layout = QVBoxLayout(self)

        self._order_manager: Optional[OrderManager] = None
        self._not_taken_orders_card_list = CardListWidget()
        self._get_order_dialog = QDialog(self)

        layout.addWidget(self._not_taken_orders_card_list)

    def _on_card_press(self, order: Order) -> None:
        self._get_order_dialog = GetOrderDialog(order)
        self._get_order_dialog.accepted.connect(lambda: self._select_order(order, self._worker))
        self._get_order_dialog.open()

    @asyncSlot()
    async def _select_order(self, order: Order, worker: Worker) -> None:
        await self._order_manager.select_order(order, worker)
        self.order_selected.emit(order)

    def set_managers(self, order_manager: OrderManager) -> None:
        self._order_manager = order_manager

    async def start_realtime(self) -> None:
        print("realtime launched")
        await self._order_manager.init_orders_realtime(self._handle_update)

        while self.isVisible():
            await asyncio.sleep(1)

    async def _handle_update(self, data: dict) -> None:
        order_id: int = data.get("record").get("id") or data.get("record").get("order_id")

        answer_type: RealtimePostgresChangesListenEvent = data.get("type")
        order = await self._order_manager.get_order(order_id)

        if answer_type == RealtimePostgresChangesListenEvent.Insert:
            self._not_taken_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=order,
                func=lambda _, o=order: self._on_card_press(o)
            )

        elif answer_type == RealtimePostgresChangesListenEvent.Update:
            if order.is_taken(): return
            self._not_taken_orders_card_list.update_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=order,
                func=lambda _, o=order: self._on_card_press(o)
            )

    def fill_cards(self, orders: list[Order], worker: Worker) -> None:
        self._worker = worker
        for order in orders:
            self._not_taken_orders_card_list.create_card(
                card_name=order.get_service_names(False),
                card_desc=order.trouble_description,
                full_card_info=order,
                func=lambda _, o=order: self._on_card_press(o)
            )


class _SelectedOrderWidget(QWidget):
    def __init__(self, notification_manager: NotificationManager):
        super().__init__()
        self._notification_manager = notification_manager
        self._order_manager: Optional[OrderManager] = None
        self._storage_manager: Optional[StorageManager] = None

        self._order_id: int = -1
        self._previous_technician_notes: Optional[str] = None

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.device_info_box = InfoBox("Устройство:", "")

        self.provided_services_box = ServiceSelectBox("Оказанные услуги:")

        self.requested_services_box = ServiceInfoBox("Запрошенные услуги:", [])
        self.order_status_box = InfoBox("Статус заказа:", "")

        self.update_button = QPushButton("Обновить")
        self.update_button.clicked.connect(self._update_button_pressed)
        self.update_button.setEnabled(False)

        left_layout.addWidget(self.device_info_box)
        left_layout.addWidget(self.provided_services_box)
        left_layout.addWidget(self.requested_services_box)
        left_layout.addWidget(self.order_status_box)
        left_layout.addWidget(self.update_button)

        self.trouble_description_box = InfoBox("Описание проблемы:", "", multi_line=True)
        self.technician_notes_box = InputBox("Заметки техника:", multi_line=True)
        self.technician_notes_box.value_input.textChanged.connect(self._check_changes)

        close_button = QPushButton("Запросить")
        close_button.clicked.connect(self.close)

        right_layout.addWidget(self.trouble_description_box)
        right_layout.addWidget(self.technician_notes_box)
        right_layout.addWidget(close_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

    def _check_changes(self):
        if self.technician_notes_box.get_value() != self._previous_technician_notes or self.provided_services_box.get_checked_services():
            self.update_button.setEnabled(True)
        else:
            self.update_button.setEnabled(False)

    def set_managers(self, order_manager: OrderManager, storage_manager: StorageManager) -> None:
        self._order_manager = order_manager
        self._storage_manager = storage_manager

    @asyncSlot()
    async def _update_button_pressed(self):
        service_manager = db.get_service_manager()

        good_prices: bool = self.provided_services_box.is_prices_set()

        if not good_prices:
            self._notification_manager.show_notification("Ошибка!", "Вы не указали цены на все услуги", NotificationType.ERROR)
            return

        notes_saved: bool = await self._order_manager.update_order_technician_notes(self._order_id, self.technician_notes_box.get_value())

        if notes_saved:
            self._notification_manager.show_notification("Успех!", "Информация о заказе обновлена!", NotificationType.SUCCESS)
        else:
            self._notification_manager.show_notification("Ошибка!", "Что-то пошло не так, во время сохранения информации о заказе!", NotificationType.ERROR)

        services_updated: bool = await service_manager.update_order_services(self._order_id, self.provided_services_box.get_checked_services())

        if not services_updated and not self.requested_services_box.is_empty():
            self._notification_manager.show_notification("Предупреждение", "Не было отмечено ни одной выполненной услуги!", NotificationType.WARNING)

    def update_info(self, order: Order):
        self._order_id = order.id
        self._previous_technician_notes = order.technician_notes
        self.device_info_box.set_value(f"{order.device_type}, {order.device_brand} {order.device_model}")

        for service in order.services:
            provided: bool = service.is_provided()
            uneditable_price: bool = False if service.name == "Замена" and not provided else True
            clickable: bool = False if provided else True
            self.provided_services_box.add_service(service=service, uneditable_price=uneditable_price, on_check=self._check_changes, is_provided=True, clickable=clickable)

        requested_services = order.get_requested_services()
        self.requested_services_box.update_list(requested_services)

        self.order_status_box.set_value(str(order.status))

        self.trouble_description_box.set_value(order.trouble_description)

        self.technician_notes_box.set_value(order.technician_notes)

    async def start_realtime(self):
        await self._order_manager.init_orders_realtime(self._order_update_handler)
        await self._storage_manager.init_order_requests_realtime(self._order_request_handler)

        while self.isVisible():
            await asyncio.sleep(1)

    async def _order_update_handler(self, data: dict) -> None:
        order_id: int = data.get("record").get("id") or data.get("record").get("order_id")
        if not order_id == self._order_id: return

        answer_type: RealtimePostgresChangesListenEvent = data.get("type")
        order = await self._order_manager.get_order(order_id)

        if answer_type == RealtimePostgresChangesListenEvent.Update:
            self.update_info(order)

    async def _order_request_handler(self, data: dict) -> None:
        order_id: int = data.get("record").get("order_id")
        if not order_id == self._order_id: return

        answer_type: RealtimePostgresChangesListenEvent = data.get("type")
        request_id: int = data.get("record").get("id")
        request = await self._storage_manager.get_request(request_id)

        if answer_type == RealtimePostgresChangesListenEvent.Update:
            self._notification_manager.show_notification(
                "Информация по запросу",
                f"Запрошенный предмет ({request.requested_item}) теперь в ячейке {request.cell_number}",
                NotificationType.NOTIFY
            )

class TechnicianScreen(QWidget):
    def __init__(self, notification_manager: NotificationManager):
        super().__init__()
        layout = QVBoxLayout(self)
        self.order_manager: Optional[OrderManager] = None
        self.storage_manager: Optional[StorageManager] = None
        self.stack = QStackedWidget()
        self.order: Optional[Order] = None
        self.not_taken_orders: list[Order] = []
        self.not_taken_orders_card_list: Optional[CardListWidget] = None
        self.notification_manager = notification_manager
        self._selected_order_ui = _SelectedOrderWidget(self.notification_manager)
        self._order_selection_ui = _OrderSelectionListWidget()
        self._order_selection_ui.order_selected.connect(self._switch_to_order)

        self.stack.addWidget(self._order_selection_ui)
        self.stack.addWidget(self._selected_order_ui)


        layout.addWidget(self.stack)

    @asyncSlot()
    async def on_show(self, worker: Worker):
        self.order_manager = db.get_order_manager()
        self.storage_manager = db.get_storage_manager()
        worker_orders: list[Order] = await self.order_manager.get_workers_orders(worker)

        if worker_orders:
            for order in worker_orders:
                if order.is_finished(): continue
                self._selected_order_ui.set_managers(self.order_manager, self.storage_manager)
                self._selected_order_ui.update_info(order)
                self.stack.setCurrentWidget(self._selected_order_ui)
                await self._selected_order_ui.start_realtime()
                return
        else:
            not_taken_orders: list[Order] = await self.order_manager.get_not_taken_orders()
            self._order_selection_ui.set_managers(self.order_manager)
            self._order_selection_ui.fill_cards(not_taken_orders, worker)
            self.stack.setCurrentWidget(self._order_selection_ui)
            await self._order_selection_ui.start_realtime()

    def _switch_to_order(self, order: Order) -> None:
        self._selected_order_ui.set_managers(self.order_manager, self.storage_manager)
        self._selected_order_ui.update_info(order)
        self.stack.setCurrentWidget(self._selected_order_ui)
        self._selected_order_ui.start_realtime()

class GetOrderDialog(QDialog):
    def __init__(self, order: Order):
        super().__init__()
        dialog_layout = QVBoxLayout(self)
        buttons_layout = QHBoxLayout()

        device_type = InfoBox("Вид устройства:", order.device_type)
        device_brand_and_model = InfoBox("Название устройства: ", f"{order.device_brand}, {order.device_model}")

        suggested_services = ServiceInfoBox("Предложенные услуги:", order.services)

        trouble_description = InfoBox("Описание проблемы:", order.trouble_description, multi_line=True)

        dialog_layout.addWidget(device_type)
        dialog_layout.addWidget(device_brand_and_model)
        dialog_layout.addWidget(suggested_services)
        dialog_layout.addWidget(trouble_description)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        accept_button = QPushButton("Принять")
        accept_button.clicked.connect(self.accept)

        buttons_layout.addWidget(accept_button)
        buttons_layout.addWidget(close_button)

        dialog_layout.addLayout(buttons_layout)
