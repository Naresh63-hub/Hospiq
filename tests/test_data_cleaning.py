"""Automated Tests: Data Cleaning, Standardization, and Validation."""

import os
import pytest
import pandas as pd

CLEANED_DIR = os.path.join("data", "cleaned")


def test_no_missing_age_in_cleaned_patients():
    """Verify missing age values are derived from DOB without missing values remaining."""
    p_df = pd.read_csv(os.path.join(CLEANED_DIR, "patients_cleaned.csv"), low_memory=False)
    assert p_df["age_cleaned"].isna().sum() == 0, "Cleaned patients table has unresolved missing ages"
    assert (p_df["age_cleaned"] < 0).sum() == 0, "Cleaned patients table has negative ages"
    assert (p_df["age_cleaned"] > 115).sum() == 0, "Cleaned patients table has unrealistic ages >115"


def test_referential_integrity():
    """Verify all patient_ids in OPD, Admissions, Lab, and Billing exist in Patients master."""
    p_df = pd.read_csv(os.path.join(CLEANED_DIR, "patients_cleaned.csv"), usecols=["patient_id"])
    valid_pids = set(p_df["patient_id"])
    
    opd_df = pd.read_csv(os.path.join(CLEANED_DIR, "opd_visits_cleaned.csv"), usecols=["patient_id"])
    adm_df = pd.read_csv(os.path.join(CLEANED_DIR, "admissions_cleaned.csv"), usecols=["patient_id"])
    lab_df = pd.read_csv(os.path.join(CLEANED_DIR, "lab_tests_cleaned.csv"), usecols=["patient_id"])
    bill_df = pd.read_csv(os.path.join(CLEANED_DIR, "billing_cleaned.csv"), usecols=["patient_id"])
    
    assert set(opd_df["patient_id"]).issubset(valid_pids), "OPD contains orphan patient IDs"
    assert set(adm_df["patient_id"]).issubset(valid_pids), "Admissions contains orphan patient IDs"
    assert set(lab_df["patient_id"]).issubset(valid_pids), "Lab tests contains orphan patient IDs"
    assert set(bill_df["patient_id"]).issubset(valid_pids), "Billing contains orphan patient IDs"


def test_no_invalid_admission_dates():
    """Verify no discharge date precedes admission date and no negative length of stay."""
    adm_df = pd.read_csv(os.path.join(CLEANED_DIR, "admissions_cleaned.csv"), parse_dates=["admission_date_cleaned", "discharge_date_cleaned"], low_memory=False)
    assert (adm_df["discharge_date_cleaned"] < adm_df["admission_date_cleaned"]).sum() == 0, "Discharge precedes admission date"
    assert (adm_df["length_of_stay_cleaned"] <= 0).sum() == 0, "Zero or negative length of stay in cleaned admissions"


def test_diagnosis_standardization():
    """Verify inconsistent free-text diagnoses are standardized to clinical categories."""
    opd_df = pd.read_csv(os.path.join(CLEANED_DIR, "opd_visits_cleaned.csv"), usecols=["diagnosis_cleaned"])
    assert opd_df["diagnosis_cleaned"].isna().sum() == 0, "Missing diagnoses in cleaned OPD"
    
    # Check that common clinical categories are present
    diag_set = set(opd_df["diagnosis_cleaned"].unique())
    assert "Type 2 Diabetes Mellitus" in diag_set
    assert "Essential Hypertension" in diag_set
    assert "Coronary Artery Disease" in diag_set
