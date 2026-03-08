import csv
import numpy as np
import joblib
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_DIR = BASE_DIR / "saved_models"
OUT_FILE = MODEL_DIR / "evaluation_report.csv"

def load_data():
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    return X, y

def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    models = {
        "linear_svm": "linear_svm.pkl",
        "logistic_regression": "logistic_regression.pkl",
        "naive_bayes": "naive_bayes.pkl",
        "random_forest": "random_forest.pkl",
        "ensemble": "ensemble_model.pkl",
    }

    results = []
    for name, fname in models.items():
        path = MODEL_DIR / fname
        if not path.exists():
            print(f"Skipping {name}: model file not found at {path}")
            continue
        try:
            model = joblib.load(path)
        except Exception as e:
            print(f"Error loading {name}: {e}")
            continue

        try:
            y_pred = model.predict(X_test)
        except Exception as e:
            print(f"Error predicting with {name}: {e}")
            continue

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
        print(f"{name}: Accuracy={acc:.4f}, Macro-F1={f1:.4f}")
        results.append((name, acc, f1))

    if results:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["model", "accuracy", "macro_f1"])
            for r in results:
                writer.writerow([r[0], f"{r[1]:.4f}", f"{r[2]:.4f}"])
        print(f"\nSaved evaluation to {OUT_FILE}")

if __name__ == "__main__":
    main()
