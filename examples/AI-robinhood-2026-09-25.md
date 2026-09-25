# Example: AI (Artificial Inu), Robinhood Chain

Data snapshot from the fomo token and clan pages, 25 Sep 2026, ~13:30 UTC.
Contract checks were not run for this example, so they are marked UNKNOWN.
Numbers change every minute. This is a worked example of the output format, not a call.

**Input the model saw**

- Market cap $238M, liquidity $1.8M, 53K holders, top 10 hold 15.81%, age 2 months
- 24h volume $13.8M, 24h change +4.19%, last hours 88 buys / 95 sells
- Clan "Risk On" (4 traders): $9.44M position, +506%
- Clan "Sparsity" (21 traders): $4.88M position, +245%

**Output**

```
AI / ROBINHOOD CHAIN / 2 MONTHS
VERDICT: SKIP (for a new entry)   SCORE: 53/100
EXIT: $1K -0.2% | $10K -2.2% | $100K -19.0% | two clans sell 10% -85.1%

RED FLAGS:
- liquidity is 0.76% of market cap. thin.
- two clans hold $14.3M. that is 8x the pool.
- both clans are +245% to +506%. their best move is selling, not buying.
- volume/mcap 0.06 per day. attention is fading.
- sells > buys in the last hours.

GREEN FLAGS:
- 53K holders, top 10 only 15.81%.
- 2 months old. survived the first-week die-off.

WHO IS MY EXIT LIQUIDITY:
nobody below you. you are theirs. if the clans take 10% off the table,
the pool can absorb it only at -85%.

PLAN (if you ignore the verdict):
max size with <3% exit impact: ~$13.8K. invalidation: clan holdings drop
by 20%+ or liquidity falls under $1.5M.

WHAT WOULD CHANGE MY MIND:
liquidity above $5M, or the clans reducing size while price holds.

UNKNOWN: contract permissions, LP lock status, dev wallet share.
```

Score breakdown: exit 8/25, holders 14/20, smart money 9/15, momentum 9/15, contract 7/15 (unknown, scored low), narrative 6/10.

Not financial advice.
