import os
import warnings


class LocalFileSystemMounter:
    def __init__(self, *, mountpoint: str = os.getcwd()) -> None:
        self.mountpoint = mountpoint

    def is_mounted(self) -> bool:
        return os.path.exists(self.mountpoint) and os.path.isdir(
            self.mountpoint
        )

    def mount(self, *, fail: bool = True) -> None:
        if self.is_mounted():
            return

        self._report_failure(f"No se pudo montar '{self.mountpoint}'", fail)

    def unmount(self, *, fail: bool = True) -> None:
        return

    def _report_failure(self, error_message: str, fail: bool) -> None:
        if fail:
            raise RuntimeError(error_message)
        warnings.warn(error_message, RuntimeWarning)
