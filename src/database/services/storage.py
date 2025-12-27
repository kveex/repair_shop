import asyncio
from dataclasses import dataclass

from realtime import RealtimePostgresChangesListenEvent
from supabase import AsyncClient
from src.database.services.order import OrderStatus
from typing import Optional, Callable

class NotExistingCellError(Exception): pass
class StorageRealtimeConnectionError(Exception): pass

@dataclass(frozen=True, order=True)
class StorageOrder:
    device_type: str
    device_brand: str
    device_model: str
    status: OrderStatus
    id: int

@dataclass(frozen=True, order=True)
class Cell:
    id: int
    order: Optional[StorageOrder]
    item: Optional[str]

@dataclass(frozen=True, order=True)
class StorageRequest:
    id: int
    order: StorageOrder
    cell_number: Optional[int]
    requested_item: str
    finished: bool

def build_storage_order(order: dict | None) -> Optional[StorageOrder]:
    if order is None: return None
    order_id: int = order.get("id")
    device_type: str = order.get("device_type")
    device_brand: str = order.get("device_brand")
    device_model: str = order.get("device_model")
    status: OrderStatus = order.get("status")

    return StorageOrder(device_type, device_brand, device_model, status, order_id)

class StorageManager:
    def __init__(self, supabase: AsyncClient):
        self.supabase: AsyncClient = supabase

    async def get_all_cells(self) -> list[Cell]:
        """Возвращает список всех ячеек, предметов в них и привязанных к ним заказов"""

        response = await self.supabase.table("storage").select("*, orders(*)").order("id").execute()

        data: list = response.data

        result: list = []

        for cell in data:
            order_info: dict = cell.get("orders")
            cell_id: int = cell.get("id")
            item: Optional[str] = cell.get("item")
            order: Optional[StorageOrder] = build_storage_order(order_info)

            storage_cell: Cell = Cell(id=cell_id, order=order, item=item)

            result.append(storage_cell)

        return result

    async def get_cell(self, cell_id: int) -> Cell:
        """Возвращает всю информацию о ячейке по номеру ячейки """
        if cell_id is None:
            raise ValueError("cell_id is None")

        response = await self.supabase.table("storage").select("*, orders(*)").eq("id", cell_id).execute()

        cell: dict = response.data[0]

        order_info: dict = cell.get("orders")
        cell_id: int = cell.get("id")
        item: Optional[str] = cell.get("item")
        order: Optional[StorageOrder] = build_storage_order(order_info)

        storage_cell: Cell = Cell(id=cell_id, order=order, item=item)

        return storage_cell

    async def get_all_requests(self) -> list[StorageRequest]:
        """Возвращает список созданных на складе запросов"""

        response = await self.supabase.table("order_requests").select("*, orders(*), storage(id)").execute()

        data: list = response.data

        result: list = []

        for request in data:
            order_info: dict = request.get("orders")
            storage_info: dict = request.get("storage")
            cell_id: Optional[int] = storage_info.get("id") if storage_info else None
            request_id: int = request.get("id")
            order: Optional[StorageOrder] = build_storage_order(order_info)
            request_item: str = request.get("request_item")
            finished: bool = request.get("finish_request")

            storage_request: StorageRequest = StorageRequest(
                id=request_id,
                order=order,
                cell_number=cell_id,
                finished=finished,
                requested_item=request_item
            )

            result.append(storage_request)

        return result

    async def update_request_cell(self, request_id: int, storage_id: int):
        try:
            await self.supabase.table("order_requests").update({"storage_id": storage_id}).eq("id", request_id).execute()
        except Exception as e:
            if "is not present in table" in str(e):
                raise NotExistingCellError("Указанная ячейка не существует или не занесена в бд")

    async def get_request(self, request_id: int) -> StorageRequest:
        """Возвращает всю информацию по запросу по id запроса"""
        response = await self.supabase.table("order_requests").select("*, orders(*), storage(id)").eq("id", request_id).execute()
        request: dict = response.data[0]

        order_info: dict = request.get("orders")
        storage_info: dict = request.get("storage")
        cell_id: Optional[int] = storage_info.get("id") if storage_info else None
        request_id: int = request.get("id")
        order: Optional[StorageOrder] = build_storage_order(order_info)
        request_item: str = request.get("request_item")
        finished: bool = request.get("finish_request")

        storage_request: StorageRequest = StorageRequest(
            id=request_id,
            order=order,
            cell_number=cell_id,
            finished=finished,
            requested_item=request_item
        )

        return storage_request

    async def init_order_requests_realtime(self, handler: Callable):
        """
        Создаёт канал для просмотра изменений в таблице с запросами к заказу и подписывается на него.

        !!! Нужно подкрепить его циклом типа while True: await asyncio.sleep(1) иначе соединение упадёт !!!
        :param handler: Функция с входным аргументом data: dict
        """

        await self.supabase.realtime.connect()

        if not self.supabase.realtime.is_connected:
            raise StorageRealtimeConnectionError("Не удалось подключиться к realtime")

        channel = self.supabase.channel("order_request_updates_and_inserts").on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Update,
            schema="public",
            table="order_requests",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Insert,
            schema="public",
            table="order_requests",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        )

        await channel.subscribe()

    async def init_storage_realtime(self, handler: Callable):
        """
        Создаёт канал для просмотра изменений в таблице с ячейками на складе и подписывается на него.

        !!! Нужно подкрепить его циклом типа while True: await asyncio.sleep(1) иначе соединение упадёт !!!
        :param handler: Функция с входным аргументом data: dict
        """

        await self.supabase.realtime.connect()

        if not self.supabase.realtime.is_connected:
            raise StorageRealtimeConnectionError("Не удалось подключиться к realtime")

        channel = self.supabase.channel("storage_updates_and_inserts").on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Update,
            schema="public",
            table="storage",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Insert,
            schema="public",
            table="storage",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        )

        await channel.subscribe()