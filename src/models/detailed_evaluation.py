import joblib
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_DIR = BASE_DIR / "saved_models"

def load_data():
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    return X, y

def find_ensemble():
    # prefer user 4-model ensemble, fallback to trained ensemble
    for name in ("ensemble_model_4.pkl", "ensemble_model.pkl"):
        p = MODEL_DIR / name
        if p.exists():
            return p
    return None

def main(low_thresh=0.4, high_thresh=0.7):
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    ens_path = find_ensemble()
    if not ens_path:
        print("No ensemble model found in saved_models/")
        return

    print(f"Using ensemble: {ens_path.name}")
    import sys
    sys.path.insert(0, str(BASE_DIR))
    model = joblib.load(ens_path)

    # Predict probabilities where possible; fallback to predict
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X_test)
    else:
        preds = model.predict(X_test)
        probs = np.zeros((len(preds), len(np.unique(y_test))))
        for i, p in enumerate(preds):
            probs[i, int(p)] = 1.0

    max_probs = probs.max(axis=1)
    preds = probs.argmax(axis=1)

    print('\nClassification report:')
    print(classification_report(y_test, preds, zero_division=0))

    print('\nConfusion matrix (partial):')
    cm = confusion_matrix(y_test, preds)
    print(cm)

    # Per-class confidence breakdown
    classes = np.unique(y_test)
    print('\nPer-class confidence rates (low<', low_thresh, ', high>=', high_thresh, '):')
    for cls in classes:
        mask = (y_test == cls)
        if mask.sum() == 0:
            continue
        low_rate = (max_probs[mask] < low_thresh).sum() / mask.sum()
        high_rate = (max_probs[mask] >= high_thresh).sum() / mask.sum()
        print(f"Class {cls}: samples={mask.sum()}, low_rate={low_rate:.2%}, high_rate={high_rate:.2%}")

if __name__ == '__main__':
    main()
