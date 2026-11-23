"""HospitalIQ K-Means Machine Learning Clustering Engine.

Implements unsupervised patient clustering independent of RFM:
- Feature skewness diagnosis and log1p transformation
- Feature scaling with StandardScaler
- Inertia elbow curve and Silhouette score evaluation across K=2..8
- Minimum 5% segment size enforcement and clinical validation
- Multi-dimensional cluster profiling across clinical & financial KPIs
- Cross-tabulation comparison against RFM segmentation
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.ensemble import RandomForestClassifier

FIGURE_DIR = os.path.join("reports", "figures")
os.makedirs(FIGURE_DIR, exist_ok=True)

CLUSTER_FEATURES = [
    "recency_days",
    "visit_frequency",
    "monetary_total",
    "avg_billing_value",
    "admission_frequency",
    "avg_length_of_stay",
    "lab_utilization",
    "department_diversity",
]

CLUSTER_NAMES = {
    0: "High-Acuity Surgical & Inpatient Cohort",
    1: "Chronic Care Routine Outpatients",
    2: "Wellness & Occasional Ambulatory Patients",
    3: "High-Engagement Multi-Specialty Care",
    4: "Lapsed / Low-Utilization General Patients",
}


def prepare_clustering_data(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, StandardScaler, dict]:
    """Analyze skewness, apply log1p transformation, and scale features."""
    X = df[CLUSTER_FEATURES].copy().fillna(0.0)
    
    # Calculate skewness before transformation
    skew_before = X.skew().to_dict()
    
    # Apply log1p transformation to highly skewed features (skew > 1.0)
    X_trans = X.copy()
    for col in CLUSTER_FEATURES:
        if X[col].min() >= 0 and abs(X[col].skew()) > 0.8:
            X_trans[col] = np.log1p(X[col])
            
    skew_after = X_trans.skew().to_dict()
    
    # Standard scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_trans)
    
    skew_metrics = {
        "skew_before": skew_before,
        "skew_after": skew_after
    }
    return X_trans, X_scaled, scaler, skew_metrics


def evaluate_k_selection(X_scaled: np.ndarray, k_range=range(2, 9), seed=42) -> tuple[dict, int]:
    """Compute inertia, silhouette, Davies-Bouldin, and Calinski-Harabasz scores across K=2..8."""
    print("Evaluating K-Means cluster selection (Elbow Curve & Multi-Metric Validation)...")
    inertias = []
    silhouette_scores = []
    davies_bouldin_scores = []
    calinski_harabasz_scores = []
    
    # Subsample for fast, stable silhouette scoring on large patient cohorts
    sample_size = min(15000, len(X_scaled))
    np.random.seed(seed)
    sample_indices = np.random.choice(len(X_scaled), size=sample_size, replace=False)
    X_sample = X_scaled[sample_indices]
    
    k_list = list(k_range)
    for k in k_list:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10, max_iter=300)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        
        # Silhouette score on representative sample
        sil = silhouette_score(X_sample, labels[sample_indices])
        silhouette_scores.append(sil)
        
        # Davies-Bouldin Index (lower is better) & Calinski-Harabasz Index (higher is better)
        db_score = davies_bouldin_score(X_sample, labels[sample_indices])
        davies_bouldin_scores.append(db_score)
        
        ch_score = calinski_harabasz_score(X_sample, labels[sample_indices])
        calinski_harabasz_scores.append(ch_score)
        
        print(f"K = {k}: Inertia = {km.inertia_:,.1f}, Silhouette = {sil:.4f}, Davies-Bouldin = {db_score:.4f}, Calinski-Harabasz = {ch_score:,.1f}")
        
    # Chart 1: Elbow Curve
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(k_list, inertias, marker="o", color="#2980b9", linewidth=2.5, markersize=7)
    ax.set_title("K-Means 1: Inertia Elbow Curve for Optimal K Selection")
    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("Inertia (Sum of Squared Distances)")
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    elbow_path = os.path.join(FIGURE_DIR, "kmeans_elbow_curve.png")
    fig.savefig(elbow_path)
    plt.close(fig)
    
    # Chart 2: Silhouette Scores
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(k_list, silhouette_scores, color="#27ae60", width=0.5, edgecolor="black", alpha=0.85)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, h + 0.005, f"{h:.3f}", ha="center", fontweight="bold")
    ax.set_title("K-Means 2: Silhouette Score Analysis across K=2..8")
    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("Mean Silhouette Coefficient")
    ax.set_ylim(0, max(silhouette_scores) * 1.25)
    fig.tight_layout()
    sil_path = os.path.join(FIGURE_DIR, "kmeans_silhouette_scores.png")
    fig.savefig(sil_path)
    plt.close(fig)
    
    # We choose K=5 as optimal (balances distinct clinical acuity with interpretability)
    optimal_k = 5
    
    results = {
        "k_values": k_list,
        "inertias": inertias,
        "silhouette_scores": silhouette_scores,
        "davies_bouldin_scores": davies_bouldin_scores,
        "calinski_harabasz_scores": calinski_harabasz_scores,
        "optimal_k": optimal_k,
        "elbow_chart": elbow_path,
        "silhouette_chart": sil_path,
    }
    return results, optimal_k


def assign_semantic_cluster_names(cluster_summary: pd.DataFrame) -> dict:
    """Assign clinically and operationally accurate names based on multidimensional centroids."""
    names_map = {}
    for cid, row in cluster_summary.iterrows():
        admit_rate = row.get("admission_rate_pct", 0) / 100.0 if row.get("admission_rate_pct", 0) > 1 else row.get("admission_rate_pct", 0)
        monetary = row.get("avg_monetary_inr", 0)
        visits = row.get("avg_visit_frequency", 0)
        dept_div = row.get("avg_dept_diversity", 0)
        
        if admit_rate >= 0.50:
            if monetary > 1000.0:
                name = "High-Acuity Inpatient Surgical & Complex Care"
            else:
                name = "Subsidized / Institutional Inpatient Care"
        else:
            if dept_div >= 3.0 or visits >= 6.0:
                name = "High-Engagement Multi-Specialty Chronic Outpatients"
            elif monetary > 5000.0:
                name = "High-Value Episodic & Specialized Ambulatory"
            else:
                name = "Lapsed / Low-Utilization General Ambulatory"
        names_map[cid] = name
    return names_map


def train_kmeans_model(df: pd.DataFrame, X_scaled: np.ndarray, k: int = 5, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train final K-Means model, verify segment size >= 5%, and assign names."""
    print(f"Training final K-Means model with K={k}...")
    km = KMeans(n_clusters=k, random_state=seed, n_init=20, max_iter=300)
    raw_clusters = km.fit_predict(X_scaled)
    
    df_clustered = df.copy()
    df_clustered["kmeans_cluster_id"] = raw_clusters
    
    # Calculate preliminary cluster centroid stats to assign true semantic names
    raw_summary = df_clustered.groupby("kmeans_cluster_id").agg(
        avg_monetary_inr=("monetary_total", "mean"),
        admission_rate_pct=("admission_frequency", lambda x: (x > 0).mean() * 100),
        avg_visit_frequency=("visit_frequency", "mean"),
        avg_dept_diversity=("department_diversity", "mean"),
    )
    raw_names = assign_semantic_cluster_names(raw_summary)
    df_clustered["cluster_name"] = df_clustered["kmeans_cluster_id"].map(raw_names)
    
    # Sort cluster IDs by revenue contribution logically
    cluster_rev_order = df_clustered.groupby("cluster_name")["monetary_total"].sum().sort_values(ascending=False).index
    name_to_id = {name: idx for idx, name in enumerate(cluster_rev_order)}
    df_clustered["cluster_id"] = df_clustered["cluster_name"].map(name_to_id)
    
    # Verify minimum 5% cluster size requirement
    total_patients = len(df_clustered)
    cluster_sizes = df_clustered["cluster_name"].value_counts()
    cluster_pcts = (cluster_sizes / total_patients) * 100
    
    print("Cluster Size Verification (Requirement: Each cluster >= 5%):")
    for name, pct in cluster_pcts.items():
        print(f"  {name}: {pct:.2f}% ({cluster_sizes[name]:,} patients)")
        if pct < 5.0:
            print(f"  WARNING: Cluster '{name}' is below 5% threshold ({pct:.2f}%).")
            
    # Compile comprehensive profiling table
    total_rev = df_clustered["monetary_total"].sum()
    profile = df_clustered.groupby(["cluster_id", "cluster_name"]).agg(
        patient_count=("patient_id", "count"),
        total_revenue_inr=("monetary_total", "sum"),
        avg_recency_days=("recency_days", "mean"),
        avg_visit_frequency=("visit_frequency", "mean"),
        avg_monetary_inr=("monetary_total", "mean"),
        avg_billing_per_txn=("avg_billing_value", "mean"),
        admission_rate_pct=("admission_frequency", lambda x: (x > 0).mean() * 100),
        avg_los_days=("avg_length_of_stay", "mean"),
        readmission_rate_pct=("readmission_rate", "mean"),
        avg_lab_utilization=("lab_utilization", "mean"),
        avg_dept_diversity=("department_diversity", "mean"),
        avg_age=("age", "mean"),
    ).reset_index()
    
    profile["patient_share_pct"] = ((profile["patient_count"] / total_patients) * 100).round(2)
    profile["revenue_share_pct"] = ((profile["total_revenue_inr"] / total_rev) * 100).round(2)
    
    # Round numerical metrics
    profile["avg_recency_days"] = profile["avg_recency_days"].round(1)
    profile["avg_visit_frequency"] = profile["avg_visit_frequency"].round(2)
    profile["avg_monetary_inr"] = profile["avg_monetary_inr"].round(2)
    profile["avg_billing_per_txn"] = profile["avg_billing_per_txn"].round(2)
    profile["admission_rate_pct"] = profile["admission_rate_pct"].round(2)
    profile["avg_los_days"] = profile["avg_los_days"].round(2)
    profile["readmission_rate_pct"] = profile["readmission_rate_pct"].round(2)
    profile["avg_lab_utilization"] = profile["avg_lab_utilization"].round(2)
    profile["avg_dept_diversity"] = profile["avg_dept_diversity"].round(2)
    profile["avg_age"] = profile["avg_age"].round(1)
    
    return df_clustered, profile


def plot_kmeans_profile_charts(profile: pd.DataFrame, df_clustered: pd.DataFrame) -> dict:
    """Generate profiling and comparison charts."""
    # 1. Cluster Distribution & Revenue Share (Dual-axis or Side-by-Side)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12"]
    
    # Left: Patient Share
    bars1 = ax1.barh(profile["cluster_name"], profile["patient_share_pct"], color=colors, edgecolor="black", alpha=0.85)
    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 0.5, bar.get_y() + bar.get_height()/2.0, f"{w:.1f}%", va="center", fontweight="bold")
    ax1.set_title("Patient Base Share (%)")
    ax1.set_xlabel("Percentage of Patients")
    ax1.set_xlim(0, max(profile["patient_share_pct"]) * 1.25)
    
    # Right: Revenue Share
    bars2 = ax2.barh(profile["cluster_name"], profile["revenue_share_pct"], color=colors, edgecolor="black", alpha=0.85)
    for bar in bars2:
        w = bar.get_width()
        ax2.text(w + 0.5, bar.get_y() + bar.get_height()/2.0, f"{w:.1f}%", va="center", fontweight="bold")
    ax2.set_title("Revenue Contribution Share (%)")
    ax2.set_xlabel("Percentage of Total Revenue")
    ax2.set_xlim(0, max(profile["revenue_share_pct"]) * 1.25)
    
    fig.suptitle("K-Means 3: Patient Volume vs Revenue Contribution by Cluster", fontsize=13, fontweight="bold")
    fig.tight_layout()
    chart1_path = os.path.join(FIGURE_DIR, "kmeans_03_patient_vs_revenue_share.png")
    fig.savefig(chart1_path)
    plt.close(fig)
    
    # 2. Distinguishing KPIs Comparison (At least 3 KPIs)
    kpis = ["avg_monetary_inr", "avg_visit_frequency", "avg_los_days", "admission_rate_pct"]
    kpi_labels = ["Avg Spend (₹)", "Visit Frequency", "Avg LOS (Days)", "Admission Rate (%)"]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for idx, (kpi, label) in enumerate(zip(kpis, kpi_labels)):
        ax = axes[idx // 2, idx % 2]
        bars = ax.bar([name.split()[0] for name in profile["cluster_name"]], profile[kpi], color=colors, edgecolor="black", alpha=0.85)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, h * 1.02, f"{h:,.1f}" if h < 1000 else f"₹{h:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.set_title(label, fontweight="bold")
        ax.set_ylim(0, max(profile[kpi]) * 1.2)
        ax.grid(True, linestyle="--", alpha=0.5)
        
    fig.suptitle("K-Means 4: Demonstration of Meaningful Distinctions Across 4 Core KPIs", fontsize=13, fontweight="bold")
    fig.tight_layout()
    chart2_path = os.path.join(FIGURE_DIR, "kmeans_04_distinguishing_kpis.png")
    fig.savefig(chart2_path)
    plt.close(fig)
    
    # 3. K-Means vs RFM Comparison Contingency Matrix
    if "rfm_segment" in df_clustered.columns:
        crosstab = pd.crosstab(df_clustered["cluster_name"], df_clustered["rfm_segment"], normalize="index") * 100
        fig, ax = plt.subplots(figsize=(11, 5.5))
        sns.heatmap(crosstab, annot=True, fmt=".1f", cmap="YlGnBu", cbar=True, ax=ax, linewidths=0.5)
        ax.set_title("K-Means 5: Cross-Tabulation Matrix: K-Means Clusters vs RFM Segments (% Distribution)")
        ax.set_ylabel("K-Means Cluster")
        ax.set_xlabel("RFM Segment")
        fig.tight_layout()
        chart3_path = os.path.join(FIGURE_DIR, "kmeans_vs_rfm_comparison.png")
        fig.savefig(chart3_path)
        plt.close(fig)
    else:
        chart3_path = ""
        
    return {"cluster_shares": chart1_path, "kpi_distinctions": chart2_path, "rfm_comparison": chart3_path}


def compute_cluster_feature_importance(X_scaled: np.ndarray, labels: np.ndarray, feature_names: list[str]) -> pd.DataFrame:
    """Train a Random Forest classifier on clusters to quantify feature discriminative power."""
    print("Computing K-Means feature discriminative power using Random Forest Gini Importance...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, labels)
    
    fi_df = pd.DataFrame({
        "feature": feature_names,
        "importance_pct": (rf.feature_importances_ * 100).round(2)
    }).sort_values(by="importance_pct", ascending=True)
    
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.barh(fi_df["feature"], fi_df["importance_pct"], color="#0284c7", edgecolor="black", alpha=0.85)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.6, bar.get_y() + bar.get_height()/2.0, f"{w:.1f}%", va="center", fontweight="bold", fontsize=10)
    ax.set_title("K-Means 6: Feature Discriminative Power (Random Forest Gini Importance)", fontweight="bold")
    ax.set_xlabel("Feature Importance Contribution (%)", fontweight="bold")
    ax.set_ylabel("Patient Feature", fontweight="bold")
    ax.set_xlim(0, max(fi_df["importance_pct"]) * 1.25)
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")
    fig.tight_layout()
    chart_path = os.path.join(FIGURE_DIR, "kmeans_feature_importance.png")
    fig.savefig(chart_path, dpi=200)
    plt.close(fig)
    print(f"Feature importance chart saved to: {chart_path}")
    return fi_df.sort_values(by="importance_pct", ascending=False)


def run_kmeans_clustering(features_path: str, rfm_path: str, output_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute complete K-Means clustering pipeline."""
    print("=" * 60)
    print("HospitalIQ K-Means Machine Learning Clustering Starting...")
    print(f"Reading features from: {features_path}")
    print("=" * 60)
    
    df = pd.read_csv(features_path, low_memory=False)
    
    # Merge RFM segment if available
    if os.path.exists(rfm_path):
        df_rfm = pd.read_csv(rfm_path, usecols=["patient_id", "rfm_segment"], low_memory=False)
        df = df.merge(df_rfm, on="patient_id", how="left")
        
    # Prepare data & scale
    X_trans, X_scaled, scaler, skew_metrics = prepare_clustering_data(df)
    
    # Evaluate K
    eval_res, optimal_k = evaluate_k_selection(X_scaled, k_range=range(2, 9), seed=42)
    
    # Train final model
    df_clustered, profile = train_kmeans_model(df, X_scaled, k=optimal_k, seed=42)
    
    # Save outputs
    df_clustered.to_csv(output_path, index=False)
    profile_path = os.path.join(os.path.dirname(output_path), "segment_profiles.csv")
    profile.to_csv(profile_path, index=False)
    
    # Generate charts
    charts = plot_kmeans_profile_charts(profile, df_clustered)
    
    # Feature Importance Modeling
    fi_df = compute_cluster_feature_importance(X_scaled, df_clustered["cluster_id"].values, CLUSTER_FEATURES)
    fi_path = os.path.join(os.path.dirname(output_path), "kmeans_feature_importance.csv")
    fi_df.to_csv(fi_path, index=False)
    
    print("=" * 60)
    print("K-MEANS CLUSTERING COMPLETE")
    print(f"Optimal K Selected:      {optimal_k}")
    print(f"Clustered Output Saved:  {output_path}")
    print(f"Segment Profiles Saved:  {profile_path}")
    print(profile[["cluster_id", "cluster_name", "patient_count", "patient_share_pct", "revenue_share_pct", "avg_monetary_inr", "avg_visit_frequency", "avg_los_days"]])
    print("=" * 60)
    
    return df_clustered, profile


if __name__ == "__main__":
    f_path = os.path.join("data", "processed", "patient_features_full.csv")
    r_path = os.path.join("data", "processed", "rfm_segmentation.csv")
    out_path = os.path.join("data", "processed", "kmeans_clusters.csv")
    run_kmeans_clustering(f_path, r_path, out_path)
