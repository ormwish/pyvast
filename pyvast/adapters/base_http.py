from __future__ import annotations

"""Universal HTTP adapter for PyVAST.

Responsibilities
----------------
* Render `AdapterSpec` (base_uri, query, headers, body) using macro engine.
* Apply ParamSetter cascade (client → group → endpoint → mixins).
* Re‑use an existing aiohttp.ClientSession passed from ManifestExecutor.
* Respect timeout from `AdapterConfig`.
* Optionally resolve `<VASTAdTagURI>` wrapper chains.

This is a *thin* but fully‑featured adapter — concrete DSP integrations can be
described declaratively in YAML and re‑use this class without writing code.
"""

import asyncio
import logging
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import aiohttp
from aiohttp.client_exceptions import ClientError

from pyvast.manifest.types import AdapterConfig, AdapterSpec, ParamSetter
from pyvast.manifest.utils_param import apply_param_setters
from pyvast.utils.macro import interpolate_macros
from pyvast.utils.wrapper_resolver import resolve_wrappers
from pyvast.utils.instrumentation import traced

log = logging.getLogger("pyvast.adapter.http")

__all__ = ["BaseHTTPAdapter"]


class BaseHTTPAdapter:
    """Generic HTTP adapter driven purely by :class:`pyvast.manifest.types.AdapterSpec`."""

    def __init__(
        self,
        spec: AdapterSpec,
        config: AdapterConfig,
        setters: Optional[List[ParamSetter]] = None,
    ):  # noqa: D401 – short docstring OK
        self.spec = spec
        self.config = config
        self.setters = setters or []

    # ---------------------------------------------------------------------
    async def fetch(
        self,
        ctx: Dict[str, Any],
        *,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> str:
        """Main entry from ManifestExecutor.

        Parameters
        ----------
        ctx
            Mutable context dict propagated by executor (adrequest, device, etc.).
        session
            Shared :class:`aiohttp.ClientSession`; executor is responsible for closing it.
        """

        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout or 3.0)
            )

        # 1. copy ctx → apply ParamSetter cascade
        work_ctx: Dict[str, Any] = {**ctx}  # shallow copy is fine
        await apply_param_setters(work_ctx, self.setters)

        # 2. Build request (URL, headers, body)
        url, headers, data = self._build_request(work_ctx)

        # 3. Perform request with OTEL span
        try:
            async with traced("vast.http", url=url, method=self.spec.method):
                async with session.request(
                    self.spec.method, url, headers=headers, data=data
                ) as resp:
                    resp.raise_for_status()
                    raw_xml = await resp.text()
        except ClientError as e:
            log.warning("HTTP error %s → %s", url, e)
            raise
        finally:
            if owns_session:
                await session.close()

        # 4. Wrapper resolution (optional)
        if work_ctx.get("resolve_all"):
            raw_xml = await resolve_wrappers(
                raw_xml,
                fetch=lambda u: self._fetch_wrapper(u, session),
                wrapper_limit=work_ctx.get("wrapper_limit", 5),
            )
        return raw_xml

    # ------------------------------------------------------------------
    def _build_request(self, ctx: Dict[str, Any]) -> Tuple[str, Dict[str, str], Any]:
        """Render base_uri + query + headers using macro engine."""
        # -- URL --------------------------------------------------------
        base_uri = interpolate_macros(self.spec.base_uri, ctx)
        parsed = urlparse(base_uri)
        query: Dict[str, str] = dict(parse_qsl(parsed.query, keep_blank_values=True))

        for key, val in self.spec.query.items():
            query[key] = interpolate_macros(str(val), ctx)

        url = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

        # -- headers ----------------------------------------------------
        hdrs: Dict[str, str] = {
            k: interpolate_macros(str(v), ctx) for k, v in self.spec.headers.items()
        }

        # -- body for POST (simple x‑www‑form)
        data = None
        if self.spec.method == "POST":
            data = urlencode(query)
            url = urlunparse(parsed._replace(query=""))  # move query into body

        log.debug("HTTP %s %s", self.spec.method, url)
        return url, hdrs, data

    # ------------------------------------------------------------------
    async def _fetch_wrapper(
        self, url: str, session: aiohttp.ClientSession
    ) -> str:  # helper for resolve_wrappers
        async with session.get(url) as r:
            r.raise_for_status()
            return await r.text()
