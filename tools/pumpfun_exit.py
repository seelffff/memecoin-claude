#!/usr/bin/env python3
"""Exit scenario for a token still on a pump.fun bonding curve (SOL pairs only).

Price comes from VIRTUAL reserves, but a seller can only be paid from REAL SOL reserves.
Aggregator "liquidity" is neither of them, so do not feed it here.

  gross SOL out = virtual_sol * n / (virtual_token + n)    (n = tokens sold)
  fee           = 125 bps (pump.fun fee table for the bonding curve, and observed on a real sell, 25 Sep 2026)
  if gross > real SOL: the model only gives an UPPER BOUND and execution is UNKNOWN

Before any math the script checks that the account really is a pump.fun SOL-pair curve:
  owner = pump program, 8-byte BondingCurve discriminator, PDA ["bonding-curve", mint] matches,
  no USDC quote (USDC-paired curves exit with UNSUPPORTED_QUOTE), real SOL <= account lamports.

Checked against a real sell (tx 2DteD4eP...sbd, 2026-09-25 15:21:32 UTC): 8,736,256.39 tokens -> 0.403888573 SOL.
The model reproduces it to within 1 lamport (see tests/test_pumpfun.py).

Live data (no dependencies; public Solana RPC unless you pass --rpc):
  python tools/pumpfun_exit.py --mint 42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump
  python tools/pumpfun_exit.py --mint <mint> --save-snapshot snap.json
Manual (no checks possible, you vouch for the inputs):
  python tools/pumpfun_exit.py --virtual-sol 39.03 --virtual-token 824846527 --real-sol 9.03 --sell-tokens 8736256
"""
import argparse
import base64
import hashlib
import json
import math
import struct
import sys
import urllib.request
from datetime import datetime, timezone

LAMPORTS = 1_000_000_000
TOKEN_DECIMALS = 6
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
CURVE_DISCRIMINATOR = hashlib.sha256(b"account:BondingCurve").digest()[:8]

# ---------- base58 and PDA (no dependencies) ----------
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        if c not in _B58:
            raise ValueError(f"not base58: {s!r}")
        n = n * 58 + _B58.index(c)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * (len(s) - len(s.lstrip("1"))) + body


def b58encode(b: bytes) -> str:
    n, out = int.from_bytes(b, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + out


_P = 2**255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P


def _on_curve(b: bytes) -> bool:
    y = int.from_bytes(b, "little") & ((1 << 255) - 1)
    if y >= _P:
        return False
    y2 = y * y % _P
    x2 = (y2 - 1) * pow((_D * y2 + 1) % _P, _P - 2, _P) % _P
    return x2 == 0 or pow(x2, (_P - 1) // 2, _P) == 1


def curve_pda(mint: str) -> str:
    """find_program_address(["bonding-curve", mint], pump program)."""
    seeds = b"bonding-curve" + b58decode(mint)
    prog = b58decode(PUMP_PROGRAM)
    for bump in range(255, -1, -1):
        h = hashlib.sha256(seeds + bytes([bump]) + prog + b"ProgramDerivedAddress").digest()
        if not _on_curve(h):
            return b58encode(h)
    raise ValueError("no PDA found")


# ---------- account checks and decoding ----------
class CurveError(Exception):
    """Carries a status code: NOT_PUMP_CURVE, UNSUPPORTED_QUOTE, PDA_MISMATCH, INCONSISTENT."""

    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


def decode_curve(data_b64: str, owner: str | None = None, lamports: int | None = None) -> dict:
    """BondingCurve: 8-byte discriminator, u64 virtual_token, virtual_sol, real_token, real_sol,
    token_total_supply, bool complete, then more fields (creator, quote mint, ...)."""
    raw = base64.b64decode(data_b64)
    if owner is not None and owner != PUMP_PROGRAM:
        raise CurveError("NOT_PUMP_CURVE", f"account owner is {owner}, not the pump program")
    if len(raw) < 49 or raw[:8] != CURVE_DISCRIMINATOR:
        raise CurveError("NOT_PUMP_CURVE", "data does not start with the BondingCurve discriminator")
    if b58decode(USDC_MINT) in raw[49:]:
        raise CurveError("UNSUPPORTED_QUOTE", "curve references the USDC mint: USDC pair, not modeled")
    vt, vs, rt, rs, supply = struct.unpack_from("<QQQQQ", raw, 8)
    if lamports is not None and rs > lamports:
        raise CurveError("INCONSISTENT", "real quote reserve exceeds the account's lamports: not a SOL pair?")
    return {
        "virtual_token": vt / 10**TOKEN_DECIMALS,
        "virtual_sol": vs / LAMPORTS,
        "real_token": rt / 10**TOKEN_DECIMALS,
        "real_sol": rs / LAMPORTS,
        "supply": supply / 10**TOKEN_DECIMALS,
        "complete": bool(raw[48]),
    }


def _rpc(rpc: str, method: str, params: list) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.load(r)
    if "error" in out:
        raise ValueError(out["error"])
    return out["result"]


def fetch_curve(address: str, rpc: str) -> tuple[dict, dict]:
    res = _rpc(rpc, "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}])
    v = res["value"]
    if not v:
        raise CurveError("NOT_PUMP_CURVE", "account not found")
    c = decode_curve(v["data"][0], owner=v["owner"], lamports=v["lamports"])
    usdc = _rpc(rpc, "getTokenAccountsByOwner", [address, {"mint": USDC_MINT}, {"encoding": "jsonParsed"}])
    if usdc["value"]:
        raise CurveError("UNSUPPORTED_QUOTE", "curve owns a USDC token account: USDC pair, not modeled")
    snap = {"rpc": rpc, "method": "getAccountInfo", "account": address, "slot": res["context"]["slot"],
            "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "owner": v["owner"],
            "lamports": v["lamports"], "data_base64": v["data"][0], "decoded": c}
    return c, snap


# ---------- the model ----------
def sell_on_curve(n_tokens: float, c: dict, fee_bps: float = 125) -> dict:
    vs, vt, rs = c["virtual_sol"], c["virtual_token"], c["real_sol"]
    spot = vs / vt
    gross = vs * n_tokens / (vt + n_tokens)
    if gross > rs:
        return {"spot_sol_per_token": spot, "capped": True, "execution": "UNKNOWN",
                "payout_upper_bound_sol": rs * (1 - fee_bps / 10_000)}
    net = gross * (1 - fee_bps / 10_000)
    return {"spot_sol_per_token": spot, "capped": False, "execution": "MODELED",
            "net_sol": net, "avg_fill": net / (n_tokens * spot) - 1,
            "spot_move": ((vs - gross) / (vt + n_tokens)) / spot - 1}


def main() -> None:
    p = argparse.ArgumentParser(description="Sell scenario on a pump.fun bonding curve (SOL pairs).")
    p.add_argument("--mint", help="token mint; the curve PDA is derived and checked")
    p.add_argument("--curve", help="bonding curve account (checked against --mint if both are given)")
    p.add_argument("--rpc", default="https://api.mainnet-beta.solana.com")
    p.add_argument("--save-snapshot", help="write raw account bytes, slot and decoded fields to this JSON file")
    p.add_argument("--virtual-sol", type=float)
    p.add_argument("--virtual-token", type=float)
    p.add_argument("--real-sol", type=float)
    p.add_argument("--sell-tokens", type=float, nargs="*", help="token amounts to sell (UI units)")
    p.add_argument("--fee-bps", type=float, default=125)
    p.add_argument("--sol-usd", type=float, help="optional SOL price to show USD")
    a = p.parse_args()

    if not 0 <= a.fee_bps < 10_000:
        sys.exit("error: --fee-bps must be between 0 and 9999")

    if a.mint or a.curve:
        try:
            address = a.curve or curve_pda(a.mint)
            if a.mint and a.curve and curve_pda(a.mint) != a.curve:
                raise CurveError("PDA_MISMATCH", "this curve is not the bonding curve of that mint")
            c, snap = fetch_curve(address, a.rpc)
        except CurveError as e:
            sys.exit(f"error: {e}. exit status: {e.code}")
        except Exception as e:  # noqa: BLE001
            sys.exit(f"error: could not read the curve over RPC: {e}. exit status: UNKNOWN")
        if a.save_snapshot:
            with open(a.save_snapshot, "w") as f:
                json.dump(snap, f, indent=2)
        src = f"{address} @ slot {snap['slot']}, {snap['utc']}"
    else:
        vals = (a.virtual_sol, a.virtual_token, a.real_sol)
        if any(v is None or not math.isfinite(v) or v < 0 for v in vals) or not a.virtual_sol or not a.virtual_token:
            sys.exit("error: pass --mint, --curve, or all of --virtual-sol, --virtual-token, --real-sol")
        c = {"virtual_sol": a.virtual_sol, "virtual_token": a.virtual_token, "real_sol": a.real_sol, "complete": False}
        src = "manual input, account not checked"

    print(f"model=pumpfun_bonding_curve (SOL pair) | source: {src} | fee {a.fee_bps:g} bps")
    if c.get("complete"):
        print("curve is COMPLETE: the token migrated. this model no longer applies. get a PumpSwap / router quote.")
        return
    spot = c["virtual_sol"] / c["virtual_token"]
    usd = (lambda s: f" (${s * a.sol_usd:,.0f})") if a.sol_usd else (lambda s: "")
    print(f"spot {spot:.10f} SOL/token | virtual SOL {c['virtual_sol']:.4f} | REAL SOL {c['real_sol']:.9f}{usd(c['real_sol'])}")
    if c["real_sol"] < 0.01:
        print("real SOL is ~0: the price is only virtual. there is nothing to sell into.")

    sizes = a.sell_tokens or [s / spot for s in (0.1, 1, 10)]
    print(f"\n  {'tokens sold':>16} {'worth at spot':>14}   result")
    for n in sizes:
        if not math.isfinite(n) or n <= 0:
            sys.exit(f"error: sell size must be positive, got {n}")
        r = sell_on_curve(n, c, a.fee_bps)
        if r["capped"]:
            line = f"payout_upper_bound {r['payout_upper_bound_sol']:.9f} SOL, execution UNKNOWN (needs a simulation)"
        else:
            line = f"get {r['net_sol']:.4f} SOL | avg fill {r['avg_fill'] * 100:.1f}% | spot after {r['spot_move'] * 100:.1f}%"
        print(f"  {n:>16,.0f} {n * spot:>10.4f} SOL   {line}")
    print("\n  model of the curve at one moment, not a guarantee of execution. a simulation or live quote beats it.")


if __name__ == "__main__":
    main()
