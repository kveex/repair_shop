from supabase import Client
from postgrest import APIError
from logger_config import logger

class ClientNotExistsError(Exception): pass
class ClientExistsError(Exception): pass

class ClientManager:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def delete_client(self, client_id: int) -> None:
        response = self.supabase.table("clients").delete().eq("id", client_id).execute()
        if response.data:
            logger.info(f"Клиент с ID {client_id} успешно удален")
        else:
            raise ClientNotExistsError(f"Клиент с ID {client_id} не удален, так как его не существует")

    def get_all_clients(self) -> list:
        clients: list = self.supabase.table("clients").select("*").execute().data

        result: list = []

        for client in clients:
            name: str = client["name"]
            phone: str = client["phone"]
            address: str = client["address"]
            c_id: int = client["id"]

            logger.info(f"ID: {c_id} | Имя: {name} | Телефон: {phone} | Адрес: {address}")

            result.append((name, phone, address, c_id))

        return result

    def add_client(self, name: str, phone: str, address: str = None) -> int:
        if len(phone) != 12 or phone[0:2] != "+7": raise ValueError("Номер телефона должен состоять из 11 цифр и начинаться с +7")
        if name == "": raise ValueError("Имя клиента не может быть пустым")
        if address == "": address = None

        try:
            response = self.supabase.table("clients").insert({"name": name, "phone": phone, "address": address}).execute()
            logger.info(f"Клиент {name} успешно добавлен")
        except APIError as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise ClientExistsError(f"Клиент с номером телефона {phone} уже существует!")
            else:
                raise ValueError(f"Ошибка при добавлении клиента {name}: {msg}")
        return response.data[0]["id"]

    def get_client(self, client_phone: str) -> tuple[str, str, str, int] | None:
        if len(client_phone) != 12 or client_phone[0:2] != "+7": raise ValueError("Номер телефона должен состоять из 11 цифр и начинаться с +7")

        client_exist: list = self.supabase.table("clients").select("*").eq("phone", client_phone).execute().data
        if client_exist:
            c_id: int = client_exist[0]["id"]
            phone: str = client_exist[0]["phone"]
            name: str = client_exist[0]["name"]
            address: str = client_exist[0]["address"] if not client_exist[0]["address"] is None else "Не выдан"

            logger.info(f"ID: {c_id} | Имя: {name} | Телефон: {phone} | Адрес: {address}")

            return name, phone, address, c_id
        return None