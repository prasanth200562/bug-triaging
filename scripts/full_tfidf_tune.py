import json
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data/processed/bug_reports_nlp_ready.json"
OUT_BASE = BASE_DIR / "experiments/tfidf_tuning"
OUT_BASE.mkdir(parents=True, exist_ok=True)


def load_data():
    import json

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


def build_word_vectorizer(max_features, ngram_range=(1, 2)):
    return TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=ngram_range,
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        strip_accents="unicode",
    )


def build_char_vectorizer(max_features, ngram_range=(3, 6)):
    return TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=ngram_range,
        max_features=max_features,
        sublinear_tf=True,
    )


def evaluate_config(name, X_train_texts, X_test_texts, y_train, y_test, config):
    if config.get("type") == "baseline":
        vec = TfidfVectorizer(
            max_features=config["max_features"],
            stop_words="english",
            ngram_range=config["ngram_range"],
            min_df=2,
            max_df=0.9,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        Xtr = vec.fit_transform(X_train_texts)
        Xte = vec.transform(X_test_texts)
    else:
        parts_tr = []
        parts_te = []
        # Word vectorizer
        if config.get("word_max", 0) and config.get("word_max") > 0:
            wvec = build_word_vectorizer(config["word_max"], config.get("word_ngram", (1, 2)))
            Xw_tr = wvec.fit_transform(X_train_texts)
            Xw_te = wvec.transform(X_test_texts)
            parts_tr.append(Xw_tr)
            parts_te.append(Xw_te)

        # Char vectorizer (optional)
        if config.get("char_max", 0) and config.get("char_max") > 0:
            cvec = build_char_vectorizer(config["char_max"], config.get("char_ngram", (3, 6)))
            Xc_tr = cvec.fit_transform(X_train_texts)
            Xc_te = cvec.transform(X_test_texts)
            parts_tr.append(Xc_tr)
            parts_te.append(Xc_te)

        if len(parts_tr) == 1:
            Xtr = parts_tr[0]
            Xte = parts_te[0]
        else:
            Xtr = hstack(parts_tr)
            Xte = hstack(parts_te)

    results = {"name": name, "config": config}

    # LinearSVC
    svc = LinearSVC(max_iter=5000, random_state=42)
    svc.fit(Xtr, y_train)
    p_svc = svc.predict(Xte)
    results["linear_svc"] = {
        "accuracy": float(round(accuracy_score(y_test, p_svc), 4)),
        "macro_f1": float(round(f1_score(y_test, p_svc, average="macro"), 4)),
    }

    # LogisticRegression: use 'saga' solver which supports multiclass on sparse data
    lr = LogisticRegression(max_iter=2000, solver="saga", random_state=42)
    lr.fit(Xtr, y_train)
    p_lr = lr.predict(Xte)
    results["logistic_regression"] = {
        "accuracy": float(round(accuracy_score(y_test, p_lr), 4)),
        "macro_f1": float(round(f1_score(y_test, p_lr, average="macro"), 4)),
    }

    return results


def main():
    texts, assignees = load_data()
    print(f"Loaded {len(texts)} valid samples")
    y, le = group_and_encode(assignees, threshold=100)

    Xs = np.array(texts)
    ys = y

    X_train_texts, X_test_texts, y_train, y_test = train_test_split(
        Xs, ys, test_size=0.2, stratify=ys, random_state=42
    )

    configs = {
        "baseline": {"type": "baseline", "ngram_range": (1, 3), "max_features": 60000},
        "wordchar_medium": {"type": "wordchar", "word_max": 40000, "char_max": 20000},
        "wordchar_small": {"type": "wordchar", "word_max": 20000, "char_max": 5000},
        "word_1_2_big": {"type": "wordchar", "word_max": 60000, "char_max": 0},
    }

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_BASE / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results = {"timestamp": timestamp, "runs": []}

    for name, cfg in configs.items():
        print(f"Evaluating config: {name}")
        res = evaluate_config(name, X_train_texts, X_test_texts, y_train, y_test, cfg)
        all_results["runs"].append(res)
        print(json.dumps(res, indent=2))

    out_file = out_dir / "metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"Saved tuning results to {out_file}")


if __name__ == "__main__":
    main()
