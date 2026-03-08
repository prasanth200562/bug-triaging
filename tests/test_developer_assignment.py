import os
import joblib
import numpy as np
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / 'saved_models'
FEATURE_DIR = BASE / 'data' / 'features'

def test_developer_assignment_ensemble_4():
    # Check required artifacts
    ensemble_path = MODEL_DIR / 'ensemble_model_4.pkl'
    vec_path = FEATURE_DIR / 'tfidf_vectorizer.pkl'
    enc_path = FEATURE_DIR / 'label_encoder.pkl'

    assert ensemble_path.exists(), f"Missing ensemble model: {ensemble_path}"
    assert vec_path.exists(), f"Missing vectorizer: {vec_path}"
    assert enc_path.exists(), f"Missing encoder: {enc_path}"

    # Make sure project root is importable so custom wrapper classes can be resolved when unpickling
    sys.path.insert(0, str(BASE))

    ensemble = joblib.load(ensemble_path)
    vectorizer = joblib.load(vec_path)
    encoder = joblib.load(enc_path)

    sample_text = "Application crashes when saving a file"
    X = vectorizer.transform([sample_text])

    # Ensure predict_proba works (soft voting requires it)
    if hasattr(ensemble, 'predict_proba'):
        probs = ensemble.predict_proba(X)
        assert probs.shape[0] == 1
        top_idx = int(np.argmax(probs[0]))
        assert 0 <= top_idx < len(encoder.classes_)
    else:
        # fallback: use predict
        pred = ensemble.predict(X)
        assert len(pred) == 1

if __name__ == '__main__':
    test_developer_assignment_ensemble_4()
    print('Developer assignment ensemble-4 test passed')
