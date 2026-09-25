#!/usr/bin/env python3
"""Exit liquidity scenario for ONE constant-product pool (Uniswap v2 style).

model = constant_product_v2
  L = total two-sided pool TVL in USD (quote side = L/2), or pass --quote-reserve
  V = USD value of the tokens sold, valued at the current spot price
  fees and sell tax optional; no external liquidity, no routing, reserves as of the snapshot

It prints two different numbers:
  spot after   how far the pool price sits below the start price after the sell
  avg fill     how much worse the seller's average price was than the start price

Not valid for CLMM (v3/v4), bonding curves (pump.fun), order books or multi-hop routes.
For those, ask a router for a live quote (Jupiter, Uniswap) or report NOT_MODELED.

Examples:
  python tools/exit.py --liq 1800000
  python tools/exit.py --liq 1800000 --sell 5000 25000 --fee-bps 30
  python tools/exit.py --liq 1800000 --holders 9440000 4880000 --pct 10
"""
import argparse
import math
import sys


def sell(v_usd: float, quote_reserve: float, fee_bps: float = 0, tax_bps: float = 0) -> dict:
    """Sell tokens worth v_usd (at spot) into a v2 pool whose quote reserve is quote_reserve.

    At spot, the token reserve is worth the same as the quote reserve, so both sides = q in USD terms.
    """
    q = quote_reserve
    into_pool = v_usd * (1 - tax_bps / 10_000)          # tax is taken before the pool
    effective = into_pool * (1 - fee_bps / 10_000)      # v2 fee: only this part moves the curve
    out = q * effective / (q + effective)               # quote received
    spot_after = (q - out) / (q + into_pool)            # new price / start price
    return {
        "proceeds": out,
        "spot_move": spot_after - 1,                    # negative number
        "avg_fill": (out / v_usd - 1) if v_usd else 0.0,  # negative number, includes fee and tax
    }


def max_size_for_spot_move(quote_reserve: float, move: float = 0.03) -> float:
    """Largest no-fee sell (USD at spot) that moves spot price by at most `move`."""
    return quote_reserve * (1 / math.sqrt(1 - move) - 1)


def positive(name: str, x: float, allow_zero: bool = False) -> float:
    if not math.isfinite(x) or x < 0 or (x == 0 and not allow_zero):
        sys.exit(f"error: {name} must be a {'non-negative' if allow_zero else 'positive'} number, got {x}")
    return x


def main() -> None:
    p = argparse.ArgumentParser(description="Exit scenario for one constant-product pool.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--liq", type=float, help="total two-sided pool TVL in USD")
    g.add_argument("--quote-reserve", type=float, help="quote side of the pool in USD (e.g. the WETH/SOL/USDC side)")
    p.add_argument("--sell", type=float, nargs="*", default=[1_000, 10_000, 100_000], help="sell sizes in USD at spot")
    p.add_argument("--fee-bps", type=float, default=0, help="pool fee in basis points (30 = 0.3%%)")
    p.add_argument("--sell-tax-bps", type=float, default=0, help="token sell tax in basis points")
    p.add_argument("--holders", type=float, nargs="*", default=[], help="big holder positions in USD, valued at spot")
    p.add_argument("--pct", type=float, default=10, help="percent of the holders' positions sold in the stress test")
    a = p.parse_args()

    q = positive("--quote-reserve", a.quote_reserve) if a.quote_reserve is not None else positive("--liq", a.liq) / 2
    fee = positive("--fee-bps", a.fee_bps, allow_zero=True)
    tax = positive("--sell-tax-bps", a.sell_tax_bps, allow_zero=True)
    if fee >= 10_000 or tax >= 10_000:
        sys.exit("error: fee and tax must be below 10000 bps")
    pct = positive("--pct", a.pct)
    if pct > 100:
        sys.exit("error: --pct must be at most 100")

    print(f"model=constant_product_v2 | quote reserve ${q:,.0f} (pool TVL ${2 * q:,.0f}) | fee {fee:g} bps | tax {tax:g} bps")
    print("valid for one v2-style pool only. CLMM, bonding curve, routes: NOT_MODELED\n")
    print(f"  {'sell (at spot)':>16} {'proceeds':>14} {'spot after':>11} {'avg fill':>9}")
    for s in a.sell:
        s = positive("--sell", s)
        r = sell(s, q, fee, tax)
        print(f"  ${s:>15,.0f} ${r['proceeds']:>13,.0f} {r['spot_move'] * 100:>10.1f}% {r['avg_fill'] * 100:>8.1f}%")

    if a.holders:
        bags = [positive("--holders", h) for h in a.holders]
        total = sum(bags) * pct / 100
        r = sell(total, q, fee, tax)
        print(f"\n  STRESS TEST (not a forecast): holders sell {pct:g}% = ${total:,.0f} valued at spot")
        print(f"  spot after {r['spot_move'] * 100:.1f}% | avg fill {r['avg_fill'] * 100:.1f}% | proceeds ${r['proceeds']:,.0f}")
        print(f"  their bags, valued at spot, are {sum(bags) / (2 * q):,.1f}x the pool TVL. check the lists do not overlap.")

    print(f"\n  max_model_input_for_3pct_spot_move (no fees): ${max_size_for_spot_move(q):,.0f}")
    print("  model and snapshot only. a live router quote beats this number.")


if __name__ == "__main__":
    main()
