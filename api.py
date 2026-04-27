from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI(title="Fuel Predictor Backend")

try:
    model = joblib.load('fuel_consumption_modelv1.pkl')
    imputer = joblib.load('imputerv1.pkl')
    
    # FIX: Model array pe train hua tha isliye usme naam nahi hain.
    # Par IMPUTER dataframe pe train hua tha, toh hum imputer se columns nikalenge
    
    if hasattr(imputer, 'feature_names_in_'):
        EXPECTED_COLUMNS = list(imputer.feature_names_in_)
        print(f"✅ Imputer loaded. Expected columns ({len(EXPECTED_COLUMNS)})")
    else:
        EXPECTED_COLUMNS = None
        print("⚠️ Warning: Neither model nor imputer has feature names.")
        
except Exception as e:
    raise RuntimeError(f"CRITICAL: Model loading failed → {e}")


@app.get("/health")
def health_check():
    return {"status": "ok"}


class VehicleData(BaseModel):
    ec: float
    m_kg: float
    ewltp: float
    ft: str
    ep: float
    mt: float
    erwltp: float
    fm: str
    electric_range: float
    z_wh: float


def build_input_dict(data: VehicleData) -> dict:
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
    
    if data.ft not in ['electric', 'petrol/electric', 'diesel/electric']:
        input_dict['Electric range (km)'] = 0.0
        input_dict['z (Wh/km)'] = 0.0
    
    ft_columns = [
        'Ft_PETROL', 'Ft_PETROL/ELECTRIC', 'Ft_diesel',
        'Ft_diesel/electric', 'Ft_e85', 'Ft_electric',
        'Ft_hydrogen', 'Ft_lpg', 'Ft_ng', 'Ft_petrol', 'Ft_petrol/electric',
    ]
    for col in ft_columns:
        input_dict[col] = False
    
    ft_col = f'Ft_{data.ft}'
    if ft_col in input_dict:
        input_dict[ft_col] = True
    else:
        raise ValueError(
            f"Fuel type '{data.ft}' has no information in data"
            f"Valid: petrol, diesel, electric, lpg, petrol/electric, diesel/electric, hydrogen, ng"
        )
    
    fm_columns = ['Fm_E', 'Fm_F', 'Fm_H', 'Fm_M', 'Fm_P']
    for col in fm_columns:
        input_dict[col] = False
    
    fm_col = f'Fm_{data.fm}'
    if fm_col in input_dict:
        input_dict[fm_col] = True
    elif data.fm != 'B':
        raise ValueError(
            f"Drive mode '{data.fm}' has no information in data. Valid: M, E, P, H, F, B")

    return input_dict


@app.post("/predict")
def predict(data: VehicleData):
    try:
        input_dict = build_input_dict(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        input_df = pd.DataFrame([input_dict])
        
        if EXPECTED_COLUMNS is not None:
            for col in EXPECTED_COLUMNS:
                if col not in input_df.columns:
                    input_df[col] = False
            input_df = input_df[EXPECTED_COLUMNS]
        
        input_ready = imputer.transform(input_df)
        prediction_l_100km = model.predict(input_ready)[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction error: {str(e)}")
    
    if prediction_l_100km > 0:
        prediction_kml = 100 / prediction_l_100km
        display_text = f"{prediction_kml:.2f} km/l"
    else:
        display_text = "EV (No Fuel)"
    
    return {"result_text": display_text}