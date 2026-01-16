from ..mapper import URIMapper


class NCEIURIMapper(URIMapper):
    """Mapeador para transformar rutas lógicas en URLs de NCEI Archive."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def to_native(self, uri: str) -> str:
        """Convierte una ruta lógica en una URL absoluta de NCEI."""
        relative_path = uri.lstrip("/")
        return (
            f"{self.base_url}/{relative_path}"
            if relative_path
            else self.base_url
        )

    def to_generic(self, uri: str) -> str:
        """Convierte una URL de NCEI en una ruta lógica POSIX."""
        if not uri.startswith(self.base_url):
            raise ValueError(
                f"La URL '{uri}' no pertenece a la base '{self.base_url}'"
            )

        path = uri.replace(self.base_url, "", 1)
        return "/" + path.lstrip("/")
