"""Busca sob demanda: sem persistência, sem inscrição. Cada chamada roda
a busca na hora e devolve os resultados relevantes já formatados."""
import datetime as dt

from harvesters import openalex
from taxon_match import evaluate_article


def run_search(taxon_name: str, uf: str = None, window_days: int = 30):
    articles = openalex.search_taxon_articles(taxon_name, window_days=window_days)
    results = []
    for article in articles:
        evaluation = evaluate_article(article, taxon_name, uf)
        if evaluation is None:
            continue
        results.append({**article, **evaluation})
    return results


def format_reference(r: dict) -> str:
    authors = r["authors"] or "Autor não informado"
    year = r["publication_year"] or "s.d."
    title = r["title"]
    journal = r["journal"] or "periódico não identificado"

    pages = ""
    if r["first_page"]:
        pages = f", p. {r['first_page']}" + (f"-{r['last_page']}" if r["last_page"] else "")
    volume = f", v. {r['volume']}" if r["volume"] else ""
    issue = f", n. {r['issue']}" if r["issue"] else ""

    ref = f"{authors} ({year}). {title}. {journal}{volume}{issue}{pages}."
    if r["doi"]:
        ref += f" DOI: {r['doi']}"
    return ref


def zoobank_link(r: dict):
    if not r.get("zoobank_lsid"):
        return None
    uuid = r["zoobank_lsid"].rsplit(":", 1)[-1]
    return f"https://zoobank.org/References/{uuid}"


def format_txt(taxon_name: str, uf: str, results: list) -> str:
    lines = [
        f"Resultado da busca — {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Táxon: {taxon_name}" + (f" | UF: {uf}" if uf else ""),
        "=" * 60,
        "",
    ]
    if not results:
        lines.append("Nenhum artigo novo encontrado.")
    for r in results:
        lines.append(f"Espécie/taxon: {r['taxon_name']}")
        if r["record_type"] and r["record_type"] != "unclassified":
            lines.append(f"Tipo de registro: {r['record_type']}")
        lines.append(f"Referência: {format_reference(r)}")
        link = zoobank_link(r)
        if link:
            lines.append(f"ZooBank: {r['zoobank_lsid']} ({link})")
        if not r["doi"]:
            lines.append(f"Link: https://openalex.org/{r['source_id'].rsplit('/', 1)[-1]}")
        lines.append("")
    return "\n".join(lines)
