from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from datetime import datetime
from bson import ObjectId
import os
import json
import hashlib   # NEW ✔

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")
FALLBACK_FILE = os.path.join(BASE_DIR, "predictions_fallback.json")

# ─────────────────────────────────────────────
# SHA256 HASH FN — for version freezing
# ─────────────────────────────────────────────
def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return "missing"

MODEL_VERSION_INFO = {}   # NEW ✔

# ─────────────────────────────────────────────
# LOAD SCALER & MODELS (FROZEN)
# ─────────────────────────────────────────────
def load_frozen_model(name, file_path):
    """Load model, compute hash, freeze version info."""
    model = joblib.load(file_path)
    MODEL_VERSION_INFO[name] = {
        "path": file_path,
        "sha256": file_hash(file_path)
    }
    return model

try:
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

    models = {
        "random_forest": load_frozen_model(
            "random_forest", os.path.join(MODEL_DIR, "random_forest.pkl")
        ),
        "logistic_regression": load_frozen_model(
            "logistic_regression", os.path.join(MODEL_DIR, "logistic_regression.pkl")
        ),
        "gradient_boosting": load_frozen_model(
            "gradient_boosting", os.path.join(MODEL_DIR, "gradient_boosting.pkl")
        ),
    }

    print("\n✔ MODELS LOADED & FROZEN")
    for m, info in MODEL_VERSION_INFO.items():
        print(f"   {m}: {info['sha256']}")

except Exception as e:
    print(f"✘ Error loading models: {e}")
    scaler = None
    models = {}

# ─────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────
MONGO_URI = (
    "mongodb+srv://riddhisharma24cse_db_user:XG2nlw73JCWSVJvF"
    "@cluster0.msy8fkt.mongodb.net/heartDB?retryWrites=true&w=majority&appName=Cluster0"
)

USE_DB = False
collection = None
_db_error = ""

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db = client["heartDB"]
    collection = db["predictions"]
    USE_DB = True
    print("✔ Connected to MongoDB Atlas")
except Exception as e:
    _db_error = str(e)
    print("⚠ MongoDB unavailable → using fallback JSON file")

# ─────────────────────────────────────────────
# FALLBACK FILE HELPERS
# ─────────────────────────────────────────────
def _read_fallback():
    if not os.path.exists(FALLBACK_FILE):
        return []
    try:
        with open(FALLBACK_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def _append_fallback(record):
    data = _read_fallback()
    data.append(record)
    with open(FALLBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────
# SERIALIZER
# ─────────────────────────────────────────────
def serialize(doc):
    out = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

# ─────────────────────────────────────────────
# NORMALISER
# ─────────────────────────────────────────────
FEATURE_KEYS = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal"
]

def normalise_record(r):
    if "input_data" in r:
        for k, v in r["input_data"].items():
            r[k] = v
        r.pop("input_data", None)

    for k in FEATURE_KEYS:
        r.setdefault(k, None)

    r.setdefault("model_used", "unknown")
    return r

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return jsonify({
        "status": "CardioScan API running ✔",
        "models": MODEL_VERSION_INFO,
        "db": "mongodb_atlas" if USE_DB else "local_json",
    })

# NEW ✔
@app.route("/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "status": "frozen_models",
        "models": MODEL_VERSION_INFO
    })

@app.route("/predict", methods=["POST"])
def predict():
    if scaler is None:
        return jsonify({"error": "Models not loaded"}), 503

    try:
        data = request.get_json(force=True)

        # Identify model
        model_name = data.get("model", "random_forest")
        if model_name not in models:
            model_name = "random_forest"
        model = models[model_name]

        print(f"[PREDICT] Using model: {model_name} ({MODEL_VERSION_INFO[model_name]['sha256']})")

        # Validate features
        features = np.array([float(data[k]) for k in FEATURE_KEYS]).reshape(1, -1)

        feats_scaled = scaler.transform(features)
        pred = int(model.predict(feats_scaled)[0])
        prob = float(model.predict_proba(feats_scaled)[0][1])

        record = {k: data[k] for k in FEATURE_KEYS}
        record["model_used"] = model_name
        record["probability"] = prob
        record["prediction"] = pred
        record["timestamp"] = datetime.now().isoformat()

        # Save record
        if USE_DB:
            try:
                collection.insert_one(record)
                stored_in = "mongodb_atlas"
            except:
                _append_fallback(record)
                stored_in = "local_json"
        else:
            _append_fallback(record)
            stored_in = "local_json"

        return jsonify({
            "prediction": pred,
            "probability": prob,
            "model_used": model_name,
            "model_hash": MODEL_VERSION_INFO[model_name]["sha256"],
            "stored_in": stored_in
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history")
def history():
    try:
        if USE_DB:
            raw = list(collection.find({}, {"_id": 0}))
            records = [normalise_record(serialize(r)) for r in raw]
        else:
            records = _read_fallback()

        return jsonify(records)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({
        "api": "ok",
        "models_loaded": list(models.keys()),
        "frozen_hashes": MODEL_VERSION_INFO,
        "db": "mongodb_atlas" if USE_DB else "local_json",
    })

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)