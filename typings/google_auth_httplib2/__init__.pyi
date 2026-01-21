from collections.abc import Sequence
from typing import Any

import httplib2

class AuthorizedHttp(httplib2.Http):
    def __init__(
        self,
        credentials: Any,
        http: httplib2.Http | None = None,
        refresh_status_codes: Sequence[int] = ...,
        max_refresh_attempts: int = ...,
    ) -> None:
        """
        Args:
            credentials (google.auth.credentials.Credentials): The credentials
                to add to the request.
            http (httplib2.Http): The underlying HTTP object to
                use to make requests. If not specified, a
                :class:`httplib2.Http` instance will be constructed.
            refresh_status_codes (Sequence[int]): Which HTTP status codes
                indicate that credentials should be refreshed and the request
                should be retried.
            max_refresh_attempts (int): The maximum number of times to attempt
                to refresh the credentials and retry the request.
        """
        ...
