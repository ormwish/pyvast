from __future__ import annotations
import asyncio, pathlib, yaml, typer, rich_click as click
from rich.table import Table
from rich import print as rprint
from pyvast.manifest.loader import ManifestLoader
from pyvast.adapters.base_http import BaseHTTPAdapter
app = typer.Typer(help="PyVAST CLI", rich_help_panel="root")
# manifest ----------------------------------------------------
man = typer.Typer(help="Validate & inspect manifests"); app.add_typer(man, name="manifest")
@man.command("inspect")
def inspect(path: pathlib.Path):
    m = ManifestLoader(path).model
    tbl = Table(title=f"[bold magenta]{m.id}", box=None)
    tbl.add_column("Group / Endpoint", style="bold green"); tbl.add_column("Adapter")
    for g in sorted(m.groups, key=lambda g: g.priority):
        tbl.add_row(f"🞇 {g.id}", f"mode={g.mode}")
        for eid in g.endpoints:
            ep = next(e for e in m.endpoints if e.id == eid)
            tbl.add_row(f" └─ {ep.id}", ep.adapter_id)
    rprint(tbl)
# adapter -----------------------------------------------------
ad = typer.Typer(help="Adapter playground"); app.add_typer(ad, name="adapter")
@ad.command("test")
def adapter_test(adapter_id: str,
                 manifest: pathlib.Path = typer.Option(..., exists=True),
                 ctx_file: pathlib.Path = typer.Option(..., "--ctx-file", "--ctx", exists=True),
                 url_only: bool = typer.Option(False, "--url-only", "-u")):
    import aiohttp
    ctx = yaml.safe_load(ctx_file.read_text())
    mdl = ManifestLoader(manifest).model
    ep  = next(e for e in mdl.endpoints if e.adapter_id == adapter_id)
    spec, cfg = mdl.adapters[adapter_id].spec, mdl.adapters[adapter_id].config
    a = BaseHTTPAdapter(spec, cfg, ep.set_params)
    ctx.setdefault("url", spec.base_uri)
    url, hdrs, _ = a._build_request(ctx)
    rprint({"url": url, "headers": hdrs})
    if url_only: raise typer.Exit()
    async def _go():
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=hdrs, timeout=cfg.timeout) as r:
                rprint({"status": r.status, "body": (await r.text())[:512]})
    asyncio.run(_go())
if __name__ == "__main__": app()
