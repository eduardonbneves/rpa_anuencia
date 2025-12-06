import logging
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


def close_webdriver(web_driver: Optional[WebDriver]) -> None:
    if web_driver is None:
        logger.debug("WebDriver instance is None")
        return

    if isinstance(web_driver, WebDriver) is False:
        raise TypeError(
            f"Expected driver to be an instance of selenium WebDriver, but got: {type(web_driver).__name__}"
        )

    logger.debug(f"Closing WebDriver instance: {type(web_driver).__name__}")
    web_driver.quit()
