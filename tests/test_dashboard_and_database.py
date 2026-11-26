"""Automated Tests: Streamlit Dashboard Data Loading and SQLite Database Integrity."""

import os
import sqlite3
import pytest
from dashboard.app import load_all_data

DB_PATH = os.path.join("data", "database", "hospitaliq.db")


def test_dashboard_data_loader():
    """Verify Streamlit dashboard data loader loads all required tables without error."""
    data = load_all_data()
    required_keys = ["patients", "opd", "admissions", "lab_tests", "billing", "features", "rfm", "kmeans", "profiles", "migration", "recommendations"]
    for k in required_keys:
        assert k in data, f"Dashboard data dictionary missing key '{k}'"
        assert not data[k].empty, f"Dashboard dataset '{k}' is empty"


def test_sqlite_database_tables():
    """Verify SQLite database exists and contains all required analytical tables."""
    assert os.path.exists(DB_PATH), f"SQLite database {DB_PATH} missing"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    expected_tables = [
        "patients_clean", "opd_visits_clean", "admissions_clean",
        "lab_tests_clean", "billing_clean", "billing_correction_log",
        "patient_features_full", "rfm_segmentation", "kmeans_clusters",
        "segment_profiles", "segment_migration"
    ]
    for tbl in expected_tables:
        assert tbl in tables, f"Expected table '{tbl}' missing in SQLite database"
