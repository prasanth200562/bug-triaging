import json
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data/processed/bug_reports_nlp_ready.json"
OUT_BASE = BASE_DIR / "experiments/hyperparam_search"
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


def build_vectorizer(config_name):
    if config_name == "word_1_2_big":
        return TfidfVectorizer(max_features=60000, stop_words="english", ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, strip_accents="unicode")
    elif config_name == "wordchar_medium":
        # word + char concatenation
        w = TfidfVectorizer(max_features=40000, stop_words="english", ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, strip_accents="unicode")
        c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), max_features=20000, sublinear_tf=True)
        return (w, c)
    else:
        raise ValueError("Unknown config")


def fit_vectorizer_and_transform(vec_cfg, train_texts, test_texts):
    if isinstance(vec_cfg, tuple):
        w, c = vec_cfg
        Xw_tr = w.fit_transform(train_texts); Xw_te = w.transform(test_texts)
        Xc_tr = c.fit_transform(train_texts); Xc_te = c.transform(test_texts)
        Xtr = hstack([Xw_tr, Xc_tr]); Xte = hstack([Xw_te, Xc_te])
        return Xtr, Xte
    else:
        v = vec_cfg
        Xtr = v.fit_transform(train_texts); Xte = v.transform(test_texts)
        return Xtr, Xte


def run_search(estimator, param_dist, Xtr, ytr, n_iter=20):
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    rs = RandomizedSearchCV(estimator, param_distributions=param_dist, n_iter=n_iter, scoring="f1_macro", cv=cv, n_jobs=-1, random_state=42, verbose=1)
    rs.fit(Xtr, ytr)
    return rs


def evaluate_best(rs, Xte, yte):
    best = rs.best_estimator_
    preds = best.predict(Xte)
    return float(round(accuracy_score(yte, preds), 4)), float(round(f1_score(yte, preds, average="macro"), 4))


def main():
    texts, assignees = load_data()
    print(f"Loaded {len(texts)} samples")
    y, le = group_and_encode(assignees, threshold=100)

    Xs = np.array(texts); ys = y
    X_train_texts, X_test_texts, y_train, y_test = train_test_split(Xs, ys, test_size=0.2, stratify=ys, random_state=42)

    configs = ["word_1_2_big", "wordchar_medium"]
    results = {"timestamp": time.strftime("%Y%m%d_%H%M%S"), "runs": []}
    out_dir = OUT_BASE / results["timestamp"]
    out_dir.mkdir(parents=True, exist_ok=True)

    Cs = list(np.logspace(-4, 2, 30))

    for cfg in configs:
        print(f"Processing config: {cfg}")
        vec_cfg = build_vectorizer(cfg)
        Xtr, Xte = fit_vectorizer_and_transform(vec_cfg, X_train_texts, X_test_texts)

        # LinearSVC search
        svc = LinearSVC(max_iter=5000, random_state=42)
        svc_params = {"C": Cs}
        print("Searching LinearSVC...")
        rs_svc = run_search(svc, svc_params, Xtr, y_train, n_iter=20)
        svc_acc, svc_f1 = evaluate_best(rs_svc, Xte, y_test)

        # LogisticRegression search
        lr = LogisticRegression(max_iter=2000, solver="saga", random_state=42)
        lr_params = {"C": Cs, "penalty": ["l1", "l2"]}
        print("Searching LogisticRegression...")
        rs_lr = run_search(lr, lr_params, Xtr, y_train, n_iter=20)
        lr_acc, lr_f1 = evaluate_best(rs_lr, Xte, y_test)

        run_res = {
            "config": cfg,
            "linear_svc": {"best_params": rs_svc.best_params_, "accuracy": svc_acc, "macro_f1": svc_f1},
            "logistic_regression": {"best_params": rs_lr.best_params_, "accuracy": lr_acc, "macro_f1": lr_f1},
        }
        results["runs"].append(run_res)

        # save intermediate
        with open(out_dir / f"results_{cfg}.json", "w", encoding="utf-8") as f:
            json.dump(run_res, f, indent=2)

    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved hyperparam search results to {out_dir}")


if __name__ == "__main__":
    main()
