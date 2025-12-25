from dataclasses import dataclass
from supabase import AsyncClient
from src.database.services.order import OrderStatus
from typing import Optional

class NotExistingCellError(Exception): pass

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
