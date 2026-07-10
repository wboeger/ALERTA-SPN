"""Busca sob demanda: sem persistência, sem inscrição. Cada chamada roda
a busca na hora e devolve os resultados relevantes já formatados."""
import calendar
import datetime as dt

from harvesters import openalex
from taxon_match import evaluate_article


def parse_from_date(raw: str) -> str:
    """Data inicial (De): ano, ano-mês, ou data completa. Obrigatória.
    Parcial vira o primeiro dia do período (ex: '2020' -> '2020-01-01')."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Data inicial (De) é obrigatória.")
    if len(raw) == 4 and raw.isdigit():
        raw = f"{raw}-01-01"
    elif len(raw) == 7:
        raw = f"{raw}-01"
    try:
        return dt.date.fromisoformat(raw).isoformat()
    except ValueError:
        raise ValueError(f"Data inicial inválida: '{raw}'. Use AAAA, AAAA-MM ou AAAA-MM-DD.")


def parse_to_date(raw: str) -> str:
    """Data final (Até): ano, ano-mês, ou data completa. Vazio = hoje.
    Parcial vira o último dia do período (ex: '2020' -> '2020-12-31')."""
    raw = (raw or "").strip()
    if not raw:
        return dt.date.today().isoformat()
    if len(raw) == 4 and raw.isdigit():
        raw = f"{raw}-12-31"
    elif len(raw) == 7:
        year, month = raw.split("-")
        last_day = calendar.monthrange(int(year), int(month))[1]
        raw = f"{raw}-{last_day:02d}"
    try:
        return dt.date.fromisoformat(raw).isoformat()
    except ValueError:
        raise ValueError(f"Data final inválida: '{raw}'. Use AAAA, AAAA-MM ou AAAA-MM-DD.")


def run_search(taxon_name: str, uf: str, from_date: str, to_date: str):
    articles = openalex.search_taxon_articles(taxon_name, from_date, to_date)
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


def format_txt(taxon_name: str, uf: str, from_date: str, to_date: str, results: list) -> str:
    lines = [
        f"Resultado da busca — {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Táxon: {taxon_name}" + (f" | UF: {uf}" if uf else ""),
        f"Período: {from_date} a {to_date}",
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
