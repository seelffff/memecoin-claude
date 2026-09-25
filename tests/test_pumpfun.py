"""Run: python -m pytest tests/  or  python tests/test_pumpfun.py"""
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from pumpfun_exit import (  # noqa: E402
    PUMP_PROGRAM, USDC_MINT, CurveError, b58decode, curve_pda, decode_curve, sell_on_curve,
)

MINT = "42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump"
CURVE = "8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh"
# Raw account data of CURVE at slot 450461734 (2026-09-25 ~20:35 UTC), owner = pump program,
# lamports 1,417,485: practically back at the starting virtual reserves, real SOL 165 lamports.
DRAINED = ("F7f4N2DYrGAAENhH488DAKWsI/wGAAAAAHjF+1HRAgClAAAAAAAAAACAxqR+jQMAAOIsFUY70ooNNO/8tAicWjiNKMwt1PMjL9JtFqu+3VbjAAAA"
           "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==")


def raises(code, fn):
    try:
        fn()
    except CurveError as e:
        assert e.code == code, e.code
        return
    raise AssertionError(f"expected {code}")


def test_pda_from_mint():
    assert curve_pda(MINT) == CURVE


def test_decode_real_account():
    c = decode_curve(DRAINED, owner=PUMP_PROGRAM, lamports=1_417_485)
    assert c["virtual_token"] == 1_073_000_000
    assert abs(c["virtual_sol"] - 30.000000165) < 1e-9
    assert c["real_sol"] == 165 / 1e9
    assert c["complete"] is False


def test_rejects_wrong_owner():
    raises("NOT_PUMP_CURVE", lambda: decode_curve(DRAINED, owner="11111111111111111111111111111111"))


def test_rejects_wrong_discriminator():
    raw = bytearray(base64.b64decode(DRAINED))
    raw[0] ^= 0xFF
    raises("NOT_PUMP_CURVE", lambda: decode_curve(base64.b64encode(bytes(raw)).decode(), owner=PUMP_PROGRAM))


def test_rejects_usdc_quote():
    raw = bytearray(base64.b64decode(DRAINED))
    raw[81:113] = b58decode(USDC_MINT)
    raises("UNSUPPORTED_QUOTE", lambda: decode_curve(base64.b64encode(bytes(raw)).decode(), owner=PUMP_PROGRAM))


def test_rejects_reserve_above_lamports():
    raises("INCONSISTENT", lambda: decode_curve(DRAINED, owner=PUMP_PROGRAM, lamports=100))


def test_reproduces_real_sell():
    # tx 2DteD4eP...sbd, 2026-09-25 15:21:32 UTC: 8,736,256.388497 tokens -> 0.403888573 SOL.
    # Pre-trade reserves rebuilt from the curve's token account balance (751,846,527.23515):
    # real_token = balance - 206,900,000 (reserved for migration), virtual = real + 279,900,000,
    # virtual_sol from the constant product 30 * 1,073,000,000. No archived RPC snapshot of that block.
    vt = 751_846_527.23515 - 206_900_000 + 279_900_000
    c = {"virtual_token": vt, "virtual_sol": 30 * 1_073_000_000 / vt, "real_sol": 10.0}
    r = sell_on_curve(8_736_256.388497, c, fee_bps=125)
    assert r["execution"] == "MODELED"
    assert abs(r["net_sol"] - 0.403888573) < 1e-8  # within 1 lamport


def test_capped_sell_is_only_an_upper_bound():
    c = decode_curve(DRAINED, owner=PUMP_PROGRAM, lamports=1_417_485)
    r = sell_on_curve(10_000_000, c)
    assert r["capped"] and r["execution"] == "UNKNOWN"
    assert "net_sol" not in r and "spot_move" not in r
    assert r["payout_upper_bound_sol"] < 1e-6


def test_bigger_sell_is_worse():
    c = {"virtual_token": 800_000_000, "virtual_sol": 40.0, "real_sol": 10.0}
    fills = [sell_on_curve(n, c)["avg_fill"] for n in (1e5, 1e6, 1e7, 5e7)]
    assert all(x > y for x, y in zip(fills, fills[1:]))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
