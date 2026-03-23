#!/usr/bin/env python3
"""Generate backend/LINE_NAVIGATION.md: one jump command per source line for app code."""

from __future__ import annotations

import argparse
from pathlib import Path


def iter_py_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.py")):
            parts = set(p.parts)
            if "__pycache__" in parts or ".venv" in parts:
                continue
            out.append(p)
    return out


def rel_from_repo_root(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def escape_md_cell(s: str) -> str:
    s = s.replace("\r", "").replace("\n", " ")
    s = s.replace("|", "\\|")
    if len(s) > 100:
        s = s[:97] + "..."
    return s


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to backend/ (default: parent of scripts/)",
    )
    args = parser.parse_args()
    backend_dir = args.backend_dir.resolve()
    repo_root = backend_dir.parent

    roots = [
        backend_dir / "app",
        backend_dir / "tests",
        backend_dir / "alembic",
        backend_dir / "scripts",
    ]
    files = iter_py_files(roots)

    lines_out: list[str] = [
        "# Backend line navigation",
        "",
        "Auto-generated: jump to any line in Cursor or VS Code.",
        "",
        f"Regenerate from repo root: `python backend/scripts/generate_line_navigation.py`",
        f"Or from `backend/`: `python scripts/generate_line_navigation.py`",
        "",
        "## Legend",
        "",
        "- **Cursor / VS Code:** paste the backtick command in a terminal, or use **Go to File** (`Cmd+P` / `Ctrl+P`) and type `path:line`.",
        "- **sed (terminal):** `sed -n 'LINEp' path` prints one line.",
        "- **nl:** `nl -ba path` prints the file with line numbers.",
        "",
    ]

    total_files = 0
    total_lines = 0

    for path in files:
        total_files += 1
        rel = rel_from_repo_root(repo_root, path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        file_lines = text.splitlines()
        n = len(file_lines)
        total_lines += n

        lines_out.append(f"## `{rel}` ({n} lines)")
        lines_out.append("")
        lines_out.append("| Line | Cursor / VS Code | `sed` | Preview |")
        lines_out.append("| ---: | --- | --- | --- |")

        for i, line in enumerate(file_lines, start=1):
            cursor_cmd = f"`cursor {rel}:{i}`"
            code_cmd = f"`code {rel}:{i}`"
            jump = f"{cursor_cmd} or {code_cmd}"
            sed_cmd = f"`sed -n '{i}p' {rel}`"
            preview = escape_md_cell(line)
            lines_out.append(f"| {i} | {jump} | {sed_cmd} | {preview} |")

        lines_out.append("")

    lines_out.insert(
        8,
        f"**Index:** {total_files} files, {total_lines} lines (first-party Python under `app/`, `tests/`, `alembic/`, `scripts/`).",
    )
    lines_out.insert(9, "")

    out_path = backend_dir / "LINE_NAVIGATION.md"
    out_path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({total_files} files, {total_lines} lines)")


if __name__ == "__main__":
    main()
