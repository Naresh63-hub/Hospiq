"""HospitalIQ End-to-End Analytics Pipeline Orchestrator.

Sequentially executes:
1. Synthetic Data Generation (~500,000 records across 4 Hyderabad hospitals)
2. Data Cleaning, GST Correction, and Validation
3. Exploratory Data Analysis (16 Publication-grade Visualizations)
4. Patient-level Behavioral Feature Engineering (Full, Period 1, Period 2)
5. RFM Patient Segmentation & Scoring
6. K-Means Machine Learning Clustering & Profiling
7. Longitudinal Segment Stability & Migration Analysis
8. Strategic Business Recommendations
9. SQLite Local Database Export (hospitaliq.db)
"""

import os
import time
import sqlite3
import pandas as pd

from src.data_generator import generate_and_save_all
from src.data_cleaner import clean_all_datasets
from src.eda_analysis import run_full_eda
from src.feature_engineering import engineer_all_features
from src.segmentation_rfm import run_rfm_segmentation
from src.clustering_kmeans import run_kmeans_clustering
from src.stability_analysis import analyze_segment_stability
from src.business_recommendations import save_recommendations_report


def export_to_sqlite(cleaned_dir: str, processed_dir: str, db_path: str):
    """Export cleaned and processed data into SQLite for reproducible SQL queries."""
    print("=" * 60)
    print(f"Exporting HospitalIQ data to SQLite Database: {db_path}...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    tables_to_export = [
        ("patients_clean", os.path.join(cleaned_dir, "patients_cleaned.csv")),
        ("opd_visits_clean", os.path.join(cleaned_dir, "opd_visits_cleaned.csv")),
        ("admissions_clean", os.path.join(cleaned_dir, "admissions_cleaned.csv")),
        ("lab_tests_clean", os.path.join(cleaned_dir, "lab_tests_cleaned.csv")),
        ("billing_clean", os.path.join(cleaned_dir, "billing_cleaned.csv")),
        ("billing_correction_log", os.path.join(cleaned_dir, "billing_correction_log.csv")),
        ("patient_features_full", os.path.join(processed_dir, "patient_features_full.csv")),
        ("rfm_segmentation", os.path.join(processed_dir, "rfm_segmentation.csv")),
        ("kmeans_clusters", os.path.join(processed_dir, "kmeans_clusters.csv")),
        ("segment_profiles", os.path.join(processed_dir, "segment_profiles.csv")),
        ("segment_migration", os.path.join(processed_dir, "segment_migration_matrix.csv")),
    ]
    
    for table_name, csv_path in tables_to_export:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, low_memory=False)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"  Exported table '{table_name}': {len(df):,} rows")
            
    conn.commit()
    conn.close()
    print("SQLite Database Export Complete.")
    print("=" * 60)


def run_full_pipeline():
    """Execute complete HospitalIQ pipeline from end to end."""
    start_time = time.time()
    print("\n" + "#" * 70)
    print("  HOSPITALIQ HEALTHCARE ANALYTICS & SEGMENTATION PIPELINE")
    print("  Hyderabad Healthcare Network Patient Segmentation Study")
    print("#" * 70 + "\n")
    
    raw_dir = os.path.join("data", "raw")
    cleaned_dir = os.path.join("data", "cleaned")
    processed_dir = os.path.join("data", "processed")
    db_path = os.path.join("data", "database", "hospitaliq.db")
    
    # Phase 2: Dataset Generation
    patients_raw_path = os.path.join(raw_dir, "patients.csv")
    if not os.path.exists(patients_raw_path):
        gen_metrics = generate_and_save_all(raw_dir)
    else:
        print("Raw datasets exist on disk. Using existing verified raw records.")
        gen_metrics = {"total": 501600}
    
    # Phase 3: Data Cleaning & Validation (Always re-run to ensure fresh audit logs)
    clean_metrics = clean_all_datasets(raw_dir, cleaned_dir)
    
    # Phase 4: Exploratory Data Analysis (16 Visualizations)
    eda_metrics = run_full_eda(cleaned_dir)
    
    # Phase 5: Feature Engineering
    fe_metrics = engineer_all_features(cleaned_dir, processed_dir)
    
    # Phase 6: RFM Segmentation
    full_feats_path = os.path.join(processed_dir, "patient_features_full.csv")
    rfm_path = os.path.join(processed_dir, "rfm_segmentation.csv")
    df_rfm, rfm_summary = run_rfm_segmentation(full_feats_path, rfm_path)
    
    # Phase 7 & 8: K-Means Clustering & Segment Profiling
    kmeans_path = os.path.join(processed_dir, "kmeans_clusters.csv")
    df_km, km_profile = run_kmeans_clustering(full_feats_path, rfm_path, kmeans_path)
    
    # Phase 9: Business Recommendations
    rec_path = os.path.join(processed_dir, "business_recommendations.csv")
    save_recommendations_report(rec_path)
    
    # Phase 10: Segment Stability Analysis
    p1_path = os.path.join(processed_dir, "patient_features_period1.csv")
    p2_path = os.path.join(processed_dir, "patient_features_period2.csv")
    mig_matrix, stab_metrics = analyze_segment_stability(p1_path, p2_path, processed_dir)
    
    # SQLite Database Export
    export_to_sqlite(cleaned_dir, processed_dir, db_path)
    
    elapsed = time.time() - start_time
    print("\n" + "#" * 70)
    print(f"  HOSPITALIQ PIPELINE EXECUTED SUCCESSFULLY IN {elapsed:.1f} SECONDS")
    print(f"  Total Raw Records:        {gen_metrics['total']:,}")
    print(f"  Patients Cleaned:         {clean_metrics['patients']['final_rows']:,}")
    print(f"  Billing Transactions:     {clean_metrics['billing']['final_rows']:,}")
    print(f"  GST Corrections Logged:   {clean_metrics['billing']['total_corrections_logged']:,}")
    print(f"  Net Corrected Revenue:    ₹{clean_metrics['billing']['corrected_total_revenue_inr']:,.2f}")
    print(f"  RFM Cohorts Formed:       {len(rfm_summary)}")
    print(f"  K-Means Clusters:         {len(km_profile)}")
    print(f"  Stability Cohort ARI:     {stab_metrics['adjusted_rand_index']:.4f}")
    print(f"  SQLite Database:          {db_path}")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    run_full_pipeline()
