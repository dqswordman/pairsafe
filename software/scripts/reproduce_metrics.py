from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pairsafe.calibration import calibrated_pcda
from pairsafe.io import read_jsonl, write_json
from pairsafe.metrics import best_mixed_bba, best_pcda, psa
from pairsafe.tables import metadata_proxy_summary


METHODS = {
    "contrastive_margin": "margin",
    "one_sided_refusal_ll": "best_refusal_ll",
    "answer_ll_baseline": "best_answer_ll",
}


SCORE_FILES = {
    "Qwen2.5-3B-Instruct": "qwen2p5_3b_margin_scores_sanitized.jsonl",
    "SmolLM2-1.7B-Instruct": "smollm2_1p7b_margin_scores_sanitized.jsonl",
}


def pair_rows(score_rows: list[dict], method: str, pair_order: list[str]) -> list[dict]:
    by_pair: dict[str, dict[str, float]] = {}
    key = METHODS[method]
    for row in score_rows:
        item = by_pair.setdefault(row["pair_id"], {"pair_id": row["pair_id"], "type_norm": row["type_norm"]})
        item[f"{row['member']}_score"] = float(row[key])
    return [by_pair[pair_id] for pair_id in pair_order if pair_id in by_pair and "safe_score" in by_pair[pair_id] and "unsafe_score" in by_pair[pair_id]]


def generation_pcga(data_root: Path) -> dict[str, float]:
    rows = read_jsonl(data_root / "generation" / "qwen_generation_labels_sanitized.jsonl")
    by_pair: dict[str, dict[str, bool]] = {}
    for row in rows:
        item = by_pair.setdefault(row["pair_id"], {})
        item[row["member"]] = bool(row["refused_by_rule"])
    complete = [row for row in by_pair.values() if "safe" in row and "unsafe" in row]
    return {
        "n_pairs": len(complete),
        "pcga": sum(1 for row in complete if row["unsafe"] and not row["safe"]) / len(complete),
        "unsafe_refusal": sum(1 for row in complete if row["unsafe"]) / len(complete),
        "safe_false_refusal": sum(1 for row in complete if row["safe"]) / len(complete),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True, help="Output JSON path; if an existing directory is supplied, writes recomputed_metrics.json inside it.")
    args = parser.parse_args()
    data_root = Path(args.data)
    pair_rows_data = read_jsonl(data_root / "pairs" / "xstest_pairs_sanitized.jsonl")
    pair_order = [row["pair_id"] for row in pair_rows_data]
    results = {"models": {}, "metadata_proxy_summary": metadata_proxy_summary(data_root)}
    for model, file_name in SCORE_FILES.items():
        score_rows = read_jsonl(data_root / "scores" / file_name)
        results["models"][model] = {}
        for method in METHODS:
            rows = pair_rows(score_rows, method, pair_order)
            oracle = best_pcda(rows)
            mixed = best_mixed_bba(rows)
            cal = calibrated_pcda(rows, k=5, seed=13)
            results["models"][model][method] = {
                "n_pairs": len(rows),
                "psa": psa(rows),
                "oracle_pcda": oracle["pcda"],
                "oracle_threshold": oracle["threshold"],
                "calibrated_pcda": cal["calibrated_pcda"],
                "ordinary_mixed_bba": mixed["mixed_bba"],
                "ordinary_mixed_threshold": mixed["threshold"],
            }
    results["pair_index"] = {
        "n_pairs": len(pair_rows_data),
        "exact_focus_subset_n": sum(1 for row in pair_rows_data if row.get("focus_match") is True),
    }
    results["generation"] = {"Qwen2.5-3B-Instruct": generation_pcga(data_root)}
    out_path = Path(args.out)
    if out_path.exists() and out_path.is_dir():
        out_path = out_path / "recomputed_metrics.json"
    write_json(out_path, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
