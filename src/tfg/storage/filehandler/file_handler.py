import typing as tp


class FileHandler(tp.Protocol):
    def load(self, *, filename: str) -> tp.Any: ...

    def save(self, *, data: tp.Any, filename: str) -> None: ...
