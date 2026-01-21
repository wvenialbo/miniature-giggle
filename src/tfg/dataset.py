import dataclasses as dc
import io
import json
import typing as tp

import numpy as np
import numpy.typing as npt

from .utils import to_indices

StrOrBytesPath = io.BytesIO | io.BufferedReader | str


@dc.dataclass(kw_only=True, frozen=True)
class DatasetInfo:
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
    timeseries: npt.NDArray[np.floating]
    valid_mask: npt.NDArray[np.bool_]
    metadata: Metadata

    @property
    def gap_indices(self) -> npt.NDArray[np.intp]:
        return to_indices(~self.valid_mask)

    @property
    def profiles(self) -> npt.NDArray[np.floating]:
        return self.timeseries.T

    @property
    def valid_indices(self) -> npt.NDArray[np.intp]:
        return to_indices(self.valid_mask)


def load_dataset(
    *, file: StrOrBytesPath, dtype: npt.DTypeLike | None = None
) -> Dataset:
    data = np.load(file=file, allow_pickle=False)

    metainfo = _extract_info(data)

    return _construct_dataset(metainfo, dtype)


def _construct_dataset(
    metainfo: DatasetInfo, dtype: npt.DTypeLike | None
) -> Dataset:
    valid_indices = to_indices(metainfo.valid_mask)

    metadata = _construct_metadata(metainfo, valid_indices)

    timeseries = _construct_timeseries(
        metainfo.profiles, valid_indices, metainfo.timeseries_shape, dtype
    )

    dataset: dict[str, tp.Any] = {
        "timeseries": timeseries,
        "valid_mask": metainfo.valid_mask,
        "metadata": Metadata(**metadata),
    }

    return Dataset(**dataset)


def _construct_list(
    rawdata: list[str], indices: npt.NDArray[np.intp], length: int
) -> list[str]:
    dataset = [""] * length
    for i, index in enumerate(indices):
        dataset[index] = rawdata[i]

    return dataset


def _construct_metadata(
    metainfo: DatasetInfo, valid_indices: npt.NDArray[np.intp]
) -> dict[str, tp.Any]:
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
    # Reconstruye las series temporales en una grilla temporal uniforme.

    # Parameters
    # ----------
    # profiles : array float (n, m)
    #     Array con n perfiles radiales de promedio acimutal, correspondientes a
    #     n instantes de tiempo (no uniformemente distribuidos), y m mediciones
    #     radiales, correspondientes a m series temporales.
    # indices : array int (p,)
    #     Array con los índices dónde colocar los perfiles en una grilla
    #     temporal uniformemente distribuida (p >= n).
    # shape : tuple[int, int]
    #     Tupla con la forma de la serie temporal original.

    # Return
    # ------
    # timeseries : array (m, p)
    #     Array con m series temporales reconstruidas en una grilla temporal
    #     uniforme, con NaN en los instantes donde no hay datos. Las filas
    #     son series temporales, y las columnas son perfiles radiales.
    ts_dtype = profiles.dtype if dtype is None else dtype
    timeseries = np.full(shape, np.nan, dtype=ts_dtype)
    timeseries[indices, :] = profiles.astype(ts_dtype)

    return timeseries.T


def _extract_info(data: tp.Any) -> DatasetInfo:
    metainfo: dict[str, tp.Any] = json.loads(str(data["metadata"][0]))

    metainfo["radii"] = np.asarray(metainfo["radii"], dtype=np.int32)
    metainfo["profiles"] = np.asarray(data["profiles"], dtype=np.float32)
    metainfo["valid_mask"] = np.asarray(metainfo["valid_mask"], dtype=np.bool_)
    metainfo["timeseries_shape"] = tuple(metainfo["timeseries_shape"])

    return DatasetInfo(**metainfo)
