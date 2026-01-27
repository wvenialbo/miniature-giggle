"""
Provide interface for Amazon Web Services S3 storage data sources.

This module implements a single entry point, `use_aws_cloud`, to
instantiate and configure `Datasource` instances that access AWS S3
buckets. It handles credential resolution for both authenticated and
anonymous (public bucket) access modes, providing a seamless interface
for remote data access.

Functions
---------
use_aws_cloud(*, bucket, root_path=None, cache_file=None,
              expire_after=None, **kwargs)
    Create a data source context for Amazon Web Services S3 bucket.

Classes
-------
AWSCloudArgs
    Define comprehensive parameter list for AWS authentication.
S3SessionArgs
    Define partial parameter list for AWS authentication.

"""

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Unpack

from ..backend import AWSBackend
from ..cache import TimedCache
from ..datasource import DataService, Datasource
from ..mapper import AWSURIMapper
from .utils import calculate_mountpoint


if TYPE_CHECKING:
    from botocore.config import Config
    from botocore.session import Session
    from mypy_boto3_s3.client import S3Client as Client


S3_PREFIX = "s3://"


class S3SessionArgs(TypedDict, total=False):
    """
    Define partial parameter list for AWS authentication.

    Attributes
    ----------
    aws_access_key_id : str | None, optional
        AWS access key ID.
    aws_secret_access_key : str | None, optional
        AWS secret access key.
    aws_session_token : str | None, optional
        AWS temporary session token.
    botocore_session : Session | None, optional
        Pre-configured ``botocore`` session object.
    aws_account_id : str | None, optional
        AWS account ID.
    """

    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    botocore_session: "Session | None"
    aws_account_id: str | None


class AWSCloudArgs(S3SessionArgs):
    """
    Define comprehensive parameter list for AWS authentication.

    Attributes
    ----------
    region_name : str | None, optional
        Default region when creating new connections.
    profile_name : str | None, optional
        The name of a profile to use. If not given, it looks for
        credentials in environment variables or metadata service.
    """

    region_name: str | None
    profile_name: str | None


def _get_s3_client(
    profile_name: str | None = None,
    region_name: str | None = None,
    **kwargs: Unpack[S3SessionArgs],
) -> "tuple[Client, Config | None]":
    """
    Initialise an S3 client and its signature configuration.

    Create a ``boto3`` S3 client based on provided credentials or
    session parameters. If no credentials are found and none were
    explicitly requested, the client is configured for anonymous
    access to public buckets.

    Parameters
    ----------
    profile_name : str | None, optional
        The name of the AWS profile to use for credentials.
    region_name : str | None, optional
        The AWS region where the bucket is located.
    **kwargs : Unpack[S3SessionArgs]
        Additional keyword arguments for session configuration,
        including explicit credentials.

    Returns
    -------
    client : Client
        The initialised S3 client for bucket operations.
    config : Config | None
        The signature configuration for the client, which is
        non-``None`` only when anonymous access is required.

    Raises
    ------
    ValueError
        If credentials cannot be resolved when they were explicitly
        specified via a profile or explicit keys.

    See Also
    --------
    use_aws_cloud : Create a data source context for S3 bucket.

    Notes
    -----
    When no credentials are available and no profile or explicit
    keys were requested, the client is re-initialised with an
    unsigned signature. This allows access to public buckets
    without requiring AWS credentials.
    """
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    session = boto3.Session(
        profile_name=profile_name, region_name=region_name, **kwargs
    )
    creds = session.get_credentials()

    if creds is None:
        # Raise error if authentication was requested (via profile or
        # keys) but failed to resolve, rather than silently falling
        # back to anonymous (unsigned) requests.
        if profile_name or kwargs:
            raise ValueError(
                "Unable to obtain AWS credentials; verify profile "
                "configuration or provided credentials"
            )
        # Use unsigned signature to access public buckets anonymously.
        config = Config(signature_version=UNSIGNED)
        # Re-initialise session to ensure no implicit configuration
        # files interfere with the anonymous request context.
        session = boto3.Session(region_name=region_name)

    else:
        config = None

    return session.client("s3", config=config), config


def use_aws_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    cache_file: str | Path | None = None,
    expire_after: float | None = None,
    **kwargs: Unpack[AWSCloudArgs],
) -> Datasource:
    """
    Create a data source context for Amazon Web Services S3 bucket.

    Establish a data service connection to a specific S3 bucket. This
    service handles key mapping, local caching for listings, and file
    retrieval using the ``boto3`` library.

    Parameters
    ----------
    bucket : str
        The name of the S3 bucket to access (e.g. ``"noaa-goes16"``).
    root_path : str | None, optional
        The directory path to use as the data root. Relative paths
        are resolved against the current working directory; absolute
        paths map directly to the corresponding location in both the
        local filesystem and the cloud storage bucket. If ``None``, the
        bucket is used as the root.
    cache_file : str | Path | None, optional
        The path to a file for persisting directory listing caches.
        If ``None``, caching is transient or in-memory only.
    expire_after : float | None, optional
        The duration in seconds before cached entries are considered
        stale. If ``None``, entries might never expire.
    **kwargs : Unpack[AWSCloudArgs]
        Additional arguments for the ``boto3`` session, including
        region, profile name, credentials, and other session parameters.

    Returns
    -------
    Datasource
        The initialised data service configured for the specified S3
        bucket.

    Notes
    -----
    This service maintains a symmetric mapping: the provided `root_path`
    resolves to identical relative or absolute locations in both the
    local filesystem and the cloud storage environment. Path
    resolution follows the symmetric mapping logic implemented in
    `calculate_mountpoint`.

    Examples
    --------
    Initialise a data source for a public GOES-16 satellite imagery
    bucket:

    >>> from tfg.storage import use_aws_cloud
    >>> datasource = use_aws_cloud(
    ...     bucket="noaa-goes16",
    ...     region_name="us-east-1",
    ...     root_path="./data/goes16",
    ... )  # doctest: +SKIP
    """
    mountpoint = calculate_mountpoint(root_path=root_path)

    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedCache[list[str]](
        cache_file=cache_path_str, expire_after=expire_after
    )

    client, config = _get_s3_client(**kwargs)

    mapper = AWSURIMapper(bucket=bucket)
    backend = AWSBackend(
        bucket=bucket, client=client, scan_cache=scan_cache, config=config
    )

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )


__all__ = ["use_aws_cloud"]
