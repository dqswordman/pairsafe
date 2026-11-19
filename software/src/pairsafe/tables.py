from __future__ import annotations

from pathlib import Path

from .io import read_csv


def metadata_proxy_summary(data_root: str | Path) -> dict[str, dict[str, float | str]]:
    path = Path(data_root) / "tables" / "pairsafe_actual_metadata_proxy_audit.csv"
    out: dict[str, dict[str, float | str]] = {}
    for row in read_csv(path):
        out[row["proxy"]] = {
            "status": row["status"],
            "psa": float(row["psa"]),
            "oracle_pcda": float(row["oracle_pcda"]),
            "calibrated_pcda": float(row["calibrated_pcda"]),
        }
    return out
