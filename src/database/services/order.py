from supabase import Client as SupabaseClient
from datetime import datetime
from logger_config import logger
from dataclasses import dataclass

from src.database.services.service import ServiceManager, ServiceNotExistsError, Service
from src.database.services.worker import WorkerManager, Worker
from src.database.services.client import ClientManager, ClientNotExistsError, Client

now_date: str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

@dataclass(frozen=True, order=True)
class Order:
    client: Client
    service: Service
    worker: Worker | None
    trouble_description: str
    status: str
    accept_date: str
    finish_date: str

class OrderManager:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.worker_manager: WorkerManager = WorkerManager(supabase)
        self.service_manager: ServiceManager = ServiceManager(supabase)
        self.client_manager: ClientManager = ClientManager(supabase)

    def make_order_new_client(self,
                              client_name: str,
                              client_phone: str,
                              client_address: str | None,
                              service: Service,
                              trouble_description: str) -> tuple[Client | None, bool]:
        try:
            client = self.client_manager.add_client(client_name, client_phone, client_address)
            good = self.make_order(client_phone, service, trouble_description)
        except Exception as e:
            msg = str(e)
            logger.error(msg)
            return None, False

        if not good:
            self.supabase.table("clients").delete().eq("id", client.id).execute()
            return None, good

        return client, good

    def make_order(self, client_phone: str, service: Service, trouble_description: str) -> bool:
        client: Client = self.client_manager.get_client(client_phone)

        if client is None: raise ClientNotExistsError("Такого клиента не существует")
        if service is None: raise ServiceNotExistsError("Такого сервиса не существует")

        if trouble_description == "" : trouble_description = "Не описано"

        accept_time: str = now_date
        try:
            self.supabase.table("orders").insert({
                "client_id": client.id,
                "service_id": service.id,
                "trouble_description": trouble_description,
                "accept_date": accept_time
            }).execute()

        except Exception as e:
            msg = str(e)
            logger.error(f"!!!THIS IS ERROR!!! -> {msg}")
            return False

        logger.info(f"Создан заказ! Имя клиента {client.name}, Номер телефона: {client.phone}, Название услуги: {service.name}, Описание проблемы: {trouble_description}")
        return True

    def get_all_orders_old(self) -> list:
        orders: list = self.supabase.table("orders").select("*").execute().data
        services: list[Service] = self.service_manager.get_all_services()
        clients: list[Client] = self.client_manager.get_all_clients()
        workers: list[Worker] = self.worker_manager.get_all_workers()

        if not orders:
            return []

        # Превращаем списки в словари для быстрого поиска
        services_dict: dict = {s.id: s for s in services}
        clients_dict: dict = {c.id: c for c in clients}
        workers_dict: dict = {w.id: w for w in workers}

        result: list = []

        for order in orders:
            client = clients_dict.get(order["client_id"], {})
            service = services_dict.get(order["service_id"], {})
            worker = workers_dict.get(order["worker_id"], {})

            client_name = client.get("name", "Не найдено")
            client_phone = client.get("phone", "Не найдено")
            client_address = client.get("address") or "Не выдан"

            service_name = service.get("name", "Не найдено")
            service_desc = service.get("description", "Не найдено")
            service_price = service.get("price") or "Нет точной до завершения"

            worker_name = worker.get("name", "Не назначен")
            trouble_desc = order.get("trouble_description") or "Не описана"
            status = order.get("status")
            accept_date = datetime.fromisoformat(order.get("accept_date")).strftime("%d/%m/%Y %H:%M:%S")
            finish_date = datetime.fromisoformat(order.get("finish_date")).strftime("%d/%m/%Y %H:%M:%S") or "Не завершен"

            logger.info(
                f"\nИмя клиента: {client_name}"
                f"\nНомер телефона клиента: {client_phone}"
                f"\nАдрес клиента: {client_address}"
                f"\nНазвание сервиса: {service_name}"
                f"\nОписание сервиса: {service_desc}"
                f"\nЦена сервиса: {service_price}"
                f"\nИмя работника: {worker_name}"
                f"\nОписание проблемы: {trouble_desc}"
                f"\nСтатус: {status}"
                f"\nВремя принятия: {accept_date}"
                f"\nВремя завершения: {finish_date}"
            )

            order_info: list = [client_name, client_phone, client_address, service_name, service_desc, service_price, worker_name, trouble_desc, status, accept_date, finish_date]
            result.append(order_info)

        return result

    def get_all_orders(self) -> list[Order]:
        clients = {c.id: c for c in self.client_manager.get_all_clients()}
        services = {s.id: s for s in self.service_manager.get_all_services()}
        workers = {w.id: w for w in self.worker_manager.get_all_workers()}

        orders_rows = self.supabase.table("orders").select("*").execute().data or []

        if not orders_rows:
            return []

        result: list[Order] = []

        for row in orders_rows:
            client_obj = clients.get(row.get("client_id"))
            service_obj = services.get(row.get("service_id"))
            worker_obj = workers.get(row.get("worker_id"))

            trouble_desc = row.get("trouble_description") or "Не описана"
            status = row.get("status") or "Не указан"
            accept_date = row.get("accept_date")
            finish_date = row.get("finish_date") if row.get("finish_date") else "Не завершен"

            order_dto = Order(
                client=client_obj,
                service=service_obj,
                worker=worker_obj,
                trouble_description=trouble_desc,
                status=status,
                accept_date=accept_date,
                finish_date=finish_date,
            )

            logger.debug("Loaded order: %s -> %s / %s", client_obj.name, service_obj.name, accept_date)

            result.append(order_dto)

        return result

    def get_order(self, client_phone: str) -> list[Order]:
        client: Client = self.client_manager.get_client(client_phone)

        orders: list = self.supabase.table("orders").select("*").eq("client_id", client.id).execute().data

        result: list = []

        for order_info in orders:
            worker: Worker | None = None
            service_id: int = order_info["service_id"]
            worker_id: int = order_info["worker_id"]

            service: Service = self.service_manager.get_service(service_id)

            if worker_id is not None:
                worker: Worker | None = self.worker_manager.get_worker(worker_id)

            status = order_info["status"]
            accept_date = order_info["accept_date"]
            finish_date = order_info["finish_date"]
            trouble_desc = order_info["trouble_description"]

            order = Order(
                client=client,
                service=service,
                worker=worker,
                trouble_description=trouble_desc,
                status=status,
                accept_date=accept_date,
                finish_date=finish_date,
            )

            result.append(order)

        return result

    def select_order(self, order_id: int, worker_id: int) -> bool:
        try:
            order = self.supabase.table("orders").update({"worker_id": worker_id, "status": "В работе"}).eq("id", order_id).execute()
        except Exception as e:
            msg = str(e)
            if "orders_worker_id_fkey" in msg:
                raise ValueError(f"Работник с ID = {worker_id} не был найден")
            else:
                logger.error(msg)
                return False

        if not order:
            raise ValueError(f"Заказ с ID = {order_id} не был найден")

        return True

    def finish_order(self, order_id: int) -> bool:
        try:
            self.supabase.table("orders").update({"status": "Завершен", "finish_date": now_date}).eq("id", order_id).execute()
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Заказ не завершен, так как введено что-то что не является ID заказа")
            else:
                logger.error(msg)
                return False
        return True