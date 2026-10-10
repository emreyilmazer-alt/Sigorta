import os, sqlite3, secrets
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
# Point DATA_DIR at a persistent volume in production so uploads and SQLite survive redeploys.
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "data"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "leads.db"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED = {"jpg", "jpeg", "png", "webp", "pdf"}
MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "12"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

ADMIN_USER = os.environ.get("ADMIN_USER", "emre")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "905445444379")
BUSINESS_NAME = "Kaymak Sigorta"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, phone TEXT NOT NULL, kind TEXT NOT NULL,
            plate TEXT, note TEXT, file_name TEXT, created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Yeni'
        )""")
init_db()

def admin_ok():
    return session.get("admin") is True

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not admin_ok():
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

@app.get("/")
def home():
    return render_template("index.html", whatsapp=WHATSAPP_NUMBER)

@app.post("/teklif")
def teklif():
    name = request.form.get("name", "").strip()[:120]
    phone = request.form.get("phone", "").strip()[:40]
    kind = request.form.get("kind", "").strip()[:100]
    plate = request.form.get("plate", "").strip()[:30]
    note = request.form.get("note", "").strip()[:2000]
    file = request.files.get("document")
    if not name or not phone or not kind:
        flash("Lütfen adınızı, telefonunuzu ve sigorta türünü doldurun.")
        return redirect(url_for("home") + "#teklif")
    saved_name = None
    if file and file.filename:
        if not allowed_file(file.filename):
            flash("Yalnızca JPG, PNG, WEBP veya PDF dosyası yükleyebilirsiniz.")
            return redirect(url_for("home") + "#teklif")
        # Random stored filename avoids exposing original names and collisions.
        ext = file.filename.rsplit(".", 1)[1].lower()
        saved_name = secrets.token_hex(16) + "." + ext
        file.save(UPLOAD_DIR / saved_name)
    with db() as con:
        con.execute("""INSERT INTO leads(name, phone, kind, plate, note, file_name, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (name, phone, kind, plate, note, saved_name, datetime.now().strftime("%Y-%m-%d %H:%M")))
    flash("Talebiniz alındı. Kaymak Sigorta sizinle iletişime geçecek.")
    return redirect(url_for("home") + "#teklif")

@app.get("/yonetim/giris")
def login():
    return render_template("login.html")

@app.post("/yonetim/giris")
def login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    valid_password = False
    if ADMIN_PASSWORD_HASH:
        valid_password = check_password_hash(ADMIN_PASSWORD_HASH, password)
    elif ADMIN_PASSWORD:
        # Plain env password is supported for initial setup; prefer ADMIN_PASSWORD_HASH in production.
        valid_password = secrets.compare_digest(password, ADMIN_PASSWORD)
    if username == ADMIN_USER and valid_password:
        session.clear()
        session["admin"] = True
        return redirect(url_for("dashboard"))
    flash("Giriş bilgileri hatalı. Sunucu yöneticisinin belirlediği kullanıcı adı ve şifreyi kullanın.")
    return redirect(url_for("login"))

@app.post("/yonetim/cikis")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/yonetim")
@login_required
def dashboard():
    with db() as con:
        leads = con.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    return render_template("dashboard.html", leads=leads, whatsapp=WHATSAPP_NUMBER)

@app.post("/yonetim/<int:lead_id>/durum")
@login_required
def update_status(lead_id):
    status = request.form.get("status", "Yeni")
    if status not in {"Yeni", "İşlemde", "Tamamlandı"}:
        abort(400)
    with db() as con:
        con.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
    return redirect(url_for("dashboard"))

@app.get("/yonetim/dosya/<int:lead_id>")
@login_required
def private_file(lead_id):
    with db() as con:
        lead = con.execute("SELECT file_name FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not lead or not lead["file_name"]:
        abort(404)
    return send_from_directory(UPLOAD_DIR, lead["file_name"], as_attachment=False, max_age=0)

@app.errorhandler(413)
def too_large(_):
    return "Dosya çok büyük. En fazla " + str(MAX_MB) + " MB yükleyebilirsiniz.", 413

if __name__ == "__main__":
    # Local testing only. Use a production WSGI server and HTTPS when deployed.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
