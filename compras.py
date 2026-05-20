import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DE ARQUIVOS
# ─────────────────────────────────────────────
DIR_BASE        = Path("compras_data")
DIR_TXT         = DIR_BASE / "relatorios"
DIR_CSV         = DIR_BASE / "csv"
DIR_ENTREGAS    = DIR_BASE / "entregas"
HISTORICO_JSON  = DIR_BASE / "historico.json"
HISTORICO_CSV   = DIR_BASE / "historico_geral.csv"
OCORRENCIAS_JSON = DIR_BASE / "ocorrencias.json"
ENTREGAS_CSV    = DIR_BASE / "entregas_geral.csv"
FORNECEDORES_JSON = DIR_BASE / "fornecedores.json"
PRODUTOS_JSON     = DIR_BASE / "produtos.json"

for d in (DIR_BASE, DIR_TXT, DIR_CSV, DIR_ENTREGAS):
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
#  CONSTANTES — COMPRAS
# ─────────────────────────────────────────────
MODOS_PAGAMENTO = {
    "1": "Boleto",
    "2": "Transferência",
    "3": "PIX",
    "4": "Dinheiro",
    "5": "Outros",
}

STATUS_OPCOES = {
    "1": "Pendente",
    "2": "Aprovada",
    "3": "Recebida",
    "4": "Cancelada",
}

CENTROS_CUSTO = {
    "1": "Estoque",
    "2": "Manutenção",
    "3": "Administrativo",
    "4": "Produção",
    "5": "TI",
    "6": "Outro",
}

MOEDAS = {
    "1": ("BRL", "R$"),
    "2": ("USD", "US$"),
    "3": ("EUR", "€"),
}

# ─────────────────────────────────────────────
#  CONSTANTES — ENTREGAS
# ─────────────────────────────────────────────
STATUS_ENTREGA = {
    "1": "Aguardando envio",
    "2": "Em trânsito",
    "3": "Saiu para entrega",
    "4": "Entregue parcialmente",
    "5": "Entregue",
    "6": "Devolvido",
    "7": "Extraviado",
    "8": "Cancelado",
}

TIPO_OCORRENCIA = {
    "1": "Atraso",
    "2": "Avaria / dano",
    "3": "Produto errado",
    "4": "Quantidade incorreta",
    "5": "Nota fiscal incorreta",
    "6": "Entrega parcial",
    "7": "Extravio",
    "8": "Recusa na entrega",
    "9": "Outro",
}

TRANSPORTADORAS_PADRAO = [
    "Correios", "Jadlog", "Azul Cargo", "Braspress",
    "TNT", "FedEx", "DHL", "Total Express", "Outro",
]

CATEGORIAS_FORNECEDOR = {
    "1": "Matéria-prima",
    "2": "Serviços",
    "3": "Equipamentos",
    "4": "TI / Tecnologia",
    "5": "Embalagens",
    "6": "MRO (Manutenção)",
    "7": "Transporte / Logística",
    "8": "Outro",
}

# ─────────────────────────────────────────────
#  FUNÇÕES UTILITÁRIAS DE ENTRADA
# ─────────────────────────────────────────────

def linha(char="─", n=50):
    print(char * n)

def titulo(texto):
    print()
    linha()
    print(f"  {texto}")
    linha()

def input_texto(prompt, obrigatorio=True):
    while True:
        valor = input(prompt).strip()
        if valor:
            return valor
        if not obrigatorio:
            return ""
        print("  ⚠  Campo obrigatório. Preencha novamente.")

def input_float(prompt, permite_zero=True):
    while True:
        entrada = input(prompt).strip().replace(",", ".")
        try:
            valor = float(entrada)
            if valor < 0:
                print("  ⚠  O valor não pode ser negativo. Tente novamente.")
                continue
            if not permite_zero and valor == 0:
                print("  ⚠  O valor deve ser maior que zero. Tente novamente.")
                continue
            return valor
        except ValueError:
            print(f"  ⚠  '{entrada}' não é válido. Use vírgula ou ponto (ex: 1500,99).")

def input_int(prompt, permite_zero=False):
    while True:
        entrada = input(prompt).strip()
        try:
            valor = int(entrada)
            if not permite_zero and valor <= 0:
                print("  ⚠  Deve ser maior que zero. Tente novamente.")
                continue
            if valor < 0:
                print("  ⚠  Não pode ser negativo. Tente novamente.")
                continue
            return valor
        except ValueError:
            print(f"  ⚠  '{entrada}' não é um inteiro válido. Tente novamente.")

def input_opcao(prompt, opcoes):
    opcoes_lower = [o.lower() for o in opcoes]
    while True:
        entrada = input(prompt).strip().lower()
        if entrada in opcoes_lower:
            return entrada
        print(f"  ⚠  Opção inválida. Escolha entre: {' / '.join(opcoes)}.")

def input_sim_nao(prompt):
    return input_opcao(prompt, ["s", "n"])

def input_data_opcional(prompt, data_padrao: datetime):
    padrao_str = data_padrao.strftime("%d/%m/%Y")
    while True:
        entrada = input(f"{prompt} [padrão: {padrao_str}] (ENTER para confirmar): ").strip()
        if entrada == "":
            return padrao_str, data_padrao
        try:
            data = datetime.strptime(entrada, "%d/%m/%Y")
            return data.strftime("%d/%m/%Y"), data
        except ValueError:
            print(f"  ⚠  Use DD/MM/AAAA ou ENTER para {padrao_str}.")

def input_data_obrigatoria(prompt):
    while True:
        entrada = input(prompt).strip()
        try:
            data = datetime.strptime(entrada, "%d/%m/%Y")
            return data.strftime("%d/%m/%Y"), data
        except ValueError:
            print(f"  ⚠  '{entrada}' inválido. Use DD/MM/AAAA.")

def input_prazo_entrega(data_base: datetime):
    while True:
        entrada = input("Prazo de entrega (dias): ").strip()
        try:
            dias = int(entrada)
            if dias <= 0:
                print("  ⚠  O prazo deve ser maior que zero.")
                continue
            data_prevista = data_base + timedelta(days=dias)
            data_prevista_str = data_prevista.strftime("%d/%m/%Y")
            print(f"  ✔  {dias} dias  →  Previsão de entrega: {data_prevista_str}")
            return f"{dias} dias", data_prevista_str
        except ValueError:
            print(f"  ⚠  '{entrada}' não é inteiro válido.")

def input_desconto(base_valor):
    print("  Desconto: valor (ex: 50,00) | percentual (ex: 10%) | ENTER para nenhum")
    while True:
        entrada = input("  Desconto: ").strip().replace(",", ".")
        if entrada == "":
            return 0.0
        if entrada.endswith("%"):
            try:
                perc = float(entrada[:-1])
                if perc < 0:
                    print("  ⚠  Percentual não pode ser negativo.")
                    continue
                return base_valor * (perc / 100)
            except ValueError:
                print(f"  ⚠  '{entrada}' inválido. Ex: 10%")
        else:
            try:
                valor = float(entrada)
                if valor < 0:
                    print("  ⚠  Não pode ser negativo.")
                    continue
                return valor
            except ValueError:
                print(f"  ⚠  '{entrada}' inválido.")

def input_menu(opcoes_dict):
    """Exibe menu numerado e retorna (código, descrição)."""
    for cod, desc in opcoes_dict.items():
        print(f"    [{cod}] {desc}")
    while True:
        entrada = input("  Código: ").strip()
        if entrada in opcoes_dict:
            return entrada, opcoes_dict[entrada]
        print(f"  ⚠  Código inválido. Escolha: {', '.join(opcoes_dict.keys())}.")

def input_pagamento():
    print("\n  Modos de pagamento:")
    cod, modo = input_menu(MODOS_PAGAMENTO)
    if modo == "Outros":
        descricao = input_texto("  Descreva o modo de pagamento: ")
        return cod, f"Outros ({descricao})"
    return cod, modo

def input_parcelas(modo_pagamento):
    """Se pagamento for Boleto ou Transferência, pergunta sobre parcelas."""
    if not any(x in modo_pagamento for x in ["Boleto", "Transferência"]):
        return 1, []
    if input_sim_nao("  Parcelado? (s/n): ") != "s":
        return 1, []
    n = input_int("  Número de parcelas: ", permite_zero=False)
    vencimentos = []
    print(f"  Informe as datas de vencimento das {n} parcela(s):")
    for i in range(1, n + 1):
        data_str, _ = input_data_obrigatoria(f"    Parcela {i} (DD/MM/AAAA): ")
        vencimentos.append(data_str)
    return n, vencimentos

def gerar_numero_pedido():
    """Gera número de pedido sequencial baseado no histórico."""
    historico = carregar_historico()
    return f"PC-{len(historico) + 1:04d}"

def gerar_codigo_fornecedor():
    """Gera código sequencial para fornecedor."""
    fornecedores = carregar_fornecedores()
    return f"FOR-{len(fornecedores) + 1:04d}"

# ─────────────────────────────────────────────
#  HISTÓRICO JSON
# ─────────────────────────────────────────────

def carregar_historico():
    if not HISTORICO_JSON.exists():
        return []
    with open(HISTORICO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_historico(compra):
    historico = carregar_historico()
    historico.append(compra)
    with open(HISTORICO_JSON, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

def atualizar_historico_compra(historico: list):
    """Persiste o histórico inteiro de volta ao JSON."""
    with open(HISTORICO_JSON, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

def _compra_por_pedido(num_pedido: str):
    """Retorna (historico, índice, compra) ou (historico, None, None)."""
    historico = carregar_historico()
    num = num_pedido.upper()
    for i, c in enumerate(historico):
        if c["num_pedido"].upper() == num:
            return historico, i, c
    return historico, None, None

# ─────────────────────────────────────────────
#  FORNECEDORES — PERSISTÊNCIA
# ─────────────────────────────────────────────

def carregar_fornecedores():
    if not FORNECEDORES_JSON.exists():
        return []
    with open(FORNECEDORES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_fornecedores(lista: list):
    with open(FORNECEDORES_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def _buscar_fornecedor_por_codigo(codigo: str):
    fornecedores = carregar_fornecedores()
    cod = codigo.upper()
    for i, f in enumerate(fornecedores):
        if f["codigo"].upper() == cod:
            return fornecedores, i, f
    return fornecedores, None, None

# ─────────────────────────────────────────────
#  FORNECEDORES — CADASTRAR
# ─────────────────────────────────────────────

def cadastrar_fornecedor(retornar_dados=False):
    """
    Cadastra um novo fornecedor.
    Se retornar_dados=True, retorna o dict do fornecedor criado (usado no fluxo de nova compra).
    """
    titulo("CADASTRAR FORNECEDOR")

    codigo = gerar_codigo_fornecedor()
    print(f"\n  Código gerado: {codigo}")
    alt = input("  Deseja usar outro código? (ENTER para confirmar ou digite): ").strip()
    if alt:
        codigo = alt.upper()
        # Verificar duplicidade
        fors = carregar_fornecedores()
        if any(f["codigo"].upper() == codigo for f in fors):
            print(f"  ⚠  Código '{codigo}' já existe. Usando código gerado: {gerar_codigo_fornecedor()}")
            codigo = gerar_codigo_fornecedor()

    print()
    nome         = input_texto("Nome / Razão social: ")
    nome_fantasia = input_texto("Nome fantasia (ENTER para pular): ", obrigatorio=False)
    cnpj_cpf     = input_texto("CNPJ/CPF (ENTER para pular): ", obrigatorio=False)
    ie           = input_texto("Inscrição Estadual (ENTER para pular): ", obrigatorio=False)

    print("\n  Categoria do fornecedor:")
    _, categoria = input_menu(CATEGORIAS_FORNECEDOR)
    if categoria == "Outro":
        categoria = input_texto("  Descreva a categoria: ")

    print()
    contato      = input_texto("Nome do contato (ENTER para pular): ", obrigatorio=False)
    telefone     = input_texto("Telefone / WhatsApp (ENTER para pular): ", obrigatorio=False)
    email        = input_texto("E-mail (ENTER para pular): ", obrigatorio=False)

    print()
    endereco     = input_texto("Endereço (ENTER para pular): ", obrigatorio=False)
    cidade       = input_texto("Cidade (ENTER para pular): ", obrigatorio=False)
    estado       = input_texto("Estado (UF, ENTER para pular): ", obrigatorio=False)

    print()
    prazo_medio  = input_texto("Prazo médio de entrega (ex: 5 dias, ENTER para pular): ", obrigatorio=False)
    cond_pagto   = input_texto("Condição de pagamento preferencial (ENTER para pular): ", obrigatorio=False)
    obs          = input_texto("Observações (ENTER para pular): ", obrigatorio=False)

    ativo = True

    # ── Resumo ──
    titulo("RESUMO DO FORNECEDOR")
    print(f"  Código         : {codigo}")
    print(f"  Nome           : {nome}")
    if nome_fantasia: print(f"  Nome Fantasia  : {nome_fantasia}")
    if cnpj_cpf:      print(f"  CNPJ/CPF       : {cnpj_cpf}")
    if ie:            print(f"  IE             : {ie}")
    print(f"  Categoria      : {categoria}")
    if contato:       print(f"  Contato        : {contato}")
    if telefone:      print(f"  Telefone       : {telefone}")
    if email:         print(f"  E-mail         : {email}")
    if endereco:      print(f"  Endereço       : {endereco}")
    if cidade:        print(f"  Cidade/UF      : {cidade} {estado}")
    if prazo_medio:   print(f"  Prazo médio    : {prazo_medio}")
    if cond_pagto:    print(f"  Cond. pagto    : {cond_pagto}")
    if obs:           print(f"  Observações    : {obs}")
    linha()

    if input_sim_nao("\n  Confirmar cadastro? (s/n): ") != "s":
        print("  ✖  Cadastro cancelado.")
        if retornar_dados:
            return None
        return

    fornecedor = {
        "codigo":          codigo,
        "nome":            nome,
        "nome_fantasia":   nome_fantasia,
        "cnpj_cpf":        cnpj_cpf,
        "ie":              ie,
        "categoria":       categoria,
        "contato":         contato,
        "telefone":        telefone,
        "email":           email,
        "endereco":        endereco,
        "cidade":          cidade,
        "estado":          estado,
        "prazo_medio":     prazo_medio,
        "cond_pagto":      cond_pagto,
        "obs":             obs,
        "ativo":           ativo,
        "data_cadastro":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_compras":   0,
        "valor_total_brl": 0.0,
    }

    fors = carregar_fornecedores()
    fors.append(fornecedor)
    salvar_fornecedores(fors)
    print(f"\n  ✔  Fornecedor '{nome}' cadastrado como {codigo}.")

    if retornar_dados:
        return fornecedor
    return None

# ─────────────────────────────────────────────
#  FORNECEDORES — SELECIONAR (usado na nova compra)
# ─────────────────────────────────────────────

def selecionar_ou_cadastrar_fornecedor():
    """
    Fluxo de seleção de fornecedor na nova compra.
    Retorna (nome, cnpj_cpf) — mantém compatibilidade com o resto do fluxo.
    Também retorna o código do fornecedor para atualizar estatísticas depois.
    """
    fors = carregar_fornecedores()
    fors_ativos = [f for f in fors if f.get("ativo", True)]

    print("\n  ── Fornecedor ──")
    print("  [1] Selecionar fornecedor cadastrado")
    print("  [2] Cadastrar novo fornecedor agora")
    print("  [3] Digitar manualmente (sem salvar)")
    op = input("  Opção: ").strip()

    if op == "1":
        if not fors_ativos:
            print("  ⚠  Nenhum fornecedor cadastrado. Digite manualmente.")
            nome     = input_texto("Fornecedor: ")
            cnpj_cpf = input_texto("CNPJ/CPF (ENTER para pular): ", obrigatorio=False)
            return nome, cnpj_cpf, None

        # Listar e buscar
        while True:
            linha()
            print(f"  {'CÓD':<10} {'NOME':<35} {'CNPJ/CPF':<20} {'CATEGORIA'}")
            linha()
            for f in fors_ativos:
                print(f"  {f['codigo']:<10} {f['nome'][:34]:<35} "
                      f"{f.get('cnpj_cpf','—')[:19]:<20} {f.get('categoria','')}")
            linha()
            print("  Digite o código, parte do nome, ou ENTER para buscar:")
            termo = input("  Busca: ").strip().lower()

            if termo == "":
                # Mostrou lista, pedir código diretamente
                cod = input_texto("  Código do fornecedor: ").upper()
                _, _, found = _buscar_fornecedor_por_codigo(cod)
                if found:
                    _exibir_ficha_fornecedor(found)
                    if input_sim_nao("  Usar este fornecedor? (s/n): ") == "s":
                        return found["nome"], found.get("cnpj_cpf", ""), found["codigo"]
                else:
                    print(f"  ⚠  Código '{cod}' não encontrado.")
            else:
                # Busca por nome ou código
                resultados = [
                    f for f in fors_ativos
                    if termo in f["nome"].lower()
                    or termo in f.get("nome_fantasia", "").lower()
                    or termo in f["codigo"].lower()
                ]
                if not resultados:
                    print(f"  ⚠  Nenhum fornecedor encontrado para '{termo}'.")
                    if input_sim_nao("  Tentar novamente? (s/n): ") != "s":
                        break
                    continue
                if len(resultados) == 1:
                    f = resultados[0]
                    _exibir_ficha_fornecedor(f)
                    if input_sim_nao("  Usar este fornecedor? (s/n): ") == "s":
                        return f["nome"], f.get("cnpj_cpf", ""), f["codigo"]
                else:
                    linha()
                    for i, f in enumerate(resultados, 1):
                        print(f"  [{i}] {f['codigo']:<10} {f['nome']}")
                    linha()
                    idx_str = input("  Número da opção (ou ENTER para cancelar): ").strip()
                    if idx_str == "":
                        continue
                    try:
                        idx_escolha = int(idx_str) - 1
                        if 0 <= idx_escolha < len(resultados):
                            f = resultados[idx_escolha]
                            return f["nome"], f.get("cnpj_cpf", ""), f["codigo"]
                    except ValueError:
                        pass
                    print("  ⚠  Seleção inválida.")

        # Saiu do loop sem selecionar → digitar manualmente
        nome     = input_texto("Fornecedor: ")
        cnpj_cpf = input_texto("CNPJ/CPF (ENTER para pular): ", obrigatorio=False)
        return nome, cnpj_cpf, None

    elif op == "2":
        fornecedor = cadastrar_fornecedor(retornar_dados=True)
        if fornecedor:
            return fornecedor["nome"], fornecedor.get("cnpj_cpf", ""), fornecedor["codigo"]
        # Se cancelou o cadastro, digitar manualmente
        nome     = input_texto("Fornecedor: ")
        cnpj_cpf = input_texto("CNPJ/CPF (ENTER para pular): ", obrigatorio=False)
        return nome, cnpj_cpf, None

    else:  # op == "3" ou qualquer outra coisa
        nome     = input_texto("Fornecedor: ")
        cnpj_cpf = input_texto("CNPJ/CPF (ENTER para pular): ", obrigatorio=False)
        return nome, cnpj_cpf, None

def _exibir_ficha_fornecedor(f: dict):
    linha("─", 50)
    print(f"  Código    : {f['codigo']}")
    print(f"  Nome      : {f['nome']}")
    if f.get("nome_fantasia"):  print(f"  Fantasia  : {f['nome_fantasia']}")
    if f.get("cnpj_cpf"):       print(f"  CNPJ/CPF  : {f['cnpj_cpf']}")
    print(f"  Categoria : {f.get('categoria','—')}")
    if f.get("contato"):        print(f"  Contato   : {f['contato']}")
    if f.get("telefone"):       print(f"  Telefone  : {f['telefone']}")
    if f.get("email"):          print(f"  E-mail    : {f['email']}")
    if f.get("cidade"):
        uf = f" - {f['estado']}" if f.get("estado") else ""
        print(f"  Cidade    : {f['cidade']}{uf}")
    if f.get("prazo_medio"):    print(f"  Prazo     : {f['prazo_medio']}")
    if f.get("cond_pagto"):     print(f"  Pagamento : {f['cond_pagto']}")
    qtd = f.get("total_compras", 0)
    val = f.get("valor_total_brl", 0.0)
    if qtd:
        print(f"  Histórico : {qtd} compra(s) | R$ {val:.2f} em pedidos")
    if f.get("obs"):            print(f"  Obs       : {f['obs']}")
    linha("─", 50)

def _atualizar_estatisticas_fornecedor(codigo: str, valor_brl: float):
    """Incrementa contadores do fornecedor após salvar compra."""
    if not codigo:
        return
    fors, idx, f = _buscar_fornecedor_por_codigo(codigo)
    if idx is None:
        return
    fors[idx]["total_compras"]   = fors[idx].get("total_compras", 0) + 1
    fors[idx]["valor_total_brl"] = fors[idx].get("valor_total_brl", 0.0) + valor_brl
    salvar_fornecedores(fors)

# ─────────────────────────────────────────────
#  FORNECEDORES — LISTAR / EDITAR / INATIVAR
# ─────────────────────────────────────────────

def listar_fornecedores(mostrar_inativos=False):
    fors = carregar_fornecedores()
    lista = fors if mostrar_inativos else [f for f in fors if f.get("ativo", True)]
    if not lista:
        print("\n  Nenhum fornecedor cadastrado.")
        return
    linha()
    print(f"  {'CÓD':<10} {'NOME':<35} {'CNPJ/CPF':<20} {'CATEG.':<20} {'COMPRAS':>7} {'TOTAL R$':>12}")
    linha()
    for f in lista:
        status_str = "" if f.get("ativo", True) else " [inativo]"
        print(f"  {f['codigo']:<10} {(f['nome'] + status_str)[:34]:<35} "
              f"{f.get('cnpj_cpf','—')[:19]:<20} "
              f"{f.get('categoria','')[:19]:<20} "
              f"{f.get('total_compras',0):>7} "
              f"R$ {f.get('valor_total_brl',0.0):>10.2f}")
    linha()
    print(f"  Total: {len(lista)} fornecedor(es)")

def editar_fornecedor():
    titulo("EDITAR FORNECEDOR")
    listar_fornecedores()
    fors = carregar_fornecedores()
    if not fors:
        return

    cod = input_texto("\n  Código do fornecedor a editar: ").upper()
    fors_all, idx, f = _buscar_fornecedor_por_codigo(cod)
    if idx is None:
        print(f"  ⚠  Fornecedor '{cod}' não encontrado.")
        return

    _exibir_ficha_fornecedor(f)
    print("\n  O que deseja editar?")
    print("  [1]  Nome / Razão social")
    print("  [2]  Nome fantasia")
    print("  [3]  CNPJ/CPF")
    print("  [4]  Inscrição Estadual")
    print("  [5]  Categoria")
    print("  [6]  Contato")
    print("  [7]  Telefone")
    print("  [8]  E-mail")
    print("  [9]  Endereço / Cidade / Estado")
    print("  [10] Prazo médio de entrega")
    print("  [11] Condição de pagamento")
    print("  [12] Observações")
    print("  [13] Inativar / Reativar fornecedor")
    print("  [0]  Cancelar")
    op = input("  Opção: ").strip()

    campo_map = {
        "1":  ("nome", "Nome / Razão social: "),
        "2":  ("nome_fantasia", "Nome fantasia: "),
        "3":  ("cnpj_cpf", "CNPJ/CPF: "),
        "4":  ("ie", "Inscrição Estadual: "),
        "6":  ("contato", "Nome do contato: "),
        "7":  ("telefone", "Telefone / WhatsApp: "),
        "8":  ("email", "E-mail: "),
        "10": ("prazo_medio", "Prazo médio de entrega: "),
        "11": ("cond_pagto", "Condição de pagamento: "),
        "12": ("obs", "Observações: "),
    }

    if op in campo_map:
        campo, prompt = campo_map[op]
        obrig = (op == "1")  # só nome é obrigatório
        novo_valor = input_texto(f"  {prompt}", obrigatorio=obrig)
        fors_all[idx][campo] = novo_valor
        salvar_fornecedores(fors_all)
        print(f"  ✔  Campo atualizado.")

    elif op == "5":
        print("\n  Categoria:")
        _, categoria = input_menu(CATEGORIAS_FORNECEDOR)
        if categoria == "Outro":
            categoria = input_texto("  Descreva a categoria: ")
        fors_all[idx]["categoria"] = categoria
        salvar_fornecedores(fors_all)
        print(f"  ✔  Categoria atualizada.")

    elif op == "9":
        fors_all[idx]["endereco"] = input_texto("  Endereço: ", obrigatorio=False)
        fors_all[idx]["cidade"]   = input_texto("  Cidade: ", obrigatorio=False)
        fors_all[idx]["estado"]   = input_texto("  Estado (UF): ", obrigatorio=False)
        salvar_fornecedores(fors_all)
        print(f"  ✔  Endereço atualizado.")

    elif op == "13":
        atual = fors_all[idx].get("ativo", True)
        acao  = "Reativar" if not atual else "Inativar"
        if input_sim_nao(f"  {acao} fornecedor '{f['nome']}'? (s/n): ") == "s":
            fors_all[idx]["ativo"] = not atual
            salvar_fornecedores(fors_all)
            print(f"  ✔  Fornecedor {'reativado' if not atual else 'inativado'}.")

    elif op != "0":
        print("  ⚠  Opção inválida.")

def buscar_fornecedor():
    titulo("BUSCAR FORNECEDOR")
    termo = input_texto("  Buscar (nome, código, CNPJ): ").lower()
    fors  = carregar_fornecedores()
    resultados = [
        f for f in fors
        if termo in f["nome"].lower()
        or termo in f.get("nome_fantasia", "").lower()
        or termo in f["codigo"].lower()
        or termo in f.get("cnpj_cpf", "").lower()
    ]
    if not resultados:
        print(f"\n  Nenhum resultado para '{termo}'.")
        return
    print(f"\n  {len(resultados)} fornecedor(es) encontrado(s):")
    for f in resultados:
        _exibir_ficha_fornecedor(f)

# ─────────────────────────────────────────────
#  MENU DE FORNECEDORES
# ─────────────────────────────────────────────

def menu_fornecedores():
    while True:
        titulo("GESTÃO DE FORNECEDORES")
        print("  [1] Listar fornecedores ativos")
        print("  [2] Cadastrar novo fornecedor")
        print("  [3] Buscar fornecedor")
        print("  [4] Editar fornecedor")
        print("  [5] Listar todos (incluindo inativos)")
        print("  [0] Voltar")
        linha()
        op = input("  Opção: ").strip()
        if   op == "1": listar_fornecedores()
        elif op == "2": cadastrar_fornecedor()
        elif op == "3": buscar_fornecedor()
        elif op == "4": editar_fornecedor()
        elif op == "5": listar_fornecedores(mostrar_inativos=True)
        elif op == "0": break
        else:           print("  ⚠  Opção inválida.")

# ─────────────────────────────────────────────
#  CONSTANTES — PRODUTOS
# ─────────────────────────────────────────────

CATEGORIAS_PRODUTO = {
    "1": "Matéria-prima",
    "2": "Produto acabado",
    "3": "Embalagem",
    "4": "Peça / Componente",
    "5": "Material de escritório",
    "6": "EPI / Segurança",
    "7": "Ferramenta / Equipamento",
    "8": "TI / Informática",
    "9": "Limpeza / Higiene",
    "10": "Outro",
}

UNIDADES_MEDIDA = {
    "1":  "UN  (unidade)",
    "2":  "CX  (caixa)",
    "3":  "KG  (quilograma)",
    "4":  "G   (grama)",
    "5":  "L   (litro)",
    "6":  "ML  (mililitro)",
    "7":  "M   (metro)",
    "8":  "M²  (metro quadrado)",
    "9":  "M³  (metro cúbico)",
    "10": "PC  (peça)",
    "11": "PT  (pacote)",
    "12": "SC  (saco)",
    "13": "RL  (rolo)",
    "14": "Outro",
}

# ─────────────────────────────────────────────
#  PRODUTOS — PERSISTÊNCIA
# ─────────────────────────────────────────────

def carregar_produtos():
    if not PRODUTOS_JSON.exists():
        return []
    with open(PRODUTOS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_produtos(lista: list):
    with open(PRODUTOS_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def _buscar_produto_por_codigo(codigo: str):
    produtos = carregar_produtos()
    cod = codigo.upper()
    for i, p in enumerate(produtos):
        if p["codigo"].upper() == cod:
            return produtos, i, p
    return produtos, None, None

def gerar_codigo_produto():
    produtos = carregar_produtos()
    return f"PROD-{len(produtos) + 1:04d}"

# ─────────────────────────────────────────────
#  PRODUTOS — EXIBIR FICHA
# ─────────────────────────────────────────────

def _exibir_ficha_produto(p: dict):
    linha("─", 50)
    print(f"  Código      : {p['codigo']}")
    print(f"  Nome        : {p['nome']}")
    if p.get("descricao"):      print(f"  Descrição   : {p['descricao']}")
    if p.get("marca"):          print(f"  Marca       : {p['marca']}")
    if p.get("modelo"):         print(f"  Modelo      : {p['modelo']}")
    print(f"  Categoria   : {p.get('categoria', '—')}")
    print(f"  Unidade     : {p.get('unidade', '—')}")
    if p.get("ncm"):            print(f"  NCM         : {p['ncm']}")
    if p.get("ean"):            print(f"  EAN/GTIN    : {p['ean']}")
    if p.get("icms_padrao"):    print(f"  ICMS padrão : {p['icms_padrao']}%")
    if p.get("ipi_padrao"):     print(f"  IPI padrão  : {p['ipi_padrao']}%")
    if p.get("preco_medio") is not None and p["preco_medio"] > 0:
        print(f"  Preço médio : R$ {p['preco_medio']:.2f}")
    if p.get("estoque_minimo") is not None:
        print(f"  Est. mínimo : {p['estoque_minimo']} {p.get('unidade','').split()[0]}")
    qtd = p.get("total_compras", 0)
    val = p.get("valor_total_brl", 0.0)
    if qtd:
        print(f"  Histórico   : {qtd} compra(s) | R$ {val:.2f} em pedidos")
    if p.get("obs"):            print(f"  Obs         : {p['obs']}")
    status_str = "Ativo" if p.get("ativo", True) else "Inativo"
    print(f"  Status      : {status_str}")
    linha("─", 50)

# ─────────────────────────────────────────────
#  PRODUTOS — CADASTRAR
# ─────────────────────────────────────────────

def cadastrar_produto(retornar_dados=False):
    """
    Cadastra um novo produto.
    Se retornar_dados=True, retorna o dict do produto (usado no fluxo de nova compra).
    """
    titulo("CADASTRAR PRODUTO")

    codigo = gerar_codigo_produto()
    print(f"\n  Código gerado: {codigo}")
    alt = input("  Deseja usar outro código? (ENTER para confirmar ou digite): ").strip()
    if alt:
        codigo = alt.upper()
        prods = carregar_produtos()
        if any(p["codigo"].upper() == codigo for p in prods):
            print(f"  ⚠  Código '{codigo}' já existe. Usando código gerado.")
            codigo = gerar_codigo_produto()

    print()
    nome      = input_texto("Nome do produto: ")
    descricao = input_texto("Descrição (ENTER para pular): ", obrigatorio=False)
    marca     = input_texto("Marca (ENTER para pular): ", obrigatorio=False)
    modelo    = input_texto("Modelo / Referência (ENTER para pular): ", obrigatorio=False)

    print("\n  Categoria:")
    _, categoria = input_menu(CATEGORIAS_PRODUTO)
    if categoria == "Outro":
        categoria = input_texto("  Descreva a categoria: ")

    print("\n  Unidade de medida:")
    _, unidade_raw = input_menu(UNIDADES_MEDIDA)
    if unidade_raw == "Outro":
        unidade = input_texto("  Descreva a unidade: ")
    else:
        unidade = unidade_raw.split()[0]  # Pega só a sigla: "UN", "KG" etc.

    print()
    ncm       = input_texto("NCM (ENTER para pular): ", obrigatorio=False)
    ean       = input_texto("EAN / GTIN (ENTER para pular): ", obrigatorio=False)

    print()
    icms_padrao = input_float("ICMS padrão (%) [ENTER = 0]: ")
    ipi_padrao  = input_float("IPI padrão  (%) [ENTER = 0]: ")

    print()
    preco_medio    = input_float("Preço médio de compra (R$) [ENTER = 0]: ")
    estoque_minimo = input_float("Estoque mínimo [ENTER = 0]: ")

    obs = input_texto("Observações (ENTER para pular): ", obrigatorio=False)

    # ── Resumo ──
    titulo("RESUMO DO PRODUTO")
    print(f"  Código      : {codigo}")
    print(f"  Nome        : {nome}")
    if descricao:    print(f"  Descrição   : {descricao}")
    if marca:        print(f"  Marca       : {marca}")
    if modelo:       print(f"  Modelo      : {modelo}")
    print(f"  Categoria   : {categoria}")
    print(f"  Unidade     : {unidade}")
    if ncm:          print(f"  NCM         : {ncm}")
    if ean:          print(f"  EAN/GTIN    : {ean}")
    print(f"  ICMS padrão : {icms_padrao}%")
    print(f"  IPI padrão  : {ipi_padrao}%")
    if preco_medio:  print(f"  Preço médio : R$ {preco_medio:.2f}")
    if estoque_minimo: print(f"  Est. mínimo : {estoque_minimo} {unidade}")
    if obs:          print(f"  Observações : {obs}")
    linha()

    if input_sim_nao("\n  Confirmar cadastro? (s/n): ") != "s":
        print("  ✖  Cadastro cancelado.")
        if retornar_dados:
            return None
        return

    produto = {
        "codigo":          codigo,
        "nome":            nome,
        "descricao":       descricao,
        "marca":           marca,
        "modelo":          modelo,
        "categoria":       categoria,
        "unidade":         unidade,
        "ncm":             ncm,
        "ean":             ean,
        "icms_padrao":     icms_padrao,
        "ipi_padrao":      ipi_padrao,
        "preco_medio":     preco_medio,
        "estoque_minimo":  estoque_minimo,
        "obs":             obs,
        "ativo":           True,
        "data_cadastro":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_compras":   0,
        "valor_total_brl": 0.0,
    }

    prods = carregar_produtos()
    prods.append(produto)
    salvar_produtos(prods)
    print(f"\n  ✔  Produto '{nome}' cadastrado como {codigo}.")

    if retornar_dados:
        return produto
    return None

# ─────────────────────────────────────────────
#  PRODUTOS — SELECIONAR (usado na nova compra)
# ─────────────────────────────────────────────

def selecionar_ou_cadastrar_produto(simbolo_moeda="R$"):
    """
    Fluxo de seleção de produto na nova compra.
    Retorna dict com os dados do item preenchido (codigo, nome, unidade,
    icms_padrao, ipi_padrao já pré-carregados) ou None para digitação manual.
    """
    prods = carregar_produtos()
    prods_ativos = [p for p in prods if p.get("ativo", True)]

    print("\n  ── Item da compra ──")
    print("  [1] Selecionar produto cadastrado")
    print("  [2] Cadastrar novo produto agora")
    print("  [3] Digitar manualmente (sem salvar)")
    op = input("  Opção: ").strip()

    produto_base = None

    if op == "1":
        if not prods_ativos:
            print("  ⚠  Nenhum produto cadastrado. Preencha manualmente.")
        else:
            while True:
                linha()
                print(f"  {'CÓD':<12} {'NOME':<35} {'UNID':<6} {'CATEG.':<22} {'PREÇO MÉDIO':>12}")
                linha()
                for p in prods_ativos:
                    pm = f"R$ {p['preco_medio']:.2f}" if p.get("preco_medio") else "—"
                    print(f"  {p['codigo']:<12} {p['nome'][:34]:<35} "
                          f"{p.get('unidade',''):<6} "
                          f"{p.get('categoria','')[:21]:<22} {pm:>12}")
                linha()
                print("  Digite o código, parte do nome, ou ENTER para listar:")
                termo = input("  Busca: ").strip().lower()

                if termo == "":
                    cod = input_texto("  Código do produto: ").upper()
                    _, _, found = _buscar_produto_por_codigo(cod)
                    if found:
                        _exibir_ficha_produto(found)
                        if input_sim_nao("  Usar este produto? (s/n): ") == "s":
                            produto_base = found
                            break
                    else:
                        print(f"  ⚠  Código '{cod}' não encontrado.")
                else:
                    resultados = [
                        p for p in prods_ativos
                        if termo in p["nome"].lower()
                        or termo in p.get("descricao", "").lower()
                        or termo in p["codigo"].lower()
                        or termo in p.get("marca", "").lower()
                    ]
                    if not resultados:
                        print(f"  ⚠  Nenhum produto encontrado para '{termo}'.")
                        if input_sim_nao("  Tentar novamente? (s/n): ") != "s":
                            break
                        continue
                    if len(resultados) == 1:
                        _exibir_ficha_produto(resultados[0])
                        if input_sim_nao("  Usar este produto? (s/n): ") == "s":
                            produto_base = resultados[0]
                            break
                    else:
                        linha()
                        for i, p in enumerate(resultados, 1):
                            pm = f"R$ {p['preco_medio']:.2f}" if p.get("preco_medio") else "—"
                            print(f"  [{i}] {p['codigo']:<12} {p['nome']:<35} {pm}")
                        linha()
                        idx_str = input("  Número da opção (ou ENTER para cancelar): ").strip()
                        if idx_str == "":
                            continue
                        try:
                            idx_e = int(idx_str) - 1
                            if 0 <= idx_e < len(resultados):
                                produto_base = resultados[idx_e]
                                break
                        except ValueError:
                            pass
                        print("  ⚠  Seleção inválida.")

                if produto_base:
                    break

    elif op == "2":
        produto_base = cadastrar_produto(retornar_dados=True)

    # ── Preenche os campos do item, pré-populando com dados do cadastro ──
    if produto_base:
        print(f"\n  ✔  Produto: {produto_base['nome']} [{produto_base['codigo']}]")
        codigo = produto_base["codigo"]
        nome   = produto_base["nome"]
        # Valor unitário: sugere preço médio se existir
        pm = produto_base.get("preco_medio", 0.0)
        if pm and pm > 0:
            entrada = input(f"  Valor unitário ({simbolo_moeda}) [sugerido: {pm:.2f}] (ENTER para confirmar): ").strip().replace(",", ".")
            valor_unit = float(entrada) if entrada else pm
        else:
            valor_unit = input_float(f"  Valor unitário ({simbolo_moeda}): ", permite_zero=False)
        quantidade = input_int("  Quantidade: ")
        obs_prod   = input_texto("  Observação do item (ENTER para pular): ", obrigatorio=False)
        # ICMS e IPI pré-populados
        icms_padrao = produto_base.get("icms_padrao", 0.0)
        ipi_padrao  = produto_base.get("ipi_padrao",  0.0)
        entrada_icms = input(f"  ICMS (%) [padrão: {icms_padrao}] (ENTER para confirmar): ").strip().replace(",", ".")
        icms_perc = float(entrada_icms) if entrada_icms else icms_padrao
        entrada_ipi = input(f"  IPI  (%) [padrão: {ipi_padrao}] (ENTER para confirmar): ").strip().replace(",", ".")
        ipi_perc  = float(entrada_ipi) if entrada_ipi else ipi_padrao
        return {
            "codigo_produto": produto_base["codigo"],
            "codigo":         codigo,
            "nome":           nome,
            "valor_unit":     valor_unit,
            "quantidade":     quantidade,
            "obs":            obs_prod,
            "icms_perc":      icms_perc,
            "ipi_perc":       ipi_perc,
        }

    # Digitação manual (op==3 ou não encontrou produto)
    codigo     = input_texto("  Código do produto: ")
    nome       = input_texto("  Nome do produto: ")
    valor_unit = input_float(f"  Valor unitário ({simbolo_moeda}): ", permite_zero=False)
    quantidade = input_int("  Quantidade: ")
    obs_prod   = input_texto("  Observação do item (ENTER para pular): ", obrigatorio=False)
    icms_perc  = input_float("  ICMS (%): ")
    ipi_perc   = input_float("  IPI  (%): ")
    return {
        "codigo_produto": "",
        "codigo":         codigo,
        "nome":           nome,
        "valor_unit":     valor_unit,
        "quantidade":     quantidade,
        "obs":            obs_prod,
        "icms_perc":      icms_perc,
        "ipi_perc":       ipi_perc,
    }

def _atualizar_estatisticas_produto(codigo: str, valor_brl: float):
    """Atualiza preço médio e contadores do produto após compra salva."""
    if not codigo:
        return
    prods, idx, p = _buscar_produto_por_codigo(codigo)
    if idx is None:
        return
    qtd_ant = prods[idx].get("total_compras", 0)
    preco_ant = prods[idx].get("preco_medio", 0.0)
    # Média ponderada simples do valor unitário (usando valor_brl como referência)
    prods[idx]["total_compras"]   = qtd_ant + 1
    prods[idx]["valor_total_brl"] = prods[idx].get("valor_total_brl", 0.0) + valor_brl
    salvar_produtos(prods)

# ─────────────────────────────────────────────
#  PRODUTOS — LISTAR / BUSCAR / EDITAR
# ─────────────────────────────────────────────

def listar_produtos(mostrar_inativos=False):
    prods = carregar_produtos()
    lista = prods if mostrar_inativos else [p for p in prods if p.get("ativo", True)]
    if not lista:
        print("\n  Nenhum produto cadastrado.")
        return
    linha()
    print(f"  {'CÓD':<12} {'NOME':<35} {'UNID':<6} {'CATEG.':<22} {'PREÇO MÉD.':>11} {'COMPRAS':>7}")
    linha()
    for p in lista:
        status_str = "" if p.get("ativo", True) else " [inativo]"
        pm = f"R$ {p['preco_medio']:.2f}" if p.get("preco_medio") else "—"
        print(f"  {p['codigo']:<12} {(p['nome'] + status_str)[:34]:<35} "
              f"{p.get('unidade',''):<6} "
              f"{p.get('categoria','')[:21]:<22} "
              f"{pm:>11} "
              f"{p.get('total_compras',0):>7}")
    linha()
    print(f"  Total: {len(lista)} produto(s)")

def buscar_produto():
    titulo("BUSCAR PRODUTO")
    termo = input_texto("  Buscar (nome, código, marca, NCM): ").lower()
    prods = carregar_produtos()
    resultados = [
        p for p in prods
        if termo in p["nome"].lower()
        or termo in p.get("descricao", "").lower()
        or termo in p["codigo"].lower()
        or termo in p.get("marca", "").lower()
        or termo in p.get("ncm", "").lower()
        or termo in p.get("ean", "").lower()
    ]
    if not resultados:
        print(f"\n  Nenhum resultado para '{termo}'.")
        return
    print(f"\n  {len(resultados)} produto(s) encontrado(s):")
    for p in resultados:
        _exibir_ficha_produto(p)

def editar_produto():
    titulo("EDITAR PRODUTO")
    listar_produtos()
    prods = carregar_produtos()
    if not prods:
        return

    cod = input_texto("\n  Código do produto a editar: ").upper()
    prods_all, idx, p = _buscar_produto_por_codigo(cod)
    if idx is None:
        print(f"  ⚠  Produto '{cod}' não encontrado.")
        return

    _exibir_ficha_produto(p)
    print("\n  O que deseja editar?")
    print("  [1]  Nome")
    print("  [2]  Descrição")
    print("  [3]  Marca")
    print("  [4]  Modelo / Referência")
    print("  [5]  Categoria")
    print("  [6]  Unidade de medida")
    print("  [7]  NCM")
    print("  [8]  EAN / GTIN")
    print("  [9]  ICMS padrão (%)")
    print("  [10] IPI padrão (%)")
    print("  [11] Preço médio de compra")
    print("  [12] Estoque mínimo")
    print("  [13] Observações")
    print("  [14] Inativar / Reativar produto")
    print("  [0]  Cancelar")
    op = input("  Opção: ").strip()

    campo_texto = {
        "1":  ("nome",      "Nome: ",            True),
        "2":  ("descricao", "Descrição: ",        False),
        "3":  ("marca",     "Marca: ",            False),
        "4":  ("modelo",    "Modelo / Ref.: ",    False),
        "7":  ("ncm",       "NCM: ",              False),
        "8":  ("ean",       "EAN / GTIN: ",       False),
        "13": ("obs",       "Observações: ",      False),
    }
    campo_float = {
        "9":  ("icms_padrao",    "ICMS padrão (%): "),
        "10": ("ipi_padrao",     "IPI padrão  (%): "),
        "11": ("preco_medio",    "Preço médio (R$): "),
        "12": ("estoque_minimo", "Estoque mínimo: "),
    }

    if op in campo_texto:
        campo, prompt, obrig = campo_texto[op]
        prods_all[idx][campo] = input_texto(f"  {prompt}", obrigatorio=obrig)
        salvar_produtos(prods_all)
        print("  ✔  Campo atualizado.")

    elif op in campo_float:
        campo, prompt = campo_float[op]
        prods_all[idx][campo] = input_float(f"  {prompt}")
        salvar_produtos(prods_all)
        print("  ✔  Campo atualizado.")

    elif op == "5":
        print("\n  Categoria:")
        _, categoria = input_menu(CATEGORIAS_PRODUTO)
        if categoria == "Outro":
            categoria = input_texto("  Descreva a categoria: ")
        prods_all[idx]["categoria"] = categoria
        salvar_produtos(prods_all)
        print("  ✔  Categoria atualizada.")

    elif op == "6":
        print("\n  Unidade de medida:")
        _, unidade_raw = input_menu(UNIDADES_MEDIDA)
        if unidade_raw == "Outro":
            unidade = input_texto("  Descreva a unidade: ")
        else:
            unidade = unidade_raw.split()[0]
        prods_all[idx]["unidade"] = unidade
        salvar_produtos(prods_all)
        print("  ✔  Unidade atualizada.")

    elif op == "14":
        atual = prods_all[idx].get("ativo", True)
        acao  = "Reativar" if not atual else "Inativar"
        if input_sim_nao(f"  {acao} produto '{p['nome']}'? (s/n): ") == "s":
            prods_all[idx]["ativo"] = not atual
            salvar_produtos(prods_all)
            print(f"  ✔  Produto {'reativado' if not atual else 'inativado'}.")

    elif op != "0":
        print("  ⚠  Opção inválida.")

# ─────────────────────────────────────────────
#  MENU DE PRODUTOS
# ─────────────────────────────────────────────

def menu_produtos():
    while True:
        titulo("GESTÃO DE PRODUTOS")
        print("  [1] Listar produtos ativos")
        print("  [2] Cadastrar novo produto")
        print("  [3] Buscar produto")
        print("  [4] Editar produto")
        print("  [5] Listar todos (incluindo inativos)")
        print("  [0] Voltar")
        linha()
        op = input("  Opção: ").strip()
        if   op == "1": listar_produtos()
        elif op == "2": cadastrar_produto()
        elif op == "3": buscar_produto()
        elif op == "4": editar_produto()
        elif op == "5": listar_produtos(mostrar_inativos=True)
        elif op == "0": break
        else:           print("  ⚠  Opção inválida.")

# ─────────────────────────────────────────────
#  NOVA COMPRA
# ─────────────────────────────────────────────

def nova_compra():
    titulo("NOVA COMPRA")
    hoje = datetime.now()

    # Número do pedido
    num_pedido = gerar_numero_pedido()
    print(f"\n  Número do pedido gerado: {num_pedido}")
    alt = input("  Deseja usar outro número? (ENTER para confirmar ou digite): ").strip()
    if alt:
        num_pedido = alt

    # ── Fornecedor (novo fluxo com cadastro) ──
    fornecedor, cnpj_cpf, cod_fornecedor = selecionar_ou_cadastrar_fornecedor()

    nota_fiscal = input_texto("\nNº Nota Fiscal (ENTER para pular): ", obrigatorio=False)

    # Datas
    print()
    data_compra_str, data_compra_obj = input_data_opcional("Data da compra", hoje)
    print()
    prazo_dias_str, data_entrega_str = input_prazo_entrega(data_compra_obj)
    print()
    data_faturamento_str, _ = input_data_opcional("Data de faturamento", hoje)

    # Pagamento
    cod_pagamento, modo_pagamento = input_pagamento()
    parcelas, vencimentos = input_parcelas(modo_pagamento)

    # Centro de custo
    print("\n  Centro de custo:")
    cod_cc, centro_custo = input_menu(CENTROS_CUSTO)
    if centro_custo == "Outro":
        centro_custo = input_texto("  Descreva o centro de custo: ")

    # Moeda
    print("\n  Moeda:")
    cod_moeda, (sigla_moeda, simbolo_moeda) = input_menu(MOEDAS)
    cotacao = 1.0
    if sigla_moeda != "BRL":
        cotacao = input_float(f"  Cotação do {sigla_moeda} em R$: ", permite_zero=False)
        print(f"  ✔  1 {sigla_moeda} = R$ {cotacao:.4f}")

    # Status nasce sempre como Pendente
    status = "Pendente"

    # Frete
    frete = input_float(f"\nFrete ({simbolo_moeda}): ")
    frete_brl = frete * cotacao

    # Observação geral
    obs_geral = input_texto("\nObservações gerais (ENTER para pular): ", obrigatorio=False)

    # ── Produtos ──
    produtos = []
    codigos_produto_cadastrado = []  # para atualizar estatísticas depois
    total_produtos = 0.0

    while True:
        titulo("ADICIONANDO PRODUTO")
        item = selecionar_ou_cadastrar_produto(simbolo_moeda)

        codigo     = item["codigo"]
        nome       = item["nome"]
        valor_unit = item["valor_unit"]
        quantidade = item["quantidade"]
        obs_prod   = item["obs"]
        icms_perc  = item["icms_perc"]
        ipi_perc   = item["ipi_perc"]

        icms_valor   = (valor_unit * quantidade) * (icms_perc / 100)
        ipi_valor    = (valor_unit * quantidade) * (ipi_perc / 100)
        desconto     = input_desconto(valor_unit * quantidade)
        subtotal     = (valor_unit * quantidade) + icms_valor + ipi_valor - desconto
        subtotal_brl = subtotal * cotacao

        produtos.append({
            "codigo_produto": item.get("codigo_produto", ""),
            "codigo":         codigo,
            "nome":           nome,
            "valor_unit":     valor_unit,
            "quantidade":     quantidade,
            "icms_perc":      icms_perc,
            "icms_valor":     icms_valor,
            "ipi_perc":       ipi_perc,
            "ipi_valor":      ipi_valor,
            "desconto":       desconto,
            "subtotal":       subtotal,
            "subtotal_brl":   subtotal_brl,
            "obs":            obs_prod,
        })
        codigos_produto_cadastrado.append(item.get("codigo_produto", ""))
        total_produtos += subtotal

        print(f"\n  ✔  Subtotal do item: {simbolo_moeda} {subtotal:.2f}", end="")
        if sigla_moeda != "BRL":
            print(f"  (R$ {subtotal_brl:.2f})", end="")
        print()

        if input_sim_nao("  Deseja editar este item? (s/n): ") == "s":
            total_produtos -= subtotal
            produtos.pop()
            codigos_produto_cadastrado.pop()
            print("  ↩  Refaça o preenchimento do item:")
            continue

        if input_sim_nao("  Adicionar mais itens? (s/n): ") != "s":
            break

    # Desconto geral
    titulo("DESCONTO GERAL")
    print(f"  Subtotal dos produtos: {simbolo_moeda} {total_produtos:.2f}")
    desc_geral = input_desconto(total_produtos)
    desc_geral_brl = desc_geral * cotacao

    total_final     = total_produtos - desc_geral + frete
    total_final_brl = total_final * cotacao

    # ── Resumo e confirmação ──
    titulo("RESUMO FINAL — CONFIRME OS DADOS")
    print(f"  Pedido           : {num_pedido}")
    print(f"  Fornecedor       : {fornecedor}", end="")
    if cod_fornecedor: print(f"  [{cod_fornecedor}]", end="")
    print()
    if cnpj_cpf:    print(f"  CNPJ/CPF         : {cnpj_cpf}")
    if nota_fiscal: print(f"  Nota Fiscal      : {nota_fiscal}")
    print(f"  Data compra      : {data_compra_str}")
    print(f"  Data faturamento : {data_faturamento_str}")
    print(f"  Prazo entrega    : {prazo_dias_str}  (previsão: {data_entrega_str})")
    print(f"  Pagamento        : [{cod_pagamento}] {modo_pagamento}", end="")
    if parcelas > 1:
        print(f"  {parcelas}x  →  Venc.: {', '.join(vencimentos)}", end="")
    print()
    print(f"  Centro de custo  : {centro_custo}")
    print(f"  Moeda            : {sigla_moeda}", end="")
    if sigla_moeda != "BRL":
        print(f"  (cotação R$ {cotacao:.4f})", end="")
    print()
    if obs_geral: print(f"  Observações      : {obs_geral}")
    linha()
    for i, p in enumerate(produtos, 1):
        print(f"  [{i}] {p['codigo']} — {p['nome']}")
        print(f"       Qtd: {p['quantidade']}  |  Unit: {simbolo_moeda} {p['valor_unit']:.2f}"
              f"  |  ICMS: {p['icms_perc']}%  |  IPI: {p['ipi_perc']}%"
              f"  |  Desc: {simbolo_moeda} {p['desconto']:.2f}"
              f"  |  Subtotal: {simbolo_moeda} {p['subtotal']:.2f}")
        if p['obs']:
            print(f"       Obs: {p['obs']}")
    linha()
    print(f"  Subtotal produtos : {simbolo_moeda} {total_produtos:.2f}")
    print(f"  Desconto geral    : {simbolo_moeda} {desc_geral:.2f}")
    print(f"  Frete             : {simbolo_moeda} {frete:.2f}")
    print(f"  TOTAL FINAL       : {simbolo_moeda} {total_final:.2f}", end="")
    if sigla_moeda != "BRL":
        print(f"  =  R$ {total_final_brl:.2f}", end="")
    print()
    linha()

    if input_sim_nao("\n  Confirmar e salvar esta compra? (s/n): ") != "s":
        print("  ✖  Compra cancelada. Voltando ao menu.")
        return

    compra = {
        "num_pedido":        num_pedido,
        "fornecedor":        fornecedor,
        "cod_fornecedor":    cod_fornecedor or "",
        "cnpj_cpf":          cnpj_cpf,
        "nota_fiscal":       nota_fiscal,
        "data_compra":       data_compra_str,
        "data_faturamento":  data_faturamento_str,
        "prazo_entrega":     prazo_dias_str,
        "data_entrega_prev": data_entrega_str,
        "data_recebimento":  "",
        "pagamento":         f"[{cod_pagamento}] {modo_pagamento}",
        "parcelas":          parcelas,
        "vencimentos":       vencimentos,
        "centro_custo":      centro_custo,
        "status":            status,
        "moeda":             sigla_moeda,
        "cotacao_brl":       cotacao,
        "frete":             frete,
        "frete_brl":         frete_brl,
        "obs_geral":         obs_geral,
        "produtos":          produtos,
        "total_produtos":    total_produtos,
        "desc_geral":        desc_geral,
        "total_final":       total_final,
        "total_final_brl":   total_final_brl,
        "data_registro":     datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "entrega":           {"status_entrega": "Aguardando envio", "historico_status": []},
    }

    salvar_historico(compra)
    salvar_txt(compra, simbolo_moeda)
    salvar_csv_individual(compra, simbolo_moeda)
    atualizar_csv_geral(compra, simbolo_moeda)

    # Atualiza estatísticas do fornecedor cadastrado
    if cod_fornecedor:
        _atualizar_estatisticas_fornecedor(cod_fornecedor, total_final_brl)

    # Atualiza estatísticas dos produtos cadastrados
    for cod_prod, prod in zip(codigos_produto_cadastrado, produtos):
        if cod_prod:
            _atualizar_estatisticas_produto(cod_prod, prod["subtotal_brl"])

    print(f"\n  ✔  Compra {num_pedido} registrada com sucesso!")

    if input_sim_nao("  Deseja gerar o PDF desta compra agora? (s/n): ") == "s":
        imprimir_ou_gerar_pdf(compra, simbolo_moeda)

# ─────────────────────────────────────────────
#  SALVAR TXT
# ─────────────────────────────────────────────

def salvar_txt(c, sim):
    nome = DIR_TXT / f"{c['num_pedido']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(nome, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("         RELATÓRIO DE COMPRA\n")
        f.write("=" * 50 + "\n")
        f.write(f"Pedido            : {c['num_pedido']}\n")
        f.write(f"Registro          : {c['data_registro']}\n")
        f.write(f"Status            : {c['status']}\n")
        f.write("-" * 50 + "\n")
        f.write(f"Fornecedor        : {c['fornecedor']}\n")
        if c.get('cod_fornecedor'): f.write(f"Cód. Fornecedor   : {c['cod_fornecedor']}\n")
        if c['cnpj_cpf']:    f.write(f"CNPJ/CPF          : {c['cnpj_cpf']}\n")
        if c['nota_fiscal']: f.write(f"Nota Fiscal       : {c['nota_fiscal']}\n")
        f.write(f"Data compra       : {c['data_compra']}\n")
        f.write(f"Data faturamento  : {c['data_faturamento']}\n")
        f.write(f"Prazo entrega     : {c['prazo_entrega']}  (previsão: {c['data_entrega_prev']})\n")
        if c['data_recebimento']: f.write(f"Data recebimento  : {c['data_recebimento']}\n")
        f.write(f"Pagamento         : {c['pagamento']}\n")
        if c['parcelas'] > 1:
            f.write(f"Parcelas          : {c['parcelas']}x  →  {', '.join(c['vencimentos'])}\n")
        f.write(f"Centro de custo   : {c['centro_custo']}\n")
        f.write(f"Moeda             : {c['moeda']}")
        if c['moeda'] != "BRL": f.write(f"  (cotação R$ {c['cotacao_brl']:.4f})")
        f.write("\n")
        if c['obs_geral']: f.write(f"Observações       : {c['obs_geral']}\n")
        f.write("-" * 50 + "\n\n")
        for p in c['produtos']:
            f.write(f"  Código     : {p['codigo']}\n")
            f.write(f"  Produto    : {p['nome']}\n")
            f.write(f"  Quantidade : {p['quantidade']}\n")
            f.write(f"  Valor unit.: {sim} {p['valor_unit']:.2f}\n")
            f.write(f"  ICMS       : {p['icms_perc']}%  | {sim} {p['icms_valor']:.2f}\n")
            f.write(f"  IPI        : {p['ipi_perc']}%   | {sim} {p['ipi_valor']:.2f}\n")
            f.write(f"  Desconto   : {sim} {p['desconto']:.2f}\n")
            f.write(f"  Subtotal   : {sim} {p['subtotal']:.2f}")
            if c['moeda'] != "BRL": f.write(f"  (R$ {p['subtotal_brl']:.2f})")
            f.write("\n")
            if p['obs']: f.write(f"  Obs        : {p['obs']}\n")
            f.write("  " + "-" * 46 + "\n")
        f.write(f"\nSubtotal produtos : {sim} {c['total_produtos']:.2f}\n")
        f.write(f"Desconto geral    : {sim} {c['desc_geral']:.2f}\n")
        f.write(f"Frete             : {sim} {c['frete']:.2f}\n")
        f.write(f"TOTAL FINAL       : {sim} {c['total_final']:.2f}")
        if c['moeda'] != "BRL": f.write(f"  =  R$ {c['total_final_brl']:.2f}")
        f.write("\n" + "=" * 50 + "\n")
    print(f"  📄 TXT: {nome}")

# ─────────────────────────────────────────────
#  GERAR PDF
# ─────────────────────────────────────────────

def gerar_pdf(c, sim, caminho_destino=None):
    """
    Gera PDF formatado do pedido de compra.
    Retorna o Path do arquivo gerado, ou None em caso de erro.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    except ImportError:
        print("  ⚠  reportlab não instalado. Execute: pip install reportlab")
        return None

    DIR_PDF = DIR_BASE / "pdf"
    DIR_PDF.mkdir(parents=True, exist_ok=True)

    if caminho_destino is None:
        caminho_destino = DIR_PDF / f"{c['num_pedido']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(caminho_destino),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    W = A4[0] - 30 * mm  # largura útil
    estilos = getSampleStyleSheet()

    # ── Estilos customizados ──
    titulo_doc = ParagraphStyle(
        "titulo_doc", parent=estilos["Heading1"],
        fontSize=16, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2, alignment=TA_CENTER,
    )
    subtitulo_doc = ParagraphStyle(
        "subtitulo_doc", parent=estilos["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"),
        spaceAfter=8, alignment=TA_CENTER,
    )
    secao = ParagraphStyle(
        "secao", parent=estilos["Heading2"],
        fontSize=9, textColor=colors.white,
        spaceAfter=0, spaceBefore=10,
        backColor=colors.HexColor("#1a1a2e"),
        leftIndent=4, rightIndent=4,
    )
    label = ParagraphStyle(
        "label", parent=estilos["Normal"],
        fontSize=8, textColor=colors.HexColor("#555555"),
    )
    valor = ParagraphStyle(
        "valor", parent=estilos["Normal"],
        fontSize=9, textColor=colors.HexColor("#1a1a2e"),
    )
    valor_neg = ParagraphStyle(
        "valor_neg", parent=estilos["Normal"],
        fontSize=9, textColor=colors.HexColor("#c0392b"),
    )
    rodape_est = ParagraphStyle(
        "rodape_est", parent=estilos["Normal"],
        fontSize=7, textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
    )

    def campo(lb, vl, estilo_val=None):
        return [Paragraph(lb, label), Paragraph(str(vl) if vl else "—", estilo_val or valor)]

    story = []

    # ── Cabeçalho ──
    story.append(Paragraph("PEDIDO DE COMPRA", titulo_doc))
    story.append(Paragraph(
        f"Nº {c['num_pedido']}  |  Emitido em: {c['data_registro']}  |  Status: {c['status']}",
        subtitulo_doc,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e"), spaceAfter=6))

    # ── Seção: Fornecedor ──
    story.append(Paragraph("  FORNECEDOR", secao))
    story.append(Spacer(1, 3))
    dados_forn = [
        [Paragraph("Fornecedor", label),   Paragraph(c["fornecedor"], valor),
         Paragraph("Cód.", label),          Paragraph(c.get("cod_fornecedor") or "—", valor)],
        [Paragraph("CNPJ/CPF", label),      Paragraph(c.get("cnpj_cpf") or "—", valor),
         Paragraph("Nota Fiscal", label),   Paragraph(c.get("nota_fiscal") or "—", valor)],
    ]
    t_forn = Table(dados_forn, colWidths=[28*mm, W*0.38, 20*mm, W*0.28])
    t_forn.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f7f7f7"), colors.white]),
        ("GRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(t_forn)

    # ── Seção: Datas e Condições ──
    story.append(Paragraph("  DATAS E CONDIÇÕES", secao))
    story.append(Spacer(1, 3))

    parcelas_str = (
        f"{c['parcelas']}x  →  {', '.join(c['vencimentos'])}"
        if c.get("parcelas", 1) > 1 else "À vista"
    )
    moeda_str = c["moeda"]
    if c["moeda"] != "BRL":
        moeda_str += f"  (cotação R$ {c.get('cotacao_brl', 1):.4f})"

    dados_cond = [
        [Paragraph("Data da compra", label),    Paragraph(c["data_compra"], valor),
         Paragraph("Data faturamento", label),  Paragraph(c["data_faturamento"], valor)],
        [Paragraph("Prazo de entrega", label),  Paragraph(c["prazo_entrega"], valor),
         Paragraph("Previsão entrega", label),  Paragraph(c["data_entrega_prev"], valor)],
        [Paragraph("Pagamento", label),         Paragraph(c["pagamento"], valor),
         Paragraph("Parcelas", label),          Paragraph(parcelas_str, valor)],
        [Paragraph("Centro de custo", label),   Paragraph(c["centro_custo"], valor),
         Paragraph("Moeda", label),             Paragraph(moeda_str, valor)],
    ]
    if c.get("data_recebimento"):
        dados_cond.append([
            Paragraph("Data recebimento", label), Paragraph(c["data_recebimento"], valor),
            Paragraph("", label), Paragraph("", valor),
        ])
    if c.get("obs_geral"):
        dados_cond.append([
            Paragraph("Observações", label),
            Paragraph(c["obs_geral"], valor),
            Paragraph("", label), Paragraph("", valor),
        ])

    col_w = [36*mm, W*0.32, 36*mm, W*0.28]
    t_cond = Table(dados_cond, colWidths=col_w)
    t_cond.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f7f7f7"), colors.white]),
        ("GRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("SPAN", (1, -1), (3, -1)) if c.get("obs_geral") else ("VALIGN", (0,0),(0,0),"TOP"),
    ]))
    story.append(t_cond)

    # ── Seção: Itens ──
    story.append(Paragraph("  ITENS DO PEDIDO", secao))
    story.append(Spacer(1, 3))

    cab_itens = [
        Paragraph("Código", label),
        Paragraph("Produto", label),
        Paragraph("Qtd", label),
        Paragraph(f"Unit. ({sim})", label),
        Paragraph("ICMS%", label),
        Paragraph("IPI%", label),
        Paragraph(f"Desc. ({sim})", label),
        Paragraph(f"Subtotal ({sim})", label),
    ]
    linhas_itens = [cab_itens]
    for p in c["produtos"]:
        linhas_itens.append([
            Paragraph(p["codigo"], valor),
            Paragraph(p["nome"], valor),
            Paragraph(str(p["quantidade"]), valor),
            Paragraph(f"{p['valor_unit']:.2f}", valor),
            Paragraph(f"{p['icms_perc']:.1f}%", valor),
            Paragraph(f"{p['ipi_perc']:.1f}%", valor),
            Paragraph(f"{p['desconto']:.2f}", valor),
            Paragraph(f"{p['subtotal']:.2f}", valor),
        ])

    cw_itens = [22*mm, W*0.30, 12*mm, 20*mm, 14*mm, 12*mm, 20*mm, 22*mm]
    t_itens = Table(linhas_itens, colWidths=cw_itens, repeatRows=1)
    t_itens.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#e8e8f0")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("ALIGN",       (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(t_itens)

    # ── Seção: Totais ──
    story.append(Spacer(1, 4))
    linhas_tot = [
        ["Subtotal dos produtos", f"{sim} {c['total_produtos']:.2f}"],
        ["Desconto geral",        f"- {sim} {c['desc_geral']:.2f}"],
        ["Frete",                 f"{sim} {c['frete']:.2f}"],
    ]
    if c["moeda"] != "BRL":
        linhas_tot.append(["TOTAL FINAL",  f"{sim} {c['total_final']:.2f}  =  R$ {c['total_final_brl']:.2f}"])
    else:
        linhas_tot.append(["TOTAL FINAL",  f"R$ {c['total_final']:.2f}"])

    est_tot = [
        ParagraphStyle("tl", parent=estilos["Normal"], fontSize=8,
                       textColor=colors.HexColor("#555555"), alignment=TA_RIGHT),
        ParagraphStyle("tv", parent=estilos["Normal"], fontSize=8,
                       textColor=colors.HexColor("#1a1a2e"), alignment=TA_RIGHT),
    ]
    est_tf_l = ParagraphStyle("tfl", parent=estilos["Normal"], fontSize=10,
                               textColor=colors.white, alignment=TA_RIGHT, fontName="Helvetica-Bold")
    est_tf_v = ParagraphStyle("tfv", parent=estilos["Normal"], fontSize=10,
                               textColor=colors.white, alignment=TA_RIGHT, fontName="Helvetica-Bold")

    rows_tot = []
    for i, (lb, vl) in enumerate(linhas_tot[:-1]):
        rows_tot.append([Paragraph(lb, est_tot[0]), Paragraph(vl, est_tot[1])])
    rows_tot.append([Paragraph(linhas_tot[-1][0], est_tf_l), Paragraph(linhas_tot[-1][1], est_tf_v)])

    t_tot = Table(rows_tot, colWidths=[W - 60*mm, 60*mm], hAlign="RIGHT")
    t_tot.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -2), [colors.HexColor("#f0f0f8"), colors.white]),
        ("BACKGROUND",   (0, -1), (-1, -1), colors.HexColor("#1a1a2e")),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("LINEABOVE",    (0, -1), (-1, -1), 1.5, colors.HexColor("#1a1a2e")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(t_tot)

    # ── Rodapé ──
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4))
    story.append(Paragraph(
        f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  |  "
        f"Pedido {c['num_pedido']}",
        rodape_est,
    ))

    doc.build(story)
    return caminho_destino


def imprimir_ou_gerar_pdf(compra, simbolo_moeda="R$"):
    """Menu pós-geração: gera PDF e oferece opção de abrir."""
    caminho = gerar_pdf(compra, simbolo_moeda)
    if caminho:
        print(f"  📄 PDF: {caminho}")
        return caminho
    return None


# ─────────────────────────────────────────────
#  SALVAR CSV INDIVIDUAL
# ─────────────────────────────────────────────

def salvar_csv_individual(c, sim):
    nome = DIR_CSV / f"{c['num_pedido']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(nome, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Pedido", "Fornecedor", "Cód. Fornecedor", "CNPJ/CPF", "Nota Fiscal",
                    "Data Compra", "Data Faturamento", "Prazo", "Previsão Entrega",
                    "Pagamento", "Parcelas", "Vencimentos", "Centro Custo",
                    "Status", "Moeda", "Cotação BRL", "Frete", "Obs Geral"])
        w.writerow([c['num_pedido'], c['fornecedor'], c.get('cod_fornecedor',''), c['cnpj_cpf'], c['nota_fiscal'],
                    c['data_compra'], c['data_faturamento'], c['prazo_entrega'], c['data_entrega_prev'],
                    c['pagamento'], c['parcelas'], "; ".join(c['vencimentos']), c['centro_custo'],
                    c['status'], c['moeda'], c['cotacao_brl'], c['frete'], c['obs_geral']])
        w.writerow([])
        w.writerow(["Código", "Produto", "Valor Unit.", "Qtd",
                    "ICMS%", "ICMS Valor", "IPI%", "IPI Valor",
                    "Desconto", "Subtotal", "Subtotal (BRL)", "Obs"])
        for p in c['produtos']:
            w.writerow([p['codigo'], p['nome'], p['valor_unit'], p['quantidade'],
                        p['icms_perc'], p['icms_valor'], p['ipi_perc'], p['ipi_valor'],
                        p['desconto'], p['subtotal'], p['subtotal_brl'], p['obs']])
        w.writerow([])
        w.writerow(["", "", "", "", "", "", "", "", "Subtotal", c['total_produtos'], "", ""])
        w.writerow(["", "", "", "", "", "", "", "", "Desc. geral", c['desc_geral'], "", ""])
        w.writerow(["", "", "", "", "", "", "", "", "Frete", c['frete'], "", ""])
        w.writerow(["", "", "", "", "", "", "", "", "TOTAL FINAL", c['total_final'], c['total_final_brl'], ""])
    print(f"  📊 CSV: {nome}")

# ─────────────────────────────────────────────
#  CSV GERAL ACUMULADO
# ─────────────────────────────────────────────

def atualizar_csv_geral(c, sim):
    cabecalho = ["Pedido", "Data Compra", "Fornecedor", "Cód. Fornecedor", "CNPJ/CPF", "Nota Fiscal",
                 "Status", "Pagamento", "Centro Custo", "Moeda", "Total Final", "Total Final BRL",
                 "Data Registro"]
    existe = HISTORICO_CSV.exists()
    with open(HISTORICO_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not existe:
            w.writerow(cabecalho)
        w.writerow([c['num_pedido'], c['data_compra'], c['fornecedor'], c.get('cod_fornecedor',''),
                    c['cnpj_cpf'], c['nota_fiscal'], c['status'], c['pagamento'], c['centro_custo'],
                    c['moeda'], c['total_final'], c['total_final_brl'], c['data_registro']])
    print(f"  📋 Histórico geral: {HISTORICO_CSV}")

# ─────────────────────────────────────────────
#  CONSULTAR HISTÓRICO
# ─────────────────────────────────────────────

def consultar_historico():
    historico = carregar_historico()
    if not historico:
        print("\n  Nenhuma compra registrada ainda.")
        return

    titulo("CONSULTAR HISTÓRICO")
    print("  [1] Listar todas as compras")
    print("  [2] Buscar por fornecedor")
    print("  [3] Buscar por período")
    print("  [4] Buscar por status")
    print("  [5] Relatório por fornecedor (total gasto)")
    print("  [6] Gerar PDF de um pedido")
    print("  [0] Voltar")
    op = input("  Opção: ").strip()

    if op == "1":
        listar_compras(historico)
    elif op == "2":
        termo = input_texto("  Nome do fornecedor (parcial): ").lower()
        filtrado = [c for c in historico if termo in c['fornecedor'].lower()]
        listar_compras(filtrado, f"Fornecedor contém '{termo}'")
    elif op == "3":
        print("  Período de busca:")
        data_ini_str, data_ini = input_data_obrigatoria("  Data inicial (DD/MM/AAAA): ")
        data_fim_str, data_fim = input_data_obrigatoria("  Data final   (DD/MM/AAAA): ")
        filtrado = []
        for c in historico:
            try:
                dc = datetime.strptime(c['data_compra'], "%d/%m/%Y")
                if data_ini <= dc <= data_fim:
                    filtrado.append(c)
            except:
                pass
        listar_compras(filtrado, f"Período {data_ini_str} a {data_fim_str}")
    elif op == "4":
        print("  Status:")
        for k, v in STATUS_OPCOES.items():
            print(f"    [{k}] {v}")
        cod_s = input("  Código: ").strip()
        status_busca = STATUS_OPCOES.get(cod_s, "")
        filtrado = [c for c in historico if c['status'] == status_busca]
        listar_compras(filtrado, f"Status: {status_busca}")
    elif op == "5":
        relatorio_fornecedor(historico)
    elif op == "6":
        _gerar_pdf_pedido_interativo(historico)

def _gerar_pdf_pedido_interativo(historico=None):
    """Solicita número de pedido e gera PDF. Pode ser chamada de qualquer menu."""
    if historico is None:
        historico = carregar_historico()
    if not historico:
        print("\n  Nenhum pedido registrado.")
        return
    listar_compras(historico)
    num = input_texto("\n  Número do pedido para gerar PDF: ").upper()
    _, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return
    moeda = compra.get("moeda", "BRL")
    sim   = {"BRL": "R$", "USD": "US$", "EUR": "€"}.get(moeda, "R$")
    imprimir_ou_gerar_pdf(compra, sim)

def listar_compras(lista, titulo_filtro="Todas"):
    if not lista:
        print(f"\n  Nenhuma compra encontrada ({titulo_filtro}).")
        return
    linha()
    print(f"  Compras — {titulo_filtro}  ({len(lista)} registro(s))")
    linha()
    for c in lista:
        moeda_info = c['moeda']
        if c['moeda'] != "BRL":
            moeda_info += f" (R$ {c['total_final_brl']:.2f})"
        print(f"  {c['num_pedido']} | {c['data_compra']} | {c['fornecedor']:<25} | "
              f"{c['status']:<10} | {c['moeda']} {c['total_final']:.2f} {moeda_info}")
    linha()
    total_brl = sum(c.get('total_final_brl', c['total_final']) for c in lista)
    print(f"  Total em R$: R$ {total_brl:.2f}")

def relatorio_fornecedor(historico):
    titulo("TOTAL GASTO POR FORNECEDOR")
    resumo = {}
    for c in historico:
        f = c['fornecedor']
        resumo.setdefault(f, {"qtd": 0, "total_brl": 0.0})
        resumo[f]["qtd"] += 1
        resumo[f]["total_brl"] += c.get('total_final_brl', c['total_final'])
    for forn, dados in sorted(resumo.items(), key=lambda x: -x[1]['total_brl']):
        print(f"  {forn:<30} | {dados['qtd']} compra(s) | R$ {dados['total_brl']:.2f}")

# ─────────────────────────────────────────────
#  ATUALIZAR STATUS / RECEBIMENTO
# ─────────────────────────────────────────────

def atualizar_compra():
    historico = carregar_historico()
    if not historico:
        print("\n  Nenhuma compra registrada.")
        return

    titulo("ATUALIZAR COMPRA")
    listar_compras(historico)
    num = input_texto("\n  Número do pedido a atualizar: ").upper()
    idx = next((i for i, c in enumerate(historico) if c['num_pedido'].upper() == num), None)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return

    c = historico[idx]
    print(f"\n  Pedido: {c['num_pedido']} — {c['fornecedor']}")
    print(f"  Status atual: {c['status']}")
    print("\n  O que deseja atualizar?")
    print("  [1] Status")
    print("  [2] Data de recebimento")
    print("  [3] Número da nota fiscal")
    print("  [4] Observações gerais")
    print("  [0] Cancelar")
    op = input("  Opção: ").strip()

    if op == "1":
        print("\n  Novo status:")
        _, novo_status = input_menu(STATUS_OPCOES)
        c['status'] = novo_status
        print(f"  ✔  Status atualizado para: {novo_status}")
    elif op == "2":
        data_str, _ = input_data_obrigatoria("  Data de recebimento (DD/MM/AAAA): ")
        c['data_recebimento'] = data_str
        if c['status'] in ("Pendente", "Aprovada"):
            c['status'] = "Recebida"
        print(f"  ✔  Recebimento registrado: {data_str}")
    elif op == "3":
        c['nota_fiscal'] = input_texto("  Número da nota fiscal: ")
        print(f"  ✔  NF atualizada.")
    elif op == "4":
        c['obs_geral'] = input_texto("  Novas observações: ", obrigatorio=False)
        print(f"  ✔  Observações atualizadas.")
    else:
        return

    atualizar_historico_compra(historico)
    print(f"  ✔  Pedido {num} salvo.")
    if input_sim_nao("  Deseja gerar PDF atualizado deste pedido? (s/n): ") == "s":
        moeda = c.get("moeda", "BRL")
        sim   = {"BRL": "R$", "USD": "US$", "EUR": "€"}.get(moeda, "R$")
        imprimir_ou_gerar_pdf(c, sim)

# ─────────────────────────────────────────────
#  PERSISTÊNCIA DE OCORRÊNCIAS
# ─────────────────────────────────────────────

def carregar_ocorrencias():
    if not OCORRENCIAS_JSON.exists():
        return []
    with open(OCORRENCIAS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_ocorrencia(ocorrencia: dict):
    lista = carregar_ocorrencias()
    lista.append(ocorrencia)
    with open(OCORRENCIAS_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def _salvar_csv_entrega(c: dict):
    """Acrescenta linha no CSV geral de entregas."""
    cabecalho = [
        "Pedido", "Fornecedor", "Status compra", "Status entrega",
        "Transportadora", "Código rastreio", "Data prev. entrega",
        "Data recebimento", "Qtd itens recebidos", "Qtd itens pedidos",
        "Observação entrega",
    ]
    ent = c.get("entrega", {})
    linha_dados = [
        c["num_pedido"],
        c["fornecedor"],
        c["status"],
        ent.get("status_entrega", ""),
        ent.get("transportadora", ""),
        ent.get("codigo_rastreio", ""),
        c.get("data_entrega_prev", ""),
        c.get("data_recebimento", ""),
        ent.get("qtd_recebida", ""),
        sum(p["quantidade"] for p in c.get("produtos", [])),
        ent.get("obs_entrega", ""),
    ]
    existe = ENTREGAS_CSV.exists()
    with open(ENTREGAS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not existe:
            w.writerow(cabecalho)
        w.writerow(linha_dados)

# ─────────────────────────────────────────────
#  GESTÃO DE ENTREGAS — REGISTRAR ENVIO
# ─────────────────────────────────────────────

def registrar_envio():
    titulo("REGISTRAR ENVIO / EXPEDIÇÃO")
    historico = carregar_historico()
    pendentes = [
        c for c in historico
        if c["status"] in ("Pendente", "Aprovada")
        and c.get("entrega", {}).get("status_entrega", "Aguardando envio") == "Aguardando envio"
    ]
    if not pendentes:
        print("\n  Nenhum pedido aguardando envio.")
        return

    print(f"\n  Pedidos aguardando envio ({len(pendentes)}):")
    linha()
    for c in pendentes:
        print(f"  {c['num_pedido']} | {c['data_compra']} | {c['fornecedor']:<25} | Prev: {c.get('data_entrega_prev','—')}")
    linha()

    num = input_texto("\n  Número do pedido: ").upper()
    historico_full, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return

    print("\n  Transportadora:")
    for i, t in enumerate(TRANSPORTADORAS_PADRAO, 1):
        print(f"    [{i}] {t}")
    while True:
        opc = input("  Código: ").strip()
        try:
            idx_t = int(opc) - 1
            if 0 <= idx_t < len(TRANSPORTADORAS_PADRAO):
                transportadora = TRANSPORTADORAS_PADRAO[idx_t]
                if transportadora == "Outro":
                    transportadora = input_texto("  Nome da transportadora: ")
                break
        except ValueError:
            pass
        print("  ⚠  Opção inválida.")

    codigo_rastreio = input_texto("\nCódigo de rastreio (ENTER para pular): ", obrigatorio=False)
    data_exp_str, _ = input_data_opcional("\nData de expedição", datetime.now())

    nova_prev = compra.get("data_entrega_prev", "")
    if input_sim_nao("\n  Deseja atualizar a previsão de entrega? (s/n): ") == "s":
        nova_prev, _ = input_data_obrigatoria("  Nova previsão (DD/MM/AAAA): ")

    obs = input_texto("\nObservação (ENTER para pular): ", obrigatorio=False)

    if "entrega" not in compra:
        compra["entrega"] = {}
    compra["entrega"].update({
        "transportadora":   transportadora,
        "codigo_rastreio":  codigo_rastreio,
        "data_expedicao":   data_exp_str,
        "status_entrega":   "Em trânsito",
        "obs_entrega":      obs,
        "historico_status": [
            {"status": "Em trânsito", "data": data_exp_str,
             "obs": f"Expedido por {transportadora}"}
        ],
    })
    compra["data_entrega_prev"] = nova_prev
    if compra["status"] == "Pendente":
        compra["status"] = "Aprovada"

    atualizar_historico_compra(historico_full)
    _salvar_csv_entrega(compra)
    print(f"\n  ✔  Envio registrado para {num} — {transportadora}"
          + (f" | Rastreio: {codigo_rastreio}" if codigo_rastreio else ""))

# ─────────────────────────────────────────────
#  GESTÃO DE ENTREGAS — ATUALIZAR STATUS
# ─────────────────────────────────────────────

def atualizar_status_entrega():
    titulo("ATUALIZAR STATUS DE ENTREGA")
    historico = carregar_historico()
    em_transito = [
        c for c in historico
        if c.get("entrega", {}).get("status_entrega", "") in
           ("Em trânsito", "Saiu para entrega", "Aguardando envio", "Entregue parcialmente")
    ]
    if not em_transito:
        print("\n  Nenhum pedido com entrega em andamento.")
        return

    print(f"\n  Entregas em andamento ({len(em_transito)}):")
    linha()
    for c in em_transito:
        ent = c.get("entrega", {})
        print(f"  {c['num_pedido']} | {c['fornecedor']:<25} | "
              f"{ent.get('status_entrega','—'):<25} | Prev: {c.get('data_entrega_prev','—')}")
    linha()

    num = input_texto("\n  Número do pedido: ").upper()
    historico_full, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return

    print("\n  Novo status de entrega:")
    _, novo_status = input_menu(STATUS_ENTREGA)
    data_str, _ = input_data_opcional("\nData do evento", datetime.now())
    obs = input_texto("Observação (ENTER para pular): ", obrigatorio=False)

    if "entrega" not in compra:
        compra["entrega"] = {}
    if "historico_status" not in compra["entrega"]:
        compra["entrega"]["historico_status"] = []

    compra["entrega"]["historico_status"].append({
        "status": novo_status, "data": data_str, "obs": obs,
    })
    compra["entrega"]["status_entrega"] = novo_status

    if novo_status == "Entregue":
        compra["status"] = "Recebida"
        compra["data_recebimento"] = data_str
    elif novo_status == "Cancelado":
        compra["status"] = "Cancelada"

    atualizar_historico_compra(historico_full)
    _salvar_csv_entrega(compra)
    print(f"\n  ✔  Status atualizado para '{novo_status}' em {data_str}.")

# ─────────────────────────────────────────────
#  GESTÃO DE ENTREGAS — CONFIRMAR RECEBIMENTO
# ─────────────────────────────────────────────

def confirmar_recebimento():
    titulo("CONFIRMAR RECEBIMENTO")
    historico = carregar_historico()
    aguardando = [
        c for c in historico
        if c.get("entrega", {}).get("status_entrega", "") in
           ("Em trânsito", "Saiu para entrega", "Entregue parcialmente", "Aguardando envio")
        or (c["status"] in ("Pendente", "Aprovada") and not c.get("data_recebimento"))
    ]
    if not aguardando:
        print("\n  Nenhum pedido aguardando confirmação de recebimento.")
        return

    print(f"\n  Pedidos aguardando recebimento ({len(aguardando)}):")
    linha()
    for c in aguardando:
        ent = c.get("entrega", {})
        print(f"  {c['num_pedido']} | {c['data_compra']} | {c['fornecedor']:<25} | "
              f"Prev: {c.get('data_entrega_prev','—')} | "
              f"Status: {ent.get('status_entrega', c['status'])}")
    linha()

    num = input_texto("\n  Número do pedido: ").upper()
    historico_full, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return

    data_rec_str, _ = input_data_opcional("\nData de recebimento", datetime.now())
    nota_fiscal = compra.get("nota_fiscal", "")
    if not nota_fiscal:
        nota_fiscal = input_texto("Nº Nota Fiscal (ENTER para pular): ", obrigatorio=False)

    print("\n  ── Conferência de itens recebidos ──")
    produtos = compra.get("produtos", [])
    conferencia = []
    total_recebido = 0
    divergencia = False

    for p in produtos:
        print(f"\n  Produto : {p['codigo']} — {p['nome']}")
        print(f"  Pedido  : {p['quantidade']} un.")
        raw = input(f"  Qtd recebida [{p['quantidade']}]: ").strip()
        if raw == "":
            qtd_rec = p["quantidade"]
        else:
            try:
                qtd_rec = int(raw)
                if qtd_rec < 0:
                    print("  ⚠  Não pode ser negativo. Usando quantidade pedida.")
                    qtd_rec = p["quantidade"]
            except ValueError:
                print("  ⚠  Inválido. Usando quantidade pedida.")
                qtd_rec = p["quantidade"]

        obs_item = ""
        if qtd_rec != p["quantidade"]:
            divergencia = True
            diff = qtd_rec - p["quantidade"]
            sinal = "a mais" if diff > 0 else "a menos"
            print(f"  ⚠  Divergência: {abs(diff)} un. {sinal}.")
            obs_item = input_texto("  Observação sobre a divergência: ", obrigatorio=False)

        conferencia.append({
            "codigo":       p["codigo"],
            "nome":         p["nome"],
            "qtd_pedida":   p["quantidade"],
            "qtd_recebida": qtd_rec,
            "divergencia":  qtd_rec != p["quantidade"],
            "obs":          obs_item,
        })
        total_recebido += qtd_rec

    obs_rec = input_texto("\nObservação geral do recebimento (ENTER para pular): ", obrigatorio=False)

    if divergencia:
        todas_ok = all(i["qtd_recebida"] >= i["qtd_pedida"] for i in conferencia)
        status_ent   = "Entregue" if todas_ok else "Entregue parcialmente"
        status_compra = "Recebida" if todas_ok else "Aprovada"
    else:
        status_ent    = "Entregue"
        status_compra = "Recebida"

    if "entrega" not in compra:
        compra["entrega"] = {}
    if "historico_status" not in compra["entrega"]:
        compra["entrega"]["historico_status"] = []

    compra["entrega"].update({
        "status_entrega": status_ent,
        "conferencia":    conferencia,
        "qtd_recebida":   total_recebido,
        "obs_entrega":    obs_rec,
    })
    compra["entrega"]["historico_status"].append({
        "status": status_ent,
        "data":   data_rec_str,
        "obs":    obs_rec or ("Com divergências" if divergencia else "Recebido conforme"),
    })
    compra["status"]           = status_compra
    compra["data_recebimento"] = data_rec_str
    if nota_fiscal:
        compra["nota_fiscal"]  = nota_fiscal

    atualizar_historico_compra(historico_full)
    _salvar_csv_entrega(compra)

    titulo("RESUMO DO RECEBIMENTO")
    print(f"  Pedido     : {compra['num_pedido']}")
    print(f"  Fornecedor : {compra['fornecedor']}")
    print(f"  Data rec.  : {data_rec_str}")
    print(f"  Status     : {status_ent}")
    if divergencia:
        print(f"\n  ⚠  Divergências encontradas:")
        for i in conferencia:
            if i["divergencia"]:
                print(f"     {i['codigo']} {i['nome']}: "
                      f"pedido {i['qtd_pedida']} | recebido {i['qtd_recebida']}"
                      + (f" — {i['obs']}" if i['obs'] else ""))
    else:
        print("\n  ✔  Todos os itens conferidos sem divergências.")

    if divergencia and input_sim_nao("\n  Deseja registrar ocorrência para as divergências? (s/n): ") == "s":
        _registrar_ocorrencia_direto(compra)

# ─────────────────────────────────────────────
#  GESTÃO DE ENTREGAS — OCORRÊNCIAS
# ─────────────────────────────────────────────

def _registrar_ocorrencia_direto(compra: dict):
    print("\n  Tipo de ocorrência:")
    _, tipo = input_menu(TIPO_OCORRENCIA)
    descricao = input_texto("  Descrição detalhada: ")
    data_str, _ = input_data_opcional("  Data da ocorrência", datetime.now())
    gravidade_map = {"1": "Baixa", "2": "Média", "3": "Alta", "4": "Crítica"}
    print("\n  Gravidade:")
    _, gravidade = input_menu(gravidade_map)
    acao = input_texto("  Ação tomada ou solicitada (ENTER para pular): ", obrigatorio=False)

    ocorrencia = {
        "num_pedido":    compra["num_pedido"],
        "fornecedor":    compra["fornecedor"],
        "tipo":          tipo,
        "descricao":     descricao,
        "data":          data_str,
        "gravidade":     gravidade,
        "acao":          acao,
        "resolvida":     False,
        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    salvar_ocorrencia(ocorrencia)
    print(f"\n  ✔  Ocorrência '{tipo}' registrada para {compra['num_pedido']}.")

def registrar_ocorrencia():
    titulo("REGISTRAR OCORRÊNCIA DE ENTREGA")
    historico = carregar_historico()
    if not historico:
        print("\n  Nenhum pedido registrado.")
        return

    linha()
    for c in historico[-15:]:
        ent = c.get("entrega", {})
        print(f"  {c['num_pedido']:<10} | {c['data_compra']} | "
              f"{c['fornecedor']:<25} | {ent.get('status_entrega', c['status'])}")
    linha()

    num = input_texto("\n  Número do pedido: ").upper()
    _, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return
    _registrar_ocorrencia_direto(compra)

def gerenciar_ocorrencias():
    titulo("GERENCIAR OCORRÊNCIAS")
    ocorrencias = carregar_ocorrencias()
    if not ocorrencias:
        print("\n  Nenhuma ocorrência registrada.")
        return

    abertas  = [o for o in ocorrencias if not o.get("resolvida")]
    fechadas = [o for o in ocorrencias if o.get("resolvida")]
    print(f"\n  Ocorrências abertas  : {len(abertas)}")
    print(f"  Ocorrências fechadas : {len(fechadas)}")
    print("\n  [1] Ver ocorrências abertas")
    print("  [2] Marcar como resolvida")
    print("  [3] Ver todas")
    print("  [0] Voltar")
    op = input("  Opção: ").strip()

    if op == "1":
        if not abertas:
            print("\n  Nenhuma ocorrência aberta."); return
        linha()
        for i, o in enumerate(abertas, 1):
            print(f"  [{i}] {o['num_pedido']} | {o['tipo']:<25} | {o['gravidade']:<8} | {o['data']}")
            print(f"       {o['descricao'][:70]}")
        linha()
    elif op == "2":
        if not abertas:
            print("\n  Nenhuma ocorrência aberta."); return
        linha()
        for i, o in enumerate(abertas, 1):
            print(f"  [{i}] {o['num_pedido']} | {o['tipo']} | {o['data']}")
        linha()
        try:
            escolha = int(input("  Número da ocorrência a resolver: ").strip()) - 1
            if 0 <= escolha < len(abertas):
                solucao = input_texto("  Descrição da solução: ")
                abertas[escolha]["resolvida"]      = True
                abertas[escolha]["solucao"]         = solucao
                abertas[escolha]["data_resolucao"]  = datetime.now().strftime("%d/%m/%Y")
                todas = abertas + fechadas
                with open(OCORRENCIAS_JSON, "w", encoding="utf-8") as f:
                    json.dump(todas, f, ensure_ascii=False, indent=2)
                print("  ✔  Ocorrência marcada como resolvida.")
            else:
                print("  ⚠  Número inválido.")
        except ValueError:
            print("  ⚠  Número inválido.")
    elif op == "3":
        linha()
        for o in ocorrencias:
            st = "✔" if o.get("resolvida") else "⚠"
            print(f"  {st} {o['num_pedido']:<10} | {o['tipo']:<25} | {o['gravidade']:<8} | {o['data']}")
        linha()

# ─────────────────────────────────────────────
#  GESTÃO DE ENTREGAS — PAINEL E TIMELINE
# ─────────────────────────────────────────────

def painel_entregas():
    titulo("PAINEL DE ENTREGAS")
    historico = carregar_historico()
    if not historico:
        print("\n  Nenhum pedido registrado.")
        return

    grupos: dict = {}
    for c in historico:
        st = c.get("entrega", {}).get("status_entrega", "Aguardando envio")
        grupos.setdefault(st, []).append(c)

    hoje = datetime.now()

    atrasados = []
    for c in historico:
        if c["status"] in ("Recebida", "Cancelada"):
            continue
        try:
            prev = datetime.strptime(c.get("data_entrega_prev", ""), "%d/%m/%Y")
            if prev < hoje:
                atrasados.append((c, (hoje - prev).days))
        except ValueError:
            pass

    if atrasados:
        print(f"\n  ⚠  PEDIDOS EM ATRASO ({len(atrasados)}):")
        linha("─", 50)
        for c, dias in sorted(atrasados, key=lambda x: -x[1]):
            ent = c.get("entrega", {})
            print(f"  {c['num_pedido']} | {c['fornecedor']:<25} | "
                  f"{dias} dia(s) de atraso | {ent.get('status_entrega', c['status'])}")
        linha("─", 50)

    proximos = []
    for c in historico:
        if c["status"] in ("Recebida", "Cancelada"):
            continue
        try:
            prev = datetime.strptime(c.get("data_entrega_prev", ""), "%d/%m/%Y")
            diff = (prev - hoje).days
            if 0 <= diff <= 3:
                proximos.append((c, diff))
        except ValueError:
            pass

    if proximos:
        print(f"\n  📅  ENTREGAS NOS PRÓXIMOS 3 DIAS ({len(proximos)}):")
        linha("─", 50)
        for c, diff in sorted(proximos, key=lambda x: x[1]):
            label = "hoje" if diff == 0 else ("amanhã" if diff == 1 else f"em {diff} dias")
            print(f"  {c['num_pedido']} | {c['fornecedor']:<25} | Prev: {c['data_entrega_prev']} ({label})")
        linha("─", 50)

    print("\n  RESUMO POR STATUS:")
    linha("─", 50)
    for st, lista in sorted(grupos.items()):
        print(f"  {st:<30} : {len(lista)} pedido(s)")
    linha("─", 50)
    print(f"  Total de pedidos: {len(historico)}")

    ocorrencias = carregar_ocorrencias()
    abertas = [o for o in ocorrencias if not o.get("resolvida")]
    if abertas:
        print(f"\n  ⚠  OCORRÊNCIAS ABERTAS: {len(abertas)}")
        for o in abertas[-5:]:
            print(f"     {o['num_pedido']} | {o['tipo']} | {o['gravidade']} | {o['data']}")
        if len(abertas) > 5:
            print(f"     ... e mais {len(abertas)-5} ocorrência(s).")

def ver_timeline():
    titulo("TIMELINE DE ENTREGA")
    num = input_texto("Número do pedido: ").upper()
    _, idx, compra = _compra_por_pedido(num)
    if idx is None:
        print(f"  ⚠  Pedido '{num}' não encontrado.")
        return

    print(f"\n  Pedido   : {compra['num_pedido']}")
    print(f"  Fornec.  : {compra['fornecedor']}")
    ent = compra.get("entrega", {})
    if ent.get("transportadora"):
        print(f"  Transp.  : {ent['transportadora']}", end="")
        if ent.get("codigo_rastreio"):
            print(f"  | Rastreio: {ent['codigo_rastreio']}", end="")
        print()
    print(f"  Status   : {ent.get('status_entrega', compra['status'])}")
    print(f"  Prev.    : {compra.get('data_entrega_prev','—')}")
    if compra.get("data_recebimento"):
        print(f"  Recebido : {compra['data_recebimento']}")

    historico_st = ent.get("historico_status", [])
    if historico_st:
        print(f"\n  ── Histórico de status ──")
        for evento in historico_st:
            sinal = "✔" if "Entregue" in evento["status"] else "○"
            obs_str = f" — {evento['obs']}" if evento.get("obs") else ""
            print(f"  {sinal}  {evento['data']:12}  {evento['status']}{obs_str}")
    else:
        print("\n  Nenhum histórico de movimentação registrado ainda.")

    if ent.get("conferencia"):
        print(f"\n  ── Conferência de itens ──")
        for item in ent["conferencia"]:
            icone = "✔" if not item["divergencia"] else "⚠"
            print(f"  {icone}  {item['codigo']:<12} {item['nome']:<30} "
                  f"Pedido: {item['qtd_pedida']:>4}  Recebido: {item['qtd_recebida']:>4}"
                  + (f"  {item['obs']}" if item['obs'] else ""))

    ocorrencias = [o for o in carregar_ocorrencias() if o["num_pedido"] == compra["num_pedido"]]
    if ocorrencias:
        print(f"\n  ── Ocorrências ({len(ocorrencias)}) ──")
        for o in ocorrencias:
            status_oc = "✔ Resolvida" if o.get("resolvida") else "⚠ Aberta"
            print(f"  [{status_oc}] {o['data']:12} | {o['tipo']:<25} | {o['gravidade']}")
            if o["descricao"]:
                print(f"              {o['descricao']}")

# ─────────────────────────────────────────────
#  MENU DE ENTREGAS
# ─────────────────────────────────────────────

def menu_entregas():
    while True:
        titulo("GESTÃO DE ENTREGAS")
        print("  [1] Painel de entregas (visão geral + alertas)")
        print("  [2] Registrar envio / expedição")
        print("  [3] Atualizar status de entrega")
        print("  [4] Confirmar recebimento (conferência de itens)")
        print("  [5] Timeline de um pedido")
        print("  [6] Registrar ocorrência")
        print("  [7] Gerenciar ocorrências")
        print("  [0] Voltar")
        linha()
        op = input("  Opção: ").strip()
        if   op == "1": painel_entregas()
        elif op == "2": registrar_envio()
        elif op == "3": atualizar_status_entrega()
        elif op == "4": confirmar_recebimento()
        elif op == "5": ver_timeline()
        elif op == "6": registrar_ocorrencia()
        elif op == "7": gerenciar_ocorrencias()
        elif op == "0": break
        else:           print("  ⚠  Opção inválida.")

# ─────────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────────

def menu_principal():
    while True:
        titulo("SISTEMA DE COMPRAS")
        print("  [1] Nova compra")
        print("  [2] Consultar histórico")
        print("  [3] Atualizar pedido (status / recebimento / NF)")
        print("  [4] Gestão de Entregas")
        print("  [5] Fornecedores")
        print("  [6] Produtos")
        print("  [0] Sair")
        linha()
        op = input("  Opção: ").strip()
        if op == "1":
            nova_compra()
        elif op == "2":
            consultar_historico()
        elif op == "3":
            atualizar_compra()
        elif op == "4":
            menu_entregas()
        elif op == "5":
            menu_fornecedores()
        elif op == "6":
            menu_produtos()
        elif op == "0":
            print("\n  Até logo!\n")
            break
        else:
            print("  ⚠  Opção inválida.")

# ─────────────────────────────────────────────
#  INICIAR
# ─────────────────────────────────────────────

if __name__ == "__main__":
    menu_principal()