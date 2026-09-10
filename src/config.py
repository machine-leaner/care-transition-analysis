"""
config.py
=========
Central configuration for the UAC Care Transition Efficiency & Placement
Outcome Analytics project.

Holds raw-column name mappings, canonical (cleaned) column names, file
paths, and project-defined analytical constants. Keeping these in one
place avoids magic strings scattered across the pipeline and makes the
"project-defined" nature of thresholds/scores auditable in a single file.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "HHS_Unaccompanied_Alien_Children_Program.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "uac_processed.csv"
PROCESSED_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "uac_features.csv"

# ---------------------------------------------------------------------------
# Raw -> canonical column mapping
# ---------------------------------------------------------------------------
# The raw HHS export uses long, human-readable headers (one with a trailing
# footnote marker "*"). We map these to short, stable, snake_case names used
# throughout the codebase so downstream code never depends on the exact raw
# header text.
RAW_COLUMNS = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "apprehensions",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "transfers",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "discharges",
}

DATE_COL = "date"
APPREHENSIONS_COL = "apprehensions"
CBP_CUSTODY_COL = "cbp_custody"
TRANSFERS_COL = "transfers"
HHS_CARE_COL = "hhs_care"
DISCHARGES_COL = "discharges"

RAW_DATE_FORMAT = "%B %d, %Y"  # e.g. "December 21, 2025"

NUMERIC_COLS = [APPREHENSIONS_COL, CBP_CUSTODY_COL, TRANSFERS_COL, HHS_CARE_COL, DISCHARGES_COL]

# ---------------------------------------------------------------------------
# Rolling windows (days) used for feature engineering / smoothing
# ---------------------------------------------------------------------------
ROLLING_WINDOWS = [7, 14, 30]

# ---------------------------------------------------------------------------
# PROJECT-DEFINED analytical thresholds (NOT official HHS/CBP thresholds).
# These are configurable defaults for the rule-based bottleneck detector.
# ---------------------------------------------------------------------------
DEFAULT_TRANSFER_EFFICIENCY_THRESHOLD = 60.0   # percent
# NOTE ON SCALE: Discharge Effectiveness = Discharges / HHS Care * 100 compares
# a daily FLOW (discharges that day) to a much larger population STOCK
# (children currently in HHS care), so it is structurally a small percentage
# in this dataset (observed median ~2.6%, max ~6.6% -- see docs/03_EDA_Findings.md).
# A generic 20% threshold would flag effectively the entire dataset as a
# "bottleneck," which is not a meaningful finding. The default below is
# calibrated to this dataset's own distribution (approx. its 25th percentile)
# and, like all thresholds in this module, is project-defined and adjustable
# via the dashboard controls -- NOT an official government benchmark.
DEFAULT_DISCHARGE_EFFECTIVENESS_THRESHOLD = 1.0  # percent
DEFAULT_SUSTAINED_DAYS = 7  # consecutive days below threshold to count as a "bottleneck period"

# Anomaly detection
ISOLATION_FOREST_CONTAMINATION = 0.03  # ~3% of observations flagged, project-defined
ROLLING_ZSCORE_WINDOW = 14
ROLLING_ZSCORE_THRESHOLD = 3.0

# Outcome Stability Score normalization bounds (project-defined, documented in docs/04_KPI_Definitions.md)
STABILITY_SCORE_MIN_CV = 0.0   # coefficient of variation mapped to score of 100
STABILITY_SCORE_MAX_CV = 1.0   # coefficient of variation mapped to score of 0 (clipped)
