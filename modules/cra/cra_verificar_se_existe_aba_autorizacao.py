import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from modules.webdriver.run_in_webdriver import (
    AlternateCondition,
    run_in_webdriver,
)
from modules.webdriver.webelement_action.click_action import click_action
from modules.webdriver.webelement_action.type_action import type_action

logger = logging.getLogger(__name__)


def cra_verificar_se_existe_aba_autorizacao(
    web_driver: WebDriver,
    cda: str,
    timeout: int,
) -> str | None:
    try:
        xpath = "//ul//li//a//span[normalize-space(.)='Consulta']"
        nome_do_elemento = "Menu Consulta"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda el: click_action(web_element=el),
                ),
            ],
        )

        xpath = "//li[@id='ul_8_li_1']//a[normalize-space(.)='Consultar título']"
        nome_do_elemento = "Consultar título"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda el: click_action(web_element=el),
                ),
            ],
        )

        xpath = "//thead//tr//th//input[@id='numeroTitulo']"
        nome_do_elemento = "Campo de Número do Título"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda web_element: type_action(
                        web_element=web_element,
                        input_value=cda,
                    ),
                ),
            ],
        )

        xpath = "//thead//tr//th//button[@type='submit' and @data-original-title='Buscar']"
        nome_do_elemento = "Botão de Pesquisar"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda el: click_action(web_element=el),
                ),
            ],
        )

        xpath = "//tbody//tr//td//a[@data-original-title='Ver']"
        nome_do_elemento = "Botão de Ver Detalhes do Título"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda el: click_action(web_element=el),
                ),
            ],
        )

        xpath = "//ul//li//a[@href='#autorizacao']"
        nome_do_elemento = "Aba Autorização"
        encontrou_aba = False

        try:
            run_in_webdriver(
                web_driver=web_driver,
                condition__list=[
                    AlternateCondition(
                        timeout=timeout,
                        condition=EC.visibility_of_element_located((By.XPATH, xpath)),
                        webdriver_action=lambda el: el,
                    )
                ],
            )

            logger.debug(f"{nome_do_elemento} encontrada.")
            encontrou_aba = True

        except (TimeoutException, Exception):
            logger.debug(f"{nome_do_elemento} não encontrada.")
            encontrou_aba = False

        try:
            xpath = "//button[@id='fechar']"
            nome_do_elemento = "Botão de Fechar Detalhes do Título"

            run_in_webdriver(
                web_driver=web_driver,
                condition__list=[
                    AlternateCondition(
                        timeout=timeout,
                        condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                        webdriver_action=lambda el: click_action(web_element=el),
                    ),
                ],
            )
        except Exception as e:
            logger.warning(f"Não foi possível fechar a janela de detalhes: {e}")

        return encontrou_aba


    except TimeoutException as e:
        msg = f"O elemento '{nome_do_elemento}' não foi encontrado ou não ficou clicável. XPath: {xpath}"
        raise TimeoutException(msg) from e

    except Exception as e:
        msg = f"ERRO DESCONHECIDO em '{nome_do_elemento}': {e}"
        raise Exception(msg) from e
