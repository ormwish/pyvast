#!/usr/bin/env python
"""
Применяет все *.diff в patches/, группируя по префиксу.
Для каждой группы:
  • создаёт ветку <prefix>-<epoch>
  • git am *.diff
  • poetry install + pytest  (отключается флагами)
  • push в origin или другой remote (опция --remote)
"""
from __future__ import annotations
import asyncio, subprocess, time
from pathlib import Path
import typer, rich_click as click

app = typer.Typer()
PATCH_DIR = Path("patches")

def sh(cmd: str):
    click.echo(f"[bold blue]$ {cmd}[/]")
    subprocess.check_call(cmd, shell=True)

def group_diffs() -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for p in sorted(PATCH_DIR.glob("*.diff")):
        prefix, _, _ = p.name.partition("__")
        groups.setdefault(prefix, []).append(p)
    return groups

@app.command()
def run(
    remote: str = typer.Option("origin", help="git remote to push"),
    poetry_dev: bool = typer.Option(True, help="poetry install --with dev"),
    run_tests: bool = typer.Option(True, help="poetry run pytest -q"),
):
    sh("git switch main")
    sh("git pull --ff-only")

    for prefix, files in group_diffs().items():
        branch = f"{prefix}-{int(time.time())}"
        sh(f"git switch -c {branch}")
        sh(f"git am {' '.join(str(f) for f in files)}")
        if poetry_dev:
            sh("poetry install --with dev")
        if run_tests:
            sh("poetry run pytest -q")
        sh(f"git push -u {remote} {branch}")

        repo = subprocess.check_output(
            "git config --get remote.origin.url", shell=True, text=True
        ).strip().split("/")[-1].removesuffix(".git")
        pr = f"https://github.com/{repo}/compare/{branch}?expand=1"
        click.secho(f"\n✅  PR ready → {pr}\n", fg="green")

if __name__ == "__main__":
    app()
