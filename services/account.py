from postgrest import APIResponse, APIError
from supabase import Client

def login(supabase: Client) -> None:
    login: str = input("Логин: ")
    password: str = input("Пароль: ")

    response: APIResponse = supabase.table("accounts").select("name, job").eq("login", login).eq("password", password).execute().data

    if not response:
        print("Неверный логин или пароль")
    else:
        name: str = response[0]["name"]
        job: str = response[0]["job"]
        print(f"Добро пожаловать, {name}, ваша роль: {job}")

def register(supabase: Client) -> None:
    
    while True:
        name: str = input("Введите своё ФИО: ")
        role: str = input("Введите свою роль: ")
        new_login: str = input("Введите новый логин: ")
        new_password: str = input("Введите новый пароль: ")

        if not name or not role or not new_login or not new_password:
                    print("Какое-то из полей пустое!")
                    print(f"{name}\n{role}\n{new_login}\n{new_password}")
                    continue

        do: str = input(f"Всё верно?\nИмя: {name}\nРоль: {role}\nЛогин: {new_login}\nПароль: {new_password}\n([д|да]/[н|нет]): ").lower()
        
        match do.lower():
            case "д" | "да":
                try:
                    supabase.table("accounts").insert({"name": name, "job": role, "login": new_login, "password": new_password}).execute()
                    print("Аккаутн создан")
                    break
                except APIError as e:
                    msg = str(e)     
                    if "duplicate key" in msg or "unique" in msg:
                        print("⚠️ Такой логин уже существует! Попробуйте другой.\n")
                    else:
                        print("❌ Ошибка:", msg)
                        print("Попробуйте снова.\n")
            case "н" | "нет":
                print("Аккаунт не создан")
                break
            case _:
                  print("Неизвестная команда!")