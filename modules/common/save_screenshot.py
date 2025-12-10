import logging
import os

logger = logging.getLogger(__name__)


def save_screenshot(web_driver, file_name, output_dir):
    raw_path = os.path.join(output_dir, file_name)
    file_path = os.path.normpath(raw_path)
    web_driver.save_screenshot(file_path)
    logger.info(f"Screenshot do erro salvo em: {file_path}")
