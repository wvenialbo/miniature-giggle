import typing as tp


class URIMapper(tp.Protocol):

    def get_base_path(self) -> str: ...

    def relative_to(self, *, absolute_uri: str) -> str: ...

    def resolve(self, *, logical_uri: str, strict: bool = False) -> str: ...
