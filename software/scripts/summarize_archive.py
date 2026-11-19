from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pairsafe.io import read_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()
    root = Path(args.data)
    pairs = read_jsonl(root / "pairs" / "xstest_pairs_sanitized.jsonl")
    print(f"pairs: {len(pairs)}")
    for path in sorted((root / "scores").glob("*.jsonl")):
        print(f"{path.name}: {len(read_jsonl(path))} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
