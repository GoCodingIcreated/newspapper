import os
import sys
from pathlib import Path
from .credentionals import MONGO_IP, MONGO_PORT
from .credentionals import MONGO_STORE_API_USER, MONGO_STORE_API_PSWD
from .credentionals import MONGO_ALARM_USER, MONGO_ALARM_PSWD
from .credentionals import MONGO_SPIDER_USER, MONGO_SPIDER_PSWD

PROJECT_PATH = Path(__file__).parent.parent
ALERT_PATH = os.path.join(PROJECT_PATH, "alert")
ALERT_TELEGRAM_PATH = os.path.join(ALERT_PATH, "telegram")
CRAWL_PATH = os.path.join(PROJECT_PATH, "crawl")
STORE_PATH = os.path.join(PROJECT_PATH, "store")
LOGS_PATH = os.path.join(PROJECT_PATH, "logs")
COMMON_PATH = os.path.join(PROJECT_PATH, "common")

LOGGING_CONF_FILE_PATH = os.path.join(COMMON_PATH, "logging.json")


MONGO_STORE_API_URL = f"mongodb://{MONGO_STORE_API_USER}:{MONGO_STORE_API_PSWD}@{MONGO_IP}:{MONGO_PORT}"
MONGO_ALARM_URL = f"mongodb://{MONGO_ALARM_USER}:{MONGO_ALARM_PSWD}@{MONGO_IP}:{MONGO_PORT}"
MONGO_SPIDER_URL = f"mongodb://{MONGO_SPIDER_USER}:{MONGO_SPIDER_PSWD}@{MONGO_IP}:{MONGO_PORT}"


TOKEN_PATH = os.path.join(ALERT_TELEGRAM_PATH, "token.txt")

PIPELINE_MONGO_ITEM_DB = "crawler_storage"
PIPELINE_MONGO_ITEM_TABLE = "items"

# PIPELINE_JSON_DUMP_LOG_DIR = "../logs/crawl/dumps"
PIPELINE_JSON_DUMP_LOG_DIR = os.path.join(LOGS_PATH, "crawl/dumps")

STORE_MONGO_REPRESENTATIONS_DB = "store"
STORE_MONGO_REPRESENTATIONS_TABLE = "representations"

STORE_MONGO_USERS_DB = "store"
STORE_MONGO_USERS_TABLE = "users"

STORE_MONGO_BOOKS_TRACK_DB = "store"
STORE_MONGO_BOOKS_TRACK_TABLE = "tracks"

STORE_MONGO_BOOKS_DB = "store"
STORE_MONGO_BOOKS_TABLE = "books"

STORE_MONGO_PLATFORM_BOOK_VALIDATIONS_DB = "store"
STORE_MONGO_PLATFORM_BOOK_VALIDATIONS_TABLE = "validations"

STORE_MONGO_PLATFORM_BOOK_INFO_EXTRACTORS_DB = "store"
STORE_MONGO_PLATFORM_BOOK_INFO_EXTRACTORS_TABLE = "book_info_extractors"

ALARM_MONGO_ALERT_DB = "alert"
ALARM_MONGO_ALERT_TABLE = "telegram"
ALARM_TELEGRAM_PAUSE_ALERT_TIME_SEC = 5
ALARM_TELEGRAM_RETRIES = 3

ALERT_TELEGRAM_INIT_DB = "alert"
ALERT_TELEGRAM_INIT_TABLE = "telegram_init"


TELEGRAM_MESSAGE_MAX_LENGTH = 4096
