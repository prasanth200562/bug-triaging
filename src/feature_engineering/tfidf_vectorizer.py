import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import sys
import os

# =====================================================
# 1. SETUP PATHS
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from database.db_connection import SessionLocal
from api import models

INPUT_FILE = BASE_DIR / "data/processed/bug_reports_nlp_ready.json"
FEATURE_DIR = BASE_DIR / "data/features"
FEATURE_DIR.mkdir(parents=True, exist_ok=True)

# Artifacts to save
TFIDF_MATRIX_FILE = FEATURE_DIR / "tfidf_features.npz"
TFIDF_VECTORIZER_FILE = FEATURE_DIR / "tfidf_vectorizer.pkl"
LABELS_FILE = FEATURE_DIR / "labels.npy"
LABEL_ENCODER_FILE = FEATURE_DIR / "label_encoder.pkl"

# =====================================================
# 2. LOAD AND PREPARE DATA
# =====================================================
print(f"Loading base data from: {INPUT_FILE}")

texts = []
assignees = []

# Load from JSON
try:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    # Filter valid JSON samples
    valid_json = [
        item for item in json_data 
        if item.get("combined_text") and item.get("assignee")
    ]
    texts.extend([item["combined_text"] for item in valid_json])
    assignees.extend([item["assignee"] for item in valid_json])
    print(f"Loaded {len(valid_json)} valid samples from JSON")
except FileNotFoundError:
    print(f"Warning: Base JSON file not found at {INPUT_FILE}")

# Load from Database (Verified Retrain Samples)
print("Fetching verified samples from Database (RetrainQueue)...")
db = SessionLocal()
try:
    from src.preprocessing.nlp_preprocessor import preprocess_text
    
    # Get all pending or previously retrained samples
    db_samples = db.query(models.RetrainQueue).all()
    db_count = 0
    
    for sample in db_samples:
        combined_text = f"{sample.title} {sample.body}"
        processed_text = preprocess_text(combined_text)
        
        if processed_text.strip() and sample.verified_developer:
            texts.append(processed_text)
            assignees.append(sample.verified_developer)
            db_count += 1
            
    print(f"Loaded {db_count} verified samples from Database")
finally:
    db.close()

if not texts:
    print("Error: No training data found (JSON or DB).")
    exit(1)

print(f"Total training pool: {len(texts)} samples")

# =====================================================
# 3. GROUP RARE CLASSES & ENCODE LABELS
# =====================================================
print("Grouping rare classes (Threshold: < 100 bugs)...")
from collections import Counter
counts = Counter(assignees)

# Threshold: Developers with < 100 bugs are grouped into "Other"
threshold = 100
new_assignees = [
    name if counts[name] >= threshold else "Other" 
    for name in assignees
]

print(f"Original unique classes: {len(set(assignees))}")
print(f"New unique classes (after grouping): {len(set(new_assignees))}")

print("Encoding assignee labels...")
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(new_assignees)

print(f"Found {len(label_encoder.classes_)} unique assignees (including 'Other')")

# =====================================================
# 4. TF-IDF FEATURE EXTRACTION
# =====================================================
print("Vectorizing text (this may take a moment)...")

vectorizer = TfidfVectorizer(
    max_features=60000,
    stop_words='english',
    ngram_range=(1, 3),      
    min_df=2,
    max_df=0.9,
    sublinear_tf=True,
    strip_accents='unicode'
)

X = vectorizer.fit_transform(texts)

print(f"Feature Matrix shape: {X.shape} (Rows, Features)")

# =====================================================
# 5. SAVE ARTIFACTS
# =====================================================
print("Saving artifacts to disk...")

np.savez_compressed(
    TFIDF_MATRIX_FILE,
    data=X.data,
    indices=X.indices,
    indptr=X.indptr,
    shape=X.shape
)

np.save(LABELS_FILE, y)

joblib.dump(vectorizer, TFIDF_VECTORIZER_FILE)
joblib.dump(label_encoder, LABEL_ENCODER_FILE)

print("DONE! All files saved to:", FEATURE_DIR)
