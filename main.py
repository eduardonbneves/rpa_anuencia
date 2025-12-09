import logging
import os
from pathlib import Path
import base64
import json

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
    "050641/22",
    "092897/25",
    "049293/25",
    "123447/19",
    "509920/19",
    "117969/25",
]

def consulta_titulo_cra():
    credenciais = f"{CRA_USERNAME}:{CRA_PASSWORD}"
    credenciais_b64 = base64.b64encode(credenciais.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {credenciais_b64}",
        "Accept": "application/json"
    }
    
    url_completa = f"{CRA_API_BASE_URL}{CRA_API_TITULO_ENDPOINT}"

    for cda in cdas:
        parametros = {
            "numeroTitulo": cda,
            "documentoDevedor": ""
        }


        logger.debug(f"Consultando título: {cda}...")

        try:
            # 2. Requisição HTTP
            response = requests.get(url_completa, headers=headers, params=parametros, timeout=15)
            
            # 3. Tratamento de Erros HTTP
            if response.status_code == 401:
                return {"status": "ERRO_AUTENTICACAO", "mensagem": "Credenciais inválidas."}
            elif response.status_code != 200:
                return {"status": "ERRO_HTTP", "codigo": response.status_code, "mensagem": response.text}

            # 4. Processamento do JSON
            dados_json = response.json()
            titulos_encontrados = dados_json.get('_embedded', {}).get('titulo', [])

            if not titulos_encontrados:
                logger.debug("Título não localizado.")
                return {
                    "status": "NAO_ENCONTRADO", 
                    "mensagem": "Título não retornado na busca.",
                    "seu_numero": cda
                }

            # 5. Extração de Dados (Foca no primeiro título retornado, que é o mais relevante)
            titulo = titulos_encontrados[0]
            
            # Dados básicos
            protocolo = titulo.get('protocolo', 'N/D')
            situacao = titulo.get('situacao', 'N/D')
            nosso_numero = titulo.get('nossoNumero', 'N/D')
            cartorio_nome = titulo.get('cartorio', {}).get('nome', 'N/D')

            # Lógica aprimorada para extrair Ocorrência (combinação dos dois scripts)
            # Prioriza a lista de 'retornos', mas tem fallbacks
            cod_ocorrencia = 'N/D'
            desc_ocorrencia = 'N/D'
            
            retornos = titulo.get('retornos', [])
            
            if retornos and isinstance(retornos, list):
                # Pega do primeiro retorno
                ocorr = retornos[0].get('ocorrencia', {})
                cod_ocorrencia = ocorr.get('codigo', 'N/D')
                desc_ocorrencia = ocorr.get('descricao', 'N/D')
            else:
                # Fallback: Tenta pegar direto da raiz se existir (lógica do main.py)
                ocorr_direta = titulo.get('ocorrencia')
                if isinstance(ocorr_direta, dict):
                    desc_ocorrencia = ocorr_direta.get('descricao', 'N/D')
                elif isinstance(ocorr_direta, str):
                    desc_ocorrencia = ocorr_direta

            # 6. Montagem do Resultado Final
            resultado = {
                "status": "ENCONTRADO",
                "seu_numero": cda,
                "nosso_numero": nosso_numero,
                "protocolo": protocolo,
                "situacao": situacao,
                "ocorrencia": {
                    "codigo": cod_ocorrencia,
                    "descricao": desc_ocorrencia
                },
                "cartorio": cartorio_nome,
                "dados_completos": titulo # Mantém o objeto original caso precise de algo mais
            }

            logger.debug(f"Encontrado! Nosso Número: {nosso_numero} | Situação: {situacao}")
            logger.debug(f"Ocorrência: {desc_ocorrencia} ({cod_ocorrencia})")

            
                # Exemplo de como acessar os dados limpos
            if resultado['status'] == 'ENCONTRADO':
                logger.debug(f"\nResumo para relatório:")
                logger.debug(f"Título: {resultado['seu_numero']}")
                logger.debug(f"Retorno Cartório: {resultado['ocorrencia']['descricao']}")
            else:
                logger.debug(f"\nErro: {resultado['mensagem']}")


        except requests.exceptions.RequestException as e:
            return {"status": "ERRO_CONEXAO", "mensagem": str(e)}
        except Exception as e:
            return {"status": "ERRO_INESPERADO", "mensagem": str(e)}

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
    consulta_titulo_cra()
