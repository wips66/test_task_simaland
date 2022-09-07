import json
from aiohttp import web
from settings import UserList, User
from sqlalchemy.exc import IntegrityError
from data_processing import get_user_data, \
    compare_password, \
    create_session_token, \
    get_expires_time, \
    get_user_data_from_request, \
    get_user_id_from_request, \
    gen_hash_password
from db import get_user_data_from_db, \
    save_token_in_db, \
    delete_token_from_db, \
    create_user, \
    get_list_users, \
    delete_user, update_user

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
        if is_authenticated:
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
            return web.HTTPForbidden()


@routes.view('/logout')
class LogoutView(web.View):
    async def post(self):
        """sign out authentication and authorization"""
        if self.request['auth_token']:
            await delete_token_from_db(engine=self.request.app['db'], token=self.request['auth_token'])
            request = web.HTTPOk()
            request.del_cookie(name='auth_token')
            return request
        else:
            return web.HTTPForbidden()


@routes.view('/user')
class CRUDView(web.View):
    async def post(self):
        """Create method of this app"""
        if not self.request['is_blocked'] and self.request['is_admin']:
            user_data = await get_user_data_from_request(self.request)
            user_data.password = gen_hash_password(user_data.password)
            await create_user(engine=self.request.app['db'], user_data=user_data)
            return web.HTTPOk()
        return web.HTTPForbidden()

    async def get(self):
        """Read method of this app, returns list of all users"""
        if not self.request['is_blocked']:
            all_users = await get_list_users(engine=self.request.app['db'])
            all_users = UserList(users=[User.parse_obj(user) for user in all_users])
            return web.json_response(data=all_users.json(exclude={"users": {'__all__': {"password"}}}))
        return web.HTTPForbidden()

    async def delete(self):
        """Delete method of this app"""
        if not self.request['is_blocked'] and self.request['is_admin']:
            user_id = await get_user_id_from_request(self.request)
            await delete_user(engine=self.request.app['db'], user_id=user_id)
            return web.HTTPOk()
        return web.HTTPForbidden()

    async def patch(self):
        """Update method of this app"""
        if not self.request['is_blocked'] and self.request['is_admin']:
            user_data = await get_user_data_from_request(self.request)
            await update_user(engine=self.request.app['db'], user_data=user_data)
            return web.HTTPOk()
        return web.HTTPForbidden()
