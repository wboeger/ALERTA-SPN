"""Harvester OpenAlex: busca artigos novos mencionando um taxon.

API gratuita, sem chave. Docs: https://docs.openalex.org
"""
import re
import requests

from config import OPENALEX_MAILTO

BASE_URL = "https://api.openalex.org/works"

PER_PAGE = 200
MAX_RESULTS = 1000  # teto de segurança: evita busca genérica (ex: período de 70 anos) travar a página


def search_taxon_articles(taxon_name: str, from_date: str, to_date: str):
    """Busca works cujo título/abstract cite o taxon, publicados entre
    from_date e to_date (ISO YYYY-MM-DD, ambos inclusive). Pagina via cursor
    até MAX_RESULTS pra não perder registros antigos num período largo
    (sem paginação, 'sort=desc' + 1 página só mostraria os mais recentes).
    Retorna (artigos, truncado: bool, total_encontrado_na_api: int)."""
    articles = []
    cursor = "*"
    total_count = None

    while cursor and len(articles) < MAX_RESULTS:
        params = {
            "filter": (
                f"title_and_abstract.search:{taxon_name},"
                f"from_publication_date:{from_date},"
                f"to_publication_date:{to_date},"
                f"type:article"
            ),
            "per_page": PER_PAGE,
            "cursor": cursor,
            "sort": "publication_date:desc",
        }
        if OPENALEX_MAILTO:
            params["mailto"] = OPENALEX_MAILTO

        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if total_count is None:
            total_count = data.get("meta", {}).get("count", 0)

        results = data.get("results", [])
        if not results:
            break
        articles.extend(_to_article(w) for w in results)
        cursor = data.get("meta", {}).get("next_cursor")

    truncated = total_count is not None and total_count > len(articles)
    return articles, truncated, total_count or 0


def _to_article(w: dict) -> dict:
    primary_location = w.get("primary_location") or {}
    source_info = primary_location.get("source") or {}
    biblio = w.get("biblio") or {}

    authors = "; ".join(
        (a.get("author") or {}).get("display_name", "")
        for a in w.get("authorships", [])
    ).strip("; ")

    return {
        "source_id": w["id"],
        "doi": w.get("doi"),
        "title": _strip_tags(w.get("title") or ""),
        "abstract": _reconstruct_abstract(w.get("abstract_inverted_index")),
        "authors": authors,
        "journal": source_info.get("display_name"),
        "publication_year": w.get("publication_year"),
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "first_page": biblio.get("first_page"),
        "last_page": biblio.get("last_page"),
        "pub_date": w.get("publication_date"),
        "source": "openalex",
    }


def _strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _reconstruct_abstract(inverted_index):
    """OpenAlex retorna abstract como índice invertido {palavra: [posições]}."""
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))
