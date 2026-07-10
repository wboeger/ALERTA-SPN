"""Validação de nome de taxon (formato, sem dependência externa), detecção
de menção ao Brasil/UF, classificação de tipo de registro e extração de
identificador ZooBank (LSID) citado no próprio artigo.

Não usa GBIF nem consulta ZooBank ao vivo (site bloqueia acesso automatizado
por anti-bot). O LSID ZooBank, quando existe, é auto-declarado pelo artigo
(exigência do ICZN para publicações eletrônicas de nomes novos), então
extraímos direto do texto já obtido via busca de literatura.
"""
import re

from config import BRAZIL_KEYWORDS, RECORD_TYPE_PATTERNS, STATE_KEYWORDS

# Genus | Genus species | Familia (uma palavra iniciada maiúscula, ou duas: maiúscula + minúscula)
TAXON_NAME_PATTERN = re.compile(r"^[A-Z][a-zA-Z-]+(\s[a-z][a-zA-Z-]+)?$")

ZOOBANK_LSID_PATTERN = re.compile(r"urn:lsid:zoobank\.org:[a-zA-Z]+:[0-9A-Fa-f-]{36}")


def is_valid_taxon_name(taxon_name: str) -> bool:
    return bool(TAXON_NAME_PATTERN.match(taxon_name.strip()))


def mentions_brazil(text: str) -> bool:
    text_l = (text or "").lower()
    return any(kw in text_l for kw in BRAZIL_KEYWORDS)


def mentions_state(text: str, uf: str) -> bool:
    patterns = STATE_KEYWORDS.get(uf.upper())
    if not patterns:
        return False
    text_l = (text or "").lower()
    return any(re.search(p, text_l) for p in patterns)


def classify_record_type(text: str) -> str:
    text_l = (text or "").lower()
    for record_type, patterns in RECORD_TYPE_PATTERNS.items():
        if any(p in text_l for p in patterns):
            return record_type
    return "unclassified"


def extract_zoobank_lsid(text: str):
    match = ZOOBANK_LSID_PATTERN.search(text or "")
    return match.group(0) if match else None


def evaluate_article(article: dict, taxon_name: str, uf: str = None):
    """Retorna avaliação do artigo pro taxon buscado, ou None se não relevante."""
    full_text = f"{article['title']} {article['abstract']}"

    if not mentions_brazil(full_text):
        return None
    if uf and not mentions_state(full_text, uf):
        return None

    return {
        "taxon_name": taxon_name,
        "record_type": classify_record_type(full_text),
        "brazil_match": True,
        "zoobank_lsid": extract_zoobank_lsid(full_text),
    }
