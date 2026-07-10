"""Harvester OpenAlex: busca artigos novos mencionando um taxon.

API gratuita, sem chave. Docs: https://docs.openalex.org
"""
import re
import requests

from config import OPENALEX_MAILTO

BASE_URL = "https://api.openalex.org/works"


def search_taxon_articles(taxon_name: str, from_date: str, to_date: str):
    """Busca works cujo título/abstract cite o taxon, publicados entre
    from_date e to_date (ISO YYYY-MM-DD, ambos inclusive)."""
    params = {
        "filter": (
            f"title_and_abstract.search:{taxon_name},"
            f"from_publication_date:{from_date},"
            f"to_publication_date:{to_date},"
            f"type:article"
        ),
        "per_page": 50,
        "sort": "publication_date:desc",
    }
    if OPENALEX_MAILTO:
        params["mailto"] = OPENALEX_MAILTO

    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return [_to_article(w) for w in data.get("results", [])]


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
