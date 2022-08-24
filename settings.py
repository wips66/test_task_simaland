import os
import pathlib
import datetime
from loguru import logger
import yaml
from enum import Enum
from typing import TypedDict

BASE_DIR = pathlib.Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
HASH_NAME = "sha256"
HASH_SALT = "fuck_your_password".encode()  # for example, not for prod!!!
TOKEN_EXPIRES = datetime.timedelta(1)  # 1day
LOG_DIR = os.path.join(os.path.dirname(__file__), 'log')

error_log_file_path = os.path.join(LOG_DIR, 'simaland_debug.log')
logger.add(sink=error_log_file_path,
           rotation="100 MB",
           format="{time} {level} {message}",
           enqueue=True,
           level=40,
           compression="zip")


def get_config(path):
    """Reads the yaml config and trans it into the dict"""
    with open(path) as file:
        parsed_config = yaml.safe_load(file)
    return parsed_config


config = get_config(CONFIG_PATH)


# For a beautiful realization
class RequestMethods(Enum):
    """Verbs specified in HTTP methods specs for requests"""
    CREATE = "POST"
    READ = "GET"
    UPDATE = "PATCH"
    DELETE = "DELETE"


class UserData(TypedDict):
    """User data in an easy-to-use format for development"""
    id: int
    first_name: str
    last_name: str
    login: str
    password: str
    birth_date: datetime.datetime
    blocked: bool
    is_admin: bool
