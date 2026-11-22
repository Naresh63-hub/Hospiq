"""HospitalIQ Segment Business Recommendations and Strategic Action Plans.

Provides concrete, financially transparent, ethical, and clinically grounded
action plans for every patient segment with transparent ROI assumptions,
implementation costs, expected benefits, and measurable target KPIs.
"""

import os
import pandas as pd

RECOMMENDATIONS = [
    {
        "segment_id": 1,
        "segment_name": "High-Value Active Patients",
        "characteristics": "High frequency (avg 7.8 visits), high monetary contribution (avg ₹48,500), recent visits (<45 days), multi-specialty surgical and inpatient utilization.",
        "business_problem": "Risk of fragmented care coordination across departments, physician burnout, and operational wait-time dissatisfaction leading to hospital switching.",
        "recommended_action": "Dedicated Care Concierge & Longitudinal Care Pathway: Assign specialized care navigators for seamless multidisciplinary consults, priority bed allocation, and expedited digital discharge.",
        "estimated_cost_inr": 1850000,
        "cost_breakdown": "₹14,00,000 (2 Senior Care Navigators across 4 hospitals) + ₹4,50,000 (Care management portal integration).",
        "expected_benefit_inr": 4200000,
        "benefit_breakdown": "Avoided patient churn (+8% retention in high-tier cohort) yielding ₹42,00,000 in retained surgical/inpatient contribution.",
        "measurement_kpi": "12-Month Cohort Retention Rate & Patient NPS",
        "target_value": "Retention >= 85%, Patient NPS >= 75",
        "implementation_period": "6 Months (Q1-Q2 2027)",
        "clinical_safeguards": "Prioritizes clinical continuity without altering care standards based on billing tier."
    },
    {
        "segment_id": 2,
        "segment_name": "Loyal Regular Patients",
        "characteristics": "Chronic disease management (Diabetes, Hypertension, CKD), steady recurring OPD visits (avg 4.2 visits), predictable pharmacy and diagnostic utilization.",
        "business_problem": "Medication non-adherence, appointment fatigue, and missed quarterly diagnostic monitoring leading to avoidable acute disease decompensation.",
        "recommended_action": "Automated Chronic Care Tele-Adherence & Home Diagnostics: Digital pill-reminder WhatsApp integration, nurse-led monthly tele-checkups, and subsidized home phlebotomy sample collection.",
        "estimated_cost_inr": 1200000,
        "cost_breakdown": "₹7,00,000 (WhatsApp/SMS API gateway & triage dashboard) + ₹5,00,000 (Home phlebotomy partner logistics).",
        "expected_benefit_inr": 2850000,
        "benefit_breakdown": "15% increase in diagnostic test compliance generating ₹28,50,000 in incremental lab and consultation revenue.",
        "measurement_kpi": "Quarterly Protocol Adherence & Appointment Compliance Rate",
        "target_value": "Follow-up compliance >= 88%, Diagnostic regularity >= 80%",
        "implementation_period": "4 Months",
        "clinical_safeguards": "Standardized evidence-based chronic care guidelines applied uniformly to all patients."
    },
    {
        "segment_id": 3,
        "segment_name": "Growing Patients",
        "characteristics": "Recent acquisition (<60 days recency), moderate initial spend, expanding department consults (Cardiology, Orthopedics, Medicine).",
        "business_problem": "Lack of structured network orientation; patients use the hospital for a single specialty without awareness of full tertiary capabilities.",
        "recommended_action": "Family Health Navigator & Preventive Onboarding: Digital health portal onboarding offering complimentary annual family health screening vouchers and preventive lifestyle counseling.",
        "estimated_cost_inr": 950000,
        "cost_breakdown": "₹5,50,000 (Digital portal feature roll-out) + ₹4,00,000 (Onboarding health counselors).",
        "expected_benefit_inr": 3100000,
        "benefit_breakdown": "22% conversion to multi-department family care packages, generating ₹31,00,000 over 12 months.",
        "measurement_kpi": "Multi-Department Cross-Consultation Rate",
        "target_value": "Secondary department engagement >= 40% (baseline 21%)",
        "implementation_period": "3 Months",
        "clinical_safeguards": "Screenings follow ICMR preventive health guidelines; no unindicated diagnostic tests."
    },
    {
        "segment_id": 4,
        "segment_name": "Occasional Patients",
        "characteristics": "Episodic acute visits (viral fever, minor trauma, seasonal infections), low frequency (1-2 visits), average recency (120-200 days).",
        "business_problem": "High sensitivity to OPD wait times and perceived administrative friction, resulting in subsequent episodic care being sought at competing neighborhood clinics.",
        "recommended_action": "Smart Triage & Fast-Track Ambulatory Experience: Implement self-service digital token booking, guaranteed <25-minute consultation turnaround, and automated post-recovery SMS check-in.",
        "estimated_cost_inr": 700000,
        "cost_breakdown": "₹4,50,000 (Queue management kiosk software upgrade) + ₹2,50,000 (Outpatient process re-engineering).",
        "expected_benefit_inr": 1950000,
        "benefit_breakdown": "14% increase in repeat episode capture rate over 12 months yielding ₹19,50,000 in outpatient contribution.",
        "measurement_kpi": "Door-to-Doctor Wait Time & Subsequent Episode Network Recapture",
        "target_value": "Wait time < 25 mins, Recapture rate >= 45%",
        "implementation_period": "3 Months",
        "clinical_safeguards": "Emergency cases strictly bypass triage queues based on Manchester Triage System."
    },
    {
        "segment_id": 5,
        "segment_name": "At-Risk Patients",
        "characteristics": "Past high engagement or significant spend, but no network visit in >180 days (>6 months lapse).",
        "business_problem": "Silent attrition due to recovery, out-of-pocket financial burden, or perceived lack of follow-up care, leading to unmonitored chronic disease escalation.",
        "recommended_action": "Clinician-Led Re-Engagement & Wellness Recall: Automated specialist-signed health reminder letters inviting patients for a complimentary annual review or second opinion tele-consult.",
        "estimated_cost_inr": 800000,
        "cost_breakdown": "₹5,00,000 (Specialist tele-consult allocation) + ₹3,00,000 (Automated HIPAA/DISHA-compliant outreach system).",
        "expected_benefit_inr": 3500000,
        "benefit_breakdown": "Reactivation of 16% of lapsed chronic patients generating ₹35,00,000 in preventative follow-up and monitoring care.",
        "measurement_kpi": "90-Day Lapsed Patient Reactivation Rate",
        "target_value": "Reactivation Rate >= 15% within 90 days",
        "implementation_period": "4 Months",
        "clinical_safeguards": "Strict adherence to patient privacy and opt-out preferences under Indian Digital Health standards."
    },
    {
        "segment_id": 6,
        "segment_name": "Low-Engagement Patients",
        "characteristics": "Single visit in past 2 years, lowest spend (avg ₹750), minimal brand attachment, general one-off OPD or health certificate visit.",
        "business_problem": "High customer acquisition cost with virtually zero ongoing engagement or network loyalty.",
        "recommended_action": "Community Health & Preventative Screening Outreach: Partner with local Hyderabad employer wellness days and resident welfare associations (RWAs) for subsidized preventive health camps.",
        "estimated_cost_inr": 650000,
        "cost_breakdown": "₹4,00,000 (Mobile screening camp equipment & logistics) + ₹2,50,000 (Consumables and nursing staff).",
        "expected_benefit_inr": 1500000,
        "benefit_breakdown": "Conversion of 10% of community-screened participants into registered primary care patients.",
        "measurement_kpi": "Community-to-Hospital Primary Care Conversion Rate",
        "target_value": "Primary care conversion >= 10%",
        "implementation_period": "6 Months",
        "clinical_safeguards": "Free basic health counseling; referrals provided based strictly on clinical findings."
    }
]


def get_recommendations_dataframe() -> pd.DataFrame:
    """Return structured recommendations dataframe."""
    return pd.DataFrame(RECOMMENDATIONS)


def save_recommendations_report(output_path: str):
    """Save recommendations as formatted CSV."""
    df = get_recommendations_dataframe()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved recommendations table to: {output_path}")
    return df


if __name__ == "__main__":
    out_file = os.path.join("data", "processed", "business_recommendations.csv")
    save_recommendations_report(out_file)
