from flask import Flask, request, jsonify
import joblib
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ------------------------------------------------
# DEFINE BASE DIRECTORY (backend folder)
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

# ------------------------------------------------
# LOAD SCALER SAFELY (absolute path)
# ------------------------------------------------
scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")

if not os.path.exists(scaler_path):
    raise FileNotFoundError(f"Scaler file missing at: {scaler_path}")

scaler = joblib.load(scaler_path)

# ------------------------------------------------
# LOAD MONGO URI FROM ENVIRONMENT
# ------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError(" ERROR: MONGO_URI environment variable not set on Render!")

client = MongoClient(MONGO_URI)
db = client["heartDB"]
collection = db["predictions"]

# ------------------------------------------------
# HELPER FUNCTION TO LOAD MODELS SAFELY
# ------------------------------------------------
def load_model(model_name):
    model_path = os.path.join(MODEL_DIR, f"{model_name}.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    return joblib.load(model_path)

# ------------------------------------------------
# ROUTES
# ------------------------------------------------
@app.route("/")
def home():
    return "Heart Disease Prediction API is Running ✔"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

        # Default model name
        model_name = data.get("model", "random_forest")

        model = load_model(model_name)

        # Extract features
        features = np.array([
            data["age"], data["sex"], data["cp"], data["trestbps"], data["chol"],
            data["fbs"], data["restecg"], data["thalach"], data["exang"],
            data["oldpeak"], data["slope"], data["ca"], data["thal"]
        ]).reshape(1, -1)

        # Scale
        features_scaled = scaler.transform(features)

        # Predict
        prediction = int(model.predict(features_scaled)[0])
        probability = float(model.predict_proba(features_scaled)[0][1])

        # Save to MongoDB
        record = {
            "input_data": data,
            "model_used": model_name,
            "prediction": prediction,
            "probability": probability,
            "timestamp": datetime.now()
        }
        collection.insert_one(record)

        return jsonify({
            "prediction": prediction,
            "probability": probability,
            "model_used": model_name
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history", methods=["GET"])
def history():
    records = list(collection.find({}, {"_id": 0}))
    return jsonify(records)

# ------------------------------------------------
# RUN APP (LOCAL MODE ONLY)
# ------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)