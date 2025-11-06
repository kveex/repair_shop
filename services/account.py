from postgrest import APIResponse, APIError
from supabase import Client

class LoginMatchError(Exception): pass
class AccountNotExistsError(Exception): pass

def login_account(client: Client, login: str, password: str) -> bool:
    response: APIResponse = client.table("accounts").select("name, job").eq("login", login).eq("password", password).execute().data

    if not response:
        print("Неверный логин или пароль")
        return False
    else:
        name: str = response[0]["name"]
        job: str = response[0]["job"]
        print(f"Добро пожаловать, {name}, ваша роль: {job}")
        return True

def register_account(client: Client, name: str, role: str, new_login: str, new_password: str) -> int:
    if not name or not role or not new_login or not new_password:
        raise ValueError("Все поля должны быть заполнены!")

    try:
        response = client.table("accounts").insert({"name": name, "job": role, "login": new_login, "password": new_password}).execute()
        print("Аккаутн создан")
        return response.data[0]["id"]
    except APIError as e:
        msg = str(e)     
        if "duplicate key" in msg or "unique" in msg:
            raise LoginMatchError("Логин уже существует!")
        else:
            print("❌ Ошибка:", msg)
            print("Попробуйте снова.\n")

def get_all_accounts(client: Client) -> list:
    accounts: APIResponse = client.table("accounts").select("*").execute().data

    result: list = []

    for account in accounts:
        name: str = account["name"]
        job: str = account["job"]
        a_id: int = account["id"]

        print(f"ID: {a_id} | Имя: {name} | Роль: {job}")

        result.append((name, job, a_id))

    return result

def get_account(client: Client, account_id: int) -> tuple[str, str, int]:
    try:
        account: APIResponse = client.table("accounts").select("*").eq("id", account_id).execute().data
    except APIError as e:
        msg = str(e)
        if "invalid input" in msg:
            raise ValueError(f"Аккаунт не найден, так как введено что-то что не является ID аккаунта")
        else:
            print("❌ Ошибка:", msg)
            print("Попробуйте снова.\n")
            return

    if account == []:
        raise AccountNotExistsError(f"Аккаунт с ID {account_id} не найден, так как его не существует")

    name: str = account[0]["name"]
    job: str = account[0]["job"]
    a_id: int = account[0]["id"]

    return name, job, a_id

def delete_account(client: Client, account_id: int) -> bool:
    try:
        response = client.table("accounts").delete().eq("id", account_id).execute()
    except APIError as e:
        msg = str(e)
        if "invalid input" in msg:
            raise ValueError(f"Аккаунт не удален, так как введено что-то что не является ID аккаунта")
        else:
            print("❌ Ошибка:", msg)
            print("Попробуйте снова.\n")
            return

    if response.data != []:
        print(f"Аккаунт с ID {account_id} успешно удален")
        return True
    else:
        raise AccountNotExistsError(f"Аккаунт с ID {account_id} не удален, так как его не существует")