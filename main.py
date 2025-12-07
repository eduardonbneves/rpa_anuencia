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
from modules.webdriver.webdriver_config.set_default_firefox_options import (
    set_default_firefox_options,
)
from modules.common.save_screenshot import save_screenshot

# Configure logging initially (can be re-configured if needed)
logger = logging.getLogger(__name__)
# configure_logging() # Move this call or ensure it doesn't conflict

FLUXO_GAE = "FLUXO GAE"

DEFAULT_LISTA_RENAVAMS = [
    "150056400",   # Renavam liquidado com uma linha
    "12345678901", # Renavam inválido
    "1213839626",  # Não liquidado com mais de uma linha
    "1151519771",  # Liquidado com várias linhas
]


def load_settings():
    """Load settings from environment variables."""
    # load_dotenv() # Assumes load_dotenv is called before or env is set
    return {
        "GAE_TIMEOUT_AUTH": int(os.environ.get("GAE_TIMEOUT_AUTH", "30")),
        "GAE_TIMEOUT_DEFAULT": int(os.environ.get("GAE_TIMEOUT_DEFAULT", "30")),
        "GAE_USERNAME": os.environ.get("GAE_USERNAME"),
        "GAE_PASSWORD": os.environ.get("GAE_PASSWORD"),
        "SEFAZ_SSO_LOGIN_PAGE_URL": os.environ.get("SEFAZ_SSO_LOGIN_PAGE_URL"),
        "GAE_DEBITO_CONTA_CORRENTE_URL": os.environ.get("GAE_DEBITO_CONTA_CORRENTE_URL"),
        "WEB_DRIVER_HEADLESS": os.environ.get("WEB_DRIVER_HEADLESS", "false").lower() == "true",
        "OUTPUT_DIR": os.environ.get("OUTPUT_DIR", "output"),
    }


def executar_teste(lista_renavams=None, stop_event=None):
    if lista_renavams is None:
        lista_renavams = DEFAULT_LISTA_RENAVAMS
    
    configure_logging() # Ensure logging is configured
    
    settings = load_settings()
    
    # Check for missing critical settings
    missing = [k for k, v in settings.items() if v is None and k != "OUTPUT_DIR"] # Check criticals
    if missing:
        logger.error(f"Faltam variáveis de ambiente: {missing}")
        return []

    OUTPUT_DIR = settings["OUTPUT_DIR"]
    output_dir = Path(os.path.join(OUTPUT_DIR, Path(__file__).stem))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir__str = output_dir.as_posix()
    
    web_driver = None
    renavams_liquidados = []

    with log_context(color=Color.GREEN, prefix__list=[FLUXO_GAE]):
        try:
            temp_browser_profile_output_dir = (
                helper_function__temp_browser_profile_dir__path()
            )
            firefox_options = set_default_firefox_options(
                headless=settings["WEB_DRIVER_HEADLESS"],
                firefox_options=FirefoxOptions(),
                browser_profile_output_dir=temp_browser_profile_output_dir,
            )
            web_driver = webdriver.Firefox(options=firefox_options)

            gae_log_in(
                timeout=settings["GAE_TIMEOUT_AUTH"],
                web_driver=web_driver,
                login_url=settings["SEFAZ_SSO_LOGIN_PAGE_URL"],
                username=settings["GAE_USERNAME"],
                password=settings["GAE_PASSWORD"],
            )

            logger.debug(f"Iniciando processamento de {len(lista_renavams)} Renavams.")

            for renavam in lista_renavams:
                if stop_event and stop_event.is_set():
                    logger.info("Execução interrompida pelo usuário.")
                    break

                with log_context(prefix__list=[FLUXO_GAE, renavam]):
                    logger.debug(f"Iniciando verificação do Renavam: {renavam}")
                    try:
                        web_driver.get(settings["GAE_DEBITO_CONTA_CORRENTE_URL"])

                        situacao_debito = gae_verificar_cda_liquidada_por_renavam(
                            web_driver=web_driver,
                            renavam=renavam,
                            timeout=settings["GAE_TIMEOUT_DEFAULT"],
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
                                file_name=f"{renavam}_RENAVAM_GAE_ERROR_.png",
                                output_dir=output_dir__str,
                            )
                    except KeyboardInterrupt:
                        logger.info(
                            "KeyboardInterrupt: Execução interrompida pelo usuário"
                        )
                        raise # Re-raise if running from CLI, or handle if GUI

            logger.info(f"Renavams com débito liquidado: {renavams_liquidados}")
            return renavams_liquidados

        except Exception as e:
            logger.exception(f"Erro fatal na execução: {e}")
            raise
        finally:
            close_webdriver(web_driver=web_driver)


if __name__ == "__main__":
    load_dotenv()
    executar_teste()
