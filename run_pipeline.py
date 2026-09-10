"""
run_pipeline.py
================
End-to-end pipeline runner:
  Raw CSV -> Validation -> Cleaning -> Transformation -> Feature Engineering
  -> Processed CSV outputs (data/processed/)

Run with: python run_pipeline.py
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_loader import load_raw_data, inspect_raw_data
from src.preprocessing import run_preprocessing_pipeline
from src.feature_engineering import run_feature_engineering
from src.config import PROCESSED_DATA_PATH, PROCESSED_FEATURES_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_pipeline")


def main():
    logger.info("=== STEP 1: Load raw data ===")
    raw_df = load_raw_data()
    raw_summary = inspect_raw_data(raw_df)
    logger.info("Raw data summary: %s", {k: v for k, v in raw_summary.items() if k != "dtypes"})

    logger.info("=== STEP 2-4: Validate, clean, transform ===")
    clean_df, report = run_preprocessing_pipeline(raw_df)
    logger.info("Preprocessing report (shapes): initial=%s after_blank_removal=%s after_dedup=%s",
                report["initial_shape"], report["shape_after_blank_row_removal"],
                report["shape_after_deduplication"])
    logger.info("Numeric validation: %s", report["numeric_validation"])

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_DATA_PATH, index=False)
    logger.info("Saved cleaned data to %s (%d rows)", PROCESSED_DATA_PATH, len(clean_df))

    logger.info("=== STEP 5: Feature engineering ===")
    features_df = run_feature_engineering(clean_df)
    features_df.to_csv(PROCESSED_FEATURES_PATH, index=False)
    logger.info("Saved feature-engineered data to %s (%d rows, %d cols)",
                PROCESSED_FEATURES_PATH, features_df.shape[0], features_df.shape[1])

    logger.info("Pipeline completed successfully.")
    return features_df


if __name__ == "__main__":
    main()
