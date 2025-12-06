import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from modules.common.DtoWebElementWrapperWithBetterRepr import (
    DtoWebElementWrapperWithBetterRepr,
)

logger = logging.getLogger(__name__)


def click_action(web_element: WebElement, open_in_the_same_tab: bool = False) -> None:
    driver: WebDriver = web_element.parent

    if open_in_the_same_tab:
        logger.info(f"webelement:\n{DtoWebElementWrapperWithBetterRepr(web_element)}")
        logger.info(
            f"Removing the target attribute from webelement:\n{DtoWebElementWrapperWithBetterRepr(web_element)}"
        )

        driver.execute_script("arguments[0].removeAttribute('target');", web_element)

        logger.info(f"webelement:\n{DtoWebElementWrapperWithBetterRepr(web_element)}")

    logger.info(f"Clicking:\n{DtoWebElementWrapperWithBetterRepr(web_element)}")
    web_element.click()
