"""Thin wrapper to preserve `python folderchronicle.py` behavior.

The actual app now lives in the package `folderchronicle.app`.
"""

from folderchronicle.app import main  # noqa: F401

if __name__ == "__main__":
    main()
