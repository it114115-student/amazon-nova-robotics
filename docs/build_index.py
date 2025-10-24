#!/usr/bin/env python3
"""
Generate a consolidated documentation index at docs/README.md by scanning the
repository for Markdown files and grouping them by top-level folder.

Usage:
  python3 docs/build_index.py   # from repo root
  python3 build_index.py        # from docs/ folder
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "cdk.out",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
}

EXCLUDE_FILES = {
    # Add any specific files to exclude if needed
}

MD_EXTENSIONS = {".md", ".markdown"}


def resolve_repo_root() -> Path:
    this_file = Path(__file__).resolve()
    # docs/build_index.py -> repo root is parent of docs
    if this_file.parent.name == "docs":
        return this_file.parent.parent
    # Fallback to current working directory
    return Path.cwd()


def should_exclude_dir(path: Path) -> bool:
    # Exclude directories listed above at any nesting level
    return any(part in EXCLUDE_DIRS for part in path.parts)


def find_markdown_files(root: Path) -> List[Path]:
    results: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        # Skip excluded directories by mutating dirnames in-place
        docs_dir = (root / "docs").resolve()
        dirnames[:] = [
            d
            for d in dirnames
            if not should_exclude_dir(current_dir / d)
            and (current_dir / d).resolve() != docs_dir
        ]

        for name in filenames:
            if name in EXCLUDE_FILES:
                continue
            p = current_dir / name
            if p.suffix.lower() in MD_EXTENSIONS:
                results.append(p)
    return sorted(results)


def title_from_filename(p: Path) -> str:
    title = p.stem.replace("_", " ")
    # Preserve acronyms by uppercasing words > 2 chars that are already uppercase in filename
    return title.title()


def group_by_top_level(root: Path, files: List[Path]) -> Dict[str, List[Path]]:
    grouped: Dict[str, List[Path]] = {}
    for f in files:
        rel = f.relative_to(root)
        parts = rel.parts
        if len(parts) == 1:
            key = "(root)"
        else:
            key = parts[0]
        grouped.setdefault(key, []).append(f)
    # Sort each group's files alphabetically by relative path
    for k in grouped:
        grouped[k] = sorted(grouped[k], key=lambda p: str(p.relative_to(root)))
    return dict(
        sorted(grouped.items(), key=lambda kv: (kv[0] != "(root)", kv[0].lower()))
    )


def make_rel_link(from_dir: Path, to_file: Path) -> str:
    rel = os.path.relpath(to_file, start=from_dir)
    # Normalize to POSIX for Markdown links
    return rel.replace(os.sep, "/")


def generate_index(root: Path, out_readme: Path) -> None:
    files = find_markdown_files(root)
    if not files:
        out_readme.write_text("# Project Documentation\n\nNo Markdown files found.\n")
        return

    # Group and prepare content
    grouped = group_by_top_level(root, files)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = []
    lines.append("# Project Documentation Index\n")
    lines.append(f"Generated: {now}\n")
    lines.append(
        "> This index links to original files across the repo. Source docs remain in their project folders.\n\n"
    )

    # Quick links for common entry points if present
    quick_links = [
        ("Repository README", root / "README.md"),
        ("Text Control: README", root / "text_control" / "README.md"),
        ("Speech Control: README", root / "speech_control" / "README.md"),
        (
            "Humanoid Robot Simulator: README",
            root / "humanoid-robot-simulator" / "README.md",
        ),
        ("CDK Infrastructure: README", root / "cdk" / "README.md"),
    ]
    present = [(label, p) for (label, p) in quick_links if p.exists()]
    if present:
        lines.append("## Quick links\n")
        for label, p in present:
            href = make_rel_link(out_readme.parent, p)
            lines.append(f"- [{label}]({href})")
        lines.append("")

    # Table of contents by top-level folder
    lines.append("## All documents by area\n")
    for group, paths in grouped.items():
        count = len(paths)
        lines.append(f"### {group} ({count})\n")
        for p in paths:
            # Skip the generated README itself if present
            if p == out_readme:
                continue
            href = make_rel_link(out_readme.parent, p)
            title = title_from_filename(p)
            lines.append(f"- [{title}]({href})")
        lines.append("")

    out_readme.write_text("\n".join(lines) + "\n")


def main() -> int:
    # Determine repo root and output path
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "docs":
        repo_root = script_path.parent.parent
        out_readme = script_path.parent / "README.md"
    else:
        # Running from repo root or elsewhere; assume standard layout
        repo_root = resolve_repo_root()
        out_readme = repo_root / "docs" / "README.md"

    out_readme.parent.mkdir(parents=True, exist_ok=True)
    generate_index(repo_root, out_readme)
    print(f"Wrote consolidated index: {out_readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
