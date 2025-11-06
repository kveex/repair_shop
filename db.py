import os
import services.account as account
import services.order as order
import services.client as client
import services.service as service
from supabase import create_client, Client
from dotenv import load_dotenv

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_S_KEY")

load_dotenv()

supabase: Client = create_client(url, key)

#TODO: перевести все print() в logging

def run() -> None:
    task: int = int(input("Выберите что сделать:\n1. Регистрация\n2. Вход\n3. Показать все заказы\n4. Создать заказ\n5. Показать все аккаунты\n6. Удалить аккаунт\n7. Показать всех клиентов\n8. Удалить клиента\n9. Добавить услугу\n10. Удалить услугу\n11. Показать все услуги\n"))

    match task:
        case 1:
            good: int = -1
            while good == -1:
                name: str = input("Введите своё ФИО: ")
                role: str = input("Введите свою роль: ")
                new_login: str = input("Введите новый логин: ")
                new_password: str = input("Введите новый пароль: ")
                try:
                    good = account.register_account(supabase, name, role, new_login, new_password)
                except ValueError as e:
                    msg = str(e)
                    if "логин уже существует" in msg:
                        print("⚠️ Такой логин уже существует! Попробуйте другой.\n")
                        continue
                    elif "заполнены" in msg:
                        print("⚠️ Все поля должны быть заполнены!\n")
                        continue
                    else:
                        print("❌ Ошибка:", msg)
                        print("Попробуйте снова.\n")
                        continue
        case 2:
            good: bool = False
            while good == False:
                login: str = input("Логин: ")
                password: str = input("Пароль: ")
                good = account.login_account(supabase, login, password)
        case 3:
            order.get_all_orders(supabase)
        case 4:
            order.make_order(supabase)
        case 5:
            account.get_all_accounts(supabase)
        case 6:
            done: bool = False
            while done == False:
                account_id = int(input("Введите ID аккаунта для удаления: "))
                done = account.delete_account(supabase, account_id)
        case 7:
            client.get_all_clients(supabase)
        case 8:
            client_id = int(input("Введите ID клиента для удаления: "))
            try:
                client.delete_client(supabase, client_id)
            except ValueError:
                print("Клиент с таким ID не найден")
        case 9:
            service_name = input("Введите название услуги: ")
            service_desc = input("Введите описание услуги: ")
            service_price = int(input("Введите цену за услугу: "))
            service.add_service(supabase, service_name, service_desc, service_price)
        case 10:
            service_id = int(input("Введите ID услуги для удаления: "))
            service.delete_service(supabase, service_id)
        case 11:
            service.get_all_services(supabase)

if __name__ == "__main__":
    run()
