from collections.abc import Sequence

from google.auth import credentials

class Credentials(
    credentials.ReadOnlyScoped, credentials.CredentialsWithQuotaProject
):
    @classmethod
    def from_authorized_user_file(
        cls, filename: str, scopes: Sequence[str] | None = None
    ) -> Credentials: ...
    def to_json(self, strip: Sequence[str] | None = None) -> str: ...
