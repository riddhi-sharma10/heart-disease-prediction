from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import json

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR     = os.path.join(BASE_DIR, "..", "model")
FALLBACK_FILE = os.path.join(BASE_DIR, "predictions_fallback.json")

# ─────────────────────────────────────────────
# LOAD SCALER & MODELS
# ─────────────────────────────────────────────
try:
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    models = {
        "random_forest":       joblib.load(os.path.join(MODEL_DIR, "random_forest.pkl")),
        "logistic_regression": joblib.load(os.path.join(MODEL_DIR, "logistic_regression.pkl")),
        "gradient_boosting":   joblib.load(os.path.join(MODEL_DIR, "gradient_boosting.pkl")),
    }
    print("✔ Models loaded successfully")
except Exception as e:
    print(f"✘ Error loading models: {e}")
    scaler = None
    models = {}

# ─────────────────────────────────────────────
# MONGODB CONNECTION
# ─────────────────────────────────────────────
client     = MongoClient("mongodb+srv://riddhisharma24cse_db_user:XG2nlw73JCWSVJvF@cluster0.msy8fkt.mongodb.net/?appName=Cluster0")
db         = client["heartDB"]
collection = db["predictions"]


# ─────────────────────────────────────────────
# FALLBACK FILE HELPERS
# ─────────────────────────────────────────────
def _read_fallback():
    if not os.path.exists(FALLBACK_FILE):
        return []
    try:
        with open(FALLBACK_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _append_fallback(record):
    records = _read_fallback()
    records.append(record)
    with open(FALLBACK_FILE, "w") as f:
        json.dump(records, f, indent=2, default=str)


# ─────────────────────────────────────────────
# SERIALIZER — makes MongoDB docs JSON-safe
# ─────────────────────────────────────────────
def serialize(doc):
    out = {}
    for k, v in doc.items():
        if k == "_id" or isinstance(v, ObjectId):
            continue
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = serialize(v)
        else:
            out[k] = v
    return out


# ─────────────────────────────────────────────
# NORMALISE — handles BOTH old & new records
# Old format: { input_data:{age,sex,...}, prediction, probability, timestamp }
# New format: { age, sex, ..., model_used, prediction, probability, timestamp }
# ─────────────────────────────────────────────
FEATURE_KEYS = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal"
]

def normalise_record(r):
    if "age" not in r and "input_data" in r and isinstance(r.get("input_data"), dict):
        for k, v in r["input_data"].items():
            if k not in r:
                r[k] = v
    r.pop("input_data", None)
    for key in FEATURE_KEYS:
        if key not in r:
            r[key] = None
    if "model_used" not in r:
        r["model_used"] = "unknown"
    return r


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "status": "CardioScan API running ✔",
        "models": list(models.keys()),
    })


@app.route("/predict", methods=["POST"])
def predict():
    if scaler is None or not models:
        return jsonify({"error": "Models not loaded. Check model directory."}), 503

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No JSON body received."}), 400

        # Resolve model
        model_name = str(data.get("model", "random_forest")).strip()
        if model_name not in models:
            model_name = "random_forest"
        model = models[model_name]

        # Validate all 13 features present
        missing = [k for k in FEATURE_KEYS if k not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        # Inference
        features        = np.array([float(data[k]) for k in FEATURE_KEYS]).reshape(1, -1)
        features_scaled = scaler.transform(features)
        prediction      = int(model.predict(features_scaled)[0])
        probability     = float(model.predict_proba(features_scaled)[0][1])

        # Build flat record — NO nested input_data
        record = {k: data[k] for k in FEATURE_KEYS}
        record["model_used"]  = model_name
        record["prediction"]  = prediction
        record["probability"] = probability
        record["timestamp"]   = datetime.now().isoformat()

        # Save to MongoDB, fallback to local file if it fails
        try:
            collection.insert_one(dict(record))
            print(f"  ✔ MongoDB   model={model_name}  prob={probability:.3f}")
        except Exception as db_err:
            print(f"  ⚠ MongoDB write failed: {db_err} — saving to fallback")
            _append_fallback(record)

        return jsonify({
            "prediction":  prediction,
            "probability": probability,
            "model_used":  model_name,
        })

    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    try:
        # Fetch from MongoDB — keep input_data so normalise_record() can lift old records
        raw     = list(collection.find({}, {"_id": 0}))
        records = [normalise_record(serialize(r)) for r in raw]

        # Also merge any local fallback records (written during connectivity loss)
        fallback_records = _read_fallback()
        if fallback_records:
            records.extend([normalise_record(r) for r in fallback_records])

        # Sort by timestamp
        records.sort(key=lambda r: r.get("timestamp") or "")

        print(f"  /history → {len(records)} records")
        return jsonify(records)

    except Exception as e:
        print(f"  /history error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    try:
        count = collection.count_documents({})
    except Exception:
        count = 0
    return jsonify({
        "api":          "ok",
        "models":       list(models.keys()),
        "scaler":       scaler is not None,
        "record_count": count,
    })


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)