from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import shutil
import tempfile
from zipfile import ZipFile
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "ctr_lotes")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

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

def gerar_pdf_minimo(path, texto):
    # Gera um PDF mínimo válido contendo texto simples
    conteudo = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(texto) + 38} >>
stream
BT
/F1 12 Tf
10 180 Td
({texto}) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000212 00000 n 
0000000305 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
{len(conteudo) + len(texto) + 100}
%%EOF
"""
    with open(path, "wb") as f:
        f.write(conteudo.encode("latin1"))

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
        gerar_pdf_minimo(pdf_path, f"Documento CTR ID: {_id}")

    return jsonify({"status": "Lote recebido"}), 200

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

    arquivos = os.listdir(session_path)
    print(f"Arquivos na sessão {session_id}: {arquivos}")  # DEBUG

    zip_path = os.path.join(BASE_TEMP_DIR, f"{session_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for filename in arquivos:
            full_path = os.path.join(session_path, filename)
            zipf.write(full_path, arcname=filename)

    shutil.rmtree(session_path, ignore_errors=True)
    return send_file(zip_path, as_attachment=True, download_name="Documentos_CTR_Final.zip")
