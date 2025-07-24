
import lxml.etree as ET, asyncio, aiohttp, logging
log = logging.getLogger('vast.wrapper')

async def resolve_wrappers(xml: str, fetch, wrapper_limit:int=5):
    doc = ET.fromstring(xml.encode())
    depth = 0
    while doc.find('.//Wrapper') is not None and depth < wrapper_limit:
        uri = doc.findtext('.//VASTAdTagURI')
        xml = await fetch(uri.strip())
        doc = ET.fromstring(xml.encode())
        depth += 1
    return ET.tostring(doc, encoding='unicode')
