from json import JSONDecodeError
from aiohttp import web
from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from settings import logger
from data_processing import get_auth_token_from_cookie, check_permissions
from db import get_user_token_data_from_db


@logger.catch(reraise=True)
async def catch_exception(request, handler):
    response = await handler(request)
    return response


@web.middleware
async def middleware_logger(request, handler):
    logger.debug(f'{request.method} {request.url} from IP: {request.remote}')
    try:
        response = await catch_exception(request, handler)
    except (AttributeError, JSONDecodeError, KeyError, ValueError):
        raise web.HTTPBadRequest()
    except (IntegrityError, UniqueViolationError):
        raise web.HTTPConflict()
    except Exception:
        raise web.HTTPError()
    return response


@web.middleware
async def middleware_get_permissions_user(request, handler):
    engine = request.app['db']
    cookies = request.cookies
    request['auth_token'] = get_auth_token_from_cookie(cookies)
    user_data_db = await get_user_token_data_from_db(engine, request['auth_token'])
    request['is_blocked'], request['is_admin'] = check_permissions(user_data_db)
    response = await handler(request)
    return response
