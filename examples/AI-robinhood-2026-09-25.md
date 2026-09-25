# Example: AI (Artificial Inu), Robinhood Chain

A worked example of the output format on real, public numbers. Not a call.

**Snapshot:** 25 Sep 2026, ~13:30 UTC, read by hand from fomo.

| Input | Value | Source |
|---|---|---|
| Token | `0x2e8c31162b855a2ffa90f6f8634643ad6f111e18` | [fomo token page](https://fomo.family/tokens/robinhood/0x2e8c31162b855a2ffa90f6f8634643ad6f111e18) |
| Market cap | $238M | same |
| Liquidity (as shown by fomo) | $1.8M | same. Pool address and pool type not shown |
| Holders / top 10 | 53K / 15.81% | same. Exclusion of pool/burn not stated |
| Age | "2 mo." (created) | same. First pool and first trade time not checked |
| 24h volume / change | $13.8M / +4.19% | same |
| Clan "Risk On", 4 traders | $9.44M position, +506% | [clan page](https://fomo.family/clans/fc94d51d-4a71-4078-a635-77a11c94a2e9?window=24h) |
| Clan "Sparsity", 21 traders | $4.88M position, +245% | [clan page](https://fomo.family/clans/87c22801-d5a6-4e9e-8f18-bceadf8b1040?window=24h) |

**Output**

```
TOKEN: robinhood:0x2e8c31162b855a2ffa90f6f8634643ad6f111e18 | POOL: UNKNOWN | UTC: 2026-09-25 ~13:30
STATUS: INSUFFICIENT_DATA   SCORE: n/a
CONFIDENCE: low (checked 3 of 8 mandatory fields, all from one source)

CHECKS:
  sellable      UNKNOWN   no sell simulation run on Robinhood Chain
  mint / roles  UNKNOWN   contract permissions not read
  proxy         UNKNOWN
  LP            UNKNOWN   pool address, lock and owner not found
  dev share     UNKNOWN
  top 10        PASS      15.81% (fomo figure, exclusions not stated)
  liquidity     PASS      $1.8M shown, pool type unknown
  identity      PASS      contract address confirmed on the fomo URL

EXIT (scenario only: assumes ONE constant-product pool holding all $1.8M):
  $1K    spot after -0.2%   avg fill -0.1%
  $10K   spot after -2.2%   avg fill -1.1%
  $100K  spot after -19.0%  avg fill -10.0%
  if the pool is CLMM or liquidity is split across pools: NOT_MODELED, get a router quote

STRESS (not a forecast):
  both clans sell 10% ($1.43M valued at spot) → spot -85.1%, avg fill -61.4%
  clan positions valued at spot are 8x the stated liquidity
  overlap: none among the members shown on both pages; full lists not checked

RED FLAGS:
- liquidity is 0.76% of market cap
- two groups hold positions 8x the stated liquidity, both deep in profit
- volume/mcap 0.06 per day

GREEN FLAGS:
- 53K holders, top 10 at 15.81%
- has traded for about 2 months

UNKNOWN → how to check:
- sellability → sell simulation or a live router quote on Robinhood Chain
- contract roles, proxy → read the verified contract on the chain explorer
- LP → find the pool address, then who holds the LP position and whether it can be pulled
- dev share → holder list with pool/burn/CEX addresses labeled

SOURCES: fomo token page and two clan pages above, 2026-09-25 ~13:30 UTC
```

What this shows: even with $10M+ of visible profit on the chart, the file does not hand out a green light. Five mandatory checks are unverified, so the status is INSUFFICIENT_DATA, and the stress test explains why size matters here.

Not financial advice.
