"""
Implement dataset management and loading utilities.

This module provides structures and functions to handle tropical cyclone
datasets, including metadata extraction and time series reconstruction
on uniform temporal grids.

Classes
-------
DatasetInfo
    Represent raw dataset details before processing.
Metadata
    Represent processed dataset metadata.
Dataset
    Represent a complete dataset with time series and metadata.

Functions
---------
load_dataset
    Load a dataset from a file or buffer and reconstruct time series.

"""

import dataclasses as dc
import io
import json
import typing as tp

import numpy as np
import numpy.typing as npt

from .utils import to_indices

type StrOrBytesPath = io.BytesIO | io.BufferedReader | str


@dc.dataclass(kw_only=True, frozen=True)
class DatasetInfo:
    """
    Represent raw dataset details before processing.

    This dataclass holds the information extracted directly from the
    storage format, including both metadata and raw data arrays.

    Attributes
    ----------
    event_name : str
        The identifier of the tropical cyclone event.
    spatial_resolution : int
        The numeric spatial resolution value.
    spatial_resolution_units : str
        The units for spatial resolution (e.g. "km").
    temporal_resolution : int
        The numeric temporal resolution value.
    temporal_resolution_units : str
        The units for temporal resolution (e.g. "min").
    radii : npt.NDArray[np.int32]
        The radial distances for the profiles.
    radii_units : str
        The units for radial distances.
    filenames : list[str]
        The list of filenames associated with the samples.
    dates : list[str]
        The list of timestamps for the samples.
    profiles : npt.NDArray[np.float32]
        The raw radial profiles data.
    valid_mask : npt.NDArray[np.bool_]
        A boolean mask indicating which temporal slots are valid.
    timeseries_shape : tuple[int, int]
        The dimensions of the full reconstructed time series.
    """

    event_name: str
    spatial_resolution: int
    spatial_resolution_units: str
    temporal_resolution: int
    temporal_resolution_units: str
    radii: npt.NDArray[np.int32]
    radii_units: str
    filenames: list[str]
    dates: list[str]
    profiles: npt.NDArray[np.float32]
    valid_mask: npt.NDArray[np.bool_]
    timeseries_shape: tuple[int, int]


@dc.dataclass(kw_only=True, frozen=True)
class Metadata:
    """
    Represent processed dataset metadata.

    Attributes
    ----------
    event_name : str
        The identifier of the tropical cyclone event.
    n_samples : int
        The total number of temporal samples (including gaps).
    n_series : int
        The number of radial points (time series).
    spatial_resolution : int
        The numeric spatial resolution value.
    spatial_resolution_units : str
        The units for spatial resolution.
    temporal_resolution : int
        The numeric temporal resolution value.
    temporal_resolution_units : str
        The units for temporal resolution.
    radii : npt.NDArray[np.int32]
        The radial distances for the profiles.
    radii_units : str
        The units for radial distances.
    filenames : list[str]
        The list of filenames associated with the samples.
    iso_dates : list[str]
        The list of dates in ISO format for each temporal slot.
    """

    event_name: str
    n_samples: int
    n_series: int
    spatial_resolution: int
    spatial_resolution_units: str
    temporal_resolution: int
    temporal_resolution_units: str
    radii: npt.NDArray[np.int32]
    radii_units: str
    filenames: list[str]
    iso_dates: list[str]


@dc.dataclass(kw_only=True, frozen=True)
class Dataset:
    """
    Represent a complete dataset with time series and metadata.

    Attributes
    ----------
    timeseries : npt.NDArray[np.floating]
        The reconstructed time series data (num_series, num_samples).
    valid_mask : npt.NDArray[np.bool_]
        A mask indicating which temporal slots have valid data.
    metadata : Metadata
        The associated metadata for the dataset.
    """

    timeseries: npt.NDArray[np.floating]
    valid_mask: npt.NDArray[np.bool_]
    metadata: Metadata

    @property
    def gap_indices(self) -> npt.NDArray[np.intp]:
        """
        Identify the indices of temporal slots without data.

        Returns
        -------
        npt.NDArray[np.intp]
            The indices of temporal gaps.
        """
        return to_indices(~self.valid_mask)

    @property
    def profiles(self) -> npt.NDArray[np.floating]:
        """
        Provide the radial profiles view of the dataset.

        Returns
        -------
        npt.NDArray[np.floating]
            The profiles data (num_samples, num_series).
        """
        return self.timeseries.T

    @property
    def valid_indices(self) -> npt.NDArray[np.intp]:
        """
        Identify the indices of temporal slots with valid data.

        Returns
        -------
        npt.NDArray[np.intp]
            The indices of valid data samples.
        """
        return to_indices(self.valid_mask)


def load_dataset(
    *, file: StrOrBytesPath, dtype: npt.DTypeLike | None = None
) -> Dataset:
    """
    Load a dataset from a file or buffer and reconstruct time series.

    Parameters
    ----------
    file : StrOrBytesPath
        The path or buffer containing the NumPy-stored dataset.
    dtype : npt.DTypeLike, optional
        The desired data type for the time series. If `None`, the
        original type is preserved.

    Returns
    -------
    Dataset
        The reconstructed dataset instance.
    """
    data = np.load(file=file, allow_pickle=False)

    metainfo = _extract_info(data)

    return _construct_dataset(metainfo, dtype)


def _construct_dataset(
    metainfo: DatasetInfo, dtype: npt.DTypeLike | None
) -> Dataset:
    """
    Assemble a Dataset instance from raw info.

    Parameters
    ----------
    metainfo : DatasetInfo
        The raw dataset info extracted from storage.
    dtype : npt.DTypeLike | None
        The target data type for numerical arrays.

    Returns
    -------
    Dataset
        The finished Dataset object.
    """
    valid_indices = to_indices(metainfo.valid_mask)

    metadata = _construct_metadata(metainfo, valid_indices)

    timeseries = _construct_timeseries(
        metainfo.profiles, valid_indices, metainfo.timeseries_shape, dtype
    )

    dataset_dict: dict[str, tp.Any] = {
        "timeseries": timeseries,
        "valid_mask": metainfo.valid_mask,
        "metadata": Metadata(**metadata),
    }

    return Dataset(**dataset_dict)


def _construct_list(
    rawdata: list[str], indices: npt.NDArray[np.intp], length: int
) -> list[str]:
    """
    Distribute list items into a larger list at specific indices.

    Parameters
    ----------
    rawdata : list[str]
        The items to distribute.
    indices : npt.NDArray[np.intp]
        The target positions for the items.
    length : int
        The total length of the resulting list.

    Returns
    -------
    list[str]
        A list of specified length with items placed at the requested
        indices.
    """
    distributed_list = [""] * length
    for i, index in enumerate(indices):
        distributed_list[index] = rawdata[i]

    return distributed_list


def _construct_metadata(
    metainfo: DatasetInfo, valid_indices: npt.NDArray[np.intp]
) -> dict[str, tp.Any]:
    """
    Prepare metadata dictionary from raw info.

    Parameters
    ----------
    metainfo : DatasetInfo
        The raw info.
    valid_indices : npt.NDArray[np.intp]
        The indices of temporal slots with data.

    Returns
    -------
    dict[str, tp.Any]
        A dictionary suitable for Metadata instantiation.
    """
    metadata: dict[str, tp.Any] = dc.asdict(metainfo)

    n_samples, n_series = metainfo.timeseries_shape

    filenames = _construct_list(metainfo.filenames, valid_indices, n_samples)
    iso_dates = _construct_list(metainfo.dates, valid_indices, n_samples)

    metadata["n_samples"] = n_samples
    metadata["n_series"] = n_series
    metadata["filenames"] = filenames
    metadata["iso_dates"] = iso_dates

    del metadata["dates"]
    del metadata["profiles"]
    del metadata["valid_mask"]
    del metadata["timeseries_shape"]
    return metadata


def _construct_timeseries(
    profiles: npt.NDArray[np.floating],
    indices: npt.NDArray[np.intp],
    shape: tuple[int, int],
    dtype: npt.DTypeLike | None,
) -> npt.NDArray[np.floating]:
    """
    Reconstruct time series on a uniform temporal grid.

    Parameters
    ----------
    profiles : npt.NDArray[np.floating]
        Array of radial profiles for valid time instances.
    indices : npt.NDArray[np.intp]
        The temporal indices where profiles should be placed.
    shape : tuple[int, int]
        The target dimensions (num_samples, num_series).
    dtype : npt.DTypeLike | None
        Target data type for the array.

    Returns
    -------
    npt.NDArray[np.floating]
        The reconstructed time series array (num_series, num_samples).
    """
    ts_dtype = profiles.dtype if dtype is None else dtype
    timeseries = np.full(shape, np.nan, dtype=ts_dtype)
    timeseries[indices, :] = profiles.astype(ts_dtype)

    return timeseries.T


def _extract_info(data: tp.Any) -> DatasetInfo:
    """
    Extract raw dataset info from NumPy data keys.

    Parameters
    ----------
    data : tp.Any
        The loaded NumPy result mapping.

    Returns
    -------
    DatasetInfo
        The extracted information.
    """
    metainfo: dict[str, tp.Any] = json.loads(str(data["metadata"][0]))

    metainfo["radii"] = np.asarray(metainfo["radii"], dtype=np.int32)
    metainfo["profiles"] = np.asarray(data["profiles"], dtype=np.float32)
    metainfo["valid_mask"] = np.asarray(metainfo["valid_mask"], dtype=np.bool_)
    metainfo["timeseries_shape"] = tuple(metainfo["timeseries_shape"])

    return DatasetInfo(**metainfo)


__all__ = [
    "Dataset",
    "DatasetInfo",
    "Metadata",
    "load_dataset",
]
