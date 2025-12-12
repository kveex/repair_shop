from supabase import AsyncClient
from logger_config import logger
from dataclasses import dataclass
class ServiceNotExistsError(Exception): pass
class ServiceExistsError(Exception): pass

@dataclass(frozen=True, order=True)
class Service:
    name: str
    description: str
    price: int | None
    id: int

class ServiceManager:
    def __init__(self, supabase: AsyncClient):
        self.supabase: AsyncClient = supabase

    async def add_service(self, name: str, description: str, price: int | None) -> Service:
        if not name or not description: raise ValueError("Имя и описание услуги должны быть заполнены!")
        try:
            if price == "": price = None
            response = await self.supabase.table("services").insert({"name": name, "description": description, "price": price}).execute()
            data = response.data
        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise ServiceExistsError(f"Услуга с именем {name} уже существует!")
            else:
                raise ValueError(f"Ошибка при добавлении услуги {name}: {msg}")

        return Service(name=name, description=description, price=price, id=data[0]["id"])

    async def delete_service(self, service: Service) -> bool:
        response = await self.supabase.table("services").delete().eq("id", service.id).execute()
        data = response.data

        if not data:
            raise ServiceNotExistsError(f"Услуга '{service.name}' не найдена")

        return True

    async def get_all_services(self) -> list[Service]:
        services = await self.supabase.table("services").select("*").execute()
        data = services.data
        result: list = []

        for service_info in data:
            s_id: int = service_info["id"]
            name: str = service_info["name"]
            description: str = service_info["description"]
            price: int = service_info["price"]

            logger.info(f"ID: {s_id} | Имя: {name} | Описание: {description} | Цена: {price}")

            service = Service(name=name, description=description, price=price, id=s_id)

            result.append(service)

        return result

    async def get_service(self, service_id: int) -> Service | None:
        try:
            service_info = await self.supabase.table("services").select("*").eq("id", service_id).execute()
            data = service_info.data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Услуга не найдена, так как введено что-то что не является ID услуги")
            else:
                logger.error(msg)
                return None

        if not data:
            raise ServiceNotExistsError("Услуга не найдена")

        name: str = data[0]["name"]
        description: str = data[0]["description"]
        price: int = data[0]["price"] | None
        s_id: int = data[0]["id"]

        service = Service(name=name, description=description, price=price, id=s_id)

        return service

    async def get_order_services(self, order) -> list[Service]:
        response = await self.supabase.table("order_services").select("*, services(*)").eq("order_id", order.id).execute()

        data = response.data
        result: list = []

        for info in data:
            service_info = info.get("services")
            service = Service(
                name=service_info.get("name"),
                description=service_info.get("description"),
                price=service_info.get("price"),
                id=service_info.get("id")
            )

            result.append(service)

        return result

    async def add_service_to_order(self, order, service: Service) -> bool:
        response = await self.supabase.table("order_services").insert({"order_id": order.id, "service_id": service.id}).execute()

        return bool(response.data)
