import typing as tp

import numpy as np


class NumpyFileHandler:
    """
    Clase para manejar la carga y guardado de archivos NumPy.

    Methods
    -------
    load(filename: str) -> Any
        Carga datos desde un archivo NumPy.
    save(data: Any, filename: str) -> None
        Guarda datos en un archivo NumPy.
    """

    def __repr__(self) -> str:
        return "NumpyFileHandler()"

    def load(self, *, filename: str) -> tp.Any:
        """
        Carga datos desde un archivo NumPy.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        return np.load(filename, allow_pickle=False)

    def save(self, *, data: tp.Any, filename: str) -> None:
        """
        Guarda datos en un archivo NumPy.

        Parameters
        ----------
        data : Any
            Datos a guardar.
        filename : str
            Nombre del archivo.

        Returns
        -------
        None
        """
        np.savez_compressed(filename, **data)
