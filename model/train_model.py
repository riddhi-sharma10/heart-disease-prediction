import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import json

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
    precision_score,
    recall_score,
    f1_score
)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

# -----------------------------
# 1. LOAD DATA
# -----------------------------

columns = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal", "target"
]

df = pd.read_csv("heart.csv", names=columns)

print("Initial Shape:", df.shape)

# -----------------------------
# 2. DATA CLEANING
# -----------------------------

df.replace("?", np.nan, inplace=True)
df = df.apply(pd.to_numeric)

print("\nMissing Values Before Cleaning:")
print(df.isnull().sum())

df.fillna(df.median(), inplace=True)

print("\nMissing Values After Cleaning:")
print(df.isnull().sum())

df["target"] = df["target"].apply(lambda x: 1 if x > 0 else 0)

# -----------------------------
# 3. EDA
# -----------------------------

plt.figure(figsize=(8,6))
sns.heatmap(df.corr(), cmap="coolwarm")
plt.title("Correlation Heatmap")
plt.savefig("heatmap.png")
plt.close()

# -----------------------------
# 4. FEATURES & TARGET
# -----------------------------

X = df.drop("target", axis=1)
y = df["target"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# -----------------------------
# 5. TRAIN MULTIPLE MODELS
# -----------------------------

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Random Forest": RandomForestClassifier(),
    "Gradient Boosting": GradientBoostingClassifier()
}

comparison_results = {}
best_model = None
best_accuracy = 0

for name, model in models.items():

    print(f"\nTraining {name}...")

    model.fit(X_train, y_train)
    joblib.dump(model, f"{name.replace(' ', '_').lower()}.pkl")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:,1]

    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)

    comparison_results[name] = {
        "accuracy": acc,
        "roc_auc": roc_auc
    }

    print(f"{name} Accuracy: {acc:.4f}")
    print(f"{name} ROC-AUC: {roc_auc:.4f}")

    if acc > best_accuracy:
        best_accuracy = acc
        best_model = model
        best_model_name = name
        best_y_pred = y_pred
        best_y_prob = y_prob
        best_fpr = fpr
        best_tpr = tpr
        best_roc_auc = roc_auc

print("\nBest Model Selected:", best_model_name)

# -----------------------------
# 6. SAVE MODEL COMPARISON
# -----------------------------

with open("model_comparison.json", "w") as f:
    json.dump(comparison_results, f)

# -----------------------------
# 7. SAVE EVALUATION METRICS
# -----------------------------

metrics = {
    "accuracy": best_accuracy,
    "precision": precision_score(y_test, best_y_pred),
    "recall": recall_score(y_test, best_y_pred),
    "f1_score": f1_score(y_test, best_y_pred),
    "roc_auc": best_roc_auc
}

with open("metrics.json", "w") as f:
    json.dump(metrics, f)

# Save Confusion Matrix
cm = confusion_matrix(y_test, best_y_pred)
np.save("confusion_matrix.npy", cm)

# Save ROC Curve
plt.figure()
plt.plot(best_fpr, best_tpr, label=f"AUC = {best_roc_auc:.2f}")
plt.plot([0,1],[0,1],'--')
plt.legend()
plt.title("ROC Curve")
plt.savefig("roc_curve.png")
plt.close()

# -----------------------------
# 8. FEATURE IMPORTANCE
# -----------------------------

if hasattr(best_model, "feature_importances_"):
    importances = best_model.feature_importances_
    feat_df = pd.DataFrame({
        "Feature": X.columns,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    print("\nFeature Importance:")
    print(feat_df)

# -----------------------------
# 9. SAVE BEST MODEL
# -----------------------------

joblib.dump(best_model, "heart_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("\nBest model and scaler saved successfully!")
