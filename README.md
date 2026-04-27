# 🏎️ AutoFuel-ML: Advanced Vehicle Fuel Predictor

This repository contains an end-to-end Machine Learning project designed to accurately predict the fuel economy (mileage) of vehicles based on their core specifications, emissions standards, and drive modes. Featuring a highly optimized Random Forest model and a premium split-layout dashboard, this tool handles everything from traditional combustion engines to modern Plug-in Hybrids and EVs.

## 🚀 Project Overview

Predicting real-world fuel consumption is complex due to the variety of fuel types, hybrid technologies, and vehicle weights. This project bridges the gap between raw automotive data and user-friendly insights, providing instant, highly accurate predictions in a format everyday users understand (km/l).

### Key Highlights:
* **High-Precision ML Model:** Utilized a `RandomForestRegressor` that captures complex non-linear relationships between vehicle weight, engine power, and emissions.
* **Smart EV & Hybrid Handling:** Built-in logic to dynamically process Battery Energy (Wh/km) and Electric Range specifically for BEVs and PHEVs, defaulting to zero for standard ICE vehicles.
* **Professional Split-Layout UI:** Developed a responsive Streamlit dashboard featuring a sleek, dark-themed 60/40 split layout. It offers intuitive inputs (hiding technical jargon) and real-time interactive results.
* **Robust Data Pipeline:** Implemented `SimpleImputer` for handling missing real-world data and One-Hot Encoding for diverse fuel modes and types, neatly packaged into serialized `.pkl` files for production.

## 📊 Performance & Metrics

The model was trained and evaluated on a massive dataset of vehicle specifications, achieving exceptional predictive performance:
* **R-squared (R²) Score:** **0.9932 (~99.3%)**, indicating that the model explains almost all the variance in fuel consumption.
* **Mean Absolute Error (MAE):** **0.024**, meaning the predictions are incredibly close to the actual real-world consumption values.
* **Root Mean Squared Error (RMSE):** **0.1469**, showing very low standard deviation in the prediction errors.
* **Feature Importance:** Identified *Drive Mode (Plug-in)*, *CO2 Emissions (Ewltp)*, and *Fuel Type (Diesel/Petrol)* as the strongest predictors of fuel efficiency.

## 🛠️ Tech Stack

* **Language:** Python 3.12+
* **ML Libraries:** Scikit-Learn (Random Forest, SimpleImputer), Pandas, Joblib
* **Visualization & Notebook:** Jupyter Notebook, Matplotlib
* **Backend API:** FastAPI, Uvicorn, Pydantic (Strict Data Validation)
* **Frontend UI:** Streamlit (Custom CSS, responsive grid layouts, requests)

## 💻 Installation & Setup

**1. Clone the repository:**
git clone [https://github.com/Jai0406/AutoFuel-ML.git](https://github.com/Jai0406/AutoFuel-ML.git)
cd AutoFuel-ML


## Create a virtual env.
# Windows
python -m venv myvenv
myvenv\Scripts\activate

# Mac/Linux
python3 -m venv myvenv
source myvenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Application (Orchestrator)
# This single command safely launches both the FastAPI backend and Streamlit frontend.
python run.py


## 📂 Project Structure

### Jai_verma_Fuel_eff_pred.ipynb: The complete research workflow including Data Loading, EDA, Preprocessing (Imputation/Encoding), Random Forest training, and evaluation.

### app.py: The production-ready Streamlit application featuring the premium UI and backend prediction logic.

### run.py: The Master Orchestrator script that safely launches and manages both the backend API and frontend UI processes, ensuring no port-clashing or freezes.

### api.py: The robust FastAPI backend that handles data validation (Pydantic), loads the ML models, and serves the prediction endpoints.

### fuel_consumption_modelv1.pkl: The trained Random Forest model exported for deployment.

### imputerv1.pkl: The fitted SimpleImputer to handle any missing values in real-time user inputs.

### requirements.txt: Manifest of all Python libraries required to run the project.
Developed by @Jai0406