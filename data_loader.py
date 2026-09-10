"""
data_loader.py
===============
Responsible ONLY for reading the raw CSV file into memory. Deliberately
contains no cleaning, transformation, or validation logic -- that belongs
in preprocessing.py. Keeping ingestion separate from cleaning makes the
pipeline auditable: we always know exactly what "raw" looked like.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import pandas as pd

from src.config import RAW_DATA_PATH

logger = logging.getLogger(__name__)


def load_raw_data(path: Union[str, Path] = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load the raw UAC CSV file exactly as it exists on disk.

    Parameters
    ----------
    path : str or Path
        Location of the raw CSV file. Defaults to the project's canonical
        raw data path.

    Returns
    -------
    pd.DataFrame
        The unmodified raw dataframe (original column headers, original
        string formatting such as comma-separated numbers, and any fully
        blank trailing rows present in the source file).

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the given path.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {path}")

    logger.info("Loading raw data from %s", path)
    df = pd.read_csv(path, dtype=str)  # read everything as string first; typing is preprocessing's job
    logger.info("Raw data loaded: %d rows, %d columns", df.shape[0], df.shape[1])
    return df


def inspect_raw_data(df: pd.DataFrame) -> dict:
    """
    Produce a lightweight data-quality snapshot of a raw dataframe without
    mutating it. Used for the initial inspection step required before any
    cleaning happens.

    Returns
    -------
    dict
        Summary statistics: shape, dtypes, missing counts, duplicate row
        count, and duplicate value counts per column.
    """
    summary = {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "fully_blank_rows": int(df.isnull().all(axis=1).sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }
    return summary
