from aiohttp import web
from settings import logger


@web.middleware
@logger.catch()
async def middleware_logger(request, handler):
    logger.debug(f'{request.method} {request.url} from IP: {request.remote}')
    response = await handler(request)
    return response
