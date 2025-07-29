from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import pdfkit
import shutil
import uuid

app = Flask(__name__)
CORS(app)

config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

@app.route("/gerar", methods=["POST"])
def gerar_pdf():
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"erro": "Nenhum ID fornecido"}), 400

    sessao = str(uuid.uuid4())
    pasta_html = f"/tmp/htmls_{sessao}"
    pasta_pdf = f"/tmp/pdfs_{sessao}"
    os.makedirs(pasta_html, exist_ok=True)
    os.makedirs(pasta_pdf, exist_ok=True)

    url_base = "https://rcc-spregula.coletas.online/Transportador/CTR/ImprimeCTR.aspx?id="

    for id_ in ids:
        url = url_base + id_
        try:
            resposta = requests.get(url)
            if resposta.status_code == 200:
                caminho_html = os.path.join(pasta_html, f"{id_}.html")
                with open(caminho_html, "w", encoding="utf-8") as f:
                    f.write(resposta.text)
                caminho_pdf = os.path.join(pasta_pdf, f"{id_}.pdf")
                pdfkit.from_file(caminho_html, caminho_pdf, configuration=config)
            else:
                print(f"Erro {resposta.status_code} ao baixar {id_}")
        except Exception as e:
            print(f"Erro ao processar {id_}: {e}")

    zip_path = f"/tmp/ctr_docs_{sessao}.zip"
    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', pasta_pdf)

    return send_file(zip_path, as_attachment=True, download_name="CTR_Documentos.zip")
