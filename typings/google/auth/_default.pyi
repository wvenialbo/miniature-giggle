from collections.abc import Sequence

from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

def default(
    scopes: Sequence[str] | None = None,
    request: Request | None = None,
    quota_project_id: str | None = None,
    default_scopes: Sequence[str] | None = None,
) -> tuple[Credentials, str | None]: ...
