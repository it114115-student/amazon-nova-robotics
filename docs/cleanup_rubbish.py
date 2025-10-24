#!/usr/bin/env python3
"""
Spot and optionally remove or archive likely "rubbish" Markdown files.

Rubbish is heuristically defined by filename patterns (e.g., performance summaries,
refactoring notes, temporary readmes) while keeping core docs (READMEs, API, deployment,
and any docs/ subtrees).

Usage:
  Dry run (default):
    python3 docs/cleanup_rubbish.py --dry-run

  Archive candidates instead of deleting:
    python3 docs/cleanup_rubbish.py --archive

  Delete candidates (dangerous):
    python3 docs/cleanup_rubbish.py --delete --yes

You can tune behavior via docs/cleanup_config.json.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set, Tuple

CONFIG_PATH = Path(__file__).parent / "cleanup_config.json"
DEFAULT_ARCHIVE = Path(__file__).parent / "archive"


@dataclass
class Rules:
    keep_globs: List[str]
    rubbish_name_contains: List[str]
    exclude_dirs: Set[str]
    archive_dir: Path


def load_rules() -> Rules:
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
    else:
        data = {}
    keep_globs = data.get("keep_globs", ["README.md", "**/README.md", "**/docs/**"])  # type: ignore
    rubbish_name_contains = data.get(
        "rubbish_name_contains",
        [
            "PERFORMANCE",
            "REFACTOR",
            "FINAL_SOLUTION",
            "SIGNATURE_ANALYSIS",
            "TEST_README",
            "QUICK_REFERENCE",
            "AUTH_README",
            "ARCHITECTURE_COMPARISON",
            "MCP_PERFORMANCE",
            "MCP_TOOLS_FIX_SUMMARY",
            "SECURE_MCP_README",
            "STRANDS_README",
        ],
    )
    exclude_dirs = set(
        data.get("exclude_dirs", [".git", "node_modules", "__pycache__", "docs"])
    )
    archive_dir = Path(data.get("archive_dir", str(DEFAULT_ARCHIVE)))
    return Rules(keep_globs, rubbish_name_contains, exclude_dirs, archive_dir)


def iter_md_files(root: Path, exclude_dirs: Set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        cur = Path(dirpath)
        # never walk into top-level docs folder
        top_docs = (root / "docs").resolve()
        dirnames[:] = [
            d
            for d in dirnames
            if (cur / d).resolve() != top_docs and d not in exclude_dirs
        ]
        for name in filenames:
            p = cur / name
            if p.suffix.lower() in {".md", ".markdown"}:
                yield p


def is_kept(p: Path, root: Path, globs: List[str]) -> bool:
    rel = str(p.relative_to(root).as_posix())
    for pattern in globs:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(p.name, pattern):
            return True
    return False


def is_rubbish(p: Path, contains_any: List[str]) -> bool:
    upper = p.name.upper()
    return any(token in upper for token in contains_any)


def partition_candidates(root: Path, rules: Rules) -> Tuple[List[Path], List[Path]]:
    keep: List[Path] = []
    candidates: List[Path] = []
    for p in iter_md_files(root, rules.exclude_dirs):
        if is_kept(p, root, rules.keep_globs):
            keep.append(p)
            continue
        if is_rubbish(p, rules.rubbish_name_contains):
            candidates.append(p)
    return keep, candidates


def archive_files(files: List[Path], root: Path, archive_dir: Path) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        rel = f.relative_to(root)
        dest = archive_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(dest))


def delete_files(files: List[Path]) -> None:
    for f in files:
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Identify and clean likely rubbish Markdown files"
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(Path(__file__).resolve().parents[1]),
        help="Repo root",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only list candidates")
    parser.add_argument(
        "--archive", action="store_true", help="Move candidates into docs/archive/"
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete candidates (irreversible)"
    )
    parser.add_argument(
        "--yes", action="store_true", help="Do not prompt for confirmation"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rules = load_rules()
    keep, candidates = partition_candidates(root, rules)

    print(f"Scanned repo: {root}")
    print(f"Kept (patterns): {len(keep)}")
    print(f"Candidates (rubbish): {len(candidates)}\n")

    def show_sample(paths: List[Path], title: str, limit: int = 20) -> None:
        print(title)
        for p in paths[:limit]:
            print(f" - {p.relative_to(root)}")
        if len(paths) > limit:
            print(f" ... and {len(paths) - limit} more")
        print()

    show_sample(candidates, "Sample candidates:")

    if args.dry_run or (not args.archive and not args.delete):
        print("Dry run only. No changes made.")
        return 0

    if not args.yes:
        print("--yes not provided; refusing to modify files.")
        return 2

    if args.archive:
        archive_files(candidates, root, rules.archive_dir.resolve())
        print(f"Archived {len(candidates)} files to {rules.archive_dir}")
        return 0

    if args.delete:
        delete_files(candidates)
        print(f"Deleted {len(candidates)} files.")
        return 0

    print("No action performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
