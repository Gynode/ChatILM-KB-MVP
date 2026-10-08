# KB Migration Plan — Dual-Scholastic Epistemic Structure

**Status:** DRAFT for review — not started
**Target:** migrate the existing knowledge in `C:\ChatILM-KB-MVP` into the taxonomy
defined by `2. Euro_Islamic Knowledge Base Structure.docx` (source document:
`C:\Users\gydan\Downloads\2. Euro_Islamic Knowledge Base Structure.docx` — it
lives outside both repos, so this path is the only record of it. A Google Docs
twin exists at `My Drive/2.  Middle East/2a. Qatar/HalalAI-ChatILM/English
version/Design Specs/5. Knowledge Base Design/KB Structure/`.)
**Engine:** PostgreSQL (decision locked)
**Content placement:** content moves into the new structure (decision locked)

---

## 1. Scope

**In scope:** the **Knowledge Base only** — the vector vault at
`KB_ROOT/staging_vault.db`, 13 content tables, **1,310,313 rows**, 7.1 GB.

**Explicitly out of scope:**

- **The TDb.** `KB_ROOT/Truth_Db/Truth_DB.db` (496 KB, the facts ledger) is a
  *separate database with a separate purpose* and is **not touched by this
  plan**. `config.py` keeps them apart: `KB_VAULT_PATH` = vector vault,
  `TDB_PATH` = facts ledger. No step below reads or writes the TDb.
- Re-embedding. All vectors are already 384-dim `all-MiniLM-L6-v2`; none are
  regenerated (see §7.3).
- The internet-extraction pipeline in `KB_INTERNET_EXTRACTION_PLAN.md`. It
  keeps running against whatever store is current; this plan does not change
  its sources.

---

## 2. What the docx actually specifies (and what it doesn't)

The docx is *Dual-Scholastic Epistemic Database Architecture* — four tables:

| Table | Purpose |
|---|---|
| `topics` | the subject registry (`name`, `code`, `description`) |
| `european_scholastic_mapping` | topic → `european_branch` + `scholastic_tier` + rationale |
| `islamic_epistemology_mapping` | topic → `islamic_root` + `traditional_category` + `obligation_level` + justification |
| `topic_relationships` | parent/child edges between topics |

Two findings that shape this plan:

**(a) The schema stores no content.** There is no text, source, or vector
column anywhere in the docx DDL. It is a *classification* schema. Because the
locked decision is that content moves into the new structure, this plan
**extends** the docx with a content table (§5.2). The four docx tables are
adopted verbatim; the extension is the one addition.

**(b) The docx's mapping matrix does not cover our corpus.** Its worked
examples cover ten *modern technical* disciplines (logic, NLP, CS, blockchain,
cybersecurity, AI, quantum, bioethics, digital governance, cyber-hygiene). The
1.31M rows we actually hold are **arXiv physics/maths, the World Factbook,
world history, Quran, Sunnah, Catholic and Anglican texts, and recipe
collections** — *none* of which appear in the matrix. The docx therefore gives
us the **structure** (two roots, branch/root enums, obligation level) and three
**extension rules**, but the classification of our own 972 paths must be
derived and then **reviewed by a human** (§6.3). This is the largest open item
in the plan.

---

## 3. Source inventory (`staging_vault.db`)

| Table | Rows | Shape | Path column |
|---|---:|---|---|
| `euro_gk` | 1,200,128 | modern | `kb_path` |
| `facts_gk` | 54,859 | bilingual + country | `kb_path` |
| `sunnah` | 34,177 | bilingual | `kb_path` |
| `quran` | 12,464 | **legacy** | `path_string` |
| `Catholic` | 4,505 | bilingual | `kb_path` |
| `euro_history` | 1,263 | history | `kb_path` |
| `islamic_history` | 1,259 | history | `kb_path` |
| `usa_cooking` | 1,072 | cooking | `kb_path` |
| `factbook_countries` | 261 | country | `kb_path` |
| `anglican` | 242 | bilingual | `kb_path` |
| `british_cooking` | 60 | cooking | `kb_path` |
| `italian_cooking` | 21 | cooking | `kb_path` |
| `kb_audit_table` | 2 | metadata | *(none — `domain`/`sub_domain`)* |
| **Total** | **1,310,313** | | |

**Five schema shapes** must each be mapped (they are not uniform):

- **modern** — `id, source_book, kb_path, content_text, vector, grade, timestamp`
- **bilingual** — adds `content_arabic, language`; `facts_gk` adds `country`
- **history** — adds `sub_domain, era, region`
- **legacy (`quran`)** — `content` (not `content_text`), `path_string` (not
  `kb_path`), `embedding` (not `vector`), plus `had_num`
- **country / cooking** — `factbook_countries` has `country_code, country_name,
  region, content_json`; cooking tables have `dietary_tags`

**Two-layer design to preserve.** `kb_io.py` names `factbook_countries` as
**Layer 1** (full country documents) and `facts_gk` as **Layer 2** (atomic
facts). Their paths overlap (`/GK/GlobalFacts/...`) but they are **not
duplicates** — the layer distinction is deliberate and must survive the
migration as a `layer` attribute.

**Path taxonomy — 972 distinct nodes:**

| Level 1 | Nodes | Note |
|---|---:|---|
| `/GK` | 640 | `/GK/GlobalFacts` 523, `/GK/Western/arXiv` 117 |
| `/https:` | 238 | **malformed** — URL captured as a path (see §6.2) |
| `/Cooking` | 70 | British / Italian / American |
| `/History` | 40 | 20 subdomains × {euro, islamic} |
| `/Islam` | 2 | `/Islam/Quran`, `/Islam/Sunni/sunnah` |
| `/Christianity` | 2 | `/Christianity/Catholicism/Catechism`, `/Christianity/Anglicanism` |

**The encouraging part:** the vault *already* carries a two-heritage split —
`euro_history` vs `islamic_history`, `/GK/Western` vs `/Islam`,
`/Christianity` vs `/Islam`, with the same 20 history subdomains under each.
The docx's dual-root design is a **formalisation of a split that exists**,
which is why this migration is tractable at all.

---

## 4. Non-obvious environment facts

- **PostgreSQL 17.25 is installed and running** — `C:\Alim\PostgreSQL\17\bin`,
  listening on **:5432** (PID 5800). No new engine needs installing.
- **pgvector is NOT installed.** The `share/extension` list has `cube`,
  `earthdistance`, `ltree` and 60 others, but no `vector`. Postgres `cube`
  caps at 100 dimensions, so it cannot hold a 384-dim embedding. This is why
  §5.2 stores vectors as `BYTEA` — a decision forced by the environment, and
  revisited in §11.
- **Python drivers are missing** — `psycopg`, `psycopg2`, `pgvector`,
  `sqlalchemy`, `alembic` are all absent from the venv. Phase 0 installs
  `psycopg[binary]` only; no ORM is needed.
- `CLAUDE.md` says the KB is at `C:/ChatILM-KB/`. **That is stale.** `.env`
  sets `KB_ROOT=C:\CHATILM-KB-MVP`, and `.env` is authoritative. `CLAUDE.md`
  should be corrected (§11).
- Every vector in every table is **384 float32** = 1536 bytes — uniform, which
  makes byte-identical transfer possible and gives a strong parity check.

---

## 5. Target schema

### 5.1 The docx tables — adopted verbatim

```sql
CREATE TYPE european_branch AS ENUM (
  'TRIVIUM_GRAMMAR','TRIVIUM_LOGIC','TRIVIUM_RHETORIC',
  'QUADRIVIUM_ARITHMETIC','QUADRIVIUM_GEOMETRY','QUADRIVIUM_MUSIC',
  'QUADRIVIUM_ASTRONOMY',
  'FACULTY_LAW','FACULTY_MEDICINE','FACULTY_PHILOSOPHY','FACULTY_THEOLOGY');
CREATE TYPE islamic_root AS ENUM ('NAQLIYYAH_REVEALED','AQLIYYAH_RATIONAL');
CREATE TYPE islamic_obligation AS ENUM ('FARD_AYN_INDIVIDUAL','FARD_KIFAYAH_COMMUNAL');

CREATE TABLE topics (
  topic_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  code VARCHAR(50) NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE european_scholastic_mapping (
  mapping_id SERIAL PRIMARY KEY,
  topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
  branch european_branch NOT NULL,
  scholastic_tier VARCHAR(100) NOT NULL,
  rationale TEXT);

CREATE TABLE islamic_epistemology_mapping (
  mapping_id SERIAL PRIMARY KEY,
  topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
  epistemic_root islamic_root NOT NULL,
  traditional_category VARCHAR(150) NOT NULL,
  obligation_level islamic_obligation NOT NULL,
  epistemic_justification TEXT);

CREATE TABLE topic_relationships (
  parent_topic_id INT REFERENCES topics(topic_id),
  child_topic_id INT REFERENCES topics(topic_id),
  relationship_type VARCHAR(100) DEFAULT 'SUBFIELD_OF',
  PRIMARY KEY (parent_topic_id, child_topic_id));
```

The only change to the docx text is spelling out its run-together enums; the
columns, types and constraints are as written.

### 5.2 The content extension — the one addition

```sql
CREATE TYPE heritage_line AS ENUM ('EUROPEAN','ISLAMIC','INTEGRATED');
CREATE TYPE kb_layer AS ENUM ('COUNTRY_DOCUMENT','ATOMIC_FACT','CORPUS','SCRIPTURE');

CREATE TABLE topic_content (
  content_id    BIGSERIAL PRIMARY KEY,
  topic_id      INT NOT NULL REFERENCES topics(topic_id) ON DELETE CASCADE,
  layer         kb_layer NOT NULL DEFAULT 'CORPUS',
  source_book   TEXT,
  kb_path       TEXT NOT NULL,        -- legacy path, kept for traceability
  content_text  TEXT,
  content_arabic TEXT,
  vector        BYTEA,                -- 384 × float32 LE, byte-identical to SQLite
  vector_dim    SMALLINT NOT NULL DEFAULT 384,
  grade         TEXT,                 -- raw, unmodified (see §6.4)
  language      TEXT,
  heritage      heritage_line,
  era           TEXT,
  region        TEXT,
  country       TEXT,
  sub_domain    TEXT,
  dietary_tags  TEXT,
  country_code  TEXT,
  country_name  TEXT,
  content_json  JSONB,
  had_num       TEXT,                 -- quran legacy column
  legacy_table  TEXT NOT NULL,        -- provenance: source SQLite table
  legacy_id     INTEGER NOT NULL,     -- provenance: original row id
  recorded_at   TIMESTAMPTZ,
  UNIQUE (legacy_table, legacy_id)    -- idempotent re-runs
);

CREATE INDEX topic_content_topic_idx  ON topic_content (topic_id);
CREATE INDEX topic_content_legacy_idx ON topic_content (legacy_table, legacy_id);
```

`UNIQUE (legacy_table, legacy_id)` is the backbone of the migration: it makes
every phase **restartable** and every row **traceable to its origin**. Note
`legacy_id` alone would collide — each SQLite table has its own `id` sequence.

Full-text search replaces the current FTS5 index:

```sql
ALTER TABLE topic_content ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(content_text,''))) STORED;
CREATE INDEX topic_content_tsv_idx ON topic_content USING GIN (tsv);
```

---

## 6. Taxonomy derivation — 972 paths → topics

### 6.1 Derivation rule

The `kb_path` is a *tree as a string*; the new schema is a *tree as rows*. The
rule, following the docx's extension rules and the tagging rules already in
`KB_INTERNET_EXTRACTION_PLAN.md`:

> **Subject-bearing segments become topics; descriptive segments become
> attributes.**

So the path is split, and each segment is classified as *topic*, *attribute*,
or *noise*:

| Path | Topic | Attributes |
|---|---|---|
| `/GK/GlobalFacts/Africa/Algeria` | `GlobalFacts` | `region=Africa`, `country=Algeria` |
| `/GK/Western/arXiv/hep` | `arXiv` → child `hep` | — |
| `/History/conflicts` | `History` → child `conflicts` | `heritage=EUROPEAN` |
| `/Islam/Quran` | `Quran` | `heritage=ISLAMIC` |
| `/Islam/Sunni/sunnah` | `Sunnah` | `heritage=ISLAMIC` |
| `/Christianity/Catholicism/Catechism` | `Catholicism` | `heritage=EUROPEAN` |
| `/Cooking/British` | `BritishCooking` | — |

Expected yield: **~40–60 topics** — 20 history subdomains × 2 heritage lines,
~13 arXiv category groups, GlobalFacts, Quran, Sunnah, Catholicism,
Anglicanism, 3 cuisines, plus root nodes — against 972 leaf paths. The 117
arXiv and 523 GlobalFacts paths collapse because region/country/subfield are
attributes, not topics.

### 6.2 Normalisation fixes (must run before derivation)

1. **238 malformed paths.** `/https:/sourcebooks.fordham.edu/...` — the
   Fordham scraper wrote the source URL where a taxonomy path belongs. These
   are history sourcebooks and belong under `/History/*`, but the *correct*
   subdomain cannot be inferred from the URL alone. **Needs a decision** (§11).
2. **Casing collision.** `/GK/GlobalFacts/Africa/...` (in `facts_gk`) vs
   `/GK/GlobalFacts/africa/...` (in `factbook_countries`) — one taxonomy node
   in two casings. Fold to a canonical form; record the original.
3. Strip trailing whitespace/slashes; NFC-normalise Arabic in `content_arabic`.

### 6.3 The dual mapping — and why a human must review it

Each topic gets **one row in each mapping table**. The docx's three extension
rules drive the derivation:

- *Rule 1 (linguistic vs computational)*: language, syntax, proof → Trivium /
  Lughah & Mantiq.
- *Rule 2 (mathematical vs applied)*: pure maths, cryptography, quantum logic
  → Quadrivium / Riyadiyyat; when applied to governance, *additionally* bind
  to Faculty of Law / Mu'amalat.
- *Rule 3 (obligation)*: fields whose misuse threatens individual moral
  responsibility add a `FARD_AYN` subset while advanced mastery stays
  `FARD_KIFAYAH`.

Worked examples this yields:

| Topic | `european_branch` | tier | `islamic_root` | category | obligation |
|---|---|---|---|---|---|
| `arXiv` (math.*) | `QUADRIVIUM_ARITHMETIC` | Quadrivium | `AQLIYYAH_RATIONAL` | Riyadiyyat | `FARD_KIFAYAH_COMMUNAL` |
| `arXiv` (physics.*) | `QUADRIVIUM_ASTRONOMY` | Quadrivium | `AQLIYYAH_RATIONAL` | Tabi'iyyat | `FARD_KIFAYAH_COMMUNAL` |
| `Catholicism` / `Anglicanism` | `FACULTY_THEOLOGY` | Higher Faculty | `NAQLIYYAH_REVEALED` | (comparative scripture) | `FARD_KIFAYAH_COMMUNAL` |
| `Quran` / `Sunnah` | `FACULTY_THEOLOGY` | Higher Faculty | `NAQLIYYAH_REVEALED` | Qur'an / Hadith | `FARD_AYN_INDIVIDUAL` |
| `History` | `FACULTY_PHILOSOPHY` | Higher Faculty | `AQLIYYAH_RATIONAL` | Tarikh | `FARD_KIFAYAH_COMMUNAL` |
| `GlobalFacts` | `QUADRIVIUM_GEOMETRY` | Quadrivium | `AQLIYYAH_RATIONAL` | Jughrafiya | `FARD_KIFAYAH_COMMUNAL` |
| `BritishCooking` | `FACULTY_MEDICINE` | Higher Faculty | `AQLIYYAH_RATIONAL` | Tibb (nutrition) | `FARD_KIFAYAH_COMMUNAL` |

**This table — not the ETL code — is the part that needs sign-off.** Assigning
an Islamic epistemic root, a traditional category and above all a *Fard 'Ayn
vs Fard Kifayah* obligation level to a corpus of texts is a **religious-scholarly
determination**, not a modelling convenience. The plan therefore emits the
full 972-row mapping as a **reviewable artefact** (CSV beside the migration
script) and gates Phase 3 on a named reviewer approving it. Suggested
reviewer, mirroring the pattern already used elsewhere in this work: a
qualified scholar for the Islamic side, and the user for the European side.

### 6.4 `grade` is not a quality grade

Sampling shows `grade` holds **arXiv categories** in `euro_gk`
(`quant-ph` 33,120; `hep-ph` 31,307; …), the string `Global Fact` in
`facts_gk`, and `A` in `euro_history`. It is an overloaded column, not a
grade. The plan preserves it raw as `grade`, and adds **no** normalised
quality field in this migration — inventing one would fabricate data.

---

## 7. ETL design

### 7.1 Shape → column mapping

One adapter per shape, all writing `topic_content`:

| Source column | Target | Notes |
|---|---|---|
| `content_text` \| `content` | `content_text` | `quran` uses `content` |
| `content_arabic` | `content_arabic` | absent in modern/history/cooking |
| `kb_path` \| `path_string` | `kb_path` | normalised per §6.2 |
| `vector` \| `embedding` | `vector` | byte-identical `BYTEA` |
| `grade`, `source_book`, `language` | same names | raw |
| `sub_domain`, `era`, `region` | same names | history only |
| `country_code`, `country_name`, `content_json` | same names | `content_json` → `JSONB` |
| `dietary_tags`, `had_num` | same names | |
| `timestamp` | `recorded_at` | text → `TIMESTAMPTZ`; blank → NULL |
| — | `layer` | `factbook_countries`→`COUNTRY_DOCUMENT`, `facts_gk`→`ATOMIC_FACT`, `quran`/`sunnah`→`SCRIPTURE`, else `CORPUS` |
| — | `heritage` | from topic mapping |
| `id` + table name | `legacy_id`, `legacy_table` | provenance + idempotency |

### 7.2 Load mechanics

- Stream in **5,000-row batches**; `euro_gk` is 1.2M rows and must never be
  materialised in memory (the current `_ensure_fts_index` already reads all
  1.2M into a list — this migration must not repeat that pattern).
- Use `COPY` (or `execute_values`) — not row-by-row inserts.
- **Create indexes after the bulk load**; then `ANALYZE`.
- Read SQLite strictly read-only: `sqlite3.connect('file:...?mode=ro', uri=True)`,
  as used for this reconnaissance. The source vault is never written to.
- Idempotent upsert on `(legacy_table, legacy_id)` so a failed batch is simply
  re-run.

### 7.3 Vectors

Copied as raw `BYTEA`, byte-identical to the SQLite blob. No re-embedding, no
re-normalising, no float conversion round-trip. Verification asserts every
stored vector is exactly **1536 bytes** (384 × float32) and that a sample
decodes to the same floats as the source.

pgvector is **not** installed (§4). Options are revisited in §11; the plan
does not depend on it.

---

## 8. Retrieval change (`kb_io.py` → `kb_pg.py`)

Today retrieval filters with `kb_path LIKE '%path%'` then scores cosine in
Python. After migration the filter becomes an **indexed `topic_id` lookup**
plus optional attribute predicates:

```
Read_KB(topic_code, query_vector, top_k, heritage=None, era=None, region=None)
  → SELECT ... FROM topic_content WHERE topic_id = $1 [AND ...]
  → cosine in Python (unchanged scoring, same 384-dim vectors)
```

`Read_KB_Text` (FTS5) becomes a `tsv @@ plainto_tsquery(...)` query ranked by
`ts_rank`. `Read_Country_KB` becomes a `layer = 'COUNTRY_DOCUMENT'` filter.

This is a **behavioural** change and needs its own regression set (§9.5) —
call sites in `main_orchestrator.py` pass `kb_path` strings today and pass
topic codes after.

**Separate defect noticed, out of scope but flag it:** `kb_io.py:290`
rewrites retrieved content with `text.replace("The Slave Colony", "South
Africa")`. A hardcoded find-and-replace sits in the KB read path. It is not
part of this migration; it should be tracked and removed on its own.

---

## 9. Phases, each with an acceptance gate

| # | Phase | Deliverable | Acceptance gate |
|---|---|---|---|
| 0 | **Preflight** | backup of `staging_vault.db`; `psycopg[binary]` installed; PG reachable | backup exists and its size matches the source; row counts recorded as a baseline manifest (13 tables, 1,310,313 rows) |
| 1 | **Schema** | `chatilm_kb` database; docx DDL + extension applied | `\d` shows all 5 tables + 4 enum types; a test insert round-trips |
| 2 | **Normalisation** | canonical path set; the 238 Fordham URLs resolved per the agreed rule | **no** path begins `/https:`; casing collisions report zero; 972 → canonical count recorded |
| 3 | **Mapping (human gate)** | 972-row path→topic→dual-mapping CSV | **named reviewer signs off** the Islamic classifications; every topic has exactly one row in *both* mapping tables |
| 4 | **Load** | all 13 tables in `topic_content` | `count(*)` = 1,310,313; per-table parity reproduced exactly; zero NULL `topic_id` |
| 5 | **Verify** | parity + integrity report | every vector 1536 bytes; source/blob float sample identical; top-10 overlap vs SQLite ≥ 9/10 on a 50-query set; zero orphans |
| 6 | **Cutover** | `kb_pg.py` wired in behind a flag | app answers the smoke set from PG with SQLite still present as rollback |

Phase 4 is the one to run **on a copy first** and time — 7.1 GB / 1.31M rows
is large enough that an untested batch size will be discovered the hard way.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Mapping is a scholarly judgement** — wrong Islamic classification ships | Phase 3 human gate; mapping stored as data, trivially correctable without re-loading content |
| **972 → topic collapse loses retrieval precision** (523 GlobalFacts paths → one topic) | attributes (`region`, `country`) are preserved and indexed; the §9.5 overlap test must catch any regression |
| **7.1 GB load fails midway** | idempotent upsert on `(legacy_table, legacy_id)`; batched; resumable |
| **`kb_path LIKE` call sites break** | Phase 6 behind a flag; SQLite vault untouched and retained |
| **Source vault corrupted** | strictly `mode=ro`; preflight backup; source never written |
| **`factbook_countries` vs `facts_gk` merged by mistake** | `layer` attribute preserves the deliberate Layer 1 / Layer 2 split |
| pgvector absent | not depended on; §11 option |

**Rollback:** entirely non-destructive. The new database is additive; the
SQLite vault keeps working until the cutover flag is flipped, and flipping it
back restores the old path.

---

## 11. Open items — decisions needed before Phase 2

1. **The 238 Fordham URL paths.** They hold real history content but no usable
   taxonomy. Options: (a) re-derive the subdomain from each row's `source_book`
   / text, (b) map all to `/History/documents_sources`, (c) exclude from this
   migration and fix in the extraction pipeline first. **Recommend (a) with (b)
   as the fallback for rows that cannot be resolved.**
2. **pgvector.** Not installed. Stay on `BYTEA` + Python scoring (recommended —
   it is what runs today), or install pgvector and move scoring into the
   database. Installing it is a separate, optional phase, not a prerequisite.
3. **Reviewer for §6.3** — needed before Phase 3 can pass its gate.
*Resolved (this session): the stale KB path. It was in **three** places, not
one — `CLAUDE.md`, and the `os.getenv("KB_ROOT", …)` **fallback defaults** in
`backend/utils/config.py` and `backend/utils/payments.py`, which pointed at a
vault that does not exist and would have produced `KB ERROR: Vault not found`
whenever `.env` was absent. All three now read `C:/CHATILM-KB-MVP`.*
*Resolved: the plan's location — it now lives in the KB repo root as
`KB_EURO_ISLAMIC_MIGRATION_PLAN.md`, beside `KB_INTERNET_EXTRACTION_PLAN.md`.*

**Not in this plan, and not to be confused with it:** the TDb at
`C:\ChatILM-KB-MVP\Truth_Db\Truth_DB.db`. It is a different store with a
different purpose and no step here touches it.

---

## 12. Resume here

**Trigger:** *"continue with Project ChatILM-KB-MVP"*.

**State: nothing migrated. Not one phase started.** The vault is untouched —
read-only reconnaissance only (§3 figures came from `mode=ro` connections).
Phase 0 (preflight backup) is the first action, and it waits on the three
decisions still open in §11:

1. The **238 malformed Fordham paths** — choose rule (a), (b) or (c).
2. **pgvector** — stay on `BYTEA` + Python scoring, or install it as its own phase.
3. **The reviewer** for the §6.3 dual mapping — required before Phase 3's gate.

Open item 4 (stale KB path) and item 5 (this plan's location) are both
**resolved** — see §11.
