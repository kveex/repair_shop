import asyncio
from typing import Callable, Optional

from realtime import RealtimePostgresChangesListenEvent
from supabase import AsyncClient
from datetime import datetime
from logger_config import logger
from dataclasses import dataclass
from enum import Enum

from src.database.services.service import Service, ServiceTypes, ServiceManager
from src.database.services.worker import Worker
from src.database.services.client import ClientNotExistsError, Client, ClientManager


class OrderStatus(Enum):
    WAITING = "Ожидание"
    IN_PROGRESS = "В работе"
    STOPPED = "Отложено"
    FINISHED = "Завершено"
    REJECTED = "Отказ"

class OrdersRealtimeConnectionError(Exception): pass

@dataclass(frozen=True, order=True)
class Order:
    client: Client
    services: Optional[list[Service]]
    worker: Optional[Worker]
    trouble_description: str
    status: OrderStatus
    accept_date: str
    finish_date: str
    device_type: str
    device_brand: str
    device_model: str
    technician_notes: str
    id: int

    def is_taken(self) -> bool:
        return self.worker is not None

    def is_taken_by(self, worker: Worker) -> bool:
        if self.worker is None:
            return False
        return self.worker == worker

    def is_finished(self) -> bool:
        return self.finish_date != "Не завершён"

    def get_full_price(self) -> int | None:
        if not self.services: return None
        price: int = 0
        for service in self.services:
            if not service.price: return None
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

    def get_provided_services(self) -> Optional[list[Service]]:
        if not self.services: return None

        result: list[Service] = []

        for service in self.services:
            if service.service_type == ServiceTypes.PROVIDED.value:
                result.append(service)

        return result

    def get_requested_services(self) -> Optional[list[Service]]:
        if not self.services: return None

        result: list[Service] = []

        for service in self.services:
            if service.service_type == ServiceTypes.REQUESTED.value:
                result.append(service)

        return result

async def _build_order(data: dict) -> Order:
    client_info = data.get("clients")
    client_id: int = client_info.get("id")
    client_name: str = client_info.get("name")
    client_phone: str = client_info.get("phone")
    client_address: str | None = client_info.get("address", None)
    client: Client = Client(name=client_name, phone=client_phone, id=client_id, address=client_address)

    services_info = data.get("order_services")
    services_list: list | None = None
    if services_info is not None:
        services_list = []
        for service in services_info:
            service_info = service.get("services")
            service_id: int = service_info.get("id")
            service_name: str = service_info.get("name")
            service_desc: str = service_info.get("description")
            service_price: int | None = service.get("price") or service_info.get("price")
            service_type: ServiceTypes = service.get("service_type")
            s = Service(name=service_name, description=service_desc, price=service_price, service_type=service_type,
                        id=service_id)
            services_list.append(s)

    worker_info: dict | None = data.get("workers", None)
    worker: Worker | None = None

    if worker_info is not None:
        worker_name: str = worker_info.get("name")
        worker_role: str = worker_info.get("role")
        worker_id: int = worker_info.get("id")
        worker = Worker(name=worker_name, role=worker_role, id=worker_id)

    trouble_desc: str = data.get("trouble_description")
    status: OrderStatus = data.get("status")
    accept_date: str = data.get("accept_date")
    finish_date: str = data.get("finish_date") or "Не завершён"
    device_type: str = data.get("device_type") or "Не указан"
    device_brand: str = data.get("device_brand") or "Не указан"
    device_model: str = data.get("device_model") or "Не указана"
    technician_notes: str = data.get("technician_notes")
    priority_code: int = data.get("priority")
    order_id: int = data.get("id")

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
        id=order_id
    )

    return order

async def _build_orders_list(orders: list) -> list[Order]:
    result: list = []

    for order in orders:
        o = await _build_order(order)

        result.append(o)

    return result


class OrderManager:
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
        self.client_manager: ClientManager = ClientManager(supabase)
        self.service_manager: ServiceManager = ServiceManager(supabase)

    async def make_order_new_client(self,
                                    client_name: str,
                                    client_phone: str,
                                    client_address: str | None,
                                    trouble_description: str,
                                    device_type: str,
                                    device_brand: str,
                                    device_model: str,
                                    requested_services: list[Service]) -> tuple[Client | None, bool]:
        try:
            client = await self.client_manager.add_client(client_name, client_phone, client_address)
            good = await self.make_order(
                client.phone,
                trouble_description,
                device_type,
                device_brand,
                device_model,
                requested_services
            )
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
                         requested_services: list[Service]) -> bool:
        client: Client = await self.client_manager.get_client(client_phone)

        if client is None: raise ClientNotExistsError("Такого клиента не существует")
        if requested_services is None: raise ValueError("Должна быть запрошена хотя бы одна услуга")

        if trouble_description == "": trouble_description = "Не описано"

        try:
            response = await self.supabase.table("orders").insert({
                "client_id": client.id,
                "trouble_description": trouble_description,
                "device_type": device_type,
                "device_brand": device_brand,
                "device_model": device_model,
                "accept_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            }).execute()
            order_id = response.data[0].get("id")
            await self.service_manager.add_services_to_order(order_id, requested_services)

        except Exception as e:
            msg = str(e)
            logger.error(f"!!!THIS IS ERROR!!! -> {msg}")
            return False

        logger.info(
            f"Создан заказ! Имя клиента {client.name}, Номер телефона: {client.phone}, Описание проблемы: {trouble_description}")
        return True

    async def get_all_orders(self) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), workers(*), order_services(*, services(*))").execute()

        data = orders.data

        if not data:
            return []

        return await _build_orders_list(data)

    async def get_order(self, order_id: int) -> Order:
        response = await self.supabase.table("orders").select("*, clients(*), workers(*), order_services(*, services(*))").eq("id", order_id).execute()
        if not response.data:
            raise ValueError(f"Заказ с id [{order_id}] не найден")

        data = response.data[0]

        return await _build_order(data)

    async def get_client_orders(self, client: Client) -> list[Order]:
        orders = await self.supabase.table("orders").select("*, clients(*), workers(*), order_services(*, services(*))").eq("clients.id", client.id).execute()
        data = orders.data

        return await _build_orders_list(data)

    async def select_order(self, order: Order, worker: Worker) -> bool:
        try:
            response = await self.supabase.table("orders").update({"worker_id": worker.id, "status": "В работе"}).eq("id",
                                                                                                                  order.id).execute()
        except Exception as e:
            msg = str(e)
            if "orders_worker_id_fkey" in msg:
                raise ValueError(f"Работник с ID = {worker.id} не был найден")
            else:
                logger.error(msg)
                return False

        if not response.data:
            raise ValueError(f"Заказ с ID = {order.id} не был найден")

        return True

    async def finish_order(self, order_id: int) -> bool:
        try:
            await self.supabase.table("orders").update({"status": "Завершен", "finish_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S")}).eq("id",
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
        orders = await self.supabase.table("orders").select("*, clients(*), order_services(*, services(*))").is_("worker_id",
                                                                                              None).execute()
        data = orders.data
        return await _build_orders_list(data)

    async def get_workers_orders(self, worker: Worker) -> list[Order]:
        orders = await (self.supabase.table("orders").select("*, clients(*), order_services(*, services(*)), workers(*)")
                        .eq("worker_id", worker.id).execute())
        data = orders.data
        return await _build_orders_list(data)

    async def update_order_technician_notes(self, order_id: int, technician_notes: str) -> bool:

        response = await self.supabase.table("orders").update({"technician_notes": technician_notes}).eq("id", order_id).execute()

        if not response.data:
            return False

        return True

    async def init_orders_realtime(self, handler: Callable):
        """
        Создаёт канал для просмотра изменений в таблице с заказами и подписывается на него.

        !!! Нужно подкрепить его циклом типа while True: await asyncio.sleep(1) иначе соединение упадёт !!!
        :param handler: Функция с входным аргументом data: dict
        """
        await self.supabase.realtime.connect()

        if not self.supabase.realtime.is_connected:
            raise OrdersRealtimeConnectionError("Не удалось подключиться к realtime")

        channel = self.supabase.channel("order_updates_and_inserts").on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Update,
            schema="public",
            table="orders",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Insert,
            schema="public",
            table="orders",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Update,
            schema="public",
            table="order_services",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
            event=RealtimePostgresChangesListenEvent.Insert,
            schema="public",
            table="order_services",
            callback=lambda payload: asyncio.create_task(handler(payload.get("data")))
        ).on_postgres_changes(
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
