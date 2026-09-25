# fomo trending sample, Sep 2026

`fomo-trending-sample-2026-09.csv`: 12 tokens that were on the fomo trending feed on Sep 22 or Sep 23, 2026.

- `change_24h_when_seen_pct`: the 24h change fomo showed when we logged the token.
- `mcap_when_seen_usd` / `mcap_2026_09_25_usd`: market cap from the fomo token page, logged by hand.
- `mcap_change_pct`: mcap on Sep 25 / mcap when seen - 1.
- `top_traders_in_holders`: whether any fomo top-10 leaderboard trader held it when seen.

Result quoted in CLAUDE.md: the 3 tokens with 1,000%+ in 24h averaged -92.6% (arithmetic mean of mcap change) 2–3 days later.

Limits: 12 tokens, 3 in the headline group, one feed, one week, hand-logged, no liquidity or rug labels. Rows have tickers, not contract addresses, and no archived snapshots, so the arithmetic can be repeated but the observations cannot. It is a manual observation (n=3), not a backtest.
