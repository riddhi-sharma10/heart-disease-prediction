import streamlit as st
import joblib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import seaborn as sns
import numpy as np
import os

st.set_page_config(page_title="CardioScan · Model Performance", layout="wide", page_icon="📈")

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 70% 40% at 50% -5%, rgba(99,102,241,0.12) 0%, #0D0F14 55%);
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.35);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #A5B4FC;
    margin-bottom: 14px;
}

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(30px, 4vw, 54px);
    font-weight: 400;
    line-height: 1.1;
    letter-spacing: -0.02em;
    margin: 0 0 8px 0;
    color: #F1F5F9;
}
.hero-title span { color: #818CF8; }

.hero-subtitle {
    font-size: 14px;
    color: #475569;
    font-weight: 300;
    margin: 0 0 36px 0;
}

/* ── Divider ── */
.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 36px 0;
}

/* ── KPI Cards ── */
.kpi-grid { display: flex; gap: 16px; flex-wrap: wrap; }

.kpi-card {
    flex: 1;
    min-width: 140px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 22px 20px 18px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
    background: var(--accent);
}

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'DM Serif Display', serif;
    font-size: 38px;
    font-weight: 400;
    line-height: 1;
    color: var(--val-color, #F1F5F9);
}
.kpi-suffix {
    font-family: 'DM Sans', sans-serif;
    font-size: 18px;
    color: #475569;
}
.kpi-sub { font-size: 12px; color: #334155; margin-top: 6px; }

/* ── Section labels ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #F1F5F9;
    margin: 0 0 2px 0;
}
.section-sub {
    font-size: 13px;
    color: #475569;
    margin-bottom: 20px;
}

/* ── Chart container ── */
.chart-wrap {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #E8EAF0 !important;
}

/* ── Info / Error / Warning overrides ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left: 3px solid !important;
    background: rgba(255,255,255,0.03) !important;
}

/* ── Summary grid ── */
.summary-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.summary-item {
    flex: 1; min-width: 180px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 16px 18px;
}
.summary-key {
    font-size: 10px; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #334155; margin-bottom: 6px;
}
.summary-val { font-size: 14px; color: #94A3B8; }

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 48px 32px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
}
.empty-state p { color: #334155; font-size: 13px; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ──────────────────────────
DARK_BG   = "#0D0F14"
SURFACE   = "#141820"
BORDER    = "#1E293B"
TEXT_MUT  = "#475569"
TEXT_MAIN = "#CBD5E1"

def apply_dark_style(fig, ax_list):
    fig.patch.set_facecolor(DARK_BG)
    for ax in (ax_list if isinstance(ax_list, list) else [ax_list]):
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=TEXT_MUT, labelsize=10)
        ax.xaxis.label.set_color(TEXT_MUT)
        ax.yaxis.label.set_color(TEXT_MUT)
        ax.title.set_color(TEXT_MAIN)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)


# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown('<div class="hero-badge">Model Evaluation</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Performance <span>Metrics</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Detailed evaluation of trained cardiac risk models — accuracy, curves, and feature analysis.</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD METRICS
# ─────────────────────────────────────────────
try:
    with open("../model/metrics.json") as f:
        metrics = json.load(f)
except Exception:
    st.error("⚠  `metrics.json` not found. Please re-run the training script to generate model artifacts.")
    st.stop()


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
st.markdown('<p class="section-header">Evaluation Metrics</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Key performance indicators across classification criteria.</p>', unsafe_allow_html=True)

METRIC_META = [
    ("Accuracy",  "accuracy",  "#818CF8", "Overall correct classifications"),
    ("Precision", "precision", "#34D399", "True positives out of all predicted positives"),
    ("Recall",    "recall",    "#F87171", "True positives out of all actual positives"),
    ("F1 Score",  "f1_score",  "#FBBF24", "Harmonic mean of precision and recall"),
    ("ROC-AUC",   "roc_auc",   "#60A5FA", "Area under the receiver operating curve"),
]

cols = st.columns(5, gap="medium")
for col, (label, key, color, desc) in zip(cols, METRIC_META):
    val = metrics.get(key, 0)
    whole = int(val * 100)
    frac  = f"{val*100:.2f}"
    col.markdown(f"""
    <div class="kpi-card" style="--accent: {color}; --val-color: {color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{frac}<span class="kpi-suffix">%</span></div>
        <div class="kpi-sub">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROC CURVE + CONFUSION MATRIX
# ─────────────────────────────────────────────
roc_col, cm_col = st.columns(2, gap="large")

with roc_col:
    st.markdown('<p class="section-header">ROC Curve</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">True positive rate vs. false positive rate across thresholds.</p>', unsafe_allow_html=True)

    roc_path = "../model/roc_curve.png"
    if os.path.exists(roc_path):
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.image(roc_path, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:36px;">📈</div>
            <p>ROC curve image not found.<br>Re-run the training script to generate it.</p>
        </div>""", unsafe_allow_html=True)

with cm_col:
    st.markdown('<p class="section-header">Confusion Matrix</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Actual vs. predicted classifications across both classes.</p>', unsafe_allow_html=True)

    cm_path = "../model/confusion_matrix.npy"
    if os.path.exists(cm_path):
        cm = np.load(cm_path)
        fig_cm, ax_cm = plt.subplots(figsize=(5, 4))
        apply_dark_style(fig_cm, ax_cm)

        # Custom indigo-tinted colormap
        from matplotlib.colors import LinearSegmentedColormap
        indigo_cmap = LinearSegmentedColormap.from_list(
            "indigo_dark", ["#141820", "#312E81", "#818CF8"]
        )

        sns.heatmap(
            cm, annot=True, fmt="d",
            cmap=indigo_cmap,
            linewidths=2, linecolor=DARK_BG,
            ax=ax_cm, cbar=False,
            annot_kws={"size": 20, "weight": "bold", "color": "#F1F5F9"},
        )
        ax_cm.set_xlabel("Predicted Label", labelpad=10)
        ax_cm.set_ylabel("Actual Label", labelpad=10)
        ax_cm.set_xticklabels(["No Disease", "Disease"], color=TEXT_MUT)
        ax_cm.set_yticklabels(["No Disease", "Disease"], color=TEXT_MUT, rotation=0)
        ax_cm.set_title("")

        fig_cm.tight_layout(pad=1.5)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.pyplot(fig_cm)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:36px;">📊</div>
            <p>Confusion matrix not found.<br>Re-run the training script to generate it.</p>
        </div>""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FEATURE IMPORTANCE
# ─────────────────────────────────────────────
st.markdown('<p class="section-header">Feature Importance</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Which clinical variables drive the model\'s predictions most?</p>', unsafe_allow_html=True)

model_choice = st.selectbox(
    "Select model",
    ["random_forest", "gradient_boosting", "logistic_regression"],
    label_visibility="collapsed"
)
st.markdown(f"<p style='font-size:12px; color:#475569; margin-top:4px; margin-bottom:20px;'>Showing: <strong style='color:#94A3B8'>{model_choice.replace('_', ' ').title()}</strong></p>", unsafe_allow_html=True)

model_path = f"../model/{model_choice}.pkl"
FEATURES = ["age","sex","cp","trestbps","chol","fbs",
            "restecg","thalach","exang","oldpeak","slope","ca","thal"]

try:
    model = joblib.load(model_path)

    if hasattr(model, "feature_importances_"):
        scores = model.feature_importances_
        label  = "Feature Importance"
        bar_color_key = "#818CF8"

    elif hasattr(model, "coef_"):
        scores = np.abs(model.coef_[0])
        label  = "Coefficient Magnitude"
        bar_color_key = "#60A5FA"

    else:
        scores = None

    if scores is not None:
        sorted_idx   = np.argsort(scores)
        feat_names   = np.array(FEATURES)[sorted_idx]
        feat_scores  = scores[sorted_idx]

        # Normalize for color gradient
        norm = (feat_scores - feat_scores.min()) / (feat_scores.max() - feat_scores.min() + 1e-9)
        bar_colors = plt.cm.get_cmap("Blues")(0.3 + norm * 0.65)

        fig_feat, ax_feat = plt.subplots(figsize=(10, 5))
        apply_dark_style(fig_feat, ax_feat)

        bars = ax_feat.barh(feat_names, feat_scores, color=bar_colors,
                            height=0.65, edgecolor=DARK_BG, linewidth=0.5)

        # Value labels
        for bar, val in zip(bars, feat_scores):
            ax_feat.text(
                bar.get_width() + feat_scores.max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left",
                fontsize=9, color=TEXT_MUT
            )

        ax_feat.set_xlabel(label, labelpad=10)
        ax_feat.set_xlim(0, feat_scores.max() * 1.18)
        ax_feat.tick_params(axis='y', labelsize=10, colors=TEXT_MUT)
        ax_feat.grid(axis='x', color=BORDER, linestyle='--', linewidth=0.6, alpha=0.8)
        ax_feat.set_axisbelow(True)
        fig_feat.tight_layout(pad=2)

        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.pyplot(fig_feat)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.warning("This model type does not expose feature importance or coefficients.")

except FileNotFoundError:
    st.markdown(f"""
    <div class="empty-state">
        <div style="font-size:36px;">🤖</div>
        <p>Model file <code>{model_path}</code> not found.<br>Re-run the training script to generate the model artifact.</p>
    </div>""", unsafe_allow_html=True)

st.markdown('<hr class="fancy-divider"/>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MODEL SUMMARY
# ─────────────────────────────────────────────
st.markdown('<p class="section-header">Model Summary</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Training configuration and methodology overview.</p>', unsafe_allow_html=True)

summary_items = [
    ("Dataset",       "UCI Cleveland Heart Disease · 303 samples"),
    ("Preprocessing", "Missing value handling + feature scaling (StandardScaler)"),
    ("Models Tested", "Logistic Regression · Random Forest · Gradient Boosting"),
    ("Selection",     "Best model auto-selected by highest accuracy on test split"),
    ("Metrics Used",  "Accuracy · Precision · Recall · F1 Score · ROC-AUC"),
]

cols = st.columns(len(summary_items), gap="medium")
for col, (key, val) in zip(cols, summary_items):
    col.markdown(f"""
    <div class="summary-item">
        <div class="summary-key">{key}</div>
        <div class="summary-val">{val}</div>
    </div>
    """, unsafe_allow_html=True)