"""Automated Tests: Synthetic Dataset Generation & Referential Integrity."""

import os
import pytest
import pandas as pd

RAW_DIR = os.path.join("data", "raw")


def test_raw_files_exist():
    """Verify all 5 raw dataset files exist on disk."""
    expected_files = ["patients.csv", "opd_visits.csv", "admissions.csv", "lab_tests.csv", "billing.csv"]
    for f in expected_files:
        path = os.path.join(RAW_DIR, f)
        assert os.path.exists(path), f"Raw file {f} missing at {path}"


def test_dataset_size_approximately_500k():
    """Verify raw dataset has approximately 500,000 records across 4 hospitals."""
    p_df = pd.read_csv(os.path.join(RAW_DIR, "patients.csv"), usecols=["patient_id"])
    opd_df = pd.read_csv(os.path.join(RAW_DIR, "opd_visits.csv"), usecols=["visit_id"])
    adm_df = pd.read_csv(os.path.join(RAW_DIR, "admissions.csv"), usecols=["admission_id"])
    lab_df = pd.read_csv(os.path.join(RAW_DIR, "lab_tests.csv"), usecols=["test_id"])
    bill_df = pd.read_csv(os.path.join(RAW_DIR, "billing.csv"), usecols=["transaction_id"])
    
    total_records = len(p_df) + len(opd_df) + len(adm_df) + len(lab_df) + len(bill_df)
    assert 480000 <= total_records <= 530000, f"Expected ~500k records, got {total_records:,}"


def test_synthetic_data_label_present():
    """Verify dataset is clearly labeled as synthetic."""
    p_df = pd.read_csv(os.path.join(RAW_DIR, "patients.csv"), nrows=50)
    assert "dataset_type" in p_df.columns or "is_synthetic" in p_df.columns or (p_df["dataset_type"].iloc[0] == "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY")


def test_four_hospitals_represented():
    """Verify records represent all four designated Hyderabad hospitals."""
    p_df = pd.read_csv(os.path.join(RAW_DIR, "patients.csv"), usecols=["hospital_id"])
    hosps = set(p_df["hospital_id"].dropna().unique())
    assert {"H101", "H102", "H103", "H104"}.issubset(hosps), f"Expected 4 hospitals, found {hosps}"
