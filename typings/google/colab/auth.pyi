# Copyright 2017 Google Inc.
"""Colab-specific authentication helpers."""

__all__ = ["authenticate_user"]

_CHECK_GCLOUD_AUTH_ERRORS: bool = True

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
