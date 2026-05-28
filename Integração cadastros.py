import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api-t1.proxpect.com.br/proxpect/integracao/comprador/api"

HEADERS = {
    "accept": "application/json",
    "client-id": os.getenv("CLIENT_ID", "teixeira"),
    "secret-key": os.getenv("SECRET_KEY", "teixeira")
}


def _get(path: str) -> list:
    url = BASE_URL + path
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        conteudo = data.get("content", data)
        if isinstance(conteudo, dict):
            conteudo = [conteudo]

        return conteudo

    except requests.exceptions.HTTPError as e:
        print(f"  Erro HTTP {e.response.status_code} em {url}")
        try:
            print(f"  Detalhe: {e.response.json()}")
        except Exception:
            print(f"  Detalhe: {e.response.text[:200]}")
        return []
    except requests.exceptions.ConnectionError:
        print(f"  Erro de conexão em {url}")
        return []
    except requests.exceptions.Timeout:
        print(f"  Timeout em {url}")
        return []


def get_centros_custos():
    print("\n=== CENTRO DE CUSTOS ===")
    conteudo = _get("/centros-custos")
    if conteudo:
        print(f"  [chaves]: {list(conteudo[0].keys())}")
    for item in conteudo:
        print(item)
    return conteudo


def get_modos_pagamentos():
    print("\n=== MODOS DE PAGAMENTO ===")
    conteudo = _get("/modos-pagamentos")
    if conteudo:
        print(f"  [chaves]: {list(conteudo[0].keys())}")
    for item in conteudo:
        print(item)
    return conteudo


def get_grupos():
    print("\n=== CATEGORIAS ===")
    conteudo = _get("/grupos")
    if conteudo:
        print(f"  [chaves]: {list(conteudo[0].keys())}")
    for item in conteudo:
        print(item)
    return conteudo


if __name__ == "__main__":
    get_centros_custos()
    get_modos_pagamentos()
    get_grupos()