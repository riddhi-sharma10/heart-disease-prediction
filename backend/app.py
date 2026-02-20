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
# DATABASE
# ─────────────────────────────────────────────
USE_DB     = False
collection = None

try:
    client = MongoClient(
        "mongodb+srv://riddhisharma24cse_db_user:XG2nlw73JCWSVJvF@cluster0.msy8fkt.mongodb.net/?appName=Cluster0",
        serverSelectionTimeoutMS=5000
    )
    client.server_info()
    db         = client["heartDB"]
    collection = db["predictions"]
    USE_DB     = True
    print("✔ Connected to MongoDB Atlas")
except Exception as e:
    print(f"⚠  MongoDB unavailable — using local fallback: {FALLBACK_FILE}")
    print(f"   Reason: {e}")


# ─────────────────────────────────────────────
# FALLBACK FILE HELPERS
# ─────────────────────────────────────────────
def _read_fallback():
    if not os.path.exists(FALLBACK_FILE):
        return []
    try:
        with open(FALLBACK_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _append_fallback(record):
    records = _read_fallback()
    records.append(record)
    with open(FALLBACK_FILE, "w") as f:
        json.dump(records, f, indent=2)


# ─────────────────────────────────────────────
# SERIALIZER — makes MongoDB docs JSON-safe
# ─────────────────────────────────────────────
def serialize(doc):
    out = {}
    for k, v in doc.items():
        if k == "_id" or isinstance(v, ObjectId):
            continue                          # drop _id / ObjectId entirely
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = serialize(v)             # keep nested dicts (e.g. input_data)
        else:
            out[k] = v
    return out


# ─────────────────────────────────────────────
# NORMALISE — handles BOTH old & new records
# ─────────────────────────────────────────────
FEATURE_KEYS = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal"
]

def normalise_record(r):
    """
    Flatten a record so all 13 features always live at root level.

    Old format  →  { input_data:{age,sex,...}, prediction, probability, timestamp }
    New format  →  { age, sex, ..., model_used, prediction, probability, timestamp }

    The critical bug was: the old /history query excluded input_data BEFORE
    normalisation could read it, so all 14 records in MongoDB showed no features.

    Fix: fetch with {"_id": 0} only (keep input_data), THEN lift it here.
    """
    # If root is missing features but input_data has them → lift to root
    if "age" not in r and "input_data" in r and isinstance(r.get("input_data"), dict):
        for k, v in r["input_data"].items():
            if k not in r:          # never overwrite a real root-level value
                r[k] = v

    r.pop("input_data", None)       # remove nested copy

    # Guarantee all feature keys exist (None if genuinely missing)
    for key in FEATURE_KEYS:
        if key not in r:
            r[key] = None

    # Guarantee model_used exists
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
        "db":     "mongodb" if USE_DB else "local_json_file",
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

        # Build flat record — NO nested input_data, ever
        record = {k: data[k] for k in FEATURE_KEYS}
        record["model_used"]  = model_name
        record["prediction"]  = prediction
        record["probability"] = probability
        record["timestamp"]   = datetime.now().isoformat()

        # Persist
        if USE_DB and collection is not None:
            collection.insert_one(dict(record))
            print(f"  ✔ MongoDB   model={model_name}  prob={probability:.3f}")
        else:
            _append_fallback(record)
            print(f"  ✔ Fallback  model={model_name}  prob={probability:.3f}")

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
        if USE_DB and collection is not None:
            # ╔══════════════════════════════════════════════════════╗
            # ║  THE CRITICAL FIX                                    ║
            # ║  Exclude ONLY _id — keep input_data in the result    ║
            # ║  so normalise_record() can lift features to root.    ║
            # ║                                                       ║
            # ║  Old (broken): {"_id":0, "input_data":0}             ║
            # ║   → removed input_data BEFORE normalisation could    ║
            # ║     read it, so all 14 MongoDB records lost their     ║
            # ║     age/sex/chol/... fields entirely.                 ║
            # ║                                                       ║
            # ║  New (fixed):  {"_id":0}                             ║
            # ║   → input_data preserved, lifted to root, then       ║
            # ║     removed by normalise_record().                   ║
            # ╚══════════════════════════════════════════════════════╝
            raw     = list(collection.find({}, {"_id": 0}))   # ← only exclude _id
            records = [normalise_record(serialize(r)) for r in raw]
        else:
            records = [normalise_record(r) for r in _read_fallback()]

        print(f"  /history → returning {len(records)} records")
        return jsonify(records)

    except Exception as e:
        print(f"  /history error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    count = 0
    try:
        count = (collection.count_documents({})
                 if USE_DB and collection is not None
                 else len(_read_fallback()))
    except Exception:
        pass
    return jsonify({
        "api":          "ok",
        "models":       list(models.keys()),
        "scaler":       scaler is not None,
        "database":     "mongodb" if USE_DB else "local_json_file",
        "record_count": count,
    })


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)