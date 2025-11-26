import bcrypt
from postgrest import APIResponse, APIError
from supabase import Client
from logger_config import logger
class LoginMatchError(Exception): pass
class AccountNotExistsError(Exception): pass

class AccountManager:
    def __init__(self, client: Client):
        self.client: Client = client

    def login_account(self, login: str, password: str) -> str | None:
        response: list = self.client.table("accounts").select("name, job, password").eq("login", login).execute().data

        if not response:
            logger.error("Неверный логин или пароль")
            return None

        account = response[0]
        hashed_password = account["password"]
        if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
            logger.error("Неверный логин или пароль")
            return None

        logger.info(f"Аккаунт найден! Имя: {account["name"]}, Роль: {account["job"]}")
        return account["job"]

    def register_account(self, name: str, new_login: str, new_password: str) -> int | None:
        if not name or not new_login or not new_password:
            raise ValueError("Все поля должны быть заполнены!")

        hashed_password: str = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        try:
            response = self.client.table("accounts").insert({"name": name, "login": new_login, "password": hashed_password}).execute()
            logger.info(f"Аккаунт создан! Имя: {name}, Логин: {new_login}")
            return response.data[0]["id"]
        except APIError as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise LoginMatchError("Логин уже существует!")
            else:
                logger.error(msg)
                return None

    def change_role(self, account_id: int, new_job: str) -> bool:
        try:
            response = self.client.table("accounts").update({"job": new_job}).eq("id", account_id).execute()
            acc = response.data[0]
            logger.info(f"Роль {acc["name"]} изменена на {new_job}")
            return True
        except APIError as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise LoginMatchError("Логин уже существует!")
            else:
                logger.error(msg)
                return False

    def get_all_accounts(self) -> list:
        accounts: list = self.client.table("accounts").select("*").execute().data

        result: list = []

        for account in accounts:
            name: str = account["name"]
            job: str = account["job"]
            a_id: int = account["id"]

            logger.info(f"ID: {a_id} | Имя: {name} | Роль: {job}")

            result.append((name, job, a_id))

        return result

    def get_account(self, account_id: int) -> tuple[str, str, int] | None:
        try:
            account: list = self.client.table("accounts").select("*").eq("id", account_id).execute().data
        except APIError as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Аккаунт не найден, так как введено что-то что не является ID аккаунта")
            else:
                logger.error(msg)
                return None

        if not account:
            raise AccountNotExistsError(f"Аккаунт с ID {account_id} не найден, так как его не существует")

        name: str = account[0]["name"]
        job: str = account[0]["job"]
        a_id: int = account[0]["id"]

        logger.info(f"ID: {a_id} | Имя: {name} | Роль: {job}")

        return name, job, a_id

    def delete_account(self, account_id: int) -> bool:
        try:
            response: APIResponse = self.client.table("accounts").delete().eq("id", account_id).execute()
        except APIError as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Аккаунт не удален, так как введено что-то что не является ID аккаунта")
            else:
                logger.error(msg)
                return False

        if response.data:
            logger.info(f"Аккаунт с ID {account_id} успешно удален")
            return True
        else:
            raise AccountNotExistsError(f"Аккаунт с ID {account_id} не удален, так как его не существует")