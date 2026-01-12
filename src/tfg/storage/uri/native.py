import pathlib as pl

from .base import URIMapper


class NativeURIMapper(URIMapper):

    def __init__(self, *, base_path: str = ".", strict: bool = True) -> None:
        self.base_path = pl.Path(base_path).resolve(strict=strict)

    def __repr__(self) -> str:
        return f"NativeURIMapper(base_path={self.base_path!r})"

    def get_base_path(self) -> str:
        return str(self.base_path)

    def relative_to(self, *, absolute_uri: str) -> str:
        return str(pl.Path(absolute_uri).relative_to(self.base_path))

    def resolve(self, *, logical_uri: str, strict: bool = False) -> str:
        return str((self.base_path / logical_uri).resolve(strict=strict))
