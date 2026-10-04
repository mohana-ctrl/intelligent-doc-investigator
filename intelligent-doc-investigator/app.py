"""
Intelligent Document Investigator - Web Server & Application API
Supports both FastAPI (if installed) and Python Standard Library http.server
for instant 0-dependency execution.
"""

import os
import sys
import json
import cgi
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

from backend.investigation_engine import InvestigationEngine
from backend.sample_data import SAMPLE_DOSSIERS

# Initialize global investigation engine
engine = InvestigationEngine()

# Automatically preload default dossier on boot
engine.load_sample_dossier("ma_due_diligence")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class InvestigationHTTPHandler(SimpleHTTPRequestHandler):
    """Zero-dependency HTTP Handler implementing full REST API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {
                "status": "online",
                "system": "Intelligent Document Investigator (ALG-AI-02)",
                "active_dossier": engine.active_dossier_name,
                "document_count": len(engine.list_documents()),
                "gemini_configured": engine.gemini_client.is_configured()
            })
        elif path == "/api/documents":
            docs = engine.list_documents()
            self._send_json(200, {"documents": docs, "count": len(docs)})
        elif path == "/api/conflict-matrix":
            matrix = engine.get_cross_document_conflict_matrix()
            self._send_json(200, matrix)
        elif path == "/api/samples":
            samples_list = [
                {
                    "key": k,
                    "title": v["title"],
                    "description": v["description"],
                    "doc_count": len(v["documents"]),
                    "suggested_queries": v.get("suggested_queries", [])
                }
                for k, v in SAMPLE_DOSSIERS.items()
            ]
            self._send_json(200, {"samples": samples_list})
        elif path == "/" or path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/styles.css":
            self._serve_file("styles.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._serve_file("app.js", "application/javascript; charset=utf-8")
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b'{}'

        try:
            req_data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            req_data = {}

        if path == "/api/investigate":
            query = req_data.get("query", "").strip()
            if not query:
                self._send_json(400, {"error": "Query string is required"})
                return
            target_doc_id = req_data.get("target_doc_id") or None
            top_k = int(req_data.get("top_k", 8))
            res = engine.query_investigation(query=query, top_k=top_k, target_doc_id=target_doc_id)
            self._send_json(200, res)

        elif path == "/api/load-sample":
            key = req_data.get("dossier_key", "ma_due_diligence")
            try:
                res = engine.load_sample_dossier(key)
                self._send_json(200, res)
            except Exception as e:
                self._send_json(400, {"error": str(e)})

        elif path == "/api/upload":
            doc_name = req_data.get("doc_name", "Untitled_Document.txt")
            doc_id = req_data.get("doc_id", doc_name.lower().replace(" ", "_"))
            text = req_data.get("content", "")
            if not text:
                self._send_json(400, {"error": "Content text is required"})
                return
            res = engine.ingest_text(text, doc_id, doc_name)
            self._send_json(200, res)

        elif path == "/api/config":
            api_key = req_data.get("gemini_api_key", "").strip()
            engine.gemini_client.set_api_key(api_key)
            self._send_json(200, {
                "status": "updated",
                "gemini_configured": engine.gemini_client.is_configured()
            })

        elif path == "/api/clear":
            engine.clear()
            self._send_json(200, {"status": "cleared"})
        else:
            self._send_json(404, {"error": f"Endpoint {path} not found"})

    def _serve_file(self, filename: str, content_type: str):
        filepath = os.path.join(FRONTEND_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, data: Any):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server(port: int = 8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, InvestigationHTTPHandler)
    print("=" * 65)
    print(" 🔎 INTELLIGENT DOCUMENT INVESTIGATOR (ALG-AI-02) PROTOTYPE")
    print("=" * 65)
    print(f" Web UI running at: http://localhost:{port}")
    print(f" REST API running at: http://localhost:{port}/api/health")
    print(f" Loaded Dossier: {engine.active_dossier_name}")
    print(f" Indexed Documents: {len(engine.list_documents())}")
    print(" Press Ctrl+C to terminate.")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
