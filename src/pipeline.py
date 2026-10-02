import argparse
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run scraping, cleaning, and preprocessing in sequence.",
    )
    parser.add_argument("--scrape", action="store_true", help="Run scraping stage")
    parser.add_argument("--clean", action="store_true", help="Run cleaning stage")
    parser.add_argument("--preprocess", action="store_true", help="Run preprocessing stage")
    parser.add_argument("--scrape-config", help="Path to scraper config JSON")
    parser.add_argument("--clean-config", help="Path to cleaning config JSON")
    parser.add_argument("--preprocess-config", help="Path to preprocessing config JSON")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry run for stages that support it",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Force run for stages that support it",
    )
    return parser


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n[{label}] {' '.join(command)}")
    result = subprocess.run(command, cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {result.returncode}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run and args.run:
        raise SystemExit("--dry-run and --run cannot be used together")

    repo_root = Path(__file__).resolve().parents[1]
    src_root = Path(__file__).resolve().parent

    selected_any = args.scrape or args.clean or args.preprocess
    run_scrape = args.scrape or not selected_any
    run_clean = args.clean or not selected_any
    run_preprocess = args.preprocess or not selected_any

    scrape_main_path = src_root / "01_data_collection" / "scrapers" / "main.py"
    clean_path = src_root / "02_cleaning" / "run_cleaning.py"
    preprocess_path = src_root / "03_preprocessing" / "run_preprocessing.py"

    default_scrape_config = src_root / "01_data_collection" / "config" / "scrapers.json"
    scrape_config = Path(args.scrape_config).resolve() if args.scrape_config else default_scrape_config
    clean_config = (
        Path(args.clean_config).resolve()
        if args.clean_config
        else src_root / "02_cleaning" / "config" / "cleaning.json"
    )
    preprocess_config = (
        Path(args.preprocess_config).resolve()
        if args.preprocess_config
        else src_root / "03_preprocessing" / "config" / "preprocessing.json"
    )

    if run_scrape:
        scrape_command = [sys.executable, str(scrape_main_path), "--config", str(scrape_config)]
        if args.dry_run:
            scrape_command.append("--dry-run")
        run_step("Scrape", scrape_command, repo_root)

    if run_clean:
        clean_command = [sys.executable, str(clean_path), str(clean_config)]
        if args.dry_run:
            clean_command.append("--dry-run")
        if args.run:
            clean_command.append("--run")
        run_step("Clean", clean_command, repo_root)

    if run_preprocess:
        preprocess_command = [sys.executable, str(preprocess_path), "--config", str(preprocess_config)]
        if args.dry_run:
            preprocess_command.append("--dry-run")
        if args.run:
            preprocess_command.append("--run")
        run_step("Preprocess", preprocess_command, repo_root)


if __name__ == "__main__":
    main()
