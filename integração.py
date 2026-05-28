import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL_T1 = "https://api-t1.proxpect.com.br/proxpect/integracao/comprador/api"
BASE_URL    = "https://api.proxpect.com.br/proxpect/integracao/comprador/api"

HEADERS = {
    "accept": "application/json",
    "client-id": os.getenv("CLIENT_ID", "teixeira"),
    "secret-key": os.getenv("SECRET_KEY", "teixeira")
}


def _get(url: str) -> list:
    """Faz GET e retorna o conteúdo como lista, com tratamento de erros."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        conteudo = response.json().get("content", [])
        return [conteudo] if isinstance(conteudo, dict) else conteudo
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP em {url}: {e}")
    except requests.exceptions.ConnectionError:
        print(f"Erro de conexão em {url}")
    except requests.exceptions.Timeout:
        print(f"Timeout em {url}")
    return []


def get_centros_custos():
    conteudo = _get(f"{BASE_URL_T1}/centros-custos")
    for item in conteudo:
        print(item.get("id"), "-", item.get("nome"))
    return conteudo


def get_fornecedor_por_cnpj(cnpj: str):
    conteudo = _get(f"{BASE_URL}/fornecedores/cnpj/{cnpj}")
    for item in conteudo:
        print(item.get("id"), "-", item.get("nome"), "-", item.get("cnpj"))
    return conteudo


def get_modos_pagamentos():
    conteudo = _get(f"{BASE_URL}/modos-pagamentos")
    for item in conteudo:
        print(item.get("id"), "-", item.get("nome"))
    return conteudo


if __name__ == "__main__":
    print("=== Centros de Custos ===")
    get_centros_custos()

    print("\n=== Fornecedor por CNPJ ===")
    get_fornecedor_por_cnpj("00000000000000")

    print("\n=== Modos de Pagamento ===")
    get_modos_pagamentos()