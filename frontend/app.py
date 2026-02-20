import streamlit as st
import os

st.set_page_config(page_title="CardioScan · Home", layout="wide", page_icon="🫀")

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 90% 55% at 15% 10%, rgba(220,38,38,0.13) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 80%, rgba(99,102,241,0.09) 0%, transparent 55%),
        #0D0F14;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Divider ── */
.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 52px 0;
}

/* ── Hero ── */
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(220,38,38,0.10);
    border: 1px solid rgba(220,38,38,0.28);
    border-radius: 999px;
    padding: 5px 16px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #F87171;
    margin-bottom: 20px;
}

.hero-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #F87171;
    display: inline-block;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.7); }
}

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(38px, 5.5vw, 72px);
    font-weight: 400;
    line-height: 1.05;
    letter-spacing: -0.025em;
    color: #F1F5F9;
    margin: 0 0 12px 0;
}

.hero-title em {
    font-style: italic;
    color: #F87171;
}

.hero-desc {
    font-size: 16px;
    color: #64748B;
    font-weight: 300;
    line-height: 1.7;
    max-width: 500px;
    margin: 0 0 36px 0;
}

/* ── CTA button ── */
.cta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

.cta-primary {
    display: inline-block;
    background: linear-gradient(135deg, #DC2626, #991B1B);
    color: #fff !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.02em;
    padding: 12px 28px;
    border-radius: 10px;
    text-decoration: none;
    box-shadow: 0 8px 28px rgba(220,38,38,0.28);
}

.cta-secondary {
    display: inline-block;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    color: #94A3B8 !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    padding: 12px 24px;
    border-radius: 10px;
    text-decoration: none;
}

/* ── Hero stat strip ── */
.hero-stats {
    display: flex; gap: 28px; flex-wrap: wrap; margin-top: 40px;
    padding-top: 32px;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.hero-stat-val {
    font-family: 'DM Serif Display', serif;
    font-size: 30px;
    color: #F1F5F9;
    line-height: 1;
}
.hero-stat-label {
    font-size: 12px;
    color: #334155;
    margin-top: 4px;
}


/* ── Features ── */
.feat-grid { display: flex; gap: 16px; flex-wrap: wrap; }

.feat-card {
    flex: 1; min-width: 220px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 26px 22px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.feat-card:hover { border-color: rgba(255,255,255,0.12); }

.feat-icon {
    width: 44px; height: 44px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    margin-bottom: 16px;
    background: var(--ic-bg);
}

.feat-title {
    font-family: 'DM Serif Display', serif;
    font-size: 18px;
    color: #F1F5F9;
    margin-bottom: 10px;
}

.feat-items { list-style: none; padding: 0; margin: 0; }
.feat-items li {
    font-size: 13px;
    color: #475569;
    padding: 5px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    display: flex; align-items: center; gap: 8px;
}
.feat-items li:last-child { border-bottom: none; }
.feat-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--dot-c);
    flex-shrink: 0;
}

/* ── Tech stack ── */
.tech-grid { display: flex; gap: 12px; flex-wrap: wrap; }

.tech-chip {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px 18px;
    min-width: 160px;
    flex: 1;
}
.tech-icon { font-size: 22px; flex-shrink: 0; }
.tech-label { font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #334155; }
.tech-name  { font-size: 14px; font-weight: 500; color: #94A3B8; margin-top: 1px; }

/* ── Nav hint ── */
.nav-hint {
    display: flex; align-items: center; gap: 14px;
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.20);
    border-radius: 14px;
    padding: 18px 24px;
    margin-top: 8px;
}
.nav-hint-icon { font-size: 24px; flex-shrink: 0; }
.nav-hint-text { font-size: 14px; color: #64748B; }
.nav-hint-text strong { color: #A5B4FC; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
left, right = st.columns([1.3, 1], gap="large")

with left:
    st.markdown("""
    <div class="hero-eyebrow">
        <span class="hero-dot"></span> AI Clinical Decision Support
    </div>
    <h1 class="hero-title">Predict cardiac risk<br>with <em>precision.</em></h1>
    <p class="hero-desc">
        An end-to-end machine learning platform for assessing heart disease risk -
        combining interpretable models, real-time inference, and rich analytics in
        one clinical dashboard.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-stats">
        <div>
            <div class="hero-stat-val">3</div>
            <div class="hero-stat-label">ML Models</div>
        </div>
        <div>
            <div class="hero-stat-val">13</div>
            <div class="hero-stat-label">Clinical Features</div>
        </div>
        <div>
            <div class="hero-stat-val">303</div>
            <div class="hero-stat-label">Training Samples</div>
        </div>
        <div>
            <div class="hero-stat-val">5</div>
            <div class="hero-stat-label">Eval Metrics</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with right:
    IMAGE_PATH = os.path.join("assets", "heart_banner.png")
    st.image(IMAGE_PATH, use_container_width=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FEATURES
# ─────────────────────────────────────────────
st.markdown("""
<p style="font-family:'DM Serif Display',serif; font-size:32px; color:#F1F5F9;
          margin:0 0 4px 0;">Platform capabilities</p>
<p style="font-size:14px; color:#475569; margin-bottom:28px;">
    Everything you need for cardiac risk assessment in one place.
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div class="feat-grid">

  <div class="feat-card">
    <div class="feat-icon" style="--ic-bg:rgba(220,38,38,0.12);">🔍</div>
    <div class="feat-title">Risk Prediction</div>
    <ul class="feat-items">
      <li><span class="feat-dot" style="--dot-c:#F87171;"></span>Real-time inference via REST API</li>
      <li><span class="feat-dot" style="--dot-c:#F87171;"></span>Switch between 3 trained models</li>
      <li><span class="feat-dot" style="--dot-c:#F87171;"></span>Probability score with risk label</li>
      <li><span class="feat-dot" style="--dot-c:#F87171;"></span>Interactive gauge visualization</li>
    </ul>
  </div>

  <div class="feat-card">
    <div class="feat-icon" style="--ic-bg:rgba(99,102,241,0.12);">📊</div>
    <div class="feat-title">Model Evaluation</div>
    <ul class="feat-items">
      <li><span class="feat-dot" style="--dot-c:#818CF8;"></span>Accuracy, Precision, Recall, F1</li>
      <li><span class="feat-dot" style="--dot-c:#818CF8;"></span>ROC curve & confusion matrix</li>
      <li><span class="feat-dot" style="--dot-c:#818CF8;"></span>Feature importance ranking</li>
      <li><span class="feat-dot" style="--dot-c:#818CF8;"></span>Model-by-model comparison</li>
    </ul>
  </div>

  <div class="feat-card">
    <div class="feat-icon" style="--ic-bg:rgba(251,191,36,0.10);">📈</div>
    <div class="feat-title">Prediction Analytics</div>
    <ul class="feat-items">
      <li><span class="feat-dot" style="--dot-c:#FBBF24;"></span>Full prediction history log</li>
      <li><span class="feat-dot" style="--dot-c:#FBBF24;"></span>Risk distribution histogram</li>
      <li><span class="feat-dot" style="--dot-c:#FBBF24;"></span>Time-series trend tracking</li>
      <li><span class="feat-dot" style="--dot-c:#FBBF24;"></span>Population-level KPIs</li>
    </ul>
  </div>

  <div class="feat-card">
    <div class="feat-icon" style="--ic-bg:rgba(16,185,129,0.10);">🏆</div>
    <div class="feat-title">Model Comparison</div>
    <ul class="feat-items">
      <li><span class="feat-dot" style="--dot-c:#34D399;"></span>Side-by-side metric comparison</li>
      <li><span class="feat-dot" style="--dot-c:#34D399;"></span>Best model auto-highlighted</li>
      <li><span class="feat-dot" style="--dot-c:#34D399;"></span>Radar chart overview</li>
      <li><span class="feat-dot" style="--dot-c:#34D399;"></span>Live ranking table</li>
    </ul>
  </div>

</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TECH STACK
# ─────────────────────────────────────────────
st.markdown("""
<p style="font-family:'DM Serif Display',serif; font-size:32px; color:#F1F5F9;
          margin:0 0 4px 0;">Technology stack</p>
<p style="font-size:14px; color:#475569; margin-bottom:28px;">
    Built on proven open-source tools for reliability and performance.
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tech-grid">
  <div class="tech-chip">
    <div class="tech-icon">🤖</div>
    <div>
      <div class="tech-label">Machine Learning</div>
      <div class="tech-name">Scikit-learn</div>
    </div>
  </div>
  <div class="tech-chip">
    <div class="tech-icon">⚙️</div>
    <div>
      <div class="tech-label">Backend API</div>
      <div class="tech-name">Flask REST</div>
    </div>
  </div>
  <div class="tech-chip">
    <div class="tech-icon">🍃</div>
    <div>
      <div class="tech-label">Database</div>
      <div class="tech-name">MongoDB Atlas</div>
    </div>
  </div>
  <div class="tech-chip">
    <div class="tech-icon">🎈</div>
    <div>
      <div class="tech-label">Frontend</div>
      <div class="tech-name">Streamlit</div>
    </div>
  </div>
  <div class="tech-chip">
    <div class="tech-icon">📉</div>
    <div>
      <div class="tech-label">Visualization</div>
      <div class="tech-name">Plotly · Matplotlib</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# NAV HINT
# ─────────────────────────────────────────────
st.markdown("""
<div class="nav-hint">
  <div class="nav-hint-icon">👈</div>
  <div class="nav-hint-text">
    Use the <strong>sidebar</strong> to navigate between modules -
    Risk Prediction, Model Evaluation, Analytics Dashboard, and Model Comparison.
  </div>
</div>
""", unsafe_allow_html=True)