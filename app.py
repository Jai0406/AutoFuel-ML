import streamlit as st
import requests
import subprocess
import time

API_URL = "http://127.0.0.1:8000"

def ensure_backend_is_running():
    if st.session_state.get("backend_started"):
        return

    try:
        r = requests.get(f"{API_URL}/health", timeout=1)
        if r.status_code == 200:
            st.session_state["backend_started"] = True
            return
    except requests.exceptions.ConnectionError:
        pass

    # Start 
    with st.spinner("⏳ Backend server shuru ho raha hai..."):
        proc = subprocess.Popen(
            ["python", "-m", "uvicorn", "api:app",
             "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        st.session_state["backend_pid"] = proc.pid

        # 15 second polling
        for _ in range(15):
            time.sleep(1)
            try:
                if requests.get(f"{API_URL}/health", timeout=1).status_code == 200:
                    st.session_state["backend_started"] = True
                    return
            except requests.exceptions.ConnectionError:
                continue

    st.error(
        "❌ Backend 15 seconds mein start nahi hua. "
        "Manually run karo: `uvicorn api:app --host 127.0.0.1 --port 8000`"
    )
    st.stop()


ensure_backend_is_running()


st.set_page_config(
    page_title="Pro Fuel Predictor",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}
header    {visibility: hidden;}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 95% !important;
}

/* Predict button */
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
    box-shadow: 0 4px 15px rgba(255,75,75,0.4);
    margin-bottom: 20px;
}
.stButton>button:hover {
    background-color: #ff1c1c !important;
    transform: translateY(-2px);
}

/* Result card */
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


# Header

st.markdown(
    "<h2 style='text-align:left; margin-bottom:0; color:#ff4b4b;'>🏎️ Vehicle Fuel Predictor</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:left; color:#9ca3af; font-size:1rem; margin-bottom:20px;'>"
    "Enter specs of your vehicle.</p>",
    unsafe_allow_html=True,
)

# Layout

left_panel, right_panel = st.columns([1.8, 1], gap="large")

with left_panel:
    st.markdown(
        "<h4 style='color:#e2e8f0; border-bottom:1px solid #3e4253; padding-bottom:10px;'>"
        "Enter Vehicle Specifications</h4>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        ec    = st.number_input("Engine Capacity (cc)",    value=1400.0, step=100.0)
        m_kg  = st.number_input("Vehicle Mass (kg)",       value=1600.0, step=50.0)
        ewltp = st.number_input("CO2 Emissions (g/km)",    value=130.0,  step=10.0)

        ft_map = {
            "Petrol":                   "petrol",
            "Diesel":                   "diesel",
            "Electric":                 "electric",
            "LPG":                      "lpg",
            "Hybrid (Petrol/Electric)": "petrol/electric",
            "Hybrid (Diesel/Electric)": "diesel/electric",
            "Hydrogen":                 "hydrogen",
            "Natural Gas (NG)":         "ng",
        }
        ft_choice = st.selectbox("Fuel Type", options=list(ft_map.keys()))
        ft = ft_map[ft_choice]

    with c2:
        ep     = st.number_input("Engine Power (KW)",      value=110.0,  step=10.0)
        mt     = st.number_input("Gross Weight (kg)",      value=1700.0, step=50.0)
        erwltp = st.number_input("Emission Reduction (g/km)", value=1.56, step=0.1)

        fm_map = {
            "Standard (M)":       "M",
            "Pure Electric (E)":  "E",
            "Plug-in Hybrid (P)": "P",
            "Hybrid (H)":         "H",
            "Flex-Fuel (F)":      "F",
            "Bifuel (B)":         "B",
        }
        fm_choice = st.selectbox("Drive Mode", options=list(fm_map.keys()))
        fm = fm_map[fm_choice]

    st.markdown(
        "<h5 style='color:#9ca3af; margin-top:15px;'>🔋 Battery Details (If Applicable)</h5>",
        unsafe_allow_html=True,
    )
    c3, c4 = st.columns(2, gap="medium")
    is_electric = ft in ["electric", "petrol/electric", "diesel/electric"]

    with c3:
        electric_range = st.number_input(
            "Electric Range (km)",
            value=50.0 if is_electric else 0.0,
            disabled=not is_electric,
        )
    with c4:
        z_wh = st.number_input(
            "Battery Energy (Wh/km)",
            value=150.0 if is_electric else 0.0,
            disabled=not is_electric,
        )


# Results Panel
with right_panel:
    st.markdown(
        "<h4 style='color:#e2e8f0; text-align:center; margin-bottom:25px;'>📊 Results Area</h4>",
        unsafe_allow_html=True,
    )

    if st.button("🚀 Calculate Mileage"):
        payload = {
            "ec": ec, "m_kg": m_kg, "ewltp": ewltp, "ft": ft,
            "ep": ep, "mt": mt,    "erwltp": erwltp, "fm": fm,
            "electric_range": electric_range, "z_wh": z_wh,
        }

        try:
            # FIX: timeout=10 streamlit wont get froze   before backend starts
            response = requests.post(
                f"{API_URL}/predict",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                display_text = response.json()["result_text"]
                st.markdown(f"""
                    <div class="prediction-card">
                        <h4 style="color:#9ca3af; margin-bottom:10px; font-weight:normal;">
                            Predicted Economy
                        </h4>
                        <h1 style="color:#4CAF50; margin-top:0; font-size:3.8rem;
                                   text-shadow:0 0 10px rgba(76,175,80,0.3);">
                            {display_text}
                        </h1>
                        <p style="color:gray; font-size:0.9rem; margin-top:15px;">
                            Based on ML prediction
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                st.balloons()

            elif response.status_code == 400:
                # wrong user input
                st.error(f"⚠️ Input Error: {response.json().get('detail', response.text)}")

            else:
                st.error(f"🔴 Server Error ({response.status_code}): {response.text}")

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout — backend respond nahi kar raha. Dobara try karo.")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Backend se connection nahi hua! App restart karo.")

    else:
        # Default placeholder
        st.markdown("""
            <div class="prediction-card" style="border-style:dashed;">
                <h4 style="color:#5e6278; margin-bottom:10px; font-weight:normal;">
                    Waiting for input...
                </h4>
                <h1 style="color:#3e4253; margin-top:0; font-size:3rem;">
                    -- km/l
                </h1>
            </div>
        """, unsafe_allow_html=True)