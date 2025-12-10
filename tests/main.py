import requests
import base64
import json

URL_BASE = "http://craam.api.crabr.com.br"
ENDPOINT = "/titulo"
USUARIO_API = "59226900272"
SENHA_API = "Barbara1$#"


def consultar_titulo_cra21(num_titulo: str, doc_devedor: str) -> dict:
    credenciais = f"{USUARIO_API}:{SENHA_API}"
    credenciais_b64 = base64.b64encode(credenciais.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {credenciais_b64}",
        "Accept": "application/json",
    }

    url_completa = f"{URL_BASE}{ENDPOINT}"

    parametros = {
        "numeroTitulo": num_titulo,
    }

    print(f"-> Tentando acessar: {url_completa}")

    try:
        response = requests.get(url_completa, headers=headers, params=parametros)

        print("\n--- JSON BRUTO RECEBIDO ---")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        print("---------------------------\n")

        # 4. Tratamento dos Códigos de Status HTTP

        if response.status_code == 200:
            # Requisição OK. O título pode ou não ter sido encontrado.
            return response.json()

        elif response.status_code == 401:
            # Erro de Autenticação
            return {
                "status": "ERRO_AUTENTICACAO",
                "mensagem": "Falha na autenticação. Verifique USUARIO_API e SENHA_API.",
            }

        elif response.status_code == 404:
            # Recurso não encontrado (Endpoint incorreto, improvável para /titulo se a base estiver certa)
            return {
                "status": "ERRO_ENDPOINT",
                "mensagem": f"Endpoint não encontrado (404). URL: {url_completa}",
            }

        else:
            # Outros erros HTTP (5xx, 4xx)
            return {
                "status": "ERRO_HTTP",
                "codigo": response.status_code,
                "mensagem": f"Erro HTTP inesperado: {response.status_code}. Detalhes: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        # Erro de conexão (timeout, DNS, SSL, etc.)
        return {
            "status": "ERRO_CONEXAO",
            "mensagem": f"Falha na conexão com a API: {e}",
        }


# --- Exemplo de Uso ---
if __name__ == "__main__":
    print("--- Consulta de Título Existente ---")
    resultado_sucesso = consultar_titulo_cra21(
        # num_titulo="123707/25",
        num_titulo="092897/25",
        doc_devedor="",
    )

    # 5. Análise da Resposta (Tratamento Específico do JSON)
    if "status" in resultado_sucesso and "ERRO" in resultado_sucesso["status"]:
        print(f"ERRO: {resultado_sucesso['mensagem']}")
    else:
        # Se for sucesso (HTTP 200), precisamos verificar se algum título foi retornado
        titulos_encontrados = resultado_sucesso.get("_embedded", {}).get("titulo", [])

        if titulos_encontrados:
            print(f"Sucesso! Total de títulos encontrados: {len(titulos_encontrados)}")
            primeiro_titulo = titulos_encontrados[0]

            # DEBUG opcional: ver estrutura do primeiro título
            # import json
            # print(json.dumps(primeiro_titulo, indent=2, ensure_ascii=False))

            print(f"   Protocolo: {primeiro_titulo.get('protocolo')}")
            print(f"   Situação: {primeiro_titulo.get('situacao')}")

            # Extrai descrição da ocorrência com vários fallbacks
            ocorr = primeiro_titulo.get("ocorrencia")
            ocorr_desc = None
            if isinstance(ocorr, dict):
                ocorr_desc = (
                    ocorr.get("descricao") or ocorr.get("desc") or ocorr.get("texto")
                )
            elif isinstance(ocorr, list) and len(ocorr) > 0:
                first = ocorr[0]
                if isinstance(first, dict):
                    ocorr_desc = (
                        first.get("descricao")
                        or first.get("desc")
                        or first.get("texto")
                    )
                else:
                    ocorr_desc = str(first)
            elif ocorr is not None:
                ocorr_desc = str(ocorr)

            # fallback final: se for dict/list imprime json resumido
            if not ocorr_desc and isinstance(ocorr, (dict, list)):
                try:
                    ocorr_desc = json.dumps(ocorr, ensure_ascii=False)
                except Exception:
                    ocorr_desc = str(ocorr)

            print(f"   Ocorrência: {ocorr_desc if ocorr_desc else 'N/D'}")
            print(f"   Cartório: {primeiro_titulo.get('cartorio', {}).get('nome')}")
        else:
            print(
                "Sucesso HTTP (200), mas o título não foi encontrado (total_items: 0)."
            )

    # print("\n" + "=" * 40 + "\n")

    # # Exemplo 2: Simulação de título não encontrado (MUITO IMPORTANTE)
    # print("--- Consulta de Título Inexistente ---")
    # resultado_nao_encontrado = consultar_titulo_cra21(
    #     num_titulo="0000000000", doc_devedor="99999999999"
    # )

    # # A resposta deve ser 200, mas com o array 'titulo' vazio.
    # if (
    #     "status" not in resultado_nao_encontrado
    #     and resultado_nao_encontrado.get("total_items") == 0
    # ):
    #     print("Resultado esperado! Título não localizado. Total de itens: 0.")
    # else:
    #     print("Comportamento inesperado na simulação de título inexistente.")
