import pdfplumber
import os

PASTA = os.path.dirname(os.path.abspath(__file__))

for arquivo in os.listdir(PASTA):
    if arquivo.lower().endswith(".pdf"):
        caminho_pdf = os.path.join(PASTA, arquivo)
        print(f"\n===== {arquivo} =====")

        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                pagina = pdf.pages[0]

                # 1) Ver texto corrido
                texto = pagina.extract_text()
                print("\n--- Trecho de texto bruto ---")
                print((texto[:1000] + "...") if texto else "NENHUM TEXTO ENCONTRADO")

                # 2) Ver as 'palavras' que o pdfplumber está enxergando
                palavras = pagina.extract_words()
                print(f"\nTotal de 'palavras' detectadas: {len(palavras)}")

                for w in palavras[:50]:  # mostra só as 50 primeiras pra não virar carnaval
                    print(repr(w["text"]))

        except Exception as e:
            print(f"Erro ao abrir {arquivo}: {e}")