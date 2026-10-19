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
* { box-sizing:border-box; }
body { margin:0; background:#0a0c14; color:#d0e0ff; font-family:monospace;
       display:flex; flex-direction:column; align-items:center; padding:20px; }
h1 { font-weight:normal; letter-spacing:4px; color:#6ea8ff; margin:5px; }
.layout { display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;
          justify-content:center; max-width:1400px; width:100%; }
#screen { max-width:900px; max-height:75vh; border:2px solid #2a3a5a;
          box-shadow:0 0 30px #1a3a6a; border-radius:6px; }
.right { flex:1; min-width:320px; max-width:500px; }
#status { margin:8px 0; color:#557; font-size:12px; }
.console { background:#05080f; border:1px solid #2a3a5a;
           border-radius:6px; padding:10px; height:300px;
           overflow-y:auto; font-size:13px; }
.line { color:#8fb8ff; padding:1px 0; }
.err { color:#ff6677; }
.prompt { color:#66ff99; }
.input-row { display:flex; margin-top:10px; }
#cmd { flex:1; background:#05080f; border:1px solid #2a3a5a; color:#d0e0ff;
       padding:8px; font-family:monospace; font-size:14px; border-radius:4px; }
#send { background:#1a3a6a; color:#d0e0ff; border:1px solid #3a6aa6;
        padding:8px 16px; cursor:pointer; margin-left:6px; border-radius:4px; }
#send:hover { background:#2a5a9a; }
</style></head>
<body>
<h1>🌐 BunnyOS LIVE</h1>
<div class="layout">
  <img id="screen" src="/screenshot?_=0">
  <div class="right">
    <div id="status">updating...</div>
    <div class="console" id="console"></div>
    <div class="input-row">
      <input id="cmd" placeholder="введи команду (ls, fortune, cowsay...)" autocomplete="off">
      <button id="send" onclick="sendCmd()">→</button>
    </div>
  </div>
</div>
<script>
let n = 0;
const img = document.getElementById('screen');
const st = document.getElementById('status');
const con = document.getElementById('console');
const inp = document.getElementById('cmd');
function tick() {
    n++;
    img.src = '/screenshot?_=' + n;
    st.textContent = 'refresh #' + n + ' — ' + new Date().toLocaleTimeString();
}
function addLine(text, cls='line') {
    const d = document.createElement('div');
    d.className = cls; d.textContent = text;
    con.appendChild(d); con.scrollTop = con.scrollHeight;
}
function sendCmd() {
    const cmd = inp.value.trim();
    if (!cmd) return;
    addLine('zayka@bunnyos:~$ ' + cmd, 'prompt');
    inp.value = '';
    fetch('/api/command', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({cmd})
    }).then(r => r.json()).then(data => {
        if (data.ok) {
            (data.output || []).forEach(l => addLine(l));
        } else {
            addLine('Ошибка: ' + data.error, 'err');
        }
        addLine('');
    }).catch(e => addLine('Network: ' + e, 'err'));
}
inp.addEventListener('keydown', e => { if (e.key==='Enter') sendCmd(); });
setInterval(tick, 500);
tick();
addLine('BunnyOS Web Console ready. Попробуй: ls /  |  fortune  |  cowsay hi');
addLine('');
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

    @app.route("/api/help")
    def api_help():
        return {
            "commands": [
                "ls", "cd", "pwd", "cat", "echo", "grep", "find",
                "fortune", "cowsay", "cal", "factor", "bc", "seq",
                "uname", "hostname", "uptime", "whoami", "df", "free",
                "ps", "lsblk", "lscpu", "ifconfig", "ping", "curl",
                "hint", "progress", "explore", "scores",
                "matrix", "banner", "sl", "weather", "help",
            ],
            "games": ["snake", "tetris", "2048", "pong", "breakout", "hub"],
            "note": "REAL system: uname -a, cat /proc/cpuinfo, ls / (видит реальный Linux!)",
        }

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
            # Только localhost — никакого внешнего доступа
            # Это важно для безопасности: команды выполняются в реальной Shell
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
