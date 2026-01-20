from collections.abc import Sequence
from typing import Any

from google.auth.credentials import Credentials
from google.auth.transport import Request

def default(
    scopes: Sequence[str] | None = None,
    request: Request | None = None,
    quota_project_id: str | None = None,
    default_scopes: Sequence[str] | None = None,
) -> tuple[Credentials | Any, str | None]: ...
