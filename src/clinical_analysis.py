import pandas as pd
import numpy as np
import os

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_data():
    print("Loading datasets...")
    patients = pd.read_csv(os.path.join(DATA_DIR, 'patients.csv'))
    encounters = pd.read_csv(os.path.join(DATA_DIR, 'encounters.csv'))
    diagnoses = pd.read_csv(os.path.join(DATA_DIR, 'diagnoses.csv'))
    procedures = pd.read_csv(os.path.join(DATA_DIR, 'procedures.csv'))
    
    # Date conversion
    encounters['encounter_date'] = pd.to_datetime(encounters['encounter_date'])
    procedures['procedure_date'] = pd.to_datetime(procedures['procedure_date'])
    
    return patients, encounters, diagnoses, procedures

def calculate_charlson_index(df_patients, df_diagnoses):
    print("Calculating Risk Scores...")
    # Simplified Charlson Weights
    CCI_WEIGHTS = {
        'E11': 1, 'J45': 1, 'I10': 1, 'M54': 0, 'Z00': 0, 'J06': 0, 'E78': 0
    }
    
    def get_weight(icd_code):
        return CCI_WEIGHTS.get(str(icd_code)[:3], 0)

    df_diagnoses['risk_points'] = df_diagnoses['icd_code'].apply(get_weight)
    
    # Sum unique points per patient
    patient_scores = df_diagnoses[['patient_id', 'icd_code', 'risk_points']].drop_duplicates() \
        .groupby('patient_id')['risk_points'].sum().reset_index()
    patient_scores.rename(columns={'risk_points': 'risk_score'}, inplace=True)
    
    return patient_scores

def calculate_care_gaps(df_patients, df_diagnoses, df_procedures):
    print("Calculating Care Gaps (HEDIS Logic)...")
    
    # 1. DENOMINATOR: Patients with Diabetes (E11)
    diabetics = df_diagnoses[df_diagnoses['icd_code'].str.startswith('E11', na=False)]['patient_id'].unique()
    
    # 2. NUMERATOR: Patients with HbA1c Test (83036)
    # Ensure cpt_code is string for comparison
    df_procedures['cpt_code'] = df_procedures['cpt_code'].astype(str)
    tested_patients = df_procedures[df_procedures['cpt_code'] == '83036']['patient_id'].unique()
    
    # 3. Calculate Gaps
    df_gaps = pd.DataFrame({'patient_id': df_patients['patient_id']})
    df_gaps['is_diabetic'] = df_gaps['patient_id'].isin(diabetics)
    df_gaps['has_hba1c_test'] = df_gaps['patient_id'].isin(tested_patients)
    
    # Flag: Diabetic AND NO Test
    df_gaps['care_gap_alert'] = df_gaps['is_diabetic'] & ~df_gaps['has_hba1c_test']
    
    return df_gaps[['patient_id', 'is_diabetic', 'care_gap_alert']]

def calculate_readmissions(df_encounters):
    print("Analyzing 30-Day Readmissions...")
    
    df = df_encounters.sort_values(['patient_id', 'encounter_date']).copy()
    
    # Calculate days since previous visit
    df['prev_date'] = df.groupby('patient_id')['encounter_date'].shift(1)
    df['days_diff'] = (df['encounter_date'] - df['prev_date']).dt.days
    
    # Flag readmissions (< 30 days)
    # We ignore the first visit (NaN days_diff)
    df['is_readmission'] = (df['days_diff'] < 30) & (df['days_diff'].notna())
    
    # Count totals per patient
    readmission_counts = df.groupby('patient_id')['is_readmission'].sum().reset_index()
    readmission_counts.rename(columns={'is_readmission': 'readmission_count'}, inplace=True)
    
    return readmission_counts

if __name__ == "__main__":
    # 1. Load Data
    patients, encounters, diagnoses, procedures = load_data()
    
    # 2. Calculate Metrics
    df_risk = calculate_charlson_index(patients, diagnoses)
    df_gaps = calculate_care_gaps(patients, diagnoses, procedures)
    df_readmits = calculate_readmissions(encounters)
    
    # 3. Merge Everything into one Master Patient Table
    print("Merging metrics...")
    final_df = patients.merge(df_risk, on='patient_id', how='left')
    final_df = final_df.merge(df_gaps, on='patient_id', how='left')
    final_df = final_df.merge(df_readmits, on='patient_id', how='left')
    
    # 4. Fill NaNs
    final_df['risk_score'] = final_df['risk_score'].fillna(0)
    final_df['readmission_count'] = final_df['readmission_count'].fillna(0)
    final_df['is_diabetic'] = final_df['is_diabetic'].fillna(False)
    final_df['care_gap_alert'] = final_df['care_gap_alert'].fillna(False)
    
    # 5. Segment Risk
    def classify(score): 
        if score == 0: return 'Healthy'
        if score == 1: return 'Moderate'
        return 'High Risk'
    final_df['risk_segment'] = final_df['risk_score'].apply(classify)
    
    # 6. Save
    output_path = os.path.join(DATA_DIR, 'patients_enriched.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"\nSUCCESS! Advanced clinical analysis complete.")
    print(f"Readmissions Identified: {final_df['readmission_count'].sum()}")
    print(f"Diabetes Care Gaps Found: {final_df['care_gap_alert'].sum()}")
    print(f"Saved to: {output_path}")
