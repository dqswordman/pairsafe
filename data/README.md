# PAIRSAFE Data Archive

This archive is a derived, sanitized PAIRSAFE artifact for anonymous review. It contains pair indices, numeric scores, aggregate tables, score manifests, and generation labels needed to reproduce the paper's main metrics with the companion software archive.

## What is included

- `pairs/xstest_pairs_sanitized.jsonl`: 150 derived PAIRSAFE pair records with official XSTest IDs, stable hashes, normalized type, match flags, lengths, and hashed focus/note metadata.
- `scores/*.jsonl`: numeric refusal-boundary scores for the paired examples. Rows contain IDs, hashes, labels, metadata, and numeric scores only.
- `generation/qwen_generation_labels_sanitized.jsonl`: conservative refusal-rule labels and response hashes for the deterministic generation cross-check.
- `tables/*.csv`: clean aggregate tables used by the paper.
- `manifests/*.json`: score, pair, and generation manifests.

## Text policy

Raw XSTest prompt text is not redistributed. Generated response text is not redistributed. The official XSTest prompt table remains the source of prompt text. Focus and note metadata are hashed or omitted where needed because they may contain task-relevant lexical material. Candidate strings, where described in manifests, are fixed scoring candidates rather than model-generated outputs.

## Reproducing metrics

Unzip the software archive next to this directory and run:

```bash
python pairsafe-software/scripts/reproduce_metrics.py --data pairsafe-data --out recomputed_metrics.json
```

The script recomputes PSA with ties as one half, Oracle-PCDA, 5-fold Calibrated-PCDA with seed 13, mixed BBA, metadata proxy summaries from the supplied tables, exact-focus count, and Qwen generation PCGA.
