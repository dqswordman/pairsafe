from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pairsafe.calibration import calibrated_pcda
from pairsafe.metrics import best_pcda, pcda_at, psa


def almost_equal(a: float, b: float, eps: float = 1e-12) -> None:
    assert abs(a - b) <= eps, (a, b)


def test_pair_constant_proxy() -> None:
    rows = [{"safe_score": 1.0, "unsafe_score": 1.0} for _ in range(4)]
    almost_equal(psa(rows), 0.5)
    almost_equal(pcda_at(rows, 1.0), 0.0)
    almost_equal(best_pcda(rows)["pcda"], 0.0)


def test_perfect_separator() -> None:
    rows = [{"safe_score": 0.0, "unsafe_score": 1.0}, {"safe_score": -1.0, "unsafe_score": 2.0}]
    almost_equal(psa(rows), 1.0)
    almost_equal(best_pcda(rows)["pcda"], 1.0)


def test_calibrated_pcda() -> None:
    rows = [{"safe_score": 0.0, "unsafe_score": 1.0} for _ in range(10)]
    result = calibrated_pcda(rows, k=5, seed=13)
    almost_equal(result["calibrated_pcda"], 1.0)
    assert len(result["folds"]) == 5


if __name__ == "__main__":
    test_pair_constant_proxy()
    test_perfect_separator()
    test_calibrated_pcda()
    print("metrics tests PASS")
