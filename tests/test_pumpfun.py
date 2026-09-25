"""Run: python -m pytest tests/  or  python tests/test_pumpfun.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from pumpfun_exit import decode_curve, sell_on_curve  # noqa: E402

# Real account data of curve 8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh at slot 450461734
# (2026-09-25 ~20:35 UTC): back at the starting virtual reserves, real SOL ~0.
DRAINED = ("F7f4N2DYrGAAENhH488DAKWsI/wGAAAAAHjF+1HRAgClAAAAAAAAAACAxqR+jQMAAOIsFUY70ooNNO/8tAicWjiNKMwt1PMjL9JtFqu+3VbjAAAA"
           "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==")


def test_decode_real_account():
    c = decode_curve(DRAINED)
    assert c["virtual_token"] == 1_073_000_000
    assert abs(c["virtual_sol"] - 30.000000165) < 1e-9
    assert c["real_token"] == 793_100_000
    assert c["real_sol"] < 1e-6
    assert c["complete"] is False


def test_reproduces_real_sell():
    # tx 2DteD4eP...sbd, 2026-09-25 15:21:32 UTC: 8,736,256.388497 tokens -> 0.403888573 SOL.
    # Before the sell the curve's token account held 751,846,527.23515 tokens:
    # real_token = 751,846,527.235 - 206,900,000 (reserved for migration), virtual = real + 279,900,000,
    # virtual_sol from the constant product 30 * 1,073,000,000.
    vt = 751_846_527.23515 - 206_900_000 + 279_900_000
    c = {"virtual_token": vt, "virtual_sol": 30 * 1_073_000_000 / vt, "real_sol": 10.0}
    r = sell_on_curve(8_736_256.388497, c, fee_bps=125)
    assert abs(r["net_sol"] - 0.403888573) < 1e-4


def test_real_sol_caps_payout():
    c = decode_curve(DRAINED)
    r = sell_on_curve(10_000_000, c)
    assert r["capped_by_real_sol"]
    assert r["net_sol"] < 1e-6
    assert r["avg_fill"] < -0.99


def test_bigger_sell_is_worse():
    c = {"virtual_token": 800_000_000, "virtual_sol": 40.0, "real_sol": 10.0}
    fills = [sell_on_curve(n, c)["avg_fill"] for n in (1e5, 1e6, 1e7, 5e7)]
    assert all(x > y for x, y in zip(fills, fills[1:]))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
