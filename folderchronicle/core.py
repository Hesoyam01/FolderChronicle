from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

__all__ = [
    "SortOptions",
    "format_exception",
    "unique_destination_path",
    "gather_files",
    "sort_files",
]


def format_exception(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"


def unique_destination_path(dest: Path) -> Path:
    """Return a unique destination path by appending (1), (2), ... if needed."""
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


@dataclass(frozen=True)
class SortOptions:
    base_dir: Path
    include_subdirs: bool = False
    use_ctime: bool = False
    copy_no_backup: bool = False


def gather_files(base_dir: Path, include_subdirs: bool) -> list[Path]:
    """Collect file paths under base_dir, optionally recursively.

    When recursive, prune directories that start with "FolderChronicle Backup" and
    skip files already under a YYYY/MM structure relative to base_dir to avoid
    reprocessing.
    """
    if include_subdirs:
        gathered: list[Path] = []
        for root, dirs, files_ in os.walk(base_dir):
            dirs[:] = [d for d in dirs if not d.startswith("FolderChronicle Backup")]
            r = Path(root)
            for name in files_:
                p = r / name
                # skip if already under YYYY/MM
                try:
                    rel = p.relative_to(base_dir)
                except ValueError:
                    gathered.append(p)
                    continue
                parts = rel.parts
                if (
                    len(parts) >= 3  # noqa: PLR2004 - conventional YYYY/MM depth
                    and len(parts[0]) == 4  # noqa: PLR2004 - year length
                    and parts[0].isdigit()
                    and len(parts[1]) == 2  # noqa: PLR2004 - month length
                    and parts[1].isdigit()
                ):
                    continue
                gathered.append(p)
        return [p for p in gathered if p.is_file()]
    else:
        return [p for p in base_dir.iterdir() if p.is_file()]


def _backup_files(files: Iterable[Path], base_dir: Path) -> tuple[int, list[str]]:
    """Copy files to a timestamped backup folder under base_dir.

    Returns (error_count, log_messages).
    """
    errors = 0
    logs: list[str] = []
    backup_root = base_dir / (
        f"FolderChronicle Backup {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"
    )
    for src in files:
        try:
            try:
                rel = src.relative_to(base_dir)
            except ValueError:
                rel = Path(src.name)
            dest_backup = backup_root / rel
            dest_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_backup)
        except Exception as e:  # pragma: no cover - file errors are environment dependent
            errors += 1
            logs.append(f"Backup error {src}: {format_exception(e)}")
    return errors, logs


def sort_files(options: SortOptions) -> tuple[int, int, list[str]]:
    """Sort files into YYYY/MM under base_dir.

    Returns (moved_or_copied_count, error_count, log_messages).
    """
    base_dir = options.base_dir
    files = gather_files(base_dir, options.include_subdirs)
    moved = 0
    errors = 0
    logs: list[str] = []

    if not files:
        return 0, 0, ["No files found."]

    # Backup phase when moving
    if not options.copy_no_backup:
        b_errors, b_logs = _backup_files(files, base_dir)
        errors += b_errors
        logs.extend(b_logs)

    for src in files:
        try:
            stat = src.stat()
            ts = stat.st_ctime if options.use_ctime else stat.st_mtime
            dt = datetime.fromtimestamp(ts)
            year = f"{dt.year:04d}"
            month = f"{dt.month:02d}"

            dest_dir = base_dir / year / month
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = unique_destination_path(dest_dir / src.name)

            if options.copy_no_backup:
                shutil.copy2(src, dest)
                logs.append(f"Copied: {src.name} -> {year}/{month}/")
            else:
                shutil.move(str(src), str(dest))
                logs.append(f"Moved: {src.name} -> {year}/{month}/")
            moved += 1
        except Exception as e:  # pragma: no cover - filesystem errors vary
            errors += 1
            logs.append(f"Error moving {src.name}: {format_exception(e)}")

    return moved, errors, logs
