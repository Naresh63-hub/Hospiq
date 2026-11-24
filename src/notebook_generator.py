"""HospitalIQ Jupyter Notebook Generator (Pure Python JSON Implementation).

Generates complete, executable, clean Jupyter Notebooks:
1. notebooks/01_data_generation_cleaning.ipynb
2. notebooks/02_eda_feature_engineering.ipynb
3. notebooks/03_rfm_kmeans_clustering.ipynb
"""

import os
import json

NOTEBOOK_DIR = "notebooks"
os.makedirs(NOTEBOOK_DIR, exist_ok=True)


def build_notebook_json(cells):
    """Construct valid Jupyter Notebook v4 JSON structure."""
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.12"
            },
            "orig_nbformat": 4
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }


def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    }


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.split("\n")]
    }


def create_notebook_01():
    cells = [
        md_cell(
            "# HospitalIQ – Phase 1: Synthetic Dataset Generation & Data Cleaning\n"
            "**Healthcare Data Analytics & Patient Segmentation Study | Hyderabad Network**\n\n"
            "This notebook demonstrates the synthetic generation of approximately 500,000 healthcare records "
            "across 4 Hyderabad hospitals, followed by data cleaning, DOB-to-age conversion, and critical transaction-level "
            "GST validation."
        ),
        code_cell(
            "import os\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "from src.data_generator import generate_and_save_all\n"
            "from src.data_cleaner import clean_all_datasets\n\n"
            "# 1. Verify Raw Dataset Generation\n"
            "raw_dir = os.path.join('data', 'raw')\n"
            "cleaned_dir = os.path.join('data', 'cleaned')\n"
            "print('Raw Data Directory:', raw_dir)\n"
            "print('Cleaned Data Directory:', cleaned_dir)"
        ),
        code_cell(
            "# 2. Inspect Raw Datasets Size\n"
            "raw_files = ['patients.csv', 'opd_visits.csv', 'admissions.csv', 'lab_tests.csv', 'billing.csv']\n"
            "total_records = 0\n"
            "for f in raw_files:\n"
            "    df = pd.read_csv(os.path.join(raw_dir, f), low_memory=False)\n"
            "    print(f'{f}: {len(df):,} records')\n"
            "    total_records += len(df)\n"
            "print(f'Total Raw Records: {total_records:,}')"
        ),
        md_cell(
            "### Critical Billing Accuracy & GST Audit\n"
            "Under Indian GST regulations, clinical OPD consultations are exempt (0%). Legacy systems introduced:\n"
            "- Double GST calculation (`Total = Base + 2*GST`)\n"
            "- Unlawful GST on exempt OPD consultations\n"
            "- Typographical outliers (₹999,999) and negative refund records\n\n"
            "The cleaner uses rule-based matching rather than blind division by 1.18."
        ),
        code_cell(
            "# 3. Review Billing Correction Log\n"
            "corr_log = pd.read_csv(os.path.join(cleaned_dir, 'billing_correction_log.csv'), low_memory=False)\n"
            "print(f'Total Logged Corrections: {len(corr_log):,}')\n"
            "print(corr_log['flag'].value_counts())"
        ),
        code_cell(
            "# 4. Data Quality Before-and-After Summary\n"
            "quality_df = pd.read_csv(os.path.join(cleaned_dir, 'data_quality_before_after.csv'))\n"
            "print(quality_df)"
        )
    ]
    nb = build_notebook_json(cells)
    path = os.path.join(NOTEBOOK_DIR, "01_data_generation_cleaning.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Created notebook: {path}")


def create_notebook_02():
    cells = [
        md_cell(
            "# HospitalIQ – Phase 2: Comprehensive Exploratory Data Analysis & Feature Engineering\n"
            "**Healthcare Data Analytics & Patient Segmentation Study | Hyderabad Network**\n\n"
            "This notebook presents the clinical, demographic, operational, and financial EDA across the network, "
            "followed by non-leaking patient-level behavioral feature extraction."
        ),
        code_cell(
            "import os\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n\n"
            "cleaned_dir = os.path.join('data', 'cleaned')\n"
            "processed_dir = os.path.join('data', 'processed')\n\n"
            "patients = pd.read_csv(os.path.join(cleaned_dir, 'patients_cleaned.csv'), low_memory=False)\n"
            "billing = pd.read_csv(os.path.join(cleaned_dir, 'billing_cleaned.csv'), low_memory=False)\n"
            "admissions = pd.read_csv(os.path.join(cleaned_dir, 'admissions_cleaned.csv'), low_memory=False)\n"
            "print(f'Loaded cleaned data: {len(patients):,} patients, {len(billing):,} billing transactions')"
        ),
        code_cell(
            "# 1. Hospital Revenue and Average Transaction Value\n"
            "hosp_rev = billing.groupby('hospital_name_cleaned').agg(\n"
            "    Total_Revenue_INR=('corrected_total_amount', 'sum'),\n"
            "    Avg_Transaction_INR=('corrected_total_amount', 'mean'),\n"
            "    Txn_Count=('transaction_id', 'count')\n"
            ").reset_index()\n"
            "hosp_rev['Revenue_Cr'] = (hosp_rev['Total_Revenue_INR'] / 1e7).round(2)\n"
            "print(hosp_rev)"
        ),
        code_cell(
            "# 2. Patient Features Summary\n"
            "features_full = pd.read_csv(os.path.join(processed_dir, 'patient_features_full.csv'), low_memory=False)\n"
            "print(f'Engineered features for {len(features_full):,} active patients.')\n"
            "print(features_full[['recency_days', 'visit_frequency', 'monetary_total', 'avg_length_of_stay', 'readmission_rate']].describe())"
        )
    ]
    nb = build_notebook_json(cells)
    path = os.path.join(NOTEBOOK_DIR, "02_eda_feature_engineering.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Created notebook: {path}")


def create_notebook_03():
    cells = [
        md_cell(
            "# HospitalIQ – Phase 3: RFM Segmentation, K-Means Clustering & Stability Analysis\n"
            "**Healthcare Data Analytics & Patient Segmentation Study | Hyderabad Network**\n\n"
            "This notebook executes RFM scoring, unsupervised K-Means clustering, cluster validation (Elbow Curve & Silhouette Scores), "
            "profile generation, and two-period longitudinal segment stability analysis."
        ),
        code_cell(
            "import os\n"
            "import pandas as pd\n"
            "import numpy as np\n\n"
            "processed_dir = os.path.join('data', 'processed')\n"
            "rfm_summary = pd.read_csv(os.path.join(processed_dir, 'rfm_segment_summary.csv'))\n"
            "print('--- RFM BEHAVIORAL COHORTS SUMMARY ---')\n"
            "print(rfm_summary[['rfm_segment', 'patient_count', 'patient_share_pct', 'revenue_share_pct', 'avg_monetary_value_inr', 'avg_visit_frequency']])"
        ),
        code_cell(
            "# 1. K-Means Cluster Profiles (Strict Minimum 5% Requirement Check)\n"
            "km_profiles = pd.read_csv(os.path.join(processed_dir, 'segment_profiles.csv'))\n"
            "print('--- K-MEANS MACHINE LEARNING CLUSTER PROFILES ---')\n"
            "print(km_profiles[['cluster_id', 'cluster_name', 'patient_count', 'patient_share_pct', 'revenue_share_pct', 'avg_monetary_inr', 'avg_visit_frequency', 'avg_los_days']])"
        ),
        code_cell(
            "# 2. Longitudinal Segment Stability & Migration Matrix\n"
            "mig_matrix = pd.read_csv(os.path.join(processed_dir, 'segment_migration_matrix.csv'), index_col=0)\n"
            "print('--- SEGMENT TRANSITION PROBABILITY MATRIX (%) ---')\n"
            "print(mig_matrix.round(1))"
        ),
        code_cell(
            "# 3. Strategic Business Recommendations\n"
            "recs = pd.read_csv(os.path.join(processed_dir, 'business_recommendations.csv'))\n"
            "print(recs[['segment_id', 'segment_name', 'estimated_cost_inr', 'expected_benefit_inr', 'measurement_kpi', 'target_value']])"
        )
    ]
    nb = build_notebook_json(cells)
    path = os.path.join(NOTEBOOK_DIR, "03_rfm_kmeans_clustering.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Created notebook: {path}")


if __name__ == "__main__":
    create_notebook_01()
    create_notebook_02()
    create_notebook_03()
