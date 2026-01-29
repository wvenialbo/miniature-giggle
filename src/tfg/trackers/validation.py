"""
Provide validation logic for tracker dataset files.

This module contains helper functions to verify the existence and
integrity of dataset files used by the tracking subpackage.

Functions
---------
validate_dataset_file
    Verify that a path points to an existing file.

"""

from pathlib import Path


def validate_dataset_file(path: str | Path) -> Path:
    """
    Verify that a path points to an existing file.

    Parameters
    ----------
    path : str | Path
        The filesystem path to validate.

    Returns
    -------
    Path
        The validated Path object.

    Raises
    ------
    FileNotFoundError
        If the path does not exist or refers to a directory.
    """
    path_obj = Path(path)

    if not path_obj.is_file():
        raise FileNotFoundError(f"File '{path_obj}' does not exist.")

    return path_obj


__all__ = ["validate_dataset_file"]
