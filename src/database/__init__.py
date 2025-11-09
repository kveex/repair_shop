import os
from supabase import create_client, Client
from dotenv import load_dotenv

from src.database.services.account import AccountManager, LoginMatchError, AccountNotExistsError
from src.database.services.order import OrderManager
from src.database.services.client import ClientManager, ClientExistsError, ClientNotExistsError
from src.database.services.service import ServiceManager, ServiceExistsError, ServiceNotExists

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

_supabase: Client = create_client(url, key)

account_manager: AccountManager = AccountManager(_supabase)
order_manager: OrderManager = OrderManager(_supabase)
service_manager: ServiceManager = ServiceManager(_supabase)
client_manager: ClientManager = ClientManager(_supabase)