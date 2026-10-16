"""Detection history and object search (Information Retrieval part).

Deep learning (detector.py) looks at a NEW image and finds objects.
This module never runs the model. It stores saved detections in SQLite and
retrieves the saved records that match a text query.

Storage
  records  one row per saved detection (time, image files, source)
  objects  one row per detected object (record_id, label, confidence, box)
           with an index on label, so "which records contain a bottle?" is a
           lookup, not a scan. This label -> records lookup is an inverted index.

Ranking (keyword match, no machine learning)
  1. records that contain more of the searched object names come first
  2. then records with more matching objects (3 people beats 1 person)
  3. then higher average confidence of the matching objects
  4. ties: newest record first
"""
import difflib
import os
import re
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("data", "history.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,              -- local time, 'YYYY-MM-DD HH:MM:SS'
    source TEXT NOT NULL,                  -- 'camera' or 'upload'
    image_file TEXT NOT NULL,
    annotated_file TEXT NOT NULL,
    width INTEGER, height INTEGER,
    note TEXT
);
CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    x1 REAL, y1 REAL, x2 REAL, y2 REAL
);
CREATE INDEX IF NOT EXISTS idx_objects_label ON objects(label);
CREATE INDEX IF NOT EXISTS idx_objects_record ON objects(record_id);
CREATE INDEX IF NOT EXISTS idx_records_created ON records(created_at);
"""

# everyday words people type -> YOLO (COCO) class names
SYNONYMS = {
    "people": "person", "persons": "person", "man": "person", "men": "person", "woman": "person",
    "women": "person", "human": "person", "humans": "person", "boy": "person", "girl": "person",
    "phone": "cell phone", "mobile": "cell phone", "smartphone": "cell phone", "phones": "cell phone",
    "television": "tv", "monitor": "tv", "sofa": "couch", "table": "dining table",
    "plant": "potted plant", "mug": "cup", "bike": "bicycle", "motorbike": "motorcycle",
    "plane": "airplane", "aeroplane": "airplane", "ball": "sports ball", "glass": "wine glass",
    "racket": "tennis racket", "bag": "handbag", "puppy": "dog", "kitten": "cat",
}


def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with connect() as con:
        con.executescript(SCHEMA)


# ------------------------------------------------------------------ saving
def save_record(source, image_file, annotated_file, width, height, detections, note=None):
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO records(created_at, source, image_file, annotated_file, width, height, note)"
            " VALUES (?,?,?,?,?,?,?)", (created, source, image_file, annotated_file, width, height, note))
        rid = cur.lastrowid
        con.executemany(
            "INSERT INTO objects(record_id, label, confidence, x1, y1, x2, y2) VALUES (?,?,?,?,?,?,?)",
            [(rid, d["label"], d["confidence"], *d["box"]) for d in detections])
    return rid


def delete_record(rid):
    with connect() as con:
        row = con.execute("SELECT image_file, annotated_file FROM records WHERE id = ?", (rid,)).fetchone()
        if row is None:
            return None
        con.execute("DELETE FROM records WHERE id = ?", (rid,))
    return dict(row)


def clear_all():
    with connect() as con:
        files = [dict(r) for r in con.execute("SELECT image_file, annotated_file FROM records")]
        con.execute("DELETE FROM objects")
        con.execute("DELETE FROM records")
    return files


# ------------------------------------------------------------------ query parsing
def parse_query(query, class_names):
    """Turns free text into known object names.
    'People and bottles' -> (['person', 'bottle'], [], {})
    Unknown words come back with 'did you mean' suggestions."""
    classes = set(class_names)
    text = re.sub(r"[^a-z ]+", " ", (query or "").lower())
    text = re.sub(r"\s+", " ", text).strip()
    terms, unknown = [], []
    # multi-word classes first: 'cell phone', 'dining table', 'traffic light' ...
    for name in sorted((c for c in classes if " " in c), key=len, reverse=True):
        for form in (name, name + "s"):
            if re.search(rf"\b{form}\b", text):
                terms.append(name)
                text = re.sub(rf"\b{form}\b", " ", text)
    for w in text.split():
        if w in ("and", "or", "with", "the", "a", "an", "of", "in", "show", "find"):
            continue
        cand = None
        if w in classes:
            cand = w
        elif w in SYNONYMS:
            cand = SYNONYMS[w]
        elif w.endswith("es") and w[:-2] in classes:
            cand = w[:-2]
        elif w.endswith("s") and w[:-1] in classes:
            cand = w[:-1]
        if cand:
            terms.append(cand)
        else:
            unknown.append(w)
    terms = list(dict.fromkeys(terms))            # unique, keep order
    suggestions = {}
    for w in unknown:
        close = difflib.get_close_matches(w, list(classes) + list(SYNONYMS), n=4, cutoff=0.7)
        suggestions[w] = list(dict.fromkeys(SYNONYMS.get(c, c) for c in close))[:3]
    return terms, unknown, suggestions


# ------------------------------------------------------------------ search
def search(query="", label=None, date_from=None, date_to=None, min_conf=0.0,
           sort="relevance", limit=60, class_names=()):
    terms, unknown, suggestions = parse_query(query, class_names)
    if label:
        terms = list(dict.fromkeys(terms + [label]))
    info = {"terms": terms, "unknown": unknown, "suggestions": suggestions}

    where, params = [], []
    if date_from:
        where.append("date(r.created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        where.append("date(r.created_at) <= date(?)")
        params.append(date_to)

    with connect() as con:
        if terms:
            # inverted-index lookup: objects whose label is one of the terms
            ph = ",".join("?" * len(terms))
            sql = f"""
                SELECT r.*, COUNT(DISTINCT o.label) AS matched_terms,
                       COUNT(o.id) AS matched_objects, AVG(o.confidence) AS match_conf
                FROM records r JOIN objects o ON o.record_id = r.id
                WHERE o.label IN ({ph}) AND o.confidence >= ?
                {"AND " + " AND ".join(where) if where else ""}
                GROUP BY r.id"""
            rows = [dict(x) for x in con.execute(sql, terms + [min_conf] + params)]
            if label:   # the object-type filter is a hard requirement
                rows = [r for r in rows if label in _labels(con, r["id"], min_conf)]
        elif query.strip() and unknown:
            rows = []   # words typed, but none is an object the model knows
        else:
            sql = f"""SELECT r.*, 0 AS matched_terms, 0 AS matched_objects, NULL AS match_conf
                      FROM records r {"WHERE " + " AND ".join(where) if where else ""}"""
            rows = [dict(x) for x in con.execute(sql, params)]
            if min_conf > 0:
                rows = [r for r in rows if _labels(con, r["id"], min_conf)]

        if sort == "oldest":
            rows.sort(key=lambda r: (r["created_at"], r["id"]))
        elif sort == "newest" or not terms:
            rows.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
        else:   # relevance, newest as the tie-breaker
            rows.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
            rows.sort(key=lambda r: (r["matched_terms"], r["matched_objects"], round(r["match_conf"] or 0, 3)),
                      reverse=True)
        total = len(rows)
        rows = rows[:limit]
        for r in rows:
            r["objects"] = [dict(o) for o in con.execute(
                "SELECT label, confidence FROM objects WHERE record_id = ? ORDER BY confidence DESC", (r["id"],))]
            r["match_conf"] = None if r["match_conf"] is None else round(r["match_conf"], 4)
    return {"items": rows, "total": total, **info}


def _labels(con, rid, min_conf):
    return {x["label"] for x in con.execute(
        "SELECT label FROM objects WHERE record_id = ? AND confidence >= ?", (rid, min_conf))}


def get_record(rid):
    with connect() as con:
        r = con.execute("SELECT * FROM records WHERE id = ?", (rid,)).fetchone()
        if r is None:
            return None
        r = dict(r)
        r["objects"] = [dict(o) for o in con.execute(
            "SELECT label, confidence, x1, y1, x2, y2 FROM objects WHERE record_id = ? ORDER BY confidence DESC", (rid,))]
    return r


def label_counts():
    """Object types present in saved records, for the filter list."""
    with connect() as con:
        return [dict(r) for r in con.execute(
            "SELECT label, COUNT(DISTINCT record_id) AS records, COUNT(*) AS objects"
            " FROM objects GROUP BY label ORDER BY records DESC, label")]


def stats():
    with connect() as con:
        n = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        last = con.execute("SELECT MAX(created_at) FROM records").fetchone()[0]
    return {"records": n, "last_saved": last}
