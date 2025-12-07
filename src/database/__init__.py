import os
from supabase import create_client, Client as SupabaseClient
from dotenv import load_dotenv

from src.database.services.worker import WorkerManager, LoginMatchError, WorkerNotExistsError, Worker
from src.database.services.order import OrderManager, Order
from src.database.services.client import ClientManager, ClientExistsError, ClientNotExistsError, Client
from src.database.services.service import ServiceManager, ServiceExistsError, ServiceNotExistsError, Service

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

_supabase: SupabaseClient = create_client(url, key)

worker_manager: WorkerManager = WorkerManager(_supabase)
order_manager: OrderManager = OrderManager(_supabase)
service_manager: ServiceManager = ServiceManager(_supabase)
client_manager: ClientManager = ClientManager(_supabase)