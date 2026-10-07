"""Servidor interno del piloto. Configuración y archivos reales permanecen en TechTop."""
import json
import os
import threading
import time
import ipaddress
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from domain import build_board
from reader import read_xlsx


ROOT = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("TECHTOP_BOARD_CONFIG", ROOT / "config.example.json"))
settings = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
for source in (settings["imports"], settings["exports"]):
    configured = Path(source["path"])
    source["path"] = str(configured if configured.is_absolute() else CONFIG.parent / configured)
state_lock = threading.Lock()
state = {"board": None, "lastSuccessfulRead": None, "lastSuccessfulReadLocal": None, "lastAttempt": None,
         "error": "Esperando primera lectura"}


def iso_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def refresh():
    with state_lock:
        state["lastAttempt"] = iso_now()
    try:
        imp = settings["imports"]
        exp = settings["exports"]
        imports = read_xlsx(imp["path"], "import", imp.get("sheet"), imp.get("headerRow"), settings.get("dateOrder", "MDY"))
        exports = read_xlsx(exp["path"], "export", exp.get("sheet"), exp.get("headerRow"), settings.get("dateOrder", "MDY"))
        board = build_board(imports, exports, bool(settings.get("demo")))
        with state_lock:
            state.update(board=board, lastSuccessfulRead=iso_now(),
                         lastSuccessfulReadLocal=datetime.now(ZoneInfo("America/Costa_Rica")).isoformat(timespec="minutes"),
                         error=None)
    except Exception as exc:
        # Exponer solo errores de estructura previstos; nunca rutas, valores de celda ni trazas.
        from reader import FormatError
        message = str(exc) if isinstance(exc, FormatError) else "No se pudieron leer ambos itinerarios"
        with state_lock:
            state["error"] = message


def poll():
    while True:
        refresh()
        time.sleep(max(15, int(settings.get("refreshSeconds", 60))))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Los identificadores enviados al tablero no se escriben en los logs.
        pass

    def send(self, body, mime, status=200):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/board":
            with state_lock:
                payload = dict(state)
            self.send(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            return
        if self.path == "/health":
            with state_lock:
                ok = state["board"] is not None and state["error"] is None
                payload = {"healthy": ok, "lastSuccessfulRead": state["lastSuccessfulRead"]}
            self.send(json.dumps(payload).encode("utf-8"), "application/json", 200 if ok else 503)
            return
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8")}
        if self.path in files:
            name, mime = files[self.path]
            self.send((ROOT / "web" / name).read_bytes(), mime)
            return
        self.send(b"Not found", "text/plain", 404)


if __name__ == "__main__":
    host = settings.get("bind", "127.0.0.1")
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback:
        raise SystemExit("El piloto solo permite escucha local. IT debe añadir autenticación y HTTPS antes de publicarlo en la red.")
    port = int(settings.get("port", 8765))
    worker = threading.Thread(target=poll, daemon=True)
    worker.start()
    print(f"Tablero iniciado en http://{host}:{port}/ (piloto local)")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
