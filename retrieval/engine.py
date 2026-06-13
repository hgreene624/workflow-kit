"""AI-Memory retrieval engine: keyword (BM25/FTS5) + wikilink/backlink graph.

A single sqlite database holds three things, all rebuildable from the markdown
corpus and therefore a DISPOSABLE CACHE, never a source of truth (NFR-2/NFR-3):

  docs(id, path, name, title, mtime)          -- one row per .md file
  docs_fts(name, title, body)                 -- FTS5 BM25 keyword index
  links(src_id, dst_name)                     -- one row per wikilink edge

FTS5 tokenizer keeps '-', '_', '.', '@' as token chars so identifiers like
`flora-postgres`, `myarroyo.com`, `cc_portal`, and `@anthropic-ai` survive as
single tokens (FR-5: proper nouns, identifiers, codes, wikilinks).

Stdlib only.
"""
from __future__ import annotations

import os
import sqlite3
import time

from corpus import DEFAULT_CORPUS, iter_markdown

DEFAULT_INDEX = os.environ.get(
    "AIMEM_INDEX",
    os.path.expanduser("~/.cache/ai-memory/index.db"),
)

# Keep identifier punctuation inside tokens. Without this, unicode61 would
# split `flora-postgres` into `flora` + `postgres` and lose exact-identifier
# retrieval, which is the whole point of FR-5.
_TOKENIZE = "unicode61 tokenchars '-_.@' remove_diacritics 2"


def connect(index_path: str = DEFAULT_INDEX) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
    con = sqlite3.connect(index_path)
    con.row_factory = sqlite3.Row
    return con


def build(corpus_root: str = DEFAULT_CORPUS, index_path: str = DEFAULT_INDEX) -> dict:
    """(Re)build the index from scratch. Returns build stats."""
    t0 = time.time()
    con = connect(index_path)
    cur = con.cursor()
    # Drop and recreate -- the index is disposable.
    cur.executescript(
        """
        DROP TABLE IF EXISTS docs_fts;
        DROP TABLE IF EXISTS links;
        DROP TABLE IF EXISTS docs;
        DROP TABLE IF EXISTS meta;
        CREATE TABLE docs (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            name TEXT,
            title TEXT,
            mtime REAL
        );
        CREATE INDEX idx_docs_name ON docs(name);
        CREATE TABLE links (
            src_id INTEGER,
            dst_name TEXT
        );
        CREATE INDEX idx_links_src ON links(src_id);
        CREATE INDEX idx_links_dst ON links(dst_name);
        CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
        """
    )
    cur.execute(
        f"CREATE VIRTUAL TABLE docs_fts USING fts5("
        f"name, title, body, tokenize=\"{_TOKENIZE}\")"
    )

    n_docs = 0
    n_links = 0
    for doc in iter_markdown(corpus_root):
        cur.execute(
            "INSERT INTO docs(path, name, title, mtime) VALUES (?,?,?,?)",
            (doc.path, doc.name, doc.title, doc.mtime),
        )
        doc_id = cur.lastrowid
        cur.execute(
            "INSERT INTO docs_fts(rowid, name, title, body) VALUES (?,?,?,?)",
            (doc_id, doc.name, doc.title, doc.body),
        )
        for dst in doc.links:
            cur.execute(
                "INSERT INTO links(src_id, dst_name) VALUES (?,?)",
                (doc_id, dst),
            )
            n_links += 1
        n_docs += 1

    cur.execute(
        "INSERT INTO meta(k,v) VALUES ('corpus_root',?),('built_at',?)",
        (os.path.abspath(os.path.expanduser(corpus_root)), str(time.time())),
    )
    con.commit()
    con.close()
    return {
        "docs": n_docs,
        "links": n_links,
        "index_path": index_path,
        "corpus_root": corpus_root,
        "seconds": round(time.time() - t0, 2),
    }


def _fts_query(terms: str) -> str:
    """Build a safe FTS5 MATCH string: quote each whitespace token as a
    literal so identifier punctuation and FTS operators never break parsing."""
    toks = terms.split()
    quoted = ['"' + t.replace('"', '""') + '"' for t in toks if t]
    return " ".join(quoted)


def search(query: str, limit: int = 10, index_path: str = DEFAULT_INDEX) -> list:
    """Keyword/BM25 search. Returns ranked list of dicts (best first)."""
    con = connect(index_path)
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT d.name AS name, d.title AS title, d.path AS path,
               bm25(docs_fts) AS score
        FROM docs_fts
        JOIN docs d ON d.id = docs_fts.rowid
        WHERE docs_fts MATCH ?
        ORDER BY score ASC
        LIMIT ?
        """,
        (_fts_query(query), limit),
    ).fetchall()
    con.close()
    out = []
    for i, r in enumerate(rows, 1):
        out.append({
            "rank": i,
            "name": r["name"],
            "title": r["title"],
            "path": r["path"],
            "score": round(r["score"], 4),  # FTS5 bm25: lower = more relevant
        })
    return out


def _resolve_doc(cur, artifact: str):
    """Find a doc row by exact name, then by path, then by case-insensitive
    name. Returns the sqlite Row or None."""
    base = os.path.basename(artifact)
    if base.lower().endswith(".md"):
        base = base[:-3]
    row = cur.execute("SELECT id, name, title, path FROM docs WHERE name = ?",
                      (base,)).fetchone()
    if row:
        return row
    row = cur.execute("SELECT id, name, title, path FROM docs WHERE path = ?",
                      (artifact,)).fetchone()
    if row:
        return row
    return cur.execute(
        "SELECT id, name, title, path FROM docs WHERE name = ? COLLATE NOCASE",
        (base,)).fetchone()


def neighbors(artifact: str, index_path: str = DEFAULT_INDEX) -> dict:
    """1-hop wikilink expansion. Returns forward links (what this artifact
    points to) and backlinks (what points to it) -- FR-6."""
    con = connect(index_path)
    cur = con.cursor()
    doc = _resolve_doc(cur, artifact)
    if not doc:
        con.close()
        return {"artifact": artifact, "found": False,
                "forward": [], "backlinks": []}

    forward = [r["dst_name"] for r in cur.execute(
        "SELECT DISTINCT dst_name FROM links WHERE src_id = ? ORDER BY dst_name",
        (doc["id"],)).fetchall()]

    backlinks = [r["name"] for r in cur.execute(
        """SELECT DISTINCT d.name AS name
           FROM links l JOIN docs d ON d.id = l.src_id
           WHERE l.dst_name = ? ORDER BY d.name""",
        (doc["name"],)).fetchall()]
    con.close()
    return {
        "artifact": doc["name"],
        "title": doc["title"],
        "path": doc["path"],
        "found": True,
        "forward": forward,
        "backlinks": backlinks,
    }


def query(q: str, limit: int = 10, expand: bool = True,
          index_path: str = DEFAULT_INDEX) -> dict:
    """Unified retrieval: keyword hits + 1-hop link expansion of the top hit.

    This is the agent-facing call (Task 14): one query in, ranked keyword
    results plus the relationship context of the best match out.
    """
    hits = search(q, limit=limit, index_path=index_path)
    result = {"query": q, "keyword": hits, "links": None}
    if expand and hits:
        result["links"] = neighbors(hits[0]["name"], index_path=index_path)
    return result


def stats(index_path: str = DEFAULT_INDEX) -> dict:
    con = connect(index_path)
    cur = con.cursor()
    try:
        ndocs = cur.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        nlinks = cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        meta = {r["k"]: r["v"] for r in cur.execute("SELECT k,v FROM meta")}
    except sqlite3.OperationalError:
        con.close()
        return {"built": False}
    con.close()
    return {"built": True, "docs": ndocs, "links": nlinks,
            "index_path": index_path, **meta}
