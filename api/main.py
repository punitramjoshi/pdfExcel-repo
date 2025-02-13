import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Flask, request, jsonify
from data.model import RAG
from data.excel_model import ExcelBot
import pandas as pd

app = Flask(__name__)


@app.route("/load_db", methods=["POST"])
def load_db():
    data: dict = request.get_json()
    user_id = data.get("user_id")
    file_path = data.get("file_path")
    supported_formats = ["pptx", "ppt", "doc", "docx", "pdf", "txt", "text", "md"]
    file_extension = file_path.split(".")[-1]
    if file_path and user_id:
        if file_extension in supported_formats:
            try:
                rag_model = RAG()
                rag_model.load_db(file_path, user_id)
                return jsonify({"success": "Database loaded successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    else:
        return jsonify({"error": "Missing required parameters"}), 400


@app.route("/pdf_invoke", methods=["POST"])
def pdf_invoke():
    data: dict = request.get_json()
    user_id = data.get("user_id")
    query = data.get("query")

    if user_id and query:
        try:
            rag_model = RAG()
            answer = rag_model.invoke(user_id=user_id, query=query)
            return jsonify({"answer": answer}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Missing required parameters"}), 400


@app.route("/delete_db", methods=["POST"])
def delete_db():
    data: dict = request.get_json()
    user_id = data.get("user_id")

    if user_id:
        try:
            rag_model = RAG()
            rag_model.delete_db(user_id)
            return jsonify({"success": "Database deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Missing required parameters"}), 400


@app.route("/excel_invoke", methods=["POST"])
def excel_invoke():
    data: dict = request.get_json()
    query: str = data.get("query")
    file_path: str = data.get("file_path")
    sheet_name: str | int = data.get("sheet_name", 0)

    if file_path and query:
        try:
            if file_path.endswith(".csv"):
                excelbot = ExcelBot(file_path=file_path)
            elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                try:
                    sheet_name = int(sheet_name)
                except:
                    pass
                excelbot = ExcelBot(file_path=file_path, sheet_name=sheet_name)

            output = excelbot.excel_invoke(query)
            return jsonify({"output": output}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Missing required parameters"}), 400


if __name__ == "__main__":
    app.run(debug=True)
