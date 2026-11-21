# Updating the MMM data library

Run this from the repository root after `pip install -r requirements.txt`.

```bash
python scripts/update_data.py
```

What the script does:

1. Reads `symbols.csv`.
2. For each symbol and interval (`1d`, `1h`, `15m`, `5m`), downloads the latest Yahoo Finance window.
3. Merges new rows into `data/<SYMBOL>/<SYMBOL>_<interval>.csv`.
4. De-duplicates on `Datetime` (last write wins) and sorts ascending.
5. Rewrites `data/inventory.csv` and the inventory table in `README.md`.

Yahoo only serves a limited lookback for intraday bars (about 730 days for 1h, about 60 days for 15m/5m). Do not replace a CSV wholesale with a fresh Yahoo pull, or older accumulated history will be lost. Always use this script (or the same merge/de-dupe logic).

Useful flags:

```bash
python scripts/update_data.py --symbols ES NQ --intervals 1d 1h
python scripts/update_data.py --sleep 0.8
python scripts/update_data.py --skip-readme
```

After a successful run, commit the changed CSVs, `data/inventory.csv`, and `README.md` together.

Suggested weekly commit message:

```
Weekly MMM data update: Yahoo Finance OHLCV
```

## Publishing the update

The GitHub connector tool `push_files` (namespace `user-GitHub-xai`) can commit many paths at once, but this environment only substitutes **4** `$file:...` contents per call. The CSV library is about 20 MB (each file is about 0.1–1.3 MB, well under GitHub’s 100 MB file limit), so a single call cannot upload every CSV by inlining.

### Weekly procedure (connector, one squash commit on `main`)

From a checkout or staging copy of the repo:

```bash
pip install -r requirements.txt
python scripts/update_data.py
```

Then publish with the GitHub connector:

1. Create a branch from current `main` (for example `data-update-YYYY-MM-DD`).
2. Call `push_files` on that branch in batches of **at most 4 files**, passing each CSV/doc as `"content": "$file:/absolute/path/to/file"`. Include every changed path (`data/**/*.csv`, `data/inventory.csv`, `README.md`).
3. Open a pull request into `main` and **squash-merge** it.

- owner: `MaxMaseratii`
- repo: `ECHANTIYONFITI`
- base: `main`
- squash commit title: `Weekly MMM data update: Yahoo Finance OHLCV`

### Preferred path once `gh` or git is authenticated

A logged-in `gh`/`git` push is simpler for weekly jobs, because it has no 4-file payload cap:

```bash
pip install -r requirements.txt
python scripts/update_data.py
git add data symbols.csv README.md UPDATING.md scripts requirements.txt
git commit -m "Weekly MMM data update: Yahoo Finance OHLCV"
git push origin main
```

The machine that built the initial library did not have `gh` logged in; do not assume a bare `git push` works until GitHub CLI or git credentials are set up for this private repo.

File-size note: warn if any committed file approaches 50 MB (GitHub hard-rejects 100 MB).
