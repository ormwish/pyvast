from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pytest

from pyvast.manifest.loader import ManifestLoader
from pyvast.adapters.base_http import BaseHTTPAdapter


DEMO_MANIFEST = Path("contrib/manifests/multi_ssp_demo.yml")
CTX_PATH = Path("contrib/ctx/demo.json")


@pytest.fixture()
def ctx():
    import json

    return json.loads(CTX_PATH.read_text())


@pytest.fixture()
def adfox_adapter():
    model = ManifestLoader(DEMO_MANIFEST).model
    endpoint = next(e for e in model.endpoints if e.id == "adfox_ssp")
    spec = model.adapters["adfox"].spec
    cfg = model.adapters["adfox"].config
    return BaseHTTPAdapter(spec, cfg, endpoint.set_params)


def test_dotted_macro_resolution(adfox_adapter, ctx):
    """
    _build_request должен подставить dotted-путь макросы
    (${self.owner_id}, ${device.ip} …) внутрь URL и заголовков.
    """
    url, headers, _ = adfox_adapter._build_request(ctx)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    assert "yandex.ru/ads/adfox/721500/" in url          # ${self.owner_id}
    assert qs["p1"] == ["dfiza"]                         # ${self.site_id}
    assert qs["p2"] == ["hyxp"]                          # ${self.placement_id}
    assert "ext_duid" in qs                              # [CACHE_BUST] -> любое число

    assert headers["X-Adfox-S2S-Key"] == "532..."
    assert headers["X-Real-IP"] == "91.240.123.86"


def test_cache_bust_unique(adfox_adapter, ctx):
    url1, *_ = adfox_adapter._build_request(ctx)
    url2, *_ = adfox_adapter._build_request(ctx)
    assert url1 != url2, "CACHE_BUST macro should differ on subsequent calls"