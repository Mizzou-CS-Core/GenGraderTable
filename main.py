from canvas_lms_api import init as initialize_canvas_client
from mucs_database.init import initialize_database
from colorlog import ColoredFormatter
import os
import logging

from gen_grader_table.grader_table import Config, generate_all_rosters, prepare_toml
import tomlkit


def setup_logging():
    handler = logging.StreamHandler()
    # this format string lets colorlog insert color around the whole line
    fmt = "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
    handler.setFormatter(ColoredFormatter(fmt, log_colors=colors))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


logger = logging.getLogger(__name__)


def load_config() -> Config:
    with open("gen_grader_table.toml", 'r') as f:
        content = f.read()
    logger.info("Loaded configuration into memory")
    doc = tomlkit.parse(content)

    # Extract values from the TOML document
    gen = doc.get('general', {})
    canvas = doc.get('canvas', {})
    paths = doc.get('paths', {})
    return Config(mucsv2_instance_code=gen.get("mucsv2_instance_code"), db_path=paths.get("db_path"),
                  canvas_token=canvas.get("canvas_token"), course_id=canvas.get("canvas_course_id"),
                  canvas_url_base=canvas.get("canvas_url_base"),
                  roster_invalidation_days=gen.get("roster_invalidation_days"))


def main():
    if not os.path.exists("gen_grader_table.toml"):
        prepare_toml()
        logger.warning("Generating default TOML for the first time!")
        exit()
    config = load_config()
    initialize_canvas_client(url_base=config.canvas_url_base, token=config.canvas_token)
    logger.info(f"Canvas client initalized")
    initialize_database(sqlite_db_path=config.db_path, mucsv2_instance_code=config.mucsv2_instance_code)
    logger.info(f"DB initalized")
    generate_all_rosters(course_id=config.course_id)


if __name__ == "__main__":
    setup_logging()
    main()
