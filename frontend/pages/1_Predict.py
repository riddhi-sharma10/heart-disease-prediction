import streamlit as st
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="CardioScan · Risk Prediction", layout="wide", page_icon="🫀")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(220,38,38,0.15) 0%, #0D0F14 60%);
}

#MainMenu, footer, header { visibility: hidden; }

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

.hero-title span { color: #F87171; }

.hero-subtitle {
    font-size: 15px;
    color: #64748B;
    font-weight: 300;
    margin: 0 0 40px 0;
    max-width: 520px;
}

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

.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #E8EAF0 !important;
}

input[type="number"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
}

.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 40px 0;
}

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

# ── Hero ───────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">AI-Powered Cardiology</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Heart Disease<br><span>Risk Prediction</span></h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">Enter the patient\'s clinical parameters below. '
    'The model will analyze cardiovascular risk in real-time.</p>',
    unsafe_allow_html=True
)

model_choice = st.selectbox(
    "Prediction model",
    ["random_forest", "logistic_regression", "gradient_boosting"],
    label_visibility="collapsed"
)
st.markdown(
    f"<p style='font-size:12px; color:#475569; margin-top:6px;'>"
    f"Model: <strong style='color:#94A3B8'>{model_choice.replace('_', ' ').title()}</strong></p>",
    unsafe_allow_html=True
)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)

# ── Parameters ─────────────────────────────────────────────────
st.markdown('<p class="section-header">Patient Clinical Parameters</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">All fields are required for an accurate prediction.</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown('<div class="param-card"><p class="card-label">Demographics & Vitals</p>', unsafe_allow_html=True)
    age      = st.number_input("Age", min_value=1, max_value=120, value=50)
    sex      = st.selectbox("Sex", [1, 0], format_func=lambda x: "Male" if x == 1 else "Female")
    trestbps = st.number_input("Resting Blood Pressure (mmHg)", min_value=0, value=120)
    chol     = st.number_input("Serum Cholesterol (mg/dl)", min_value=0, value=200)
    fbs      = st.selectbox("Fasting Blood Sugar > 120 mg/dl", [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="param-card"><p class="card-label">ECG & Exercise</p>', unsafe_allow_html=True)
    cp       = st.slider("Chest Pain Type", 0, 3, help="0=Typical angina, 1=Atypical, 2=Non-anginal, 3=Asymptomatic")
    restecg  = st.slider("Resting ECG Results", 0, 2, help="0=Normal, 1=ST-T abnormality, 2=LV hypertrophy")
    thalach  = st.number_input("Maximum Heart Rate Achieved", min_value=0, value=150)
    exang    = st.selectbox("Exercise-Induced Angina", [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
    oldpeak  = st.number_input("ST Depression (Oldpeak)", min_value=0.0, step=0.1, value=1.0)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="param-card"><p class="card-label">Angiography & Thal</p>', unsafe_allow_html=True)
    slope    = st.slider("Slope of Peak ST Segment", 0, 2, help="0=Upsloping, 1=Flat, 2=Downsloping")
    ca       = st.slider("Major Vessels Colored by Fluoroscopy", 0, 4)
    thal     = st.slider("Thalassemia Type", 0, 3, help="0=Normal, 1=Fixed defect, 2=Reversible defect, 3=Unknown")
    st.markdown('<br><br>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)

# ── Predict ────────────────────────────────────────────────────
predict_clicked = st.button("🔍  Run Cardiac Risk Analysis", use_container_width=True)

if predict_clicked:
    # ✔ FIX: include "model" key so backend uses the selected algorithm
    data = {
        "age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol,
        "fbs": fbs, "restecg": restecg, "thalach": thalach, "exang": exang,
        "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal,
        "model": model_choice          # ← was missing in original
    }

    try:
        with st.spinner("Analyzing patient data…"):
            response = requests.post("http://127.0.0.1:5000/predict", json=data, timeout=10)
            response.raise_for_status()
            result      = response.json()
            probability = result["probability"]
            pct         = probability * 100

        st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Prediction Summary</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">Based on the provided clinical parameters.</p>', unsafe_allow_html=True)

        g_col, r_col = st.columns([2, 1], gap="large")

        with g_col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={'suffix': "%", 'font': {'size': 40, 'color': '#F1F5F9', 'family': 'DM Serif Display'}},
                title={'text': "Cardiovascular Risk Score", 'font': {'size': 14, 'color': '#64748B', 'family': 'DM Sans'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': '#334155', 'tickfont': {'color': '#475569', 'size': 11}},
                    'bar': {'color': "#E63946", 'thickness': 0.22},
                    'bgcolor': 'rgba(0,0,0,0)',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0,  30], 'color': 'rgba(16,185,129,0.15)'},
                        {'range': [30, 60], 'color': 'rgba(245,158,11,0.15)'},
                        {'range': [60,100], 'color': 'rgba(220,38,38,0.18)'},
                    ],
                    'threshold': {
                        'line': {'color': '#F87171', 'width': 2},
                        'thickness': 0.75,
                        'value': pct
                    }
                }
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=30, b=10, l=20, r=20),
                height=280,
                font=dict(family='DM Sans')
            )
            st.plotly_chart(fig, use_container_width=True)

        with r_col:
            st.markdown("<br><br>", unsafe_allow_html=True)

            if probability < 0.3:
                st.markdown(f"""
                <div class="result-low">
                    <div class="result-level" style="color:#10B981;">● Low Risk</div>
                    <div class="result-pct" style="color:#34D399;">{pct:.1f}%</div>
                    <div class="result-desc">Cardiovascular risk appears low. Routine monitoring advised.</div>
                </div>""", unsafe_allow_html=True)
            elif probability < 0.6:
                st.markdown(f"""
                <div class="result-moderate">
                    <div class="result-level" style="color:#F59E0B;">◆ Moderate Risk</div>
                    <div class="result-pct" style="color:#FCD34D;">{pct:.1f}%</div>
                    <div class="result-desc">Elevated risk detected. Clinical follow-up recommended.</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-high">
                    <div class="result-level" style="color:#EF4444;">▲ High Risk</div>
                    <div class="result-pct" style="color:#F87171;">{pct:.1f}%</div>
                    <div class="result-desc">Significant cardiac risk detected. Urgent consultation advised.</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
                        border-radius:12px; padding:16px 20px;">
                <p style="font-size:11px; color:#475569; font-weight:600; letter-spacing:0.1em;
                           text-transform:uppercase; margin-bottom:10px;">Model Details</p>
                <p style="font-size:13px; color:#94A3B8; margin:0;">
                    <span style="color:#64748B;">Algorithm:</span> {result.get('model_used', model_choice).replace('_', ' ').title()}<br>
                    <span style="color:#64748B;">Confidence:</span> {max(pct, 100-pct):.1f}%
                </p>
            </div>""", unsafe_allow_html=True)

    except requests.exceptions.ConnectionError:
        st.markdown("""
        <div style="background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.25);
                    border-radius:12px; padding:18px 22px; margin-top:20px;">
            <p style="font-size:14px; color:#F87171; margin:0;">
                ⚠ &nbsp;Backend unreachable. Please start the Flask server:<br>
                <code style="font-size:13px;">cd backend &amp;&amp; python app.py</code>
            </p>
        </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.25);
                    border-radius:12px; padding:18px 22px; margin-top:20px;">
            <p style="font-size:14px; color:#F87171; margin:0;">⚠ &nbsp;Error: {e}</p>
        </div>""", unsafe_allow_html=True)