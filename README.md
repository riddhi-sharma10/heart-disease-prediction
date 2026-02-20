# 🫀 CardioScan - Heart Disease Risk Prediction System

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST%20API-000000?style=flat&logo=flask&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-ML-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> A full-stack machine learning system for real-time cardiac risk assessment - combining interpretable ML models, a Flask REST API, a visually refined Streamlit dashboard, and MongoDB-backed data persistence.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [How It Works](#-how-it-works)
- [Dependencies](#-dependencies)
- [Future Enhancements](#-future-enhancements)
- [References](#-references)
- [Author](#-author)

---

## 🔍 Overview

**CardioScan** predicts the risk of heart disease using **13 clinical parameters**. It combines a Flask REST API backend with three trained ML classifiers, a Streamlit frontend dashboard, and MongoDB Atlas for persistent prediction storage - with automatic local JSON fallback if the database is unavailable.

Built with a focus on **backend architecture**, **ML pipeline engineering**, and a visually refined dark-themed medical dashboard UI.

> ⚡ This application is designed to run entirely on **localhost**. No cloud deployment is required.

---

## 🌟 Features

### 🧠 Machine Learning Pipeline
- Trained on the **UCI Cleveland Heart Disease Dataset** (303 samples, 13 features)
- Three classifiers available at runtime:
  - **Random Forest Classifier**
  - **Logistic Regression**
  - **Gradient Boosting Classifier**
- Real-time inference with calibrated probability scores
- `MinMaxScaler` normalization via saved `scaler.pkl`
- Version-controlled `.pkl` model files - no retraining needed at startup
- Backward compatibility for old prediction record formats

---

### ⚙️ Backend — Flask REST API

A lightweight, production-style microservice that loads all models once for fast inference.

| Endpoint | Method | Description |
|---|---|---|
| `/predict` | POST | Returns prediction + probability score |
| `/history` | GET | Fetches all past predictions (flattened & merged) |
| `/health` | GET | API status, model availability, DB health |
| `/debug/db` | GET | MongoDB diagnostics + fallback mode info |

**Key features:**
- All models loaded once at startup → fast inference
- **Dual storage:** MongoDB Atlas (primary) → `predictions_fallback.json` (automatic fallback)
- `/history` flattens nested records for consistent frontend DataFrame rendering
- CORS enabled for local frontend–backend communication
- Strong error handling and input validation

---

### 🎛️ Frontend - Streamlit Dashboard

A modern dark-themed medical interface with custom CSS and Plotly visualizations.

| Page | Description |
|---|---|
| **Home** | Hero section, platform overview, tech stack |
| **1 · Risk Prediction** | 13-parameter form, animated gauge chart, risk classification |
| **2 · Analytics Dashboard** | KPI cards, donut chart, time-series scatter, raw data table |
| **3 · Model Info** | Accuracy metrics, ROC curve, confusion matrix, feature importance |
| **4 · Model Comparison** | Side-by-side bar charts, radar chart, ranked leaderboard |
| **5 · Prediction Analytics** | Histogram, rolling average timeline, box plot, percentile stats |

**UI highlights:**
- Risk classification: **Low** (<30%) · **Moderate** (30–60%) · **High** (>60%)
- Animated gauge chart with color-coded risk zones
- ROC curve, confusion matrix (custom indigo colormap), feature importance charts
- DM Serif Display + DM Sans typography
- Dark glassmorphism card design system with unique accent color per page

---

### 🗄️ Database & Storage
- **Primary:** MongoDB Atlas (cloud)
- **Fallback:** `predictions_fallback.json` (local) - zero data loss if DB is unavailable
- `/history` merges both sources so the UI always shows all predictions
- Records stored flat at top-level for easy DataFrame processing on the frontend

---

## 📁 Project Structure

```
CardioScan/
│
├── backend/
│   ├── app.py                    # Flask REST API
│   └── predictions_fallback.json # Local fallback storage
│
├── model/
│   ├── heart.csv                 # Training dataset
│   ├── train_model.py            # Model training script
│   ├── scaler.pkl                # Fitted MinMaxScaler
│   ├── random_forest.pkl
│   ├── logistic_regression.pkl
│   ├── gradient_boosting.pkl
│   ├── metrics.json              # Evaluation metrics
│   ├── model_comparison.json     # Head-to-head scores
│   ├── confusion_matrix.npy      # Saved confusion matrix
│   └── roc_curve.png             # ROC curve image
│
├── frontend/
│   ├── app.py                    # Home page (Streamlit entry point)
│   ├── pages/
│   │   ├── 1_Predict.py
│   │   ├── 2_Dashboard.py
│   │   ├── 3_Model_Info.py
│   │   ├── 4_Model_Comparison.py
│   │   └── 5_Prediction_Analytics.py
│   └── assets/
│       ├── heart_banner.png
│       ├── hero_preview.png
│       └── dashboard_preview.png
│
├── requirements.txt
└── README.md
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- pip
- MongoDB Atlas account (free tier works)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/riddhi-sharma10/CardioScan.git
cd CardioScan
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Train the Models *(first-time setup only)*
```bash
cd model
python train_model.py
cd ..
```

This generates: `scaler.pkl`, `random_forest.pkl`, `logistic_regression.pkl`, `gradient_boosting.pkl`, `metrics.json`, `model_comparison.json`, `confusion_matrix.npy`, `roc_curve.png`

---

## ▶️ Running the Application

> You need **two terminals running simultaneously** - one for Flask and one for Streamlit.

### Terminal 1 - Start Flask Backend
```bash
cd backend
python app.py
```
Expected output:
```
✔ Models loaded successfully
✔ Connected to MongoDB Atlas
* Running on http://127.0.0.1:5000
```

### Terminal 2 - Start Streamlit Frontend
```bash
cd frontend
streamlit run app.py
```
Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

| Service | Command | URL |
|---|---|---|
| Flask Backend | `python app.py` | http://127.0.0.1:5000 |
| Streamlit Frontend | `streamlit run app.py` | http://localhost:8501 |

---

## 🔁 How It Works

1. User enters **13 clinical parameters** on the Predict page (age, sex, chest pain type, blood pressure, cholesterol, etc.)
2. Streamlit sends a `POST` request to Flask `/predict` with the values and chosen model.
3. Flask scales the inputs using `MinMaxScaler`, runs the selected classifier, and returns a prediction (0 or 1) and probability score (0.0 – 1.0).
4. The record is saved to **MongoDB Atlas**. If Atlas is unavailable, it is written to `predictions_fallback.json` automatically.
5. Streamlit displays the animated gauge chart, risk category, confidence score, and model details.
6. The Dashboard and Analytics pages call `/history`, which merges and flattens all records for consistent rendering.

---

## 📦 Dependencies

| Package | Purpose | Layer |
|---|---|---|
| `streamlit` | Frontend dashboard framework | Frontend |
| `flask` | REST API backend | Backend |
| `flask-cors` | CORS support for local dev | Backend |
| `pymongo` | MongoDB Atlas driver | Backend |
| `scikit-learn` | ML models + preprocessing | ML |
| `joblib` | Model serialization (.pkl) | ML |
| `numpy` | Numerical computation | ML |
| `pandas` | DataFrame processing | Both |
| `plotly` | Interactive charts | Frontend |
| `matplotlib` | Static charts (confusion matrix) | Frontend |
| `seaborn` | Heatmap styling | Frontend |

---

## 🚀 Future Enhancements

- [ ] Automatic model retraining pipeline when new data is added
- [ ] SHAP value integration for per-prediction feature explainability
- [ ] Downloadable patient risk report as a styled PDF
- [ ] Authentication system for doctors and admin users
- [ ] Cloud deployment (Render backend + Streamlit Cloud frontend)
- [ ] Model performance drift monitoring over time

---

## 📚 References

**Dataset**

Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1988). *Heart Disease Dataset*. UCI Machine Learning Repository.
https://archive.ics.uci.edu/dataset/45/heart+disease

---

## 👤 Author

**Riddhi Sharma**
*Computer Science Engineering · AI/ML & Full-Stack Development*

📧 riddhisharmawave18@gmail.com
💼 [linkedin.com/in/riddhi-sharma-95b7a7324/](https://www.linkedin.com/in/riddhi-sharma-95b7a7324/)
🐱 [github.com/riddhi-sharma10](https://github.com/riddhi-sharma10)

---

*Made with ❤️ by Riddhi Sharma · © 2025 All Rights Reserved*
