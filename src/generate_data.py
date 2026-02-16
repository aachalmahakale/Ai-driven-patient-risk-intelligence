import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker()
random.seed(42)
np.random.seed(42)

# Configuration
NUM_PATIENTS = 1000
MAX_ENCOUNTERS_PER_PATIENT = 5
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Common ICD-10 Codes (Diagnosis)
ICD_CODES = {
    'E11.9': 'Type 2 diabetes mellitus without complications',
    'I10': 'Essential (primary) hypertension',
    'J45.909': 'Unspecified asthma, uncomplicated',
    'M54.5': 'Low back pain',
    'Z00.00': 'Encounter for general adult medical exam',
    'J06.9': 'Acute upper respiratory infection, unspecified',
    'E78.5': 'Hyperlipidemia, unspecified'
}

# Common CPT Codes (Procedures)
CPT_CODES = {
    '99213': 'Office or other outpatient visit (15 min)',
    '99214': 'Office or other outpatient visit (25 min)',
    '83036': 'Hemoglobin A1C level',
    '80053': 'Comprehensive metabolic panel',
    '71045': 'Radiologic examination, chest; single view',
    '85025': 'Blood count; complete (CBC), automated'
}

def generate_patients(n):
    patients = []
    for i in range(n):
        patients.append({
            'patient_id': f'P{str(i+1).zfill(4)}',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'dob': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'gender': random.choice(['M', 'F'])
        })
    return pd.DataFrame(patients)

def generate_encounters(patients_df):
    encounters = []
    diagnoses = []
    procedures = []
    
    encounter_id_counter = 1
    
    for _, patient in patients_df.iterrows():
        # Determines how many visits this patient had
        num_visits = random.randint(1, MAX_ENCOUNTERS_PER_PATIENT)
        
        # Base date for first visit
        current_date = fake.date_between(start_date='-2y', end_date='today')
        
        for _ in range(num_visits):
            enc_id = f'ENC{str(encounter_id_counter).zfill(6)}'
            encounter_id_counter += 1
            
            # Encounters happen sequentially
            visit_date = current_date + timedelta(days=random.randint(0, 180))
            current_date = visit_date
            
            # Determine encounter type (Inpatient/Outpatient)
            enc_type = random.choice(['Outpatient', 'Outpatient', 'Outpatient', 'Inpatient']) # Weighted heavily to outpatient
            
            encounters.append({
                'encounter_id': enc_id,
                'patient_id': patient['patient_id'],
                'encounter_date': visit_date,
                'encounter_type': enc_type,
                'provider': f'Dr. {fake.last_name()}'
            })
            
            # Generate Diagnoses (1-3 per visit)
            num_diagnoses = random.randint(1, 3)
            selected_icds = random.sample(list(ICD_CODES.keys()), num_diagnoses)
            
            for code in selected_icds:
                diagnoses.append({
                    'encounter_id': enc_id,
                    'patient_id': patient['patient_id'],
                    'icd_code': code,
                    'icd_description': ICD_CODES[code],
                    'diagnosis_priority': 1  # Simplified
                })
                
            # Generate Procedures (1-2 per visit, often related to diagnosis realistically, but random here for simplicity)
            num_procedures = random.randint(1, 2)
            selected_cpts = random.sample(list(CPT_CODES.keys()), num_procedures)
            
            for code in selected_cpts:
                procedures.append({
                    'encounter_id': enc_id,
                    'patient_id': patient['patient_id'],
                    'cpt_code': code,
                    'cpt_description': CPT_CODES[code],
                    'procedure_date': visit_date
                })

    return pd.DataFrame(encounters), pd.DataFrame(diagnoses), pd.DataFrame(procedures)

if __name__ == "__main__":
    print("Generating synthetic healthcare data...")
    
    df_patients = generate_patients(NUM_PATIENTS)
    df_encounters, df_diagnoses, df_procedures = generate_encounters(df_patients)
    
    # Save to CSV
    df_patients.to_csv(os.path.join(DATA_DIR, 'patients.csv'), index=False)
    df_encounters.to_csv(os.path.join(DATA_DIR, 'encounters.csv'), index=False)
    df_diagnoses.to_csv(os.path.join(DATA_DIR, 'diagnoses.csv'), index=False)
    df_procedures.to_csv(os.path.join(DATA_DIR, 'procedures.csv'), index=False)
    
    print(f"Data generation complete! Files saved to {DATA_DIR}")
    print(f"  - Patients: {len(df_patients)}")
    print(f"  - Encounters: {len(df_encounters)}")
    print(f"  - Diagnosis Lines: {len(df_diagnoses)}")
    print(f"  - Procedure Lines: {len(df_procedures)}")
