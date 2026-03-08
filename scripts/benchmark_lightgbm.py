import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

BASE = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE / 'data' / 'features'

def load_data():
    loader = np.load(FEATURE_DIR / 'tfidf_features.npz')
    X = csr_matrix((loader['data'], loader['indices'], loader['indptr']), shape=loader['shape'])
    y = np.load(FEATURE_DIR / 'labels.npy')
    return X, y

def main():
    try:
        import lightgbm as lgb
    except Exception as e:
        print('lightgbm not installed:', e)
        return

    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = lgb.LGBMClassifier(n_estimators=500, random_state=42)
    print('Training LightGBM (may take a moment)...')
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    print(f'LightGBM Accuracy: {acc:.4f}, Macro-F1: {f1:.4f}')

if __name__ == '__main__':
    main()
