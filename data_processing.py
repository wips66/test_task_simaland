import datetime
import uuid
from hashlib import pbkdf2_hmac
from json import JSONDecodeError
from typing import Mapping
from aiohttp.web_request import Request
from aiohttp.web import HTTPBadRequest
from sqlalchemy.engine import RowMapping
from settings import HASH_SALT, HASH_NAME, TOKEN_EXPIRES, UserData, User


def gen_hash_password(password: str) -> pbkdf2_hmac:
    """Returns password hash"""
    hash_password = pbkdf2_hmac(hash_name=HASH_NAME,
                                password=password.encode(),
                                salt=HASH_SALT,
                                iterations=1000)
    return hash_password.hex().upper()


async def get_user_data_from_request(request: Request) -> User:
    """Parsing a user request. Returns query data"""
    user_data = User.parse_raw(await request.text())

    return user_data


async def get_user_id_from_request(request: Request) -> int:
    """Returns the user id from a user request"""
    user_data = await request.json()
    user_id = user_data['id']
    return user_id


def check_login_password_in_json(data: dict) -> bool:
    """Stupid (easy) data validation"""
    if "login" and "password" in data.keys():
        return True
    else:
        raise HTTPBadRequest


async def get_user_data(request: Request) -> UserData:
    """Returns user query from request"""
    user_data = await request.json()
    is_valid_data = check_login_password_in_json(user_data)
    if is_valid_data:
        user_data['password'] = gen_hash_password(user_data['password'])
        user_data = UserData(**user_data)
    return user_data


def check_permissions(user_data: RowMapping) -> (bool, bool):
    """Returns permissions for a user from the database"""
    if user_data:
        return user_data.get('blocked', True), user_data.get('is_admin', False)
    else:
        return True, False


def compare_password(user_pass, user_pass_db):
    """password comparison"""
    return user_pass == user_pass_db


def create_session_token() -> str:
    """Generating a random token"""
    some_string = uuid.uuid4().hex
    token = gen_hash_password(some_string)
    return token


def get_expires_time() -> int:
    """Returns the token lifetime"""
    expires_time = datetime.datetime.utcnow() + TOKEN_EXPIRES
    return int(round(expires_time.timestamp()))


def get_time_utc_now_timestamp() -> int:
    """Returns the current time in timestamp format"""
    return int(round(datetime.datetime.utcnow().timestamp()))


def get_auth_token_from_cookie(cookies: Mapping) -> str | None:
    """Returns the authorization token from the cookie, if it is there"""
    token = cookies.get('auth_token', None)
    return token
