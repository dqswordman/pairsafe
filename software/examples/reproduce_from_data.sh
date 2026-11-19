#!/usr/bin/env bash
set -euo pipefail
python pairsafe-software/scripts/reproduce_metrics.py --data pairsafe-data --out recomputed_metrics.json
