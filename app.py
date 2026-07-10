"""Interface web (Flask) pro sistema de alerta de fauna do Brasil.
Sem persistência: usuário digita táxon/UF/período a cada visita, busca roda na hora.
Local: python3 app.py  ->  http://127.0.0.1:5000
Produção (Railway): gunicorn app:app (ver Procfile)
"""
import os

from flask import Flask, render_template, request, flash, Response

from taxon_match import is_valid_taxon_name
from config import STATE_KEYWORDS
from search import run_search, format_reference, zoobank_link, format_txt, parse_from_date, parse_to_date

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-in-production")


@app.route("/")
def index():
    return render_template("index.html", states=sorted(STATE_KEYWORDS), results=None)


def _validate(taxon_name, uf, from_raw, to_raw):
    """Valida entrada. Retorna (from_date, to_date) ISO ou levanta ValueError."""
    if not is_valid_taxon_name(taxon_name):
        raise ValueError(f"Nome de taxon inválido: '{taxon_name}'. Use 'Genus' ou 'Genus species'.")
    if uf and uf not in STATE_KEYWORDS:
        raise ValueError(f"UF inválida: '{uf}'.")
    from_date = parse_from_date(from_raw)
    to_date = parse_to_date(to_raw)
    if from_date > to_date:
        raise ValueError(f"Data inicial ({from_date}) posterior à data final ({to_date}).")
    return from_date, to_date


@app.route("/search", methods=["POST"])
def search():
    taxon_name = request.form.get("taxon_name", "").strip()
    uf = request.form.get("uf", "").strip().upper() or None
    from_raw = request.form.get("from_date", "").strip()
    to_raw = request.form.get("to_date", "").strip()

    try:
        from_date, to_date = _validate(taxon_name, uf, from_raw, to_raw)
    except ValueError as e:
        flash(str(e), "error")
        return render_template(
            "index.html", states=sorted(STATE_KEYWORDS), results=None,
            taxon_name=taxon_name, uf=uf, from_date=from_raw, to_date=to_raw,
        )

    results = run_search(taxon_name, uf, from_date, to_date)

    return render_template(
        "index.html",
        states=sorted(STATE_KEYWORDS),
        taxon_name=taxon_name,
        uf=uf,
        from_date=from_date,
        to_date=to_date,
        results=results,
        format_reference=format_reference,
        zoobank_link=zoobank_link,
    )


@app.route("/download")
def download():
    taxon_name = request.args.get("taxon_name", "").strip()
    uf = request.args.get("uf", "").strip().upper() or None
    from_raw = request.args.get("from_date", "").strip()
    to_raw = request.args.get("to_date", "").strip()

    try:
        from_date, to_date = _validate(taxon_name, uf, from_raw, to_raw)
    except ValueError as e:
        return str(e), 400

    results = run_search(taxon_name, uf, from_date, to_date)
    content = format_txt(taxon_name, uf, from_date, to_date, results)

    filename = f"resultado_busca_{taxon_name.replace(' ', '_')}.txt"
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
