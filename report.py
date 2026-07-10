"""Gera arquivo .txt com o resultado da busca (sem envio de email)."""
import datetime as dt

import db


def _format_reference(r) -> str:
    """Referência bibliográfica no estilo autor-data (ABNT/APA simplificado)."""
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


def _format_entry(r) -> str:
    lines = [f"Espécie/taxon: {r['taxon_name']}"]
    if r["record_type"] and r["record_type"] != "unclassified":
        lines.append(f"Tipo de registro: {r['record_type']}")
    lines.append(f"Referência: {_format_reference(r)}")
    if r["zoobank_lsid"]:
        lsid = r["zoobank_lsid"]
        uuid = lsid.rsplit(":", 1)[-1]
        lines.append(f"ZooBank: {lsid} (https://zoobank.org/References/{uuid})")
    if not r["doi"]:
        lines.append(f"Link: https://openalex.org/{r['source_id'].rsplit('/', 1)[-1]}")
    return "\n".join(lines)


def write_report(output_path: str = None) -> str:
    """Escreve todos os alertas pendentes num .txt agrupado por usuário/inscrição
    e marca como reportados. Retorna o caminho do arquivo gerado."""
    output_path = output_path or f"resultado_busca_{dt.date.today().isoformat()}.txt"

    grouped = db.pending_alerts_by_user()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Resultado da busca — {dt.datetime.now().isoformat(timespec='seconds')}\n")
        f.write("=" * 60 + "\n\n")

        if not grouped:
            f.write("Nenhum artigo novo encontrado nesta execução.\n")
        else:
            for user_email, rows in grouped.items():
                f.write(f"Inscrição: {user_email} ({len(rows)} novo(s) artigo(s))\n")
                f.write("-" * 60 + "\n")
                for r in rows:
                    f.write(_format_entry(r) + "\n\n")
                f.write("\n")

    all_alert_ids = [r["alert_id"] for rows in grouped.values() for r in rows]
    if all_alert_ids:
        db.mark_alerts_sent(all_alert_ids)

    return output_path
