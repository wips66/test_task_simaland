import asyncio
import datetime
from data_processing import gen_hash_password
from sqlalchemy.engine import RowMapping
from settings import UserData, config, logger
from sqlalchemy import MetaData, Table, String, Integer, Column, DateTime, Boolean, ForeignKey, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)

users = Table("users", metadata,
              Column('id', Integer(), autoincrement=True, primary_key=True),
              Column('first_name', String(200), nullable=False),
              Column('last_name', String(200), nullable=False),
              Column('login', String(200), unique=True, nullable=False, index=True),
              Column('password', String(64), nullable=False),
              Column('birth_date', DateTime)
              )

permissions = Table("permissions", metadata,
                    Column('user_id', ForeignKey(users.c.id, ondelete="CASCADE"), primary_key=True),
                    Column('blocked', Boolean(), default=False),
                    Column('is_admin', Boolean(), default=False),
                    )

cookie_auth = Table("cookie_auth", metadata,
                    Column('user_id', ForeignKey(users.c.id, ondelete="CASCADE"), primary_key=True),
                    Column('token', String(200)),
                    Column('expire_time', Integer())
                    )


async def pg_context(app):
    """Init async connecting to DB"""
    conf = app['config']['postgres']
    engine = create_async_engine(conf['database_url'], echo=True)
    app['db'] = engine
    yield
    await app['db'].dispose()
    logger.info("Connetcting to DB is close")


# async def sign_in(engine: AsyncEngine):
#     pass
#
#
# async def sign_out(engine: AsyncEngine):
#     pass
#
#
# async def check_authenticate(user_data: UserData) -> bool:
#     pass
#
#
# async def get_user(engine: AsyncEngine, user_id: int) -> UserData:
#     pass


async def create_user(engine: AsyncEngine, user_data: UserData) -> None:
    """Query for create new user in DB"""
    async with engine.begin() as conn:
        new_user_query = users.insert().values(first_name=user_data['first_name'],
                                               last_name=user_data['last_name'],
                                               login=user_data['login'],
                                               password=user_data['password'],
                                               birth_date=user_data['birth_date'],
                                               ).returning(users.c.id)
        result = await conn.execute(new_user_query)
        user_id = result.all()[0][0]  # crutch
        if 'blocked' and 'is_admin' in user_data.keys():
            user_permissions = permissions.insert().values(user_id=user_id,
                                                           blocked=user_data['blocked'],
                                                           is_admin=user_data['is_admin'])
        else:
            user_permissions = permissions.insert().values(user_id=user_id)
        await conn.execute(user_permissions)


async def get_list_users(engine: AsyncEngine) -> list[RowMapping]:
    """Returns a list of all users"""
    async with engine.connect() as conn:
        all_users_query = select([users.c.id,
                                  users.c.first_name,
                                  users.c.last_name,
                                  users.c.login,
                                  users.c.birth_date,
                                  permissions.c.blocked,
                                  permissions.c.is_admin]).select_from(users.join(permissions))
        all_users = await conn.execute(all_users_query)
        return all_users.mappings().all()


async def update_user(engine: AsyncEngine, user_data: UserData):
    """Updating user data"""
    async with engine.begin() as conn:
        update_user_query = users.update().where(users.c.id == user_data['id']).values(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            login=user_data['login'],
            password=user_data['password'],
            birth_date=user_data['birth_date'],
        )
        await conn.execute(update_user_query)

        if 'blocked' and 'is_admin' in user_data.keys():
            user_permissions = permissions.update().where(permissions.c.user_id == user_data['id']) \
                .values(blocked=user_data['blocked'],
                        is_admin=user_data[
                            'is_admin'])
            await conn.execute(user_permissions)


async def delete_user(engine: AsyncEngine, user_id: int) -> None:
    """Deletes the user from all linked tables"""
    async with engine.connect() as conn:
        delete_user_query = users.delete().where(users.c.id == user_id)
        await conn.execute(delete_user_query)
        await conn.commit()


async def get_user_data_from_db(engine: AsyncEngine, user_data: UserData) -> RowMapping | None:
    """Returns user data from the database"""
    async with engine.connect() as conn:
        get_user_query = select([users.c.id,
                                 users.c.login,
                                 users.c.password,
                                 permissions.c.blocked,
                                 permissions.c.is_admin]).select_from(users.join(permissions)) \
            .where(users.c.login == user_data['login'])
        result = await conn.execute(get_user_query)
    return result.mappings().fetchone()


async def save_token_in_db(engine: AsyncEngine, user_id: int, token: str, token_expire: int) -> None:
    """Deletes an existing token and adds a new one"""
    async with engine.begin() as conn:
        delete_old_cookies_query = cookie_auth.delete().where(cookie_auth.c.user_id == user_id)
        await conn.execute(delete_old_cookies_query)
        save_token_query = cookie_auth.insert().values(user_id=user_id,
                                                       token=token,
                                                       expire_time=token_expire
                                                       )
        await conn.execute(save_token_query)


async def delete_token_from_db(engine: AsyncEngine, token: str) -> None:
    """Deletes the user's token from the database"""
    async with engine.connect() as conn:
        delete_token_query = cookie_auth.delete().where(cookie_auth.c.token == token)
        await conn.execute(delete_token_query)
        await conn.commit()


async def get_user_token_data_from_db(engine: AsyncEngine, token: str) -> RowMapping | None:
    """Returns user permissions for the specified token"""
    async with engine.connect() as conn:
        get_user_query = select([permissions.c.blocked,
                                 permissions.c.is_admin]). \
            select_from(permissions.join(cookie_auth,
                                         cookie_auth.c.user_id == permissions.c.user_id)) \
            .where(cookie_auth.c.token == token)
        result = await conn.execute(get_user_query)
    return result.mappings().fetchone()


if __name__ == '__main__':
    # kludge!!! only test. Don't do this in production

    #  kludge
    admin_data = {'first_name': 'admin',
                  'last_name': 'admin',
                  'login': 'admin',
                  'password': gen_hash_password('admin'),
                  'birth_date': datetime.datetime(1970, 1, 1, 0, 0),
                  'blocked': False,
                  'is_admin': True
                  }

    async def kludge_init_database():
        """wtf!? THIS IS KLUDGE"""
        logger.info("Connect to the database to delete all tables "
                    "and create new ones with the first admin user")
        engine = create_async_engine(config['postgres']['database_url'], echo=True)
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
            await conn.run_sync(metadata.create_all)
        user_data = UserData(**admin_data)
        await create_user(engine, user_data)

    asyncio.run(kludge_init_database())