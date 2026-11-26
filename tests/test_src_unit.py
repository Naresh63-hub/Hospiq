"""Comprehensive Unit Tests Directly Exercising src/ Modules for Full Test Coverage."""

import os
import pytest
import pandas as pd
import numpy as np

import src.data_cleaner as dc
import src.segmentation_rfm as rfm
import src.clustering_kmeans as km
import src.business_recommendations as br
import src.feature_engineering as fe


# =============================================================================
# 1. DATA CLEANER UNIT TESTS
# =============================================================================

def test_parse_date_robust_formats():
    """Test date parsing handles mixed valid and invalid strings."""
    dates = pd.Series([
        "2025-01-15",
        "15/01/2025",
        "15-01-2025",
        "2025.01.15",
        "2025/01/15",
        "invalid-date",
        None
    ])
    parsed = dc.parse_date_robust(dates)
    assert parsed.iloc[0] == pd.Timestamp("2025-01-15")
    assert parsed.iloc[1] == pd.Timestamp("2025-01-15")
    assert pd.isna(parsed.iloc[5])
    assert pd.isna(parsed.iloc[6])


def test_standardize_diagnosis_mapping():
    """Test diagnosis standardization covers major clinical ICD-10 categories."""
    assert dc.standardize_diagnosis("Acute T2DM with hyperglycemia") == "Type 2 Diabetes Mellitus"
    assert dc.standardize_diagnosis("Hypertension Essential stage 2") == "Essential Hypertension"
    assert dc.standardize_diagnosis("CAD post CABG review") == "Coronary Artery Disease"
    assert dc.standardize_diagnosis("Severe Asthma attack") == "Bronchial Asthma / COPD"
    assert dc.standardize_diagnosis("Acute viral gastroenteritis") == "Gastroenteritis"
    assert dc.standardize_diagnosis("Fever with chills undiagnosed") == "Viral Fever / PUO"
    assert dc.standardize_diagnosis("Chronic Osteoarthritis knee") == "Osteoarthritis"
    assert dc.standardize_diagnosis("CKD stage 3") == "Chronic Kidney Disease"
    assert dc.standardize_diagnosis("Annual routine wellness checkup") == "Routine Health Checkup"
    assert dc.standardize_diagnosis("") == "Unspecified / General Consultation"
    assert dc.standardize_diagnosis(None) == "Unspecified / General Consultation"


def test_clean_patients_data_unit():
    """Test patient cleaning logic on synthetic micro-dataset."""
    raw_p = pd.DataFrame([
        {"patient_id": "P001", "date_of_birth": "1980-05-15", "age": None, "gender": "Male", "city": "Hyderabad", "hospital_id": "H101", "registration_date": "2025-01-01"},
        {"patient_id": "P002", "date_of_birth": None, "age": -5, "gender": "F", "city": "Secunderabad", "hospital_id": "H102", "registration_date": "2025-02-01"},
        {"patient_id": "P003", "date_of_birth": "1995-10-10", "age": 31, "gender": "Female", "city": "Warangal", "hospital_id": "H103", "registration_date": "2025-03-01"},
    ])
    cleaned, metrics = dc.clean_patients_data(raw_p)
    
    assert len(cleaned) == 3
    assert cleaned.loc[cleaned["patient_id"] == "P001", "age_cleaned"].iloc[0] == 46  # (2026-10-31 - 1980-05-15)
    assert cleaned.loc[cleaned["patient_id"] == "P002", "gender_cleaned"].iloc[0] == "Female"


def test_clean_and_validate_billing_unit():
    """Test billing tax rules: double GST, exempt OPD, keying typos, refunds."""
    raw_b = pd.DataFrame([
        # Rule 3: GST double counting (total = base + 2*gst)
        {"transaction_id": "T1", "patient_id": "P1", "service_type": "Pharmacy", "base_amount": 1000.0, "gst": 180.0, "total_amount": 1360.0, "payment_status": "Paid", "hospital_id": "H101", "transaction_date": "2025-03-01"},
        # Rule 4: Exempt OPD GST
        {"transaction_id": "T2", "patient_id": "P1", "service_type": "OPD Consultation", "base_amount": 600.0, "gst": 108.0, "total_amount": 708.0, "payment_status": "Paid", "hospital_id": "H101", "transaction_date": "2025-03-02"},
        # Rule 1: Keying error (₹999,999)
        {"transaction_id": "T3", "patient_id": "P1", "service_type": "Surgery & OT Charges", "base_amount": 999999.0, "gst": 0.0, "total_amount": 999999.0, "payment_status": "Paid", "hospital_id": "H101", "transaction_date": "2025-03-03"},
        # Rule 2: Negative refund
        {"transaction_id": "T4", "patient_id": "P1", "service_type": "Pharmacy", "base_amount": -500.0, "gst": -90.0, "total_amount": -590.0, "payment_status": "Paid", "hospital_id": "H101", "transaction_date": "2025-03-04"},
        # Rule 5: Valid standard
        {"transaction_id": "T5", "patient_id": "P1", "service_type": "Inpatient Bed Charges", "base_amount": 5000.0, "gst": 900.0, "total_amount": 5900.0, "payment_status": "Paid", "hospital_id": "H101", "transaction_date": "2025-03-05"},
    ])
    cleaned, log, metrics = dc.clean_and_validate_billing(raw_b, {"P1"})
    
    assert len(cleaned) == 5
    assert metrics["total_corrections_logged"] == 4
    
    # Check T1: Double counted corrected to 1180
    t1 = cleaned[cleaned["transaction_id"] == "T1"].iloc[0]
    assert t1["corrected_total_amount"] == 1180.0
    assert t1["gst_correction_flag"] == "GST_DOUBLE_COUNTED_CORRECTED"
    
    # Check T2: Exempt OPD corrected to 600
    t2 = cleaned[cleaned["transaction_id"] == "T2"].iloc[0]
    assert t2["corrected_total_amount"] == 600.0
    assert t2["corrected_gst_amount"] == 0.0
    assert t2["gst_correction_flag"] == "EXEMPT_HEALTHCARE_GST_REMOVED"
    
    # Check T3: Outlier corrected to standard surgical reference (48000)
    t3 = cleaned[cleaned["transaction_id"] == "T3"].iloc[0]
    assert t3["corrected_total_amount"] == 48000.0
    assert t3["gst_correction_flag"] == "EXTREME_OUTLIER_KEYING_ERROR"
    
    # Check T4: Negative neutralized to 0
    t4 = cleaned[cleaned["transaction_id"] == "T4"].iloc[0]
    assert t4["corrected_total_amount"] == 0.0
    assert t4["gst_correction_flag"] == "NEGATIVE_REFUND_REMOVED"
    
    # Check T5: Valid preserved
    t5 = cleaned[cleaned["transaction_id"] == "T5"].iloc[0]
    assert t5["corrected_total_amount"] == 5900.0
    assert t5["gst_correction_flag"] == "VALID_TRANSACTION"


# =============================================================================
# 2. SEGMENTATION RFM UNIT TESTS
# =============================================================================

def test_rfm_calculation_and_cohort_assignment():
    """Test RFM scoring and 6-segment assignment logic."""
    np.random.seed(42)
    n = 200
    mock_features = pd.DataFrame({
        "patient_id": [f"P{i:04d}" for i in range(n)],
        "recency_days": np.random.uniform(5, 400, n),
        "visit_frequency": np.random.randint(1, 20, n),
        "monetary_total": np.random.uniform(0, 50000, n)
    })
    
    scored = rfm.calculate_rfm_scores(mock_features)
    assert "r_score" in scored.columns
    assert "f_score" in scored.columns
    assert "m_score" in scored.columns
    
    assigned = rfm.assign_rfm_segments(scored)
    assert "rfm_segment" in assigned.columns
    
    expected_segments = {
        "High-Value Active Patients",
        "Loyal Regular Patients",
        "Growing Patients",
        "Occasional Patients",
        "At-Risk Patients",
        "Low-Engagement Patients"
    }
    assert set(assigned["rfm_segment"].unique()).issubset(expected_segments)


# =============================================================================
# 3. K-MEANS CLUSTERING UNIT TESTS
# =============================================================================

def test_feature_scaling_and_naming():
    """Test log1p skewness handling and semantic cluster naming."""
    features = pd.DataFrame({
        "recency_days": np.random.uniform(1, 300, 100),
        "visit_frequency": np.random.exponential(3, 100) + 1,
        "monetary_total": np.random.exponential(5000, 100),
        "avg_billing_value": np.random.exponential(2000, 100),
        "admission_frequency": np.random.binomial(1, 0.2, 100),
        "avg_length_of_stay": np.random.exponential(2, 100),
        "lab_utilization": np.random.poisson(2, 100),
        "department_diversity": np.random.randint(1, 4, 100),
    })
    
    X_trans, X_scaled, scaler, metrics = km.prepare_clustering_data(features)
    assert X_scaled.shape == (100, 8)
    assert np.allclose(X_scaled.mean(axis=0), 0.0, atol=1e-1)
    
    # Test semantic naming dictionary mapping
    mock_profiles = pd.DataFrame([
        {"cluster_id": 0, "admission_rate_pct": 5.0, "avg_los_days": 0.2, "avg_visit_frequency": 1.5, "avg_monetary_inr": 20000.0, "avg_dept_diversity": 1.2},
        {"cluster_id": 1, "admission_rate_pct": 100.0, "avg_los_days": 12.0, "avg_visit_frequency": 4.5, "avg_monetary_inr": 22000.0, "avg_dept_diversity": 2.5},
        {"cluster_id": 2, "admission_rate_pct": 8.0, "avg_los_days": 0.3, "avg_visit_frequency": 10.0, "avg_monetary_inr": 8000.0, "avg_dept_diversity": 3.1},
        {"cluster_id": 3, "admission_rate_pct": 4.0, "avg_los_days": 0.1, "avg_visit_frequency": 1.5, "avg_monetary_inr": 0.0, "avg_dept_diversity": 1.1},
        {"cluster_id": 4, "admission_rate_pct": 100.0, "avg_los_days": 11.5, "avg_visit_frequency": 4.0, "avg_monetary_inr": 0.0, "avg_dept_diversity": 2.0},
    ])
    name_map = km.assign_semantic_cluster_names(mock_profiles)
    assert isinstance(name_map, dict)
    assert len(name_map) == 5
    assert "Inpatient" in name_map[1]


# =============================================================================
# 4. BUSINESS RECOMMENDATIONS UNIT TESTS
# =============================================================================

def test_business_recommendations_structure():
    """Test business recommendation dataframe contains required operational parameters."""
    df_recs = br.get_recommendations_dataframe()
    assert len(df_recs) == 6
    expected_cols = {
        "segment_id",
        "segment_name",
        "characteristics",
        "business_problem",
        "recommended_action",
        "estimated_cost_inr",
        "expected_benefit_inr",
        "cost_breakdown",
        "benefit_breakdown",
        "measurement_kpi",
        "target_value",
        "implementation_period",
        "clinical_safeguards",
    }
    assert expected_cols.issubset(set(df_recs.columns))
    assert (df_recs["expected_benefit_inr"] > df_recs["estimated_cost_inr"]).all()


# =============================================================================
# 5. FEATURE ENGINEERING UNIT TESTS
# =============================================================================

def test_extract_patient_features_unit():
    """Test non-leaking feature extraction within defined date boundary."""
    p_df = pd.DataFrame([
        {"patient_id": "P001", "hospital_id_cleaned": "H101", "hospital_name_cleaned": "CareElite", "age_cleaned": 45, "gender_cleaned": "Male", "city_cleaned": "Hyderabad"},
        {"patient_id": "P002", "hospital_id_cleaned": "H102", "hospital_name_cleaned": "MetroCare", "age_cleaned": 60, "gender_cleaned": "Female", "city_cleaned": "Secunderabad"},
    ])
    opd_df = pd.DataFrame([
        {"patient_id": "P001", "visit_date_cleaned": pd.Timestamp("2025-03-01"), "department_cleaned": "Cardiology"},
        {"patient_id": "P001", "visit_date_cleaned": pd.Timestamp("2025-06-01"), "department_cleaned": "Endocrinology"},
        {"patient_id": "P002", "visit_date_cleaned": pd.Timestamp("2025-02-15"), "department_cleaned": "General Medicine"},
        # Outside window visit
        {"patient_id": "P001", "visit_date_cleaned": pd.Timestamp("2026-11-15"), "department_cleaned": "Cardiology"},
    ])
    adm_df = pd.DataFrame([
        {"patient_id": "P001", "admission_date_cleaned": pd.Timestamp("2025-04-01"), "discharge_date_cleaned": pd.Timestamp("2025-04-05"), "length_of_stay_cleaned": 4, "readmission_indicator": 0},
    ])
    lab_df = pd.DataFrame([
        {"patient_id": "P001", "test_date_cleaned": pd.Timestamp("2025-03-02")},
        {"patient_id": "P002", "test_date_cleaned": pd.Timestamp("2025-02-16")},
    ])
    bill_df = pd.DataFrame([
        {"patient_id": "P001", "transaction_date_cleaned": pd.Timestamp("2025-03-01"), "corrected_total_amount": 1500.0},
        {"patient_id": "P001", "transaction_date_cleaned": pd.Timestamp("2025-04-05"), "corrected_total_amount": 25000.0},
        {"patient_id": "P002", "transaction_date_cleaned": pd.Timestamp("2025-02-15"), "corrected_total_amount": 800.0},
    ])
    
    start_date = pd.Timestamp("2025-01-01")
    cutoff_date = pd.Timestamp("2025-10-31")
    
    feats = fe.extract_patient_features(p_df, opd_df, adm_df, lab_df, bill_df, start_date, cutoff_date, "test_window")
    
    assert len(feats) == 2
    assert "recency_days" in feats.columns
    assert "visit_frequency" in feats.columns
    assert "monetary_total" in feats.columns
    assert "admission_frequency" in feats.columns
    assert "department_diversity" in feats.columns
    
    # Assert outside window interaction was excluded
    p1 = feats[feats["patient_id"] == "P001"].iloc[0]
    assert p1["opd_visits"] == 2  # 3rd visit on 2026-11-15 was outside window
    assert p1["admission_frequency"] == 1
    assert p1["monetary_total"] == 26500.0
    assert p1["department_diversity"] == 2


# =============================================================================
# 6. ADVANCED ML & STATISTICAL HYPOTHESIS TESTS
# =============================================================================

def test_statistical_hypothesis_tests_unit():
    """Test ANOVA and Kruskal-Wallis hypothesis testing across patient clusters."""
    mock_df = pd.DataFrame({
        "cluster_id": [0, 0, 1, 1, 2, 2],
        "avg_length_of_stay": [0.1, 0.2, 12.0, 13.0, 0.5, 0.4],
        "monetary_total": [20000.0, 22000.0, 25000.0, 24000.0, 1000.0, 1200.0],
        "visit_frequency": [1.5, 2.0, 4.0, 4.5, 1.0, 1.2],
        "admission_frequency": [0, 0, 1, 1, 0, 0]
    })
    res = km.compute_statistical_hypothesis_tests(mock_df)
    assert len(res) == 4
    assert "anova_f_stat" in res.columns
    assert "kruskal_h_stat" in res.columns
    assert "statistical_significance" in res.columns
    assert (res["null_hypothesis_rejected"] == True).all()


def test_pca_projection_unit():
    """Test PCA 2D projection and coordinate extraction."""
    X_scaled = np.random.randn(50, 8)
    labels = np.random.choice([0, 1, 2, 3, 4], size=50)
    names_map = {0: "C0", 1: "C1", 2: "C2", 3: "C3", 4: "C4"}
    pca_df, chart_path = km.compute_pca_projection(X_scaled, labels, names_map)
    assert len(pca_df) == 50
    assert "PC1" in pca_df.columns
    assert "PC2" in pca_df.columns
    assert os.path.exists(chart_path)


def test_compute_financial_scenarios_unit():
    """Test Bear, Base, and Bull financial scenario modeling."""
    scenarios = br.compute_financial_scenarios()
    assert len(scenarios) == 3
    assert set(scenarios["scenario"].tolist()) == {
        "Bear Case (Conservative)",
        "Base Case (Expected)",
        "Bull Case (Optimistic)"
    }
    assert (scenarios["expected_benefit_inr"] > scenarios["total_cost_inr"]).all()
    assert scenarios.loc[scenarios["scenario"] == "Bull Case (Optimistic)", "roi_pct"].iloc[0] > \
           scenarios.loc[scenarios["scenario"] == "Base Case (Expected)", "roi_pct"].iloc[0]

