# Extending the platform debate beyond cities: Assessing the scale and scope of platform-mediated childcare work in Switzerland

This repository contains the code for the paper:

> Corinna Hertweck, Aniko Hannak and Karin Schwiter: Extending the platform debate beyond cities: Assessing the scale and scope of platform-mediated childcare work in Switzerland, Geographica Helvetica, 2026.

Paper link / DOI: *to be added upon publication*

The code scrapes worker and customer profiles from care work platforms operating in Switzerland, cleans and preprocesses the scraped data (activity levels, name-based gender inference, location standardisation) and creates the figures of the paper.

## Repository structure

- `src/01_data_collection/`: platform-specific scrapers, shared scraping utilities, and resources
- `src/02_cleaning/`: cleaning and standardization steps
- `src/03_preprocessing/`: aggregation and feature preparation
- `src/04_analysis/`: figures of the paper
- `docs/PIPELINE.md`: pipeline overview and replication limits

## Data availability

The record-level data are private and **not included** in this repository. Contact the authors for access to aggregate data under appropriate agreements.

The repository does include publicly available reference data: the official directory of towns and cities by the Swiss Federal Office of Topography (swisstopo) in `src/01_data_collection/resources/postal_codes/` as well as population, population density and municipality name translations by the Swiss Federal Statistical Office (BFS) in `src/03_preprocessing/plz_data/`.

## Setup

The code was developed with Python 3.13. The scrapers use Selenium with Google Chrome, so Chrome needs to be installed.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` is a snapshot of the full development environment on macOS. On other operating systems, you may have to remove the macOS-specific packages (`pyobjc*`, `appnope`).

## Credentials

Copy `credentials.template.json` to a local `credentials.json` and fill in your own credentials there.

## Minimal scrape test

To run a quick test scrape, set a short `plz_list` in `src/01_data_collection/config/scrapers.json` and run `main.py`. Use `--dry-run` to validate configuration without launching a browser.
Scraper output and log locations can be overridden in `src/shared/config/paths.json`.
You can also pass `--config <path>` to point `main.py` at another config file.

## Scraper configuration

The main scraper runner reads `src/01_data_collection/config/scrapers.json` to determine which platforms to run and optional PLZ filtering. Use `--dry-run` to validate configuration without scraping, and `--config <path>` to point to another config file.

## Cleaning and preprocessing

Use the config-driven runners (both default to `dry_run: true`):
- `src/02_cleaning/run_cleaning.py` with `src/02_cleaning/config/cleaning.json` (override with `--run` or `--dry-run`)
- `src/03_preprocessing/run_preprocessing.py` with `src/03_preprocessing/config/preprocessing.json` (override with `--run` or `--dry-run`)

Cleaning paths use the shared config in `src/shared/config/paths.json` (data/log/scraper runs directories).
Preprocessing parameters are defined in `src/03_preprocessing/config/config.yaml`.
You can override the preprocessing config path with `--config <path>`.

Gender inference uses a local cache file (`src/03_preprocessing/gender_data.csv`) to avoid repeat API calls. This cache is intentionally excluded from version control.
Use `gender_use_api` in `src/03_preprocessing/config/preprocessing.json` to enable API calls (default off). The API used is [Gender API](https://gender-api.com/) — sign up there to obtain a key and add it as `GENDER_API_KEY` in your `credentials.json`.

## Pipeline orchestrator

Use `src/pipeline.py` to run scraping → cleaning → preprocessing in sequence. If no stage flags are provided, all three run by default.
You can override the config path for each stage using `--scrape-config`, `--clean-config`, and `--preprocess-config`.

Examples:

```bash
python src/pipeline.py --dry-run
python src/pipeline.py --scrape
python src/pipeline.py --clean --clean-config src/02_cleaning/config/cleaning.json
python src/pipeline.py --preprocess --preprocess-config src/03_preprocessing/config/preprocessing.json
```

## Figures

`src/04_analysis/make_figures.py` creates the four figures of the paper from the processed data in `data/processed/`:

```bash
python src/04_analysis/make_figures.py
```

The figures are written to `outputs/figures/` as `f01.pdf` to `f04.pdf` (vector graphics with embedded fonts) and collected in `outputs/figures/figures.zip` without subfolders, as requested by the journal. Each figure is also saved as a 300 dpi PNG (`f01.png` to `f04.png`), which is not part of the zip file. Use `--data-dir <path>` to read the processed data from another directory and `--out-dir <path>` to change the output directory.

## Transparency note

The scraping and analysis code in this repository was mostly written manually by the authors with some help from [GitHub Copilot](https://github.com/features/copilot). The repository cleanup and preparation for public release (removal of unused code, documentation updates, and minor refactoring) was to a large part assisted by GitHub Copilot and [Claude Code](https://claude.com/claude-code).

## Scraping and replication limits

The scrapers in this repository were built in 2025 and target specific HTML/CSS structures of each platform at that time. Platform operators may change their UI, class names, or pagination logic at any point, which can break individual scrapers without notice. If a scraper fails unexpectedly, the most likely cause is a site-side UI change requiring selector updates.

Reproduction of the full scraping pipeline also depends on platform access, credentials, and platform-specific anti-bot measures. Pages, layouts, and rate limits can change, so results may vary over time. See `docs/PIPELINE.md` for details.

## Funding

This work was funded by the Swiss National Science Foundation (project no. 206161), by the Digital Society Initiative and by the Departments of Geography and of Informatics at the University of Zurich.

## License

The code in this repository is licensed under the [MIT License](LICENSE). The reference data by swisstopo and the Swiss Federal Statistical Office remain subject to the terms of use of their respective sources.
