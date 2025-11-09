from src.database import _supabase
from src.logger_config import logger

a = _supabase.table("accounts").update({"job": "Техник"}).eq("id", 15).execute()
logger.info(a)