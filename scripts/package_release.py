"""Build the byte-reproducible offline ZIP from the frozen PAIRSAFE Git tag."""
import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0.0"
NAME = f"pairsafe-{VERSION}"
ROOTS = ("README.md", "LICENSE", "CITATION.cff", "DATA_PROVENANCE.md", "data", "software",
         "scripts", "reference", "docs", "space", ".github/workflows/publish-hugging-face.yml")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def snapshot(revision):
    raw = git("archive", "--format=zip", revision, "--", *ROOTS)
    with ZipFile(io.BytesIO(raw)) as bundle:
        return {info.filename: bundle.read(info) for info in bundle.infolist() if not info.is_dir()}


def write_entries(target, files):
    for name, data in sorted(files.items()):
        entry = ZipInfo(f"{NAME}/{name}", (2026, 11, 19, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        target.writestr(entry, data, compress_type=ZIP_STORED)


def build(destination):
    revision = git("rev-parse", f"refs/tags/{VERSION}^{{commit}}").decode().strip()
    files = snapshot(revision)
    hashes = {path: hashlib.sha256(data).hexdigest() for path, data in sorted(files.items())}
    manifest = {"version": VERSION, "git_commit": revision, "sha256": hashes}
    files["RELEASE.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    destination.mkdir(parents=True, exist_ok=True)
    final = destination / f"{NAME}.zip"
    with io.BytesIO() as output:
        with ZipFile(output, "w") as archive:
            write_entries(archive, files)
        payload = output.getvalue()
    if len(payload) > 100_000_000:
        raise ValueError("The release exceeds the 100,000,000-byte limit.")
    with ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() or any(archive.read(f"{NAME}/{k}") != v for k,v in files.items()):
            raise ValueError("The packaged files differ from the frozen release.")
    final.write_bytes(payload)
    return {"version": VERSION, "git_commit": revision, "name": final.name, "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    print(json.dumps(build(parser.parse_args().destination), indent=2))
