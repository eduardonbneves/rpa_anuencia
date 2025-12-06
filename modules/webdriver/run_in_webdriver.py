import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


def pretty_print_condition(condition: object) -> str:
    qual = getattr(condition, "__qualname__", "")
    if "<locals>" in qual:
        name = qual.split(".")[0]
    else:
        name = qual or condition.__class__.__name__

    def extract_raw(val: object) -> str:
        if isinstance(val, str):
            return val.strip("\n")
        if isinstance(val, tuple) and len(val) == 2 and isinstance(val[1], str):
            return val[1].strip("\n")
        return str(val)

    lines = [name]

    try:
        attrs = vars(condition)
    except TypeError:
        attrs = {}

    for value in attrs.values():
        raw = extract_raw(value)
        if raw:
            lines.append(raw)

    closure = getattr(condition, "__closure__", None)
    if closure:
        for cell in closure:
            try:
                raw = extract_raw(cell.cell_contents)
            except Exception:
                raw = "<unrepr>"
            if raw:
                lines.append(raw)

    return "\n".join(lines)


@dataclass
class DtoRunInWebDriverOutput:
    web_element: WebElement
    frame_to_switch: Optional[list[tuple[str, str]]]


@dataclass
class AlternateCondition:
    condition: Callable[[WebDriver], WebElement]
    timeout: int
    exception_to_raise: Exception | None = None
    frame_to_switch: list[tuple[str, str]] | None = None
    webdriver_action: Callable[[WebElement], None] | None = None


def run_in_webdriver(
    web_driver: WebDriver, condition__list: list[AlternateCondition]
) -> DtoRunInWebDriverOutput:
    if not isinstance(condition__list, list) or not condition__list:
        raise ValueError(
            "condition__list must be a non-empty list of AlternateCondition"
        )

    for index, spec in enumerate(condition__list):
        if not isinstance(spec.timeout, int) or spec.timeout <= 0:
            raise ValueError(
                f"condition__list[{index}].timeout must be a positive integer"
            )

        if not callable(spec.condition):
            raise TypeError(f"condition__list[{index}].condition must be callable")

        if spec.webdriver_action is not None and not callable(spec.webdriver_action):
            raise TypeError(
                f"condition__list[{index}].webdriver_action must be callable if provided"
            )

        if spec.frame_to_switch is not None:
            frames = spec.frame_to_switch
            if not (
                isinstance(frames, list)
                and all(isinstance(f, tuple) and len(f) == 2 for f in frames)
            ):
                raise TypeError(
                    f"condition__list[{index}].frame_to_switch must be a list of (By, locator) tuples if provided"
                )

    for index, spec in enumerate(condition__list, start=1):
        timeout = spec.timeout
        web_driver.switch_to.default_content()

        frame_list = spec.frame_to_switch
        if frame_list:
            for frame_locator in frame_list:
                try:
                    WebDriverWait(web_driver, timeout).until(
                        EC.frame_to_be_available_and_switch_to_it(frame_locator)
                    )
                except TimeoutException:
                    break
            else:
                pass

            if (
                frame_list
                and web_driver.switch_to is web_driver.switch_to.default_content
            ):
                continue

        try:
            wait = WebDriverWait(web_driver, timeout)
            element = wait.until(spec.condition)

            if spec.exception_to_raise is not None:
                raise spec.exception_to_raise

            if spec.webdriver_action:
                spec.webdriver_action(element)

            return DtoRunInWebDriverOutput(
                web_element=element, frame_to_switch=frame_list
            )

        except TimeoutException:
            continue

    raise TimeoutException(
        f"No elements found: none of the {len(condition__list)} condition__list matched."
    )
