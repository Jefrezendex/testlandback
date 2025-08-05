from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from reportlab.pdfgen import canvas
import os
import tempfile
import shutil
from zipfile import ZipFile
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "ctr_lotes")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

def limpar_sessoes_antigas():
    """Remove sessões e ZIPs com mais de 1h para liberar espaço."""
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

def gerar_pdf_reportlab(path, texto):
    """Gera PDF válido usando reportlab."""
    c = canvas.Canvas(path)
    c.setFont("Helvetica", 16)
    c.drawString(50, 750, "Documento CTR")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"ID: {texto}")
    c.save()

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

    for _id in ids:
        pdf_path = os.path.join(session_path, f"{_id}.pdf")
        gerar_pdf_reportlab(pdf_path, _id)

    return jsonify({"status": "ok", "lote": len(ids)}), 200

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

@app.route("/finalizar", methods=["POST"])
def finalizar_zip():
    limpar_sessoes_antigas()
    data = request.get_json()
    session_id = data.get("session_id")

    session_path = os.path.join(BASE_TEMP_DIR, session_id)
    if not os.path.exists(session_path):
        return jsonify({"erro": "Sessão não encontrada"}), 404

    arquivos = [f for f in os.listdir(session_path) if f.endswith(".pdf")]
    if not arquivos:
        return jsonify({"erro": "Nenhum PDF gerado"}), 400

    zip_path = os.path.join(BASE_TEMP_DIR, f"{session_id}.zip")
    with ZipFile(zip_path, "w") as zipf:
        for filename in arquivos:
            full_path = os.path.join(session_path, filename)
            zipf.write(full_path, arcname=filename)

    shutil.rmtree(session_path, ignore_errors=True)
    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR_Final.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
