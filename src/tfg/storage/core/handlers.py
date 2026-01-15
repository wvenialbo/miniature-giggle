"""
Fábrica para crear contextos de almacenamiento preconfigurados.

Proporciona una interfaz simple para crear DataSourceContexts
preconfigurados para diferentes backends (Colab, local, S3, etc.).
"""

from ..handler import (
    BypassHandler,
    CSVHandler,
    DataHandler,
    JSONHandler,
    NumpyHandler,
    PickleHandler,
    YAMLHandler,
)

_DEFAULT_HANDLERS: list[DataHandler] = [
    BypassHandler(),
    CSVHandler(),
    JSONHandler(),
    NumpyHandler(),
    PickleHandler(),
    YAMLHandler(),
]

# Handlers de archivo por defecto
_file_handlers: list[DataHandler] = _DEFAULT_HANDLERS.copy()


def get_file_handlers() -> list[DataHandler]:
    """Obtiene la lista de handlers de archivo por defecto."""
    return [handler.copy() for handler in _file_handlers]


def reset_default_handlers() -> None:
    """
    Restablece la lista de handlers de archivo por defecto a los originales.

    Parameters
    ----------
    handlers : list[DataHandler]
        Nueva lista de handlers de archivo por defecto.
    """
    global _file_handlers
    _file_handlers = _DEFAULT_HANDLERS.copy()


def set_default_handlers(handlers: list[DataHandler]) -> None:
    """
    Establece la lista de handlers de archivo por defecto.

    Parameters
    ----------
    handlers : list[DataHandler]
        Nueva lista de handlers de archivo por defecto.
    """
    format_id = [id for handler in handlers for id in handler.format_id]
    if len(format_id) != len(set(format_id)):
        repeated = sorted(
            {fmt_id for fmt_id in format_id if format_id.count(fmt_id) > 1}
        )
        duplicates = "', '".join(repeated)
        raise ValueError(
            f"Existen handlers con extensiones duplicados: '{duplicates}'"
        )

    global _file_handlers
    _file_handlers = [handler.copy() for handler in handlers]
