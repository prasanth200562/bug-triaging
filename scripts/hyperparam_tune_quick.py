import json
from pathlib import Path
from datetime import datetime
import numpy as np
import joblib
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import make_scorer, f1_score

BASE = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE / 'data' / 'features'
OUT_ROOT = BASE / 'experiments' / 'quick_tune'

def load_data():
    loader = np.load(FEATURE_DIR / 'tfidf_features.npz')
    X = csr_matrix((loader['data'], loader['indices'], loader['indptr']), shape=loader['shape'])
    y = np.load(FEATURE_DIR / 'labels.npy')
    return X, y

def main(n_iter=12, cv=3, random_state=42):
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state, stratify=y)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = OUT_ROOT / ts
    out_dir.mkdir()

    scorer = make_scorer(f1_score, average='macro', zero_division=0)

    jobs = [
        ('linear_svm', LinearSVC(random_state=random_state, max_iter=5000), {
            'C': [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
        }),
        ('logistic_regression', LogisticRegression(solver='saga', max_iter=2000, random_state=random_state), {
            'C': [0.01, 0.1, 1.0, 5.0, 10.0],
            'penalty': ['l2']
        }),
        ('random_forest', RandomForestClassifier(random_state=random_state, n_jobs=-1), {
            'n_estimators': [100, 200, 400],
            'max_depth': [20, 50, 80, None],
            'min_samples_leaf': [1, 2, 4]
        })
    ]

    summary = {}
    for name, estimator, param_dist in jobs:
        print(f"Tuning {name} with RandomizedSearchCV ({n_iter} iterations)...")
        rs = RandomizedSearchCV(estimator, param_distributions=param_dist, n_iter=n_iter, scoring=scorer, cv=cv, random_state=random_state, n_jobs=-1, verbose=1)
        rs.fit(X_train, y_train)
        best = rs.best_estimator_
        joblib.dump(best, out_dir / f"{name}_best.pkl")
        summary[name] = {
            'best_score': float(rs.best_score_),
            'best_params': rs.best_params_
        }
        print(f"{name} best_score={rs.best_score_:.4f}")

    # Save summary
    with open(out_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"Tuning complete. Results saved to {out_dir}")

if __name__ == '__main__':
    main()
