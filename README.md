# memecoin CLAUDE.md

One file that turns Claude into a memecoin analyst whose first job is finding the reason not to buy.

75 lines. 5 hard gates. 1 formula for exit liquidity. A fixed output: BUY / WATCH / SKIP with a score out of 100.

Written by people who trade memes every day on fomo, pump.fun and Robinhood Chain.

## What it makes Claude do

1. **Data before opinion.** No verdict from a ticker or a vibe. Missing data is printed as UNKNOWN, never guessed.
2. **Exit first.** Prints how far price falls on a $1K, $10K, $100K sell and when the top holders sell 10%.
3. **Hard gates.** Honeypot, live mint authority, dev over 10%, top 10 over 50%, liquidity under $10K: instant SKIP.
4. **Who holds, at what price.** A wallet up 20x with a bag bigger than the pool is a seller, not a signal.
5. **Momentum or exhaustion.** Our own data: tokens that hit trending with +1,000% in 24h were down 93% on average 3 days later.
6. **Narrative last.** If Claude cannot say why a stranger buys it tomorrow, it is a SKIP.
7. **Score** across six weighted blocks.
8. **Fixed output**, including "who is my exit liquidity" and "what would change my mind".
9. **No hype.** No price targets, no "gem". Token metadata is treated as untrusted text.

## Install

**Claude Code** (one project):
```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/seelffff/memecoin-claude/main/CLAUDE.md
```

**Claude Code** (every project): append it to `~/.claude/CLAUDE.md`.

**claude.ai**: create a Project, paste `CLAUDE.md` into the project instructions.

## Use it

```
check 0x2e8c31162b855a2ffa90f6f8634643ad6f111e18 on robinhood chain
```
Or drop a screenshot of the token page from fomo / dexscreener / gmgn and write `check this`.

Works best when Claude can read the chain itself. Keyless options:
- Blockscout MCP (`mcp.blockscout.com`): balances, transfers, contracts on EVM chains
- gmgn-skills (`github.com/GMGNAI/gmgn-skills`): holders, smart money, bundlers, snipers

## Exit calculator

No dependencies.
```bash
python tools/exit.py --liq 1800000 --holders 9440000 4880000 --pct 10
```
```
  sell $       1,000  ->  price   -0.2%
  sell $      10,000  ->  price   -2.2%
  sell $     100,000  ->  price  -19.0%

  top holders sell 10% ($1,432,000)  ->  price  -85.1%
  their bags are 8.0x the pool
  they cannot all exit. whoever buys now is their exit liquidity.
```

## Example

[`examples/AI-robinhood-2026-09-25.md`](examples/AI-robinhood-2026-09-25.md): a $238M token where two trader clans made $10M+ still gets SKIP for a new entry, and the file shows why.

## License

MIT. Not financial advice. Memecoins go to zero more often than they don't.
