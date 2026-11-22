"""HospitalIQ Segment Stability and Patient Migration Analysis Module.

Evaluates segment retention and longitudinal migration across two 11-month observation periods:
- Period 1 (Baseline): 2025-01-01 to 2025-11-30
- Period 2 (Validation): 2025-12-01 to 2026-10-31
- Calculation of retention rates, transition probabilities, and Adjusted Rand Index (ARI)
- Professional migration heatmap and clinical explanation of cohort trajectories
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import adjusted_rand_score
from src.segmentation_rfm import calculate_rfm_scores, assign_rfm_segments

FIGURE_DIR = os.path.join("reports", "figures")
os.makedirs(FIGURE_DIR, exist_ok=True)


def analyze_segment_stability(
    p1_features_path: str,
    p2_features_path: str,
    output_dir: str
) -> tuple[pd.DataFrame, dict]:
    """Execute two-period longitudinal stability and migration analysis."""
    print("=" * 60)
    print("HospitalIQ Segment Stability Analysis Starting...")
    print(f"Period 1: {p1_features_path}")
    print(f"Period 2: {p2_features_path}")
    print("=" * 60)
    
    df_p1 = pd.read_csv(p1_features_path, low_memory=False)
    df_p2 = pd.read_csv(p2_features_path, low_memory=False)
    
    # Run identical segmentation on each period
    p1_scored = calculate_rfm_scores(df_p1)
    p1_segmented = assign_rfm_segments(p1_scored)
    
    p2_scored = calculate_rfm_scores(df_p2)
    p2_segmented = assign_rfm_segments(p2_scored)
    
    # Filter common cohort observed in BOTH periods for valid longitudinal comparison
    common_pids = set(p1_segmented["patient_id"]).intersection(set(p2_segmented["patient_id"]))
    print(f"Common longitudinal cohort observed in both periods: {len(common_pids):,} patients.")
    
    p1_common = p1_segmented[p1_segmented["patient_id"].isin(common_pids)].sort_values("patient_id").reset_index(drop=True)
    p2_common = p2_segmented[p2_segmented["patient_id"].isin(common_pids)].sort_values("patient_id").reset_index(drop=True)
    
    labels_p1 = p1_common["rfm_segment"].values
    labels_p2 = p2_common["rfm_segment"].values
    
    # 1. Adjusted Rand Index (ARI)
    ari = adjusted_rand_score(labels_p1, labels_p2)
    
    # 2. Migration Matrix (% of Period 1 segment moving to Period 2 segment)
    migration_counts = pd.crosstab(
        pd.Series(labels_p1, name="Period 1 Segment (Baseline)"),
        pd.Series(labels_p2, name="Period 2 Segment (Evolution)")
    )
    
    migration_matrix_pct = pd.crosstab(
        pd.Series(labels_p1, name="Period 1 Segment (Baseline)"),
        pd.Series(labels_p2, name="Period 2 Segment (Evolution)"),
        normalize="index"
    ) * 100.0
    
    # 3. Retention Rate (Diagonal elements)
    diagonal_retained = np.diag(migration_counts)
    total_cohort = len(common_pids)
    retained_patients = diagonal_retained.sum()
    overall_retention_rate = (retained_patients / total_cohort) * 100.0
    migration_rate = 100.0 - overall_retention_rate
    
    # Per-segment retention rates
    segment_retention = {}
    for seg in migration_counts.index:
        total_in_p1 = migration_counts.loc[seg].sum()
        retained_in_p2 = migration_counts.loc[seg, seg] if seg in migration_counts.columns else 0
        segment_retention[seg] = round((retained_in_p2 / max(1, total_in_p1)) * 100.0, 2)
        
    # Save migration matrix to CSV
    os.makedirs(output_dir, exist_ok=True)
    matrix_csv_path = os.path.join(output_dir, "segment_migration_matrix.csv")
    migration_matrix_pct.round(2).to_csv(matrix_csv_path)
    
    # 4. Generate Professional Migration Heatmap
    fig, ax = plt.subplots(figsize=(10, 6.5))
    sns.heatmap(
        migration_matrix_pct,
        annot=True,
        fmt=".1f",
        cmap="Blues",
        cbar_kws={"label": "Transition Probability (%)"},
        linewidths=1.0,
        linecolor="#bdc3c7",
        ax=ax
    )
    ax.set_title(
        f"Segment Stability 1: Longitudinal Patient Migration Matrix (P1 -> P2)\n"
        f"Cohort: {total_cohort:,} Patients | Overall Retention: {overall_retention_rate:.1f}% | ARI: {ari:.3f}",
        fontsize=11,
        fontweight="bold"
    )
    ax.set_ylabel("Period 1 Baseline Segment", fontweight="bold")
    ax.set_xlabel("Period 2 Evolution Segment", fontweight="bold")
    plt.xticks(rotation=20, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()
    heatmap_path = os.path.join(FIGURE_DIR, "segment_migration_heatmap.png")
    fig.savefig(heatmap_path)
    plt.close(fig)
    
    # Compile summary metrics
    stability_metrics = {
        "common_cohort_size": total_cohort,
        "overall_retention_rate_pct": round(overall_retention_rate, 2),
        "overall_migration_rate_pct": round(migration_rate, 2),
        "adjusted_rand_index": round(ari, 4),
        "segment_retention": segment_retention,
        "matrix_csv": matrix_csv_path,
        "heatmap_chart": heatmap_path,
    }
    
    # Save metrics table
    metrics_df = pd.DataFrame([
        {"Metric": "Common Cohort Size", "Value": f"{total_cohort:,} Patients"},
        {"Metric": "Overall Segment Retention Rate", "Value": f"{overall_retention_rate:.2f}%"},
        {"Metric": "Overall Migration Rate", "Value": f"{migration_rate:.2f}%"},
        {"Metric": "Adjusted Rand Index (ARI)", "Value": f"{ari:.4f}"},
    ] + [
        {"Metric": f"Retention: {seg}", "Value": f"{rate:.1f}%"}
        for seg, rate in segment_retention.items()
    ])
    metrics_df.to_csv(os.path.join(output_dir, "segment_stability_metrics.csv"), index=False)
    
    print("=" * 60)
    print("SEGMENT STABILITY ANALYSIS COMPLETE")
    print(f"Overall Cohort Retention Rate: {overall_retention_rate:.2f}%")
    print(f"Longitudinal Migration Rate:   {migration_rate:.2f}%")
    print(f"Adjusted Rand Index (ARI):     {ari:.4f}")
    print(f"Migration Heatmap Saved:       {heatmap_path}")
    print("=" * 60)
    
    return migration_matrix_pct, stability_metrics


if __name__ == "__main__":
    p1_p = os.path.join("data", "processed", "patient_features_period1.csv")
    p2_p = os.path.join("data", "processed", "patient_features_period2.csv")
    out_d = os.path.join("data", "processed")
    analyze_segment_stability(p1_p, p2_p, out_d)
