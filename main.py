import logging
import os
from pathlib import Path
import base64
import re
import sys

import requests
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
from modules.cra.cra_verificar_se_existe_aba_autorizacao import cra_verificar_se_existe_aba_autorizacao
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
CRA_TIMEOUT_DEFAULT = int(os.environ["CRA_TIMEOUT_DEFAULT"])
CRA_USERNAME = os.environ["CRA_USERNAME"]
CRA_PASSWORD = os.environ["CRA_PASSWORD"]
CRA_LOGIN_PAGE_URL = os.environ["CRA_LOGIN_PAGE_URL"]

CRA_API_BASE_URL = os.environ["CRA_API_BASE_URL"]
CRA_API_TITULO_ENDPOINT = os.environ["CRA_API_TITULO_ENDPOINT"]

WEB_DRIVER_HEADLESS: bool = os.environ["WEB_DRIVER_HEADLESS"].lower() == "true"

OUTPUT_DIR = os.environ["OUTPUT_DIR"]
output_dir = Path(os.path.join(OUTPUT_DIR, Path(__file__).stem))
output_dir.mkdir(parents=True, exist_ok=True)
output_dir__str = output_dir.as_posix()

FLUXO_CRA = "FLUXO CRA"
FLUXO_GAE = "FLUXO GAE"

cdas = [
    "090835/25",
    "050641/22",
    "092897/25",
    "049293/25",
    "123447/19",
    "509920/19",
    "117969/25",
]


def consulta_cra_descricao_ocorrencia_titulo():
    with log_context(color=Color.BLUE, prefix__list=[FLUXO_CRA]):
        credenciais = f"{CRA_USERNAME}:{CRA_PASSWORD}"
        credenciais_b64 = base64.b64encode(credenciais.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {credenciais_b64}",
            "Accept": "application/json",
        }

        url_completa = f"{CRA_API_BASE_URL}{CRA_API_TITULO_ENDPOINT}"

        cdas_protestadas_ou_protestadas_por_edital = []

        for cda in cdas:
            parametros = {"numeroTitulo": cda}

            logger.debug(f"Consultando título: {cda}...")

            try:
                response = requests.get(url_completa, headers=headers, params=parametros)

                response_json = response.json()

                if response.status_code == 200:

                    titulos = response_json.get('_embedded', {}).get('titulo', [])

                    if titulos:
                        titulo_atual = titulos[0]

                        lista_retornos = titulo_atual.get('retornos', [])

                        if lista_retornos:
                            ultimo_retorno = lista_retornos[-1]

                            descricao = ultimo_retorno.get('ocorrencia', {}).get('descricao')

                            logger.debug(f"Última Ocorrência: {descricao}")

                            if descricao in ["Protestado", "Protesto por edital"]:
                                numero_titulo = titulo_atual.get('numeroTitulo')
                                nosso_numero = titulo_atual.get('nossoNumero', '')

                                renavam = "NAO_ENCONTRADO"

                                match = re.search(r'RENA(\d+)', nosso_numero)
                                if match:
                                    renavam = match.group(1)
                                else:
                                    renavam = "".join(filter(str.isdigit, nosso_numero))

                                dados_titulo = {
                                    'numero_titulo': numero_titulo,
                                    'nosso_numero': renavam,
                                }

                                cdas_protestadas_ou_protestadas_por_edital.append(dados_titulo)
                        else:
                            logger.debug("Lista de retornos vazia.")

                    else:
                        logger.debug("Nenhum título encontrado")

                elif response.status_code == 401:
                    logger.debug("Falha na autenticação. Verifique usuário e senha da API.")
                    sys.exit("Encerrando por falha de autenticação.")

                elif response.status_code == 404:
                    logger.debug(f"Endpoint não encontrado (404). URL: {url_completa}")
                    sys.exit("Encerrando por falha de endpoint.")

                else:
                    logger.debug(f"Erro HTTP inesperado: {response.status_code}. Detalhes: {response.text}")
                    raise Exception(f"Erro HTTP inesperado: {response.status_code}")

            except Exception:
                logger.error(f"Erro ao consultar título {cda}: {response}")

        logger.debug(f"CDAs protestadas ou protestadas por edital: {cdas_protestadas_ou_protestadas_por_edital}")

        verificar_se_existe_aba_autorizacao_cra(cdas_protestadas_ou_protestadas_por_edital)

def verificar_se_existe_aba_autorizacao_cra(cdas_protestadas_ou_protestadas_por_edital: list):
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

            renavams_nao_autorizados = []
            for cda in cdas_protestadas_ou_protestadas_por_edital:
                cda_numero = cda['numero_titulo']
                with log_context(prefix__list=[FLUXO_CRA, cda_numero]):
                    logger.debug(f"Iniciando verificação da CDA: {cda_numero}")
                    try:
                        aba_autorizacao = cra_verificar_se_existe_aba_autorizacao(
                            web_driver=web_driver,
                            cda=cda_numero,
                            timeout=CRA_TIMEOUT_DEFAULT,
                        )

                        if not aba_autorizacao:
                            logger.info(
                                f"A CDA {cda_numero} ainda não está com autorização."
                            )
                            renavam = cda['nosso_numero']

                            dados_titulo = {
                                    'cda_numero': cda_numero,
                                    'renavam': renavam,
                            }

                            renavams_nao_autorizados.append(dados_titulo)

                    except Exception as e:
                        with log_context(color=Color.YELLOW, prefix__list=[FLUXO_GAE]):
                            logger.error(f"FALHOU: 'CDA = {cda_numero}'")
                            logger.exception(f"{e.__class__.__name__}: {e}")
                            save_screenshot(
                                web_driver=web_driver,
                                file_name=f"CDA_CRA_ERROR.png",
                                output_dir=output_dir__str,
                            )
                    except KeyboardInterrupt:
                        logger.info(
                            "KeyboardInterrupt: Execução interrompida pelo usuário"
                        )
                        web_driver = None
                        raise

            logger.info(f"Renavams ainda não autorizados: {renavams_nao_autorizados}")

        except Exception as e:
            with log_context(color=Color.YELLOW, prefix__list=[FLUXO_CRA]):
                logger.exception(f"{e.__class__.__name__}: {e}")
                save_screenshot(
                    web_driver=web_driver,
                    file_name="CRA_ERROR.png",
                    output_dir=output_dir__str,
                )
                raise
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: Execução interrompida pelo usuário")
            web_driver = None
            raise
        finally:
            close_webdriver(web_driver=web_driver)

    if renavams_nao_autorizados:
        fluxo_gae(renavams_nao_autorizados)
    else:
        logger.info("Nenhum renavam pendente para o GAE.")

def fluxo_gae(renavams_nao_autorizados: list):
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

            logger.debug(f"Iniciando processamento de {len(renavams_nao_autorizados)} Renavams.")

            renavams_liquidados = []
            for renavam in renavams_nao_autorizados:
                renavam_numero = renavam['renavam']
                with log_context(prefix__list=[FLUXO_GAE, renavam_numero]):
                    logger.debug(f"Iniciando verificação do Renavam: {renavam_numero}")
                    try:
                        web_driver.get(GAE_DEBITO_CONTA_CORRENTE_URL)

                        situacao_debito = gae_verificar_cda_liquidada_por_renavam(
                            web_driver=web_driver,
                            renavam=renavam_numero,
                            timeout=GAE_TIMEOUT_DEFAULT,
                        )

                        if situacao_debito == "LIQUIDADO":
                            logger.info(
                                f"O Renavam {renavam_numero} está com débito liquidado."
                            )

                            cda = renavam['cda_numero']

                            dados_titulo = {
                                'cda_numero': cda,
                                'renavam': renavam_numero,
                            }

                            renavams_liquidados.append(dados_titulo)

                    except Exception as e:
                        with log_context(color=Color.YELLOW, prefix__list=[FLUXO_GAE]):
                            logger.error(f"FALHOU: 'renavam = {renavam_numero}'")
                            logger.exception(f"{e.__class__.__name__}: {e}")
                            save_screenshot(
                                web_driver=web_driver,
                                file_name=f"{renavam_numero}_RENAVAM_GAE_ERROR.png",
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

if __name__ == "__main__":
    consulta_cra_descricao_ocorrencia_titulo()
