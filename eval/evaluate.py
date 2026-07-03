"""Retrieval quality evaluation script.

Usage:
    1. Place test documents in a directory
    2. Update eval/queries.json with correct expected_doc and expected_page
    3. Run: python -m eval.evaluate <docs_directory>
"""

import json
import os
import sys

from src.config import get_qdrant_client, QDRANT_COLLECTION_NAME
from src.ingest import ingest_document
from src.retrieve import retrieve


def load_queries(path="eval/queries.json"):
    with open(path) as f:
        data = json.load(f)
    return data["queries"], data.get("target_recall_at_5", 0.80)


def ingest_test_corpus(docs_dir: str) -> dict[str, str]:
    ingested = {}
    for fname in sorted(os.listdir(docs_dir)):
        fpath = os.path.join(docs_dir, fname)
        if os.path.isfile(fpath):
            try:
                n = ingest_document(fpath)
                ingested[fname] = f"{n} pages"
                print(f"  Ingested {fname}: {n} pages")
            except ValueError as e:
                print(f"  Skipped {fname}: {e}")
    return ingested


def evaluate(queries: list[dict], top_k: int = 5) -> dict:
    hits = 0
    reciprocal_ranks = []

    print(f"\nEvaluating {len(queries)} queries (top_k={top_k})...\n")
    print(f"{'Query':<50} {'Expected':<25} {'Hit@{}'.format(top_k):<8} {'Rank':<6}")
    print("-" * 95)

    for q in queries:
        results = retrieve(q["query"], top_k=top_k)

        hit = False
        rank = None
        for i, r in enumerate(results):
            if (
                r["filename"] == q["expected_doc"]
                and r["page_number"] == q["expected_page"]
            ):
                hit = True
                rank = i + 1
                break

        hits += int(hit)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

        query_short = q["query"][:48]
        expected = f"{q['expected_doc']} p.{q['expected_page']}"
        rank_str = str(rank) if rank else "miss"
        print(f"{query_short:<50} {expected:<25} {'Y' if hit else 'N':<8} {rank_str:<6}")

    recall = hits / len(queries) if queries else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    return {"recall_at_k": recall, "mrr": mrr, "hits": hits, "total": len(queries)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m eval.evaluate <docs_directory>")
        print("  docs_directory: path to folder containing test PDFs/images")
        sys.exit(1)

    docs_dir = sys.argv[1]
    if not os.path.isdir(docs_dir):
        print(f"Error: {docs_dir} is not a directory")
        sys.exit(1)

    queries, target = load_queries()

    print(f"Ingesting test corpus from {docs_dir}...")
    ingest_test_corpus(docs_dir)

    info = get_qdrant_client().get_collection(QDRANT_COLLECTION_NAME)
    print(f"\nQdrant collection: {info.points_count} points\n")

    metrics = evaluate(queries)

    print(f"\n{'='*50}")
    print(f"Recall@5:  {metrics['recall_at_k']:.2%} (target: {target:.0%})")
    print(f"MRR:       {metrics['mrr']:.3f}")
    print(f"Hits:      {metrics['hits']}/{metrics['total']}")
    print(f"{'='*50}")

    if metrics["recall_at_k"] >= target:
        print("PASS — Recall target met")
    else:
        print("FAIL — Recall below target")


if __name__ == "__main__":
    main()
