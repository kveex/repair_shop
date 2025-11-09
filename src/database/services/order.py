from supabase import Client
from postgrest import APIError
from datetime import datetime
from src.logger_config import logger

from src.database.services.service import ServiceManager
from src.database.services.account import AccountManager
from src.database.services.client import ClientManager

now_date: str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

class OrderManager:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.account_manager: AccountManager = AccountManager(supabase)
        self.service_manager: ServiceManager = ServiceManager(supabase)
        self.client_manager: ClientManager = ClientManager(supabase)

    def make_order_new_client(self, client_name, client_phone, client_address, service_name, trouble_description) -> tuple[int, bool]:
        client_id = self.client_manager.add_client(client_name, client_phone, client_address)
        try:
            good = self.make_order(client_phone, service_name, trouble_description)
        except Exception:
            self.supabase.table("clients").delete().eq("id", client_id).execute()
            raise
        if not good:
            self.supabase.table("clients").delete().eq("id", client_id).execute()
            return -1, good
        return client_id, good

    def make_order(self, client_phone: str, service_name: str, trouble_description: str) -> bool:
        client_info: tuple[str, str, str, int] = self.client_manager.get_client(client_phone)
        if client_info is None: raise ValueError("Такого клиента не существует")

        service_info: tuple[str, str, int | None, int] = self.service_manager.get_service_by_name(service_name)
        if service_info is None: raise ValueError("Такого сервиса не существует")

        client_id = client_info[3]
        service_id = service_info[3]

        if trouble_description == "" : trouble_description = "Не описано"

        accept_time: str = now_date
        try:
            self.supabase.table("orders").insert({"client_id": client_id, "service_id": service_id, "trouble_description": trouble_description, "accept_date": accept_time}).execute()
            logger.info(f"Создан заказ! Имя клиента {client_info[0]}, Номер телефона: {client_info[1]}, Название услуги: {service_name}, Описание проблемы: {trouble_description}")
        except APIError:
            return False
        return True

    def get_all_orders(self) -> list:
        orders: list = self.supabase.table("orders").select("*").execute().data
        services: list = self.supabase.table("services").select("*").execute().data
        clients: list = self.supabase.table("clients").select("*").execute().data
        workers: list = self.supabase.table("accounts").select("id, name").execute().data

        # Превращаем списки в словари для быстрого поиска
        services_dict: dict = {s["id"]: s for s in services}
        clients_dict: dict = {c["id"]: c for c in clients}
        workers_dict: dict = {w["id"]: w for w in workers}

        result: list = []

        for order in orders:
            client = clients_dict.get(order["client_id"], {})
            service = services_dict.get(order["service_id"], {})
            worker = workers_dict.get(order["worker_id"], {})

            client_name = client.get("name", "Не найдено")
            client_phone = client.get("phone", "Не найдено")
            client_address = client.get("address") if not client.get("address") is None else "Не выдан"

            service_name = service.get("name", "Не найдено")
            service_desc = service.get("description", "Не найдено")
            service_price = service.get("price") if not service.get("price") is None else "Нет точной до завершения"

            worker_name = worker.get("name", "Не назначен")
            trouble_desc = order.get("trouble_description") if not order.get("trouble_description") is None else "Не описана"
            status = order.get("status")
            accept_date = datetime.fromisoformat(order.get("accept_date")).strftime("%d/%m/%Y %H:%M:%S")
            finish_date = datetime.fromisoformat(order.get("finish_date")).strftime("%d/%m/%Y %H:%M:%S") if not order.get("finish_date") is None else "Не завершен"

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

    def get_order(self, client_phone: str) -> list:
        client_info: tuple[str, str, str, int] = self.client_manager.get_client(client_phone)

        client_name: str = client_info[0]
        client_address: str = client_info[2]
        client_id: int = client_info[3]

        orders: list = self.supabase.table("orders").select("*").eq("client_id", client_id).execute().data

        result: list = []

        for order in orders:
            service_id = order["service_id"]
            worker_id = order["worker_id"]

            service_info = self.service_manager.get_service_by_id(service_id)

            if worker_id is not None:
                worker_info = self.account_manager.get_account(worker_id)
                worker_name = worker_info[1]
            else:
                worker_name = "Не назначен"

            service_name = service_info[0]
            service_desc = service_info[1]
            service_price = service_info[2]

            status = order["status"]
            accept_date = order["accept_date"]
            finish_date = order["finish_date"]
            trouble_desc = order["trouble_description"]

            info = (client_name, client_phone, client_address, service_name, service_desc, service_price, worker_name, trouble_desc, status, accept_date, finish_date)
            result.append(info)

        return result

    def select_order(self, order_id: int, worker_id: int) -> bool:
        try:
            self.supabase.table("orders").update({"worker_id": worker_id, "status": "В работе"}).eq("id", order_id).execute()
            return True
        except APIError as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Заказ не назначен, так как введено что-то что не является ID заказа или ID работника")
            else:
                logger.error(msg)
                return False

    def finish_order(self, order_id: int) -> bool:
        try:
            self.supabase.table("orders").update({"status": "Завершен", "finish_date": now_date}).eq("id", order_id).execute()
            return True
        except APIError as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Заказ не завершен, так как введено что-то что не является ID заказа")
            else:
                logger.error(msg)
                return False