import requests
import base64
import json
from typing import Dict, Any, List

# --- Configurações da API ---
# ATENÇÃO: Por segurança, senhas e credenciais reais não devem ficar no código-fonte.
# Considere usar variáveis de ambiente ou um arquivo de configuração.
URL_BASE = "http://craam.api.crabr.com.br"
ENDPOINT = "/titulo"
USUARIO_API = "59226900272"
SENHA_API = "Barbara1$#"


def consultar_titulo_cra21(num_titulo: str, doc_devedor: str = "") -> Dict[str, Any]:
    """
    Consulta o status de um título na CRA21 API utilizando o número do título e o documento do devedor.

    Args:
        num_titulo: O número do título (NumeroTitulo) para consulta.
        doc_devedor: O CPF/CNPJ do devedor (DocumentoDevedor). Padrão: "" (vazio).

    Returns:
        Um dicionário contendo o resultado JSON da consulta ou uma mensagem de erro.
    """

    # 1. Autenticação: Codifica usuário e senha em Base64 (HTTP Basic Authentication)
    credenciais = f"{USUARIO_API}:{SENHA_API}"
    # Codifica em bytes, depois aplica Base64, e decodifica para string novamente
    credenciais_b64 = base64.b64encode(credenciais.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {credenciais_b64}",
        "Accept": "application/json",
    }

    # 2. Montagem da URL com os parâmetros de consulta (Query String)
    url_completa = f"{URL_BASE}{ENDPOINT}"

    parametros = {"numeroTitulo": num_titulo, "documentoDevedor": doc_devedor}

    try:
        # 3. Execução da requisição GET
        response = requests.get(
            url_completa, headers=headers, params=parametros, timeout=15
        )

        # 4. Tratamento dos Códigos de Status HTTP
        if response.status_code == 200:
            return response.json()

        elif response.status_code == 401:
            return {
                "status": "ERRO_AUTENTICACAO",
                "mensagem": "Falha na autenticação. Verifique USUARIO_API e SENHA_API.",
            }

        # 404 pode ocorrer se o endpoint ou o recurso (título) não for encontrado.
        # Vamos tratar 404 como "Não Encontrado" no bloco subsequente.

        else:
            # Captura outros erros HTTP (e.g., 500 Server Error)
            return {
                "status": "ERRO_HTTP",
                "codigo": response.status_code,
                "mensagem": f"Erro HTTP inesperado: {response.status_code}. Detalhes: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        return {
            "status": "ERRO_CONEXAO",
            "mensagem": f"Falha na conexão com a API: {e}",
        }


def consultar_status_titulo(
    seu_numero: str, doc_devedor: str = "", verbose: bool = True
) -> Dict[str, Any]:
    """
    Consulta o status de um título usando o "SEU NUMERO" e retorna informações resumidas,
    incluindo 'nossoNumero' e a 'ocorrencia' do primeiro retorno.
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"CONSULTANDO TÍTULO: {seu_numero}")
        print(f"{'=' * 80}")

    # Consulta na API
    resultado = consultar_titulo_cra21(num_titulo=seu_numero, doc_devedor=doc_devedor)

    # Processa a resposta
    if "status" in resultado and "ERRO" in resultado["status"]:
        if verbose:
            print(f"Erro na consulta: {resultado['mensagem']}\n")
        return {
            "seu_numero": seu_numero,
            "status": "ERRO",
            "mensagem": resultado["mensagem"],
        }

    # Verifica se encontrou títulos (a chave é _embedded -> titulo)
    titulos: List[Dict[str, Any]] = resultado.get("_embedded", {}).get("titulo", [])

    if not titulos:
        if verbose:
            print("Título não localizado na base da CRA21\n")
        return {
            "seu_numero": seu_numero,
            "status": "NAO_ENCONTRADO",
            "mensagem": "Título não localizado na base da CRA21",
        }

    # Pega o primeiro título encontrado (o mais relevante)
    titulo = titulos[0]

    # --- 1. Extrai informações principais e o 'nossoNumero' (NOVA EXTRAÇÃO) ---
    protocolo = titulo.get("protocolo", "N/D")
    situacao = titulo.get("situacao", "N/D")
    nosso_numero = titulo.get("nossoNumero", "N/D")

    # --- 2. Extrai a ocorrência do primeiro retorno (EXTRAÇÃO AJUSTADA) ---
    retornos = titulo.get("retornos", [])

    codigo_ocorrencia = "N/D"
    descricao_ocorrencia = "N/D"

    if retornos and isinstance(retornos, list) and len(retornos) > 0:
        # Ocorrência está dentro do primeiro item da lista 'retornos'
        primeiro_retorno = retornos[0]
        ocorrencia_info = primeiro_retorno.get("ocorrencia", {})

        # Extrai o código e a descrição solicitados
        codigo_ocorrencia = ocorrencia_info.get("codigo", "N/D")
        descricao_ocorrencia = ocorrencia_info.get("descricao", "N/D")

    # Extrai informações do cartório
    cartorio_info = titulo.get("cartorio", {})
    cartorio_nome = (
        cartorio_info.get("nome", "N/D") if isinstance(cartorio_info, dict) else "N/D"
    )

    # Monta resultado estruturado
    resultado_formatado = {
        "seu_numero": seu_numero,
        "status": "ENCONTRADO",
        "protocolo": protocolo,
        "situacao": situacao,
        # NOVAS INFORMAÇÕES SOLICITADAS
        "nosso_numero": nosso_numero,
        "ocorrencia_codigo": codigo_ocorrencia,
        "ocorrencia_descricao": descricao_ocorrencia,
        "cartorio": cartorio_nome,
        "dados_completos": titulo,  # Mantém dados completos
    }

    # Exibe resultado formatado se verbose=True
    if verbose:
        print("\nTÍTULO ENCONTRADO")
        print(f"   Número do Título (Seu): {seu_numero}")
        print(f"   Nosso Número (API): {nosso_numero}")  # Adicionado
        print(f"   Protocolo: {protocolo}")
        print(f"   Situação Geral: {situacao}")
        print(f"   Código Ocorrência: {codigo_ocorrencia}")  # Adicionado
        print(f"   Descrição Ocorrência: {descricao_ocorrencia}")  # Adicionado
        print(f"   Cartório: {cartorio_nome}")
        print(f"{'=' * 80}\n")

    return resultado_formatado


def processar_carteira_json(arquivo_json: str) -> List[Dict[str, Any]]:
    """
    Lê o arquivo JSON da carteira e consulta cada título na API.
    """
    resultados = []

    try:
        # Lê o arquivo JSON
        with open(arquivo_json, "r", encoding="utf-8") as f:
            titulos = json.load(f)

        print(f"\n{'=' * 80}")
        print(f"PROCESSAMENTO EM LOTE - {arquivo_json.upper()}")
        print(f"{'=' * 80}")
        print(f"Total de títulos no arquivo: {len(titulos)}\n")

        # Itera sobre cada título e consulta na API
        for idx, item in enumerate(titulos, 1):
            seu_numero = item.get("SEU NUMERO", "")
            valor_titulo = item.get("VALOR DO TITULO", 0)

            if not seu_numero:
                print(f"[{idx}]Título sem 'SEU NUMERO', pulando...")
                continue

            print(
                f"[{idx}/{len(titulos)}] Consultando: {seu_numero} (R$ {valor_titulo:.2f})"
            )

            # Consulta na API (verbose=False para não poluir output em lote)
            resultado = consultar_status_titulo(seu_numero, verbose=False)

            # Adiciona o valor do título ao resultado
            resultado["valor_titulo"] = valor_titulo
            resultados.append(resultado)

            # Exibe resumo
            if resultado["status"] == "ENCONTRADO":
                # Usa a nova chave 'ocorrencia_descricao'
                print(
                    f"{resultado['ocorrencia_descricao']} ({resultado['ocorrencia_codigo']}) | Nosso Número: {resultado['nosso_numero']}"
                )
            elif resultado["status"] == "NAO_ENCONTRADO":
                print(" Não encontrado")
            else:
                print(f"Erro: {resultado['mensagem']}")

            print("-" * 80)

        # Resumo final
        print(f"\n{'=' * 80}")
        print("RESUMO DO PROCESSAMENTO")
        print(f"{'=' * 80}")
        print(f"Total processado: {len(resultados)}")

        encontrados = sum(1 for r in resultados if r["status"] == "ENCONTRADO")
        nao_encontrados = sum(1 for r in resultados if r["status"] == "NAO_ENCONTRADO")
        erros = sum(1 for r in resultados if r["status"] == "ERRO")

        print(f"Encontrados: {encontrados}")
        print(f"Não encontrados: {nao_encontrados}")
        print(f"Erros: {erros}")

        return resultados

    except FileNotFoundError:
        print(f"Arquivo não encontrado: {arquivo_json}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return []


# --- Exemplos de Uso ---
if __name__ == "__main__":
    print("=" * 80)
    print("SCRIPT DE CONSULTA DE TÍTULOS - CRA21 API")
    print("=" * 80)

    # ==================================================
    # EXEMPLO 1: Consulta Individual (Use um número de teste real se possível)
    # ==================================================
    """
    print("\n### EXEMPLO 1: Consulta Individual ###")
    
    # Usando o número do título do JSON de exemplo que você forneceu
    resultado = consultar_status_titulo("092897/25") 
    
    # Acessando os dados retornados (agora com as novas chaves)
    if resultado['status'] == 'ENCONTRADO':
        print(f"\nRESULTADO DETALHADO:")
        print(f"   Status: {resultado['status']}")
        print(f"   Protocolo: {resultado['protocolo']}")
        print(f"   **Nosso Número (API): {resultado['nosso_numero']}**")
        print(f"   Situação Geral: {resultado['situacao']}")
        print(f"   **Cód. Ocorrência: {resultado['ocorrencia_codigo']}**")
        print(f"   **Desc. Ocorrência: {resultado['ocorrencia_descricao']}**")
        print(f"   Cartório: {resultado['cartorio']}")
    else:
        print(f"\n {resultado['mensagem']}")
    """

    # ==================================================
    # EXEMPLO 2: Consulta em Lote (DESCOMENTE PARA USAR)
    # ==================================================
    # Para usar este bloco, você precisaria de um arquivo 'carteira9.json'
    # contendo uma lista de objetos como: [{"SEU NUMERO": "...", "VALOR DO TITULO": 123.45}, ...]

    print("\n\n### EXEMPLO 2: Consulta em Lote ###")

    # Crie o arquivo 'carteira9.json' no mesmo diretório
    resultados = processar_carteira_json("carteira9.json")

    # Salvar resultados em um arquivo JSON
    with open("resultados_consulta.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\nResultados salvos em 'resultados_consulta.json'")

    # ==================================================
    # EXEMPLO 3: Consultar múltiplos títulos específicos
    # ==================================================
    """
    print("\n\n### EXEMPLO 3: Consultar Lista Específica ###")
    
    titulos_para_consultar = ["092897/25", "15735B", "515T", "516T"]
    
    for titulo in titulos_para_consultar:
        resultado = consultar_status_titulo(titulo, verbose=False)
        ocorr_info = f"{resultado['ocorrencia_descricao']} ({resultado['ocorrencia_codigo']})"
        print(f"{titulo} | Status: {resultado['status']} | Ocorrência: {ocorr_info} | Nosso Número: {resultado['nosso_numero']}")
    """

    print("\n" + "=" * 80)
    print("SCRIPT FINALIZADO")
    print("=" * 80)
