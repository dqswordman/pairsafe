from __future__ import annotations

import random
from typing import Any

from .metrics import best_pcda, mixed_bba_at, pcda_at


def calibrated_pcda(rows: list[dict[str, Any]], k: int = 5, seed: int = 13) -> dict[str, Any]:
    items = list(rows)
    rng = random.Random(seed)
    rng.shuffle(items)
    folds = [items[i::k] for i in range(k)]
    fold_rows: list[dict[str, Any]] = []
    total_correct = 0
    total_pairs = 0
    for idx, heldout in enumerate(folds):
        train = [row for j, fold in enumerate(folds) if j != idx for row in fold]
        threshold = best_pcda(train)["threshold"]
        heldout_pcda = pcda_at(heldout, threshold)
        heldout_mixed = mixed_bba_at(heldout, threshold)
        fold_rows.append(
            {
                "fold": idx + 1,
                "n_train": len(train),
                "n_heldout": len(heldout),
                "threshold": threshold,
                "heldout_pcda": heldout_pcda,
                **heldout_mixed,
            }
        )
        total_correct += sum(1 for row in heldout if row["unsafe_score"] > threshold and row["safe_score"] <= threshold)
        total_pairs += len(heldout)
    return {
        "calibrated_pcda": total_correct / total_pairs if total_pairs else float("nan"),
        "folds": fold_rows,
        "seed": seed,
        "k": k,
    }
