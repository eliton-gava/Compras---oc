import requests

BASE_URL_T1 = "https://api-t1.proxpect.com.br/proxpect/integracao/comprador/api"
BASE_URL    = "https://api.proxpect.com.br/proxpect/integracao/comprador/api"

HEADERS = {
    "accept": "application/json",
    "client-id": "teixeira",
    "secret-key": "teixeira"
}


def get_centros_custos():
    url = f"{BASE_URL_T1}/centros-custos"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    conteudo = response.json().get("content", [])
    for item in conteudo:
        print(item.get("id"))
        print(item.get("nome"))

    return conteudo


def get_fornecedor_por_cnpj(cnpj: str):
    url = f"{BASE_URL}/fornecedores/cnpj/{cnpj}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    conteudo = response.json().get("content", [])
    for item in conteudo:
        print(item.get("id"))
        print(item.get("nome"))
        print(item.get("cnpj"))

    return conteudo


def get_modos_pagamentos():
    url = f"{BASE_URL}/modos-pagamentos"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    conteudo = response.json().get("content", [])
    for item in conteudo:
        print(item.get("id"))
        print(item.get("nome"))

    return conteudo


if __name__ == "__main__":
    print("=== Centros de Custos ===")
    get_centros_custos()

    print("\n=== Fornecedor por CNPJ ===")
    get_fornecedor_por_cnpj("00000000000000")  # substitua pelo CNPJ real

    print("\n=== Modos de Pagamento ===")
    get_modos_pagamentos()