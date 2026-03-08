import json
import os
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data/processed/bug_reports_nlp_ready.json"
OUT_DIR = BASE_DIR / "experiments/quick_tfidf_smoke"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    valid = [d for d in data if d.get("combined_text") and d.get("assignee")]
    texts = [d["combined_text"] for d in valid]
    assignees = [d["assignee"] for d in valid]
    return texts, assignees


def group_and_encode(assignees, threshold=100):
    from collections import Counter

    counts = Counter(assignees)
    new = [a if counts[a] >= threshold else "Other" for a in assignees]
    le = LabelEncoder()
    y = le.fit_transform(new)
    return y, le


def vectorize_baseline(train_texts, test_texts):
    vec = TfidfVectorizer(
        max_features=60000,
        stop_words="english",
        ngram_range=(1, 3),
        min_df=2,
        max_df=0.9,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    X_train = vec.fit_transform(train_texts)
    X_test = vec.transform(test_texts)
    return X_train, X_test, vec


def vectorize_variant(train_texts, test_texts):
    # word ngrams (1,2)
    wvec = TfidfVectorizer(
        max_features=40000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    # char ngrams (char_wb) to capture subword patterns
    cvec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 6),
        max_features=10000,
        sublinear_tf=True,
    )

    Xw_train = wvec.fit_transform(train_texts)
    Xw_test = wvec.transform(test_texts)

    Xc_train = cvec.fit_transform(train_texts)
    Xc_test = cvec.transform(test_texts)

    X_train = hstack([Xw_train, Xc_train])
    X_test = hstack([Xw_test, Xc_test])
    return X_train, X_test, (wvec, cvec)


def train_and_eval(X_train, X_test, y_train, y_test):
    clf = LinearSVC(max_iter=5000, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average="macro")
    return acc, f1


def main():
    print("Loading data...")
    texts, assignees = load_data()
    print(f"Total samples: {len(texts)}")

    y, le = group_and_encode(assignees, threshold=100)

    # quick smoke: limit to at most 5000 samples for speed
    N = min(len(texts), 5000)
    print(f"Using N={N} samples for smoke test")

    Xs = np.array(texts[:N])
    ys = y[:N]

    X_train_texts, X_test_texts, y_train, y_test = train_test_split(
        Xs, ys, test_size=0.2, stratify=ys, random_state=42
    )

    print("Vectorizing baseline...")
    Xb_train, Xb_test, _ = vectorize_baseline(X_train_texts, X_test_texts)
    print("Training baseline LinearSVC...")
    base_acc, base_f1 = train_and_eval(Xb_train, Xb_test, y_train, y_test)

    print("Vectorizing variant (word+char)...")
    Xv_train, Xv_test, _ = vectorize_variant(X_train_texts, X_test_texts)
    print("Training variant LinearSVC...")
    var_acc, var_f1 = train_and_eval(Xv_train, Xv_test, y_train, y_test)

    result = {
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "n_samples": int(N),
        "baseline": {"accuracy": float(round(base_acc, 4)), "macro_f1": float(round(base_f1, 4))},
        "variant": {"accuracy": float(round(var_acc, 4)), "macro_f1": float(round(var_f1, 4))},
    }

    out_file = OUT_DIR / f"metrics_{result['timestamp']}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("--- Results ---")
    print("Baseline -> Accuracy: {:.4f}, Macro-F1: {:.4f}".format(base_acc, base_f1))
    print("Variant  -> Accuracy: {:.4f}, Macro-F1: {:.4f}".format(var_acc, var_f1))
    print(f"Saved metrics to: {out_file}")


if __name__ == "__main__":
    main()
