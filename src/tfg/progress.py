import collections.abc as col

import tqdm.auto


def tqdm_progress(
    *,
    iterable: col.Iterable[bytes],
    total_size: int,
    description: str | None = None,
) -> col.Iterable[bytes]:
    return tqdm.auto.tqdm(
        iterable,
        total=total_size,
        unit="B",
        unit_scale=True,
        desc=description,
        leave=True,
    )
