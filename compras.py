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
HISTORICO_JSON  = DIR_BASE / "historico.json"
HISTORICO_CSV   = DIR_BASE / "historico_geral.csv"

for d in (DIR_BASE, DIR_TXT, DIR_CSV):
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
#  CONSTANTES
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

    # Fornecedor
    print()
    fornecedor   = input_texto("Fornecedor: ")
    cnpj_cpf     = input_texto("CNPJ/CPF do fornecedor (ENTER para pular): ", obrigatorio=False)
    nota_fiscal  = input_texto("Nº Nota Fiscal (ENTER para pular): ", obrigatorio=False)

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

    # Status
    print("\n  Status da compra:")
    cod_status, status = input_menu(STATUS_OPCOES)

    # Frete
    frete = input_float(f"\nFrete ({simbolo_moeda}): ")
    frete_brl = frete * cotacao

    # Observação geral
    obs_geral = input_texto("\nObservações gerais (ENTER para pular): ", obrigatorio=False)

    # ── Produtos ──
    produtos = []
    total_produtos = 0.0

    while True:
        titulo("ADICIONANDO PRODUTO")
        codigo     = input_texto("Código do produto: ")
        nome       = input_texto("Nome do produto: ")
        valor_unit = input_float(f"Valor unitário ({simbolo_moeda}): ", permite_zero=False)
        quantidade = input_int("Quantidade: ")
        obs_prod   = input_texto("Observação do item (ENTER para pular): ", obrigatorio=False)

        icms_perc  = input_float("ICMS (%): ")
        icms_valor = (valor_unit * quantidade) * (icms_perc / 100)

        ipi_perc   = input_float("IPI (%): ")
        ipi_valor  = (valor_unit * quantidade) * (ipi_perc / 100)

        desconto   = input_desconto(valor_unit * quantidade)
        subtotal   = (valor_unit * quantidade) + icms_valor + ipi_valor - desconto
        subtotal_brl = subtotal * cotacao

        produtos.append({
            "codigo":      codigo,
            "nome":        nome,
            "valor_unit":  valor_unit,
            "quantidade":  quantidade,
            "icms_perc":   icms_perc,
            "icms_valor":  icms_valor,
            "ipi_perc":    ipi_perc,
            "ipi_valor":   ipi_valor,
            "desconto":    desconto,
            "subtotal":    subtotal,
            "subtotal_brl": subtotal_brl,
            "obs":         obs_prod,
        })
        total_produtos += subtotal

        print(f"\n  ✔  Subtotal do item: {simbolo_moeda} {subtotal:.2f}", end="")
        if sigla_moeda != "BRL":
            print(f"  (R$ {subtotal_brl:.2f})", end="")
        print()

        # Editar item recém-adicionado?
        if input_sim_nao("  Deseja editar este item? (s/n): ") == "s":
            total_produtos -= subtotal
            produtos.pop()
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
    print(f"  Fornecedor       : {fornecedor}")
    if cnpj_cpf:   print(f"  CNPJ/CPF         : {cnpj_cpf}")
    if nota_fiscal: print(f"  Nota Fiscal      : {nota_fiscal}")
    print(f"  Data compra      : {data_compra_str}")
    print(f"  Data faturamento : {data_faturamento_str}")
    print(f"  Prazo entrega    : {prazo_dias_str}  (previsão: {data_entrega_str})")
    print(f"  Pagamento        : [{cod_pagamento}] {modo_pagamento}", end="")
    if parcelas > 1:
        print(f"  {parcelas}x  →  Venc.: {', '.join(vencimentos)}", end="")
    print()
    print(f"  Centro de custo  : {centro_custo}")
    print(f"  Status           : {status}")
    print(f"  Moeda            : {sigla_moeda}", end="")
    if sigla_moeda != "BRL":
        print(f"  (cotação R$ {cotacao:.4f})", end="")
    print()
    if obs_geral:  print(f"  Observações      : {obs_geral}")
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

    # ── Montar dict da compra ──
    compra = {
        "num_pedido":        num_pedido,
        "fornecedor":        fornecedor,
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
    }

    salvar_historico(compra)
    salvar_txt(compra, simbolo_moeda)
    salvar_csv_individual(compra, simbolo_moeda)
    atualizar_csv_geral(compra, simbolo_moeda)

    print(f"\n  ✔  Compra {num_pedido} registrada com sucesso!")

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
        if c['cnpj_cpf']:   f.write(f"CNPJ/CPF          : {c['cnpj_cpf']}\n")
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
#  SALVAR CSV INDIVIDUAL
# ─────────────────────────────────────────────

def salvar_csv_individual(c, sim):
    nome = DIR_CSV / f"{c['num_pedido']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(nome, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Pedido", "Fornecedor", "CNPJ/CPF", "Nota Fiscal",
                    "Data Compra", "Data Faturamento", "Prazo", "Previsão Entrega",
                    "Pagamento", "Parcelas", "Vencimentos", "Centro Custo",
                    "Status", "Moeda", "Cotação BRL", "Frete", "Obs Geral"])
        w.writerow([c['num_pedido'], c['fornecedor'], c['cnpj_cpf'], c['nota_fiscal'],
                    c['data_compra'], c['data_faturamento'], c['prazo_entrega'], c['data_entrega_prev'],
                    c['pagamento'], c['parcelas'], "; ".join(c['vencimentos']), c['centro_custo'],
                    c['status'], c['moeda'], c['cotacao_brl'], c['frete'], c['obs_geral']])
        w.writerow([])
        w.writerow(["Código", "Produto", "Valor Unit.", "Qtd",
                    "ICMS%", "ICMS Valor", "IPI%", "IPI Valor",
                    "Desconto", "Subtotal", f"Subtotal (BRL)", "Obs"])
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
    cabecalho = ["Pedido", "Data Compra", "Fornecedor", "CNPJ/CPF", "Nota Fiscal",
                 "Status", "Pagamento", "Centro Custo", "Moeda", "Total Final", "Total Final BRL",
                 "Data Registro"]
    existe = HISTORICO_CSV.exists()
    with open(HISTORICO_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not existe:
            w.writerow(cabecalho)
        w.writerow([c['num_pedido'], c['data_compra'], c['fornecedor'], c['cnpj_cpf'],
                    c['nota_fiscal'], c['status'], c['pagamento'], c['centro_custo'],
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
        if c['status'] == "Pendente" or c['status'] == "Aprovada":
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

    with open(HISTORICO_JSON, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
    print(f"  ✔  Pedido {num} salvo.")

# ─────────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────────

def menu_principal():
    while True:
        titulo("SISTEMA DE COMPRAS")
        print("  [1] Nova compra")
        print("  [2] Consultar histórico")
        print("  [3] Atualizar pedido (status / recebimento / NF)")
        print("  [0] Sair")
        linha()
        op = input("  Opção: ").strip()
        if op == "1":
            nova_compra()
        elif op == "2":
            consultar_historico()
        elif op == "3":
            atualizar_compra()
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