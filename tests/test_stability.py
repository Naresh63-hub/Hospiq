"""Automated Tests: Longitudinal Segment Stability & Patient Migration."""

import os
import pytest
import pandas as pd

PROCESSED_DIR = os.path.join("data", "processed")


def test_migration_matrix_exists_and_rows_sum_to_100():
    """Verify segment migration matrix exists and each row sums to 100%."""
    matrix_path = os.path.join(PROCESSED_DIR, "segment_migration_matrix.csv")
    assert os.path.exists(matrix_path), f"Migration matrix {matrix_path} missing"
    
    matrix_df = pd.read_csv(matrix_path, index_col=0)
    assert not matrix_df.empty, "Migration matrix is empty"
    
    row_sums = matrix_df.sum(axis=1)
    for seg, r_sum in row_sums.items():
        assert abs(r_sum - 100.0) < 1.0, f"Row '{seg}' sum {r_sum}% deviates from 100%"


def test_stability_metrics_reconcile():
    """Verify retention + migration equals 100%."""
    metrics_path = os.path.join(PROCESSED_DIR, "segment_stability_metrics.csv")
    assert os.path.exists(metrics_path), f"Stability metrics file {metrics_path} missing"
    
    df = pd.read_csv(metrics_path).set_index("Metric")
    ret_str = df.loc["Overall Segment Retention Rate", "Value"].replace("%", "")
    mig_str = df.loc["Overall Migration Rate", "Value"].replace("%", "")
    
    ret_val = float(ret_str)
    mig_val = float(mig_str)
    
    assert abs((ret_val + mig_val) - 100.0) < 0.2, f"Retention ({ret_val}) + Migration ({mig_val}) != 100%"
    assert 10.0 <= ret_val <= 90.0, f"Unrealistic retention rate: {ret_val}%"
