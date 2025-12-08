from supabase import Client as SupabaseClient
from dataclasses import dataclass
from logger_config import logger

class ClientNotExistsError(Exception): pass
class ClientExistsError(Exception): pass

@dataclass(frozen=True, order=True)
class Client:
    name: str
    phone: str
    id: int
    address: str | None = None

class ClientManager:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    def delete_client(self, client_id: int) -> bool:
        try:
            response = self.supabase.table("clients").delete().eq("id", client_id).execute().data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError("Клиент не удалён, так как введено что-то, что не является ID клиента")
            else:
                logger.error(msg)
                return False

        if not response:
            raise ClientNotExistsError(f"Клиент с ID {client_id} не удален, так как его не существует")

        logger.info(f"Клиент с ID {client_id} успешно удален")
        return True

    def get_all_clients(self) -> list[Client]:
        clients: list = self.supabase.table("clients").select("*").execute().data

        if not clients:
            raise ClientNotExistsError("Клиентов в базе данных нет")

        result: list = []

        for client_info in clients:
            name: str = client_info["name"]
            phone: str = client_info["phone"]
            address: str = client_info["address"]
            c_id: int = client_info["id"]

            logger.info(f"ID: {c_id} | Имя: {name} | Телефон: {phone} | Адрес: {address}")

            client = Client(name=name, phone=phone, id=c_id, address=address)

            result.append(client)

        return result

    def add_client(self, name: str, phone: str, address: str = None) -> Client:
        if len(phone) != 12 or phone[0:2] != "+7": raise ValueError("Номер телефона должен состоять из 11 цифр и начинаться с +7")
        if name == "": raise ValueError("Имя клиента не может быть пустым")
        if address == "": address = None

        try:
            response = self.supabase.table("clients").insert({"name": name, "phone": phone, "address": address}).execute().data
            logger.info(f"Клиент {name} успешно добавлен")
        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise ClientExistsError(f"Клиент с номером телефона {phone} уже существует!")
            else:
                raise ValueError(f"Ошибка при добавлении клиента {name}: {msg}")

        client_info = response[0]

        return Client(name=name, phone=phone, id=client_info["id"], address=address)

    def get_client(self, client_phone: str) -> Client:
        if len(client_phone) != 12 or client_phone[0:2] != "+7": raise ValueError("Номер телефона должен состоять из 11 цифр и начинаться с +7")

        client_info: list = self.supabase.table("clients").select("*").eq("phone", client_phone).execute().data

        if not client_info:
            raise ClientNotExistsError(f"Клиент с номером телефона [{client_phone}] не найден")

        c_id: int = client_info[0]["id"]
        phone: str = client_info[0]["phone"]
        name: str = client_info[0]["name"]
        address: str = client_info[0]["address"] if not client_info[0]["address"] is None else "Не выдан"

        logger.info(f"ID: {c_id} | Имя: {name} | Телефон: {phone} | Адрес: {address}")

        return Client(name=name, phone=phone, id=c_id, address=address)