"""HospitalIQ Synthetic Healthcare Dataset Generator.

Generates ~500,000 realistic records across 4 fictional Hyderabad hospitals
with interconnected relational tables, realistic clinical distributions,
and deliberate data-quality issues for data cleaning and validation.

All records are EXPLICITLY SYNTHETIC and designed for evaluation.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set reproducible seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Network Hospital Definitions in Hyderabad
HOSPITALS = {
    "H101": {
        "name": "CareElite Super Specialty Hospital",
        "location": "Banjara Hills",
        "city": "Hyderabad",
        "beds": 350,
        "name_variants": [
            "CareElite Super Specialty Hospital",
            "CareElite Super Specialty Hospital, Banjara Hills",
            "CareElite Banjara",
            "Care Elite Hospital - Banjara Hills",
            "CAREELITE HOSP",
        ],
    },
    "H102": {
        "name": "MetroCare Multispecialty Hospital",
        "location": "Hitec City",
        "city": "Hyderabad",
        "beds": 280,
        "name_variants": [
            "MetroCare Multispecialty Hospital",
            "MetroCare Multispecialty Hospital, Hitec City",
            "MetroCare Hitec City",
            "Metro Care Hospital",
            "METROCARE HOSP HITEC",
        ],
    },
    "H103": {
        "name": "Deccan Health City Institute",
        "location": "Secunderabad",
        "city": "Hyderabad",
        "beds": 420,
        "name_variants": [
            "Deccan Health City Institute",
            "Deccan Health City Institute, Secunderabad",
            "Deccan Health City",
            "Deccan Healthcity Sec-bad",
            "DECCAN HEALTH CITY INST",
        ],
    },
    "H104": {
        "name": "CityCure General Hospital",
        "location": "Kukatpally",
        "city": "Hyderabad",
        "beds": 200,
        "name_variants": [
            "CityCure General Hospital",
            "CityCure General Hospital, Kukatpally",
            "CityCure Kukatpally",
            "City Cure Gen Hosp",
            "CITYCURE GENERAL",
        ],
    },
}

DEPARTMENTS = [
    "General Medicine",
    "Cardiology",
    "Endocrinology",
    "Orthopedics",
    "Pulmonology",
    "Gastroenterology",
    "Nephrology",
    "Neurology",
]

DIAGNOSIS_MAP = {
    "Type 2 Diabetes Mellitus": [
        "Type 2 Diabetes Mellitus",
        "T2DM",
        "Diabetes Mellitus Type II",
        "type 2 diabetes",
        "Non-insulin dependent diabetes mellitus (NIDDM)",
        "Diabetes Mellitus - uncontrolled",
    ],
    "Essential Hypertension": [
        "Essential Hypertension",
        "HTN",
        "Hypertension (primary)",
        "High Blood Pressure",
        "Systemic Hypertension",
    ],
    "Coronary Artery Disease": [
        "Coronary Artery Disease",
        "CAD",
        "Ischemic Heart Disease (IHD)",
        "Angina Pectoris",
        "Coronary Atherosclerosis",
    ],
    "Bronchial Asthma / COPD": [
        "Bronchial Asthma",
        "Asthma",
        "COPD with acute exacerbation",
        "Chronic Obstructive Pulmonary Disease",
        "Asthma bronchiale",
    ],
    "Acute Bronchitis": [
        "Acute Bronchitis",
        "Bronchitis acute",
        "Chest infection / bronchitis",
    ],
    "Osteoarthritis": [
        "Osteoarthritis Knee",
        "OA bilateral knees",
        "Degenerative joint disease",
        "Osteoarthritis of lumbar spine",
    ],
    "Chronic Kidney Disease": [
        "Chronic Kidney Disease - Stage 3",
        "CKD Stage 3",
        "Chronic Renal Failure (CRF)",
        "Diabetic Nephropathy / CKD",
    ],
    "Gastroenteritis": [
        "Acute Gastroenteritis (AGE)",
        "Gastroenteritis with mild dehydration",
        "Food poisoning / acute colitis",
        "Infectious diarrhea",
    ],
    "Viral Fever / PUO": [
        "Viral Fever",
        "Pyrexia of Unknown Origin (PUO)",
        "Acute febrile illness",
        "Dengue fever (seronegative)",
    ],
    "Routine Checkup": [
        "Routine Health Checkup",
        "Annual Wellness Exam",
        "Executive Health Screening",
        "General health evaluation",
    ],
}

DOCTORS = [f"DOC{i:03d}" for i in range(101, 161)]
CITIES = ["Hyderabad", "Secunderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam", "Vijayawada", "Guntur"]
CITY_WEIGHTS = [0.55, 0.20, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03]

LAB_TEST_CATALOG = [
    ("HbA1c", "Biochemistry", 650.0),
    ("Complete Blood Picture (CBP)", "Hematology", 450.0),
    ("Lipid Profile", "Biochemistry", 950.0),
    ("Liver Function Test (LFT)", "Biochemistry", 850.0),
    ("Renal Function Test (RFT)", "Biochemistry", 800.0),
    ("Serum Creatinine & Urea", "Biochemistry", 400.0),
    ("Thyroid Profile (T3, T4, TSH)", "Biochemistry", 750.0),
    ("Urine Routine & Microscopic", "Pathology", 250.0),
    ("Blood Culture & Sensitivity", "Microbiology", 1200.0),
    ("ECG (12-Lead)", "Cardiology Diagnostics", 350.0),
    ("2D Echocardiogram", "Cardiology Diagnostics", 2500.0),
    ("Chest X-Ray PA View", "Radiology / Imaging", 500.0),
    ("Ultrasound Abdomen & Pelvis", "Radiology / Imaging", 1800.0),
    ("CT Scan Brain / Abdomen", "Radiology / Imaging", 5500.0),
    ("MRI Lumbar Spine", "Radiology / Imaging", 7500.0),
]


def format_date_mixed(dt: datetime) -> str:
    """Simulate mixed date formatting from legacy hospital IT systems."""
    r = random.random()
    if r < 0.65:
        return dt.strftime("%Y-%m-%d")
    elif r < 0.82:
        return dt.strftime("%d/%m/%Y")
    elif r < 0.94:
        return dt.strftime("%m/%d/%Y")
    else:
        return dt.strftime("%Y/%m/%d")


def generate_patients(n_patients=65000) -> pd.DataFrame:
    """Generate master patient demographic table."""
    print(f"Generating {n_patients:,} synthetic patient records...")
    patient_ids = [f"P{100000 + i}" for i in range(1, n_patients + 1)]
    
    # Age distribution: healthcare demographics have peaks in middle aged and elderly
    # 0-18: 12%, 19-35: 22%, 36-50: 28%, 51-65: 24%, 66-90: 14%
    age_bins = [
        (1, 18, 0.10),
        (19, 35, 0.22),
        (36, 50, 0.28),
        (51, 65, 0.25),
        (66, 88, 0.15)
    ]
    
    ages = []
    for _ in range(n_patients):
        r = random.random()
        cum = 0
        chosen_bin = age_bins[-1]
        for low, high, prob in age_bins:
            cum += prob
            if r <= cum:
                chosen_bin = (low, high, prob)
                break
        ages.append(random.randint(chosen_bin[0], chosen_bin[1]))
    
    ages = np.array(ages)
    
    # Calculate DOB relative to study end date 2026-10-31
    base_date = datetime(2026, 10, 31)
    dobs = []
    for age in ages:
        days_offset = int(age * 365.25 + random.randint(0, 360))
        dob_dt = base_date - timedelta(days=days_offset)
        dobs.append(format_date_mixed(dob_dt))
        
    # Genders
    genders = np.random.choice(["Male", "Female", "Other"], size=n_patients, p=[0.50, 0.48, 0.02])
    
    # Registration dates: between 2024-01-01 and 2025-12-31
    reg_start = datetime(2024, 1, 1)
    reg_days = (datetime(2025, 12, 31) - reg_start).days
    reg_dates = [
        format_date_mixed(reg_start + timedelta(days=int(d)))
        for d in np.random.uniform(0, reg_days, size=n_patients)
    ]
    
    # Cities
    cities = np.random.choice(CITIES, size=n_patients, p=CITY_WEIGHTS)
    
    # Hospital ID & Name variants
    hosp_keys = list(HOSPITALS.keys())
    assigned_hosps = np.random.choice(hosp_keys, size=n_patients, p=[0.28, 0.24, 0.32, 0.16])
    hospital_names = [
        random.choice(HOSPITALS[h]["name_variants"]) for h in assigned_hosps
    ]
    
    # Quality Issue: Some patients have age missing (null), requiring DOB-to-age derivation
    ages_with_missing = [
        None if random.random() < 0.12 else a for a in ages
    ]
    
    df = pd.DataFrame({
        "patient_id": patient_ids,
        "date_of_birth": dobs,
        "age": ages_with_missing,
        "gender": genders,
        "registration_date": reg_dates,
        "city": cities,
        "hospital_id": assigned_hosps,
        "hospital_name": hospital_names,
        "dataset_type": "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY"
    })
    return df, ages


def generate_opd_visits(patients_df: pd.DataFrame, n_visits=220000) -> pd.DataFrame:
    """Generate outpatient department (OPD) visits."""
    print(f"Generating {n_visits:,} synthetic OPD visit records...")
    patient_ids = patients_df["patient_id"].values
    
    # Assign higher visit probability to a subset of patients (Pareto-like visit frequency)
    p_weights = np.random.pareto(a=2.5, size=len(patient_ids)) + 0.1
    p_weights /= p_weights.sum()
    
    chosen_patient_indices = np.random.choice(len(patient_ids), size=n_visits, p=p_weights)
    chosen_patients = patient_ids[chosen_patient_indices]
    
    visit_ids = [f"OPD{2000000 + i}" for i in range(1, n_visits + 1)]
    
    # Observation window: 2025-01-01 to 2026-10-31
    obs_start = datetime(2025, 1, 1)
    obs_end = datetime(2026, 10, 31)
    total_days = (obs_end - obs_start).days
    
    visit_dates = [
        format_date_mixed(obs_start + timedelta(days=int(d)))
        for d in np.random.uniform(0, total_days, size=n_visits)
    ]
    
    # Select diagnoses and departments
    diag_categories = list(DIAGNOSIS_MAP.keys())
    diag_probs = [0.18, 0.16, 0.12, 0.10, 0.08, 0.09, 0.06, 0.07, 0.08, 0.06]
    chosen_diag_cats = np.random.choice(diag_categories, size=n_visits, p=diag_probs)
    
    diagnoses_text = []
    departments = []
    
    category_to_dept = {
        "Type 2 Diabetes Mellitus": "Endocrinology",
        "Essential Hypertension": "Cardiology",
        "Coronary Artery Disease": "Cardiology",
        "Bronchial Asthma / COPD": "Pulmonology",
        "Acute Bronchitis": "General Medicine",
        "Osteoarthritis": "Orthopedics",
        "Chronic Kidney Disease": "Nephrology",
        "Gastroenteritis": "Gastroenterology",
        "Viral Fever / PUO": "General Medicine",
        "Routine Checkup": "General Medicine",
    }
    
    for cat in chosen_diag_cats:
        # Quality issue: inconsistent text, casing, and abbreviations
        variant = random.choice(DIAGNOSIS_MAP[cat])
        if random.random() < 0.10:
            variant = variant.lower()
        elif random.random() < 0.05:
            variant = variant.upper()
        diagnoses_text.append(variant)
        
        # Dept
        dept = category_to_dept.get(cat, "General Medicine")
        if random.random() < 0.12:
            dept = random.choice(DEPARTMENTS)  # cross-consultation
        departments.append(dept)
        
    doctors = np.random.choice(DOCTORS, size=n_visits)
    visit_types = np.random.choice(
        ["Consultation", "Follow-up", "Emergency", "Routine Checkup"],
        size=n_visits,
        p=[0.48, 0.35, 0.10, 0.07]
    )
    
    # Quality issues: Missing diagnosis in ~1.5% records
    diagnoses_text = [
        None if random.random() < 0.015 else d for d in diagnoses_text
    ]
    
    df = pd.DataFrame({
        "visit_id": visit_ids,
        "patient_id": chosen_patients,
        "visit_date": visit_dates,
        "diagnosis": diagnoses_text,
        "department": departments,
        "doctor_id": doctors,
        "visit_type": visit_types,
        "dataset_type": "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY"
    })
    return df


def generate_admissions(patients_df: pd.DataFrame, n_admissions=45000) -> pd.DataFrame:
    """Generate inpatient hospital admissions table."""
    print(f"Generating {n_admissions:,} synthetic admission records...")
    patient_ids = patients_df["patient_id"].values
    
    # Older patients have higher hospitalization rate
    p_weights = np.random.exponential(scale=1.0, size=len(patient_ids)) + 0.05
    p_weights /= p_weights.sum()
    chosen_patients = np.random.choice(patient_ids, size=n_admissions, p=p_weights)
    
    admission_ids = [f"ADM{3000000 + i}" for i in range(1, n_admissions + 1)]
    
    obs_start = datetime(2025, 1, 1)
    obs_end = datetime(2026, 10, 25)
    total_days = (obs_end - obs_start).days
    
    # Generate admission dates
    admit_days = np.random.uniform(0, total_days, size=n_admissions)
    admit_dts = [obs_start + timedelta(days=int(d)) for d in admit_days]
    
    # Length of stay: geometric/lognormal distribution, median 3-4 days, tail up to 28 days
    raw_los = np.random.lognormal(mean=1.2, sigma=0.7, size=n_admissions)
    los = np.clip(np.round(raw_los).astype(int), 1, 35)
    
    discharge_dts = [
        admit + timedelta(days=int(l)) for admit, l in zip(admit_dts, los)
    ]
    
    admission_types = np.random.choice(
        ["Emergency", "Elective", "Urgent", "Day Care"],
        size=n_admissions,
        p=[0.42, 0.32, 0.16, 0.10]
    )
    
    hosp_keys = list(HOSPITALS.keys())
    hospital_ids = np.random.choice(hosp_keys, size=n_admissions, p=[0.30, 0.25, 0.30, 0.15])
    
    # 30-day readmission indicator: simulate realistic hospital readmission (~8-12%)
    # Some patients will have readmission = 1
    readmit_indicator = np.random.choice([0, 1], size=n_admissions, p=[0.90, 0.10])
    
    # Introduce data quality anomalies:
    # 1. Missing discharge date (~2% current inpatients or omitted)
    # 2. Discharge date before admission date (~0.3% error)
    # 3. Mixed date formats
    admit_dates_str = []
    discharge_dates_str = []
    los_reported = []
    
    for admit, discharge, l in zip(admit_dts, discharge_dts, los):
        r = random.random()
        if r < 0.02:
            # missing discharge
            discharge_dates_str.append(None)
            los_reported.append(None)
            admit_dates_str.append(format_date_mixed(admit))
        elif r < 0.025:
            # invalid date: discharge before admission
            discharge_dates_str.append(format_date_mixed(admit - timedelta(days=2)))
            los_reported.append(-2)
            admit_dates_str.append(format_date_mixed(admit))
        else:
            discharge_dates_str.append(format_date_mixed(discharge))
            los_reported.append(l)
            admit_dates_str.append(format_date_mixed(admit))
            
    df = pd.DataFrame({
        "admission_id": admission_ids,
        "patient_id": chosen_patients,
        "hospital_id": hospital_ids,
        "admission_date": admit_dates_str,
        "discharge_date": discharge_dates_str,
        "length_of_stay": los_reported,
        "admission_type": admission_types,
        "readmission_indicator": readmit_indicator,
        "dataset_type": "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY"
    })
    return df


def generate_lab_tests(patients_df: pd.DataFrame, n_tests=90000) -> pd.DataFrame:
    """Generate laboratory test orders and results table."""
    print(f"Generating {n_tests:,} synthetic laboratory test records...")
    patient_ids = patients_df["patient_id"].values
    chosen_patients = np.random.choice(patient_ids, size=n_tests)
    
    test_ids = [f"LAB{4000000 + i}" for i in range(1, n_tests + 1)]
    
    obs_start = datetime(2025, 1, 1)
    obs_end = datetime(2026, 10, 31)
    total_days = (obs_end - obs_start).days
    
    test_dates = [
        format_date_mixed(obs_start + timedelta(days=int(d)))
        for d in np.random.uniform(0, total_days, size=n_tests)
    ]
    
    catalog_indices = np.random.choice(len(LAB_TEST_CATALOG), size=n_tests)
    test_names = [LAB_TEST_CATALOG[idx][0] for idx in catalog_indices]
    categories = [LAB_TEST_CATALOG[idx][1] for idx in catalog_indices]
    test_costs = [LAB_TEST_CATALOG[idx][2] for idx in catalog_indices]
    
    hosp_keys = list(HOSPITALS.keys())
    hospital_ids = np.random.choice(hosp_keys, size=n_tests, p=[0.29, 0.25, 0.31, 0.15])
    
    df = pd.DataFrame({
        "test_id": test_ids,
        "patient_id": chosen_patients,
        "hospital_id": hospital_ids,
        "test_date": test_dates,
        "test_name": test_names,
        "test_category": categories,
        "test_cost": test_costs,
        "dataset_type": "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY"
    })
    return df


def generate_billing(patients_df: pd.DataFrame, n_bills=80000) -> pd.DataFrame:
    """Generate billing and financial transactions table with explicit GST anomalies."""
    print(f"Generating {n_bills:,} synthetic billing transaction records...")
    patient_ids = patients_df["patient_id"].values
    
    # Billing distribution: some patients generate high monetary value (surgeries/admissions)
    p_weights = np.random.pareto(a=2.0, size=len(patient_ids)) + 0.1
    p_weights /= p_weights.sum()
    chosen_patients = np.random.choice(patient_ids, size=n_bills, p=p_weights)
    
    transaction_ids = [f"TXN{5000000 + i}" for i in range(1, n_bills + 1)]
    
    obs_start = datetime(2025, 1, 1)
    obs_end = datetime(2026, 10, 31)
    total_days = (obs_end - obs_start).days
    
    txn_dates = [
        format_date_mixed(obs_start + timedelta(days=int(d)))
        for d in np.random.uniform(0, total_days, size=n_bills)
    ]
    
    services = [
        ("OPD Consultation", 0.35, 750.0, 300.0, 0.0),      # Standard OPD is GST exempt (0%)
        ("Pharmacy & Consumables", 0.22, 2800.0, 1500.0, 0.12), # 12% GST
        ("Laboratory Diagnostics", 0.18, 1600.0, 800.0, 0.0),   # Diagnostic tests are exempt
        ("IPD Bed & Nursing", 0.13, 14500.0, 8000.0, 0.05),     # Higher rooms attract GST
        ("Surgery & OT Charges", 0.08, 48000.0, 22000.0, 0.0),  # Healthcare service exempt
        ("Day Care Procedure", 0.04, 12000.0, 5000.0, 0.0),     # Exempt
    ]
    
    svc_names = [s[0] for s in services]
    svc_probs = [s[1] for s in services]
    chosen_services_idx = np.random.choice(len(services), size=n_bills, p=svc_probs)
    
    base_amounts = []
    gst_amounts = []
    total_amounts = []
    service_names = []
    
    # We will track synthetic GST anomaly types for verification
    for idx in chosen_services_idx:
        name, _, mean_val, std_val, normal_gst_rate = services[idx]
        service_names.append(name)
        
        # Base amount
        b_amt = max(350.0, float(np.round(np.random.normal(mean_val, std_val), 2)))
        
        # Anomaly generation
        r = random.random()
        
        if r < 0.06:
            # Case 1: GST Double-Counting Error in legacy billing module
            # The system calculated Total = (Base + GST) + GST = Base + 2 * GST
            tax_rate = 0.18 if normal_gst_rate == 0 else normal_gst_rate
            gst_val = float(np.round(b_amt * tax_rate, 2))
            tot_val = float(np.round(b_amt + 2 * gst_val, 2))
        elif r < 0.10:
            # Case 2: Erroneous GST charged on GST-exempt OPD Consultation / Lab test
            # Standard healthcare consultation is 0% GST, but legacy system levied 18% GST
            gst_val = float(np.round(b_amt * 0.18, 2))
            tot_val = float(np.round(b_amt + gst_val, 2))
        elif r < 0.12:
            # Case 3: Base Amount was already inclusive of GST, but GST added again
            # Total = Base + GST
            gst_val = float(np.round(b_amt * 0.18, 2))
            tot_val = float(np.round(b_amt + gst_val, 2))
        elif r < 0.124:
            # Case 4: Extreme outlier - typo keying error (e.g. ₹9,999,999 or extra zeros)
            b_amt = 999999.0
            gst_val = 0.0
            tot_val = 999999.0
        elif r < 0.127:
            # Case 5: Negative billing value (unflagged refund/reversal)
            b_amt = -float(np.round(b_amt, 2))
            gst_val = 0.0
            tot_val = b_amt
        else:
            # Case 6: Correct standard billing
            gst_val = float(np.round(b_amt * normal_gst_rate, 2))
            tot_val = float(np.round(b_amt + gst_val, 2))
            
        base_amounts.append(b_amt)
        gst_amounts.append(gst_val)
        total_amounts.append(tot_val)
        
    payment_statuses = np.random.choice(
        ["Paid", "Pending", "Partially Paid", "Refunded", "Failed"],
        size=n_bills,
        p=[0.82, 0.08, 0.05, 0.03, 0.02]
    )
    # Quality issue: Missing payment status ~2.5%
    payment_statuses = [
        None if random.random() < 0.025 else s for s in payment_statuses
    ]
    
    hosp_keys = list(HOSPITALS.keys())
    hospital_ids = np.random.choice(hosp_keys, size=n_bills, p=[0.29, 0.25, 0.31, 0.15])
    
    df = pd.DataFrame({
        "transaction_id": transaction_ids,
        "patient_id": chosen_patients,
        "hospital_id": hospital_ids,
        "transaction_date": txn_dates,
        "service_type": service_names,
        "base_amount": base_amounts,
        "gst": gst_amounts,
        "total_amount": total_amounts,
        "payment_status": payment_statuses,
        "dataset_type": "SYNTHETIC_DATA_FOR_INTERNSHIP_STUDY"
    })
    
    # Quality issue: Duplicate transactions (~2% exact duplicates appended)
    n_dups = int(n_bills * 0.02)
    dup_rows = df.sample(n=n_dups, random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)
    
    return df


def generate_and_save_all(output_dir: str):
    """Generate all 5 tables and save to disk."""
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 60)
    print("HospitalIQ Synthetic Dataset Generation Starting...")
    print(f"Target Output Directory: {output_dir}")
    print("=" * 60)
    
    patients_df, _ = generate_patients(65000)
    patients_path = os.path.join(output_dir, "patients.csv")
    patients_df.to_csv(patients_path, index=False)
    print(f"Saved: {patients_path} ({len(patients_df):,} rows)")
    
    opd_df = generate_opd_visits(patients_df, 220000)
    opd_path = os.path.join(output_dir, "opd_visits.csv")
    opd_df.to_csv(opd_path, index=False)
    print(f"Saved: {opd_path} ({len(opd_df):,} rows)")
    
    admissions_df = generate_admissions(patients_df, 45000)
    adm_path = os.path.join(output_dir, "admissions.csv")
    admissions_df.to_csv(adm_path, index=False)
    print(f"Saved: {adm_path} ({len(admissions_df):,} rows)")
    
    lab_df = generate_lab_tests(patients_df, 90000)
    lab_path = os.path.join(output_dir, "lab_tests.csv")
    lab_df.to_csv(lab_path, index=False)
    print(f"Saved: {lab_path} ({len(lab_df):,} rows)")
    
    billing_df = generate_billing(patients_df, 80000)
    bill_path = os.path.join(output_dir, "billing.csv")
    billing_df.to_csv(bill_path, index=False)
    print(f"Saved: {bill_path} ({len(billing_df):,} rows)")
    
    total_records = len(patients_df) + len(opd_df) + len(admissions_df) + len(lab_df) + len(billing_df)
    print("=" * 60)
    print(f"DATASET GENERATION COMPLETE: Total Records = {total_records:,}")
    print("=" * 60)
    return {
        "patients": len(patients_df),
        "opd_visits": len(opd_df),
        "admissions": len(admissions_df),
        "lab_tests": len(lab_df),
        "billing": len(billing_df),
        "total": total_records
    }


if __name__ == "__main__":
    out_dir = os.path.join("data", "raw")
    generate_and_save_all(out_dir)
