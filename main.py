import os
import re
import ezdxf
import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))

resultados = []

# Detecta andar com base no nome do arquivo, igual ao script para PDF
def detectar_andar_do_nome(nome):
    nums = re.findall(r"\d{1,2}", nome)
    if not nums:
        return None

    # tenta achar algo como "10º", "10 ANDAR"
    for n in nums:
        if re.search(fr"{n}\s*(º|o|°|andar)", nome, flags=re.IGNORECASE):
            return n.zfill(2)

    return nums[0].zfill(2)


def associar_mesas_por_faixa_vertical(mesas, espinhas, tolerancia=200):
    assoc = []
    for mesa in mesas:
        mx, my = mesa["x"], mesa["y"]
        melhor = None
        melhor_dy = None

        for esp in espinhas:
            ey = esp["y"]
            dy = abs(my - ey)

            if dy <= tolerancia:
                if melhor_dy is None or dy < melhor_dy:
                    melhor_dy = dy
                    melhor = esp

        assoc.append((mesa, melhor))
    return assoc


print(f"📂 Procurando DWGs na pasta: {PASTA}")

for arquivo in os.listdir(PASTA):
    if not arquivo.lower().endswith(".dwg"):
        continue

    caminho = os.path.join(PASTA, arquivo)
    print(f"\n🔍 Lendo DWG: {arquivo}")

    andar = detectar_andar_do_nome(arquivo)
    if not andar:
        print("  ⚠️ Não foi possível detectar o andar. Ignorando.")
        continue

    # espinhas tipo 10.12, 10.13...
    PADRAO_ESPINHA = re.compile(fr"^{andar}\.\d{{2}}$")

    try:
        doc = ezdxf.readfile(caminho)
    except Exception as e:
        print(f"❌ Erro abrindo {arquivo}: {e}")
        continue

    msp = doc.modelspace()

    espinhas = []
    mesas = []

    # percorre todos os textos
    for e in msp.query("TEXT MTEXT"):
        texto = e.dxf.text.strip()
        x = float(e.dxf.insert.x)
        y = float(e.dxf.insert.y)

        # espinha ex: 10.12
        if PADRAO_ESPINHA.fullmatch(texto):
            espinhas.append({"texto": texto, "x": x, "y": y})
            continue

        # mesa: número de 2 dígitos
        if texto.isdigit() and len(texto) == 2:
            mesas.append({"texto": texto, "x": x, "y": y})

    print(f"  ✔ Espinhas encontradas: {len(espinhas)}")
    print(f"  ✔ Mesas encontradas: {len(mesas)}")

    # associa mesas às espinhas
    associacoes = associar_mesas_por_faixa_vertical(mesas, espinhas)

    for mesa, espinha in associacoes:
        mesa_num = mesa["texto"].zfill(2)

        if espinha:
            esp_txt = espinha["texto"]
            esp_num = esp_txt.split(".")[1]
            mesa_id = f"{esp_num}{mesa_num}"
        else:
            esp_txt = None
            mesa_id = mesa_num

        resultados.append({
            "arquivo": arquivo,
            "andar": andar,
            "mesa_texto": mesa_num,
            "mesa_id": mesa_id,
            "mesa_x": mesa["x"],
            "mesa_y": mesa["y"],
            "espinha_texto": esp_txt,
        })


# exporta CSV
if resultados:
    df = pd.DataFrame(resultados)
    df.to_csv(os.path.join(PASTA, "dwg_detectado.csv"), sep=";", index=False)
    print("\n📄 Extração concluída! Arquivo gerado: dwg_detectado.csv")
else:
    print("\n⚠️ Nenhuma mesa/espinha encontrada nos DWGs.")
