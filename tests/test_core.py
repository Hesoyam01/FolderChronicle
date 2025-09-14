from __future__ import annotations

import os
import time
from pathlib import Path

from folderchronicle.core import SortOptions, gather_files, sort_files, unique_destination_path


def test_unique_destination_path(tmp_path: Path) -> None:
    d = tmp_path / "sub"
    d.mkdir()
    f = d / "a.txt"
    f.write_text("x")
    u1 = unique_destination_path(f)
    assert u1.name == "a (1).txt"
    (d / "a (1).txt").write_text("x")
    u2 = unique_destination_path(f)
    assert u2.name == "a (2).txt"


def test_gather_files_skips_existing_structure(tmp_path: Path) -> None:
    # Create files under normal and already-sorted structure
    (tmp_path / "file1.txt").write_text("1")
    y = tmp_path / "2020" / "01"
    y.mkdir(parents=True)
    (y / "already.txt").write_text("a")
    files = gather_files(tmp_path, include_subdirs=True)
    names = {p.name for p in files}
    assert "file1.txt" in names
    assert "already.txt" not in names


def test_sort_files_copy_mode(tmp_path: Path) -> None:
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    f2.write_text("b")
    # Set mod times to deterministic month
    jan_2023 = int(time.mktime((2023, 1, 15, 12, 0, 0, 0, 0, -1)))
    os.utime(f1, (jan_2023, jan_2023))
    os.utime(f2, (jan_2023, jan_2023))

    moved, errors, logs = sort_files(
        SortOptions(base_dir=tmp_path, include_subdirs=False, use_ctime=False, copy_no_backup=True)
    )
    assert moved == 2  # noqa: PLR2004 - verifying two files processed
    assert errors == 0
    assert (tmp_path / "2023" / "01" / "a.txt").exists()
    assert (tmp_path / "2023" / "01" / "b.txt").exists()
    # Original files still exist due to copy mode
    assert f1.exists() and f2.exists()
