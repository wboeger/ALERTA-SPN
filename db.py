import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    taxon_name TEXT NOT NULL,
    taxon_rank TEXT,
    uf TEXT,                    -- sigla de estado (opcional): filtra menção a esse estado no texto
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT UNIQUE,      -- id OpenAlex
    doi TEXT,
    title TEXT,
    abstract TEXT,
    authors TEXT,                -- "Sobrenome A; Sobrenome B; ..."
    journal TEXT,
    publication_year INTEGER,
    volume TEXT,
    issue TEXT,
    first_page TEXT,
    last_page TEXT,
    pub_date TEXT,
    source TEXT,
    processed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS article_taxa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id),
    taxon_name TEXT,
    record_type TEXT,
    brazil_match INTEGER DEFAULT 0,
    zoobank_lsid TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER REFERENCES subscriptions(id),
    article_id INTEGER REFERENCES articles(id),
    sent_at TEXT,
    status TEXT DEFAULT 'pending',
    UNIQUE(subscription_id, article_id)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def add_subscription(user_email: str, taxon_name: str, taxon_rank: str = None, uf: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO subscriptions (user_email, taxon_name, taxon_rank, uf) VALUES (?, ?, ?, ?)",
            (user_email, taxon_name, taxon_rank, uf),
        )


def active_subscriptions():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM subscriptions WHERE active = 1").fetchall()


def article_exists(source_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM articles WHERE source_id = ?", (source_id,)).fetchone()
        return row is not None


def insert_article(source_id, doi, title, abstract, authors, journal, publication_year,
                    volume, issue, first_page, last_page, pub_date, source) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO articles
               (source_id, doi, title, abstract, authors, journal, publication_year,
                volume, issue, first_page, last_page, pub_date, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_id, doi, title, abstract, authors, journal, publication_year,
             volume, issue, first_page, last_page, pub_date, source),
        )
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute("SELECT id FROM articles WHERE source_id = ?", (source_id,)).fetchone()
        return row["id"]


def insert_article_taxon(article_id, taxon_name, record_type, brazil_match, zoobank_lsid):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO article_taxa (article_id, taxon_name, record_type, brazil_match, zoobank_lsid)
               VALUES (?, ?, ?, ?, ?)""",
            (article_id, taxon_name, record_type, int(brazil_match), zoobank_lsid),
        )


def create_alert_if_new(subscription_id, article_id) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO alerts (subscription_id, article_id, status) VALUES (?, ?, 'pending')",
            (subscription_id, article_id),
        )
        return cur.rowcount > 0


def pending_alerts_by_user():
    """Agrupa alerts pendentes por email pra digest."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT a.id as alert_id, s.user_email, s.taxon_name,
                      art.title, art.doi, art.authors, art.journal, art.publication_year,
                      art.volume, art.issue, art.first_page, art.last_page,
                      art.source_id, at.record_type, at.zoobank_lsid
               FROM alerts a
               JOIN subscriptions s ON s.id = a.subscription_id
               JOIN articles art ON art.id = a.article_id
               LEFT JOIN article_taxa at ON at.article_id = art.id AND at.taxon_name = s.taxon_name
               WHERE a.status = 'pending'
               ORDER BY s.user_email"""
        ).fetchall()
    grouped = {}
    for r in rows:
        grouped.setdefault(r["user_email"], []).append(r)
    return grouped


def mark_alerts_sent(alert_ids):
    with get_conn() as conn:
        conn.executemany(
            "UPDATE alerts SET status = 'sent', sent_at = datetime('now') WHERE id = ?",
            [(aid,) for aid in alert_ids],
        )
