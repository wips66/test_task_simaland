import json
from aiohttp import web
from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from data_processing import get_user_data, \
    compare_password, \
    check_permissions, \
    create_session_token, \
    get_expires_time, \
    get_auth_token_from_cookie, \
    get_user_data_from_request, \
    fix_datetime_to_str, \
    get_user_id_from_request
from db import get_user_data_from_db, \
    save_token_in_db, \
    delete_token_from_db, \
    get_user_token_data_from_db, \
    create_user, \
    get_list_users, \
    delete_user, \
    update_user

routes = web.RouteTableDef()


# Ideally use the JWT token, but not today
@routes.view('/login')
class LoginView(web.View):
    async def post(self):
        """entry point authentication and authorization"""
        # check authorized and permission
        engine = self.request.app['db']
        user_data = await get_user_data(self.request)
        user_data_db = await get_user_data_from_db(engine, user_data)
        if not user_data_db:
            raise web.HTTPForbidden
        is_authenticated = compare_password(user_data['password'], user_data_db['password'])
        is_blocked, is_admin = check_permissions(user_data_db)
        if is_authenticated and not is_blocked:
            session_token = create_session_token()
            session_token_expires = get_expires_time()
            try:
                await save_token_in_db(engine,
                                       user_id=user_data_db['id'],
                                       token=session_token,
                                       token_expire=session_token_expires)
            except IntegrityError:
                raise web.HTTPConflict
            request = web.HTTPOk()
            request.set_cookie(name='auth_token', value=session_token)
            return request
        else:
            return web.HTTPForbidden


@routes.view('/logout')
class LogoutView(web.View):
    async def post(self):
        """sign out authentication and authorization"""
        engine = self.request.app['db']
        cookies = self.request.cookies
        if 'auth_token' in cookies.keys():
            await delete_token_from_db(engine, cookies['auth_token'])
            request = web.HTTPOk()
            request.del_cookie(name='auth_token')
            return request
        else:
            return web.HTTPForbidden


@routes.view('/user')
class CRUDView(web.View):
    async def post(self):
        """Create method of this app"""
        engine = self.request.app['db']
        # check authorized and permission
        cookies = self.request.cookies
        auth_token = get_auth_token_from_cookie(cookies)

        try:
            user_data_db = await get_user_token_data_from_db(engine, auth_token)
            is_blocked, is_admin = check_permissions(user_data_db)
        except AttributeError:
            raise web.HTTPForbidden()

        if not is_blocked and is_admin:
            user_data = await get_user_data_from_request(self.request)
            try:
                await create_user(engine, user_data)
            except (IntegrityError, UniqueViolationError):
                raise web.HTTPConflict()
            return web.HTTPOk()
        return web.HTTPForbidden()

    async def get(self):
        """Read method of this app"""
        engine = self.request.app['db']
        # check authorized and permission
        cookies = self.request.cookies
        auth_token = get_auth_token_from_cookie(cookies)

        try:
            user_data_db = await get_user_token_data_from_db(engine, auth_token)
            is_blocked, is_admin = check_permissions(user_data_db)
        except AttributeError:
            raise web.HTTPForbidden()

        if not is_blocked:
            all_users = await get_list_users(engine)
            all_users = fix_datetime_to_str(all_users)
            all_users_json = json.dumps(all_users)
            return web.json_response(data=all_users_json)
        return web.HTTPForbidden

    async def delete(self):
        """Delete method of this app"""
        engine = self.request.app['db']
        # check authorized and permission
        cookies = self.request.cookies
        auth_token = get_auth_token_from_cookie(cookies)
        try:
            user_data_db = await get_user_token_data_from_db(engine, auth_token)
            is_blocked, is_admin = check_permissions(user_data_db)
        except AttributeError:
            raise web.HTTPForbidden()

        if not is_blocked and is_admin:
            user_id = await get_user_id_from_request(self.request)
            await delete_user(engine, user_id)
            return web.HTTPOk()
        return web.HTTPForbidden()

    async def patch(self):
        """Update method of this app"""
        engine = self.request.app['db']
        # check authorized and permission
        cookies = self.request.cookies
        auth_token = get_auth_token_from_cookie(cookies)
        try:
            user_data_db = await get_user_token_data_from_db(engine, auth_token)
            is_blocked, is_admin = check_permissions(user_data_db)
        except AttributeError:
            raise web.HTTPForbidden()

        if not is_blocked and is_admin:
            user_data = await get_user_data_from_request(self.request)

            try:
                await update_user(engine, user_data)
            except (IntegrityError, UniqueViolationError):
                raise web.HTTPConflict
            return web.HTTPOk()
        return web.HTTPForbidden()
