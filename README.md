# AI-Driven Patient Risk Intelligence 🩺

> **Bridging Clinical Care & Data Science**

##  Project Overview
Healthcare providers are overwhelmed with data but starved for actionable insights. **AI-Driven Patient Risk Intelligence** is a unified dashboard that transforms raw medical billing codes (ICD-10 & CPT) into a comprehensive, predictive view of patient health.

Built with a focus on **Precision Medicine**, this tool stratifies patient populations by risk, visualizes financial impact, and uses AI to generate simulated clinical care plans.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

---

##  Key Features

### 1. Population Health Command Center 
- **Real-Time Risk Stratification:** instantly identifies High, Moderate, and Healthy cohorts (e.g., "18.7% High Risk").
- **Financial Forecasting:** Projects revenue ($3.2M) based on standard Medicare CPT fee schedules.
- **Top Condition Analysis:** Visualizes the prevalence of chronic drivers like Hypertension and Diabetes using ICD-10 data.

### 2. AI-Powered Patient 360° 
- **Clinical Summary Generation:** Transforms structured data into a narrative clinical summary for rapid review.
- **Patient Journey Timeline:** Interactive visualization of a patient's encounter history (ER visits vs. Checkups).
- **Care Gap Detection:** deterministic rules engine flags missing standard-of-care procedures (e.g., missing HbA1c for diabetics).

### 3. Predictive Risk Simulator 
- **Interactive "What-If" Analysis:** Clinicians can simulate interventions (Medication Adherence, Lifestyle Changes) using sliders.
- **Dynamic Modeling:** The Radar Chart updates in real-time to show the *projected* reduction in Utilization and Clinical Risk.

---

##  Technical Architecture

### Tech Stack
- **Frontend / UI:** [Streamlit](https://streamlit.io/) (Python-based web framework)
- **Data Processing:** [Pandas](https://pandas.pydata.org/) (Relational joins on ICD/CPT datasets)
- **Visualization:** [Plotly](https://plotly.com/) (Interactive Radar & Donut Charts) & [TailwindCSS](https://tailwindcss.com/) (Styling)
- **Logic Engine:** Deterministic rule-based algorithms for Risk Scoring & Gap Analysis.

### Data Logic
The system integrates three core datasets:
1.  **Enriched Patient Data:** Demographics + calculated Risk Scores.
2.  **Diagnoses (ICD-10):** Clinical conditions linked via `patient_id`.
3.  **Procedures (CPT):** Medical actions & billing codes for accurate cost estimation.

---

##  How to Run Locally

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/patient-risk-analytics.git
    cd patient-risk-analytics
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Dashboard**
    ```bash
    python -m streamlit run src/app.py
    ```

---

##  Future Roadmap
- [ ] **EHR Integration:** Connect to Epic/Cerner via FHIR standards.
- [ ] **Genomic Risk Scoring:** Incorporate Polygenic Risk Scores (PRS) for personalized medicine.
- [ ] **RAG Implementation:** Upgrade AI summary to use Retrieval-Augmented Generation on unstructured clinical notes.

---

##  Author
**Aachal**  
*B.Pharm | MS in Bioinformatics & Data Science*  
Passionate about leveraging data to improve patient outcomes.
