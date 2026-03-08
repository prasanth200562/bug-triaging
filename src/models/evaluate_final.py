import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURE_DIR = BASE_DIR / "data/features"
MODEL_FILE = BASE_DIR / "saved_models/ensemble_model.pkl"
RF_FILE = BASE_DIR / "saved_models/random_forest.pkl" # Changed from _best.pkl

def load_data():
    print("Loading features...")
    loader = np.load(FEATURE_DIR / "tfidf_features.npz")
    X = csr_matrix((loader["data"], loader["indices"], loader["indptr"]), shape=loader["shape"])
    y = np.load(FEATURE_DIR / "labels.npy")
    encoder = joblib.load(FEATURE_DIR / "label_encoder.pkl")
    return X, y, encoder

def main():
    try:
        X, y, encoder = load_data()
        
        # Split exactly as training did
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Load Ensemble
        if MODEL_FILE.exists():
            print(f"Loading {MODEL_FILE.name}...")
            model = joblib.load(MODEL_FILE)
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            print(f"\n>>> ENSEMBLE TEST ACCURACY: {acc:.4%}")
        else:
            print("Ensemble model not found.")

        # Load Random Forest
        if RF_FILE.exists():
            print(f"Loading {RF_FILE.name}...")
            rf = joblib.load(RF_FILE)
            y_pred_rf = rf.predict(X_test)
            acc_rf = accuracy_score(y_test, y_pred_rf)
            print(f"\n>>> RANDOM FOREST ACCURACY: {acc_rf:.4%}")
            
        # Load and Evaluate Other Models
        svm_file = BASE_DIR / "saved_models/linear_svm.pkl" # Changed from _best.pkl
        if svm_file.exists():
            print(f"Loading {svm_file.name}...")
            svm = joblib.load(svm_file)
            y_pred_svm = svm.predict(X_test)
            print(f"\n>>> LINEAR SVM ACCURACY: {accuracy_score(y_test, y_pred_svm):.4%}")
            
            # Feature Importance Analysis (Check for Cheating)
            print("\n--- TOP PREDICTIVE WORDS (Checking for Cheating) ---")
            vectorizer = joblib.load(BASE_DIR / "data/features/tfidf_vectorizer.pkl")
            feature_names = vectorizer.get_feature_names_out()
            
            # Check specific classes
            target_devs = ['Tyriar', 'DonJayamanne', 'roblourens']
            for target in target_devs:
                if target in encoder.classes_:
                    idx = list(encoder.classes_).index(target)
                    top10_indices = np.argsort(svm.coef_[idx])[-10:]
                    top10_words = [feature_names[j] for j in top10_indices]
                    print(f"\nDeveloper '{target}' Top Features: {top10_words}")

        lr_file = BASE_DIR / "saved_models/logistic_regression.pkl" # Changed from _best.pkl
        if lr_file.exists():
            print(f"Loading {lr_file.name}...")
            lr = joblib.load(lr_file)
            y_pred_lr = lr.predict(X_test)
            print(f"\n>>> LOGISTIC REGRESSION ACCURACY: {accuracy_score(y_test, y_pred_lr):.4%}")

        nb_file = BASE_DIR / "saved_models/naive_bayes.pkl"
        if nb_file.exists():
            print(f"Loading {nb_file.name}...")
            nb = joblib.load(nb_file)
            y_pred_nb = nb.predict(X_test)
            print(f"\n>>> NAIVE BAYES ACCURACY: {accuracy_score(y_test, y_pred_nb):.4%}")

    except Exception as e:
        print(f"Error evaluation: {e}")

if __name__ == "__main__":
    main()
