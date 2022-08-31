from aiohttp import web
from settings import config, logger
from db import pg_context
from handlers import routes
from middlewares import middleware_logger


@logger.catch()
async def make_app():
    logger.info("Start make app simaland")
    app = web.Application(middlewares=[middleware_logger])
    app['config'] = config
    logger.info("Config has been added to app")
    app.cleanup_ctx.append(pg_context)
    logger.info("Connecting to DB has been init")
    # aiohttp_debugtoolbar.setup(app)
    # aiohttp_swagger.setup_swagger(app)
    # fernet_key = fernet.Fernet.generate_key()
    # secret_key = base64.urlsafe_b64decode(fernet_key)
    # setup(app, EncryptedCookieStorage(secret_key))
    app.add_routes(routes)
    logger.info("Routes has benn added to app")
    return app

if __name__ == "__main__":
    web.run_app(make_app(), host=config["common"]["host"], port=config["common"]["port"])