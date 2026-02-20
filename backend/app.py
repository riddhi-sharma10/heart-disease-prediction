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

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# PATHS  (all absolute so cwd never matters)
# ─────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR     = os.path.join(BASE_DIR, "..", "model")
FALLBACK_FILE = os.path.join(BASE_DIR, "predictions_fallback.json")   # absolute path

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
# DATABASE  — verbose diagnostics on failure
# ─────────────────────────────────────────────
MONGO_URI = "mongodb+srv://riddhisharma24cse_db_user:XG2nlw73JCWSVJvF@cluster0.msy8fkt.mongodb.net/heartDB?retryWrites=true&w=majority&appName=Cluster0"
USE_DB     = False
collection = None
_db_error  = ""          # store the reason so /health can report it

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    # Force an actual round-trip to Atlas to confirm connectivity
    client.admin.command("ping")
    db         = client["heartDB"]
    collection = db["predictions"]
    USE_DB     = True
    print("✔ Connected to MongoDB Atlas")
except ServerSelectionTimeoutError as e:
    _db_error = (
        "Cannot reach Atlas — check (1) your internet connection, "
        "(2) that your IP is whitelisted in Atlas → Network Access, "
        f"(3) credentials are correct.  Detail: {e}"
    )
    print(f"⚠  {_db_error}")
    print(f"   Falling back to local file: {FALLBACK_FILE}")
except OperationFailure as e:
    _db_error = f"Atlas auth failed — bad username/password. Detail: {e}"
    print(f"⚠  {_db_error}")
    print(f"   Falling back to local file: {FALLBACK_FILE}")
except Exception as e:
    _db_error = str(e)
    print(f"⚠  MongoDB error: {_db_error}")
    print(f"   Falling back to local file: {FALLBACK_FILE}")


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
# SERIALIZER  — makes MongoDB docs JSON-safe
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
# NORMALISE  — handles BOTH old & new record formats
#
#  Old (2 days ago):  { input_data:{age,sex,...}, prediction, probability, timestamp }
#  New (flat):        { age, sex, ..., model_used, prediction, probability, timestamp }
# ─────────────────────────────────────────────
FEATURE_KEYS = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal"
]

def normalise_record(r):
    # Lift nested input_data fields to root level (old format fix)
    if "age" not in r and "input_data" in r and isinstance(r.get("input_data"), dict):
        for k, v in r["input_data"].items():
            if k not in r:
                r[k] = v

    r.pop("input_data", None)

    # Guarantee all feature keys exist
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
        "status":   "CardioScan API running ✔",
        "db":       "mongodb_atlas" if USE_DB else "local_json_file",
        "db_error": _db_error if not USE_DB else None,
        "models":   list(models.keys()),
        "fallback": FALLBACK_FILE,
    })


@app.route("/debug/db", methods=["GET"])
def debug_db():
    """
    Diagnostic endpoint — call http://127.0.0.1:5000/debug/db from your browser
    to see exactly why MongoDB is or isn't connected.
    """
    status = {
        "USE_DB":       USE_DB,
        "db_error":     _db_error,
        "fallback_path": FALLBACK_FILE,
        "fallback_exists": os.path.exists(FALLBACK_FILE),
        "fallback_count": len(_read_fallback()),
    }
    if USE_DB and collection is not None:
        try:
            status["atlas_count"] = collection.count_documents({})
            # Show a sample record (without _id) so you can inspect the format
            sample = collection.find_one({}, {"_id": 0})
            status["sample_record"] = serialize(sample) if sample else None
        except Exception as e:
            status["atlas_error"] = str(e)
    return jsonify(status)


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

        # Persist
        if USE_DB and collection is not None:
            try:
                collection.insert_one(dict(record))
                stored_in = "mongodb_atlas"
                print(f"  ✔ MongoDB   model={model_name}  prob={probability:.3f}")
            except Exception as db_err:
                # Atlas write failed mid-session — fall back gracefully
                print(f"  ⚠ Atlas write failed: {db_err} — writing to fallback")
                _append_fallback(record)
                stored_in = "local_json_fallback"
        else:
            _append_fallback(record)
            stored_in = "local_json_fallback"
            print(f"  ✔ Fallback  model={model_name}  prob={probability:.3f}")

        return jsonify({
            "prediction":  prediction,
            "probability": probability,
            "model_used":  model_name,
            "stored_in":   stored_in,
        })

    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    try:
        records = []

        if USE_DB and collection is not None:
            # Exclude ONLY _id — keep input_data so normalise_record() can lift it
            raw     = list(collection.find({}, {"_id": 0}))
            records = [normalise_record(serialize(r)) for r in raw]
            print(f"  /history → {len(records)} records from MongoDB Atlas")
        else:
            records = [normalise_record(r) for r in _read_fallback()]
            print(f"  /history → {len(records)} records from local fallback")

        # ── MERGE: if fallback file also has records, include them too ──────
        # This handles the case where some predictions went to Atlas and some
        # to the local file (e.g. during connectivity loss).
        if USE_DB and os.path.exists(FALLBACK_FILE):
            fallback_records = _read_fallback()
            if fallback_records:
                normalised_fb = [normalise_record(r) for r in fallback_records]
                records.extend(normalised_fb)
                print(f"  /history → merged {len(fallback_records)} local fallback records too")

        # Sort by timestamp ascending (newest last) — tolerant of missing field
        try:
            records.sort(key=lambda r: r.get("timestamp") or "")
        except Exception:
            pass

        return jsonify(records)

    except Exception as e:
        print(f"  /history error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    count = 0
    try:
        if USE_DB and collection is not None:
            count = collection.count_documents({})
        else:
            count = len(_read_fallback())
    except Exception:
        pass

    return jsonify({
        "api":          "ok",
        "models":       list(models.keys()),
        "scaler":       scaler is not None,
        "database":     "mongodb_atlas" if USE_DB else "local_json_file",
        "db_error":     _db_error if not USE_DB else None,
        "record_count": count,
        "fallback_path": FALLBACK_FILE,
    })


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)