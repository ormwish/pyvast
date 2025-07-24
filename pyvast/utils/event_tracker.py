
import asyncio, aiohttp, logging
from .macro import interpolate_macros
log = logging.getLogger('vast.tracker')

async def fire_pixels(urls, ctx):
    async with aiohttp.ClientSession() as s:
        await asyncio.gather(*(_hit(u, ctx, s) for u in urls))

async def _hit(url_raw, ctx, session):
    url = interpolate_macros(url_raw, ctx)
    try:
        async with session.get(url):
            log.debug('fired %s', url)
    except Exception as e:
        log.warning('pixel fail %s: %s', url, e)
