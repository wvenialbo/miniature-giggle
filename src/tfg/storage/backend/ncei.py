import re
import urllib.parse as url

import requests

from ..backend import StorageBackend
from ..cache import CacheBase, DummyCache

NCEICache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]


class NCEIBackend(StorageBackend):
    """Backend de solo lectura para repositorios HTTP de NCEI."""

    def __init__(self, scan_cache: NCEICache | None = None) -> None:
        self.scan_cache = scan_cache or NoopCache()
        self._session = requests.Session()

    def __repr__(self) -> str:
        return f"NCEIBackend(scan_cache={repr(self.scan_cache)})"

    def read(self, *, uri: str) -> bytes:
        response = self._session.get(uri, timeout=15)
        response.raise_for_status()
        return response.content

    def scan(self, *, prefix: str) -> list[str]:
        # El prefijo en este caso es una URL de directorio
        folder_url = prefix if prefix.endswith("/") else f"{prefix}/"

        # Intentar recuperar de caché si existe
        if self.scan_cache:
            cached = self.scan_cache.get(folder_url)
            if cached is not None:
                return cached

        response = self._session.get(folder_url, timeout=15)
        if response.status_code != 200:
            return []

        # Extraer enlaces href del HTML (lógica heredada de
        # DatasourceNCEI)
        href_links: list[str] = re.findall(
            r'<a\s+href="([^"]+)"', response.text
        )

        # Normalizar URLs: filtrar las que suben de nivel y convertir a
        # absolutas
        results: list[str] = []
        for href in href_links:
            if href.startswith("?") or ".." in href:
                continue

            # Unir para asegurar URIs absolutas nativas
            full_url = url.urljoin(folder_url, href)
            results.append(full_url)

        if self.scan_cache:
            self.scan_cache.set(folder_url, results)

        return results

    def exists(self, *, uri: str) -> bool:
        response = self._session.head(uri, timeout=10)
        return response.status_code == 200

    def write(self, *, uri: str, data: bytes) -> None:
        raise RuntimeError("NCEIBackend no soporta operaciones de escritura.")

    def delete(self, *, uri: str) -> None:
        raise RuntimeError(
            "NCEIBackend no soporta operaciones de eliminación."
        )

    def create_path(self, *, uri: str) -> str:
        raise RuntimeError("NCEIBackend no soporta creación de rutas.")
