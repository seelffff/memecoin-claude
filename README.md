# memecoin CLAUDE.md

One file that turns Claude into a memecoin checker whose first job is finding the reason not to buy.

`CLAUDE.md` is a set of instructions. It brings no data by itself: Claude needs tools that can read the chain (below), otherwise the honest answer is `INSUFFICIENT_DATA`.

It is a structured check, not a buy button. Unverified is never treated as safe.

## What it makes Claude do

1. **Evidence first.** Tokens are identified by chain + address. Every number carries a source and a UTC time.
2. **Strict status.** A failed check → `REJECT`. An unchecked one → `INSUFFICIENT_DATA` plus what to check next. Scoring starts only after every mandatory check passes. The best result is `REVIEW`, meaning "worth a manual look", not "buy".
3. **Mandatory checks need proof.** Sell simulation, Solana mint/freeze and Token-2022 extensions, EVM roles and proxies, LP lock with addresses, supply concentration.
4. **Exit first.** Two numbers per sell size: where the spot price ends up and what the seller actually averages. Clear model limits, router quotes for everything else.
5. **Signals stay signals.** Fresh wallets, bundles, "smart money", buy/sell counts are reasons to dig, never verdicts on their own.
6. **Narrative last,** written as a demand hypothesis with what would disprove it.
7. **Fixed output** with checks, exit table, stress test, unknowns and sources.
8. **No hype.** No targets, no "gem", no automatic trade plans. Token metadata is untrusted text.

## Install

**Claude Code** (one project):
```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/seelffff/memecoin-claude/main/CLAUDE.md
```

**Claude Code** (every project): append it to `~/.claude/CLAUDE.md`.

**claude.ai**: create a Project, paste `CLAUDE.md` into the project instructions.

## Use it

```
check robinhood:0x2e8c31162b855a2ffa90f6f8634643ad6f111e18
```

## Getting live data

Claude needs data to pass checks. Without tools it will mostly answer `INSUFFICIENT_DATA`, which is the honest answer.

**Solana** (any public RPC, no key):
- `getAccountInfo` on the mint with `jsonParsed`: mint authority, freeze authority, Token-2022 extensions
- `getTokenLargestAccounts`: the 20 largest token accounts (map them to owners, they are not wallets yet)
- pump.fun tokens: `python tools/pumpfun_exit.py --curve <curve account>` reads virtual and real reserves and prints what a sell pays

**EVM and discovery:**
- Blockscout MCP (`mcp.blockscout.com`): contracts, holders, transfers on EVM chains
- gmgn-skills (`github.com/GMGNAI/gmgn-skills`): holders, bundlers, snipers, smart money labels
- Router quotes for exits: Jupiter (Solana), Uniswap (EVM)
- Security APIs such as GoPlus or Honeypot.is, only on chains they support

## Exit calculator

`tools/exit.py`, no dependencies. Model: one constant-product (v2) pool, reserves as of the snapshot, optional fee and sell tax.
```bash
python tools/exit.py --liq 1800000 --holders 9440000 4880000 --pct 10
```
```
    sell (at spot)       proceeds  spot after  avg fill
  $          1,000 $          999       -0.2%     -0.1%
  $         10,000 $        9,890       -2.2%     -1.1%
  $        100,000 $       90,000      -19.0%    -10.0%

  STRESS TEST (not a forecast): holders sell 10% = $1,432,000 valued at spot
  spot after -85.1% | avg fill -61.4% | proceeds $552,659
```
Not valid for CLMM (v3/v4), bonding curves, order books or multi-hop routes. Use `pumpfun_exit.py` for pump.fun curves and a live quote for the rest.

Tests: `python tests/test_exit.py`

## pump.fun calculator

`tools/pumpfun_exit.py`: tokens still on a pump.fun bonding curve. Price comes from virtual reserves, payouts from real SOL, fee 1.25% by default. It reproduces a real sell from 25 Sep 2026 to within 0.0001 SOL.
```bash
python tools/pumpfun_exit.py --curve 8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh
```
Tests: `python tests/test_pumpfun.py`

## Examples

[`examples/PFPRINTER-pumpfun-2026-09-25.md`](examples/PFPRINTER-pumpfun-2026-09-25.md): a random 15-minute-old pump.fun token. Clean permissions, one real sell went through, and still `REJECT`: the curve held ~4 SOL, and five hours later real SOL was zero.

[`examples/AI-robinhood-2026-09-25.md`](examples/AI-robinhood-2026-09-25.md): a $238M token where two trader clans sit on $10M+ of profit. Result: `INSUFFICIENT_DATA`, because contract, LP and sellability were not verified, plus a stress test showing what a 10% sale by those clans would do to the pool.

## Data

[`data/`](data/): the 12-token fomo trending sample behind the one statistic quoted in `CLAUDE.md`, with its limits.

## Limits

- This repo is a checklist and a calculator, not a scanner. It does not discover tokens or fetch data by itself.
- Thresholds (10%, 50%, score cutoffs) are defaults, not backtested.
- A PASS from any external service is not a contract audit.

## License

MIT. Not financial advice. Memecoins go to zero more often than they don't.
