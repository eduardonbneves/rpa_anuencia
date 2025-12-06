import logging
from selenium.webdriver.remote.webelement import WebElement
from modules.common.DtoWebElementWrapperWithBetterRepr import (
    DtoWebElementWrapperWithBetterRepr,
)

logger = logging.getLogger(__name__)


def type_action(web_element: WebElement, input_value: str) -> None:
    if not isinstance(input_value, str) or not input_value.strip():
        raise ValueError("type_action requires a non-empty string value.")
    web_element.clear()
    web_element.send_keys(input_value)
    logger.info(
        f"Typed '{input_value}' into:\n{DtoWebElementWrapperWithBetterRepr(web_element)}"
    )
