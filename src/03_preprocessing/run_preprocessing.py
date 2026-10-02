import json
import os
import sys
from pathlib import Path

from Platforms_Processor import Platforms_Processor


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    config_arg = "./config/preprocessing.json"
    if "--config" in sys.argv:
        config_index = sys.argv.index("--config")
        if config_index + 1 < len(sys.argv):
            config_arg = sys.argv[config_index + 1]
        else:
            raise ValueError("--config flag requires a path argument")
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)

    config_path = (base_dir / config_arg).resolve()
    config = load_config(config_path)

    dry_run = config.get("dry_run", False)
    if "--dry-run" in sys.argv:
        dry_run = True
    if "--run" in sys.argv:
        dry_run = False
    if dry_run:
        print("Dry run: preprocessing not executed.")
        print("Config:", config)
        return

    processor = Platforms_Processor(
        from_clean_data=config.get("from_clean_data", True),
        gender=config.get("gender", True),
        gender_use_api=config.get("gender_use_api", False),
        location=config.get("location", True),
        location_count=config.get("location_count", True),
        active=config.get("active", True),
    )
    processor.export_clean_data()


if __name__ == "__main__":
    main()
