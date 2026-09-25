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

**Full repo** (rules + calculators + tests):
```bash
git clone https://github.com/seelffff/memecoin-claude.git
cd memecoin-claude && claude
```

**Rules only, inside a project you already have.** Save under a new name so your own `CLAUDE.md` is not overwritten, then import it:
```bash
curl -o memecoin.md https://raw.githubusercontent.com/seelffff/memecoin-claude/main/CLAUDE.md
echo "@memecoin.md" >> CLAUDE.md
```
The `tools/` calculators are not included in this mode.

**claude.ai**: create a Project, paste `CLAUDE.md` into the project instructions. Calculators are not available there.

## Use it

```
check robinhood:0x2e8c31162b855a2ffa90f6f8634643ad6f111e18
```

## Getting live data

Claude needs data to pass checks. Without tools it will mostly answer `INSUFFICIENT_DATA`, which is the honest answer.

**Solana** (any public RPC, no key). Read-only JSON-RPC, for example the mint's permissions:
```bash
curl -s https://api.mainnet-beta.solana.com -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":1,"method":"getAccountInfo",
  "params":["<MINT>",{"encoding":"jsonParsed"}]}'
```
Look at `result.value.data.parsed.info`: `mintAuthority`, `freezeAuthority`, `extensions`. The response also carries `context.slot`: keep it as the snapshot reference.
- `getTokenLargestAccounts` with the mint: the 20 largest token accounts. Map them to owners, they are not wallets yet.
- pump.fun tokens, from the mint alone:
  ```bash
  python tools/pumpfun_exit.py --mint <MINT> --save-snapshot snap.json
  ```
  It derives the curve PDA from the mint, checks the owner program, the account type and that the pair is SOL (USDC pairs stop with `UNSUPPORTED_QUOTE`), then prints what a sell pays and saves the raw bytes with the slot.

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

`tools/pumpfun_exit.py`: tokens still on a pump.fun bonding curve, SOL pairs only. Price comes from virtual reserves, payouts from real SOL, fee 1.25% by default. It reproduces a real sell from 25 Sep 2026 to within 1 lamport. When a sell is bigger than the real SOL on the curve it prints only an upper bound and `execution UNKNOWN`.
```bash
python tools/pumpfun_exit.py --mint 42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump
```
Tests: `python tests/test_pumpfun.py`

## Examples

[`examples/PFPRINTER-pumpfun-2026-09-25.md`](examples/PFPRINTER-pumpfun-2026-09-25.md): a random 15-minute-old pump.fun token. Clean permissions, one real sell went through, and still `REJECT`: the curve held ~4 SOL, and five hours later real SOL was zero.

[`examples/AI-robinhood-2026-09-25.md`](examples/AI-robinhood-2026-09-25.md): a $238M token where two trader clans sit on $10M+ of profit. Result: `INSUFFICIENT_DATA`, because contract, LP and sellability were not verified, plus a stress test showing what a 10% sale by those clans would do to the pool.

## Data

[`data/`](data/): the 12-token fomo trending sample behind the one statistic quoted in `CLAUDE.md`, with its limits.

## Limits

- `CLAUDE.md` does not fetch data. `pumpfun_exit.py --mint` reads one pump.fun curve over RPC. There is no scanner and no pipeline: nothing here discovers tokens.
- No sell simulation is built in. Sellability stays `UNKNOWN` until an external simulator or live quote answers.
- Thresholds (10%, 50%, score cutoffs) are defaults, not backtested.
- A PASS from any external service is not a contract audit.

## License

MIT. Not financial advice. Memecoins go to zero more often than they don't.
