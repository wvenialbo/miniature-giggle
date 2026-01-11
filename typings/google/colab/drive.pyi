# Copyright 2018 Google Inc.
"""Colab-specific Google Drive integration."""

from typing import NamedTuple

__all__ = ["flush_and_unmount", "mount"]

# Inferencia: NamedTuple mantiene su estructura de tipos interna
class _Environment(NamedTuple):
    home: str
    root_dir: str
    dev: str
    path: str
    config_dir: str

def _env() -> _Environment:
    """Create and return an _Environment to use."""
    ...

def _logs_dir() -> str:
    """Inferred from os.path.join usage."""
    ...

def _timeouts_path() -> str:
    """Inferred from os.path.join usage."""
    ...

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

def _mount(
    mountpoint: str,
    force_remount: bool = False,
    timeout_ms: int = 120000,
    ephemeral: bool = False,
    readonly: bool = False,
) -> None:
    """
    Internal helper to mount Google Drive.

    Args:
        mountpoint: Inferred as str from logic.
        force_remount: Inferred as bool from default.
        timeout_ms: Inferred as int from default.
        ephemeral: Inferred as bool from default.
        readonly: Inferred as bool from default.
    """
    ...
