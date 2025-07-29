from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, pdfkit

app = Flask(__name__)
CORS(app)


WKHTMLTOPDF_PATH = "/usr/bin/wkhtmltopdf"
pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

HTML_DIR = "htmls_salvos"
PDF_DIR = "pdfs_gerados"
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

BASE_URL = "https://rcc-spregula.coletas.online/Transportador/CTR/ImprimeCTR.aspx?id="

@app.route('/executar', methods=['POST'])
def executar():
    ids = request.json.get('ids', [])
    resultados = []

    for id_ in ids:
        id_ = id_.strip()
        url = BASE_URL + id_

        # Baixar HTML
        html_path = os.path.join(HTML_DIR, f"{id_}.html")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                resultados.append(f"✔️ HTML salvo para ID {id_}")
            else:
                resultados.append(f"⚠️ Falha ao baixar HTML do ID {id_}: {response.status_code}")
                continue
        except Exception as e:
            resultados.append(f"❌ Erro ao baixar HTML do ID {id_}: {e}")
            continue

        # Gerar PDF
        pdf_path = os.path.join(PDF_DIR, f"{id_}.pdf")
        try:
            pdfkit.from_url(url, pdf_path, configuration=pdfkit_config)
            resultados.append(f"✔️ PDF gerado para ID {id_}")
        except Exception as e:
            resultados.append(f"❌ Erro ao gerar PDF do ID {id_}: {e}")

    return jsonify(resultados)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
