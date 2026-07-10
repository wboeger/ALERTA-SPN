import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("ALERTA_DB_PATH", "alerta.db")

# Identifica requisições no "polite pool" do OpenAlex (evita rate-limit agressivo)
OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO", "")

# janela de busca (dias) em cada execução do harvester
HARVEST_WINDOW_DAYS = int(os.getenv("HARVEST_WINDOW_DAYS", "3"))

BRAZIL_KEYWORDS = ["brazil", "brasil", "brazilian", "brasileir"]
RECORD_TYPE_PATTERNS = {
    "new_species": ["new species", "sp. nov", "spec. nov", "gen. nov", "espécie nova"],
    "new_record": ["new record", "first record", "novo registro", "primeiro registro"],
    "range_extension": ["range extension", "extensão de distribuição", "distributional extension"],
    "checklist": ["checklist", "faunal list", "lista de espécies"],
}

# nomes de estado preservam acento propositalmente: "pará" (estado) vs "para" (preposição comum)
STATE_KEYWORDS = {
    "AC": ["acre"],
    "AL": ["alagoas"],
    "AP": ["amapá"],
    "AM": ["amazonas"],
    "BA": ["bahia"],
    "CE": ["ceará"],
    "DF": ["distrito federal"],
    "ES": ["espírito santo"],
    "GO": ["goiás"],
    "MA": ["maranhão"],
    "MT": ["mato grosso(?! do sul)"],
    "MS": ["mato grosso do sul"],
    "MG": ["minas gerais"],
    "PA": ["pará"],
    "PB": ["paraíba"],
    "PR": ["paraná"],
    "PE": ["pernambuco"],
    "PI": ["piauí"],
    "RJ": ["rio de janeiro"],
    "RN": ["rio grande do norte"],
    "RS": ["rio grande do sul"],
    "RO": ["rondônia"],
    "RR": ["roraima"],
    "SC": ["santa catarina"],
    "SP": ["são paulo"],
    "SE": ["sergipe"],
    "TO": ["tocantins"],
}
