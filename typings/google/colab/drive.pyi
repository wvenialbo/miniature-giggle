# Copyright 2018 Google Inc.
"""Colab-specific Google Drive integration."""

__all__ = ["flush_and_unmount", "mount"]

def flush_and_unmount(timeout_ms: int = 86400000) -> None:
    """
    Unmount Google Drive and flush any outstanding writes to it.

    Args:
        timeout_ms: Inferred as int from default value (24 * 60 * 60 * 1000).
    """
    ...

def mount(
    mountpoint: str,
    force_remount: bool = False,
    timeout_ms: int = 120000,
    readonly: bool = False,
) -> None:
    """
    Mount your Google Drive at the specified mountpoint path.

    Args:
        mountpoint: Inferred as str from path usage and docstring.
        force_remount: Inferred as bool from default value.
        timeout_ms: Inferred as int from default value.
        readonly: Inferred as bool from default value.
    """
    ...
