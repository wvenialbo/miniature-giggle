"""
Configure dataset access for Google Colab environment.

This module provides helpers to mount and access Google Drive within a
Google Colab notebook session. It bridges the local filesystem
available in Colab with the project's data source abstractions.

Functions
---------
use_colab_drive(*, root_path=None)
    Mount Google Drive and configure a data source.
release_colab_drive(*, fail=False)
    Unmount Google Drive and flush pending writes.
"""

import warnings
from pathlib import Path

from ...utils import running_on_colab
from ..backend import FilesystemBackend
from ..datasource import DataService, Datasource
from ..mapper import PathURIMapper
from .utils import calculate_mountpoint


try:
    from google.colab import drive

    def _colab_drive_flush_and_unmount() -> None:
        """Force flush and unmount using the colab sdk."""
        drive.flush_and_unmount()

    def _colab_drive_mount(mountpoint: str) -> None:
        """Mount the drive using the colab sdk."""
        drive.mount(mountpoint)

except ImportError:

    def _colab_drive_flush_and_unmount() -> None:
        """Raise error as colab sdk is missing."""
        _colab_not_found_error(_MOUNT_POINT)

    def _colab_drive_mount(mountpoint: str) -> None:
        """Raise error as colab sdk is missing."""
        _colab_not_found_error(mountpoint)

    def _colab_not_found_error(mountpoint: str) -> None:
        """
        Raise a RuntimeError indicating google.colab is missing.

        Raises
        ------
        RuntimeError
            Always raised to indicate missing dependency.
        """
        raise RuntimeError(
            "Module 'google.colab' unavailable; ensure code execution "
            "within a Google Colab environment."
        )


_MOUNT_POINT = "/content/drive"
_ROOT_PATH = "MyDrive"


def _is_mounted() -> bool:
    """
    Check if the standard Colab mount point is active.

    Returns
    -------
    bool
        True if running on Colab and the mount point is active.
    """
    return running_on_colab() and Path(_MOUNT_POINT).is_mount()


def _mount_drive(*, fail: bool = False) -> None:
    """
    Attempt to mount the Google Drive.

    Parameters
    ----------
    fail : bool, optional
        Whether to raise an exception on failure.
    """
    if _is_mounted():
        return

    _colab_drive_mount(_MOUNT_POINT)

    if not _is_mounted():
        _report_failure(
            f"Failed to mount Google Drive at '{_MOUNT_POINT}'", fail=fail
        )


def _report_failure(error_message: str, *, fail: bool) -> None:
    """
    Handle failure reporting via exception or warning.

    Parameters
    ----------
    error_message : str
        The message to display.
    fail : bool
        If ``True``, raise RuntimeError. Else warn.

    Raises
    ------
    RuntimeError
        If `fail` is ``True``.
    """
    if fail:
        raise RuntimeError(error_message)

    warnings.warn(error_message, RuntimeWarning, stacklevel=3)


def _unmount_drive(*, fail: bool = False) -> None:
    """
    Attempt to unmount the Google Drive.

    Parameters
    ----------
    fail : bool, optional
        Whether to raise an exception on failure.
    """
    if not _is_mounted():
        return

    _colab_drive_flush_and_unmount()

    if _is_mounted():
        _report_failure("Failed to unmount Google Drive", fail=fail)


def use_colab_drive(*, root_path: str | None = None) -> Datasource:
    """
    Mount Google Drive and configure a data source.

    Initialise the Colab runtime environment by mounting the user's
    Google Drive to the local filesystem. This allows transparent
    access to datasets stored in the 'MyDrive' folder.

    Parameters
    ----------
    root_path : str | None, optional
        The relative path within 'MyDrive' to use as the dataset root.
        If ``None``, the root of 'MyDrive' is used.

    Returns
    -------
    Datasource
        An initialized data service pointing to the mounted Drive path.
    """
    mountpoint = calculate_mountpoint(
        root_path=root_path, mountpoint=_MOUNT_POINT, base_path=_ROOT_PATH
    )

    _mount_drive(fail=True)

    mapper = PathURIMapper()
    backend = FilesystemBackend()

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
    )


def release_colab_drive(*, fail: bool = False) -> None:
    """
    Unmount Google Drive and flush pending writes.

    Force the synchronisation of any changes made to the mounted
    filesystem back to Google Drive and detach the mount point.

    Parameters
    ----------
    fail : bool, optional
        If ``True``, raise a generic exception if unmounting fails.
        If ``False``, issue a warning instead. Default is ``False``.
    """
    _unmount_drive(fail=fail)


__all__ = ["release_colab_drive", "use_colab_drive"]
