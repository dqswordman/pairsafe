"""Verify the submission files and replay PAIRSAFE from archived per-example records."""
import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "software" / "scripts"))
from reproduce_metrics import METHODS, SCORE_FILES, pair_rows
from pairsafe.calibration import calibrated_pcda
from pairsafe.io import read_csv, read_jsonl
from pairsafe.metrics import best_mixed_bba, best_pcda, psa


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_values(actual, expected, keys, context):
    for key in keys:
        require(math.isclose(actual[key], float(expected[key]), rel_tol=0, abs_tol=1e-10),
                f"{context} / {key}: computed {actual[key]}, expected {expected[key]}")


def verify_inputs():
    counts = {}
    for folder in (DATA, ROOT / "software"):
        entries = (folder / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
        for entry in entries:
            digest, name = entry.split(maxsplit=1)
            require(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest,
                    f"Checksum mismatch: {folder.name}/{name}")
        counts[folder.name] = len(entries)
    return counts


def members(path, pairs):
    rows = read_jsonl(path)
    seen = set()
    for row in rows:
        key = row["pair_id"], row["member"]
        pair = pairs[key[0]]
        side = key[1]
        require(side in ("safe", "unsafe") and key not in seen, f"Invalid member: {key}")
        require(row["type_norm"] == pair["type_norm"] and
                row["prompt_hash"] == pair[f"{side}_prompt_hash"] and
                str(row["xstest_id"]) == str(pair[f"{side}_id"]), f"Alignment mismatch: {key}")
        seen.add(key)
    require(len(seen) == 2 * len(pairs), f"Missing members in {path.name}")
    return rows


def evaluate(rows):
    oracle = best_pcda(rows)
    mixed = best_mixed_bba(rows)
    held = calibrated_pcda(rows, k=5, seed=13)
    return {"n_pairs": len(rows), "ordinary_mixed_bba": mixed["mixed_bba"], "psa": psa(rows),
            "oracle_pcda": oracle["pcda"], "calibrated_pcda": held["calibrated_pcda"],
            "oracle_threshold": oracle["threshold"], "ordinary_mixed_threshold": mixed["threshold"],
            "positive_gaps": sum(r["unsafe_score"] > r["safe_score"] for r in rows),
            "ties": sum(r["unsafe_score"] == r["safe_score"] for r in rows),
            "heldout_correct": sum(round(f["heldout_pcda"] * f["n_heldout"]) for f in held["folds"]),
            "folds": held["folds"]}


def table(name):
    return read_csv(DATA / "tables" / f"pairsafe_{name}.csv")


def logmeanexp(values):
    maximum = max(values)
    return maximum + math.log(mean(math.exp(value - maximum) for value in values))


def replay():
    checksums = verify_inputs()
    index = read_jsonl(DATA / "pairs" / "xstest_pairs_sanitized.jsonl")
    pairs = {p["pair_id"]: p for p in index}
    categories = Counter(p["type_norm"] for p in index)
    prompt_ids = {str(p[f"{s}_id"]) for p in index for s in ("safe", "unsafe")}
    require(len(pairs) == len(index) == 150 and len(prompt_ids) == 300, "Pair population differs")
    require(len(categories) == 6 and set(categories.values()) == {25}, "Category counts differ")
    for field in ("focus", "note"):
        require(all(p[field + "_match"] == (p["safe_" + field + "_hash"] == p["unsafe_" + field + "_hash"]) for p in index),
                f"{field} flags disagree with the stored hashes")
    focus = {p["pair_id"] for p in index if p["focus_match"]}
    ref = {(r["model"], r["method"]): r for r in table("calibrated_pcda")}
    core = ("ordinary_mixed_bba", "psa", "oracle_pcda", "calibrated_pcda")
    models = {}
    for model, filename in SCORE_FILES.items():
        scores = members(DATA / "scores" / filename, pairs)
        for row in scores:
            require(math.isclose(row["margin"], row["best_refusal_ll"] - row["best_answer_ll"], abs_tol=1e-10),
                    f"Primary margin differs in {model}")
        results = {}
        for method in METHODS:
            rows = pair_rows(scores, method, list(pairs))
            results[method] = evaluate(rows)
            check_values(results[method], ref[model, method],
                         (*core, "ordinary_mixed_threshold", "oracle_threshold"), f"{model}/{method}")
        primary = pair_rows(scores, "contrastive_margin", list(pairs))
        if model == "Qwen2.5-3B-Instruct":
            shuffled = list(primary)
            random.Random(13).shuffle(shuffled)
            example = next(r for r in shuffled[0::5] if r["pair_id"] == "pairsafe_xstest_093")
            threshold = results["contrastive_margin"]["folds"][0]["threshold"]
            require(threshold < example["safe_score"] < example["unsafe_score"], "Worked example differs")
            results["worked_example"] = dict(example, heldout_fold=1, threshold=threshold)
        results["exact_focus"] = evaluate([r for r in primary if r["pair_id"] in focus])
        target = next(r for r in table("exact_focus_subset") if r["section"] == "model_score" and r["model"] == model)
        check_values(results["exact_focus"], dict(target, ordinary_mixed_bba=target["mixed_bba"]), core, model + "/focus")
        by_type = {}
        for r in table("type_breakdown"):
            if r["method"] == "contrastive_margin" and r["model"] == model:
                subset = [v for v in primary if v["type_norm"] == r["type_norm"]]
                by_type[r["type_norm"]] = {"n_pairs": len(subset), "psa": psa(subset), "oracle_pcda": best_pcda(subset)["pcda"]}
                check_values(by_type[r["type_norm"]], r, ("n_pairs", "psa", "oracle_pcda"), model + "/" + r["type_norm"])
        results["by_type"] = by_type
        models[model] = results
    qwen_cache = members(DATA / "scores" / "qwen_candidate_ablation_scores_sanitized.jsonl", pairs)
    candidates = {}
    for name, aggregate in (("single_candidate_margin", lambda v: v[0]), ("multi_max_margin", max),
                            ("multi_mean_margin", mean), ("multi_logsumexp_margin", logmeanexp)):
        for row in qwen_cache:
            row["margin"] = aggregate(row["refusal_lls"]) - aggregate(row["answer_lls"])
        candidates[name] = evaluate(pair_rows(qwen_cache, "contrastive_margin", list(pairs)))
        target = next(r for r in table("candidate_ablation") if r["method"] == name)
        check_values(candidates[name], target, core, name)
    labels = members(DATA / "generation" / "qwen_generation_labels_sanitized.jsonl", pairs)
    decisions = {key: {} for key in pairs}
    for row in labels:
        require(type(row["refused_by_rule"]) is bool, "Expected a Boolean refusal label")
        decisions[row["pair_id"]][row["member"]] = row["refused_by_rule"]
    outcomes = Counter((d["safe"], d["unsafe"]) for d in decisions.values())
    n = len(pairs)
    generation = {"n_pairs": n, "both_correct": outcomes[False, True], "both_refused": outcomes[True, True],
                  "both_answered": outcomes[False, False], "both_reversed": outcomes[True, False],
                  "pcga": outcomes[False, True] / n,
                  "unsafe_refusal_rate": sum(d["unsafe"] for d in decisions.values()) / n,
                  "safe_false_refusal_rate": sum(d["safe"] for d in decisions.values()) / n}
    check_values(generation, {r["metric"]: r["value"] for r in table("generation_refusal")},
                 ("n_pairs", "pcga", "unsafe_refusal_rate", "safe_false_refusal_rate"), "generation")
    return {"version": "v1.0.0", "input_checksums_verified": checksums, "pairs": n,
            "categories": dict(categories), "focus_matches": len(focus),
            "note_matches": sum(p["note_match"] for p in index), "models": models,
            "qwen_candidate_cache": candidates, "qwen_generation": generation}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write the full metrics and per-fold ledger as JSON.")
    args = parser.parse_args()
    result = replay()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes((json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    for model, results in result["models"].items():
        m = results["contrastive_margin"]
        print(f"{model}: PSA {m['psa']:.3f}, oracle {m['oracle_pcda']:.3f}, held-out {m['calibrated_pcda']:.3f} ({m['heldout_correct']}/150)")
    print(f"Qwen generation: {result['qwen_generation']['both_correct']}/150 pairs. All replay checks passed.")


if __name__ == "__main__":
    main()
