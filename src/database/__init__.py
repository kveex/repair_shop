import os
import asyncio
from typing import Optional
from supabase import AsyncClient, acreate_client
from dotenv import load_dotenv

from src.database.services.worker import WorkerManager
from src.database.services.order import OrderManager
from src.database.services.service import ServiceManager
from src.database.services.client import ClientManager

_lock = asyncio.Lock()
_supabase: Optional[AsyncClient] = None

_worker_manager: Optional[WorkerManager] = None
_order_manager: Optional[OrderManager] = None
_service_manager: Optional[ServiceManager] = None
_client_manager: Optional[ClientManager] = None

async def init_db(url: str | None = None, key: str | None = None) -> None:
    """
    Инициализация supabase + менеджеров. Можете вызывать при старте приложения.
    БЕЗОПАСНО вызывать несколько раз — инициализация выполнится один раз.
    """
    global _supabase, _worker_manager, _order_manager, _service_manager, _client_manager
    if _supabase is not None:
        return

    async with _lock:
        if _supabase is not None:
            return
        load_dotenv()
        url = url or os.environ.get("SUPABASE_URL")
        key = key or os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL / SUPABASE_KEY не заданы")

        _supabase = await acreate_client(url, key)

        _worker_manager = WorkerManager(_supabase)
        _order_manager = OrderManager(_supabase)
        _service_manager = ServiceManager(_supabase)
        _client_manager = ClientManager(_supabase)
        print("All done")

def get_supabase_sync() -> AsyncClient:
    """Синхронный геттер: возвращает клиент, если он уже инициализирован, иначе бросает."""
    if _supabase is None:
        raise RuntimeError("Supabase не инициализирован. Вызовите await init_db(...)")
    return _supabase

async def get_supabase() -> AsyncClient:
    if _supabase is None:
        await init_db()
    return _supabase

def get_worker_manager() -> WorkerManager:
    if _worker_manager is None:
        raise RuntimeError("Supabase не инициализирован. Вызовите await init_db(...)")
    return _worker_manager

def get_order_manager() -> OrderManager:
    if _order_manager is None:
        raise RuntimeError("Supabase не инициализирован. Вызовите await init_db(...)")
    return _order_manager

def get_service_manager() -> ServiceManager:
    if _service_manager is None:
        raise RuntimeError("Supabase не инициализирован. Вызовите await init_db(...)")
    return _service_manager

def get_client_manager() -> ClientManager:
    if _client_manager is None:
        raise RuntimeError("Supabase не инициализирован. Вызовите await init_db(...)")
    return _client_manager
