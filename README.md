# NQ System — SELF-UPDATING board site

After a one-time ~7-minute setup, this updates ITSELF every 15 minutes, Mon–Fri.
You never drop a file again.

## One-time setup
1. Free account at github.com → New repository → name `nq-board` → Public → Create.
2. Add file → Upload files → drag EVERYTHING in this folder in (including the `.github` folder — if your unzip hides it, upload via "creating a new file" named `.github/workflows/board.yml` and paste its contents). Commit.
3. Settings → Pages → Deploy from branch → `main` / root → Save.  Your URL: `https://YOU.github.io/nq-board/`
4. Actions tab → click "I understand… enable workflows" → open `auto-board` → **Run workflow** once to test.
5. Done. It now runs itself every 15 minutes on GitHub's computers.

## What updates itself vs what doesn't
- **Live chart (top)**: streams continuously on its own — TradingView's widget.
- **Mechanical board (bottom)**: rebuilt every 15 min by the engine — session, DCV bands, pools, open efficiency, macro ledger, virgin connectors (50% rule, 1M-verified), active MIST with HP flags, ladder, probability tags.
- **Not in auto mode**: bias narrative, scenario writing, trade grading, the scorecard — the judgment layer stays in the Claude sessions (paste any auto-board into chat for the full treatment).

## Data honesty
Auto mode uses Yahoo's free continuous futures (NQ=F/ES=F/YM=F): unofficial, can lag CME by minutes and differ by ticks. Good enough for structure; your TradingView chart remains the execution truth. Swap `fetch()` for a real vendor (Databento/broker API) anytime for exact data.

## If a run fails
Actions tab → open the red run → copy the log → paste it to Claude → patched engine comes back.
