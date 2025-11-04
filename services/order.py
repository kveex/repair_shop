from supabase import Client
from services.client import get_client
from services.managment import get_service
import datetime

def make_order(supabase: Client) -> None:
    client_info: tuple[str, str, str, int] = get_client(supabase)
    service_info: tuple[str, str, int | None, int] = get_service(supabase)
    new_client: bool = False

    if not client_info is None:
        client_name, client_phone, client_address, client_id = client_info
    else:
        client_name: str = input("Введите ФИО клиента: ")
        client_phone: str = input("Введите номер телефона клиента: ")
        client_address: str = input("Введите адрес клиента (не обязательно): ")
        if not client_address: client_address = None
        new_client = True

    if not service_info is None:
        service_name, service_description, service_price, service_id = service_info
        if service_price is None:
            service_price = "Плавающая"
    
    trouble_description: str = input("Опишите проблему:\n")

    do: str = input(
        f"Всё верно?"
        f"\ФИО клиента: {client_name}"
        f"\nНомер телефона: {client_phone}"
        f"\nАдрес: {client_address}"
        f"\nНазвание услуги: {service_name}"
        f"\nОписание услуги: {service_description}"
        f"\nЦена за услугу: {service_price}"
        f"\nОписание проблемы: {trouble_description}"
        f"\n([д|да]/[н|нет]): "
        )
    
    accept_time: str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    match do.lower():
            case "д" | "да":
                if new_client:
                    supabase.table("clients").insert({"name": client_name, "phone": client_phone, "address": client_address}).execute()
                    client_id = supabase.table("clients").select("id").eq("phone", client_phone).execute().data[0]["id"]
                supabase.table("orders").insert({"client_id": client_id, "service_id": service_id, "trouble_description": trouble_description, "accept_date": accept_time}).execute()
            case "н" | "нет":
                pass
            case _:
                print("Неизвестная команда!")

def get_all_orders(supabase: Client) -> None:
    orders = supabase.table("orders").select("*").execute().data
    services = supabase.table("services").select("*").execute().data
    clients = supabase.table("clients").select("*").execute().data
    workers = supabase.table("accounts").select("id, name").execute().data

    # Превращаем списки в словари для быстрого поиска
    services_dict = {s["id"]: s for s in services}
    clients_dict = {c["id"]: c for c in clients}
    workers_dict = {w["id"]: w for w in workers}

    for order in orders:
        client = clients_dict.get(order["client_id"], {})
        service = services_dict.get(order["service_id"], {})
        worker = workers_dict.get(order["worker_id"], {})

        client_name = client.get("name", "Не найдено")
        client_phone = client.get("phone", "Не найдено")
        client_address = client.get("address", "Не найдено")

        service_name = service.get("name", "Не найдено")
        service_desc = service.get("description", "Не найдено")
        service_price = service.get("price", "Не найдено")

        worker_name = worker.get("name", "Не назначен")

        print(
            f"\nИмя клиента: {client_name}"
            f"\nНомер телефона клиента: {client_phone}"
            f"\nАдрес клиента: {client_address}"
            f"\nНазвание сервиса: {service_name}"
            f"\nОписание сервиса: {service_desc}"
            f"\nЦена сервиса: {service_price}"
            f"\nИмя работника: {worker_name}"
            f"\nОписание проблемы: {order.get('trouble_description')}"
            f"\nСтатус: {order.get('status')}"
            f"\nВремя принятия: {order.get('accept_date')}"
            f"\nВремя завершения: {order.get('finish_date')}"
        )