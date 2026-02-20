import streamlit as st
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="CardioScan · Risk Prediction", layout="wide", page_icon="🫀")

# ─────────────────────────────────────────────
# CUSTOM STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

/* Background radial glow */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(220,38,38,0.15) 0%, #0D0F14 60%);
}

/* Hide default Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero-badge {
    display: inline-block;
    background: rgba(220,38,38,0.15);
    border: 1px solid rgba(220,38,38,0.4);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #F87171;
    margin-bottom: 16px;
}

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(36px, 5vw, 64px);
    font-weight: 400;
    line-height: 1.1;
    letter-spacing: -0.02em;
    margin: 0 0 10px 0;
    color: #F1F5F9;
}

.hero-title span {
    color: #F87171;
}

.hero-subtitle {
    font-size: 15px;
    color: #64748B;
    font-weight: 300;
    margin: 0 0 40px 0;
    max-width: 520px;
}

/* ── Cards ── */
.param-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 28px 24px 20px;
}

.card-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 18px;
}

/* ── Model selector ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #E8EAF0 !important;
}

/* ── Inputs ── */
.stNumberInput > div > div > input,
.stSlider, .stSelectbox {
    color: #E8EAF0 !important;
}

input[type="number"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
}

/* ── Slider track color ── */
[data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: #F87171;
}

/* ── Divider ── */
.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 40px 0;
}

/* ── Predict button ── */
.stButton > button {
    background: linear-gradient(135deg, #DC2626, #991B1B) !important;
    color: #fff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    transition: opacity 0.2s, transform 0.1s !important;
    box-shadow: 0 8px 32px rgba(220,38,38,0.3) !important;
}

.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Result cards ── */
.result-low {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
}

.result-moderate {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
}

.result-high {
    background: rgba(220,38,38,0.1);
    border: 1px solid rgba(220,38,38,0.35);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
}

.result-level {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.result-pct {
    font-family: 'DM Serif Display', serif;
    font-size: 48px;
    font-weight: 400;
    line-height: 1;
}

.result-desc {
    font-size: 13px;
    color: #64748B;
    margin-top: 6px;
}

/* ── Section headers ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    font-weight: 400;
    color: #F1F5F9;
    margin: 0 0 4px 0;
}

.section-sub {
    font-size: 13px;
    color: #475569;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# HERO SECTION
# ------------------------------------------------------------
st.markdown('<div class="hero-badge">AI-Powered Cardiology</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Heart Disease<br><span>Risk Prediction</span></h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">Enter the patient\'s clinical parameters below. '
    'The model will analyze cardiovascular risk in real-time.</p>',
    unsafe_allow_html=True
)

# Model selector
model_choice = st.selectbox(
    "Prediction model",
    ["random_forest", "logistic_regression", "gradient_boosting"],
    label_visibility="collapsed"
)

st.markdown(
    f"<p style='font-size:12px; color:#475569; margin-top:6px;'>Model: "
    f"<strong style='color:#94A3B8'>{model_choice.replace('_', ' ').title()}</strong></p>",
    unsafe_allow_html=True
)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ------------------------------------------------------------
# INPUT FIELDS
# ------------------------------------------------------------
st.markdown('<p class="section-header">Patient Clinical Parameters</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">All fields are required for an accurate prediction.</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    age = st.number_input("Age", min_value=1, max_value=120, value=50)
    sex = st.selectbox("Sex", [1, 0], format_func=lambda x: "Male" if x == 1 else "Female")
    trestbps = st.number_input("Resting Blood Pressure (mmHg)", min_value=0, value=120)
    chol = st.number_input("Serum Cholesterol (mg/dl)", min_value=0, value=200)
    fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dl", [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")

with col2:
    cp = st.slider("Chest Pain Type", 0, 3)
    restecg = st.slider("Resting ECG Results", 0, 2)
    thalach = st.number_input("Maximum Heart Rate Achieved", min_value=0, value=150)
    exang = st.selectbox("Exercise-Induced Angina", [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
    oldpeak = st.number_input("ST Depression (Oldpeak)", min_value=0.0, step=0.1, value=1.0)

with col3:
    slope = st.slider("Slope of Peak ST Segment", 0, 2)
    ca = st.slider("Major Vessels Colored by Fluoroscopy", 0, 4)
    thal = st.slider("Thalassemia Type", 0, 3)


st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ------------------------------------------------------------
# PREDICTION
# ------------------------------------------------------------
predict_clicked = st.button("🔍  Run Cardiac Risk Analysis", use_container_width=True)

if predict_clicked:
    data = {
        "age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol,
        "fbs": fbs, "restecg": restecg, "thalach": thalach, "exang": exang,
        "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal,
        "model": model_choice
    }

    try:
        with st.spinner("Analyzing patient data…"):
            response = requests.post(
                "http://127.0.0.1:5000/predict",
                json=data,
                timeout=30
            )
            result = response.json()
            probability = result["probability"]
            pct = probability * 100

        # SUCCESS UI
        st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Prediction Summary</p>', unsafe_allow_html=True)

        col_g, col_r = st.columns([2, 1])

        with col_g:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={'suffix': "%"},
                gauge={'axis': {'range': [0, 100]}}
            ))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            if probability < 0.3:
                level = "Low Risk"
                color = "#10B981"
            elif probability < 0.6:
                level = "Moderate Risk"
                color = "#F59E0B"
            else:
                level = "High Risk"
                color = "#EF4444"

            st.markdown(
                f"<div class='result-high'><div class='result-level'>{level}</div>"
                f"<div class='result-pct'>{pct:.1f}%</div></div>",
                unsafe_allow_html=True
            )

    except Exception as e:
    st.markdown(
        f"""
        <div style="background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.25);
                    border-radius:12px; padding:18px 22px; margin-top:20px;">
            <p style="font-size:14px; color:#F87171; margin:0;">
                ⚠ Backend unreachable.<br><br>
                Tried: <code>http://127.0.0.1:5000/predict</code><br><br>
                Error: <code>{str(e)}</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )