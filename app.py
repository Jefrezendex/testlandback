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

# Pasta temporária para armazenar PDFs gerados
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "ctr_lotes")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

# 🔹 Função para limpar sessões antigas
def limpar_sessoes_antigas():
    agora = datetime.now()
    for pasta in os.listdir(BASE_TEMP_DIR):
        caminho = os.path.join(BASE_TEMP_DIR, pasta)
        try:
            if os.path.isdir(caminho):
                ultima_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
                if agora - ultima_mod > timedelta(hours=1):
                    shutil.rmtree(caminho, ignore_errors=True)
            elif pasta.endswith(".zip"):
                ultima_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
                if agora - ultima_mod > timedelta(hours=1):
                    os.remove(caminho)
        except:
            pass

# 🔹 Endpoint para receber um lote de IDs
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

    # 🔹 Simulação de geração de PDFs
    # Substitua por sua função real de gerar PDFs se necessário
    for _id in ids:
        pdf_path = os.path.join(session_path, f"{_id}.pdf")
        with open(pdf_path, "wb") as f:
            # Conteúdo mínimo de PDF válido para teste
            f.write(b"%PDF-1.4\n% Simulacao de PDF para ID: " + _id.encode() + b"\n%%EOF")

    return jsonify({"status": "Lote recebido"}), 200

# 🔹 Endpoint para consultar progresso
@app.route("/progresso", methods=["POST"])
def progresso():
    data = request.get_json()
    session_id = data.get("session_id")
    total_ids = data.get("total_ids", 0)

    session_path = os.path.join(BASE_TEMP_DIR, session_id)
    if not os.path.exists(session_path):
        return jsonify({"progresso": 0, "total": total_ids}), 200

    gerados = len([f for f in os.listdir(session_path) if f.endswith(".pdf")])
    return jsonify({"progresso": gerados, "total": total_ids}), 200

# 🔹 Endpoint para finalizar e gerar ZIP único
@app.route("/finalizar", methods=["POST"])
def finalizar_zip():
    limpar_sessoes_antigas()
    data = request.get_json()
    session_id = data.get("session_id")

    session_path = os.path.join(BASE_TEMP_DIR, session_id)
    if not os.path.exists(session_path):
        return jsonify({"erro": "Sessão não encontrada"}), 404

    zip_path = os.path.join(BASE_TEMP_DIR, f"{session_id}.zip")

    # Monta o ZIP com todos os PDFs
    with ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(session_path):
            full_path = os.path.join(session_path, filename)
            zipf.write(full_path, arcname=filename)

    # Limpa PDFs temporários da sessão
    shutil.rmtree(session_path, ignore_errors=True)

    # Retorna o ZIP para download
    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR_Final.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
