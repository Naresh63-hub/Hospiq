"""HospitalIQ Patient RFM Segmentation Engine.

Implements clinical-administrative Recency, Frequency, Monetary scoring
and segments patients into 6 interpretable behavioral cohorts with
complete KPI profiling, distribution charts, and clinical disclaimers.

CLINICAL DISCLAIMER:
Monetary value is an administrative utilization metric and must NEVER be
interpreted as clinical priority or used to restrict or ration medical care.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

FIGURE_DIR = os.path.join("reports", "figures")
os.makedirs(FIGURE_DIR, exist_ok=True)


def calculate_rfm_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate R, F, M quintiles (1-5) and composite scores."""
    df_rfm = df.copy()
    
    # 1. Recency Score: Lower recency_days is better (higher score)
    # Using rank(pct=True) to handle duplicate values gracefully
    r_pct = df_rfm["recency_days"].rank(pct=True, ascending=False)
    df_rfm["r_score"] = pd.qcut(r_pct, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # 2. Frequency Score: Higher visit_frequency is better
    f_pct = df_rfm["visit_frequency"].rank(pct=True, method="first", ascending=True)
    df_rfm["f_score"] = pd.qcut(f_pct, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # 3. Monetary Score: Higher monetary_total is better
    m_pct = df_rfm["monetary_total"].rank(pct=True, method="first", ascending=True)
    df_rfm["m_score"] = pd.qcut(m_pct, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Composite RFM Score
    df_rfm["rfm_cell"] = (
        df_rfm["r_score"].astype(str) +
        df_rfm["f_score"].astype(str) +
        df_rfm["m_score"].astype(str)
    )
    df_rfm["rfm_composite_score"] = (
        df_rfm["r_score"] * 0.35 +
        df_rfm["f_score"] * 0.35 +
        df_rfm["m_score"] * 0.30
    ).round(2)
    
    return df_rfm


def assign_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Map RFM scores into 6 interpretable healthcare segments."""
    segments = []
    
    for _, row in df.iterrows():
        r = row["r_score"]
        f = row["f_score"]
        m = row["m_score"]
        
        # Segment 1: High-Value Active Patients (Recent, frequent, high utilization)
        if r >= 4 and f >= 4 and m >= 4:
            seg = "High-Value Active Patients"
        # Segment 5: At-Risk Patients (Past high engagement/spend, but lapsed >180 days)
        elif r <= 2 and (f >= 3 or m >= 3):
            seg = "At-Risk Patients"
        # Segment 2: Loyal Regular Patients (Consistent ongoing care, moderate-high frequency)
        elif r >= 3 and f >= 3:
            seg = "Loyal Regular Patients"
        # Segment 3: Growing Patients (Recent visits, expanding interactions)
        elif r >= 4 and f <= 3 and m >= 2:
            seg = "Growing Patients"
        # Segment 6: Low-Engagement Patients (Low recency, minimal frequency, low spend)
        elif r <= 2 and f <= 2 and m <= 2:
            seg = "Low-Engagement Patients"
        # Segment 4: Occasional Patients (Episodic acute care, average recency and frequency)
        else:
            seg = "Occasional Patients"
            
        segments.append(seg)
        
    df["rfm_segment"] = segments
    return df


def generate_rfm_profile_table(df_rfm: pd.DataFrame) -> pd.DataFrame:
    """Compute comprehensive KPI summary across all RFM segments."""
    total_patients = len(df_rfm)
    total_revenue = df_rfm["monetary_total"].sum()
    
    summary = df_rfm.groupby("rfm_segment").agg(
        patient_count=("patient_id", "count"),
        total_revenue_inr=("monetary_total", "sum"),
        avg_recency_days=("recency_days", "mean"),
        avg_visit_frequency=("visit_frequency", "mean"),
        avg_monetary_value_inr=("monetary_total", "mean"),
        avg_billing_per_txn=("avg_billing_value", "mean"),
        admission_rate_pct=("admission_frequency", lambda x: (x > 0).mean() * 100),
        avg_los_days=("avg_length_of_stay", "mean"),
        readmission_rate_pct=("readmission_rate", "mean"),
        lab_utilization_avg=("lab_utilization", "mean"),
    ).reset_index()
    
    summary["patient_share_pct"] = (summary["patient_count"] / total_patients) * 100
    summary["revenue_share_pct"] = (summary["total_revenue_inr"] / total_revenue) * 100
    
    # Sort logically by revenue contribution
    summary = summary.sort_values(by="revenue_share_pct", ascending=False).reset_index(drop=True)
    
    # Round metrics for readability
    summary["avg_recency_days"] = summary["avg_recency_days"].round(1)
    summary["avg_visit_frequency"] = summary["avg_visit_frequency"].round(2)
    summary["avg_monetary_value_inr"] = summary["avg_monetary_value_inr"].round(2)
    summary["avg_billing_per_txn"] = summary["avg_billing_per_txn"].round(2)
    summary["admission_rate_pct"] = summary["admission_rate_pct"].round(2)
    summary["avg_los_days"] = summary["avg_los_days"].round(2)
    summary["readmission_rate_pct"] = summary["readmission_rate_pct"].round(2)
    summary["patient_share_pct"] = summary["patient_share_pct"].round(2)
    summary["revenue_share_pct"] = summary["revenue_share_pct"].round(2)
    
    return summary


def plot_rfm_charts(df_rfm: pd.DataFrame, summary: pd.DataFrame) -> dict:
    """Generate professional RFM visualization charts."""
    # Chart 1: Segment Distribution (Patient Count and Share)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#e67e22", "#e74c3c"]
    bars = ax.barh(summary["rfm_segment"], summary["patient_count"], color=colors[:len(summary)], edgecolor="black", alpha=0.85)
    for bar, pct in zip(bars, summary["patient_share_pct"]):
        w = bar.get_width()
        ax.text(w + 300, bar.get_y() + bar.get_height()/2.0, f"{w:,} ({pct:.1f}%)", va="center", fontweight="bold")
    ax.set_title("RFM 1: Patient Distribution by Behavioral Segment")
    ax.set_xlabel("Number of Patients")
    ax.set_xlim(0, max(summary["patient_count"]) * 1.25)
    fig.tight_layout()
    chart1_path = os.path.join(FIGURE_DIR, "rfm_01_segment_distribution.png")
    fig.savefig(chart1_path)
    plt.close(fig)
    
    # Chart 2: Revenue Contribution Donut Chart
    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        summary["revenue_share_pct"],
        labels=summary["rfm_segment"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(summary)],
        pctdistance=0.75,
        explode=[0.03] * len(summary)
    )
    # Donut hole
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre_circle)
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(9)
    ax.set_title("RFM 2: Corrected Revenue Contribution by Segment")
    fig.tight_layout()
    chart2_path = os.path.join(FIGURE_DIR, "rfm_02_revenue_contribution.png")
    fig.savefig(chart2_path)
    plt.close(fig)
    
    # Chart 3: KPI Heatmap Comparison
    kpi_cols = ["avg_recency_days", "avg_visit_frequency", "avg_monetary_value_inr", "admission_rate_pct", "readmission_rate_pct"]
    norm_summary = summary.set_index("rfm_segment")[kpi_cols].copy()
    # Normalize 0-1 for heatmap display
    norm_summary_scaled = (norm_summary - norm_summary.min()) / (norm_summary.max() - norm_summary.min() + 1e-6)
    
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.heatmap(norm_summary_scaled, annot=norm_summary.round(1), fmt="g", cmap="YlGnBu", cbar=True, ax=ax, linewidths=0.5)
    ax.set_title("RFM 3: Clinical & Financial KPI Comparison Matrix")
    ax.set_ylabel("RFM Segment")
    fig.tight_layout()
    chart3_path = os.path.join(FIGURE_DIR, "rfm_03_kpi_comparison.png")
    fig.savefig(chart3_path)
    plt.close(fig)
    
    return {"chart1": chart1_path, "chart2": chart2_path, "chart3": chart3_path}


def run_rfm_segmentation(features_path: str, output_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute complete RFM segmentation pipeline."""
    print("=" * 60)
    print("HospitalIQ RFM Patient Segmentation Starting...")
    print(f"Reading features from: {features_path}")
    print("=" * 60)
    
    df = pd.read_csv(features_path, low_memory=False)
    
    # Calculate scores & assign segments
    df_rfm = calculate_rfm_scores(df)
    df_rfm = assign_rfm_segments(df_rfm)
    
    # Summary profile
    summary = generate_rfm_profile_table(df_rfm)
    
    # Save outputs
    df_rfm.to_csv(output_path, index=False)
    summary_path = os.path.join(os.path.dirname(output_path), "rfm_segment_summary.csv")
    summary.to_csv(summary_path, index=False)
    
    # Generate charts
    charts = plot_rfm_charts(df_rfm, summary)
    
    print("=" * 60)
    print("RFM SEGMENTATION COMPLETE")
    print(f"Total Patients Segmented: {len(df_rfm):,}")
    print(f"Segments Generated:       {len(summary)}")
    print(summary[["rfm_segment", "patient_count", "patient_share_pct", "revenue_share_pct", "avg_recency_days", "avg_visit_frequency"]])
    print("=" * 60)
    
    return df_rfm, summary


if __name__ == "__main__":
    f_path = os.path.join("data", "processed", "patient_features_full.csv")
    out_path = os.path.join("data", "processed", "rfm_segmentation.csv")
    run_rfm_segmentation(f_path, out_path)
