
import asyncio, aiohttp
from typing import Dict, Any
from .types import ManifestModel
from ..adapters.registry import get_adapter
from .utils_param import apply_param_setters
from ..adapters.base_http import BaseHTTPAdapter
from ..utils.macro import interpolate_macros

class ManifestExecutor:
    def __init__(self, model: ManifestModel):
        self.model = model
        self.endpoints = {e.id: e for e in model.endpoints}

    async def execute(self, ctx: Dict[str,Any], *, session=None):
        if session is None:
            session = aiohttp.ClientSession()
        for group in sorted(self.model.groups, key=lambda g: g.priority):
            for eid in group.endpoints:
                ep = self.endpoints[eid]
                spec = self.model.adapters[ep.adapter_id].spec
                cfg  = self.model.adapters[ep.adapter_id].config
                adapter = BaseHTTPAdapter(spec=spec, config=cfg, setters=ep.set_params)
                local_ctx = dict(ctx); local_ctx['url']=spec.base_uri
                await apply_param_setters(local_ctx, ep.set_params)
                try:
                    xml = await adapter.fetch(local_ctx, session=session)
                    await session.close()
                    return xml
                except Exception:
                    continue
        await session.close()
        raise RuntimeError('NoFill')
