import pickle  # nosec
import typing as tp
import warnings


class PickleFileHandler:
    """
    Clase para manejar la carga y guardado de archivos pickle.

    Methods
    -------
    load(filename: str) -> Any
        Carga datos desde un archivo pickle.
    save(data: Any, filename: str) -> None
        Guarda datos en un archivo pickle.
    """

    def __repr__(self) -> str:
        return "PickleFileHandler()"

    @staticmethod
    def _issue_warning() -> None:
        warnings.warn(
            "El uso de archivos pickle puede ser inseguro. "
            "Asegúrese de que el archivo provenga de una "
            "fuente confiable",
            UserWarning,
        )

    def load(self, *, filename: str) -> tp.Any:
        """
        Carga datos desde un archivo pickle.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        self._issue_warning()
        with open(filename, "rb") as file:
            return pickle.load(file)  # nosec

    def save(self, *, data: tp.Any, filename: str) -> None:
        """
        Guarda datos en un archivo pickle.

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
        self._issue_warning()
        with open(filename, "wb") as file:
            pickle.dump(data, file)  # nosec
