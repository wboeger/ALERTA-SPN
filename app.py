"""Interface web (Flask) pro sistema de alerta de fauna do Brasil.
Sem persistência: usuário digita táxon/UF a cada visita, busca roda na hora.
Local: python3 app.py  ->  http://127.0.0.1:5000
Produção (Railway): gunicorn app:app (ver Procfile)
"""
import os

from flask import Flask, render_template, request, flash, Response

from taxon_match import is_valid_taxon_name
from config import STATE_KEYWORDS
from search import run_search, format_reference, zoobank_link, format_txt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-in-production")

WINDOW_OPTIONS = {
    "1": "1 dia",
    "7": "1 semana",
    "30": "1 mês",
    "365": "1 ano",
}
DEFAULT_WINDOW_DAYS = "30"


def _parse_window_days(raw: str) -> int:
    return int(raw) if raw in WINDOW_OPTIONS else int(DEFAULT_WINDOW_DAYS)


@app.route("/")
def index():
    return render_template(
        "index.html", states=sorted(STATE_KEYWORDS), window_options=WINDOW_OPTIONS,
        window_days=DEFAULT_WINDOW_DAYS, results=None,
    )


@app.route("/search", methods=["POST"])
def search():
    taxon_name = request.form.get("taxon_name", "").strip()
    uf = request.form.get("uf", "").strip().upper() or None
    window_days = _parse_window_days(request.form.get("window_days", ""))

    if not is_valid_taxon_name(taxon_name):
        flash(f"Nome de taxon inválido: '{taxon_name}'. Use 'Genus' ou 'Genus species'.", "error")
        return render_template("index.html", states=sorted(STATE_KEYWORDS), window_options=WINDOW_OPTIONS, window_days=str(window_days), results=None)

    if uf and uf not in STATE_KEYWORDS:
        flash(f"UF inválida: '{uf}'.", "error")
        return render_template("index.html", states=sorted(STATE_KEYWORDS), window_options=WINDOW_OPTIONS, window_days=str(window_days), results=None)

    results = run_search(taxon_name, uf, window_days)

    return render_template(
        "index.html",
        states=sorted(STATE_KEYWORDS),
        window_options=WINDOW_OPTIONS,
        taxon_name=taxon_name,
        uf=uf,
        window_days=str(window_days),
        results=results,
        format_reference=format_reference,
        zoobank_link=zoobank_link,
    )


@app.route("/download")
def download():
    taxon_name = request.args.get("taxon_name", "").strip()
    uf = request.args.get("uf", "").strip().upper() or None
    window_days = _parse_window_days(request.args.get("window_days", ""))

    if not is_valid_taxon_name(taxon_name):
        return "Táxon inválido", 400

    results = run_search(taxon_name, uf, window_days)
    content = format_txt(taxon_name, uf, results)

    filename = f"resultado_busca_{taxon_name.replace(' ', '_')}.txt"
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
