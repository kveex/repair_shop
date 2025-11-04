import os
import services.account as account
import services.order as order
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_S_KEY")
supabase: Client = create_client(url, key)

task: int = int(input("Выберите что сделать:\n1. Регистрация\n2. Вход\n3. Показать все заказы\n4. Создать заказ\n"))

match task:
    case 1:
        account.register(supabase)
    case 2:
        account.login(supabase)
    case 3:
        order.get_all_orders(supabase)
    case 4:
        order.make_order(supabase)