from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator,model_validator
import pandas as pd
import joblib

app = FastAPI(title="Fuel Predictor Backend")

# ── Step 1: Model Loading (Initialization) ──
try:
    model = joblib.load('fuel_consumption_modelv1.pkl')
    imputer = joblib.load('imputerv1.pkl')
    
    # Imputer se expected columns nikal rahe hain
    if hasattr(imputer, 'feature_names_in_'):
        EXPECTED_COLUMNS = list(imputer.feature_names_in_)
        print(f"✅ Imputer loaded. Expected columns ({len(EXPECTED_COLUMNS)})")
    else:
        EXPECTED_COLUMNS = None
        print("⚠️ Warning: Neither model nor imputer has feature names.")
        
except Exception as e:
    raise RuntimeError(f"CRITICAL: Model loading failed -> {e}")


# ── Step 2: Schemas (The Contract) ──

class VehicleData(BaseModel):
    """Input validation guard"""
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

    # Improvement 1: Field Validators (Bouncer)
    @field_validator('ec', 'm_kg', 'ep', 'mt')
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Values (Engine, Weight, Power) must be strictly positive.")
        return v
    
    @field_validator('ft')
    @classmethod
    def valid_fuel(cls, v):
        valid_fuels = ['petrol', 'diesel', 'electric', 'lpg', 'petrol/electric', 'diesel/electric', 'hydrogen', 'ng']
        if v.lower() not in valid_fuels:
            raise ValueError(f"Invalid Fuel Type. Valid: {valid_fuels}")
        return v.lower()
    
    
    @model_validator(mode='after')
    def validate_ev_logic(self):
        # Yahan 'self' ke paas saari fields ka access hai
        is_electric = self.ft in ['electric', 'petrol/electric', 'diesel/electric']
        
        # Agar gaadi EV/Hybrid nahi hai, par user ne electric range daal di hai
        if not is_electric and self.electric_range > 0:
            raise ValueError(f"Fuel type '{self.ft}' ke liye Electric Range 0 honi chahiye.")
        return self

class PredictionResponse(BaseModel):
    """Improvement 2: Response Model (The Menu Card)"""
    result_text: str
    model_version: str
    status: str


# ── Step 3: Utility Functions ──

def build_input_dict(data: VehicleData) -> dict:
    """Transforming 10 inputs into 24 features"""
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
    
    # EV/Hybrid logic
    if data.ft not in ['electric', 'petrol/electric', 'diesel/electric']:
        input_dict['Electric range (km)'] = 0.0
        input_dict['z (Wh/km)'] = 0.0
    
    # One-Hot Encoding for Fuel Type
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
    
    # One-Hot Encoding for Drive Mode
    fm_columns = ['Fm_E', 'Fm_F', 'Fm_H', 'Fm_M', 'Fm_P']
    for col in fm_columns:
        input_dict[col] = False
    
    fm_col = f'Fm_{data.fm}'
    if fm_col in input_dict:
        input_dict[fm_col] = True
    
    return input_dict


# ── Step 4: Endpoints ──

@app.get("/health")
def health_check():
    """Heartbeat for run.py"""
    return {"status": "ok"}

@app.post("/predict", response_model=PredictionResponse)
def predict(data: VehicleData):
    """Main ML Prediction Pipeline"""
    try:
        # Transformation
        input_dict = build_input_dict(data)
        input_df = pd.DataFrame([input_dict])
        
        # Alignment with 24 columns
        if EXPECTED_COLUMNS is not None:
            for col in EXPECTED_COLUMNS:
                if col not in input_df.columns:
                    input_df[col] = False
            input_df = input_df[EXPECTED_COLUMNS]
        
        # ML Logic
        input_ready = imputer.transform(input_df)
        prediction_l_100km = model.predict(input_ready)[0]
        
        # Unit Conversion
        if prediction_l_100km > 0:
            prediction_kml = 100 / prediction_l_100km
            display_text = f"{prediction_kml:.2f} km/l"
        else:
            display_text = "EV (No Fuel)"
        
        # Improvement 3: Response with Versioning
        return {
            "result_text": display_text,
            "model_version": "v1.0-RandomForest",
            "status": "success"
        }
        
    except ValueError as v_err:
        raise HTTPException(status_code=400, detail=str(v_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")