import bcrypt
from dataclasses import dataclass
from supabase import Client
from logger_config import logger

class LoginMatchError(Exception): pass
class WrongCredentialsError(Exception): pass
class WorkerNotExistsError(Exception): pass

class WorkerManager:
    def __init__(self, client: Client):
        self.client: Client = client

    def login_worker(self, login: str, password: str) -> Worker | None:
        response: list = self.client.table("workers").select("id, name, role, password").eq("login", login).execute().data

        if not response:
            raise WrongCredentialsError("Неверный логин или пароль")

        worker_info = response[0]
        a_id = worker_info["id"]
        name = worker_info["name"]
        role = worker_info["role"]
        hashed_password = worker_info["password"]

        if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
            raise WrongCredentialsError("Неверный логин или пароль")

        logger.info(f"Аккаунт найден! Имя: {name}, Роль: {role}")

        worker = Worker(name=name, role=role, id=a_id)

        return worker

    def register_worker(self, name: str, new_login: str, new_password: str) -> Worker | None:
        if not name or not new_login or not new_password:
            raise ValueError("Все поля должны быть заполнены!")

        hashed_password: str = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        try:
            worker_info = self.client.table("workers").insert({"name": name, "login": new_login, "password": hashed_password}).execute().data[0]
        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg or "unique" in msg:
                raise LoginMatchError("Логин уже существует!")
            else:
                logger.error(msg)
                return None

        logger.info(f"Аккаунт создан! Имя: {name}, Логин: {new_login}")
        worker = Worker(name=name, role="Не назначена", id=worker_info["id"])
        return worker

    def change_role(self, worker_id: int, new_role: str) -> bool:
        try:
            worker_info = self.client.table("workers").update({"role": new_role}).eq("id", worker_id).execute().data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Аккаунт не найден, так как введено что-то что не является ID аккаунта")
            else:
                logger.error(msg)
                return False

        if not worker_info:
            raise WorkerNotExistsError(f"Аккаунт с ID {worker_id} не найден, так как его не существует")

        logger.info(f"Аккаунту '{worker_info[0]["name"]}' присвоена роль '{new_role}')")
        return True

    def get_all_workers(self) -> list[Worker]:
        workers: list = self.client.table("workers").select("*").execute().data

        if not workers:
            raise WorkerNotExistsError("В базе данных нет аккаунтов")

        result: list = []

        for worker_info in workers:
            name: str = worker_info["name"]
            role: str = worker_info["role"]
            a_id: int = worker_info["id"]

            logger.info(f"ID: {a_id} | Имя: {name} | Роль: {role}")

            worker = Worker(name=name, role=role, id=a_id)
            result.append(worker)

        return result

    def get_worker(self, worker_id: int) -> Worker | None:
        try:
            worker_info: list = self.client.table("workers").select("*").eq("id", worker_id).execute().data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Аккаунт не найден, так как введено что-то что не является ID аккаунта")
            else:
                logger.error(msg)
                return None

        if not worker_info:
            raise WorkerNotExistsError(f"Аккаунт с ID {worker_id} не найден, так как его не существует")

        name: str = worker_info[0]["name"]
        job: str = worker_info[0]["job"]
        a_id: int = worker_info[0]["id"]

        logger.info(f"ID: {a_id} | Имя: {name} | Роль: {job}")
        worker = Worker(name=name, role=job, id=a_id)

        return worker

    def delete_worker(self, worker_id: int) -> bool:
        try:
            response = self.client.table("workers").delete().eq("id", worker_id).execute().data
        except Exception as e:
            msg = str(e)
            if "invalid input" in msg:
                raise ValueError(f"Аккаунт не удален, так как введено что-то что не является ID аккаунта")
            else:
                logger.error(msg)
                return False

        if not response:
            raise WorkerNotExistsError(f"Аккаунт с ID {worker_id} не удален, так как его не существует")

        logger.info(f"Аккаунт с ID {worker_id} успешно удален")
        return True


@dataclass(frozen=True, order=True)
class Worker:
    name: str
    role: str
    id: int