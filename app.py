"""Interface web (Flask) pro sistema de alerta de fauna do Brasil.
Local: python3 app.py  ->  http://127.0.0.1:5000
Produção (Railway): gunicorn app:app (ver Procfile)
"""
import os

from flask import Flask, render_template, request, redirect, url_for, flash

import db
from taxon_match import is_valid_taxon_name
from config import STATE_KEYWORDS
from main import run_pipeline

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-in-production")

db.init_db()


@app.route("/")
def index():
    subs = db.active_subscriptions()
    return render_template("index.html", subs=subs, states=sorted(STATE_KEYWORDS))


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    taxon_name = request.form.get("taxon_name", "").strip()
    uf = request.form.get("uf", "").strip().upper() or None

    if not email or "@" not in email:
        flash("Email inválido.", "error")
    elif not is_valid_taxon_name(taxon_name):
        flash(f"Nome de taxon inválido: '{taxon_name}'. Use 'Genus' ou 'Genus species'.", "error")
    elif uf and uf not in STATE_KEYWORDS:
        flash(f"UF inválida: '{uf}'.", "error")
    else:
        taxon_rank = "species" if " " in taxon_name else "genus_or_higher"
        db.add_subscription(user_email=email, taxon_name=taxon_name, taxon_rank=taxon_rank, uf=uf)
        flash(f"Inscrição criada: {email} -> {taxon_name}" + (f" ({uf})" if uf else ""), "ok")

    return redirect(url_for("index"))


@app.route("/run", methods=["POST"])
def run():
    log_lines = []
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_pipeline()
    log_lines = buf.getvalue().strip().splitlines()

    report_content = None
    for line in log_lines:
        if line.startswith("Resultado gravado em:"):
            path = line.split(":", 1)[1].strip()
            with open(path, encoding="utf-8") as f:
                report_content = f.read()

    subs = db.active_subscriptions()
    return render_template(
        "index.html",
        subs=subs,
        states=sorted(STATE_KEYWORDS),
        run_log=log_lines,
        report_content=report_content,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
