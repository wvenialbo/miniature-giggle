import pathlib as pl

from .base import AbstractCache, CacheBase

DriveCache = CacheBase[tuple[str, str]]
ScanCache = CacheBase[list[str]]

ID_PREFIX = "id://"


class GoogleDriveCacheWrapper(AbstractCache):
    """
    Coordina la invalidación de la caché de rutas -> IDs (DriveCache)
    y la caché de rutas -> listados (ScanCache).
    """

    def __init__(self, drive_cache: DriveCache, scan_cache: ScanCache):
        self._drive_cache = drive_cache
        self._scan_cache = scan_cache

    def invalidate(self, path: str) -> None:
        # 1. Obtiene el ítem en caché (si existe)
        cached_item = self._drive_cache.get(path)

        if cached_item is None:
            return

        file_id, _ = cached_item

        # 2. Invalida el mapeo de ruta -> ID
        self._drive_cache.invalidate(path)

        # 3. Actualiza la caché de listados de la carpeta padre
        parent_path = str(pl.PurePosixPath(path).parent)
        cached_content = self._scan_cache.get(parent_path)

        if cached_content is None:
            return

        def get_id(uri: str) -> str:
            return uri.split("|")[0].replace(ID_PREFIX, "")

        if indices_to_remove := [
            i for i, uri in enumerate(cached_content) if get_id(uri) == file_id
        ]:
            index_to_remove = indices_to_remove[0]
            del cached_content[index_to_remove]
            if cached_content:
                self._scan_cache.set(parent_path, cached_content)

        # 4. Invalida las cachés de la carpeta padre si es necesario
        if not cached_content:
            self._scan_cache.invalidate(parent_path)
            self._drive_cache.invalidate(parent_path)

    def clear(self) -> None:
        self._drive_cache.clear()
        self._scan_cache.clear()

    def purge(self) -> None:
        self._drive_cache.purge()
        self._scan_cache.purge()
