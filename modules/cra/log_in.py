import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from modules.webdriver.run_in_webdriver import (
    AlternateCondition,
    run_in_webdriver,
)

from modules.cra.xpath import xpath_cra_logout_button

from modules.webdriver.webelement_action.click_action import click_action
from modules.webdriver.webelement_action.type_action import type_action

logger = logging.getLogger(__name__)


def log_in(
    timeout: int,
    web_driver: WebDriver,
    login_url: str,
    username: str,
    password: str,
    skip_login_form: bool = False,
) -> None:
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("timeout must be a positive integer")
    if not login_url or not isinstance(login_url, str) or not login_url.strip():
        raise ValueError("login URL must be a non-empty string")
    if not username or not password:
        raise ValueError("Missing credentials")

    logger.debug(f"Navigating to: {login_url}")
    web_driver.get(login_url)

    if skip_login_form is False:
        xpath = """
        //input[
            @id='login'
        ]
        """
        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda web_element: type_action(
                        web_element=web_element,
                        input_value=username,
                    ),
                ),
            ],
        )

        xpath = """
        //input[
            @id='senha'
        ]
        """
        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda web_element: type_action(
                        web_element=web_element,
                        input_value=password,
                    ),
                ),
            ],
        )

        xpath = """
        //button[
            @id='confirmar'
        ]
        """
        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda web_element: click_action(
                        web_element=web_element
                    ),
                ),
            ],
        )

    logger.debug("Waiting for login confirmation...")

    run_in_webdriver(
        web_driver=web_driver,
        condition__list=[
            AlternateCondition(
                timeout=timeout,
                condition=EC.presence_of_element_located(
                    (By.XPATH, xpath_cra_logout_button)
                ),
            ),
        ],
    )

    logger.info("CRA login successful.")
