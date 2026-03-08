import numpy as np
import joblib
import json
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_DIR = BASE_DIR / "saved_models"
REPORT_DIR = BASE_DIR / "docs/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    
    unique, counts = np.unique(y, return_counts=True)
    rare_classes = unique[counts < 5] # Increased threshold for CV
    if len(rare_classes) > 0:
        mask = ~np.isin(y, rare_classes)
        X = X[mask]
        y = y[mask]
    
    return X, y

def tune_models():
    X, y = load_data()
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42) # Reduced from 5 to 3
    
    models_params = {
        "logistic_regression": {
            "model": LogisticRegression(solver='saga', max_iter=1000, class_weight='balanced', random_state=42),
            "params": {
                "C": [1, 10], # Simplified
                "penalty": ["l2"] 
            }
        },
        "random_forest": {
            "model": RandomForestClassifier(class_weight='balanced', n_jobs=-1, random_state=42),
            "params": {
                "n_estimators": [100, 200], # Removed 500 to save RAM/time
                "max_depth": [None, 30]
            }
        },
        "linear_svm": {
            "model": LinearSVC(class_weight='balanced', dual='auto', max_iter=2000, random_state=42),
            "params": {
                "C": [0.1, 1, 10]
            }
        }
    }
    
    best_models = {}
    tuning_results = {}

    for name, config in models_params.items():
        print(f"Tuning {name}...")
        search = RandomizedSearchCV(
            config["model"], config["params"], 
            n_iter=5, cv=cv, scoring='accuracy', # Reduced from 10 to 5
            n_jobs=-1, random_state=42
        )
        search.fit(X, y)
        
        print(f"  Best Score: {search.best_score_:.4f}")
        print(f"  Best Params: {search.best_params_}")
        
        best_models[name] = search.best_estimator_
        tuning_results[name] = {
            "best_score": float(search.best_score_),
            "best_params": search.best_params_
        }
        
        # Save individual best models
        joblib.dump(search.best_estimator_, MODEL_DIR / f"{name}_best.pkl")

    # Save tuning summary
    with open(REPORT_DIR / "hyperparameter_tuning_results.json", "w") as f:
        json.dump(tuning_results, f, indent=4)
    
    print(f"Tuning complete. Results saved to {REPORT_DIR / 'hyperparameter_tuning_results.json'}")
    return best_models

if __name__ == "__main__":
    tune_models()
