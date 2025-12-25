import logging
import os

# Папка для логов
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Основная конфигурация логирования
logging.basicConfig(
    level=logging.INFO,  # уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/app.log", encoding="utf-8"),
        logging.StreamHandler()  # вывод в консоль
    ]
)

# Пример: создать отдельный логгер для конкретного модуля
logger = logging.getLogger("repair_shop")
logging.getLogger("realtime").setLevel(logging.WARNING)
