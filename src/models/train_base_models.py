import numpy as np
import joblib
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)

def load_data():
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    return X, y

def train_base_models():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "linear_svm": LinearSVC(C=1.0, class_weight="balanced", dual="auto", random_state=42),
        "logistic_regression": LogisticRegression(C=10.0, solver='saga', max_iter=1000, class_weight='balanced', random_state=42),
        "naive_bayes": MultinomialNB(),
        "random_forest": RandomForestClassifier(n_estimators=300, max_depth=80, min_samples_leaf=3, class_weight="balanced", n_jobs=-1, random_state=42)
    }

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        print(f"  {name} Accuracy: {accuracy_score(y_test, y_pred):.2%}")
        joblib.dump(model, MODEL_DIR / f"{name}.pkl")

    print(f"\nAll base models trained and saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_base_models()
