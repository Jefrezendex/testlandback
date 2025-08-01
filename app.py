from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import pdfkit
import shutil
import uuid
import re

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

    sessao = str(uuid.uuid4())
    pasta_html = f"/tmp/htmls_{sessao}"
    pasta_pdf = f"/tmp/pdfs_{sessao}"
    os.makedirs(pasta_html, exist_ok=True)
    os.makedirs(pasta_pdf, exist_ok=True)

    total_gerados = 0
    erros = []

    for id_ in ids:
        url = URL_BASE + id_
        try:
            resposta = requests.get(url, timeout=15)
            if resposta.status_code == 200:
                # Detecta o encoding correto
                resposta.encoding = resposta.apparent_encoding or 'utf-8'
                html = resposta.text

                # 🔹 Remove ou corrige CSS que gira elementos
                html_corrigido = re.sub(r'transform\s*:\s*rotate\(180deg\)', '', html, flags=re.IGNORECASE)

                # Salva HTML corrigido temporário
                caminho_html = os.path.join(pasta_html, f"{id_}.html")
                with open(caminho_html, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(html_corrigido)

                # Gera PDF a partir do HTML corrigido
                caminho_pdf = os.path.join(pasta_pdf, f"{id_}.pdf")
                pdfkit.from_file(caminho_html, caminho_pdf, configuration=config)
                total_gerados += 1
                print(f"✔️ PDF gerado: {caminho_pdf}")
            else:
                erros.append(f"Falha ao baixar ID {id_}: Status {resposta.status_code}")
        except Exception as e:
            erros.append(f"Erro ao processar ID {id_}: {e}")

    # Cria arquivo ZIP final
    zip_path = f"/tmp/ctr_docs_{sessao}.zip"
    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', pasta_pdf)

    print(f"📦 {total_gerados} PDFs gerados | {len(erros)} erros")
    if erros:
        print("Detalhes dos erros:", erros)

    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR.zip")
