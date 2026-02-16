import pandas as pd
import random
import datetime

def generate_clinical_summary(patient):
    """
    Simulates a GenAI response for a patient care plan.
    """
    first_name = patient['first_name']
    last_name = patient['last_name']
    risk = patient['risk_segment']
    score = patient['risk_score']
    is_diabetic = patient['is_diabetic']
    care_gap = patient['care_gap_alert']
    
    # Dynamic Templates
    intros = [
        f"**Patient Analysis for {first_name} {last_name}:**",
        f"**Clinical Summary: {last_name}, {first_name}**"
    ]
    
    risk_drivers = []
    if is_diabetic:
        risk_drivers.append("uncontrolled metabolic factors")
    if score > 50:
        risk_drivers.append("high historical utilization")
    if care_gap:
        risk_drivers.append("outstanding preventive care gaps")
        
    driver_text = f"The primary drivers for the **{risk}** classification include {', '.join(risk_drivers)}." if risk_drivers else "Patient maintains a stable health profile."
    
    care_plan = []
    if is_diabetic:
        care_plan.append("- **Endocrinology**: Schedule quarterly HbA1c monitoring.")
        care_plan.append("- **Lifestyle**: Referral to nutritional counseling for glycemic control.")
    
    if care_gap:
        care_plan.append("- **Immediate Action**: Close care gap (e.g., Annual Wellness Visit or Cancer Screening).")
        
    if risk == "High Risk":
        care_plan.append("- **Care Management**: Enroll in complex care management program.")
        care_plan.append("- **Telehealth**: Bi-weekly remote monitoring check-ins.")
    elif risk == "Moderate":
        care_plan.append("- **Monitoring**: Standard biannual primary care review.")
    else:
        care_plan.append("- **Prevention**: Continue annual preventive screenings.")

    summary = f"""
### 🤖 AI-Generated Clinical Note

{random.choice(intros)}

**Risk Assessment:**
Patient is currently stratified as **{risk}** (Risk Score: {score}). {driver_text}

**Recommended Care Plan:**
{chr(10).join(care_plan)}

**Predicted Trajectory:**
Without intervention, probability of readmission in next 6 months is estimated at **{min(score * 0.8, 95):.1f}%**. Adherence to the above plan is projected to reduce risk score by 15 points.
    """
    
    return summary
