import joblib
import numpy as np
from pathlib import Path
from src.preprocessing.nlp_preprocessor import preprocess_text

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "saved_models/ensemble_model.pkl"
VECTORIZER_PATH = BASE_DIR / "data/features/tfidf_vectorizer.pkl"
ENCODER_PATH = BASE_DIR / "data/features/label_encoder.pkl"

class DeveloperAssigner:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.encoder = None
        self.load_models()

    def load_models(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            print("Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")

    def predict(self, title: str, body: str, top_n: int = 5):
        if not self.model or not self.vectorizer or not self.encoder:
            return []

        combined_text = f"{title.strip()} {body.strip()}"
        clean_text = preprocess_text(combined_text)
        
        # Transform text to TF-IDF vector
        X = self.vectorizer.transform([clean_text])
        
        # Get probability scores
        probs = self.model.predict_proba(X)[0]
        
        # Get indices of top_n classes
        top_indices = np.argsort(probs)[-top_n:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "predicted_developer": self.encoder.classes_[idx],
                "confidence": float(probs[idx])
            })
            
        return results

# Singleton instance
assigner = DeveloperAssigner()

if __name__ == "__main__":
    # Quick test
    test_title = "App crashes on startup"
    test_body = "The application freezes and then crashes when I click the login button."
    predictions = assigner.predict(test_title, test_body)
    print(f"Predictions for: {test_title}")
    for p in predictions:
        print(f"- {p['developer']}: {p['confidence']:.2%}")
