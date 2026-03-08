import json
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, RandomizedSearchCV
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


def build_vectorizers(config):
    if config["type"] == "baseline":
        vec = TfidfVectorizer(max_features=config["max_features"], stop_words="english", ngram_range=config["ngram_range"], min_df=2, max_df=0.9, sublinear_tf=True, strip_accents="unicode")
        return (vec,)
    else:
        parts = []
        if config.get("word_max", 0) > 0:
            wvec = TfidfVectorizer(max_features=config["word_max"], stop_words="english", ngram_range=config.get("word_ngram", (1, 2)), min_df=2, max_df=0.95, sublinear_tf=True, strip_accents="unicode")
            parts.append(wvec)
        if config.get("char_max", 0) > 0:
            cvec = TfidfVectorizer(analyzer="char_wb", ngram_range=config.get("char_ngram", (3, 6)), max_features=config["char_max"], sublinear_tf=True)
            parts.append(cvec)
        return tuple(parts)


def vectorize(parts, train_texts, test_texts):
    mats_tr = []
    mats_te = []
    for p in parts:
        Xtr = p.fit_transform(train_texts)
        Xte = p.transform(test_texts)
        mats_tr.append(Xtr)
        mats_te.append(Xte)
    if len(mats_tr) == 1:
        return mats_tr[0], mats_te[0]
    return hstack(mats_tr), hstack(mats_te)


def run_search(estimator, param_dist, X, y, n_iter=12, cv=3):
    rs = RandomizedSearchCV(estimator, param_distributions=param_dist, n_iter=n_iter, scoring="f1_macro", cv=cv, random_state=42, n_jobs=1, verbose=0)
    rs.fit(X, y)
    return rs


def main():
    texts, assignees = load_data()
    print(f"Loaded {len(texts)} samples")
    y_all, le = group_and_encode(assignees, threshold=100)

    # Use a stratified subset for speed
    N = min(5000, len(texts))
    print(f"Subset size: {N}")
    Xs = np.array(texts[:N])
    ys = y_all[:N]

    X_train_texts, X_test_texts, y_train, y_test = train_test_split(Xs, ys, test_size=0.2, stratify=ys, random_state=42)

    configs = {
        "word_1_2_big": {"type": "wordchar", "word_max": 20000, "char_max": 0, "word_ngram": (1, 2)},
        "wordchar_medium": {"type": "wordchar", "word_max": 20000, "char_max": 5000},
    }

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_BASE / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {"timestamp": timestamp, "runs": []}

    C_values = np.logspace(-4, 2, 12).tolist()

    for name, cfg in configs.items():
        print(f"Running config: {name}")
        parts = build_vectorizers(cfg)
        Xtr, Xte = vectorize(parts, X_train_texts, X_test_texts)

        # LinearSVC search
        svc = LinearSVC(max_iter=2000, random_state=42)
        svc_params = {"C": C_values}
        print(" Searching LinearSVC...")
        rs_svc = run_search(svc, svc_params, Xtr, y_train, n_iter=12, cv=3)
        best_svc = rs_svc.best_estimator_
        svc_preds = best_svc.predict(Xte)
        svc_acc = accuracy_score(y_test, svc_preds)
        svc_f1 = f1_score(y_test, svc_preds, average="macro")

        # LogisticRegression search
        lr = LogisticRegression(max_iter=2000, solver="saga", random_state=42)
        lr_params = {"C": C_values}
        print(" Searching LogisticRegression...")
        rs_lr = run_search(lr, lr_params, Xtr, y_train, n_iter=12, cv=3)
        best_lr = rs_lr.best_estimator_
        lr_preds = best_lr.predict(Xte)
        lr_acc = accuracy_score(y_test, lr_preds)
        lr_f1 = f1_score(y_test, lr_preds, average="macro")

        run = {
            "config": name,
            "linear_svc": {"best_params": rs_svc.best_params_, "cv_best_score": float(round(rs_svc.best_score_, 4)), "test_accuracy": float(round(svc_acc, 4)), "test_macro_f1": float(round(svc_f1, 4))},
            "logistic_regression": {"best_params": rs_lr.best_params_, "cv_best_score": float(round(rs_lr.best_score_, 4)), "test_accuracy": float(round(lr_acc, 4)), "test_macro_f1": float(round(lr_f1, 4))},
        }

        summary["runs"].append(run)
        print(json.dumps(run, indent=2))

    out_file = out_dir / "hyperparam_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved results to {out_file}")


if __name__ == "__main__":
    main()
import json
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import RandomizedSearchCV, train_test_split, StratifiedKFold
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
from scipy.stats import expon


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
    # two configs chosen for speed/quality tradeoff
    if config_name == "word_1_2_big":
        return TfidfVectorizer(max_features=20000, stop_words="english", ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, strip_accents="unicode")
    elif config_name == "wordchar_medium":
        w = TfidfVectorizer(max_features=15000, stop_words="english", ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, strip_accents="unicode")
        c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 6), max_features=5000, sublinear_tf=True)
        return (w, c)
    else:
        raise ValueError("Unknown config")


def run_search(X_train, y_train, estimator, param_distributions, n_iter=12, cv=3):
    rs = RandomizedSearchCV(
        estimator,
        param_distributions=param_distributions,
        n_iter=n_iter,
        scoring="f1_macro",
        n_jobs=-1,
        cv=cv,
        verbose=1,
        random_state=42,
    )
    rs.fit(X_train, y_train)
    return rs


def eval_on_test(rs, X_test, y_test):
    best = rs.best_estimator_
    preds = best.predict(X_test)
    return {"accuracy": float(round(accuracy_score(y_test, preds), 4)), "macro_f1": float(round(f1_score(y_test, preds, average='macro'), 4))}


def main():
    texts, assignees = load_data()
    print(f"Loaded {len(texts)} samples")
    y, le = group_and_encode(assignees, threshold=100)

    Xs = np.array(texts)
    ys = y

    X_train_texts, X_test_texts, y_train, y_test = train_test_split(Xs, ys, test_size=0.2, stratify=ys, random_state=42)

    configs = ["word_1_2_big", "wordchar_medium"]

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_BASE / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {"timestamp": timestamp, "results": []}

    for cfg in configs:
        print(f"Processing vectorizer config: {cfg}")
        vec = build_vectorizer(cfg)
        if isinstance(vec, tuple):
            wvec, cvec = vec
            Xw_tr = wvec.fit_transform(X_train_texts)
            Xw_te = wvec.transform(X_test_texts)
            Xc_tr = cvec.fit_transform(X_train_texts)
            Xc_te = cvec.transform(X_test_texts)
            from scipy.sparse import hstack

            X_train = hstack([Xw_tr, Xc_tr])
            X_test = hstack([Xw_te, Xc_te])
        else:
            X_train = vec.fit_transform(X_train_texts)
            X_test = vec.transform(X_test_texts)

        # LinearSVC search
        print("Running RandomizedSearch for LinearSVC...")
        ls_param = {"C": [0.001, 0.01, 0.1, 1, 10, 100], "loss": ["squared_hinge", "hinge"]}
        rs_ls = run_search(X_train, y_train, LinearSVC(max_iter=5000, random_state=42), ls_param, n_iter=12, cv=3)
        ls_metrics = eval_on_test(rs_ls, X_test, y_test)

        # LogisticRegression search
        print("Running RandomizedSearch for LogisticRegression...")
        lr_param = {"C": [0.001, 0.01, 0.1, 1, 10, 100], "penalty": ["l2"]}
        rs_lr = run_search(X_train, y_train, LogisticRegression(solver='saga', max_iter=2000, random_state=42), lr_param, n_iter=12, cv=3)
        lr_metrics = eval_on_test(rs_lr, X_test, y_test)

        result = {"config": cfg, "linear_svc_best_params": rs_ls.best_params_, "linear_svc_test": ls_metrics, "logistic_best_params": rs_lr.best_params_, "logistic_test": lr_metrics}
        report["results"].append(result)
        with open(out_dir / f"report_{cfg}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Saved hyperparameter search results to {out_dir}")


if __name__ == "__main__":
    main()
