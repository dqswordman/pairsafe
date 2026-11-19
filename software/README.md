# PAIRSAFE Software

This archive contains small, deterministic utilities for reproducing PAIRSAFE metrics from the companion sanitized data archive. It does not include model weights, prompt text, generated responses, paper source, or a PDF.

## Requirements

Python 3.9 or newer. The runtime code uses only the Python standard library. Tests can be run directly with Python.

## Reproduce metrics

Place `pairsafe-software/` and `pairsafe-data/` next to each other, then run:

```bash
python pairsafe-software/scripts/reproduce_metrics.py --data pairsafe-data --out recomputed_metrics.json
```

Windows PowerShell:

```powershell
python .\pairsafe-software\scripts\reproduce_metrics.py --data .\pairsafe-data --out .\recomputed_metrics.json
```

The `--out` argument should normally be a JSON file path; if an existing directory is supplied, the script writes `recomputed_metrics.json` inside it.

The script recomputes:

- PSA with ties counted as one half
- Oracle-PCDA
- 5-fold Calibrated-PCDA with seed 13
- mixed BBA when labels are available
- metadata proxy summaries from the supplied tables
- exact-focus subset count
- Qwen generation PCGA

## Tests

```bash
python pairsafe-software/tests/test_metrics.py
```
