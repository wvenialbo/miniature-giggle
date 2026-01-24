"""
Provide common utility functions for storage operations.

This module offers helper functions used across different storage
backends to ensure consistent path handling and configuration.

Functions
---------
calculate_mountpoint(root_path)
    Determine the POSIX-style virtual mountpoint for a given path.
"""

from pathlib import Path, PurePosixPath


def calculate_mountpoint(
    *, root_path: str | None, mountpoint: str = "/", base_path: str = ""
) -> PurePosixPath:
    """
    Determine the virtual mountpoint for a given root path.

    Calculate a standardized POSIX-style path to serve as the root for
    virtual file systems. This ensures consistent path addressing
    regardless of the underlying operating system's drive letter
    conventions.

    Parameters
    ----------
    root_path : str | None
        The user-provided root path. If ``None``, defaults to the root
        directory.
    mountpoint : str, optional
        The base mountpoint to use. Defaults to "/".
    base_path : str, optional
        An additional base path segment to append to the mountpoint.
        Defaults to "".

    Returns
    -------
    PurePosixPath
        The normalized, absolute POSIX path for the mountpoint.

    Notes
    -----
    This function resolves the absolute path and strips any drive
    letters (e.g., 'C:') to create a uniform path structure suitable for
    cross-platform usage.
    """
    local_root = PurePosixPath(mountpoint) / base_path
    local_path = Path("/" if root_path is None else root_path).resolve()
    local_path = local_path.relative_to(local_path.anchor)
    return local_root / local_path.as_posix()
