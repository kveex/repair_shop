from supabase import Client as SupabaseClient
from logger_config import logger
from dataclasses import dataclass
class ServiceNotExistsError(Exception): pass
class ServiceExistsError(Exception): pass

class ServiceManager:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    def add_service(self, name: str, description: str, price: int | None) -> Service:
        if not name or not description: raise ValueError("Имя и описание услуги должны быть заполнены!")
        try:
            if price == "": price = None
            response = self.supabase.table("services").insert({"name": name, "description": description, "price": price}).execute().data
        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise ServiceExistsError(f"Услуга с именем {name} уже существует!")
            else:
                raise ValueError(f"Ошибка при добавлении услуги {name}: {msg}")

        return Service(name=name, description=description, price=price, id=response[0]["id"])

    def delete_service(self, service_id: int) -> bool:
        if not service_id: raise ValueError("ID услуги должен быть заполнен!")

        response = self.supabase.table("services").select("*").eq("id", service_id).execute().data

        if not response:
            raise ServiceNotExistsError(f"Услуга с ID {service_id} не найдена")
        else:
            name: str = response[0]["name"]

            self.supabase.table("services").delete().eq("id", service_id).execute()
            logger.info(f"Услуга {name} успешно удалена")

            return True

    def get_all_services(self) -> list[Service]:
        services: list = self.supabase.table("services").select("*").execute().data
        result: list = []

        for service_info in services:
            s_id: int = service_info["id"]
            name: str = service_info["name"]
            description: str = service_info["description"]
            price: int = service_info["price"]

            logger.info(f"ID: {s_id} | Имя: {name} | Описание: {description} | Цена: {price}")

            service = Service(name=name, description=description, price=price, id=s_id)

            result.append(service)

        return result

    def get_service(self, service_id: int) -> Service | None:
        try:
            service_info: list = self.supabase.table("services").select("*").eq("id", service_id).execute().data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Услуга не найдена, так как введено что-то что не является ID услуги")
            else:
                logger.error(msg)
                return None

        if not service_info:
            raise ServiceNotExistsError("Услуга не найдена")

        name: str = service_info[0]["name"]
        description: str = service_info[0]["description"]
        price: int = service_info[0]["price"] | None
        s_id: int = service_info[0]["id"]

        service = Service(name=name, description=description, price=price, id=s_id)

        return service

@dataclass(frozen=True, order=True)
class Service:
    name: str
    description: str
    price: int | None
    id: int