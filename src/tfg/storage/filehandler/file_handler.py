import typing as tp


class FileHandler(tp.Protocol):
    """
    Protocolo para manejar la carga y guardado de archivos.

    Methods
    -------
    load(filename: str) -> Any
        Carga datos desde un archivo.
    save(data: Any, filename: str) -> None
        Guarda datos en un archivo.
    """

    def load(self, *, filename: str) -> tp.Any:
        """
        Load data from a file.

        Parameters
        ----------
        filename : str
            The name of the file to load data from.

        Returns
        -------
        tp.Any
            The data loaded from the file.
        """

        ...

    def save(self, *, data: tp.Any, filename: str) -> None:
        """
        Save data to a file.

        Parameters
        ----------
        data : tp.Any
            The data to save to the file.
        filename : str
            The name of the file to save data to.
        """
        ...
