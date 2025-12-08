import logging
import os
from pathlib import Path
from logger import (
    Color,
    configure_logging,
    log_context,
)
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from modules.common.helper_function__temp_browser_profile_dir__path import (
    helper_function__temp_browser_profile_dir__path,
)
from modules.gae.gae_verificar_cda_liquidada_por_renavam import (
    gae_verificar_cda_liquidada_por_renavam,
)
from modules.webdriver.close_webdriver import close_webdriver

from modules.gae.log_in import log_in as gae_log_in
from modules.cra.log_in import log_in as cra_log_in
from modules.webdriver.webdriver_config.set_default_firefox_options import (
    set_default_firefox_options,
)
from modules.common.save_screenshot import save_screenshot

load_dotenv()
logger = logging.getLogger(__name__)
configure_logging()

GAE_TIMEOUT_AUTH = int(os.environ["GAE_TIMEOUT_AUTH"])
GAE_TIMEOUT_DEFAULT = int(os.environ["GAE_TIMEOUT_DEFAULT"])
GAE_USERNAME = os.environ["GAE_USERNAME"]
GAE_PASSWORD = os.environ["GAE_PASSWORD"]
SEFAZ_SSO_LOGIN_PAGE_URL = os.environ["SEFAZ_SSO_LOGIN_PAGE_URL"]
GAE_DEBITO_CONTA_CORRENTE_URL = os.environ["GAE_DEBITO_CONTA_CORRENTE_URL"]

CRA_TIMEOUT_AUTH = int(os.environ["CRA_TIMEOUT_AUTH"])
CRA_USERNAME = os.environ["CRA_USERNAME"]
CRA_PASSWORD = os.environ["CRA_PASSWORD"]
CRA_LOGIN_PAGE_URL = os.environ["CRA_LOGIN_PAGE_URL"]

WEB_DRIVER_HEADLESS: bool = os.environ["WEB_DRIVER_HEADLESS"].lower() == "true"

OUTPUT_DIR = os.environ["OUTPUT_DIR"]
output_dir = Path(os.path.join(OUTPUT_DIR, Path(__file__).stem))
output_dir.mkdir(parents=True, exist_ok=True)
output_dir__str = output_dir.as_posix()

FLUXO_CRA = "FLUXO CRA"
FLUXO_GAE = "FLUXO GAE"

LISTA_RENAVAMS = [
    "150056400",   # Renavam liquidado com uma linha
    "12345678901", # Renavam inválido
    "1213839626",  # Não liquidado com mais de uma linha
    "1151519771",  # Liquidado com várias linhas
]


def executar_teste():
    with log_context(color=Color.GREEN, prefix__list=[FLUXO_GAE]):
        web_driver = None
        try:
            temp_browser_profile_output_dir = (
                helper_function__temp_browser_profile_dir__path()
            )
            firefox_options = set_default_firefox_options(
                headless=WEB_DRIVER_HEADLESS,
                firefox_options=FirefoxOptions(),
                browser_profile_output_dir=temp_browser_profile_output_dir,
            )
            web_driver = webdriver.Firefox(options=firefox_options)

            gae_log_in(
                timeout=GAE_TIMEOUT_AUTH,
                web_driver=web_driver,
                login_url=SEFAZ_SSO_LOGIN_PAGE_URL,
                username=GAE_USERNAME,
                password=GAE_PASSWORD,
            )

            logger.debug(f"Iniciando processamento de {len(LISTA_RENAVAMS)} Renavams.")

            renavams_liquidados = []
            for renavam in LISTA_RENAVAMS:
                with log_context(prefix__list=[FLUXO_GAE, renavam]):
                    logger.debug(f"Iniciando verificação do Renavam: {renavam}")
                    try:
                        web_driver.get(GAE_DEBITO_CONTA_CORRENTE_URL)

                        situacao_debito = gae_verificar_cda_liquidada_por_renavam(
                            web_driver=web_driver,
                            renavam=renavam,
                            timeout=GAE_TIMEOUT_DEFAULT,
                        )

                        if situacao_debito == "LIQUIDADO":
                            logger.info(
                                f"O Renavam {renavam} está com débito liquidado."
                            )
                            renavams_liquidados.append(renavam)

                    except Exception as e:
                        with log_context(color=Color.YELLOW, prefix__list=[FLUXO_GAE]):
                            logger.error(f"FALHOU: 'renavam = {renavam}'")
                            logger.exception(f"{e.__class__.__name__}: {e}")
                            save_screenshot(
                                web_driver=web_driver,
                                file_name=f"{renavam}_RENAVAM_GAE_ERROR.png",
                                output_dir=output_dir__str,
                            )
                    except KeyboardInterrupt:
                        logger.info(
                            "KeyboardInterrupt: Execução interrompida pelo usuário"
                        )
                        web_driver = None
                        raise

            logger.info(f"Renavams com débito liquidado: {renavams_liquidados}")

        except Exception:
            raise
        finally:
            close_webdriver(web_driver=web_driver)

def executar_teste2():
    with log_context(color=Color.BLUE, prefix__list=[FLUXO_CRA]):
        web_driver = None
        try:
            temp_browser_profile_output_dir = (
                helper_function__temp_browser_profile_dir__path()
            )
            firefox_options = set_default_firefox_options(
                headless=WEB_DRIVER_HEADLESS,
                firefox_options=FirefoxOptions(),
                browser_profile_output_dir=temp_browser_profile_output_dir,
            )
            web_driver = webdriver.Firefox(options=firefox_options)

            cra_log_in(
                timeout=CRA_TIMEOUT_AUTH,
                web_driver=web_driver,
                login_url=CRA_LOGIN_PAGE_URL,
                username=CRA_USERNAME,
                password=CRA_PASSWORD,
            )

        except Exception as e:
             with log_context(color=Color.YELLOW, prefix__list=[FLUXO_CRA]):
                logger.exception(f"{e.__class__.__name__}: {e}")
                save_screenshot(
                    web_driver=web_driver,
                    file_name="LOGIN_CRA_ERROR.png",
                    output_dir=output_dir__str,
                )
                raise
        except KeyboardInterrupt:
                logger.info(
                    "KeyboardInterrupt: Execução interrompida pelo usuário"
                )
                web_driver = None
                raise
        finally:
            close_webdriver(web_driver=web_driver)

if __name__ == "__main__":
    executar_teste()
