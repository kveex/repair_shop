from supabase import AsyncClient
from datetime import datetime
from logger_config import logger
from dataclasses import dataclass
from enum import IntEnum

from src.database.services.service import Service
from src.database.services.worker import Worker
from src.database.services.client import ClientNotExistsError, Client, ClientManager

now_date: str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

class Priorities(IntEnum):
    NORMAL = 0
    HIGH = 1
    EMERGENT = 2

priority_to_name = {
    Priorities.NORMAL: "Обычный",
    Priorities.HIGH: "Высокий",
    Priorities.EMERGENT: "Срочный"
}

priority_to_color = {
    Priorities.NORMAL: "#f0f0f0",
    Priorities.HIGH: "#f2b02b",
    Priorities.EMERGENT: "#f2352b"
}

@dataclass(frozen=True, order=True)
class Order:
    client: Client
    services: list[Service] | None
    worker: Worker | None
    trouble_description: str
    status: str
    accept_date: str
    finish_date: str
    device_type: str
    device_brand: str
    device_model: str
    technician_notes: str
    priority: Priorities
    id: int

    def is_taken(self) -> bool:
        return self.worker is None

    def is_taken_by(self, worker: Worker) -> bool:
        if self.worker is None:
            return False
        return self.worker == worker

    def is_finished(self) -> bool:
        return self.finish_date is not None

    def get_full_price(self) -> int:
        price: int = 0
        for service in self.services:
            price += service.price
        return price

    def get_service_names(self, short: bool = True) -> str:
        if not self.services:
            return "Услуг нет"

        if short:
            first_service = self.services[0].name
            service_count = len(self.services) - 1
            return f"{first_service}+{service_count}" if service_count > 0 else first_service
        else:
            return ", ".join(service.name for service in self.services)

async def _get_orders(orders: list) -> list[Order]:
    result: list = []

    for order in orders:
        client_info = order.get("clients")
        client_id: int = client_info.get("id")
        client_name: str = client_info.get("name")
        client_phone: str = client_info.get("phone")
        client_address: str | None = client_info.get("address", None)
        client: Client = Client(name=client_name, phone=client_phone, id=client_id, address=client_address)

        services_info = order.get("order_services")
        services_list: list | None = None
        if services_info is not None:
            services_list = []
            for service in services_info:
                service_info = service.get("services")
                service_id: int = service_info.get("id")
                service_name: str = service_info.get("name")
                service_desc: str = service_info.get("description")
                service_price: int | None = service.get("price") or service_info.get("price")
                s = Service(name=service_name, description=service_desc, price=service_price, id=service_id)
                services_list.append(s)

        worker_info: dict | None = order.get("workers", None)
        worker: Worker | None = None

        if worker_info is not None:
            worker_name: str = worker_info.get("name")
            worker_role: str = worker_info.get("role")
            worker_id: int = worker_info.get("id")
            worker = Worker(name=worker_name, role=worker_role, id=worker_id)

        trouble_desc: str = order.get("trouble_description")
        status: str = order.get("status")
        accept_date: str = order.get("accept_date")
        finish_date: str = order.get("finish_date") or "Не завершен"
        device_type: str = order.get("device_type") or "Не указан"
        device_brand: str = order.get("device_brand") or "Не указан"
        device_model: str = order.get("device_model") or "Не указана"
        technician_notes: str = order.get("technician_notes") or "Заметок не было указано"
        priority_code: int = order.get("priority")
        priority: Priorities = Priorities(priority_code)
        order_id: int = order.get("id")

        order = Order(
            client=client,
            services=services_list,
            worker=worker,
            trouble_description=trouble_desc,
            status=status,
            accept_date=accept_date,
            finish_date=finish_date,
            device_type=device_type,
            device_brand=device_brand,
            device_model=device_model,
            technician_notes=technician_notes,
            priority=priority,
            id=order_id
        )

        logger.debug("Loaded order: %s -> %s / %s", client.name, accept_date)

        result.append(order)

    return result


class OrderManager:
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
        self.client_manager: ClientManager = ClientManager(supabase)

    async def make_order_new_client(self,
                                    client_name: str,
                                    client_phone: str,
                                    client_address: str | None,
                                    trouble_description: str,
                                    device_type: str,
                                    device_brand: str,
                                    device_model: str,
                                    priority: int) -> tuple[Client | None, bool]:
        try:
            client = await self.client_manager.add_client(client_name, client_phone, client_address)
            good = await self.make_order(client.phone, trouble_description, device_type, device_brand, device_model, priority)
        except Exception as e:
            msg = str(e)
            logger.error(msg)
            return None, False

        if not good:
            await self.client_manager.delete_client(client.id)
            return None, good

        return client, good

    async def make_order(self, client_phone: str,
                         trouble_description: str,
                         device_type: str,
                         device_brand: str,
                         device_model: str,
                         priority: int) -> bool:
        client: Client = await self.client_manager.get_client(client_phone)

        if client is None: raise ClientNotExistsError("Такого клиента не существует")

        if trouble_description == "": trouble_description = "Не описано"

        try:
            await self.supabase.table("orders").insert({
                "client_id": client.id,
                "trouble_description": trouble_description,
                "device_type": device_type,
                "device_brand": device_brand,
                "device_model": device_model,
                "accept_date": now_date,
                "priority": priority
            }).execute()

        except Exception as e:
            msg = str(e)
            logger.error(f"!!!THIS IS ERROR!!! -> {msg}")
            return False

        logger.info(
            f"Создан заказ! Имя клиента {client.name}, Номер телефона: {client.phone}, Описание проблемы: {trouble_description}, Приоритет: {priority}")
        return True

    async def get_all_orders(self) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), workers(*), order_services(*, services(*))").execute()

        data = orders.data

        if not data:
            return []

        return await _get_orders(data)

    async def get_client_orders(self, client: Client) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), workers(*), order_services(*, services(*))").eq("clients.id", client.id).execute()
        data = orders.data

        return await _get_orders(data)

    async def select_order(self, order: Order, worker: Worker) -> bool:
        try:
            order = await self.supabase.table("orders").update({"worker_id": worker.id, "status": "В работе"}).eq("id",
                                                                                                                  order.id).execute()
        except Exception as e:
            msg = str(e)
            if "orders_worker_id_fkey" in msg:
                raise ValueError(f"Работник с ID = {worker.id} не был найден")
            else:
                logger.error(msg)
                return False

        if not order:
            raise ValueError(f"Заказ с ID = {order.id} не был найден")

        return True

    def finish_order(self, order_id: int) -> bool:
        try:
            self.supabase.table("orders").update({"status": "Завершен", "finish_date": now_date}).eq("id",
                                                                                                     order_id).execute()
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Заказ не завершен, так как введено что-то что не является ID заказа")
            else:
                logger.error(msg)
                return False
        return True

    async def get_not_taken_orders(self) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), services(*)").is_("worker_id",
                                                                                              None).execute()
        data = orders.data
        return await _get_orders(data)

    async def get_workers_orders(self, worker: Worker) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), services(*), workers(*)").eq("worker_id",
                                                                                                         worker.id).execute()
        data = orders.data
        return await _get_orders(data)
