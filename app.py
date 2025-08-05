from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import shutil
import tempfile
import uuid
from zipfile import ZipFile
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "ctr_lotes")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

# Limpa sessões antigas com mais de 1 hora
def limpar_sessoes_antigas():
    agora = datetime.now()
    for pasta in os.listdir(BASE_TEMP_DIR):
        caminho = os.path.join(BASE_TEMP_DIR, pasta)
        if os.path.isdir(caminho):
            ultima_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
            if agora - ultima_mod > timedelta(hours=1):
                shutil.rmtree(caminho, ignore_errors=True)
        elif pasta.endswith(".zip"):
            ultima_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
            if agora - ultima_mod > timedelta(hours=1):
                os.remove(caminho)

@app.route("/gerar-lote", methods=["POST"])
def gerar_lote():
    limpar_sessoes_antigas()
    data = request.get_json()
    ids = data.get("ids")
    session_id = data.get("session_id")

    if not ids or not session_id:
        return jsonify({"erro": "IDs ou session_id ausente"}), 400

    session_path = os.path.join(BASE_TEMP_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    # Geração de PDFs simulada
    for _id in ids:
        pdf_path = os.path.join(session_path, f"{_id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n% Simulacao de PDF para ID: " + _id.encode() + b"\n%%EOF")

    return jsonify({"status": "Lote recebido"}), 200

@app.route("/finalizar", methods=["POST"])
def finalizar_zip():
    limpar_sessoes_antigas()
    data = request.get_json()
    session_id = data.get("session_id")

    session_path = os.path.join(BASE_TEMP_DIR, session_id)
    if not os.path.exists(session_path):
        return jsonify({"erro": "Sessão não encontrada"}), 404

    zip_path = os.path.join(BASE_TEMP_DIR, f"{session_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(session_path):
            full_path = os.path.join(session_path, filename)
            zipf.write(full_path, arcname=filename)

    shutil.rmtree(session_path, ignore_errors=True)
    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR_Final.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
