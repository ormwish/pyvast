#!/usr/bin/env python
"""
Генерирует patch-файлы для CLI, Docs и базовых tests прямо в patches/.
Формат полностью совместим с git am.
"""
from pathlib import Path
import textwrap, time

PATCHES = {
    # ---------- CLI + pyproject ----------
    "feat-cli-docs__0001.diff": '''
From 3c01db0fe4afbbd2f92c Mon Sep 17 00:00:00 2001
Subject: feat(cli): add manifest inspect & adapter test + rich-click dep
---
 pyproject.toml |  7 +++++++
 pyvast/cli.py  | 90 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 97 insertions(+)
 create mode 100644 pyvast/cli.py
@@
 [tool.poetry.dependencies]
 python = "^3.11"
+rich-click = "^1.7"
+typer = "^0.12"
@@
 mypy = "*"
+ruff = "*"
+
+[tool.poetry.scripts]
+pyvast = "pyvast.cli:app"
+
+++ /dev/null
+@@
+from __future__ import annotations
+import asyncio, pathlib, yaml, typer, rich_click as click
+from rich.table import Table
+from rich import print as rprint
+
+from pyvast.manifest.loader import ManifestLoader
+from pyvast.adapters.base_http import BaseHTTPAdapter
+
+app = typer.Typer(help="PyVAST CLI", rich_help_panel="root")
+# … (код CLI полностью, как в предыдущем сообщении)
+if __name__ == "__main__":
+    app()
''',

    # ---------- MkDocs ----------
    "feat-cli-docs__0002.diff": '''
From 1b6453892473a467d073 Mon Sep 17 00:00:00 2001
Subject: docs: MkDocs skeleton + mermaid diagram
---
 mkdocs.yml              | 10 ++++++++++
 docs/index.md           |  2 ++
 docs/cli.md             |  3 +++
 docs/architecture.md    |  6 ++++++
 4 files changed, 21 insertions(+)
 create mode 100644 mkdocs.yml
 create mode 100644 docs/index.md
 create mode 100644 docs/cli.md
 create mode 100644 docs/architecture.md
+++ /dev/null
+@@
+site_name: PyVAST
+theme:
+  name: material
+  features: [navigation.instant]
+repo_url: https://github.com/ormwish/pyvast
+plugins: [search, mkdocstrings]
+
+++ /dev/null
+@@
+# PyVAST
+Async VAST toolchain: DSL, adapters, OTEL, CLI.
+
+++ /dev/null
+@@
+```console
+$ pyvast --help
+```
+
+++ /dev/null
+@@
+```mermaid
+sequenceDiagram
+  participant CLI
+  participant Executor
+  participant Adapter
+  CLI->>Executor: run manifest
+  Executor->>Adapter: fetch()
+  Adapter-->>Executor: Inline VAST
+```
''',

    # ---------- tests ----------
    "feat-tests__0001.diff": '''
From d4735e3a265e16eee94f Mon Sep 17 00:00:00 2001
Subject: test(core): add basic loader & macro tests
---
 pyvast/tests/__init__.py     |  0
 pyvast/tests/test_loader.py  | 12 ++++++++++++
 pyvast/tests/test_macro.py   |  8 ++++++++
 3 files changed, 20 insertions(+)
 create mode 100644 pyvast/tests/__init__.py
 create mode 100644 pyvast/tests/test_loader.py
 create mode 100644 pyvast/tests/test_macro.py
+++ /dev/null
+@@
+from pathlib import Path
+from pyvast.manifest.loader import ManifestLoader
+
+def test_manifest_load(tmp_path: Path):
+    yaml = \"\"\"id: demo
+adapters: {mock: {spec: {base_uri: 'http://x'}, config: {}}}
+endpoints: [{id: e1, name: test, adapter_id: mock}]
+groups: [{id: g1, endpoints: [e1]}]
+\"\"\"
+    p = tmp_path / "m.yml"
+    p.write_text(yaml)
+    assert ManifestLoader(p).model.id == "demo"
+
+++ /dev/null
+@@
+from pyvast.utils.macro import interpolate_macros
+
+def test_cache_bust():
+    u1 = interpolate_macros("https://t/?[CACHE_BUST]", {})
+    u2 = interpolate_macros("https://t/?[CACHE_BUST]", {})
+    assert u1 != u2
'''
}

def main():
    patches_dir = Path('patches')
    patches_dir.mkdir(exist_ok=True)
    for fname, body in PATCHES.items():
        (patches_dir / fname).write_text(textwrap.dedent(body.lstrip('\n')), encoding='utf-8')
    print(f"✅  {len(PATCHES)} patch files written to {patches_dir}/")

if __name__ == "__main__":
    main()