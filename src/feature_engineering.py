"""HospitalIQ Patient-Level Feature Engineering Engine.

Extracts behavioral, clinical, and financial features without data leakage
for both the full study period and two split periods for stability analysis.
"""

import os
import numpy as np
import pandas as pd


def extract_patient_features(
    patients: pd.DataFrame,
    opd: pd.DataFrame,
    admissions: pd.DataFrame,
    lab_tests: pd.DataFrame,
    billing: pd.DataFrame,
    start_date: pd.Timestamp,
    cutoff_date: pd.Timestamp,
    period_name: str = "full"
) -> pd.DataFrame:
    """Extract patient-level features strictly within [start_date, cutoff_date]."""
    print(f"Extracting patient features for period: {period_name} ({start_date.strftime('%Y-%m-%d')} to {cutoff_date.strftime('%Y-%m-%d')})...")
    
    # Filter datasets strictly within the observation window to prevent data leakage
    opd_win = opd[(opd["visit_date_cleaned"] >= start_date) & (opd["visit_date_cleaned"] <= cutoff_date)].copy()
    adm_win = admissions[(admissions["admission_date_cleaned"] >= start_date) & (admissions["admission_date_cleaned"] <= cutoff_date)].copy()
    lab_win = lab_tests[(lab_tests["test_date_cleaned"] >= start_date) & (lab_tests["test_date_cleaned"] <= cutoff_date)].copy()
    bill_win = billing[(billing["transaction_date_cleaned"] >= start_date) & (billing["transaction_date_cleaned"] <= cutoff_date)].copy()
    
    # 1. Base active patients in this window (patients who had any OPD, Admission, Lab, or Billing)
    active_pids = set(opd_win["patient_id"]).union(
        set(adm_win["patient_id"])
    ).union(
        set(lab_win["patient_id"])
    ).union(
        set(bill_win["patient_id"])
    )
    
    base_df = patients[patients["patient_id"].isin(active_pids)].copy()
    if base_df.empty:
        print("Warning: No active patients in window.")
        return pd.DataFrame()
        
    pids = base_df["patient_id"]
    
    # 2. Recency: Days since last interaction (min days between cutoff and latest contact date)
    # Contact dates can come from OPD, Admission, or Lab
    opd_dates = opd_win.groupby("patient_id")["visit_date_cleaned"].max()
    adm_dates = adm_win.groupby("patient_id")["admission_date_cleaned"].max()
    lab_dates = lab_win.groupby("patient_id")["test_date_cleaned"].max()
    
    dates_df = pd.DataFrame({"patient_id": list(active_pids)}).set_index("patient_id")
    dates_df["latest_opd"] = opd_dates
    dates_df["latest_adm"] = adm_dates
    dates_df["latest_lab"] = lab_dates
    latest_contact = dates_df[["latest_opd", "latest_adm", "latest_lab"]].max(axis=1)
    
    recency_days = (cutoff_date - latest_contact).dt.days.clip(lower=0)
    
    # 3. Frequency: Total OPD visits + Inpatient Admissions
    opd_freq = opd_win.groupby("patient_id").size()
    adm_freq = adm_win.groupby("patient_id").size()
    
    # 4. Monetary: Total corrected billing amount & Transaction Count
    bill_agg = bill_win.groupby("patient_id").agg(
        monetary_total=("corrected_total_amount", "sum"),
        txn_count=("corrected_total_amount", "count")
    )
    
    # 5. Inpatient Clinical Features: Length of stay & Readmissions
    adm_agg = adm_win.groupby("patient_id").agg(
        total_los=("length_of_stay_cleaned", "sum"),
        readmissions=("readmission_indicator", "sum")
    )
    
    # 6. Laboratory Utilization
    lab_freq = lab_win.groupby("patient_id").size()
    
    # 7. Department Diversity: Number of distinct OPD departments visited
    dept_div = opd_win.groupby("patient_id")["department_cleaned"].nunique()
    
    # 8. Visit Growth Rate (H2 vs H1 of the window)
    mid_date = start_date + (cutoff_date - start_date) / 2
    opd_h1 = opd_win[opd_win["visit_date_cleaned"] < mid_date].groupby("patient_id").size()
    opd_h2 = opd_win[opd_win["visit_date_cleaned"] >= mid_date].groupby("patient_id").size()
    
    # 9. Seasonal Visit Behavior: Standard deviation across 4 quarters in window
    # Assign quarter number relative to start date
    opd_win["quarter"] = ((opd_win["visit_date_cleaned"] - start_date).dt.days // 91).clip(lower=0, upper=3)
    q_counts = opd_win.groupby(["patient_id", "quarter"]).size().unstack(fill_value=0)
    # Ensure all 4 quarters exist
    for q in range(4):
        if q not in q_counts.columns:
            q_counts[q] = 0
    seasonal_std = q_counts.std(axis=1)
    
    # 10. Assemble Patient Features Table
    features = pd.DataFrame(index=base_df["patient_id"])
    features["patient_id"] = base_df["patient_id"].values
    features["hospital_id"] = base_df["hospital_id_cleaned"].values
    features["hospital_name"] = base_df["hospital_name_cleaned"].values
    features["age"] = base_df["age_cleaned"].values
    features["gender"] = base_df["gender_cleaned"].values
    features["city"] = base_df["city_cleaned"].values
    
    # Add mapped metrics
    features["recency_days"] = features["patient_id"].map(recency_days).fillna((cutoff_date - start_date).days).astype(int)
    features["opd_visits"] = features["patient_id"].map(opd_freq).fillna(0).astype(int)
    features["admission_frequency"] = features["patient_id"].map(adm_freq).fillna(0).astype(int)
    features["visit_frequency"] = features["opd_visits"] + features["admission_frequency"]
    
    features["monetary_total"] = features["patient_id"].map(bill_agg["monetary_total"]).fillna(0.0).round(2)
    features["transaction_count"] = features["patient_id"].map(bill_agg["txn_count"]).fillna(0).astype(int)
    features["avg_billing_value"] = np.where(features["transaction_count"] > 0, features["monetary_total"] / features["transaction_count"], 0.0).round(2)
    
    features["total_los"] = features["patient_id"].map(adm_agg["total_los"]).fillna(0).astype(int)
    features["avg_length_of_stay"] = np.where(features["admission_frequency"] > 0, features["total_los"] / features["admission_frequency"], 0.0).round(2)
    features["readmission_frequency"] = features["patient_id"].map(adm_agg["readmissions"]).fillna(0).astype(int)
    features["readmission_rate"] = np.where(features["admission_frequency"] > 0, (features["readmission_frequency"] / features["admission_frequency"]) * 100.0, 0.0).round(2)
    
    features["lab_utilization"] = features["patient_id"].map(lab_freq).fillna(0).astype(int)
    features["department_diversity"] = features["patient_id"].map(dept_div).fillna(0).astype(int)
    
    # Growth rate: (H2 - H1) / max(1, H1)
    h1_val = features["patient_id"].map(opd_h1).fillna(0)
    h2_val = features["patient_id"].map(opd_h2).fillna(0)
    features["visit_growth_rate"] = ((h2_val - h1_val) / np.maximum(1, h1_val)).round(2)
    
    features["seasonal_visit_std"] = features["patient_id"].map(seasonal_std).fillna(0.0).round(2)
    features["recent_activity_flag"] = (features["recency_days"] <= 90).astype(int)
    
    features["period"] = period_name
    features.reset_index(drop=True, inplace=True)
    
    print(f"Period '{period_name}' extracted: {len(features):,} active patients.")
    return features


def engineer_all_features(cleaned_dir: str, processed_dir: str) -> dict:
    """Run feature engineering across Full period, Period 1, and Period 2."""
    os.makedirs(processed_dir, exist_ok=True)
    print("=" * 60)
    print("HospitalIQ Feature Engineering Starting...")
    print(f"Reading from: {cleaned_dir}")
    print(f"Saving to: {processed_dir}")
    print("=" * 60)
    
    patients = pd.read_csv(os.path.join(cleaned_dir, "patients_cleaned.csv"), parse_dates=["dob_cleaned", "reg_date_cleaned"], low_memory=False)
    opd = pd.read_csv(os.path.join(cleaned_dir, "opd_visits_cleaned.csv"), parse_dates=["visit_date_cleaned"], low_memory=False)
    admissions = pd.read_csv(os.path.join(cleaned_dir, "admissions_cleaned.csv"), parse_dates=["admission_date_cleaned", "discharge_date_cleaned"], low_memory=False)
    lab_tests = pd.read_csv(os.path.join(cleaned_dir, "lab_tests_cleaned.csv"), parse_dates=["test_date_cleaned"], low_memory=False)
    billing = pd.read_csv(os.path.join(cleaned_dir, "billing_cleaned.csv"), parse_dates=["transaction_date_cleaned"], low_memory=False)
    
    # Define observation periods
    # Full: 2025-01-01 to 2026-10-31 (22 months)
    full_start = pd.to_datetime("2025-01-01")
    full_end = pd.to_datetime("2026-10-31")
    
    # Period 1 (Baseline): 2025-01-01 to 2025-11-30 (11 months)
    p1_start = pd.to_datetime("2025-01-01")
    p1_end = pd.to_datetime("2025-11-30")
    
    # Period 2 (Validation): 2025-12-01 to 2026-10-31 (11 months)
    p2_start = pd.to_datetime("2025-12-01")
    p2_end = pd.to_datetime("2026-10-31")
    
    # 1. Full period
    df_full = extract_patient_features(patients, opd, admissions, lab_tests, billing, full_start, full_end, "full")
    full_path = os.path.join(processed_dir, "patient_features_full.csv")
    df_full.to_csv(full_path, index=False)
    
    # 2. Period 1
    df_p1 = extract_patient_features(patients, opd, admissions, lab_tests, billing, p1_start, p1_end, "period1")
    p1_path = os.path.join(processed_dir, "patient_features_period1.csv")
    df_p1.to_csv(p1_path, index=False)
    
    # 3. Period 2
    df_p2 = extract_patient_features(patients, opd, admissions, lab_tests, billing, p2_start, p2_end, "period2")
    p2_path = os.path.join(processed_dir, "patient_features_period2.csv")
    df_p2.to_csv(p2_path, index=False)
    
    print("=" * 60)
    print("FEATURE ENGINEERING COMPLETE")
    print(f"Full Period Features:    {len(df_full):,} patients saved to {full_path}")
    print(f"Period 1 Features:       {len(df_p1):,} patients saved to {p1_path}")
    print(f"Period 2 Features:       {len(df_p2):,} patients saved to {p2_path}")
    print("=" * 60)
    
    return {
        "full_count": len(df_full),
        "period1_count": len(df_p1),
        "period2_count": len(df_p2),
    }


if __name__ == "__main__":
    c_dir = os.path.join("data", "cleaned")
    p_dir = os.path.join("data", "processed")
    engineer_all_features(c_dir, p_dir)
