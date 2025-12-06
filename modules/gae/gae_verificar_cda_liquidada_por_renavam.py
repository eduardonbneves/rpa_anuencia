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


def gae_verificar_cda_liquidada_por_renavam(
    web_driver: WebDriver,
    renavam: str,
    timeout: int,
) -> str | None:
    try:
        xpath = "//select[@name='tpContribuinte']//option[text()='RENAVAM']"
        nome_do_elemento = "Opção de Tipo de Contribuinte"

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

        xpath = "//input[@id='codContribuinteFormatada']"
        nome_do_elemento = "Campo de Renavam"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.element_to_be_clickable((By.XPATH, xpath)),
                    webdriver_action=lambda web_element: type_action(
                        web_element=web_element,
                        input_value=renavam,
                    ),
                ),
            ],
        )

        xpath = "//select[@name='tpDocOrigem']//option[text()='20 - Dívida Ativa']"
        nome_do_elemento = "Opção do Tipo do Documento de Origem"

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

        xpath = "//select[@name='anoInicial']//option[text()='2010']"
        nome_do_elemento = "Ano Inicial"

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

        xpath = "//input[@id='search']"
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

        xpath = "//a[text()='Situação']"
        nome_do_elemento = "Link de Situação da Débito"

        run_in_webdriver(
            web_driver=web_driver,
            condition__list=[
                AlternateCondition(
                    timeout=timeout,
                    condition=EC.visibility_of_element_located((By.XPATH, xpath)),
                    webdriver_action=lambda el: el,
                ),
            ],
        )

        xpath = "//table[@id='item']"
        linhas = web_driver.find_elements(By.XPATH, f"{xpath}/tbody/tr")
        qtd_linhas = len(linhas)

        if qtd_linhas != 1:
            logger.debug(
                f"Renavam: {renavam} - A tabela não possui exatamente uma linha. Ignorando extração."
            )
            return None

        xpath = "//table[@id='item']/tbody/tr[1]/td[12]"

        situacao_debito_element = web_driver.find_element(By.XPATH, xpath)
        situacao_debito = situacao_debito_element.text.strip()

        return situacao_debito

    except TimeoutException as e:
        msg = f"O elemento '{nome_do_elemento}' não foi encontrado ou não ficou clicável. XPath: {xpath}"
        raise TimeoutException(msg) from e

    except Exception as e:
        msg = f"ERRO DESCONHECIDO em '{nome_do_elemento}': {e}"
        raise Exception(msg) from e
