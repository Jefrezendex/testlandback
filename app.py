from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import pdfkit
import shutil
import uuid

app = Flask(__name__)
CORS(app)

# Caminho do wkhtmltopdf no Render
config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

URL_BASE = "https://rcc-spregula.coletas.online/Transportador/CTR/ImprimeCTR.aspx?id="

@app.route("/ping")
def ping():
    return {"status": "ok"}

@app.route("/gerar", methods=["POST"])
def gerar_pdf():
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"erro": "Nenhum ID fornecido"}), 400

    # Criar pastas temporárias
    sessao = str(uuid.uuid4())
    pasta_pdf = f"/tmp/pdfs_{sessao}"
    os.makedirs(pasta_pdf, exist_ok=True)

    total_gerados = 0
    erros = []

    for id_ in ids:
        url = URL_BASE + id_
        caminho_pdf = os.path.join(pasta_pdf, f"{id_}.pdf")
        try:
            # Gerar PDF diretamente da URL (mantém layout)
            pdfkit.from_url(url, caminho_pdf, configuration=config)
            total_gerados += 1
            print(f"✔️ PDF gerado: {caminho_pdf}")
        except Exception as e:
            erros.append(f"Erro ao gerar PDF para ID {id_}: {e}")

    # Compactar PDFs em um ZIP
    zip_path = f"/tmp/ctr_docs_{sessao}.zip"
    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', pasta_pdf)

    print(f"📦 {total_gerados} PDFs gerados | {len(erros)} erros")
    if erros:
        print("Detalhes dos erros:", erros)

    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR.zip")
