import json
import os
from pathlib import Path
import sys
from datetime import datetime
from importlib import import_module

src_root = Path(__file__).resolve().parents[2]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from Scraper import Scraper

# Only for debugging!
# import os
# os.chdir('src/01_data_collection')

import logging

from shared.paths import logs_dir, data_dir

main_log = str(logs_dir() / (datetime.today().strftime('%Y-%m-%d') + "_main.log"))
logging.basicConfig(filename=main_log, level=logging.INFO, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_scraper(platform, run_stamp, plz_counter=0, profile_counter=0, chunk=None, preload=False):
    platform.initialise_platform_credentials()
    filename = str(
        data_dir()
        / (
            run_stamp
            + (("_chunk-" + str(chunk)) if chunk is not None else "")
            + "_"
            + platform.get_filename()
            + ".csv"
        )
    )
    scraper = Scraper(platform, filename, plz_counter, profile_counter)
    if preload:
        scraper.preload_plz_profile_counter(chunk=chunk)
    return scraper

def run_scraper_failsafe(scraper, chunk=None, plz_list=None):
    try:
        logger.info('Started scraper for platform ' + scraper.platform.get_name().value + ' with type ' + scraper.platform.get_type().value)
        # Switch to the platform-specific log file
        handler = logging.FileHandler(str(logs_dir() / (datetime.today().strftime('%Y-%m-%d') + (("_chunk-" + str(chunk)) if chunk != None else "") + "_" + scraper.platform.get_filename() + '.log')))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False
        scraper.run(chunk=chunk, plz_list=plz_list)
        success = True
        # Switch to the main log file
        logger.handlers.clear()
        handler = logging.FileHandler(main_log)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info("Finished scraper run for platform " + scraper.platform.get_name().value + ' with type ' + scraper.platform.get_type().value)
    except Exception as e:
        success = False
        scraper.logger.exception("Scraper run for platform " + scraper.platform.get_name().value + " failed at PLZ " + str(scraper.get_plz_counter()) + " and profile # " + str(scraper.get_profile_counter()))
    scraper.write_results_to_json(success, chunk)

def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_platform(platform_path: str, logger: logging.Logger):
    module_name, class_name = platform_path.rsplit(".", 1)
    module = import_module(module_name)
    platform_class = getattr(module, class_name)
    return platform_class(logger=logger)


if __name__ == '__main__':
    logger.info('Started')

    config_arg = "../config/scrapers.json"
    if "--config" in sys.argv:
        config_index = sys.argv.index("--config")
        if config_index + 1 < len(sys.argv):
            config_arg = sys.argv[config_index + 1]
        else:
            raise ValueError("--config flag requires a path argument")
    config_path = Path(__file__).resolve().parent / config_arg
    config = load_config(config_path)

    platforms = config.get("platforms", [])
    if not platforms:
        raise ValueError("No platforms configured in scrapers.json")

    chunk = config.get("chunk")
    preload = config.get("preload", False)
    plz_filter = config.get("plz_filter", "")
    plz_list = config.get("plz_list")
    dry_run = "--dry-run" in sys.argv

    logger.info(f'Chunk: {chunk}')
    logger.info(f'Preload: {preload}')
    logger.info(f'PLZ filter: {plz_filter}')

    if plz_list is not None and not isinstance(plz_list, list):
        raise ValueError("plz_list must be null or a list of PLZ integers")

    if dry_run:
        print("Dry run: no scraping executed.")
        print(f"Platforms: {platforms}")
        print(f"Chunk: {chunk}")
        print(f"Preload: {preload}")
        print(f"PLZ filter: {plz_filter}")
        print(f"PLZ list: {plz_list}")
        sys.exit(0)

    run_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    for platform_path in platforms:
        platform = resolve_platform(platform_path, logger)
        if plz_filter == "with" and not platform.is_plz_search_required():
            continue
        if plz_filter == "without" and platform.is_plz_search_required():
            continue

        scraper = create_scraper(platform, run_stamp, 0, 0, chunk=chunk, preload=preload)
        run_scraper_failsafe(scraper, chunk, plz_list=plz_list)

    logger.info('Finished')