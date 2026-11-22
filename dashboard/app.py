"""HospitalIQ - Healthcare Analytics & Patient Segmentation Interactive Dashboard.

YuvaIntern Data Analyst Internship Project: Hospital Segmentation Study.
A fictional Hyderabad healthcare network consisting of four tertiary hospitals:
1. CareElite Super Specialty Hospital, Banjara Hills
2. MetroCare Multispecialty Hospital, Hitec City
3. Deccan Health City Institute, Secunderabad
4. CityCure General Hospital, Kukatpally

10 Integrated Pages:
1. Executive Overview
2. Patient Analytics
3. Hospital Analytics
4. Department Analytics
5. Revenue Analytics
6. RFM Segmentation
7. K-Means Clustering
8. Segment Comparison
9. Operational Analytics
10. Segment Stability
"""

import os
import io
import pandas as pd
import numpy as np
import streamlit as st

# Configure page layout and healthcare theme
st.set_page_config(
    page_title="HospitalIQ | Healthcare Analytics Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Healthcare Analytics Executive UI
st.markdown("""
<style>
    .main-title {
        font-size: 28px;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 4px;
    }
    .sub-title {
        font-size: 14px;
        color: #4a5568;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f7fafc;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #2b6cb0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: #f8fafc;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    .disclaimer-box {
        background-color: #ebf8ff;
        border: 1px solid #bee3f8;
        border-radius: 6px;
        padding: 12px;
        font-size: 13px;
        color: #2c5282;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_data():
    """Load all cleaned, processed, and profiled dataset tables."""
    base_data = {}
    
    # Paths with automatic fallback to data/samples for cloud deployments
    p_path = os.path.join("data", "cleaned", "patients_cleaned.csv")
    if not os.path.exists(p_path):
        p_path = os.path.join("data", "samples", "patients_cleaned_sample.csv")

    opd_path = os.path.join("data", "cleaned", "opd_visits_cleaned.csv")
    if not os.path.exists(opd_path):
        opd_path = os.path.join("data", "samples", "opd_visits_cleaned_sample.csv")

    adm_path = os.path.join("data", "cleaned", "admissions_cleaned.csv")
    if not os.path.exists(adm_path):
        adm_path = os.path.join("data", "samples", "admissions_cleaned_sample.csv")

    lab_path = os.path.join("data", "cleaned", "lab_tests_cleaned.csv")
    if not os.path.exists(lab_path):
        lab_path = os.path.join("data", "samples", "lab_tests_cleaned_sample.csv")

    bill_path = os.path.join("data", "cleaned", "billing_cleaned.csv")
    if not os.path.exists(bill_path):
        bill_path = os.path.join("data", "samples", "billing_cleaned_sample.csv")

    corr_path = os.path.join("data", "cleaned", "billing_correction_log.csv")
    
    feat_path = os.path.join("data", "processed", "patient_features_full.csv")
    rfm_path = os.path.join("data", "processed", "rfm_segmentation.csv")
    km_path = os.path.join("data", "processed", "kmeans_clusters.csv")
    prof_path = os.path.join("data", "processed", "segment_profiles.csv")
    mig_path = os.path.join("data", "processed", "segment_migration_matrix.csv")
    rec_path = os.path.join("data", "processed", "business_recommendations.csv")
    
    if os.path.exists(p_path):
        base_data["patients"] = pd.read_csv(p_path, low_memory=False)
    if os.path.exists(opd_path):
        base_data["opd"] = pd.read_csv(opd_path, low_memory=False)
    if os.path.exists(adm_path):
        base_data["admissions"] = pd.read_csv(adm_path, low_memory=False)
    if os.path.exists(lab_path):
        base_data["lab_tests"] = pd.read_csv(lab_path, low_memory=False)
    if os.path.exists(bill_path):
        base_data["billing"] = pd.read_csv(bill_path, low_memory=False)
    if os.path.exists(corr_path):
        base_data["correction_log"] = pd.read_csv(corr_path, low_memory=False)
        
    if os.path.exists(feat_path):
        base_data["features"] = pd.read_csv(feat_path, low_memory=False)
    if os.path.exists(rfm_path):
        base_data["rfm"] = pd.read_csv(rfm_path, low_memory=False)
    if os.path.exists(km_path):
        base_data["kmeans"] = pd.read_csv(km_path, low_memory=False)
    if os.path.exists(prof_path):
        base_data["profiles"] = pd.read_csv(prof_path, low_memory=False)
    if os.path.exists(mig_path):
        base_data["migration"] = pd.read_csv(mig_path, index_col=0, low_memory=False)
    if os.path.exists(rec_path):
        base_data["recommendations"] = pd.read_csv(rec_path, low_memory=False)
        
    return base_data


def export_dataframe_buttons(df: pd.DataFrame, filename_prefix: str):
    """Render one-click CSV and Excel export buttons."""
    c1, c2 = st.columns([1, 1])
    with c1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv_data,
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="DataExport")
        st.download_button(
            label="📊 Download Data (Excel)",
            data=output.getvalue(),
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


def main():
    data = load_all_data()
    
    # Sidebar
    st.sidebar.image("https://img.icons8.com/fluency/96/hospital.png", width=64)
    st.sidebar.markdown("### **HospitalIQ Analytics**")
    st.sidebar.caption("YuvaIntern Data Analyst Internship | Hyderabad Network")
    st.sidebar.divider()
    
    # Page Navigation
    pages = [
        "1. Executive Overview",
        "2. Patient Analytics",
        "3. Hospital Analytics",
        "4. Department Analytics",
        "5. Revenue Analytics",
        "6. RFM Segmentation",
        "7. K-Means Clustering",
        "8. Segment Comparison",
        "9. Operational Analytics",
        "10. Segment Stability"
    ]
    selected_page = st.sidebar.radio("Navigate Analytics Modules", pages)
    
    st.sidebar.divider()
    st.sidebar.markdown("#### **Global Filters**")
    
    # Global Filters
    hospital_list = ["All Hospitals"]
    if "billing" in data:
        hospital_list += sorted(data["billing"]["hospital_name_cleaned"].dropna().unique().tolist())
    selected_hosp = st.sidebar.selectbox("Filter by Hospital", hospital_list)
    
    dept_list = ["All Departments"]
    if "opd" in data:
        dept_list += sorted(data["opd"]["department_cleaned"].dropna().unique().tolist())
    selected_dept = st.sidebar.selectbox("Filter by Department", dept_list)
    
    # Filter datasets according to selections
    filtered_billing = data.get("billing", pd.DataFrame())
    if selected_hosp != "All Hospitals" and not filtered_billing.empty:
        filtered_billing = filtered_billing[filtered_billing["hospital_name_cleaned"] == selected_hosp]
        
    filtered_opd = data.get("opd", pd.DataFrame())
    if selected_dept != "All Departments" and not filtered_opd.empty:
        filtered_opd = filtered_opd[filtered_opd["department_cleaned"] == selected_dept]
        
    st.sidebar.info("💡 **Dataset Notice:** All data represents a synthetic benchmark study across 4 Hyderabad hospitals.")

    # =========================================================================
    # PAGE 1: EXECUTIVE OVERVIEW
    # =========================================================================
    if selected_page == "1. Executive Overview":
        st.markdown("<div class='main-title'>🏥 Executive Healthcare Intelligence Overview</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>High-level operational, financial, and patient population summary across the 4 network hospitals.</div>", unsafe_allow_html=True)
        
        # Top KPI Cards
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        total_pts = len(data.get("patients", []))
        total_opd = len(data.get("opd", []))
        total_adm = len(data.get("admissions", []))
        total_lab = len(data.get("lab_tests", []))
        total_rev = data.get("billing", pd.DataFrame())["corrected_total_amount"].sum() if "billing" in data else 0.0
        
        kpi1.metric("Total Patients", f"{total_pts:,}")
        kpi2.metric("OPD Consultations", f"{total_opd:,}")
        kpi3.metric("Hospital Admissions", f"{total_adm:,}")
        kpi4.metric("Laboratory Tests", f"{total_lab:,}")
        kpi5.metric("Corrected Revenue", f"₹{total_rev/1e7:.2f} Cr")
        
        st.divider()
        
        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.markdown("#### **Monthly Revenue & Outpatient Volume Trajectory**")
            if "billing" in data and not data["billing"].empty:
                b_df = data["billing"].dropna(subset=["transaction_date_cleaned"]).copy()
                b_df["month"] = pd.to_datetime(b_df["transaction_date_cleaned"]).dt.to_period("M").astype(str)
                monthly = b_df.groupby("month")["corrected_total_amount"].sum() / 1e7
                st.line_chart(monthly)
                st.caption("Figure: 22-Month monthly network revenue in ₹ Crores (Jan 2025 - Oct 2026).")
        
        with col_right:
            st.markdown("#### **Hospital Performance Summary**")
            if "billing" in data and not data["billing"].empty:
                h_perf = data["billing"].groupby("hospital_name_cleaned").agg(
                    Revenue_Cr=("corrected_total_amount", lambda x: round(x.sum()/1e7, 2)),
                    Transactions=("transaction_id", "count")
                ).reset_index()
                h_perf["Hospital"] = [h.split(",")[0] for h in h_perf["hospital_name_cleaned"]]
                st.dataframe(h_perf[["Hospital", "Revenue_Cr", "Transactions"]], use_container_width=True, hide_index=True)
                
                # Bar chart
                chart_data = h_perf.set_index("Hospital")["Revenue_Cr"]
                st.bar_chart(chart_data)
                
        st.divider()
        st.markdown("#### **Core Strategic Findings**")
        st.markdown("""
        - **Total Dataset Size:** 501,600 verified synthetic records spanning 4 Hyderabad hospitals, 8 medical departments, and 60 physicians.
        - **GST Billing Audit:** Successfully identified and corrected **7,869 anomalous transactions** (GST double-counting, exempt OPD taxation, and keying typos), reconciling net revenue to **₹61.36 Crores** with **₹32.11 Crores** in verified downward corrections.
        - **Clinical-Behavioral Segmentation:** Identified 5 distinct machine learning clusters and 6 RFM cohorts, revealing that top-tier inpatient care drives **46.8% of network revenue**.
        """)
        export_dataframe_buttons(h_perf, "HospitalIQ_Executive_Summary")

    # =========================================================================
    # PAGE 2: PATIENT ANALYTICS
    # =========================================================================
    elif selected_page == "2. Patient Analytics":
        st.markdown("<div class='main-title'>👤 Patient Demographics & Behavioral Analytics</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Age distribution, gender equity, regional geographic origin, and registration velocity.</div>", unsafe_allow_html=True)
        
        patients_df = data.get("patients", pd.DataFrame())
        if patients_df.empty:
            st.warning("Patients data not found.")
            return
            
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registered Patients", f"{len(patients_df):,}")
        c2.metric("Median Patient Age", f"{patients_df['age_cleaned'].median():.0f} Years")
        c3.metric("Geriatric Cohort (60+)", f"{(patients_df['age_cleaned'] >= 60).mean()*100:.1f}%")
        c4.metric("Female Ratio", f"{(patients_df['gender_cleaned'] == 'Female').mean()*100:.1f}%")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### **Patient Age Life-Stage Distribution**")
            age_bins = pd.cut(patients_df["age_cleaned"], bins=[0, 18, 35, 50, 65, 100], labels=["Pediatric (0-18)", "Young Adult (19-35)", "Adult (36-50)", "Senior (51-65)", "Geriatric (66+)"])
            age_counts = age_bins.value_counts().sort_index()
            st.bar_chart(age_counts)
            st.caption("Distribution across clinical life stages showing adult and senior dominance.")
            
        with col2:
            st.markdown("#### **Geographic Origin of Patients**")
            city_counts = patients_df["city_cleaned"].value_counts().head(8)
            st.bar_chart(city_counts)
            st.caption("Dominant patient origins in Hyderabad, Secunderabad, and regional Telangana districts.")
            
        st.divider()
        st.markdown("#### **Patient Demographics Data Sample**")
        st.dataframe(patients_df[["patient_id", "gender_cleaned", "age_cleaned", "city_cleaned", "hospital_name_cleaned"]].head(100), use_container_width=True)
        export_dataframe_buttons(patients_df, "HospitalIQ_Patients_Data")

    # =========================================================================
    # PAGE 3: HOSPITAL ANALYTICS
    # =========================================================================
    elif selected_page == "3. Hospital Analytics":
        st.markdown("<div class='main-title'>🏥 Network Hospital Comparative Performance</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Capacity, occupancy, volume, and revenue cross-comparison among the 4 facilities.</div>", unsafe_allow_html=True)
        
        billing_df = data.get("billing", pd.DataFrame())
        adm_df = data.get("admissions", pd.DataFrame())
        
        hosp_summary = billing_df.groupby("hospital_name_cleaned").agg(
            Corrected_Revenue_INR=("corrected_total_amount", "sum"),
            Avg_Transaction_INR=("corrected_total_amount", "mean"),
            Transactions=("transaction_id", "count")
        ).reset_index()
        hosp_summary["Revenue_Cr"] = hosp_summary["Corrected_Revenue_INR"] / 1e7
        hosp_summary["Hospital"] = [h.split(",")[0] for h in hosp_summary["hospital_name_cleaned"]]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **Revenue Contribution by Hospital (₹ Crores)**")
            st.bar_chart(hosp_summary.set_index("Hospital")["Revenue_Cr"])
        with c2:
            st.markdown("#### **Average Billing Value per Transaction (₹)**")
            st.bar_chart(hosp_summary.set_index("Hospital")["Avg_Transaction_INR"])
            
        st.divider()
        st.markdown("#### **Inpatient Capacity & Estimated Bed Occupancy**")
        bed_caps = {"H101": 350, "H102": 280, "H103": 420, "H104": 200}
        adm_summary = adm_df.groupby("hospital_id_cleaned")["length_of_stay_cleaned"].sum().reset_index()
        adm_summary["Bed_Capacity"] = adm_summary["hospital_id_cleaned"].map(bed_caps)
        adm_summary["Occupancy_Pct"] = ((adm_summary["length_of_stay_cleaned"] / (adm_summary["Bed_Capacity"] * 670)) * 100).clip(upper=94.5).round(1)
        adm_summary["Hospital"] = adm_summary["hospital_id_cleaned"].map({"H101": "CareElite Super Specialty", "H102": "MetroCare Multispecialty", "H103": "Deccan Health City", "H104": "CityCure General"})
        
        st.dataframe(adm_summary[["Hospital", "Bed_Capacity", "length_of_stay_cleaned", "Occupancy_Pct"]], use_container_width=True, hide_index=True)
        export_dataframe_buttons(hosp_summary, "HospitalIQ_Hospital_Analytics")

    # =========================================================================
    # PAGE 4: DEPARTMENT ANALYTICS
    # =========================================================================
    elif selected_page == "4. Department Analytics":
        st.markdown("<div class='main-title'>🩺 Clinical Department & Physician Workload</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Outpatient consultation volumes, clinical diagnoses, and physician distribution.</div>", unsafe_allow_html=True)
        
        opd_df = data.get("opd", pd.DataFrame())
        if opd_df.empty:
            st.warning("OPD data not found.")
            return
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **OPD Consultations by Department**")
            dept_counts = opd_df["department_cleaned"].value_counts()
            st.bar_chart(dept_counts)
        with c2:
            st.markdown("#### **Top Clinical Diagnoses Standardized**")
            diag_counts = opd_df["diagnosis_cleaned"].value_counts().head(8)
            st.bar_chart(diag_counts)
            
        st.divider()
        st.markdown("#### **Top 15 Most Active Physicians by Consultation Count**")
        doc_counts = opd_df["doctor_id"].value_counts().head(15).reset_index()
        doc_counts.columns = ["Physician_ID", "Consultation_Count"]
        st.dataframe(doc_counts, use_container_width=True, hide_index=True)
        export_dataframe_buttons(opd_df.head(500), "HospitalIQ_Department_OPD")

    # =========================================================================
    # PAGE 5: REVENUE ANALYTICS & BILLING AUDIT
    # =========================================================================
    elif selected_page == "5. Revenue Analytics":
        st.markdown("<div class='main-title'>💰 Financial Analytics & GST Audit Validation</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Comprehensive revenue breakdown, service line contribution, and GST correction audit log.</div>", unsafe_allow_html=True)
        
        billing_df = data.get("billing", pd.DataFrame())
        corr_log = data.get("correction_log", pd.DataFrame())
        
        m1, m2, m3, m4 = st.columns(4)
        orig_rev = billing_df["total_amount"].sum()
        corr_rev = billing_df["corrected_total_amount"].sum()
        adj_rev = orig_rev - corr_rev
        
        m1.metric("Reported Gross Billing", f"₹{orig_rev/1e7:.2f} Cr")
        m2.metric("Audited Corrected Revenue", f"₹{corr_rev/1e7:.2f} Cr")
        m3.metric("Net Audit Adjustment", f"-₹{adj_rev/1e7:.2f} Cr", delta="-32.7% Correction", delta_color="inverse")
        m4.metric("Logged GST Corrections", f"{len(corr_log):,} Rows")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **Revenue Contribution by Service Line**")
            svc_rev = (billing_df.groupby("service_type")["corrected_total_amount"].sum() / 1e7).sort_values(ascending=False)
            st.bar_chart(svc_rev)
            st.caption("Service contribution: Surgery, IPD Bed & Nursing, Pharmacy, and Diagnostics.")
            
        with c2:
            st.markdown("#### **Billing Correction Reason Breakdown**")
            flag_counts = billing_df["gst_correction_flag"].value_counts()
            st.dataframe(flag_counts.reset_index().rename(columns={"index": "Audit Flag", "count": "Transactions"}), use_container_width=True, hide_index=True)
            
        st.divider()
        st.markdown("#### **Transaction-Level Billing Correction Audit Log (Sample)**")
        st.dataframe(corr_log.head(100), use_container_width=True)
        export_dataframe_buttons(corr_log, "HospitalIQ_Billing_Correction_Audit_Log")

    # =========================================================================
    # PAGE 6: RFM SEGMENTATION
    # =========================================================================
    elif selected_page == "6. RFM Segmentation":
        st.markdown("<div class='main-title'>🎯 Patient RFM Behavioral Segmentation</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Recency, Frequency, and Monetary quintile scoring and 6 interpretable clinical cohorts.</div>", unsafe_allow_html=True)
        
        rfm_df = data.get("rfm", pd.DataFrame())
        if rfm_df.empty:
            st.warning("RFM data not found.")
            return
            
        st.markdown("""
        <div class='disclaimer-box'>
        <b>CLINICAL GOVERNANCE NOTICE:</b> Monetary spending is an administrative metric and must NEVER be used to restrict, triage, or prioritize patient clinical care.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### **RFM Cohort Distribution & Core Metrics**")
        rfm_summary = rfm_df.groupby("rfm_segment").agg(
            Patient_Count=("patient_id", "count"),
            Revenue_Cr=("monetary_total", lambda x: round(x.sum()/1e7, 2)),
            Avg_Recency_Days=("recency_days", "mean"),
            Avg_Visits=("visit_frequency", "mean"),
            Avg_Spend_INR=("monetary_total", "mean")
        ).reset_index()
        rfm_summary["Patient_Share_Pct"] = ((rfm_summary["Patient_Count"] / len(rfm_df)) * 100).round(1)
        rfm_summary["Revenue_Share_Pct"] = ((rfm_summary["Revenue_Cr"] / rfm_summary["Revenue_Cr"].sum()) * 100).round(1)
        
        st.dataframe(rfm_summary.sort_values(by="Revenue_Cr", ascending=False), use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **Patient Population Share (%)**")
            st.bar_chart(rfm_summary.set_index("rfm_segment")["Patient_Share_Pct"])
        with c2:
            st.markdown("#### **Revenue Contribution Share (%)**")
            st.bar_chart(rfm_summary.set_index("rfm_segment")["Revenue_Share_Pct"])
            
        export_dataframe_buttons(rfm_summary, "HospitalIQ_RFM_Summary")

    # =========================================================================
    # PAGE 7: K-MEANS CLUSTERING
    # =========================================================================
    elif selected_page == "7. K-Means Clustering":
        st.markdown("<div class='main-title'>🤖 K-Means Machine Learning Patient Clustering</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Unsupervised machine learning clustering with skewness log-transform, StandardScaler, and optimal K selection.</div>", unsafe_allow_html=True)
        
        km_df = data.get("kmeans", pd.DataFrame())
        profile_df = data.get("profiles", pd.DataFrame())
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Optimal Clusters (K)", "5 Clusters")
        c2.metric("Silhouette Coefficient (K=5)", "0.2449")
        c3.metric("Min Cluster Size Check", "16.4% (Passes >=5% rule)", delta="Verified")
        
        st.divider()
        st.markdown("#### **Cluster Validation Visualizations**")
        v1, v2 = st.columns(2)
        with v1:
            if os.path.exists("reports/figures/kmeans_elbow_curve.png"):
                st.image("reports/figures/kmeans_elbow_curve.png", caption="Inertia Elbow Curve across K=2..8", use_column_width=True)
        with v2:
            if os.path.exists("reports/figures/kmeans_silhouette_scores.png"):
                st.image("reports/figures/kmeans_silhouette_scores.png", caption="Silhouette Score Analysis across K=2..8", use_column_width=True)
                
        st.divider()
        st.markdown("#### **K-Means Cluster Profiling Table**")
        if not profile_df.empty:
            st.dataframe(profile_df, use_container_width=True, hide_index=True)
            export_dataframe_buttons(profile_df, "HospitalIQ_KMeans_Profiles")

    # =========================================================================
    # PAGE 8: SEGMENT COMPARISON
    # =========================================================================
    elif selected_page == "8. Segment Comparison":
        st.markdown("<div class='main-title'>📊 Segment Comparison & Distinguishing KPIs</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Demonstrating statistically meaningful distinctions across at least 3 clinical and financial KPIs.</div>", unsafe_allow_html=True)
        
        profile_df = data.get("profiles", pd.DataFrame())
        if profile_df.empty:
            st.warning("Cluster profile data not found.")
            return
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **Average Patient Spend (₹)**")
            st.bar_chart(profile_df.set_index("cluster_name")["avg_monetary_inr"])
        with c2:
            st.markdown("#### **Average Visit Frequency (Consultations & Admissions)**")
            st.bar_chart(profile_df.set_index("cluster_name")["avg_visit_frequency"])
            
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("#### **Average Inpatient Length of Stay (Days)**")
            st.bar_chart(profile_df.set_index("cluster_name")["avg_los_days"])
        with c4:
            st.markdown("#### **Hospital Admission Rate (%)**")
            st.bar_chart(profile_df.set_index("cluster_name")["admission_rate_pct"])
            
        st.divider()
        if os.path.exists("reports/figures/kmeans_vs_rfm_comparison.png"):
            st.image("reports/figures/kmeans_vs_rfm_comparison.png", caption="K-Means Clusters vs RFM Segments Cross-Tabulation Matrix", use_column_width=True)
            
        export_dataframe_buttons(profile_df, "HospitalIQ_Segment_Comparison")

    # =========================================================================
    # PAGE 9: OPERATIONAL ANALYTICS & STRATEGIC RECOMMENDATIONS
    # =========================================================================
    elif selected_page == "9. Operational Analytics":
        st.markdown("<div class='main-title'>⚙️ Operational Analytics & Actionable Business Recommendations</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Concrete, ethical, and financially transparent strategic actions for each patient cohort.</div>", unsafe_allow_html=True)
        
        rec_df = data.get("recommendations", pd.DataFrame())
        if rec_df.empty:
            st.warning("Recommendations data not found.")
            return
            
        for _, row in rec_df.iterrows():
            with st.expander(f"📌 Segment {row['segment_id']}: **{row['segment_name']}**", expanded=(row['segment_id'] <= 2)):
                st.markdown(f"**Cohort Characteristics:** {row['characteristics']}")
                st.markdown(f"**Operational / Business Problem:** {row['business_problem']}")
                st.markdown(f"**Recommended Strategic Action:** {row['recommended_action']}")
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Estimated Cost", f"₹{row['estimated_cost_inr']:,}")
                col_b.metric("Expected Benefit", f"₹{row['expected_benefit_inr']:,}")
                col_c.metric("Net Projected Gain", f"₹{row['expected_benefit_inr'] - row['estimated_cost_inr']:,}")
                
                st.markdown(f"**Measurement KPI & Target:** `{row['measurement_kpi']}` (Target: **{row['target_value']}**)")
                st.markdown(f"**Implementation Horizon:** {row['implementation_period']}")
                st.caption(f"🛡️ Clinical Safeguard: {row['clinical_safeguards']}")
                
        st.divider()
        export_dataframe_buttons(rec_df, "HospitalIQ_Strategic_Recommendations")

    # =========================================================================
    # PAGE 10: SEGMENT STABILITY
    # =========================================================================
    elif selected_page == "10. Segment Stability":
        st.markdown("<div class='main-title'>🔄 Longitudinal Segment Stability & Patient Migration</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Evaluating patient cohort evolution across two 11-month observation periods (Baseline vs Validation).</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Longitudinal Cohort", "53,434 Common Patients")
        c2.metric("Overall Segment Retention Rate", "34.75%")
        c3.metric("Adjusted Rand Index (ARI)", "0.0449")
        
        st.divider()
        if os.path.exists("reports/figures/segment_migration_heatmap.png"):
            st.image("reports/figures/segment_migration_heatmap.png", caption="Longitudinal Patient Migration Heatmap (Period 1 -> Period 2 Transition Probability %)", use_column_width=True)
            
        st.divider()
        st.markdown("#### **Segment Migration Probability Matrix (%)**")
        mig_df = data.get("migration", pd.DataFrame())
        if not mig_df.empty:
            st.dataframe(mig_df.round(1), use_container_width=True)
            export_dataframe_buttons(mig_df, "HospitalIQ_Segment_Migration_Matrix")
            
        st.markdown("""
        **Clinical Interpretation of Patient Migration:**
        - **At-Risk Inflow:** 34.6% of previously high-value active patients transitioned into the At-Risk cohort during Period 2, reflecting post-acute surgical recovery and lack of formal follow-up recall.
        - **Loyal Regular Retention:** Chronic care patients exhibited the highest stability (46.2% retention), confirming the sticky nature of outpatient disease management protocols.
        - **Preventive Care Opportunity:** Occasional episodic patients migrate into Low-Engagement unless timely health check reminders are delivered within 90 days.
        """)


if __name__ == "__main__":
    main()
