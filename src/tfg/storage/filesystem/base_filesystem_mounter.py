import warnings


class BaseFileSystemMounter:
    """
    Clase base para montar y desmontar sistemas de archivos.
    """

    def _report_failure(self, error_message: str, fail: bool) -> None:
        if fail:
            raise RuntimeError(error_message)
        warnings.warn(error_message, RuntimeWarning)
