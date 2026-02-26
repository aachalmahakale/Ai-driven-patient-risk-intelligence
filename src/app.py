import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import plotly.graph_objects as go
from ai_generator import generate_clinical_summary

# --- APP CONFIG ---
st.set_page_config(
    page_title="AI-Driven Patient Risk Intelligence", 
    layout="wide", 
    page_icon="🩺",
    initial_sidebar_state="collapsed"
)

# --- 1. DATA LOADING & PROCESSING ---
# Same logic as before to get Real Numbers
CPT_COSTS = {
    '99213': 92.00, '99214': 128.00, '83036': 16.00,
    '80053': 14.00, '71045': 35.00, '85025': 10.00
}
# Get Data
try:
    # --- INTERACTIVITY: STREAMLIT FILTERS ---
    with st.sidebar:
        st.header("Patient Filters")
        
        # Style filters with some CSS
        st.markdown(
            """
            <style>
            .stMultiSelect [data-baseweb="tag"] {
                background-color: #EFF6FF !important;
                color: #1D4ED8 !important;
                border: 1px solid #BFDBFE;
            }
            .stSelectbox div[data-baseweb="select"] > div {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # 1. Risk Filter
        selected_risk = st.multiselect(
            "Filter by Risk Level",
            options=["High Risk", "Moderate", "Healthy"],
            default=["High Risk", "Moderate", "Healthy"]
        )
        
        # 2. Condition Filter (Top 10 for brevity)
        all_conditions = ["All"] + list(pd.read_csv('data/diagnoses.csv')['icd_description'].value_counts().head(10).index)
        selected_condition = st.selectbox("Filter by Primary Diagnosis", all_conditions)

        st.markdown("---")
        st.header("Downloads")
        
        # 3. CSV Download Setup
        # Prepare the CSV string
        csv_data = pd.read_csv('data/patients_enriched.csv')
        # Filter strictly for HIGH RISK
        high_risk_csv = csv_data[csv_data['risk_segment'] == "High Risk"].to_csv(index=False).encode('utf-8')
        
        with st.container():
            st.markdown(
                """
                <div style="background-color: #EFF6FF; padding: 12px; border-radius: 12px; border: 1px solid #BFDBFE; margin-bottom: 10px;">
                    <h4 style="color: #1E40AF; margin: 0; font-size: 14px; font-weight: 600;">High Risk Cohort</h4>
                    <p style="color: #3B82F6; font-size: 11px; margin: 2px 0 8px 0;">Pre-filtered list of high risk patients.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.download_button(
                label="Download List",
                data=high_risk_csv,
                file_name="high_risk_cohort.csv",
                mime="text/csv",
                key="sidebar_download",
                use_container_width=True
            )

    # --- FILTER LOGIC ---
    # Reload data for filtering
    patients = pd.read_csv('data/patients_enriched.csv')
    procedures = pd.read_csv('data/procedures.csv')
    diagnoses = pd.read_csv('data/diagnoses.csv')
    encounters = pd.read_csv('data/encounters.csv')

    # Apply Risk Filter
    if selected_risk:
        patients = patients[patients['risk_segment'].isin(selected_risk)]
    
    # Apply Diagnosis Filter
    if selected_condition != "All":
        # Find patients who have this diagnosis
        relevant_patients = diagnoses[diagnoses['icd_description'] == selected_condition]['patient_id'].unique()
        patients = patients[patients['patient_id'].isin(relevant_patients)]

    # Filter downstream tables based on remaining patients
    filtered_ids = patients['patient_id'].unique()
    procedures = procedures[procedures['patient_id'].isin(filtered_ids)]
    
    # Check if we should restrict diagnosis view to ONLY the selected one
    # User request: "showing 4 result instaed of one" implies they want to see ONLY the selected diagnosis in the list
    if selected_condition != "All":
        diagnoses = diagnoses[(diagnoses['patient_id'].isin(filtered_ids)) & (diagnoses['icd_description'] == selected_condition)]
    else:
        diagnoses = diagnoses[diagnoses['patient_id'].isin(filtered_ids)]

    # --- RE-CALCULATE METRICS WITH FILTERED DATA ---
    # A. KPI Calculations
    total_pts = len(patients)
    
    # Avoid division by zero
    if total_pts > 0:
        high_risk_pts = len(patients[patients['risk_segment'] == "High Risk"])
        risk_pct = (high_risk_pts / total_pts) * 100
        # Calculate Readmission Rate (Total Readmissions / Total Patients) - illustrative
        readmission_rate = (patients['readmission_count'].sum() / total_pts) * 100
    else:
        risk_pct = 0
        readmission_rate = 0
    
    procedures['estimated_cost'] = procedures['cpt_code'].astype(str).map(CPT_COSTS).fillna(0)
    total_rev = procedures['estimated_cost'].sum()
    
    # B. Risk Stratification Data (Donut Chart)
    risk_counts = patients['risk_segment'].value_counts()
    risk_data = [
        int(risk_counts.get('High Risk', 0)),
        int(risk_counts.get('Moderate', 0)),
        int(risk_counts.get('Healthy', 0))
    ]
    
    # D. New Metrics: Care Gaps & Demographics
    if 'care_gap_alert' in patients.columns:
        care_gaps = int(patients['care_gap_alert'].sum())
    else:
        care_gaps = 0

    # C. Top Conditions (List)
    if not diagnoses.empty:
        # If we selected a condition, 'diagnoses' only has that condition now unless we want co-morbidities
        # User requested ONLY seeing the 1 result.
        # So we just tally up.
        top_dx = diagnoses['icd_description'].value_counts().head(4).reset_index()
        top_dx.columns = ['Condition', 'Count']
    else:
        top_dx = pd.DataFrame(columns=['Condition', 'Count'])
    
    # Format conditions for HTML injection
    conditions_list = []
    
    # Icons mapping
    icons = {
        'Hypertension': 'blood_pressure',
        'Diabetes': 'glucose', 
        'Heart': 'favorite', 
        'Osteoarthritis': 'accessibility_new',
        'Respiratory': 'lungs'
    }
    
    bg_colors = ['bg-orange-100', 'bg-purple-100', 'bg-blue-600', 'bg-green-100']
    text_colors = ['text-orange-600', 'text-purple-600', 'text-white', 'text-green-600']
    
    for i, row in top_dx.iterrows():
        cond_name = row['Condition']
        count = row['Count']
        
        icon = 'local_hospital'
        for key, val in icons.items():
            if key.lower() in cond_name.lower():
                icon = val
                break
        
        is_highlight = (i == 2)
        
        if is_highlight:
            html = f"""
            <div class="flex items-center justify-between group p-3 bg-blue-600 rounded-2xl shadow-lg shadow-blue-200 cursor-pointer transform scale-[1.02]">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center text-white backdrop-blur-sm">
                        <span class="material-symbols-outlined">{icon}</span>
                    </div>
                    <div>
                        <h4 class="text-sm font-bold text-white">{cond_name[:20]}...</h4>
                        <p class="text-xs text-blue-100">Critical Priority</p>
                    </div>
                </div>
                <span class="text-sm font-semibold text-blue-600 bg-white px-2 py-1 rounded-lg shadow-sm">{count}</span>
            </div>
            """
        else:
            bg = bg_colors[i % len(bg_colors)]
            txt = text_colors[i % len(text_colors)]
            
            html = f"""
            <div class="flex items-center justify-between group p-2 hover:bg-gray-50 rounded-2xl transition-colors cursor-pointer">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-2xl {bg} flex items-center justify-center {txt} shadow-sm">
                        <span class="material-symbols-outlined">{icon}</span>
                    </div>
                    <div>
                        <h4 class="text-sm font-bold text-gray-800">{cond_name[:20]}...</h4>
                        <p class="text-xs text-gray-500">Chronic Condition</p>
                    </div>
                </div>
                <span class="text-sm font-semibold text-gray-900 bg-white border border-gray-100 px-2 py-1 rounded-lg shadow-sm">{count}</span>
            </div>
            """
        conditions_list.append(html)

    conditions_html = "".join(conditions_list)

except Exception as e:
    st.error(f"Error loading metrics: {e}")
    st.stop()

st.markdown("""
    <!-- Load Material Symbols Font -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
    <style>
        .block-container { padding: 0 !important; }
        [data-testid="stSidebar"] { display: block; }
        footer { visibility: hidden; }
        /* Fix icon sizing */
        .material-symbols-outlined {
            font-size: 24px !important;
            vertical-align: middle;
        }
    </style>
""", unsafe_allow_html=True)


# --- 3. INJECT DATA INTO HTML ---
# We format the revenue (e.g., 3200000 -> $3.2M)
rev_str = f"${total_rev/1000000:.1f}M"

dashboard_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>AI-Driven Patient Risk Intelligence</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
    
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: "#3B82F6", 
                        "primary-dark": "#2563EB",
                        "accent-blue": "#EFF6FF", 
                        "background-base": "#F3F4F6", 
                        "surface-white": "#FFFFFF",
                        "text-dark": "#111827",
                        "text-gray": "#6B7280",
                        "success": "#10B981",
                        "warning": "#F59E0B",
                        "danger": "#EF4444",
                    }},
                    fontFamily: {{
                        sans: ["Inter", "sans-serif"],
                    }},
                    borderRadius: {{
                        'xl': '1rem',
                        '2xl': '1.5rem',
                        '3xl': '2rem',
                    }},
                    boxShadow: {{
                        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
                        'card': '0 2px 10px rgba(0,0,0,0.02), 0 10px 30px rgba(0,0,0,0.04)',
                        'floating': '0 20px 40px -5px rgba(0, 0, 0, 0.1)',
                    }}
                }},
            }},
        }};
    </script>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #F3F4F6;
            background-image: radial-gradient(at 0% 0%, hsla(219,70%,96%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,90%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,96%,1) 0, transparent 50%);
            background-attachment: fixed;
            overflow-x: hidden;
        }}
        .hotspot-pulse {{
            animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
        }}
        @keyframes pulse-ring {{
            0% {{ transform: scale(0.8); opacity: 0.8; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }}
            70% {{ transform: scale(1); opacity: 0; box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }}
            100% {{ transform: scale(0.8); opacity: 0; }}
        }}
        #root {{ width: 100%; }}
    </style>
</head>
<body class="text-text-dark min-h-screen p-4 md:p-6 lg:p-8 flex flex-col gap-6">

    <!-- Header Navigation -->
    <header class="bg-surface-white/80 backdrop-blur-md rounded-2xl shadow-sm px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-4 z-50 border border-white/50">
        <div class="flex items-center gap-12 w-full md:w-auto">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                    <span class="material-symbols-outlined text-xl">monitor_heart</span>
                </div>
                <span class="text-xl font-bold tracking-tight text-gray-900">AI-Driven Patient Risk Intelligence.</span>
            </div>
            
            <nav class="hidden md:flex items-center bg-gray-100/50 p-1 rounded-xl">
                <a class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all nav-item active flex items-center gap-2" href="#">
                    <span class="material-symbols-outlined text-[18px]">dashboard</span> Dashboard
                </a>
            </nav>
        </div>
        
        <div class="flex items-center gap-4 w-full md:w-auto justify-end">
             <div class="flex items-center gap-3 pl-2 border-l border-gray-200">
                <img alt="Dr. Aachal" class="w-9 h-9 rounded-full object-cover ring-2 ring-white shadow-sm" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDYox-QPisjcuATUi_6UdZ1-3toasfL8o8WfNPtVA9dpH9LUvrcqNmS-DAO0ztpxPLa-ItrJHEjYbbMExlPj7eh-boh-Wi2fnhLycqNEAH_3cP51XDUfQE5ZdY0dgDgn8x6igfQzBCmM4xBdOHL5phFeHmpv48JIc7DHnUKyYWMAXiSQh1uj_0RBdvaVWLRe2NC0n-fKxvpOZajKPlUhYjF5PE6HmWVGPki2YcZOqdqJ0W_cCfxmSw7P30rjPYirCwrOSl5J6q4RLQ"/>
                <div class="hidden xl:block">
                    <p class="text-sm font-bold text-gray-900 leading-tight">Dr. Aachal</p>
                    <p class="text-[11px] text-gray-500 font-medium">Chief Physician</p>
                </div>
            </div>
        </div>
    </header>

    <main class="grid grid-cols-12 gap-6 pb-8">
        <!-- Left Column (Heart Card) -->
        <div class="col-span-12 lg:col-span-5 flex flex-col gap-6">
            <div class="flex flex-col gap-1 pl-2">
                <h1 class="text-3xl font-bold text-gray-900">Good Morning, Aachal</h1>
                <p class="text-gray-500">You have 3 critical alerts pending review today.</p>
            </div>
            
            <!-- THE BIG HEART CARD -->
            <div class="bg-surface-white rounded-3xl shadow-card p-8 flex-1 relative overflow-hidden min-h-[500px] flex items-center justify-center group">
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-red-100 rounded-full blur-3xl opacity-50"></div>
                <div class="relative w-full h-full flex items-center justify-center">
                    <div class="relative w-72 h-72 md:w-96 md:h-96">
                        <img alt="3D Heart Model" class="w-full h-full object-contain drop-shadow-2xl mix-blend-multiply opacity-90 grayscale-[20%] contrast-125 hover:scale-105 transition-transform duration-700" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDP_rpZonJiKYgOiWm9pER_kdS6erljmUUrEzoqc64uw-shRPGB7COfrOk2fEe57CTJ0x-4a8eUykPlohYQlpJkdKD5ckiUFagYifEuFi1DcX4K0r9COHnfIQ9t-on4WJ0W1pg8I8oOoUysWJI1TwaOaH11RmGsy5umBwGTOdMYcpw9n0jG5Yx4xoMmgwY3r4aRqN9YjIw9Hr64Xmyqxrr3NI9khMD6NBSZPZjlXcSsY15LX3BESm52QBxxx_DwXEPnJdufrg0wRHA"/>
                        
                        <!-- Floating Readmission Metric -->
                        <div class="absolute top-[40%] right-[0px] md:right-[-40px] bg-white/80 backdrop-blur-md p-4 rounded-2xl shadow-floating border border-white w-48 animate-bounce" style="animation-duration: 3s;">
                            <div class="flex justify-between items-start mb-2">
                                <div class="flex items-center gap-2">
                                    <div class="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                                        <span class="material-symbols-outlined text-sm">monitor_heart</span>
                                    </div>
                                    <span class="text-xs font-bold text-gray-700">Readmission</span>
                                </div>
                            </div>
                            <div class="flex items-baseline gap-1">
                                <span class="text-2xl font-bold text-gray-900">{readmission_rate:.1f}%</span>
                                <span class="text-[10px] text-red-500 font-medium bg-red-50 px-1.5 py-0.5 rounded-full">High</span>
                            </div>
                            <div class="h-8 w-full mt-2">
                                <canvas id="miniHeartChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right Column: Metrics & Charts -->
        <div class="col-span-12 lg:col-span-7 flex flex-col gap-6">
            
            <!-- Filters -->
            <div class="bg-surface-white p-2 rounded-2xl shadow-sm flex flex-wrap justify-between items-center px-4">
                <div class="flex items-center gap-2">
                    <div class="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg text-sm font-medium text-gray-600">
                        <span class="material-symbols-outlined text-lg">calendar_today</span>
                        <span>Today</span>
                    </div>
                </div>
            </div>

            <!-- Top KPI Cards Row (INJECTED VARIABLES) -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <!-- KPI 1: Patients -->
                <div class="bg-surface-white p-5 rounded-3xl shadow-card border border-gray-100 relative group overflow-hidden">
                    <div class="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Total Patients</p>
                            <div class="flex items-baseline gap-2">
                                <h3 class="text-2xl font-bold text-gray-900">{total_pts:,}</h3>
                                <span class="text-xs font-semibold text-green-500 bg-green-50 px-1.5 py-0.5 rounded">Active</span>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- KPI 2: Risk % -->
                <div class="bg-surface-white p-5 rounded-3xl shadow-card border border-gray-100 relative group overflow-hidden">
                    <div class="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">High Risk %</p>
                            <div class="flex items-baseline gap-2">
                                <h3 class="text-2xl font-bold text-gray-900">{risk_pct:.1f}%</h3>
                                <span class="text-xs font-semibold text-red-500 bg-red-50 px-1.5 py-0.5 rounded">Critical</span>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- KPI 3: Care Gaps (NEW) -->
                <div class="bg-surface-white p-5 rounded-3xl shadow-card border border-gray-100 relative group overflow-hidden">
                    <div class="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Care Gaps Found</p>
                            <div class="flex items-baseline gap-2">
                                <h3 class="text-2xl font-bold text-gray-900">{care_gaps}</h3>
                                <span class="text-xs font-semibold text-orange-500 bg-orange-50 px-1.5 py-0.5 rounded">Action Req</span>
                            </div>
                        </div>
                         <div class="p-2 bg-orange-100 rounded-lg absolute top-4 right-4">
                            <span class="material-symbols-outlined text-orange-600">warning</span>
                        </div>
                    </div>
                    <!-- Small progress bar for gaps -->
                    <div class="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                        <div class="bg-orange-500 h-1.5 rounded-full" style="width: 45%"></div>
                    </div>
                </div>
                <!-- KPI 4: Revenue -->
                <div class="bg-surface-white p-5 rounded-3xl shadow-card border border-gray-100 relative group overflow-hidden">
                    <div class="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Proj. Revenue</p>
                            <div class="flex items-baseline gap-2">
                                <h3 class="text-2xl font-bold text-gray-900">{rev_str}</h3>
                                <span class="text-xs font-semibold text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">+8.4%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>
    </main>

    <script>
        //... charts scripts removed as we cut the HTML early
    </script>
</body>
</html>
"""

# Increase 'height' to ensure no internal scrollbar appears
# 800px should be plenty for the header + heart card + KPIs section
components.html(dashboard_html, height=800, scrolling=False)


# --- 4. MIDDLE SECTION (NATIVE STREAMLIT + PLOTLY) ---
col_mid1, col_mid2 = st.columns(2)

with col_mid1:
    # Stylized Header
    st.markdown("""
    <div style="background: white; padding: 20px; border-radius: 20px 20px 0 0; border-bottom: 1px solid #f3f4f6;">
        <h3 style="margin:0; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #111827; display: flex; align-items: center; gap: 10px;">
            <span style="background: #eff6ff; color: #3b82f6; padding: 8px; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
                <span class="material-symbols-outlined" style="font-size: 20px">medical_services</span>
            </span>
            Top Conditions
        </h3>
    </div>
    <div style="background: white; padding: 20px; border-radius: 0 0 20px 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    """, unsafe_allow_html=True)

    if not top_dx.empty:
        for i, row in top_dx.iterrows():
            cond = row['Condition']
            count = row['Count']
            
            # Icons mapping (simplified)
            icon = 'local_hospital'
            if 'diabetes' in cond.lower(): icon = 'glucose'
            elif 'hypertension' in cond.lower(): icon = 'blood_pressure'
            elif 'heart' in cond.lower(): icon = 'cardiology'
            
            # Styling
            is_top = (i == 0)
            bg_class = "background: #eff6ff; border-left: 4px solid #3b82f6;" if is_top else "background: #f9fafb;"
            text_class = "color: #1e3a8a; font-weight: 700;" if is_top else "color: #374151; font-weight: 600;"
            
            st.markdown(f"""
            <div style="{bg_class} padding: 12px 16px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span class="material-symbols-outlined" style="opacity: 0.7; font-size: 20px;">{icon}</span>
                    <span style="{text_class} font-family: 'Inter', sans-serif; font-size: 0.9rem;">{cond[:25]}{'...' if len(cond)>25 else ''}</span>
                </div>
                <span style="background: white; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; color: #111827; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">{count}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No conditions found for current filters.")

    st.markdown("</div>", unsafe_allow_html=True)

with col_mid2:
    # Stylized Header
    st.markdown("""
    <div style="background: white; padding: 20px; border-radius: 20px 20px 0 0; border-bottom: 1px solid #f3f4f6;">
        <h3 style="margin:0; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #111827; display: flex; align-items: center; gap: 10px;">
            <span style="background: #eef2ff; color: #6366f1; padding: 8px; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
                <span class="material-symbols-outlined" style="font-size: 20px">donut_large</span>
            </span>
            Cohort Risk Distribution
        </h3>
    </div>
    <div style="background: white; padding: 20px; border-radius: 0 0 20px 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    """, unsafe_allow_html=True)

    # Donut Chart (Plotly) - Cleaner visual than Bar for 'Distribution'
    labels = ['High Risk', 'Moderate', 'Healthy']
    values = risk_data
    colors = ['#ef4444', '#f59e0b', '#10b981'] # Red, Yellow, Green

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.6,
        marker=dict(colors=colors),
        textinfo='percent',
        hoverinfo='label+value',
        textfont=dict(size=14, color='white')
    )])

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=0, b=0, l=0, r=0),
        height=260,
        font=dict(family="Inter, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")


# --- AI & INDIVIDUAL ANALYSIS SECTION ---
st.markdown("""
<div style="background: linear-gradient(90deg, #eff6ff 0%, #ffffff 100%); padding: 24px; border-radius: 16px; border: 1px solid #bfdbfe; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <div style="display: flex; align-items: center; gap: 16px;">
        <div style="background: white; padding: 12px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <span class="material-symbols-outlined" style="font-size: 32px; color: #2563eb;">neurology</span>
        </div>
        <div>
            <h2 style="margin:0; font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 700; color: #1e3a8a;">AI-Powered Patient 360°</h2>
            <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 0.95rem;">Real-time clinical summary and predictive risk modeling engine.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Filter to relevant patients based on global filters, sorted by risk
demo_subset = patients.sort_values('risk_score', ascending=False).head(20)
patient_options = demo_subset.apply(lambda x: f"{x['last_name']}, {x['first_name']} (ID: {x['patient_id']}) - {x['risk_segment']}", axis=1).tolist()

col_sel, _ = st.columns([1, 2])
with col_sel:
    selected_patient_str = st.selectbox("Select Patient Record", patient_options)

if selected_patient_str:
    # Extract ID
    selected_id = selected_patient_str.split("(ID: ")[1].split(")")[0]
    patient_row = patients[patients['patient_id'] == selected_id].iloc[0]
    
    # 1. Generate AI Summary
    ai_summary = generate_clinical_summary(patient_row)
    
    # 2. Layout
    p_col1, p_col2 = st.columns([1.6, 1])
    
    with p_col1:
        st.markdown(ai_summary)
        
        # --- NEW: PATIENT JOURNEY TIMELINE ---
        st.markdown("### 📅 Patient Clinical Journey")
        
        # Filter encounters
        pat_encounters = encounters[encounters['patient_id'] == selected_id].copy()
        if not pat_encounters.empty:
            pat_encounters['encounter_date'] = pd.to_datetime(pat_encounters['encounter_date'])
            pat_encounters = pat_encounters.sort_values('encounter_date')
            
            # Create Timeline Plot
            fig_timeline = go.Figure()
            
            # Add trace
            fig_timeline.add_trace(go.Scatter(
                x=pat_encounters['encounter_date'],
                y=pat_encounters['encounter_type'],
                mode='markers+lines',
                marker=dict(size=14, color='#3b82f6', line=dict(width=2, color='white')),
                line=dict(color='#bfdbfe', width=2),
                text=pat_encounters['provider'],
                hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Provider: %{text}<extra></extra>"
            ))
            
            fig_timeline.update_layout(
                xaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
                yaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
                height=250,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("No encounter history found.")

    with p_col2:
        # Stylized Header for Chart
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 20px 20px 0 0; border-bottom: 1px solid #f3f4f6;">
            <h3 style="margin:0; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #111827; display: flex; align-items: center; gap: 10px;">
                <span style="background: #fdf2f8; color: #db2777; padding: 8px; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
                    <span class="material-symbols-outlined" style="font-size: 20px">radar</span>
                </span>
                Risk Simulator
            </h3>
        </div>
        <div style="background: white; padding: 20px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #f3f4f6;">
        """, unsafe_allow_html=True)
        
        # --- NEW: INTERACTIVE SIMULATION SLIDERS ---
        st.markdown("**Simulate Interventions**")
        med_adherence = st.slider("Medication Adherence Improvement", 0, 100, 0, format="+%d%%")
        lifestyle_change = st.slider("Lifestyle Management Index", 0, 50, 0, format="+%d pts")

        # Basic Logic for Values
        risk_val = patient_row['risk_score']
        
        # 1. Current Values
        current_values = [
            risk_val,
            min(risk_val * 1.2, 95),
            min(risk_val * 0.9 + 10, 90),
            80 if patient_row['care_gap_alert'] else 20,
            min(risk_val * 1.1, 85)
        ]
        current_values.append(current_values[0])
        
        # 2. Projected Values (Simulation)
        # Logic: Adherence lowers Utilization & Clinical Risk. Lifestyle lowers Lifestyle Risk & Clinical Risk.
        p_risk = max(10, risk_val - (med_adherence * 0.4) - (lifestyle_change * 0.5))
        p_util = max(10, current_values[1] - (med_adherence * 0.5))
        p_lifestyle = max(10, current_values[4] - (lifestyle_change * 0.8))
        
        projected_values = [
            p_risk,
            p_util,
            current_values[2], # Cost stays roughly same short term
            current_values[3], # Gaps stay same unless closed
            p_lifestyle
        ]
        projected_values.append(projected_values[0])
        
        categories = ['Clinical Risk', 'Utilization', 'Proj. Cost', 'Care Gaps', 'Lifestyle Risk', 'Clinical Risk']
        
        fig = go.Figure()
        
        # Trace 1: Current
        fig.add_trace(go.Scatterpolar(
          r=current_values,
          theta=categories,
          fill='toself',
          name='Current Profile',
          line_color='#ef4444',
          fillcolor='rgba(239, 68, 68, 0.2)'
        ))
        
        # Trace 2: Projected (only if changed)
        if med_adherence > 0 or lifestyle_change > 0:
            fig.add_trace(go.Scatterpolar(
              r=projected_values,
              theta=categories,
              fill='toself',
              name='Simulated Future',
              line_color='#10b981',
              line=dict(dash='dot'),
              fillcolor='rgba(16, 185, 129, 0.1)'
            ))

        fig.update_layout(
          polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
            angularaxis=dict(tickfont=dict(size=10, color='#6b7280')),
            bgcolor='white'
          ),
          showlegend=True,
          legend=dict(orientation="h", y=-0.2), # Legend at bottom
          height=350,
          margin=dict(l=30, r=30, t=10, b=30),
          font=dict(family="Inter, sans-serif")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### High-Risk Cohort Ready")
    st.markdown("Download the latest data set for analysis.")
    
    # Prepare the CSV string specifically for this button
    csv_download = patients.to_csv(index=False).encode('utf-8')
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 24px; border-radius: 16px; color: white; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">Download Analysis Dataset</h3>
                <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.9;">Export the currently filtered patient cohort with all risk scores.</p>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 12px;">
                <span style="font-size: 24px;">📥</span>
            </div>
        </div>
    </div>
    <div style="margin-top: -20px; text-align: right; padding-right: 20px;">
    """, unsafe_allow_html=True)
    
    st.download_button(
        label="Download CSV File",
        data=csv_download,
        file_name="cohort_data.csv",
        mime="text/csv",
        type="primary",
        key="main_download",
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
