import os

try:
    from google import colab

    def colab_drive_flush_and_unmount() -> None:  # type: ignore
        colab.drive.flush_and_unmount()

    def colab_drive_mount(mountpoint: str) -> None:  # type: ignore
        colab.drive.mount(mountpoint)

    def running_on_colab() -> bool:
        return bool(os.getenv("COLAB_RELEASE_TAG"))

except ImportError:

    def colab_drive_flush_and_unmount() -> None:
        colab_not_found_error()

    def colab_drive_mount(_: str) -> None:
        colab_not_found_error()

    def colab_not_found_error() -> None:
        raise RuntimeError(
            "El módulo 'colab' de Google no está disponible. "
            "Asegúrate de estar ejecutando este código en "
            "Google Colab"
        )

    def running_on_colab() -> bool:
        return False


class ColabDriveBackend:
    """
    Backend para Google Drive en Google Colab.

    Esta clase proporciona métodos para interactuar con Google Drive
    montado en Google Colab, incluyendo operaciones para leer, escribir,
    eliminar y listar archivos.

    Parameters
    ----------
    mountpoint : str
        Ruta base para todas las URIs. Por defecto es '/content/drive'.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        self.mountpoint = mountpoint

    def __repr__(self) -> str:
        return f"ColabDriveBackend(mountpoint='{self.mountpoint}')"

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        if not running_on_colab():
            colab_not_found_error()

        path = self._resolve_path(uri)
        return os.path.exists(path)

    def list_files(self, *, prefix: str) -> list[str]:
        """
        Lista las URIs que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URIs.

        Returns
        -------
        list[str]
            Una lista de URIs que comienzan con el prefijo dado.
        """
        base_dir = self._resolve_path(prefix)

        if not (os.path.exists(base_dir) and os.path.isdir(base_dir)):
            raise ValueError(
                "La ruta especificada no existe "
                f"o no es un directorio: {base_dir}"
            )

        uris: list[str] = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.mountpoint)
                uris.append(relative_path)

        return uris

    def read(self, *, uri: str) -> bytes:
        """
        Lee datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        """
        if not running_on_colab():
            colab_not_found_error()

        path = self._resolve_path(uri)
        with open(path, "rb") as file:
            return file.read()

    def _resolve_path(self, uri: str) -> str:
        """Resuelve URI a ruta completa en Google Drive."""
        full_path = os.path.join(self.mountpoint, uri)
        return os.path.normpath(full_path)

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        if not running_on_colab():
            colab_not_found_error()

        path = self._resolve_path(uri)

        with open(path, "wb") as file:
            file.write(data)
