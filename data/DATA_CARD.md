# PAIRSAFE Data Card

## Scope

This is a derived XSTest-based paired evaluation artifact for refusal-boundary analysis. It is not a new prompt-label dataset and does not redistribute the original prompt text.

## Composition

The archive contains 150 matched safe/unsafe pair records, sanitized model score rows, sanitized generation labels, and aggregate result tables. Pair records include normalized semantic type, stable prompt hashes, match flags, and lengths. Score rows include numeric log-likelihood-derived scores and labels.

## Recommended use

Use this archive with the companion software archive to reproduce PAIRSAFE pairwise metrics and table checks. The archive is intended for review and diagnostic analysis, not safety certification.

## Restrictions

Raw prompt text and generated response text are intentionally absent. Users who need prompt text should obtain it from the official XSTest source and apply the pair IDs/hashes in this archive.
