# Example: a random fresh pump.fun token (PFPRINTER)

How it was picked: row 13 of the first 20 rows on [GeckoTerminal new Solana pools](https://www.geckoterminal.com/explore/new-crypto-pools/solana) at ~15:20 UTC, 25 Sep 2026, chosen with `secrets.randbelow(20) + 1`. The other 19 rows were not saved, so the pick cannot be replayed from the list. The addresses below can.

| Field | Value |
|---|---|
| Mint | [`42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump`](https://solscan.io/token/42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump) |
| Market | pump.fun bonding curve, not migrated |
| Curve account | [`8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh`](https://solscan.io/account/8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh) |

## Two snapshots

**15:20–15:26 UTC** (manual check on GeckoTerminal and Solscan, not archived): age ~15 min, market cap ~$4.2K, GeckoTerminal "liquidity" $3,357, 184 buys / 141 sells, about -52% since launch. The curve account's SOL balance was ~4.4 at 15:24 and ~3.8 at 15:25 (account balance, which includes rent; the decoded reserve field was not saved). 86.28% of supply sat on the curve.

**20:35 UTC** (Solana RPC `getAccountInfo`, base64, slot 450461734, raw bytes below): virtual token 1,073,000,000, virtual SOL 30.000000165, real SOL **0.000000165** (165 lamports). The curve is practically back at its starting state: almost everything that was bought has been sold back. Read again at slot 450465423 with the same bytes.

## Output

```
TOKEN: solana:42pHP3TzLVX7Egx8zBwidnAFB4vUR9tzGgZssyGspump | MARKET: pump.fun curve 8t4tkj...h1wh | UTC: 2026-09-25 20:35
STATUS: REJECT   SCORE: n/a
CONFIDENCE: medium (mint and curve read from chain; holders not mapped to owners)

CHECKS:
  identity        PASS   mint and curve confirmed on chain
  mint / freeze   PASS   both null (Solana RPC, jsonParsed)
  Token-2022 ext  PASS   only metadataPointer + tokenMetadata. no transfer fee, hook, delegate or pause
  sellable        UNKNOWN  no simulation run for now
  HISTORICAL_SELL verified at 15:21:32 UTC (tx 2DteD4eP...sbd), says nothing about now
  LP              N/A    still on the bonding curve, no LP exists yet
  supply          UNKNOWN  86.28% on the curve (program account, excluded). ordinary wallets not mapped
  exit depth      FAIL   at 15:24 the curve held ~4.4 SOL (~$530): a $1K exit was impossible.
                         at 20:35 real SOL is ~0: nothing to sell into

EXIT: v2 calculator does not apply. pump.fun model (tools/pumpfun_exit.py):
  any sell at 20:35 → payout_upper_bound ~0.000000163 SOL, execution UNKNOWN

LABELS (opinions, not checks): GeckoTerminal score 20/100, RugCheck "DANGER"

SOURCES: GeckoTerminal pool page and Solscan 15:20–15:26 UTC; Solana RPC getAccountInfo 20:35 UTC
```

## What this shows

- The aggregator said "$3.4K liquidity". The curve could pay out about 4 SOL at that moment, and zero five hours later.
- Clean token permissions and one successful sell do not make a token exitable.
- 86% "held by one account" was the bonding curve itself, not a whale.

The pump.fun model in `tools/pumpfun_exit.py` reproduces the real sell in this token (8,736,256.39 tokens → 0.403888573 SOL) to within 1 lamport with the 1.25% bonding curve fee. The pre-trade reserves are rebuilt from the curve's token balance, not from an archived RPC snapshot. See `tests/test_pumpfun.py`.

## Raw snapshot

```json
{"method": "getAccountInfo", "account": "8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh", "slot": 450461734,
 "owner": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P", "lamports": 1417485,
 "data_base64": "F7f4N2DYrGAAENhH488DAKWsI/wGAAAAAHjF+1HRAgClAAAAAAAAAACAxqR+jQMAAOIsFUY70ooNNO/8tAicWjiNKMwt1PMjL9JtFqu+3VbjAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="}
```


Not financial advice.
