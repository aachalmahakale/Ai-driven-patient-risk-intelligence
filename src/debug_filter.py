import pandas as pd
import os

# Mock data loading
patients = pd.read_csv('data/patients_enriched.csv')
diagnoses = pd.read_csv('data/diagnoses.csv')

print(f"Total Diagnoses Rows: {len(diagnoses)}")
print(f"Unique Conditions: {diagnoses['icd_description'].nunique()}")

# Simulate Filter - EXACT MATCH IS USED IN APP
selected_condition = "Low back pain"
print(f"\nFiltering by (Exact Match): '{selected_condition}'")

# In App Logic: relevant_patients = diagnoses[diagnoses['icd_description'] == selected_condition]['patient_id'].unique()
relevant_patients_df = diagnoses[diagnoses['icd_description'] == selected_condition]
relevant_patient_ids = relevant_patients_df['patient_id'].unique()
print(f"  -> Found {len(relevant_patient_ids)} patients with this diagnosis.")

if len(relevant_patient_ids) == 0:
    print("  !! ZERO PATIENTS FOUND. Check exact string match.")
    print("  Here are some actual values:")
    print(diagnoses['icd_description'].unique()[:10])

# Filter Patients
patients_filtered = patients[patients['patient_id'].isin(relevant_patient_ids)]
print(f"  -> Patients DF filtered to {len(patients_filtered)} rows.")

# Filter downstream Diagnoses - THIS IS WHERE THE USER ISSUE MIGHT BE
# Does the user want ONLY diagnoses matching the filter, or ALL diagnoses OF patients matching the filter?
# The code does: diagnoses = diagnoses[diagnoses['patient_id'].isin(filtered_ids)] -> ALL diagnoses of these patients.
filtered_ids = patients_filtered['patient_id'].unique()
diagnoses_filtered = diagnoses[diagnoses['patient_id'].isin(filtered_ids)]

print(f"  -> Diagnoses DF filtered to {len(diagnoses_filtered)} rows.")

# Top Conditions
print("\nTop Conditions in Filtered Set:")
print(diagnoses_filtered['icd_description'].value_counts().head(5))
