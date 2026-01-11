# Copyright 2017 Google Inc.
"""Colab-specific file helpers."""

import socketserver as _socketserver
from http import server as _http_server
from typing import Any

__all__ = ["upload_file", "upload", "download", "view"]

def upload_file(filename: str) -> None:
    """
    Upload local (to the browser) file to the kernel.

    Args:
        filename: Name of the file to be written to. Deducido de open(filename, 'wb').
    """
    ...

def upload(target_dir: str = "") -> dict[str, bytes]:
    """
    Render a widget to upload local files to the kernel.

    Args:
        target_dir: Directory path. Inferred from os.makedirs usage.

    Returns:
        A map of the form {filename: file_contents}.
        Contents are bytes (inferred from 'ab' mode and b64decode).
    """
    ...

def _upload_file(filepath: str | None = None) -> tuple[str, bytes] | None:
    """
    Internal widget for single file upload.

    Args:
        filepath: Optional string path. If None, uses original filename.

    Returns:
        A 2-element tuple of (filename, contents), or None if cancelled.
    """
    ...

def _upload_files(multiple: bool) -> dict[str, bytes]:
    """
    Internal helper for the upload widget logic.

    Args:
        multiple: Boolean to enable multiple file selection.

    Returns:
        Dictionary mapping filenames to bytes contents.
    """
    ...

def _get_unique_filename(filename: str) -> str:
    """
    Generates a unique filename if the target already exists.
    """
    ...

class _V6Server(_socketserver.TCPServer):
    address_family: int  # socket.AF_INET6

class _FileHandler(_http_server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with a couple tweaks."""

    def translate_path(self, path: str) -> str: ...
    def log_message(self, format: str, *args: Any) -> None: ...
    def end_headers(self) -> None: ...

def download(filename: str) -> None:
    """
    Downloads the file to the user's local disk via a browser action.

    Args:
        filename: Name of the file on disk. Inferred from os.path.exists.
    """
    ...

def view(filepath: str) -> None:
    """
    Views a file in Colab's file viewer.

    Args:
        filepath: Path to the file or directory. Inferred from os.path.abspath.
    """
    ...
