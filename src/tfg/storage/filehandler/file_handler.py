import typing as tp


class FileHandlerInterface(tp.Protocol):
    def load(self, *, filename: str) -> tp.Any: ...

    def save(self, *, data: tp.Any, filename: str) -> None: ...
