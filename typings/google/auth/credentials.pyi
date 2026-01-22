import abc
from collections.abc import Sequence

from google.auth.transport.requests import Request

class Credentials(metaclass=abc.ABCMeta):
    @property
    def valid(self) -> bool: ...
    def refresh(self, request: Request) -> None: ...

class AnonymousCredentials(Credentials): ...

class CredentialsWithQuotaProject(Credentials, metaclass=abc.ABCMeta):
    def with_quota_project(self, quota_project_id: str) -> None: ...

class ReadOnlyScoped(metaclass=abc.ABCMeta):
    def has_scopes(self, scopes: Sequence[str]) -> bool: ...
