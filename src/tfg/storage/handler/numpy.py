import io
import typing as tp

import numpy as np

from .base import DataHandler


class NumpyHandler(DataHandler):
    """
    Handler para cargar y guardar archivos NumPy (.npy, .npz).

    Parameters
    ----------
    allow_pickle : bool, optional
        Indica si se permite cargar objetos serializados con pickle. Por
        defecto es False.
    compressed : bool, optional
        Indica si los archivos .npz se guardan comprimidos. Por defecto
        es True.
    npz : bool, optional
        Indica si se utiliza el formato .npz (True) o .npy (False) para
        guardar los datos. Por defecto es True.

    Atributes
    ---------
    allow_pickle : bool
        Indica si se permite cargar objetos serializados con pickle.
    compressed : bool
        Indica si los archivos .npz se guardan comprimidos.
    npz : bool
        Indica si se utiliza el formato .npz (True) o .npy (False) para
        guardar los datos.

    Methods
    -------
    load(stream: tp.BinaryIO) -> tp.Any
        Carga datos NumPy desde un flujo binario.
    save(data: tp.Any, stream: tp.BinaryIO) -> None
        Guarda datos NumPy en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este
        handler.
    """

    def __init__(
        self,
        *,
        allow_pickle: bool = False,
        compressed: bool = True,
        npz: bool = True,
    ) -> None:
        self.allow_pickle = allow_pickle
        self.compressed = compressed
        self.npz = npz

    def __repr__(self) -> str:
        return (
            f"NumpyHandler(allow_pickle={self.allow_pickle}, "
            f"compressed={self.compressed}, npz={self.npz})"
        )

    def copy(self) -> DataHandler:
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        return NumpyHandler(
            allow_pickle=self.allow_pickle,
            compressed=self.compressed,
            npz=self.npz,
        )

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos NumPy desde un flujo binario.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los datos NumPy.

        Returns
        -------
        tp.Any
            Datos NumPy cargados desde el flujo.
        """
        # Posicionamos el stream al inicio por seguridad
        stream.seek(0)
        return np.load(stream, allow_pickle=self.allow_pickle)

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos NumPy en un flujo binario.

        Parameters
        ----------
        data : tp.Any
            Datos a guardar en el flujo.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos NumPy.
        """
        stream.seek(0)

        if self.npz:
            self._save_npz(data=data, stream=stream)
        else:
            np.save(stream, data, allow_pickle=self.allow_pickle)

        stream.truncate()  # Eliminar datos sobrantes si había algo antes

    def _save_npz(
        self, *, data: dict[str, tp.Any], stream: io.BytesIO
    ) -> None:
        """
        Guarda múltiples arrays en un archivo .npz.

        Parameters
        ----------
        data : dict[str, tp.Any]
            Diccionario de arrays a guardar.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos.
        """
        if self.compressed:
            np.savez_compressed(stream, allow_pickle=self.allow_pickle, **data)
        else:
            np.savez(stream, allow_pickle=self.allow_pickle, **data)

    @property
    def format_id(self) -> list[str]:
        """
        Identificadores formato.

        Devuelve una lista con los identificadores de formato de datos
        manejado por este handler.

        Returns
        -------
        list[str]
            Identificadores del formato de datos.
        """
        return [".npz"] if self.npz else [".npy"]
