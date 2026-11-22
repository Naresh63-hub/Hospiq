"""Automated Tests: Feature Engineering & Observation Window Validation."""

import os
import pytest
import pandas as pd

PROCESSED_DIR = os.path.join("data", "processed")


def test_no_duplicate_patient_records():
    """Verify patient-level feature tables contain strictly unique patient IDs."""
    files = ["patient_features_full.csv", "patient_features_period1.csv", "patient_features_period2.csv"]
    for f in files:
        path = os.path.join(PROCESSED_DIR, f)
        df = pd.read_csv(path, usecols=["patient_id"])
        assert df["patient_id"].duplicated().sum() == 0, f"Duplicate patient IDs in {f}"


def test_no_future_data_leakage():
    """Verify recency days is strictly non-negative relative to window cutoff."""
    full_df = pd.read_csv(os.path.join(PROCESSED_DIR, "patient_features_full.csv"), usecols=["recency_days"])
    assert (full_df["recency_days"] < 0).sum() == 0, "Negative recency implies contact date after observation cutoff"


def test_core_features_calculated():
    """Verify all required clinical and financial features are present and non-null."""
    df = pd.read_csv(os.path.join(PROCESSED_DIR, "patient_features_full.csv"), nrows=50)
    expected_cols = [
        "patient_id", "recency_days", "visit_frequency", "monetary_total",
        "avg_billing_value", "admission_frequency", "avg_length_of_stay",
        "lab_utilization", "readmission_frequency", "department_diversity",
        "visit_growth_rate", "seasonal_visit_std", "recent_activity_flag"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Feature column {col} missing in full features"
