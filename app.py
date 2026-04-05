import streamlit as st
import pandas as pd
import joblib

# --- 1. Page Configuration & Custom CSS ---
st.set_page_config(page_title="Pro Fuel Predictor", page_icon="🏎️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Default junk hide karna */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top padding ko ekdum kam karna taaki header top corner me set ho */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 95% !important;
    }
    
    /* Premium Predict Button */
    .stButton>button {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 8px !important;
        height: 60px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        transition: 0.3s;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
        margin-bottom: 20px;
    }
    .stButton>button:hover {
        background-color: #ff1c1c !important;
        transform: translateY(-2px);
    }
    
    /* Result Card Styling */
    .prediction-card {
        background-color: #1e2130;
        padding: 30px 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #3e4253;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Load Model & Imputer ---
@st.cache_resource
def load_models():
    model = joblib.load('fuel_consumption_modelv1.pkl')
    imputer = joblib.load('imputerv1.pkl')
    return model, imputer

try:
    model, imputer = load_models()
except Exception as e:
    st.error(f"⚠️ Model cannot be loaded. Error: {e}")

# --- 3. App Header (Top Left Corner) ---
st.markdown("<h2 style='text-align: left; margin-bottom: 0px; color: #ff4b4b;'>🏎️ Vehicle Fuel Predictor</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left; color: #9ca3af; font-size: 1rem; margin-bottom: 20px;'>Enter specs of your vehicle.</p>", unsafe_allow_html=True)

left_panel, right_panel = st.columns([1.8, 1], gap="large")

with left_panel:
    st.markdown("<h4 style='color: #e2e8f0; border-bottom: 1px solid #3e4253; padding-bottom: 10px;'>⚙️ Enter Vehicle Specifications</h4>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2, gap="medium")
    
    with c1:
        ec = st.number_input("Engine Capacity (cc)", value=1400.0, step=100.0)
        m_kg = st.number_input("Vehicle Mass (kg)", value=1600.0, step=50.0)
        ewltp = st.number_input("CO2 Emissions (g/km)", value=130.0, step=10.0)
        
        ft_map = {"Petrol": "petrol", "Diesel": "diesel", "Electric": "electric", "LPG": "lpg", "Hybrid (Petrol/Electric)": "petrol/electric", "Hybrid (Diesel/Electric)": "diesel/electric", "Hydrogen": "hydrogen", "Natural Gas (NG)": "ng"}
        ft_choice = st.selectbox("Fuel Type", options=list(ft_map.keys()))
        ft = ft_map[ft_choice]

    with c2:
        ep = st.number_input("Engine Power (KW)", value=110.0, step=10.0)
        mt = st.number_input("Gross Weight (kg)", value=1700.0, step=50.0)
        erwltp = st.number_input("Emission Reduction (g/km)", value=1.56, step=0.1)
        
        fm_map = {"Standard (M)": "M", "Pure Electric (E)": "E", "Plug-in Hybrid (P)": "P", "Hybrid (H)": "H", "Flex-Fuel (F)": "F", "Bifuel (B)": "B"}
        fm_choice = st.selectbox("Drive Mode", options=list(fm_map.keys()))
        fm = fm_map[fm_choice]

    st.markdown("<h5 style='color: #9ca3af; margin-top: 15px;'>🔋 Battery Details (If Applicable)</h5>", unsafe_allow_html=True)
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        is_electric = ft in ['electric', 'petrol/electric', 'diesel/electric']
        electric_range = st.number_input("Electric Range (km)", value=0.0 if not is_electric else 50.0, disabled=not is_electric)
    with c4:
        z_wh = st.number_input("Battery Energy (Wh/km)", value=0.0 if not is_electric else 150.0, disabled=not is_electric)


with right_panel:
    st.markdown("<h4 style='color: #e2e8f0; text-align: center; margin-bottom: 25px;'>📊 Results Area</h4>", unsafe_allow_html=True)
    
    # Prediction Logic
    if st.button("🚀 Calculate Mileage"):
        
        input_dict = {
            'm (kg)': m_kg, 'Mt': mt, 'Ewltp (g/km)': ewltp, 'ec (cm3)': ec,
            'ep (KW)': ep, 'z (Wh/km)': z_wh, 'Erwltp (g/km)': erwltp,
            'Electric range (km)': electric_range,
            'Ft_PETROL': False, 'Ft_PETROL/ELECTRIC': False, 'Ft_diesel': False,
            'Ft_diesel/electric': False, 'Ft_e85': False, 'Ft_electric': False,
            'Ft_hydrogen': False, 'Ft_lpg': False, 'Ft_ng': False, 'Ft_petrol': False,
            'Ft_petrol/electric': False, 'Fm_E': False, 'Fm_F': False,
            'Fm_H': False, 'Fm_M': False, 'Fm_P': False
        }
        
        if ft not in ['electric', 'petrol/electric', 'diesel/electric']:
            input_dict['Electric range (km)'] = 0.0
            input_dict['z (Wh/km)'] = 0.0
            
        ft_column_name = f'Ft_{ft}'
        if ft_column_name in input_dict:
            input_dict[ft_column_name] = True
            
        fm_column_name = f'Fm_{fm}'
        if fm_column_name in input_dict:
            input_dict[fm_column_name] = True

        input_df = pd.DataFrame([input_dict])
        
        try:
            input_ready = imputer.transform(input_df)
            prediction_l_100km = model.predict(input_ready)[0]
            
            if prediction_l_100km > 0:
                prediction_kml = 100 / prediction_l_100km
                display_text = f"{prediction_kml:.2f} km/l"
            else:
                display_text = "EV (No Fuel)"
            
            st.markdown(f"""
                <div class="prediction-card">
                    <h4 style="color: #9ca3af; margin-bottom: 10px; font-weight: normal;">Predicted Economy</h4>
                    <h1 style="color: #4CAF50; margin-top: 0; font-size: 3.8rem; text-shadow: 0px 0px 10px rgba(76, 175, 80, 0.3);">{display_text}</h1>
                    <p style="color: gray; font-size: 0.9rem; margin-top: 15px;">Based on ML predictionl</p>
                </div>
            """, unsafe_allow_html=True)
            st.balloons() 
                
        except Exception as e:
            st.error(f"Prediction Error: {e}")
            
    else:
        # Default state box
        st.markdown(f"""
            <div class="prediction-card" style="border-style: dashed;">
                <h4 style="color: #5e6278; margin-bottom: 10px; font-weight: normal;">Waiting for input...</h4>
                <h1 style="color: #3e4253; margin-top: 0; font-size: 3rem;">-- km/l</h1>
            </div>
        """, unsafe_allow_html=True)