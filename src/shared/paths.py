import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
COMBINED_DIR = DATA_DIR / "combined"
CLEAN_DIR = DATA_DIR / "clean"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = PROJECT_ROOT / "loggers"
SCRAPER_RUNS_DIR = PROJECT_ROOT / "scraper_runs"

CONFIG_DIR = SRC_ROOT / "shared" / "config"
PATHS_CONFIG = CONFIG_DIR / "paths.json"


def load_paths_config() -> dict:
    if PATHS_CONFIG.exists():
        with PATHS_CONFIG.open("r", encoding="utf-8") as file:
            return json.load(file)
    return {}


def data_dir() -> Path:
    config = load_paths_config()
    return PROJECT_ROOT / config.get("data_dir", "data")


def logs_dir() -> Path:
    config = load_paths_config()
    return PROJECT_ROOT / config.get("logs_dir", "loggers")


def scraper_runs_dir() -> Path:
    config = load_paths_config()
    return PROJECT_ROOT / config.get("scraper_runs_dir", "scraper_runs")


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
