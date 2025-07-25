#!/usr/bin/env bash
# bootstrap_cli_docs_tests.sh
#  ▸ Создаёт pyvast/cli.py, docs/, tests/
#  ▸ Добавляет rich-click+typer+ruff в pyproject.toml
#  ▸ Прописывает entrypoint  pyvast = pyvast.cli:app
#  ▸ Делает один git-коммит  feat(cli+docs+tests)

set -euo pipefail
root=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
cd "$root"

echo "🐍  creating CLI…"
mkdir -p pyvast
cat > pyvast/cli.py <<'PY'
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
                 ctx_file: pathlib.Path = typer.Option(..., exists=True),
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
PY

echo "📚  creating docs…"
mkdir -p docs
cat > mkdocs.yml <<'YML'
site_name: PyVAST
theme: { name: material, features: [navigation.instant] }
plugins: [search, mkdocstrings]
YML
cat > docs/index.md <<'MD'
# PyVAST

Async VAST toolchain: DSL, adapters, OTEL, CLI.
MD
echo -e '```console\n$ pyvast --help\n```' > docs/cli.md
cat > docs/architecture.md <<'MD'
```mermaid
sequenceDiagram
  participant CLI
  participant Executor
  participant Adapter
  CLI->>Executor: run manifest
  Executor->>Adapter: fetch()
  Adapter-->>Executor: Inline VAST

MD

echo "🧪  creating tests…"
mkdir -p pyvast/tests
touch pyvast/tests/init.py
cat > pyvast/tests/test_loader.py <<'PY'
from pathlib import Path
from pyvast.manifest.loader import ManifestLoader
def test_manifest_load(tmp_path: Path):
p = tmp_path / "m.yml"
p.write_text("id: d\nadapters:{mock:{spec:{base_uri:'x'},config:{}}}\n"
"endpoints:[{id:e,adapter_id:mock}]\ngroups:[{id:g,endpoints:[e]}]")
assert ManifestLoader(p).model.id == "d"
PY
cat > pyvast/tests/test_macro.py <<'PY'
from pyvast.utils.macro import interpolate_macros
def test_cache_bust():
assert interpolate_macros("http://t?[CACHE_BUST]",{}) != interpolate_macros("http://t?[CACHE_BUST]",{})
PY

echo "🛠  patching pyproject.toml…"
pyproj=pyproject.toml

# add deps if absent

for dep in 'rich-click = "^1.7"' 'typer = "^0.12"'; do
grep -q "${dep%% *}" "$pyproj" || sed -i '' "/^python =/a\\
$dep" "$pyproj"
done

# add ruff in dev

grep -q "^ruff" "$pyproj" || sed -i '' "/\[tool.poetry.group.dev.dependencies]/a\\
ruff = \"*\"" "$pyproj"

# entrypoint

grep -q "\[tool.poetry.scripts]" "$pyproj" || echo -e "\n[tool.poetry.scripts]" >> "$pyproj"
grep -q "pyvast = " "$pyproj" || echo "pyvast = \"pyvast.cli:app\"" >> "$pyproj"

echo "🔧  git commit…"
git add pyvast/cli.py docs mkdocs.yml pyvast/tests "$pyproj"
git commit -m "feat(cli+docs+tests): bootstrap"

echo "✅  done.  Run:\n   poetry install --with dev\n   poetry run pyvast --help"

### как пользоваться

```bash
pbpaste > bootstrap_cli_docs_tests.sh   # или скопируйте файл вручную
chmod +x bootstrap_cli_docs_tests.sh
./bootstrap_cli_docs_tests.sh           # создаст файлы и commit
git push -u origin feat/bootstrap       # залить ветку

# CI соберётся, а локально:

poetry install --with dev
poetry run pyvast manifest inspect contrib/manifests/multi_ssp_demo.yml
poetry run pytest -q
mkdocs serve
```
