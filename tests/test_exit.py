"""Run: python -m pytest tests/  or  python tests/test_exit.py"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from exit import max_size_for_spot_move, sell  # noqa: E402

Q = 900_000  # quote reserve of a $1.8M TVL pool
EXIT = os.path.join(os.path.dirname(__file__), "..", "tools", "exit.py")


def close(a, b, tol=1e-3):
    return abs(a - b) < tol


def test_known_values():
    r = sell(100_000, Q)
    assert close(r["spot_move"], -(1 - 1 / (1 + 200_000 / 1_800_000) ** 2))  # -19.0%
    assert close(r["avg_fill"], -(1 - 1 / (1 + 200_000 / 1_800_000)))       # -10.0%
    r = sell(1_432_000, Q)
    assert close(r["spot_move"], -0.851)
    assert close(r["avg_fill"], -0.614)


def test_monotonic():
    moves = [sell(v, Q)["spot_move"] for v in (1e3, 1e4, 1e5, 1e6, 1e7)]
    assert all(a > b for a, b in zip(moves, moves[1:]))


def test_fee_and_tax_make_it_worse():
    base = sell(50_000, Q)
    assert sell(50_000, Q, fee_bps=30)["avg_fill"] < base["avg_fill"]
    assert sell(50_000, Q, tax_bps=500)["avg_fill"] < sell(50_000, Q, fee_bps=30)["avg_fill"]


def test_spot_and_average_differ():
    r = sell(100_000, Q)
    assert r["spot_move"] < r["avg_fill"] < 0


def test_max_size():
    v = max_size_for_spot_move(Q, 0.03)
    assert close(sell(v, Q)["spot_move"], -0.03)


def test_bad_input_is_rejected():
    for args in (["--liq", "0"], ["--liq", "-5"], ["--liq", "nan"], ["--liq", "1e6", "--sell", "-1"],
                 ["--liq", "1e6", "--pct", "150"], ["--liq", "1e6", "--fee-bps", "10000"]):
        out = subprocess.run([sys.executable, EXIT, *args], capture_output=True, text=True)
        assert out.returncode != 0, args
        assert "error" in out.stderr, args


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    assert math.isfinite(sell(1, Q)["spot_move"])
