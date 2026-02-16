import pandas as pd
import numpy as np
import os

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_data():
    print("Loading data...")
    df_patients = pd.read_csv(os.path.join(DATA_DIR, 'patients.csv'))
    df_diagnoses = pd.read_csv(os.path.join(DATA_DIR, 'diagnoses.csv'))
    return df_patients, df_diagnoses

def calculate_risk_scores(df_patients, df_diagnoses):
    print("Calculating Risk Scores (Charlson Index)...")
    
    # Simplified Charlson Weights
    # In a real job, this dictionary would be much larger!
    CCI_WEIGHTS = {
        'E11': 1,   # Diabetes
        'J45': 1,   # Asthma
        'I10': 1,   # Hypertension
        'M54': 0,   # Back pain (low risk)
        'Z00': 0,   # General Exam
        'J06': 0,   # Acute infection
        'E78': 0    # Hyperlipidemia
    }

    def get_weight(icd_code):
        prefix = str(icd_code)[:3]
        return CCI_WEIGHTS.get(prefix, 0)

    # 1. Apply weights
    df_diagnoses['risk_points'] = df_diagnoses['icd_code'].apply(get_weight)

    # 2. Get unique conditions per patient (don't double count the same disease)
    df_unique = df_diagnoses[['patient_id', 'icd_code', 'risk_points']].drop_duplicates()

    # 3. Sum points
    patient_scores = df_unique.groupby('patient_id')['risk_points'].sum().reset_index()
    patient_scores.rename(columns={'risk_points': 'total_risk_score'}, inplace=True)

    # 4. Merge with all patients
    df_scored = pd.merge(df_patients, patient_scores, on='patient_id', how='left')
    df_scored['total_risk_score'] = df_scored['total_risk_score'].fillna(0)
    
    return df_scored

def segment_population(df):
    print("Segmenting population...")
    def classify(score):
        if score == 0: return 'Healthy'
        if score == 1: return 'Moderate'
        return 'High Risk'
    
    df['risk_segment'] = df['total_risk_score'].apply(classify)
    return df

if __name__ == "__main__":
    # 1. Load
    patients, diagnoses = load_data()
    
    # 2. Calculate
    measure_df = calculate_risk_scores(patients, diagnoses)
    
    # 3. Segment
    final_df = segment_population(measure_df)
    
    # 4. Save
    output_path = os.path.join(DATA_DIR, 'patients_with_scores.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"\nSUCCESS! Analysis complete.")
    print(f"File saved to: {output_path}")
    print("\nRisk Segment Distribution:")
    print(final_df['risk_segment'].value_counts())
