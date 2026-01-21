# Copyright 2016 Google LLC
"""Interfaces for credentials."""

import abc
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Any

from google.auth._credentials_base import _BaseCredentials
from google.auth._refresh_worker import RefreshThreadManager

DEFAULT_UNIVERSE_DOMAIN: str = "googleapis.com"
NO_OP_TRUST_BOUNDARY_LOCATIONS: list[str] = []
NO_OP_TRUST_BOUNDARY_ENCODED_LOCATIONS: str = "0x0"

class Credentials(_BaseCredentials):
    """Base class for all credentials."""

    expiry: datetime | None
    _quota_project_id: str | None
    _trust_boundary: dict[str, Any] | None
    _universe_domain: str | None
    _use_non_blocking_refresh: bool
    _refresh_worker: RefreshThreadManager

    def __init__(self) -> None: ...
    @property
    def expired(self) -> bool: ...
    @property
    def valid(self) -> bool: ...
    @property
    def token_state(self) -> TokenState: ...
    @property
    def quota_project_id(self) -> str | None: ...
    @property
    def universe_domain(self) -> str | None: ...
    def get_cred_info(self) -> Mapping[str, str] | None: ...
    @abc.abstractmethod
    def refresh(self, request: Any) -> None: ...
    def _metric_header_for_usage(self) -> str | None: ...
    def apply(
        self, headers: Mapping[str, str], token: str | None = None
    ) -> None: ...
    def _blocking_refresh(self, request: Any) -> None: ...
    def _non_blocking_refresh(self, request: Any) -> None: ...
    def before_request(
        self, request: Any, method: str, url: str, headers: Mapping[str, str]
    ) -> None: ...
    def with_non_blocking_refresh(self) -> None: ...

class CredentialsWithQuotaProject(Credentials):
    """Abstract base for credentials supporting ``with_quota_project`` factory"""

    def with_quota_project(self, quota_project_id: str) -> Credentials: ...
    def with_quota_project_from_environment(self) -> Credentials: ...

class CredentialsWithTokenUri(Credentials):
    """Abstract base for credentials supporting ``with_token_uri`` factory"""

    def with_token_uri(self, token_uri: str) -> Credentials: ...

class CredentialsWithUniverseDomain(Credentials):
    """Abstract base for credentials supporting ``with_universe_domain`` factory"""

    def with_universe_domain(self, universe_domain: str) -> Credentials: ...

class CredentialsWithTrustBoundary(Credentials):
    """Abstract base for credentials supporting ``with_trust_boundary`` factory"""

    @abc.abstractmethod
    def _refresh_token(self, request: Any) -> None: ...
    def with_trust_boundary(
        self, trust_boundary: Mapping[str, str]
    ) -> Credentials: ...
    def _is_trust_boundary_lookup_required(self) -> bool: ...
    def _get_trust_boundary_header(self) -> dict[str, str]: ...
    def apply(
        self, headers: Mapping[str, str], token: str | None = None
    ) -> None: ...
    def refresh(self, request: Any) -> None: ...
    def _refresh_trust_boundary(self, request: Any) -> None: ...
    def _lookup_trust_boundary(self, request: Any) -> dict[str, Any]: ...
    @abc.abstractmethod
    def _build_trust_boundary_lookup_url(self) -> str | None: ...
    def _has_no_op_trust_boundary(self) -> bool: ...

class AnonymousCredentials(Credentials):
    """Credentials that do not provide any authentication information."""

    @property
    def expired(self) -> bool: ...
    @property
    def valid(self) -> bool: ...
    def refresh(self, request: Any) -> None: ...
    def apply(
        self, headers: Mapping[str, str], token: str | None = None
    ) -> None: ...
    def before_request(
        self, request: Any, method: str, url: str, headers: Mapping[str, str]
    ) -> None: ...

class ReadOnlyScoped(metaclass=abc.ABCMeta):
    """Interface for credentials whose scopes can be queried."""

    _scopes: Sequence[str] | None
    _default_scopes: Sequence[str] | None

    def __init__(self) -> None: ...
    @property
    def scopes(self) -> Sequence[str] | None: ...
    @property
    def default_scopes(self) -> Sequence[str] | None: ...
    @abc.abstractproperty
    def requires_scopes(self) -> bool: ...
    def has_scopes(self, scopes: Sequence[str]) -> bool: ...

class Scoped(ReadOnlyScoped):
    """Interface for credentials whose scopes can be replaced while copying."""

    @abc.abstractmethod
    def with_scopes(
        self,
        scopes: Sequence[str],
        default_scopes: Sequence[str] | None = None,
    ) -> Scoped: ...

def with_scopes_if_required(
    credentials: Credentials,
    scopes: Sequence[str],
    default_scopes: Sequence[str] | None = None,
) -> Credentials: ...

class Signing(metaclass=abc.ABCMeta):
    """Interface for credentials that can cryptographically sign messages."""

    @abc.abstractmethod
    def sign_bytes(self, message: bytes) -> bytes: ...
    @abc.abstractproperty
    def signer_email(self) -> str | None: ...
    @abc.abstractproperty
    def signer(self) -> Any: ...

class TokenState(Enum):
    """Tracks the state of a token."""

    FRESH = 1
    STALE = 2
    INVALID = 3
