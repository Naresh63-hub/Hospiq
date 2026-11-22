"""Automated Tests: Critical Billing Accuracy & Transaction-Level GST Validation."""

import os
import pytest
import pandas as pd

CLEANED_DIR = os.path.join("data", "cleaned")


def test_no_blind_division_by_fixed_factor():
    """Verify GST correction was performed via transaction rules rather than fixed 1.18 division."""
    bill_df = pd.read_csv(os.path.join(CLEANED_DIR, "billing_cleaned.csv"), low_memory=False)
    
    # Calculate what blind division by 1.18 would yield
    blind_quotient = bill_df["total_amount"] / 1.18
    actual_corrected = bill_df["corrected_total_amount"]
    
    # Assert that actual corrected total is NOT identical to blind division
    diff = (blind_quotient - actual_corrected).abs()
    assert (diff > 1.0).sum() > len(bill_df) * 0.50, "Billing values match blind division by 1.18; rule-based logic required"


def test_no_negative_billing_values_in_corrected():
    """Verify all negative billing amounts have been neutralized / handled in corrected totals."""
    bill_df = pd.read_csv(os.path.join(CLEANED_DIR, "billing_cleaned.csv"), low_memory=False)
    assert (bill_df["corrected_total_amount"] < 0).sum() == 0, "Negative billing amounts in corrected totals"
    assert (bill_df["corrected_base_amount"] < 0).sum() == 0, "Negative base amounts in corrected base"


def test_billing_correction_log_exists_and_populated():
    """Verify billing correction log is maintained and tracks before-and-after values."""
    log_path = os.path.join(CLEANED_DIR, "billing_correction_log.csv")
    assert os.path.exists(log_path), f"Correction log {log_path} missing"
    
    log_df = pd.read_csv(log_path, low_memory=False)
    assert len(log_df) > 1000, f"Expected >1,000 logged corrections, found {len(log_df):,}"
    
    required_cols = ["transaction_id", "patient_id", "orig_total", "corrected_total", "flag", "reason"]
    for col in required_cols:
        assert col in log_df.columns, f"Required log column {col} missing"


def test_revenue_reconciliation():
    """Verify total corrected revenue reconciles with individual corrected transactions."""
    bill_df = pd.read_csv(os.path.join(CLEANED_DIR, "billing_cleaned.csv"), low_memory=False)
    computed_sum = bill_df["corrected_total_amount"].sum()
    component_sum = bill_df["corrected_base_amount"].sum() + bill_df["corrected_gst_amount"].sum()
    
    assert abs(computed_sum - component_sum) < 5.0, f"Reconciliation discrepancy: {computed_sum} vs {component_sum}"
    assert computed_sum > 500000000.0, f"Total corrected revenue unexpectedly low: ₹{computed_sum:,.2f}"
