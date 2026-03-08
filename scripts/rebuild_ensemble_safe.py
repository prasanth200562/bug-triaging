import joblib
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report

BASE = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE / 'data' / 'features'
SAVED_MODELS = BASE / 'saved_models'
EXPERIMENTS = BASE / 'experiments'
OUT_ROOT = EXPERIMENTS / 'ensemble_rebuild'

def load_data():
    loader = np.load(FEATURE_DIR / 'tfidf_features.npz')
    X = csr_matrix((loader['data'], loader['indices'], loader['indptr']), shape=loader['shape'])
    y = np.load(FEATURE_DIR / 'labels.npy')
    return X, y

def latest_experiment(folder):
    if not folder.exists():
        return None
    subs = [p for p in folder.iterdir() if p.is_dir()]
    if not subs:
        return None
    subs_sorted = sorted(subs, key=lambda p: p.name)
    return subs_sorted[-1]

def backup_models():
    bk_script = BASE / 'scripts' / 'backup_models.py'
    if bk_script.exists():
        print('Running backup script...')
        import subprocess
        subprocess.run(['python', str(bk_script)])
    else:
        print('No backup script found; skipping backup')

def find_model(expt_folder, name):
    # name like 'linear_svm' -> file linear_svm_best.pkl in expt
    if expt_folder:
        candidate = expt_folder / f"{name}_best.pkl"
        if candidate.exists():
            return candidate
    # fallback to saved_models
    mapping = {
        'linear_svm': 'linear_svm.pkl',
        'logistic_regression': 'logistic_regression.pkl',
        'naive_bayes': 'naive_bayes.pkl',
        'random_forest': 'random_forest.pkl'
    }
    return SAVED_MODELS / mapping.get(name, '')

def main():
    # 1) backup
    backup_models()

    # 2) load data and split
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 3) find latest experiment with tuned models
    expt = latest_experiment(EXPERIMENTS / 'quick_tune')
    if expt:
        print(f'Using tuned models from: {expt}')
    else:
        print('No tuned experiment found; falling back to production saved_models')

    # 4) load models
    model_files = {
        'logistic_regression': find_model(expt, 'logistic_regression'),
        'random_forest': find_model(expt, 'random_forest'),
        'linear_svm': find_model(expt, 'linear_svm'),
        'naive_bayes': find_model(expt, 'naive_bayes')
    }

    models = {}
    for k, p in model_files.items():
        if p and p.exists():
            models[k] = joblib.load(p)
            print(f'Loaded {k} from {p}')
        else:
            raise FileNotFoundError(f'Model file for {k} not found at {p}')

    # 5) Calibrate SVM
    print('Calibrating SVM probabilities via CalibratedClassifierCV(cv=3)')
    svm = models['linear_svm']
    svm_cal = CalibratedClassifierCV(svm, method='sigmoid', cv=3)
    svm_cal.fit(X_train, y_train)

    # 6) Build ensemble (soft voting)
    estimators = [
        ('lr', models['logistic_regression']),
        ('rf', models['random_forest']),
        ('svm', svm_cal),
        ('nb', models['naive_bayes'])
    ]
    ensemble = VotingClassifier(estimators=estimators, voting='soft', n_jobs=-1)

    # Fit ensemble on training data (will refit clones of estimators)
    print('Fitting ensemble on training data (in experiments workspace)')
    ensemble.fit(X_train, y_train)

    # 7) Evaluate
    y_pred = ensemble.predict(X_test)
    y_prob = ensemble.predict_proba(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    report = classification_report(y_test, y_pred, zero_division=0)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = OUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(ensemble, out_dir / 'ensemble_rebuilt.pkl')
    with open(out_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump({'accuracy': acc, 'macro_f1': f1}, f, indent=2)
    with open(out_dir / 'classification_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f'Ensemble rebuilt and saved to {out_dir}')
    print(f'Accuracy: {acc:.4f}, Macro-F1: {f1:.4f}')

if __name__ == '__main__':
    main()
