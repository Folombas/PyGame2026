"""HTTP-сервер BunnyOS — рабочий стол в браузере."""
import io
import threading
from flask import Flask, Response, render_template_string, request

import pygame

_current_jpeg = None
_lock = threading.Lock()
_shell_ref = None
_thread = None
_running = False
PORT = 8000


def _update_frame(surface):
    """Вызывается из главного цикла — обновляет JPEG."""
    global _current_jpeg
    try:
        with _lock:
            buf = io.BytesIO()
            pygame.image.save(surface, buf, "frame.jpg")
            _current_jpeg = buf.getvalue()
    except Exception as e:
        print(f"[web] frame error: {e}")


def get_frame():
    with _lock:
        return _current_jpeg


def create_app():
    app = Flask(__name__)

    INDEX_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>BunnyOS Live</title>
<style>
body { margin:0; background:#0a0c14; color:#d0e0ff; font-family:monospace;
       display:flex; flex-direction:column; align-items:center; }
h1 { font-weight:normal; letter-spacing:4px; color:#6ea8ff; }
#screen { max-width:95vw; max-height:80vh; border:2px solid #2a3a5a;
          box-shadow:0 0 30px #1a3a6a; border-radius:6px; }
#status { margin:8px; color:#557; }
</style></head>
<body>
<h1>🌐 BunnyOS LIVE</h1>
<img id="screen" src="/screenshot?_=0">
<div id="status">updating...</div>
<script>
let n = 0;
const img = document.getElementById('screen');
const st = document.getElementById('status');
function tick() {
    n++;
    img.src = '/screenshot?_=' + n;
    st.textContent = 'refresh #' + n + ' — ' + new Date().toLocaleTimeString();
}
setInterval(tick, 500);
tick();
</script>
</body></html>"""

    @app.route("/")
    def index():
        return render_template_string(INDEX_HTML)

    @app.route("/screenshot")
    def screenshot():
        data = get_frame()
        if not data:
            return Response(b"no frame yet", status=503)
        return Response(data, mimetype="image/jpeg")

    @app.route("/api/status")
    def status():
        return {"running": _running, "port": PORT,
                "frame_size": len(_current_jpeg) if _current_jpeg else 0}

    @app.route("/api/command", methods=["POST"])
    def api_command():
        """Выполняет команду в Shell BunnyOS."""
        if _shell_ref is None:
            return {"ok": False, "error": "shell not available"}, 503
        data = request.get_json(silent=True) or {}
        cmd = data.get("cmd", "").strip()
        if not cmd:
            return {"ok": False, "error": "empty command"}, 400
        try:
            result = _shell_ref.run(cmd)
            return {"ok": True, "output": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}, 500

    return app


def start(shell_ref=None, port=8000):
    """Запускает сервер в фоновом потоке."""
    global _thread, _running, _shell_ref, PORT
    _shell_ref = shell_ref
    PORT = port
    if _running:
        return False
    app = create_app()

    def run():
        global _running
        _running = True
        try:
            app.run(host="127.0.0.1", port=PORT, threaded=True,
                    use_reloader=False, debug=False)
        except Exception as e:
            print(f"[web] server stopped: {e}")
        finally:
            _running = False

    _thread = threading.Thread(target=run, daemon=True)
    _thread.start()
    print(f"[web] 🌐 Server started at http://localhost:{PORT}")
    return True


def stop():
    global _running
    _running = False
    print("[web] server marked stopped (thread will die with app)")
