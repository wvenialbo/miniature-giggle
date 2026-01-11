import dataclasses as dc
import json
import os
import typing as tp
import warnings

import numpy as np
import numpy.typing as npt
from google import colab

from .storage.filehandler import FileHandler
from .utils import format_report, format_table, get_columns_size, to_indices


class GoogleDriver:
    """
    Clase para manejar la conexión con Google Drive en Google Colab.

    Parameters
    ----------
    storage : list[tuple[str, StorageInterface]]
        Lista de tuplas con el nombre del formato y la instancia del
        manejador de almacenamiento correspondiente.
    directory : str
        Directorio en Google Drive donde se almacenan los archivos.
    mountpoint : str, optional
        Punto de montaje en Google Colab.  Por defecto es
        '/content/drive'.

    Attributes
    ----------
    mountpoint : str
        Punto de montaje en Google Colab.
    directory : str
        Directorio en Google Drive donde se almacenan los archivos.
    rootpath_ : str
        Ruta raíz en Google Drive después de montar (se crea al montar).

    Methods
    -------
    mount(fail: bool = True) -> None
        Monta Google Drive si aún no está montado.
    unmount(fail: bool = True) -> None
        Desmonta Google Drive y guarda todos los cambios.
    is_mounted() -> bool
        Verifica si Google Drive está montado.
    get_pathname(filename: str) -> str
        Obtiene la ruta completa de un archivo en Google Drive.
    exists(filename: str) -> bool
        Verifica si un archivo existe en Google Drive.
    load(filename: str) -> Any
        Carga datos desde un archivo en Google Drive.
    save(data: Any, filename: str) -> None
        Guarda datos en un archivo en Google Drive.
    """

    def __init__(
        self,
        *,
        storage: list[tuple[str, FileHandler]],
        directory: str,
        mountpoint: str = "/content/drive",
    ) -> None:
        self.mountpoint = mountpoint
        self.directory = directory
        self.storage = storage

    def __repr__(self) -> str:
        return (
            f"GoogleDriver(directory='{self.directory}', "
            f"mountpoint='{self.mountpoint}')"
        )

    def __str__(self) -> str:
        """
        Genera un reporte profesional con el estado y configuración.

        Returns
        -------
        str
            Reporte formateado con la configuración y estado actual.
        """
        mounted = self.is_mounted() and self.is_active()

        rootpath = self.rootpath_ if mounted else "No montado"

        config_data = [
            ("Directorio en Drive", f"'{self.directory}'", ""),
            ("Punto de montaje en Colab", f"'{self.mountpoint}'", ""),
            ("Ruta raíz", f"'{rootpath}'", ""),
        ]

        # Construir tabla de configuración
        size = get_columns_size(config_data)

        config_table = format_table(size, "CONFIGURACIÓN", config_data)

        status = "Montado" if mounted else "Desmontado"

        header = f"GoogleDriver - Estado: {status}"

        return format_report(header, config_table)

    def _activate(self) -> None:
        rootpath = os.path.join(self.mountpoint, self.directory)

        if not (os.path.exists(rootpath) and os.path.isdir(rootpath)):
            raise RuntimeError(
                f"La ruta '{rootpath}' no existe en Google Drive."
            )

        self.rootpath_ = rootpath
        self.storagehandler_ = dict(self.storage)

    def _deactivate(self) -> None:
        del self.rootpath_
        del self.storagehandler_

    def exists(self, *, filename: str) -> bool:
        """
        Verifica si un archivo existe en Google Drive.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        bool
            True si el archivo existe, False en caso contrario.
        """
        check_drive_mounted(self)

        pathname = self.get_pathname(filename=filename)

        return os.path.exists(pathname) and os.path.isfile(pathname)

    def get_pathname(self, *, filename: str) -> str:
        """
        Obtiene la ruta completa de un archivo en Google Drive.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        str
            Ruta completa del archivo en Google Drive.
        """
        check_drive_mounted(self)

        return os.path.join(self.rootpath_, filename)

    def _get_storage_handler(self, pathname: str) -> FileHandler:
        """
        Obtiene el manejador de almacenamiento para un archivo dado.

        Parameters
        ----------
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        StorageInterface
            Manejador de almacenamiento correspondiente.

        Raises
        ------
        ValueError
            Si el formato del archivo no es compatible.
        """
        path_ext = os.path.splitext(pathname)[1]

        if path_ext in self.storagehandler_:
            return self.storagehandler_[path_ext]

        raise ValueError(
            f"El formato del archivo '{pathname}' no es compatible"
        )

    def is_active(self) -> bool:
        """
        Verifica si el manejador de Google Drive está activo.

        Returns
        -------
        bool
            True si el manejador está activo, False en caso contrario.
        """
        return hasattr(self, "rootpath_") and hasattr(self, "storagehandler_")

    def is_mounted(self) -> bool:
        """
        Verifica si Google Drive está montado.

        Returns
        -------
        bool
            True si Google Drive está montado, False en caso contrario.
        """
        return os.path.exists(self.mountpoint) and os.path.isdir(
            self.mountpoint
        )

    def load(self, *, filename: str) -> tp.Any:
        """
        Carga datos desde un archivo en Google Drive.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        pathname = self.get_pathname(filename=filename)

        loaded_data = self._load_from_drive(pathname)

        print(f"Datos cargados desde: '{filename}'")

        return loaded_data

    def _load_from_drive(self, pathname: str) -> tp.Any:
        """
        Carga datos desde un archivo en Google Drive.

        Parameters
        ----------
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        check_drive_mounted(self)

        storage_handler = self._get_storage_handler(pathname)

        return storage_handler.load(filename=pathname)

    def mount(self, *, fail: bool = True) -> None:
        """
        Monta Google Drive si aún no está montado.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede montar Google
            Drive.  Por defecto es True.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Si la ruta raíz no existe en Google Drive.
        """
        if self.is_mounted():
            if not self.is_active():
                self._activate()
            return

        colab.drive.mount(self.mountpoint)

        if not self.is_mounted():
            err_message = "No se pudo montar Google Drive."
            if fail:
                raise RuntimeError(err_message)
            warnings.warn(err_message, RuntimeWarning)
            return

        self._activate()

    def register_storage(
        self,
        *,
        storage: list[tuple[str, FileHandler]] | tuple[str, FileHandler],
    ) -> None:
        """
        Registra un nuevo manejador de almacenamiento.

        Parameters
        ----------
        storage : list[tuple[str, StorageInterface]] | tuple[str, StorageInterface]
            Manejador de almacenamiento a registrar.

        Returns
        -------
        None
        """
        if isinstance(storage, tuple):
            storage = [storage]

        self.storage.extend(storage)

    def save(self, *, data: tp.Any, filename: str) -> None:
        """
        Guarda datos en un archivo en Google Drive.

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
        pathname = self.get_pathname(filename=filename)

        self._save_to_drive(data, pathname)

        print(f"Datos guardados en: '{pathname}'")

    def _save_to_drive(self, data: tp.Any, pathname: str) -> None:
        """
        Guarda datos en un archivo en Google Drive.

        Parameters
        ----------
        data : Any
            Datos a guardar.
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        None
        """
        check_drive_mounted(self)

        storage_handler = self._get_storage_handler(pathname)

        return storage_handler.save(data=data, filename=pathname)

    def unmount(self, *, fail: bool = True) -> None:
        """
        Desmonta Google Drive y guarda todos los cambios.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede desmontar
            Google Drive.  Por defecto es True.

        Returns
        -------
        None
        """
        if not self.is_mounted():
            if self.is_active():
                self._deactivate()
            return

        colab.drive.flush_and_unmount()

        if self.is_mounted():
            err_message = "No se pudo desmontar Google Drive."
            if fail:
                raise RuntimeError(err_message)
            warnings.warn(err_message, RuntimeWarning)
            return

        self._deactivate()


def check_drive_mounted(drive: GoogleDriver) -> None:
    """
    Verifica si Google Drive está montado.

    Parameters
    ----------
    drive : GoogleDriver
        Instancia de GoogleDriver.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        Si Google Drive no está montado.
    """
    if not (drive.is_mounted() and drive.is_active()):
        raise RuntimeError(
            "Google Drive no está montado. "
            "Por favor, monte Google Drive antes de continuar."
        )


@dc.dataclass(kw_only=True, frozen=True)
class DatasetInfo:
    event_name: str
    spatial_resolution: int
    spatial_resolution_units: str
    temporal_resolution: int
    temporal_resolution_units: str
    radii: npt.NDArray[np.int32]
    radii_units: str
    filenames: list[str]
    dates: list[str]
    profiles: npt.NDArray[np.float32]
    valid_mask: npt.NDArray[np.bool_]
    timeseries_shape: tuple[int, int]


@dc.dataclass(kw_only=True, frozen=True)
class Metadata:
    event_name: str
    n_samples: int
    n_series: int
    spatial_resolution: int
    spatial_resolution_units: str
    temporal_resolution: int
    temporal_resolution_units: str
    radii: npt.NDArray[np.int32]
    radii_units: str
    filenames: list[str]
    iso_dates: list[str]


@dc.dataclass(kw_only=True, frozen=True)
class Dataset:
    timeseries: npt.NDArray[np.floating]
    valid_mask: npt.NDArray[np.bool_]
    metadata: Metadata

    @property
    def gap_indices(self) -> npt.NDArray[np.intp]:
        return to_indices(~self.valid_mask)

    @property
    def profiles(self) -> npt.NDArray[np.floating]:
        return self.timeseries.T

    @property
    def valid_indices(self) -> npt.NDArray[np.intp]:
        return to_indices(self.valid_mask)


class DatasetRepository:

    def __init__(self, *, drive: GoogleDriver) -> None:
        self.drive = drive

    def __repr__(self) -> str:
        return f"DatasetRepository(drive={repr(self.drive)})"

    def activate(self) -> None:
        self.drive.mount()

    @classmethod
    def _construct_dataset(
        cls, metainfo: DatasetInfo, dtype: npt.DTypeLike | None
    ) -> Dataset:
        metadata: dict[str, tp.Any] = dc.asdict(metainfo)

        n_samples, n_series = metainfo.timeseries_shape

        valid_indices = to_indices(metainfo.valid_mask)

        filenames = cls._construct_list(
            metainfo.filenames, valid_indices, n_samples
        )
        iso_dates = cls._construct_list(
            metainfo.dates, valid_indices, n_samples
        )

        metadata["n_samples"] = n_samples
        metadata["n_series"] = n_series
        metadata["filenames"] = filenames
        metadata["iso_dates"] = iso_dates

        del metadata["dates"]
        del metadata["profiles"]
        del metadata["valid_mask"]
        del metadata["timeseries_shape"]

        timeseries = cls._construct_timeseries(
            metainfo.profiles, valid_indices, metainfo.timeseries_shape, dtype
        )

        dataset: dict[str, tp.Any] = {
            "timeseries": timeseries,
            "valid_mask": metainfo.valid_mask,
            "metadata": Metadata(**metadata),
        }

        return Dataset(**dataset)

    @staticmethod
    def _construct_list(
        rawdata: list[str], indices: npt.NDArray[np.intp], length: int
    ) -> list[str]:
        dataset = [""] * length
        for i, index in enumerate(indices):
            dataset[index] = rawdata[i]

        return dataset

    @staticmethod
    def _construct_timeseries(
        profiles: npt.NDArray[np.floating],
        indices: npt.NDArray[np.intp],
        shape: tuple[int, int],
        dtype: npt.DTypeLike | None,
    ) -> npt.NDArray[np.floating]:
        # Reconstruye las series temporales en una grilla temporal uniforme.

        # Parameters
        # ----------
        # profiles : array float (n, m)
        #     Array con n perfiles radiales de promedio acimutal, correspondientes a
        #     n instantes de tiempo (no uniformemente distribuidos), y m mediciones
        #     radiales, correspondientes a m series temporales.
        # indices : array int (p,)
        #     Array con los índices dónde colocar los perfiles en una grilla
        #     temporal uniformemente distribuida (p >= n).
        # shape : tuple[int, int]
        #     Tupla con la forma de la serie temporal original.

        # Return
        # ------
        # timeseries : array (m, p)
        #     Array con m series temporales reconstruidas en una grilla temporal
        #     uniforme, con NaN en los instantes donde no hay datos. Las filas
        #     son series temporales, y las columnas son perfiles radiales.
        ts_dtype = profiles.dtype if dtype is None else dtype
        timeseries = np.full(shape, np.nan, dtype=ts_dtype)
        timeseries[indices, :] = profiles.astype(ts_dtype)

        return timeseries.T

    def deactivate(self) -> None:
        self.drive.unmount()

    @staticmethod
    def _extract_info(data: tp.Any) -> DatasetInfo:
        metainfo: dict[str, tp.Any] = json.loads(str(data["metadata"][0]))

        metainfo["radii"] = np.asarray(metainfo["radii"], dtype=np.int32)
        metainfo["profiles"] = np.asarray(data["profiles"], dtype=np.float32)
        metainfo["valid_mask"] = np.asarray(
            metainfo["valid_mask"], dtype=np.bool_
        )
        metainfo["timeseries_shape"] = tuple(metainfo["timeseries_shape"])

        datainfo = DatasetInfo(**metainfo)

        return datainfo

    def load(self, *, src: str, dtype: npt.DTypeLike | None = None) -> Dataset:
        data = self.drive.load(filename=src)

        metainfo = self._extract_info(data)

        dataset = self._construct_dataset(metainfo, dtype)

        return dataset
