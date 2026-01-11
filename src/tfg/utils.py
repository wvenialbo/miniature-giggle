import typing as tp

import numpy as np
import numpy.typing as npt


def to_indices(mask: npt.NDArray[np.bool_]) -> npt.NDArray[np.intp]:
    """
    Convierte una máscara booleana en índices de los elementos True.

    Parameters
    ----------
    mask : npt.NDArray[np.bool_]
        Una máscara booleana.

    Returns
    -------
    npt.NDArray[np.intp]
        Un array de índices correspondientes a los elementos True en la máscara.
    """
    return np.flatnonzero(mask)


def check_frequencies(frequencies: npt.ArrayLike) -> npt.NDArray[np.float64]:
    # 1. Validación rápida

    # Asegurar que tenemos un array
    frequencies = np.asarray(frequencies, dtype=np.float64)

    if frequencies.ndim != 1:
        raise ValueError("El array de frecuencias debe ser unidimensional")

    # Verificar si el array está vacío
    if frequencies.size == 0:
        raise ValueError("El array de frecuencias está vacío")

    # 2. Validación general de datos

    # Validar tipos de datos
    if not np.issubdtype(frequencies.dtype, np.floating):
        raise TypeError(
            "El array de frecuencias debe contener valores numéricos float, "
            f"pero tiene tipo '{frequencies.dtype}'"
        )

    # Verificar que todas las frecuencias sean finitas
    if not np.all(np.isfinite(frequencies)):
        raise ValueError("El array de frecuencias contiene valores no finitos")

    # Verificar que todas las frecuencias sean no negativas
    if not np.all(frequencies >= 0):
        raise ValueError("El array de frecuencias contiene valores negativos")

    return frequencies


def check_is_active(self: tp.Any, attributes: list[str]) -> bool:
    """
    Verifica si una instancia de una clase está activa.

    Verifica si una instancia está activa comprobando la presencia de
    los atributos dinámicos especificados.

    Parameters
    ----------
    self : tp.Any
        Instancia que contiene los atributos.
    attributes : list[str]
        Lista de nombres de atributos a verificar.

    Returns
    -------
    bool
        True si todos los atributos existen, False en caso contrario.
    """
    return all(hasattr(self, attr) for attr in attributes)


def check_is_fitted(self: tp.Any, attributes: list[str]) -> None:
    """
    Verifica si una instancia de un estimador ha sido ajustada.

    Parameters
    ----------
    self : tp.Any
        Instancia que contiene los atributos.
    attributes : list[str]
        Lista de nombres de atributos a verificar.

    Raises
    ------
    ValueError
        Si alguno de los atributos no existe en la instancia.
    """
    for attr in attributes:
        if not hasattr(self, attr):
            raise ValueError(f"El estimador no ha sido ajustado con '{attr}'")


def check_mode(
    self: tp.Any,
    attribute: str,
    mode: tp.Any,
    discourage_single_char: bool = True,
) -> None:
    """
    Verifica que el atributo tenga un valor dentro de los modos permitidos.

    Parameters
    ----------
    self : tp.Any
        Instancia que contiene el atributo.
    attribute : str
        Nombre del atributo a verificar.
    mode : tp.Any
        Modos permitidos para el atributo.
    discourage_single_char : bool, optional
        Si es True, desaconseja modos de un solo carácter. Por defecto es True.

    Raises
    ------
    ValueError
        Si el atributo no existe o su valor no está en los modos permitidos.
    """
    if not hasattr(self, attribute):
        raise ValueError(
            f"El parámetro '{attribute}' no existe en la instancia."
        )

    attribute_value = getattr(self, attribute)
    valid_modes = set(tp.get_args(mode))

    if attribute_value not in valid_modes:
        modes = sorted(valid_modes)
        if discourage_single_char:
            modes = [mode for mode in modes if len(mode) > 1]

        modes_str = "', '".join(modes)

        raise ValueError(
            f"El parámetro '{attribute}' debe ser uno de: '{modes_str}'"
        )


def check_timeseries(time_series: npt.ArrayLike) -> npt.NDArray[np.float64]:
    # 1. Validación rápida

    # Asegurar que tenemos un array 2D
    time_series = np.asarray(time_series, dtype=np.float64)

    if time_series.ndim == 1:
        time_series = time_series.reshape(1, -1)

    # Verificar si el array está vacío
    if time_series.size == 0:
        raise ValueError("El array de series temporales está vacío")

    # 2. Validación general de datos

    n_times = time_series.shape[1]

    # Validar tamaño mínimo de series temporales
    if n_times < 2:
        raise ValueError(
            f"Cada serie temporal debe tener al menos 2 puntos. "
            f"Recibido: {n_times} puntos por serie"
        )

    # Validar tipos de datos
    if not np.issubdtype(time_series.dtype, np.floating):
        raise TypeError(
            "El array de series temporales debe contener valores numéricos "
            f"float, pero tiene tipo '{time_series.dtype}'"
        )

    # Verificar que todas las series tengan NaN en las mismas columnas
    nan_mask = np.isnan(time_series)
    nan_by_column = nan_mask == nan_mask[0, :]
    if not np.all(nan_by_column, axis=0).all():
        raise ValueError("Las series tienen NaNs en columnas no homogéneas")

    return time_series


TOPRULE = "@═"
MIDRULE = "@─"
BOTTOMRULE = "@-"


def format_table(
    size: tuple[int, int], title: str, data_lines: list[tuple[str, str, str]]
) -> list[str]:
    """
    Formatea una linea de una tabla con los datos proporcionados.

    Parameters
    ----------
    size : tuple[int, int]
        Tamaño de las dos primeras columnas.
    title : str
        El título de la tabla.
    data_lines : list[tuple[str, str, str]]
        Una lista de tuplas que contienen los datos a imprimir en la tabla.

        Cada tupla debe tener tres elementos:
        - El primer elemento es la columna de la etiqueta.
        - El segundo elemento es la columna del valor.
        - El tercer elemento es la columna de la unidad de medida.

    Returns
    -------
    None
    """
    data_table = [f"{title}", MIDRULE]
    for label, value, units in data_lines:
        if not value:
            continue
        if value in {"No ajustado", "No establecido", "No montado"}:
            units = ""
        data_table.append(f"{label:<{size[0]}}:{value:>{size[1]}} {units}")

    return data_table


def format_report(header: str, data_table: list[str]) -> str:
    """
    Formatea un informe reemplazando las líneas especiales.

    Parameters
    ----------
    header : str
        El encabezado del informe.
    data_table : list[str]
        Las líneas del informe a formatear.

    Returns
    -------
    str
        El informe formateado.
    """
    formatted_lines = _format_lines(header, data_table)

    return "\n".join(formatted_lines)


def _format_lines(header: str, data_table: list[str]) -> list[str]:
    """
    Formatea un informe reemplazando las líneas especiales.

    Parameters
    ----------
    header : str
        El encabezado del informe.
    data_table : list[str]
        Las líneas del informe a formatear.

    Returns
    -------
    list[str]
        Las líneas formateadas del informe.
    """
    report_lines = [TOPRULE, header, TOPRULE] + data_table + [BOTTOMRULE]
    max_length = len(max(report_lines, key=len))

    replacements = {
        TOPRULE: TOPRULE[1] * max_length,
        MIDRULE: MIDRULE[1] * max_length,
    }

    return [replacements.get(line, line) for line in report_lines]


def get_columns_size(
    data_lines: list[tuple[str, str, str]], spacing: int = 1
) -> tuple[int, int]:
    """
    Obtiene el tamaño máximo de las dos primeras columnas de una tabla.

    Parameters
    ----------
    data_lines : list[tuple[str, str, str]]
        Una lista de tuplas que contienen los datos a imprimir en la tabla.

        Cada tupla debe tener tres elementos:
        - El primer elemento es la columna de la etiqueta.
        - El segundo elemento es la columna del valor.
        - El tercer elemento es la columna de la unidad de medida.
    spacing : int, optional
        Espacio adicional a añadir al tamaño de las columnas, por defecto 1.

    Returns
    -------
    tuple[int, int]
        Una tupla con el tamaño máximo de las dos primeras columnas.
    """
    # Calcular ancho de columnas
    label_length = max(len(label) for label, _, _ in data_lines) + spacing
    value_length = max(len(value) for _, value, _ in data_lines) + spacing

    return label_length, value_length
