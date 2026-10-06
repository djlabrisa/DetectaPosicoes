import os
import requests
import pandas as pd
from datetime import datetime, date
import urllib3
urllib3.disable_warnings()

# =====================================
# CONFIG
# =====================================
TOKEN_URL = os.environ["TOKEN_URL"]
QUERY_URL = os.environ["QUERY_URL"]

REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
CLIENT_ID = "EpmPortalv2"

# =====================================
# OBTÉM NOVO ACCESS TOKEN
# =====================================
def get_access_token():
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": "epm_profile email openid profile role epm_webapi epm_portal_webapi EpmProcessorWebApi offline_access",
        "client_id": CLIENT_ID
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(TOKEN_URL, data=payload, verify=False, headers=headers)

    if r.status_code != 200:
        print("ERRO NA AUTENTICAÇÃO:", r.text)
        raise Exception("Falha ao obter access token")

    data = r.json()
    access_token = data["access_token"]

    print("🔐 Novo access_token obtido com sucesso.")
    return access_token


# =====================================
# MONTAR PAYLOAD DA QUERY
# =====================================
def build_payload(continuation=None):
    return {
        "continuationPoint": continuation,
        "release": False,
        "connectionType": 3,
        "connectionString": "content://br.com.elipse.provider/Data%20Source%2FPrisma.eds",
        "blockSize": 10000,
        "command": """
SELECT TOP (1000) [sysId]
      ,[number]
      ,[sysName]
      ,coalesce(ajuda, '') as [ajuda]
      ,[wo_openedAt] as 'data_de_abertura'
      ,[wo_closedAt]
      ,[Name]
      ,[CostCenterId]
      ,[Tipo]
      ,[Polo]
      ,coalesce(Torre, '-') as [Torre]
      ,coalesce(Andar, '-') as [Andar]
      ,coalesce(Setor, '-') as [Setor]
      ,coalesce(Sala, '-') as [Sala]
      ,coalesce(Mesa, '-') as [Mesa]
      ,coalesce(TelefoneContato, 'Não informado') as [TelefoneContato]
      ,coalesce(Detalhes, '-') as [Detalhes]
      ,[wo_state]
      ,[wo_state_name]
      ,[task_count]
      ,[task_status_sequence]
      ,[last_task_state_name]
      ,[last_task_closedAt]
      ,[last_task_workEnd]
      ,[sistema_integrador]
      ,[tag_nao_localizada]
      ,[entrou_em_retry]
      ,[tag_nao_comunicou]
      ,[limite_max_atingido]
      ,[limite_min_atingido]
      ,[chamado_atendido]
      ,[tag_inexistente_dexpara]
      ,[atendimento_iniciado]
      ,[tag_inexistente_epm]
      ,[falha_login_api_middleware]
      ,[fora_horario_comercial]
      ,[os_aberta_prisma_automacao]
      ,[falha_comunicacao_prisma]
      ,[ritm_fechada_automacao]
      ,[timeout_fechamento]
  FROM [ItauPredialResults].[dbo].[ServiceNow_WorkOrderUnified] w
  WHERE CAST(w.wo_openedAt AS DATE) BETWEEN CAST(@StartDate AS DATE) AND CAST(@EndDate AS DATE)
  AND (@SysNamefltr = '*' OR sysName = @SysNamefltr)
  AND (@Andarfltr = '*' OR Andar = @Andarfltr)
  AND (@Polofltr = '*' OR Polo = @Polofltr)
  AND (@Prediofltr = '*' OR Torre = @Prediofltr)
  AND (@Setorfltr = '*' OR Setor = @Setorfltr)
""",
        "inputs": [
            {"name": "SysNameFltr", "value": "*", "type": "nvarchar"},
            {"name": "StartDate", "value": "2025-12-03T00:00:00.000Z", "type": "datetime"},
            {"name": "SetorFltr", "value": "*", "type": "nvarchar"},
            {"name": "PredioFltr", "value": "*", "type": "nvarchar"},
            {"name": "PoloFltr", "value": "Centro Empresarial", "type": "nvarchar"},
            {"name": "AndarFltr", "value": "*", "type": "nvarchar"},
            {"name": "EndDate", "value": "2025-12-04T00:00:00.000Z", "type": "datetime"}
        ]
    }


# =====================================
# CONSULTA PAGINADA
# =====================================
def fetch_all_records(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_records = []
    continuation = None

    while True:
        payload = build_payload(continuation)
        r = requests.post(QUERY_URL, json=payload, verify=False, headers=headers)

        if r.status_code != 200:
            print("ERRO:", r.text)
            raise Exception("Falha na query")

        data = r.json()

        records = data.get("recordSet")
        if records:
            all_records.extend(records)

        continuation = data.get("continuationPoint")
        if not continuation:
            break
        print(f"📊 Total de registros obtidos: {len(all_records)}")
        if all_records:
            print("EXEMPLO DE PRIMEIRO REGISTRO:", all_records[0])

    return all_records


# =====================================
# FILTROS
# =====================================
def aplicar_filtros(registros):
    hoje = date.today()
    filtrados = []

    for r in registros:
        dt_str = r.get("data_de_abertura") or r.get("wo_openedAt")

        if not dt_str:
            continue

        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "")).date()
        except:
            continue

        # Filtros solicitados
        if (
            dt < hoje and
            r.get("tag_inexistente_dexpara") is True or
            r.get("tag_inexistente_epm") is True or
            r.get("tag_nao_comunicou") is True or
            r.get("tag_nao_localizada") is True
        ):
            filtrados.append(r)

    return filtrados


# =====================================
# EXCEL
# =====================================
def salvar_excel(lista, arquivo="resultado.xlsx"):
    df = pd.DataFrame(lista)
    df.to_excel(arquivo, index=False)
    print(f"📁 Excel gerado: {arquivo}")


# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    print("🔐 Obtendo token...")
    token = get_access_token()

    print("📡 Coletando dados...")
    dados = fetch_all_records(token)
    print(f"➡️ Total bruto: {len(dados)}")

    print("🔍 Aplicando filtros...")
    filtrados = aplicar_filtros(dados)
    print(f"✔️ Total filtrado: {len(filtrados)}")

    salvar_excel(filtrados)
