#!/usr/bin/env python3

import argparse
import os
import re
from collections import Counter, defaultdict

import bibtexparser
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def read_bib_abstracts(bib_path):
    with open(bib_path, encoding="utf-8", errors="ignore") as fh:
        bib = bibtexparser.load(fh)

    docs = []
    for entry in bib.entries:
        text_parts = []
        # abstracts often in 'abstract'
        if "abstract" in entry and entry["abstract"].strip():
            text_parts.append(entry["abstract"].strip())
        else:
            # fallback to title and keywords
            if "title" in entry and entry["title"].strip():
                text_parts.append(entry["title"].strip())
            if "keywords" in entry and entry["keywords"].strip():
                text_parts.append(entry["keywords"].strip())

        if text_parts:
            docs.append(". ".join(text_parts))

    return docs


def normalize_text(s):
    s = s.lower()
    # remove LaTeX braces and special chars
    s = re.sub(r"[{}]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def count_seed_occurrences(docs, seeds):
    # seeds may be multi-word; count occurrences across all docs
    seed_counts = Counter()
    doc_has_seed = [False] * len(docs)

    for i, doc in enumerate(docs):
        text = normalize_text(doc)
        for seed in seeds:
            pattern = re.escape(seed.lower())
            matches = re.findall(pattern, text)
            if matches:
                seed_counts[seed] += len(matches)
                doc_has_seed[i] = True

    return seed_counts, doc_has_seed


def discover_candidates(docs, seeds, max_new=15):
    # vectorize with TF-IDF over unigrams and bigrams
    # use scikit-learn's english stop words to avoid external NLTK downloads
    sw = ENGLISH_STOP_WORDS

    # Prepare cleaned docs
    cleaned = [normalize_text(d) for d in docs]

    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words=list(sw), token_pattern=r"(?u)\b\w\w+\b")
    X = vectorizer.fit_transform(cleaned)

    terms = vectorizer.get_feature_names_out()
    # compute average tf-idf score across documents
    avg_tfidf = X.mean(axis=0).A1

    term_scores = list(zip(terms, avg_tfidf))
    # exclude terms that are seeds or contain purely numeric
    seed_set = set(s.lower() for s in seeds)
    filtered = [(t, s) for t, s in term_scores if t not in seed_set and not t.isdigit()]
    filtered.sort(key=lambda x: x[1], reverse=True)

    candidates = [t for t, _ in filtered[: max_new * 3]]  # pick some extra then filter by freq
    # deduplicate and keep top max_new
    seen = set()
    final = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        final.append(c)
        if len(final) >= max_new:
            break

    return final


def compute_candidate_stats(docs, candidates, doc_has_seed):
    # For each candidate compute total occurrences and occurrences within seed-containing docs
    cand_counts = Counter()
    cand_counts_in_seed_docs = Counter()

    for i, doc in enumerate(docs):
        text = normalize_text(doc)
        for cand in candidates:
            pattern = re.escape(cand)
            matches = re.findall(pattern, text)
            if matches:
                cand_counts[cand] += len(matches)
                if doc_has_seed[i]:
                    cand_counts_in_seed_docs[cand] += len(matches)

    rows = []
    for cand in candidates:
        total = cand_counts[cand]
        in_seed = cand_counts_in_seed_docs[cand]
        precision = (in_seed / total) if total > 0 else 0.0
        rows.append({"candidate": cand, "freq_total": total, "freq_in_seed_docs": in_seed, "precision": precision})

    return rows


def save_csv_seed_counts(seed_counts, out_path):
    df = pd.DataFrame([{"seed": k, "count": v} for k, v in seed_counts.items()])
    df = df.sort_values("count", ascending=False)
    df.to_csv(out_path, index=False)


def save_csv_candidates(rows, out_path):
    df = pd.DataFrame(rows)
    df = df.sort_values(["freq_total", "precision"], ascending=[False, False])
    df.to_csv(out_path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bib", required=True, help="Path to .bib file")
    parser.add_argument("--seeds", required=False, help="Path to seeds file (one seed per line). If omitted, defaults are used.")
    parser.add_argument("--out", required=False, default="src/r3 - frecuencia/files", help="Output directory")
    parser.add_argument("--max-new", required=False, type=int, default=15, help="Max new candidate words to discover")

    args = parser.parse_args()

    bib_path = args.bib
    seeds_path = args.seeds
    out_dir = args.out
    max_new = args.max_new

    os.makedirs(out_dir, exist_ok=True)

    print("Reading .bib and extracting documents...")
    docs = read_bib_abstracts(bib_path)
    print(f"Found {len(docs)} documents with abstracts/title/keywords.")

    if seeds_path and os.path.exists(seeds_path):
        with open(seeds_path, encoding="utf-8") as fh:
            seeds = [line.strip() for line in fh if line.strip()]
    else:
        # reasonable default seeds for 'Concepts of Generative AI in Education'
        seeds = [
            "generative", "generative ai", "generative artificial intelligence",
            "chatgpt", "large language model", "llm", "gpt",
            "prompt engineering", "ai-assisted", "ai", "education", "teaching", "learning"
        ]
        print("No seeds file provided: using built-in default seed words (editable via --seeds file).")

    print("Counting seed word frequencies...")
    seed_counts, doc_has_seed = count_seed_occurrences(docs, seeds)
    save_csv_seed_counts(seed_counts, os.path.join(out_dir, "seeds_frequency.csv"))

    print("Discovering candidate words via TF-IDF...")
    candidates = discover_candidates(docs, seeds, max_new=max_new)
    print(f"Discovered {len(candidates)} candidates: {candidates}")

    print("Computing candidate stats and precision estimates...")
    rows = compute_candidate_stats(docs, candidates, doc_has_seed)
    save_csv_candidates(rows, os.path.join(out_dir, "candidates_frequency.csv"))

    print("Done. Outputs:")
    print(" - seed frequencies: ", os.path.join(out_dir, "seeds_frequency.csv"))
    print(" - candidate frequencies: ", os.path.join(out_dir, "candidates_frequency.csv"))


if __name__ == "__main__":
    main()
