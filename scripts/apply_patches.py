#!/usr/bin/env python
"""
Применяет все *.diff в patches/, группируя по префиксу.
Для каждой группы:
  • создаёт ветку <prefix>-<epoch>
  • применяет патчи (git am для format-patch, light_apply для простых diff)
  • poetry install + pytest  (отключается флагами)
  • push в origin или другой remote (опция --remote)
"""
from __future__ import annotations
import asyncio, subprocess, time, tempfile, shutil
from pathlib import Path
import typer, rich_click as click

app = typer.Typer()
PATCH_DIR = Path("patches")

def sh(cmd: str):
    click.echo(f"[bold blue]$ {cmd}[/]")
    subprocess.check_call(cmd, shell=True)

def light_apply(diff_file: Path):
    """Apply simple diff format (with +++ file paths and + content lines)"""
    current_file = None
    
    for line in diff_file.read_text().splitlines():
        if line.startswith("+++"):
            # Extract file path from +++ line
            path_part = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
            # Remove a/ or b/ prefix if present
            if path_part.startswith(("a/", "b/")):
                path_part = path_part[2:]
            current_file = Path(path_part)
            
            # Create parent directories if needed
            if current_file:
                current_file.parent.mkdir(parents=True, exist_ok=True)
                # Initialize file if it doesn't exist
                if not current_file.exists():
                    current_file.write_text("")
                    
        elif line.startswith("+") and not line.startswith("+++") and current_file:
            # Add content line (remove the + prefix)
            content = line[1:] + "\n"
            if current_file.exists():
                current_file.write_text(current_file.read_text() + content)
            else:
                current_file.write_text(content)

def is_git_format_patch(diff_file: Path) -> bool:
    """Check if diff file is in git format-patch format (starts with 'From ')"""
    content = diff_file.read_text().lstrip()
    return content.startswith("From ")

def apply_patch(diff_file: Path):
    """Apply a patch file using appropriate method based on format"""
    if is_git_format_patch(diff_file):
        # Use git am for format-patch files
        sh(f"git am {diff_file}")
    else:
        # Use light_apply for simple diff format
        light_apply(diff_file)
        # Stage all changes and commit
        sh("git add -A")
        sh(f"git commit -m '{diff_file.stem}'")

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
        
        # Apply each patch file using appropriate method
        for diff_file in files:
            apply_patch(diff_file)
            
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
