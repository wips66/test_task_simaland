import datetime
import uuid
from hashlib import pbkdf2_hmac
from json import JSONDecodeError
from typing import Mapping
from aiohttp.web_request import Request
from aiohttp.web import HTTPBadRequest
from sqlalchemy.engine import RowMapping
from settings import HASH_SALT, HASH_NAME, TOKEN_EXPIRES, UserData


def gen_hash_password(password: str) -> pbkdf2_hmac:
    """Returns password hash"""
    hash_password = pbkdf2_hmac(hash_name=HASH_NAME,
                                password=password.encode(),
                                salt=HASH_SALT,
                                iterations=1000)
    return hash_password.hex().upper()


async def get_user_data_from_request(request: Request) -> UserData:
    """Parsing a user request. Returns query data"""
    try:
        user_data = await request.json()
        is_valid_data = validate_user_data(user_data)
    except (AttributeError, JSONDecodeError):
        raise HTTPBadRequest
    if is_valid_data:
        user_data['password'] = gen_hash_password(user_data['password'])
        user_data['birth_date'] = make_correct_date(user_data['birth_date'])
        user_data = UserData(**user_data)
    return user_data


def validate_user_data(user_data: UserData) -> bool:
    """Stupid (easy) data validation"""
    if user_data.get('first_name') and \
            user_data.get('last_name') and \
            user_data.get('login') and \
            user_data.get('password') and \
            user_data.get('birth_date'):
        return True
    else:
        raise HTTPBadRequest(body="JSON is broken")


def make_correct_date(request_date: str) -> datetime:
    """Returns the date data type from the string"""
    try:
        correct_date = datetime.datetime.strptime(request_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPBadRequest
    return correct_date


def fix_datetime_to_str(list_users: list[RowMapping]) -> list[dict]:
    """Corrects the data type from the database"""
    list_users = [dict(user_data) for user_data in list_users]
    for num, user_data in enumerate(list_users):
        list_users[num]['birth_date'] = str(user_data['birth_date'])
    return list_users


async def get_user_id_from_request(request: Request) -> int:
    """Returns the user id from a user request"""
    try:
        user_data = await request.json()
        user_id = user_data['id']
    except (KeyError, JSONDecodeError):
        raise HTTPBadRequest
    return user_id


def check_login_password_in_json(data: dict) -> bool:
    """Stupid (easy) data validation"""
    if "login" and "password" in data.keys():
        return True
    else:
        raise HTTPBadRequest


async def get_user_data(request: Request) -> UserData:
    """Returns user query from request"""
    try:
        user_data = await request.json()
        is_valid_data = check_login_password_in_json(user_data)
    except (AttributeError, JSONDecodeError):
        raise HTTPBadRequest
    if is_valid_data:
        user_data['password'] = gen_hash_password(user_data['password'])
        user_data = UserData(**user_data)
    return user_data


def check_permissions(user_data: RowMapping) -> (bool, bool):
    """Returns permissions for a user from the database"""
    return user_data.get('blocked', True), user_data.get('is_admin', False)


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