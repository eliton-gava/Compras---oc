import requests

BASE_URL = "https://api.proxpect.com.br/proxpect/integracao/comprador/api"

HEADERS = {
    "accept": "application/json",
    "client-id": "teixeira",
    "secret-key": "teixeira"
}
# ──────────────────────────────────────────
# GET - REQUISIÇÕES (lista completa)
# ──────────────────────────────────────────
def get_requisicoes():
    url = f"{BASE_URL}/requisicoes"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    result = response.json()
    print("=== Estrutura completa da resposta ===")
    print(result)

    conteudo = result.get("content", [])
    print(f"\nTotal de registros: {len(conteudo)}")

    for item in conteudo:
        print("\n--- Requisição ---")
        for campo, valor in item.items():
            print(f"  {campo}: {valor}")

    return conteudo

# ──────────────────────────────────────────
# EXECUÇÃO
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== Requisições ===")
    get_requisicoes()