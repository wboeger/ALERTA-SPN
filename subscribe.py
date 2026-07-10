"""CLI simples pra cadastrar inscrição.
Uso: python subscribe.py "seu@email.com" "Harpia harpyja" [UF]
"""
import sys

import db
from taxon_match import is_valid_taxon_name
from config import STATE_KEYWORDS


def main():
    if len(sys.argv) not in (3, 4):
        print("Uso: python subscribe.py <email> <nome_taxon> [UF]")
        sys.exit(1)

    email, taxon_name = sys.argv[1], sys.argv[2].strip()
    uf = sys.argv[3].upper() if len(sys.argv) == 4 else None

    if not is_valid_taxon_name(taxon_name):
        print(f"Nome de taxon inválido: '{taxon_name}'. Use formato 'Genus' ou 'Genus species'.")
        sys.exit(1)

    if uf and uf not in STATE_KEYWORDS:
        print(f"UF inválida: '{uf}'. Use sigla de estado brasileiro (ex: SP, RJ, AM).")
        sys.exit(1)

    taxon_rank = "species" if " " in taxon_name else "genus_or_higher"

    db.init_db()
    db.add_subscription(user_email=email, taxon_name=taxon_name, taxon_rank=taxon_rank, uf=uf)
    print(f"Inscrição criada: {email} -> {taxon_name}" + (f" (UF: {uf})" if uf else ""))


if __name__ == "__main__":
    main()
