import json
import os
import sys
from importlib import import_module
from pathlib import Path


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_cleaner(cleaner_path: str):
    module_name, class_name = cleaner_path.rsplit(".", 1)
    module = import_module(module_name)
    cleaner_class = getattr(module, class_name)
    return cleaner_class()


def main():
    config_arg = sys.argv[1] if len(sys.argv) > 1 else "./config/cleaning.json"
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)

    config_path = (base_dir / config_arg).resolve()
    config = load_config(config_path)

    cleaners = config.get("cleaners", [])
    dry_run = config.get("dry_run", False)
    if "--dry-run" in sys.argv:
        dry_run = True
    if "--run" in sys.argv:
        dry_run = False
    if not cleaners:
        raise ValueError("No cleaners configured in cleaning config.")

    for cleaner_path in cleaners:
        if dry_run:
            print(f"Dry run: would execute {cleaner_path}")
            continue
        cleaner = resolve_cleaner(cleaner_path)
        cleaner.export_clean_data()


if __name__ == "__main__":
    main()
