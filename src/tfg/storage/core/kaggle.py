import os
import pathlib as pl
import re

from kaggle.api.kaggle_api_extended import KaggleApi

from ..backend import KaggleBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import KaggleURIMapper

KAGGLE_PREFIX = "kaggle://"
KAGGLE_SEPARATOR = "/"
POSIX_PREFIX = "/"


def use_kaggle_dataset(
    *,
    dataset: str,
    root_path: str | None = None,
    username: str | None = None,
    key: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a un dataset de Kaggle.

    Configura un backend para acceder a los archivos de un dataset de Kaggle
    utilizando la API oficial. El acceso depende de las credenciales
    configuradas en el entorno (archivo kaggle.json o variables de entorno).
    Permite autenticación mediante parámetros directos, lo cual es útil si
    no existe el archivo 'kaggle.json'.

    Parameters
    ----------
    dataset : str
        Identificador del dataset en formato 'owner/dataset-slug'.
    root_path : str, optional
        Ruta lógica raíz para montar este dataset. Por defecto '/'
        seguido del slug del dataset.
    username : str, optional
        Nombre de usuario de Kaggle para autenticación.
    key : str, optional
        Llave de la API (Kaggle Key) para autenticación.
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de las operaciones
        'scan'.
    expire_after : float, optional
        Tiempo en segundos tras el cual expira la caché de escaneo.
        Si es None, la caché no expira automáticamente.

    Returns
    -------
    DatasourceContract
        Objeto orquestador configurado para Kaggle.
    """
    # 1. Configuración de credenciales en el entorno (si se proveen)
    if username:
        os.environ["KAGGLE_USERNAME"] = username
    if key:
        os.environ["KAGGLE_KEY"] = key

    # 2. Configuración de la API de Kaggle
    api = _initialize_kaggle_api()

    # Aseguramos que el dataset tenga el formato esperado owner/slug
    _check_kaggle_uri(dataset)

    # 3. Inicialización de la Caché de Listado (ScanCache)
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedScanCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    # 4. Configuración de rutas y puntos de montaje
    # Si no se define root_path, usamos el slug del dataset como carpeta base
    if root_path is None:
        dataset_slug = dataset.split("/")[-1]
        root_path = f"/{dataset_slug}"

    mountpoint = _configure_mountpoint(root_path)

    # 5. Instanciación de componentes
    mapper = KaggleURIMapper(dataset=dataset)

    backend = KaggleBackend(
        api=api,
        dataset=dataset,
        scan_cache=scan_cache,
    )

    # 6. Retorno del Orquestador
    return Datasource(
        mountpoint=mountpoint,
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )


def _check_kaggle_uri(owner_slug: str) -> None:
    # Aseguramos que el dataset tenga el formato esperado owner/slug
    # owner: alfanumérico, punto o guion
    # slug: empieza por letra o número, sigue con alfanuméricos o
    #       guiones, entre 3 y 50 total
    kaggle_pattern = r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$"
    if bool(re.match(kaggle_pattern, owner_slug)):
        return

    raise ValueError(
        f"Formato de dataset inválido: '{owner_slug}'. "
        "Se esperaba 'owner/dataset-slug'."
    )


def _configure_mountpoint(root_path: str) -> str:
    """Resuelve y normaliza el punto de montaje lógico."""
    base_path = pl.Path(root_path).resolve()
    # Eliminar el ancla (ej: 'C:/' o '/') para hacerlo relativo al montar
    relative_base = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath(POSIX_PREFIX)
    return str(local_root / relative_base.as_posix())


def _initialize_kaggle_api() -> KaggleApi:
    """
    Inicializa y autentica el cliente de la API de Kaggle.

    Notes
    -----
    La autenticación es automática si el archivo kaggle.json está
    en ~/.kaggle/ o si KAGGLE_USERNAME y KAGGLE_KEY están en el entorno.
    """
    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as e:
        # Nota: Kaggle API suele imprimir errores en consola,
        # aquí intentamos capturarlos para dar contexto.
        raise RuntimeError(
            "No se pudo autenticar la API de Kaggle. Asegúrese de tener "
            "configuradas sus credenciales correctamente."
        ) from e
    return api
