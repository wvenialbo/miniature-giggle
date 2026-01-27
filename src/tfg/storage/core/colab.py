"""
Provide interface for Google Colab environment storage data sources.

This module implements a single entry point, `use_colab_drive`, to
initialise and configure `Datasource` instances that access Google
Drive within a Colab session. It bridges the local filesystem
available in Colab with the project's data service abstractions.

Functions
---------
use_colab_drive(*, root_path=None)
    Create a data source context for Google Drive access within Colab.
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
        """Force flush and unmount using the Google Colab SDK."""
        drive.flush_and_unmount()

    def _colab_drive_mount(mountpoint: str) -> None:
        """Mount the drive using the Google Colab SDK."""
        drive.mount(mountpoint)

except ImportError:

    def _colab_drive_flush_and_unmount() -> None:
        """Raise error as Google Colab SDK is missing."""
        _colab_not_found_error(_MOUNT_POINT)

    def _colab_drive_mount(mountpoint: str) -> None:
        """Raise error as Google Colab SDK is missing."""
        _colab_not_found_error(mountpoint)

    def _colab_not_found_error(mountpoint: str) -> None:
        """
        Raise a `RuntimeError` indicating ``google.colab`` is missing.

        Raises
        ------
        RuntimeError
            Always raised to indicate missing dependency.
        """
        raise RuntimeError(
            "Module 'google.colab' is unavailable outside of a Google "
            "Colab environment."
        )


_MOUNT_POINT = "/content/drive"
_ROOT_PATH = "MyDrive"


def _is_mounted() -> bool:
    """
    Check if the standard Google Colab mount point is active.

    Returns
    -------
    bool
        ``True`` if running on Colab and the mount point is active.
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
            f"Google Drive mount failed at '{_MOUNT_POINT}'", fail=fail
        )


def _report_failure(error_message: str, *, fail: bool) -> None:
    """
    Handle failure reporting via exception or warning.

    Parameters
    ----------
    error_message : str
        The message to display.
    fail : bool
        If ``True``, raise `RuntimeError`. Else warn.

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
        _report_failure("Google Drive unmount failed", fail=fail)


def use_colab_drive(*, root_path: str | None = None) -> Datasource:
    """
    Create a data source context for Google Drive access within Colab.

    Initialise the Colab runtime environment by mounting the user's
    Google Drive to the local filesystem. This allows transparent access
    to datasets stored in the 'MyDrive' folder.

    Parameters
    ----------
    root_path : str | None, optional
        The directory path to use as the data root. Relative paths are
        resolved against the current working directory; absolute paths
        map directly to the corresponding location in both the local
        filesystem and Google Drive. If ``None``, the root ('MyDrive')
        is used.

    Returns
    -------
    Datasource
        The initialised data service pointing to the mounted Drive path.

    Notes
    -----
    This service maintains a symmetric mapping: the provided `root_path`
    resolves to identical relative or absolute locations in both the
    local filesystem and the mounted Google Drive environment. Path
    resolution follows the symmetric mapping logic implemented in
    :func:`~tfg.storage.core.utils.calculate_mountpoint`.

    Examples
    --------
    Initialise a data source for the root of 'MyDrive':

    >>> from tfg.storage import use_colab_drive
    >>> ds = use_colab_drive()  # doctest: +SKIP

    Initialise a data source for a specific project subfolder:

    >>> ds = use_colab_drive(root_path="data")  # doctest: +SKIP
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
        If ``False``, issue a warning instead.

    Examples
    --------
    Flush and unmount the drive after data processing is finished:

    >>> from tfg.storage.core.colab import release_colab_drive
    >>> release_colab_drive()  # doctest: +SKIP
    """
    _unmount_drive(fail=fail)


__all__ = ["release_colab_drive", "use_colab_drive"]
