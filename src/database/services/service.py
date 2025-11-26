from supabase import Client
from postgrest import APIError
from logger_config import logger

class ServiceNotExists(Exception): pass
class ServiceExistsError(Exception): pass

class ServiceManager:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def add_service(self, name: str, description: str, price: int | None) -> int:
        if not name or not description: raise ValueError("Имя и описание услуги должны быть заполнены!")
        try:
            if price == "": price = None
            response = self.supabase.table("services").insert({"name": name, "description": description, "price": price}).execute()
            return response.data[0]["id"]
        except APIError as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise ServiceExistsError(f"Услуга с именем {name} уже существует!")
            else:
                raise ValueError(f"Ошибка при добавлении услуги {name}: {msg}")

    def delete_service(self, service_id: int) -> bool:
        if not service_id: raise ValueError("ID услуги должен быть заполнен!")

        response = self.supabase.table("services").select("*").eq("id", service_id).execute().data

        if not response:
            raise ServiceNotExists(f"Услуга с ID {service_id} не найдена")
        else:
            name: str = response[0]["name"]

            self.supabase.table("services").delete().eq("id", service_id).execute()
            logger.info(f"Услуга {name} успешно удалена")

            return True

    def get_all_services(self) -> list:
        services: list = self.supabase.table("services").select("*").execute().data
        result: list = []

        for service in services:
            s_id: int = service["id"]
            name: str = service["name"]
            description: str = service["description"]
            price: int = service["price"]

            logger.info(f"ID: {s_id} | Имя: {name} | Описание: {description} | Цена: {price}")

            result.append((name, description, price, s_id))

        return result

    def get_service_by_id(self, service_id: int) -> tuple[str, str, int, int] | None:
        try:
            service_info: list = self.supabase.table("services").select("*").eq("id", service_id).execute().data
        except APIError as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Услуга не найдена, так как введено что-то что не является ID услуги")
            else:
                logger.error(msg)
                return None

        service: tuple[str, str, int, int] = _give_service(service_info)

        return service

    def get_service_by_name(self, service_name: str) -> tuple[str, str, int | None, int]:
        if not service_name: raise ValueError("Название услуги не может быть пустым")

        service_info: list = self.supabase.table("services").select("*").eq("name", service_name).execute().data
        service = _give_service(service_info)

        return service

def _give_service(service_info: list) -> tuple[str, str, int, int]:
    if not service_info:
        raise ServiceNotExists("Услига не существует")

    s_id: int = service_info[0]["id"]
    name: str = service_info[0]["name"]
    description: str = service_info[0]["description"]
    price: int = service_info[0]["price"]

    return name, description, price, s_id