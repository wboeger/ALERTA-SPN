"""Pipeline principal: harvest (OpenAlex) -> match -> alert -> notify.
Roda via cron (ex: diário) ou manualmente: python main.py
"""
import db
from harvesters import openalex
from taxon_match import evaluate_article
import report


def _process(sub, article, evaluation_fn):
    """Insere artigo (idempotente), avalia relevância se ainda não visto,
    cria alerta se novo. evaluation_fn(article) -> dict avaliação | None."""
    already_seen = db.article_exists(article["source_id"])
    article_id = db.insert_article(**article)

    if not already_seen:
        evaluation = evaluation_fn(article)
        if evaluation is None:
            return False
        db.insert_article_taxon(article_id, **evaluation)

    return db.create_alert_if_new(sub["id"], article_id)


def run_pipeline():
    db.init_db()
    subs = db.active_subscriptions()
    if not subs:
        print("Nenhuma inscrição ativa.")
        return

    cache = {}  # (taxon_name) -> artigos já buscados nessa run
    novos_alertas = 0

    for sub in subs:
        taxon_name = sub["taxon_name"]
        uf = sub["uf"]

        if taxon_name not in cache:
            cache[taxon_name] = openalex.search_taxon_articles(taxon_name)

        for article in cache[taxon_name]:
            if _process(sub, article, lambda a: evaluate_article(a, taxon_name, uf)):
                novos_alertas += 1

    print(f"{novos_alertas} novo(s) alerta(s) gerado(s).")

    path = report.write_report()
    print(f"Resultado gravado em: {path}")


if __name__ == "__main__":
    run_pipeline()
