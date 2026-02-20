from flask import Flask, request, jsonify
import joblib
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# -----------------------------
# LOAD SCALER
# -----------------------------

scaler = joblib.load("../model/scaler.pkl")

# -----------------------------
# MONGODB CONNECTION
# -----------------------------

MONGO_URI = os.environ.get("mongodb+srv://riddhisharma24cse_db_user:XG2nlw73JCWSVJvF@cluster0.msy8fkt.mongodb.net/?appName=Cluster0")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(MONGO_URI)
db = client["heartDB"]
collection = db["predictions"]

# -----------------------------
# HELPER FUNCTION
# -----------------------------

def load_model(model_name):
    model_path = f"../model/{model_name}.pkl"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    else:
        raise FileNotFoundError(f"Model {model_name} not found")

# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def home():
    return "Heart Disease Prediction API Running"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

        # Default model
        model_name = data.get("model", "random_forest")

        model = load_model(model_name)

        features = np.array([
            data["age"],
            data["sex"],
            data["cp"],
            data["trestbps"],
            data["chol"],
            data["fbs"],
            data["restecg"],
            data["thalach"],
            data["exang"],
            data["oldpeak"],
            data["slope"],
            data["ca"],
            data["thal"]
        ]).reshape(1, -1)

        features_scaled = scaler.transform(features)

        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0][1]

        # Save to DB
        record = {
            "input_data": data,
            "model_used": model_name,
            "prediction": int(prediction),
            "probability": float(probability),
            "timestamp": datetime.now()
        }

        collection.insert_one(record)

        return jsonify({
            "prediction": int(prediction),
            "probability": float(probability),
            "model_used": model_name
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    records = list(collection.find({}, {"_id": 0}))
    return jsonify(records)


# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
