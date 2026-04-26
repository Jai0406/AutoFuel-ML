from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI(title="Fuel Predictor Backend")

# Agar model load na ho toh app start hi nahi hogi (silent fail nahi)

try:
    model = joblib.load('fuel_consumption_modelv1.pkl')
    imputer = joblib.load('imputerv1.pkl')
    
    # SAFEGUARD: Model ke actual feature names yahan se milenge
    # Agar model ke paas feature_names_in_ hai (sklearn >= 1.0), use karo
    if hasattr(model, 'feature_names_in_'):
        EXPECTED_COLUMNS = list(model.feature_names_in_)
        print(f"✅ Model loaded. Expected columns ({len(EXPECTED_COLUMNS)}): {EXPECTED_COLUMNS}")
    else:
        EXPECTED_COLUMNS = None
        print("⚠️ Model does not have feature_names_in_. Proceeding with manual column list.")
        
except Exception as e:
    raise RuntimeError(f"CRITICAL: Model loading failed → {e}")


#  Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Pydantic schema — frontend ke variables se match karta hai
class VehicleData(BaseModel):
    ec: float
    m_kg: float
    ewltp: float
    ft: str          # e.g., "petrol", "diesel", "electric", "lpg", etc.
    ep: float
    mt: float
    erwltp: float
    fm: str          # e.g., "M", "E", "P", "H", "F", "B"
    electric_range: float
    z_wh: float


def build_input_dict(data: VehicleData) -> dict:
    
    # Numeric features (training ke column names se exactly match)
    input_dict = {
        'm (kg)':              data.m_kg,
        'Mt':                  data.mt,
        'Ewltp (g/km)':        data.ewltp,
        'ec (cm3)':            data.ec,
        'ep (KW)':             data.ep,
        'z (Wh/km)':           data.z_wh,
        'Erwltp (g/km)':       data.erwltp,
        'Electric range (km)': data.electric_range,
    }
    
    # ── Electric/hybrid nahi hai toh battery values 0
    if data.ft not in ['electric', 'petrol/electric', 'diesel/electric']:
        input_dict['Electric range (km)'] = 0.0
        input_dict['z (Wh/km)'] = 0.0
    
    ft_columns = [
        'Ft_PETROL',           
        'Ft_PETROL/ELECTRIC',
        'Ft_diesel',
        'Ft_diesel/electric',
        'Ft_e85',
        'Ft_electric',
        'Ft_hydrogen',
        'Ft_lpg',
        'Ft_ng',
        'Ft_petrol',
        'Ft_petrol/electric',
    ]
    for col in ft_columns:
        input_dict[col] = False
    
    # Frontend se jo value aayi hai uske hisaab se column True karo
    ft_col = f'Ft_{data.ft}'
    if ft_col in input_dict:
        input_dict[ft_col] = True
    else:
        # Agar koi match nahi mila toh 400 error do
        raise ValueError(
            f"Fuel type '{data.ft}' ke liye koi column nahi mila. "
            f"Valid values: petrol, diesel, electric, lpg, petrol/electric, "
            f"diesel/electric, hydrogen, ng"
        )
    
    # ── Fm one-hot columns ──
    # 'Fm_B' DROP FIRST hai (reference category) isliye nahi hai.
    fm_columns = ['Fm_E', 'Fm_F', 'Fm_H', 'Fm_M', 'Fm_P']
    for col in fm_columns:
        input_dict[col] = False
    
    fm_col = f'Fm_{data.fm}'
    if fm_col in input_dict:
        input_dict[fm_col] = True
    elif data.fm != 'B':  # 'B' reference category hai, saare False rehne dena sahi hai
        raise ValueError(
            f"Drive mode '{data.fm}' ke liye koi column nahi mila. "
            f"Valid values: M, E, P, H, F, B"
        )
    
    return input_dict


@app.post("/predict")
def predict(data: VehicleData):
    
    # Step 1: Input dict banao (user input validation — 400 error)
    try:
        input_dict = build_input_dict(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Step 2: Model se prediction lo (server-side error — 500 error)
    try:
        input_df = pd.DataFrame([input_dict])
        
        # Agar model ke paas feature names hain toh column order match karo
        if EXPECTED_COLUMNS is not None:
            # Missing columns ko False se fill karo, extra columns drop karo
            for col in EXPECTED_COLUMNS:
                if col not in input_df.columns:
                    input_df[col] = False
            input_df = input_df[EXPECTED_COLUMNS]
        
        input_ready = imputer.transform(input_df)
        prediction_l_100km = model.predict(input_ready)[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction error: {str(e)}")
    
    # Step 3: Result format karo
    if prediction_l_100km > 0:
        prediction_kml = 100 / prediction_l_100km
        display_text = f"{prediction_kml:.2f} km/l"
    else:
        display_text = "EV (No Fuel)"
    
    return {"result_text": display_text}