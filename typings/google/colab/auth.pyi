# Copyright 2017 Google Inc.
"""Colab-specific authentication helpers."""

import enum as _enum
from collections.abc import Generator

__all__ = ["authenticate_service_account", "authenticate_user"]

_CHECK_GCLOUD_AUTH_ERRORS: bool = True

def _is_service_account_key(key_json_text: str | bytes) -> bool:
    """
    Return true if the provided text is a JSON service credentials file.
    Inferred from json.loads usage.
    """
    ...

def _set_gcloud_project(project_id: str, clear_output: bool) -> None:
    """
    Inferred from gcloud command list and usage in authenticate_user.
    """
    ...

def _set_no_service_account_env_for_project(project_id: str) -> None:
    """
    Sets project environment variables.
    """
    ...

class _CredentialType(_enum.Enum):
    """Enum class for selecting the type of credential that is expected."""

    NO_CHECK = 0
    USER = 1
    SERVICE_ACCOUNT = 2

def _check_adc(
    credential_type: _CredentialType = _CredentialType.NO_CHECK,
) -> bool:
    """
    Return whether the application default credential exists and is valid.

    Args:
        credential_type: Inferred from default value and enum type.
    """
    ...

def _gcloud_login() -> None:
    """Call `gcloud auth login` with custom input handling."""
    ...

def _get_adc_path() -> str:
    """Inferred from os.path.join and dir_path usage."""
    ...

def _install_adc() -> None:
    """Install the gcloud token as the Application Default Credential."""
    ...

def _enable_metadata_server_for_gcloud() -> None:
    """Removes GCE cache and unsets timeout config."""
    ...

def _noop() -> Generator[None, None, None]:
    """Null context manager."""
    ...

def authenticate_user(
    clear_output: bool = True, project_id: str | None = None
) -> None:
    """
    Ensures that the given user is authenticated.

    Args:
        clear_output: Inferred as bool from default True.
        project_id: Inferred as str | None from rule 4 (default None + usage in os.environ).
    """
    ...

def _activate_service_account_key(
    key_content: str | bytes, clear_output: bool
) -> None:
    """
    Activates service account credentials with gcloud.
    """
    ...

def authenticate_service_account(clear_output: bool = True) -> None:
    """
    Ensures that a service account key is present and valid.

    Args:
        clear_output: Inferred as bool from default True.
    """
    ...
