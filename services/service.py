from supabase import Client
from postgrest import APIError

class ServiceNotExists(Exception): pass
class ServiceExistsError(Exception): pass

def add_service(supabase: Client, name: str, description: str, price: int | None) -> int:
    if not name or not description: raise ValueError("Имя и описание услуги должны быть заполнены!")
    try:
        if price == "": price = None
        response = supabase.table("services").insert({"name": name, "description": description, "price": price}).execute()
        return response.data[0]["id"]
    except APIError as e:
        msg = str(e)
        if "duplicate key" in msg or "unique" in msg:
            raise ServiceExistsError(f"Услуга с именем {name} уже существует!")
        else:
            raise ValueError(f"Ошибка при добавлении услуги {name}: {msg}")

def delete_service(supabase: Client, service_id: int) -> bool:
    if not service_id: raise ValueError("ID услуги должен быть заполнен!")

    response = supabase.table("services").select("*").eq("id", service_id).execute().data

    if not response:
        raise ServiceNotExists(f"Услуга с ID {service_id} не найдена")
    else:
        name: str = response[0]["name"]

        supabase.table("services").delete().eq("id", service_id).execute()
        print(f"Услуга {name} успешно удалена")

        return True



def get_all_services(supabase: Client) -> list:
    services: list = supabase.table("services").select("*").execute().data
    result: list = []

    for service in services:
        s_id: int = service["id"]
        name: str = service["name"]
        description: str = service["description"]
        price: int = service["price"]

        print(f"ID: {s_id} | Имя: {name} | Описание: {description} | Цена: {price}")

        result.append((name, description, price, s_id))

    return result

def get_service_by_id(supabase: Client, service_id: int) -> tuple[str, str, int | None, int]:
    try:
        service: list = supabase.table("services").select("*").eq("id", service_id).execute().data
    except APIError as e:
        msg = str(e)
        if "invalid input" in msg:
            raise ValueError(f"Услуга не найдена, так как введено что-то что не является ID услуги")
        else:
            print("❌ Ошибка:", msg)
            print("Попробуйте снова.\n")
            return

    if not service:
        raise ServiceNotExists(f"Услуга с ID {service_id} не найдена")

    s_id: int = service[0]["id"]
    name: str = service[0]["name"]
    description: str = service[0]["description"]
    price: int = service[0]["price"]

    return name, description, price, s_id

def get_service_by_name(supabase: Client, service_name: str) -> tuple[str, str, int | None, int]:
    if not service_name: raise ValueError("Название услуги не может быть пустым")
    
    service: list = supabase.table("services").select("*").eq("name", service_name).execute().data

    if not service:
        raise ServiceNotExists(f"Услуга с именем {service_name} не найдена")

    s_id: int = service[0]["id"]
    name: str = service[0]["name"]
    description: str = service[0]["description"]
    price: int = service[0]["price"]

    return name, description, price, s_id

