"""Automated Tests: RFM Segmentation, K-Means Clustering, and Profiling."""

import os
import pytest
import pandas as pd

PROCESSED_DIR = os.path.join("data", "processed")


def test_rfm_segments_percentage_sums_to_100():
    """Verify RFM segment percentages sum to 100%."""
    summary_path = os.path.join(PROCESSED_DIR, "rfm_segment_summary.csv")
    df = pd.read_csv(summary_path)
    total_pct = df["patient_share_pct"].sum()
    assert abs(total_pct - 100.0) < 0.5, f"RFM patient share sum {total_pct}% deviates from 100%"


def test_kmeans_minimum_5_percent_cluster_size():
    """CRITICAL REQUIREMENT: Verify every final K-Means cluster meets the 5% minimum threshold."""
    profile_path = os.path.join(PROCESSED_DIR, "segment_profiles.csv")
    df = pd.read_csv(profile_path)
    for _, row in df.iterrows():
        c_name = row["cluster_name"]
        pct = row["patient_share_pct"]
        assert pct >= 5.0, f"Cluster '{c_name}' has {pct:.2f}% size, failing minimum 5% requirement"


def test_at_least_three_kpis_distinguish_segments():
    """CRITICAL REQUIREMENT: Demonstrate meaningful distinctions across at least 3 KPIs."""
    profile_path = os.path.join(PROCESSED_DIR, "segment_profiles.csv")
    df = pd.read_csv(profile_path)
    
    # KPI 1: Monetary Value difference ratio (max / min)
    spend_ratio = df["avg_monetary_inr"].max() / max(1.0, df["avg_monetary_inr"].min())
    assert spend_ratio > 3.0, f"Monetary difference ratio too low: {spend_ratio:.2f}"
    
    # KPI 2: Visit Frequency difference ratio
    freq_ratio = df["avg_visit_frequency"].max() / max(0.1, df["avg_visit_frequency"].min())
    assert freq_ratio > 2.0, f"Frequency difference ratio too low: {freq_ratio:.2f}"
    
    # KPI 3: Inpatient Length of Stay (LOS) difference
    los_diff = df["avg_los_days"].max() - df["avg_los_days"].min()
    assert los_diff > 3.0, f"LOS difference between clusters too small: {los_diff:.2f} days"
    
    # KPI 4: Admission Rate difference
    adm_diff = df["admission_rate_pct"].max() - df["admission_rate_pct"].min()
    assert adm_diff > 15.0, f"Admission rate distinction too small: {adm_diff:.2f}%"


def test_business_friendly_names_assigned():
    """Verify clusters and segments have clear business-friendly names."""
    profile_path = os.path.join(PROCESSED_DIR, "segment_profiles.csv")
    df = pd.read_csv(profile_path)
    assert df["cluster_name"].notna().all(), "Null cluster names found"
    for name in df["cluster_name"]:
        assert len(str(name).strip()) > 5, f"Cluster name too short: {name}"
