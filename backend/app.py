from flask import Flask, request, jsonify
import joblib
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ------------------------------------------------
# DEFINE BASE DIRECTORY
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

# ------------------------------------------------
# LOAD SCALER ONCE
# ------------------------------------------------
scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
scaler = joblib.load(scaler_path)

# ------------------------------------------------
# LOAD ALL MODELS ONCE (NO RELOADING!)
# ------------------------------------------------
models = {
    "random_forest": joblib.load(os.path.join(MODEL_DIR, "random_forest.pkl")),
    "logistic_regression": joblib.load(os.path.join(MODEL_DIR, "logistic_regression.pkl")),
    "gradient_boosting": joblib.load(os.path.join(MODEL_DIR, "gradient_boosting.pkl")),
}

print("✔ Models Loaded Successfully")

# ------------------------------------------------
# MONGODB CONNECTION
# ------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError("ERROR: MONGO_URI environment variable missing!")

client = MongoClient(MONGO_URI)
db = client["heartDB"]
collection = db["predictions"]

# ------------------------------------------------
# ROUTES
# ------------------------------------------------
@app.route("/")
def home():
    return "Heart Disease Prediction API Running ✔"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

        # Choose model
        model_name = data.get("model", "random_forest")
        model = models.get(model_name, models["random_forest"])

        # Prepare features
        features = np.array([
            data["age"], data["sex"], data["cp"], data["trestbps"], data["chol"],
            data["fbs"], data["restecg"], data["thalach"], data["exang"],
            data["oldpeak"], data["slope"], data["ca"], data["thal"]
        ]).reshape(1, -1)

        features_scaled = scaler.transform(features)

        # Prediction
        prediction = int(model.predict(features_scaled)[0])
        probability = float(model.predict_proba(features_scaled)[0][1])

        # Save to DB
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
# LOCAL RUN
# ------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)