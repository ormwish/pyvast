
from urllib.parse import urlparse, parse_qsl, urlencode
import importlib, asyncio
from .types import ParamSetter
from ..utils.macro import interpolate_macros

async def apply_param_setters(ctx, setters:list[ParamSetter]):
    for s in setters:
        mod, _, attr = s.factory.fn.replace(':','.').rpartition('.')
        fn = getattr(importlib.import_module(mod), attr)
        value_raw = fn(*s.factory.args, **s.factory.kwargs, ctx=ctx)
        if asyncio.iscoroutine(value_raw):
            value_raw = await value_raw
        value = interpolate_macros(str(value_raw), ctx)
        bag, _, key = s.target.partition('.')
        if bag=='query':
            parsed=urlparse(ctx['url'])
            q=dict(parse_qsl(parsed.query))
            q[key]=value
            ctx['url']=parsed._replace(query=urlencode(q)).geturl()
        elif bag=='header':
            ctx.setdefault('headers',{})[key]=value
