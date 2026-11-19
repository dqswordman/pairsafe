"""Build the static Space, mirror the frozen offline ZIP and verify its public contents."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from package_release import ROOT, build, git, snapshot
from verify import DATA, SCORE_FILES, pair_rows, read_jsonl

SPACE = "DQSWORDMAN/pairsafe"
GITHUB = "https://github.com/dqswordman/pairsafe"


def threshold_data():
    index = [p["pair_id"] for p in read_jsonl(DATA / "pairs/xstest_pairs_sanitized.jsonl")]
    replay = json.loads((ROOT / "reference/replay.json").read_text(encoding="utf-8"))
    models = {}
    for model, filename in SCORE_FILES.items():
        pairs = pair_rows(read_jsonl(DATA / "scores" / filename), "contrastive_margin", index)
        oracle = replay["models"][model]["contrastive_margin"]["oracle_threshold"]
        values = {p[s] for p in pairs for s in ("safe_score", "unsafe_score")}
        ticks = sorted(values | {min(values) - 0.001, max(values) + 0.001, oracle})
        counts = []
        for t in ticks:
            correct = sum(r["safe_score"] <= t < r["unsafe_score"] for r in pairs)
            safe = sum(r["safe_score"] <= t for r in pairs)
            unsafe = sum(t < r["unsafe_score"] for r in pairs)
            counts.append([t, correct, safe, unsafe])
        models[model] = {"oracle_index": ticks.index(oracle), "rows": counts}
    return models


def prepare(destination):
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("Supply an empty Space build directory.")
    head = git("rev-parse", "HEAD").decode().strip()
    for name, data in snapshot(head).items():
        if name == "README.md":
            name = "GITHUB_README.md"
        elif name.startswith("space/"):
            name = name[len("space/"):]
        elif name.startswith(".github/"):
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    with tempfile.TemporaryDirectory() as tmp:
        receipt = Path(tmp) / "replay.json"
        subprocess.run([sys.executable, "-B", str(destination / "scripts/verify.py"), "--out", str(receipt)], check=True)
        if receipt.read_bytes() != (destination / "reference/replay.json").read_bytes():
            raise ValueError("Frozen CPU receipt differs from the newly computed ledger.")
    (destination / "thresholds.json").write_bytes(json.dumps(threshold_data(), separators=(",", ":")).encode())
    release = build(destination)
    digests = {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(destination.rglob("*")) if p.is_file()}
    record = {"github": GITHUB, "github_commit": head, "frozen_release": release, "sha256": digests}
    (destination / "SNAPSHOT.json").write_bytes((json.dumps(record, indent=2) + "\n").encode())
    print(f"Prepared {len(digests) + 1} files for GitHub {head[:12]}. ZIP {release['bytes']} bytes.")
    return head, release


def publish(destination, head, release):
    from huggingface_hub import HfApi
    if git("ls-remote", "--heads", GITHUB + ".git", "refs/heads/main").decode().split()[0] != head:
        print("GitHub main advanced. Skipping the older snapshot.")
        return
    api = HfApi()
    previous = api.space_info(SPACE)
    if previous.private or previous.sdk != "static":
        raise ValueError("Expected the public PAIRSAFE static Space.")
    commit = api.upload_folder(repo_id=SPACE, repo_type="space", folder_path=destination,
                               parent_commit=previous.sha, delete_patterns=["*", "**/*"],
                               ignore_patterns=[".gitattributes"], commit_message=f"Mirror GitHub {head[:12]}")
    actual = set(api.list_repo_files(SPACE, repo_type="space", revision=commit.oid, token=False))
    expected = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
    if actual - {".gitattributes"} != expected:
        raise ValueError("Public file inventory differs from staged Space.")
    for name in ("SNAPSHOT.json", "index.html", "thresholds.json", release["name"]):
        url = f"https://huggingface.co/spaces/{SPACE}/resolve/{commit.oid}/{name}"
        contents = (destination / name).read_bytes()
        with urlopen(Request(url, headers={"User-Agent":"pairsafe-release-verifier"}), timeout=45) as response:
            if response.read(len(contents) + 1) != contents:
                raise ValueError(f"Public mirror returned different bytes for {name}")
    print(commit.commit_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    directory = args.destination.resolve()
    revision, artifact = prepare(directory)
    if args.publish:
        publish(directory, revision, artifact)
