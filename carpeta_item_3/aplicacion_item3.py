import os
import sqlite3
import secrets
from typing import Optional

from flask import Flask, request, redirect, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

# ======================
# Configuración general
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

app = Flask(__name__)

# Gestión de clave secreta para Flask (seguridad de sesiones)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(16)

# ======================
# Funciones de base de datos SQLite
# ======================
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    # Crea la tabla de usuarios si no existe
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        """)
        conn.commit()

def get_password_hash(username: str) -> Optional[str]:
    # Obtiene el hash de contraseña almacenado
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return row[0] if row else None

def add_user(username: str, password: str):
    # Genera el hash de la contraseña antes de guardarla
    pw_hash = generate_password_hash(password)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username, password_hash) VALUES(?, ?)", (username, pw_hash))
        conn.commit()

def validate_user(username: str, password: str) -> bool:
    # Valida usuario comparando hash
    pw_hash = get_password_hash(username)
    if not pw_hash:
        return False
    return check_password_hash(pw_hash, password)

# ======================
# Vistas web (HTML simple)
# ======================
HOME_HTML = """
<h2>Item 3 - Sitio Web (Flask + SQLite + Hash)</h2>
<p><b>Puerto:</b> 5800</p>
<ul>
  <li><a href="/register">Registrar usuario</a></li>
  <li><a href="/login">Iniciar sesión</a></li>
</ul>
"""

REGISTER_HTML = """
<h3>Registro de usuario</h3>
<form method="POST">
  Usuario: <input name="username" required><br><br>
  Contraseña: <input name="password" type="password" required><br><br>
  <button type="submit">Registrar</button>
</form>
<p style="color:red;">{{msg}}</p>
<a href="/">Volver</a>
"""

LOGIN_HTML = """
<h3>Inicio de sesión</h3>
<form method="POST">
  Usuario: <input name="username" required><br><br>
  Contraseña: <input name="password" type="password" required><br><br>
  <button type="submit">Ingresar</button>
</form>
<p style="color:red;">{{msg}}</p>
<a href="/">Volver</a>
"""

OK_HTML = """
<h3>✅ Autenticación exitosa</h3>
<p>Usuario autenticado: <b>{{user}}</b></p>
<a href="/">Volver</a>
"""

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if not u or not p:
            msg = "Datos inválidos."
        else:
            try:
                add_user(u, p)
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                msg = "El usuario ya existe."
    return render_template_string(REGISTER_HTML, msg=msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if validate_user(u, p):
            return render_template_string(OK_HTML, user=u)
        msg = "Usuario o contraseña incorrectos."
    return render_template_string(LOGIN_HTML, msg=msg)

# ======================
# Uso por comandos desde terminal
# ======================
def usage():
    print("Uso del programa:")
    print("  python3 aplicacion_item_3.py init-db")
    print("  python3 aplicacion_item_3.py add-user Gabriel_Badilla Clave123")
    print("  python3 aplicacion_item_3.py validate Gabriel_Badilla Clave123")
    print("  python3 aplicacion_item_3.py run")

if __name__ == "__main__":
    init_db()

    if len(os.sys.argv) < 2:
        usage()
        os.sys.exit(0)

    cmd = os.sys.argv[1].lower()

    if cmd == "init-db":
        init_db()
        print("Base de datos inicializada correctamente.")

    elif cmd == "add-user":
        user = os.sys.argv[2]
        pw = os.sys.argv[3]
        add_user(user, pw)
        print(f"Usuario creado: {user}")

    elif cmd == "validate":
        user = os.sys.argv[2]
        pw = os.sys.argv[3]
        print("Credenciales válidas" if validate_user(user, pw) else "Credenciales inválidas")

    elif cmd == "run":
        print("Servidor ejecutándose en http://localhost:5800")
        app.run(host="0.0.0.0", port=5800, debug=False)
