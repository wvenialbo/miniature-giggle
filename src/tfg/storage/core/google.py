import os
import typing as tp
import warnings

from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build  # type: ignore

from ..backend import GoogleDriveAPIBackend
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..uri import GoogleDriveURIMapper


class GoogleDrive:
    def __init__(self, service: Resource) -> None:
        self.service = service

    def open(self, *, fail: bool = False) -> bool:
        try:
            # Test simple de conectividad
            self.service.about().get(fields="user").execute()  # type: ignore
            return True
        except Exception as e:
            self._report_failure(f"Error conectando a Drive API: {e}", fail)
            return False

    @staticmethod
    def _report_failure(error_message: str, fail: bool) -> None:
        """
        Informa de un fallo lanzando una excepción o emitiendo una
        advertencia.

        Parameters
        ----------
        error_message : str
            Mensaje de error a utilizar en la excepción o advertencia.
        fail : bool
            Si es True, lanza una excepción RuntimeError con el mensaje
            de error.  Si es False, emite una advertencia RuntimeWarning
            con el mensaje de error.

        Returns
        -------
        None
        """
        if fail:
            raise RuntimeError(error_message)

        warnings.warn(error_message, RuntimeWarning)


def use_drive_api(
    *,
    root_path: str = "/",
    service: Resource | None = None,
    credentials_path: str | None = None,
    handlers: list[DataHandler] | None = None,
) -> DatasourceContract:
    """
    Factoría para crear un contexto de Google Drive API.
    """
    if service is None:
        if credentials_path is None or not os.path.exists(credentials_path):
            raise ValueError(
                "Se requiere un objeto 'service' o una ruta válida a 'credentials_path'"
            )

        # Lógica de carga de credenciales (simplificada)
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = tp.cast(Resource, build("drive", "v3", credentials=creds))

    connection = GoogleDrive(service=service)
    backend = GoogleDriveAPIBackend(service=service)

    # Reutilizamos GenericURIMapper ya que la API no usa paths nativos de SO
    mapper = GoogleDriveURIMapper(base_path=root_path)

    if handlers is None:
        handlers = _get_file_handlers()

    return Datasource(
        connection=connection,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )
