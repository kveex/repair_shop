from supabase import Client
from services.client import get_client, add_client
from services.account import get_account
from services.service import get_service_by_id, get_service_by_name
from datetime import datetime

#TODO: Сделать метод на взятие информации о заказе

def make_order_new_client(supabase: Client, client_name: str, client_phone: str, client_address: str, service_name: str, trouble_description: str) -> tuple[int, bool]:
    client_id = add_client(supabase, client_name, client_phone, client_address)
    good = make_order(supabase, client_phone, service_name, trouble_description)
    return client_id, good

def make_order(supabase: Client, client_phone: str, service_name: str, trouble_description: str) -> bool:
    client_info: tuple[str, str, str, int] = get_client(supabase, client_phone)
    if client_info == None: raise ValueError("Такого клиента не существует")

    service_info: tuple[str, str, int | None, int] = get_service_by_name(supabase, service_name)
    if service_info == None: raise ValueError("Такого сервиса не существует")

    client_id = client_info[3]
    service_id = service_info[3]

    if trouble_description == "" : trouble_description = "Не описано"

    accept_time: str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    supabase.table("orders").insert({"client_id": client_id, "service_id": service_id, "trouble_description": trouble_description, "accept_date": accept_time}).execute()
    return True

def get_all_orders(supabase: Client) -> list:
    orders: list = supabase.table("orders").select("*").execute().data
    services: list = supabase.table("services").select("*").execute().data
    clients: list = supabase.table("clients").select("*").execute().data
    workers: list = supabase.table("accounts").select("id, name").execute().data

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
        client_address = client.get("address") if not client.get("address") == None else "Не выдан"

        service_name = service.get("name", "Не найдено")
        service_desc = service.get("description", "Не найдено")
        service_price = service.get("price") if not service.get("price") == None else "Нет точной до завершения" 

        worker_name = worker.get("name", "Не назначен")
        trouble_desc = order.get("trouble_description") if not order.get("trouble_description") == None else "Не описана"
        status = order.get("status")
        accept_date = datetime.fromisoformat(order.get("accept_date")).strftime("%d/%m/%Y %H:%M:%S")
        finish_date = datetime.fromisoformat(order.get("finish_date")).strftime("%d/%m/%Y %H:%M:%S") if not order.get("finish_date") == None else "Не завершен"

        print(
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

def get_order(supabase: Client, client_phone: str) -> list:
    client_info: int = get_client(supabase, client_phone)

    client_name: str = client_info[0]
    client_address: str = client_info[2]
    client_id: int = client_info[3]

    orders: list = supabase.table("orders").select("*").eq("client_id", client_id).execute().data

    retult: list = []

    for order in orders:    
        service_id = order["service_id"]
        worker_id = order["worker_id"]
        
        service_info = get_service_by_id(supabase, service_id)
        
        if worker_id != None:
            worker_info = get_account(supabase, worker_id)
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
        retult.append(info)

    return retult