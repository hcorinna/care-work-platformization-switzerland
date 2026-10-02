# Pipeline Overview

This repository contains the public code for the project. Raw and record-level data are excluded.

## 1) Data collection (`src/01_data_collection/`)

- Platform-specific scrapers and shared utilities for login, pagination, and extraction
- Output is saved as raw snapshots (private)
- Postal code resources live in `src/01_data_collection/resources/postal_codes/`
- Output/log locations can be configured in `src/shared/config/paths.json`
- Scraper selection is configured in `src/01_data_collection/config/scrapers.json` (use `--dry-run` to validate without scraping, `--config <path>` for alternate configs)

## 2) Cleaning (`src/02_cleaning/`)

- Standardizes column names and data types
- Normalizes locations and monetary fields
- Resolves obvious duplicates and malformed records
- Drops out-of-scope entries
- Location cleaning uses a local Nominatim cache (see below)
- Run via `src/02_cleaning/run_cleaning.py` with `src/02_cleaning/config/cleaning.json` (defaults to `dry_run: true`, override with `--run` or `--dry-run`)
- Raw data is stored under `data/raw/` and uses timestamped filenames rather than hardcoded date folders

## 3) Preprocessing (`src/03_preprocessing/`)

- Aggregates records into analysis-ready tables
- Generates derived features used in figures
- Run via `src/03_preprocessing/run_preprocessing.py` with `src/03_preprocessing/config/preprocessing.json` (defaults to `dry_run: true`, override with `--run` or `--dry-run`)
- Parameters for preprocessing live in `src/03_preprocessing/config/config.yaml`
- You can override the preprocessing config path with `--config <path>`
- Gender inference uses a local cache (`src/03_preprocessing/gender_data.csv`) to avoid repeat API calls; this cache is not committed
- Set `gender_use_api` in `src/03_preprocessing/config/preprocessing.json` to enable API calls (default off)

## 4) Analysis (`src/04_analysis/`)

- `src/04_analysis/make_figures.py` creates the figures of the paper (`f01`–`f04`) from the processed data in `data/processed/`
- Figures are written to `outputs/figures/` as PDF (vector graphics with embedded fonts) and collected in `outputs/figures/figures.zip` for the journal upload
- Each figure is also saved as a 300 dpi PNG, which is not part of the zip file
- Use `--data-dir <path>` to read the processed data from another location and `--out-dir <path>` to write somewhere else

## Orchestrator (`src/pipeline.py`)

Use the orchestrator to run scraping → cleaning → preprocessing in one command.
If no stage flags are provided, all three stages run by default.

Examples:

```bash
python src/pipeline.py --dry-run
python src/pipeline.py --scrape
python src/pipeline.py --clean --clean-config src/02_cleaning/config/cleaning.json
python src/pipeline.py --preprocess --preprocess-config src/03_preprocessing/config/preprocessing.json
```

## Outputs

- Aggregated, non-identifying figures are written to `outputs/` locally, but this folder is excluded from version control (see `.gitignore`)
- Raw, intermediate, and record-level datasets are not included

## Replication limits

- Full reproduction requires valid platform accounts and credentials
- Scraping behavior is sensitive to platform changes and anti-bot measures
- Rate limits and layout updates can alter scrape results
- The public repo supports code review and figure regeneration from the processed data, not raw data reconstruction

## Nominatim cache

Location normalization uses OpenStreetMap Nominatim and stores responses in a local cache at `src/shared/cache/nominatim_cache.json`. The cache is meant to be local and can be deleted to re-query fresh results; avoid committing it when sharing the repo.

## Minimal test run

To run a small scrape, set a short `plz_list` in `src/01_data_collection/config/scrapers.json` and run `src/01_data_collection/scrapers/main.py`. Use `--dry-run` to validate configuration without launching a browser, and `--config <path>` to point to an alternate config file.
