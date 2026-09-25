#!/usr/bin/env python3
"""Exit liquidity check for a constant-product pool (Uniswap v2 style, pump-style AMMs).

Price impact of selling V dollars into a pool with total liquidity L (both sides, in $):
    impact = 1 - 1 / (1 + 2V / L) ** 2

Examples:
    python tools/exit.py --liq 1800000
    python tools/exit.py --liq 1800000 --sell 5000 25000
    python tools/exit.py --liq 1800000 --holders 9440000 4880000 --pct 10
"""
import argparse


def impact(sell_usd: float, liquidity_usd: float) -> float:
    if liquidity_usd <= 0:
        return 1.0
    return 1 - 1 / (1 + 2 * sell_usd / liquidity_usd) ** 2


def main() -> None:
    p = argparse.ArgumentParser(description="How far does price fall when someone sells?")
    p.add_argument("--liq", type=float, required=True, help="pool liquidity in USD (both sides)")
    p.add_argument("--sell", type=float, nargs="*", default=[1_000, 10_000, 100_000], help="sell sizes in USD")
    p.add_argument("--holders", type=float, nargs="*", default=[], help="big holder positions in USD")
    p.add_argument("--pct", type=float, default=10, help="percent of the holders' positions they sell")
    a = p.parse_args()

    print(f"pool liquidity: ${a.liq:,.0f}\n")
    for s in a.sell:
        print(f"  sell ${s:>12,.0f}  ->  price {-impact(s, a.liq) * 100:6.1f}%")

    if a.holders:
        total = sum(a.holders) * a.pct / 100
        print(f"\n  top holders sell {a.pct:g}% (${total:,.0f})  ->  price {-impact(total, a.liq) * 100:6.1f}%")
        ratio = sum(a.holders) / a.liq
        print(f"  their bags are {ratio:,.1f}x the pool")
        if ratio > 1:
            print("  they cannot all exit. whoever buys now is their exit liquidity.")

    safe = a.liq * ((1 / 0.97) ** 0.5 - 1) / 2
    print(f"\n  max size you can fully exit with <3% impact: ${safe:,.0f}")


if __name__ == "__main__":
    main()
