import numpy as np
import joblib
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_DIR = BASE_DIR / "saved_models"

def load_data():
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    return X, y

def train_ensemble():
    X, y = load_data()
    
    # Stratified Split (Same seed as other models for consistency)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Load best-tuned models
    # Note: We re-instantiate them because the saved pkls might be trained on old data
    # (Checking if best params exist would be better, but for now we trust the "best" pkls have good params)
    print("Loading base models for Ensemble...")
    
    # 1. Logistic Regression
    lr_best = joblib.load(MODEL_DIR / "logistic_regression.pkl")
    
    # 2. Random Forest
    rf_best = joblib.load(MODEL_DIR / "random_forest.pkl")
    
    # 3. SVM (Needs calibration for Soft Voting)
    from sklearn.calibration import CalibratedClassifierCV
    svm_best = joblib.load(MODEL_DIR / "linear_svm.pkl")
    svm_calibrated = CalibratedClassifierCV(svm_best, method='sigmoid', cv='prefit') 
    # NOTE: 'prefit' assumes svm_best is already fitted. 
    # But if input features changed (new grouping), we MUST re-fit.
    # Safe bet: Create new CalibratedClassifierCV with the base estimator and cv=5
    svm_calibrated = CalibratedClassifierCV(svm_best, method='sigmoid', cv=3)

    ensemble = VotingClassifier(
        estimators=[
            ('lr', lr_best),
            ('rf', rf_best),
            ('svm', svm_calibrated)
        ],
        voting='soft', # Soft voting usually beats hard voting
        n_jobs=-1
    )
    
    print("Training Ensemble Model (Soft Voting)...")
    ensemble.fit(X_train, y_train)
    
    y_pred = ensemble.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nEnsemble Accuracy: {acc:.2%}")
    
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save ensemble
    joblib.dump(ensemble, MODEL_DIR / "ensemble_model.pkl")
    print(f"Ensemble model saved to {MODEL_DIR / 'ensemble_model.pkl'}")

if __name__ == "__main__":
    train_ensemble()
