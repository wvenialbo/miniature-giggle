from collections.abc import Mapping, Sequence
from typing import Any

from google.auth.external_account_authorized_user import (
    Credentials as AuthCredentials,
)
from google.oauth2.credentials import Credentials as OAuthCredentials

class Flow: ...

class InstalledAppFlow(Flow):
    @classmethod
    def from_client_config(
        cls,
        client_config: Mapping[str, Any],
        scopes: Sequence[str],
        **kwargs: Any,
    ) -> InstalledAppFlow: ...
    @classmethod
    def from_client_secrets_file(
        cls,
        client_secrets_file: str,
        scopes: list[str],
        **kwargs: Any,
    ) -> InstalledAppFlow: ...
    def run_local_server(
        self,
        host: str = "localhost",
        bind_addr: str | None = None,
        port: int = 8080,
        authorization_prompt_message: str | None = ...,
        success_message: str | None = ...,
        open_browser: bool = True,
        redirect_uri_trailing_slash: bool = True,
        timeout_seconds: int | None = None,
        token_audience: str | None = None,
        browser: str | None = None,
        **kwargs: Any,
    ) -> AuthCredentials | OAuthCredentials: ...
