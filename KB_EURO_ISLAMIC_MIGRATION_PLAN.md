# KB Migration Plan — Dual-Scholastic Epistemic Structure

**Status:** DRAFT for review — not started
**Revision:** 3 — 2026-10-22. Full audit pass before implementation; 21 defects
fixed and listed in §13. Revision 2 reconciled this plan with the two registry
documents `1a. Knowledge Base Table Structure.docx` and `1b. Vault Registry
Report` (both in `C:\Users\gydan\Downloads`).
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
`KB_ROOT/staging_vault.db`, **12 content tables, 1,310,311 rows**, 7.1 GB —
plus `kb_audit_table` (2 rows of registry metadata, not knowledge; see §3).

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
| **Content total** | **1,310,311** | | |
| `kb_audit_table` | 2 | registry metadata | *(none — `domain`/`sub_domain`)* |
| **All rows** | **1,310,313** | | |

`kb_audit_table` is **not** knowledge: two rows, one per Fordham history
sourcebook, recording row count, status and a note. It is not loaded into
`topic_content`; its function is replaced by the `topics` registry. Counting it
as a thirteenth content table (as revision 1 did) would create two content rows
with no topic and no path.

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
| `https://` | 238 | **malformed** — URL captured as a path, 2,338 rows in the two history tables (see §6.2) |
| `/Cooking` | 70 | British 60 / Italian 9 / American 1 |
| `/History` | 20 | 20 sub-domains; each appears in *both* heritage tables |
| `/Islam` | 2 | `/Islam/Quran`, `/Islam/Sunni/sunnah` |
| `/Christianity` | 2 | `/Christianity/Catholicism/Catechism`, `/Christianity/Anglicanism` |

**The encouraging part:** the vault *already* carries a two-heritage split —
`euro_history` vs `islamic_history`, `/GK/Western` vs `/Islam`,
`/Christianity` vs `/Islam`, with the same 20 history subdomains under each.
The docx's dual-root design is a **formalisation of a split that exists**,
which is why this migration is tractable at all.

### 3.1 The registry documents versus the vault

Two registry documents describe the vault: `1a. Knowledge Base Table Structure`
(S1) and `1b. Vault Registry Report` (S2). Neither is a reliable inventory, and
the `topics` table must therefore be **generated from the data**, not
transcribed from either.

| # | S1 / S2 say | Vault actually has | Consequence |
|---|---|---|---|
| 1 | 10 content tables | **12** — `euro_history` and `islamic_history` appear in neither document | 2,522 rows are invisible to anyone planning from the registry |
| 2 | "Existing (10 of 17)", "Missing (7)" | 12 exist, and all 7 are genuinely absent | The "17" is a target, not a state |
| 3 | `islamic_gk` is used twice (S1: *Islam/General Knowledge* and *GK/Islamic Heritage*) | — | One name, two intended corpora |
| 4 | S2 calls the missing Islamic-GK table `islamic_heritage_gk`; S1 calls it `islamic_gk` | — | Two names, one slot → 6 distinct corpora, not 7 |
| 5 | `physics` (Al-Anwari) is a domain (S1) and missing (S2) | No `physics` table, and no history of one | Planned, never loaded |
| 6 | Every existing table `✅ OK` | Row-count check only | `grade` is healthy to S2 and overloaded in fact (§6.4) |

Consequence for this plan: S2's gap list is **not** a build backlog. The new
design does not need one table per corpus, so the missing tables are retired
from this migration's scope unless a corpus is actually acquired (§11.5).

---

## 4. Non-obvious environment facts

- **PostgreSQL 17.6 is installed and running** — `C:\Alim\PostgreSQL\17\bin`,
  service `postgresql-x64-17`, listening on **:5432**. No new engine needs
  installing. (Revision 2 said "17.25"; `psql --version` reports **17.6**.)
- **pgvector is NOT installed.** The `share/extension` list has `cube`,
  `earthdistance`, `ltree` and 60 others, but no `vector`. Postgres `cube`
  caps at 100 dimensions, so it cannot hold a 384-dim embedding. This is why
  §5.2 stores vectors as `BYTEA` — a decision forced by the environment, and
  revisited in §11.
- **Python drivers are missing** — `psycopg`, `psycopg2`, `pgvector`,
  `sqlalchemy`, `alembic` are all absent from the pinned venv (each verified by
  import on 2026-10-22). Phase 0 installs `psycopg[binary]` only; no ORM is
  needed.
- ~~`CLAUDE.md` says the KB is at `C:/ChatILM-KB/`~~ — **resolved in revision
  1**; `CLAUDE.md`, `config.py` and `payments.py` all now read
  `C:/CHATILM-KB-MVP` (see §11, resolved items).
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
  rationale TEXT,
  UNIQUE (topic_id, branch));          -- one row per branch; see Rule 2

CREATE TABLE islamic_epistemology_mapping (
  mapping_id SERIAL PRIMARY KEY,
  topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
  epistemic_root islamic_root NOT NULL,
  traditional_category VARCHAR(150) NOT NULL,
  obligation_level islamic_obligation NOT NULL,
  epistemic_justification TEXT,
  UNIQUE (topic_id));                  -- exactly one per topic

CREATE TABLE topic_relationships (
  parent_topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
  child_topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
  relationship_type VARCHAR(100) DEFAULT 'SUBFIELD_OF',
  PRIMARY KEY (parent_topic_id, child_topic_id),
  CHECK (parent_topic_id <> child_topic_id));
```

The only changes to the docx DDL are spelling out its run-together enums, two
`UNIQUE` constraints that enforce in the schema the mapping cardinality the
docx's prose already assumes, and `ON DELETE` behaviour on the relationship
edges. Columns and types are as written.

**Mapping cardinality — a correction.** The docx allows more than one European
branch per topic: Rule 2 says an applied field *"additionally binds"* to
Faculty of Law. So a topic may hold one row per branch, and Phase 3's gate
requires **at least one** European row per topic, not exactly one. The Islamic
mapping is one row per topic (`UNIQUE (topic_id)`).

### 5.2 The content extension — the one addition

```sql
CREATE TYPE heritage_line AS ENUM ('EUROPEAN','ISLAMIC','INTEGRATED');
CREATE TYPE kb_layer AS ENUM ('COUNTRY_DOCUMENT','ATOMIC_FACT','CORPUS','SCRIPTURE');

CREATE TABLE topic_content (
  content_id    BIGSERIAL PRIMARY KEY,
  topic_id      INT NOT NULL REFERENCES topics(topic_id) ON DELETE RESTRICT,
  layer         kb_layer NOT NULL,    -- set explicitly; no default (see below)
  source_book   TEXT,
  legacy_path   TEXT,                 -- original path, verbatim, never rewritten
  kb_path       TEXT NOT NULL,        -- canonical path after §6.2 fixes
  content_text  TEXT,
  content_arabic TEXT,
  vector        BYTEA,                -- 384 × float32 LE, byte-identical to SQLite
  vector_dim    SMALLINT NOT NULL DEFAULT 384,
  CHECK (vector IS NULL OR octet_length(vector) = vector_dim * 4),
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
  legacy_id     TEXT NOT NULL,        -- provenance: original row id, as text
  recorded_at   TIMESTAMPTZ,
  UNIQUE (legacy_table, legacy_id)    -- idempotent re-runs
);

CREATE INDEX topic_content_topic_idx  ON topic_content (topic_id);
CREATE INDEX topic_content_legacy_idx ON topic_content (legacy_table, legacy_id);
CREATE INDEX topic_content_source_idx ON topic_content (topic_id, source_book);  -- sunnah collections (§8)
```

`UNIQUE (legacy_table, legacy_id)` is the backbone of the migration: it makes
every phase **restartable** and every row **traceable to its origin**. Note
`legacy_id` alone would collide — each SQLite table has its own `id` sequence.

**`legacy_id` is TEXT, not INTEGER.** `quran.id` holds values such as
`'001.001_P'` and `'001.001_Y'` — 12,464 text ids. An integer column would
either coerce them to a single value or reject them; both outcomes are silent
loss of the entire Quran corpus. The column is TEXT and the adapter for every
other table stringifies its integer id.

`ON DELETE RESTRICT` on `topic_id` (the docx uses `CASCADE` on the mapping
tables, which is right for classification) means a topic with content attached
cannot be deleted silently. Removing a topic becomes a reviewed two-step.

**`layer` has no default.** A `DEFAULT 'CORPUS'` would silently mislabel any
row whose adapter forgot to set it — collapsing exactly the Layer 1 / Layer 2
distinction this plan exists to preserve. Every adapter sets it explicitly and
the load fails on NULL rather than inheriting a wrong value.

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

Expected yield: **~40–60 topics** — 20 history sub-domains (one topic each, with
`heritage` as an attribute), ~13 arXiv category groups, GlobalFacts, Quran,
Sunnah, Catholicism, Anglicanism, 3 cuisines, plus root nodes — against 972
leaf paths. The 117 arXiv and 523 GlobalFacts paths collapse because
region/country/subfield are attributes, not topics.

**Hard rule — content attaches to leaves only.** Every content row is attached
to the most specific topic its path identifies. Parent topics (`arXiv`,
`History`, `GK`, `Islam`, `Christianity`, `Cooking`) hold **no content rows**;
they exist for navigation and for `topic_relationships`. Without this rule a
query on `arXiv` would load 1.2M rows (1.8 GB of vectors) for scoring, and a
query on `History` would mix both heritages. Phase 5 asserts that no topic with
children carries content.

Where a path is already the leaf (`/Islam/Quran`, `/Christianity/Catholicism`),
the topic *is* the leaf and carries content directly.

### 6.2 Normalisation fixes (must run before derivation)

1. **238 malformed paths.** `https://sourcebooks.fordham.edu/...` — the
   Fordham scraper wrote the source URL where a taxonomy path belongs. These
   are history sourcebooks and belong under `/History/*`, but the *correct*
   subdomain cannot be inferred from the URL alone. **Needs a decision** (§11).
2. **Casing collision — systemic, not local.** **261 country/region nodes**
   exist in two casings: `/GK/GlobalFacts/Africa/Algeria` (in `facts_gk`) vs
   `/GK/GlobalFacts/africa/Algeria` (in `factbook_countries`). That is **522
   paths and 54,119 rows**. The *nodes* collide; the *content* does not — this
   is the Layer 1 / Layer 2 boundary (§3), so rows must **never** be merged on
   case-folding. Fold to a canonical path, record the original in `legacy_path`,
   and keep `layer` as the discriminator.
3. **Strip trailing whitespace/slashes in the canonical path only** — the raw
   string stays in `legacy_path`. NFC-normalise Arabic into a *derived*
   column (`content_arabic_norm`); never rewrite `content_arabic` in place
   (§11.6).
4. **Junk paths in `facts_gk`.** `/GK/GlobalFacts/Meta/CATEGORIES` (1,001 rows;
   its `country` value is literally `CATEGORIES`) is a meta bucket, and at
   least two paths hold prose instead of a taxonomy node
   (`/GK/GlobalFacts/Europe/In the aftermath and devastation of the two World
   Wars`, `/GK/GlobalFacts/Oceans/A large body of recent oceanographic
   research`). These map to `GlobalFacts` with a `quality_flag` attribute —
   they are not given topics of their own. This is also why `facts_gk` reports
   262 distinct `country` values against `factbook_countries`' 261.

### 6.3 The dual mapping — and why a human must review it

Each topic gets **one Islamic mapping row** and **at least one European
mapping row** (Rule 2 allows more than one branch). The docx's three extension
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
`facts_gk`, `A` in both history tables, `Sovereign` in `quran`, and **genuine
hadith authenticity grades** in `sunnah` (`Sahih` 9,083; `Hasan` 2,229;
`Da'if` 1,474; 1,232 blank). It is an overloaded column, not a grade. The plan
preserves it raw as `grade`, and adds **no** normalised quality field in this
migration — inventing one would fabricate data. The `sunnah` values in
particular are religious metadata and must not be "cleaned".

---

## 7. ETL design

### 7.1 Shape → column mapping

One adapter per shape, all writing `topic_content`:

| Source column | Target | Notes |
|---|---|---|
| `content_text` \| `content` | `content_text` | `quran` uses `content` |
| `content_arabic` | `content_arabic` | absent in modern/history/cooking |
| `kb_path` \| `path_string` | `legacy_path` (verbatim) **and** `kb_path` (normalised per §6.2) | the raw path is never overwritten |
| `vector` \| `embedding` | `vector` | byte-identical `BYTEA` |
| `grade`, `source_book`, `language` | same names | raw |
| `sub_domain`, `era`, `region` | same names | history only |
| `country_code`, `country_name`, `content_json` | same names | `content_json` → `JSONB` |
| `dietary_tags`, `had_num`, `servings` | same names | |
| `timestamp` | `recorded_at` | text → `TIMESTAMPTZ`; blank → NULL |
| — | `layer` | `factbook_countries`→`COUNTRY_DOCUMENT`, `facts_gk`→`ATOMIC_FACT`, `quran`/`sunnah`→`SCRIPTURE`, else `CORPUS` |
| — | `heritage` | from the **source table** for `euro_history`→EUROPEAN and `islamic_history`→ISLAMIC; for every other table from the topic mapping |
| `id` + table name | `legacy_id`, `legacy_table` | provenance + idempotency; `id` stringified (TEXT) |

### 7.2 Load mechanics

- Stream in **5,000-row batches**; `euro_gk` is 1.2M rows and must never be
  materialised in memory (the current `_ensure_fts_index` already reads all
  1.2M into a list — this migration must not repeat that pattern).
- **`COPY` cannot upsert.** Load each batch into an `UNLOGGED` staging table
  with `COPY`, then `INSERT INTO topic_content (...) SELECT ... FROM staging
  ON CONFLICT (legacy_table, legacy_id) DO UPDATE SET ...`. That is what makes
  a re-run idempotent; a bare `COPY` into `topic_content` would abort the batch
  on the first conflict. `execute_values` with the same `ON CONFLICT` is the
  simpler fallback at the cost of speed.
- **Indexes:** the `UNIQUE (legacy_table, legacy_id)` index must exist *during*
  the load (it backs the upsert). Create only the **secondary** indexes
  (`topic_idx`, `source_idx`, attribute indexes, `tsv` GIN) after the bulk
  load; then `ANALYZE`.
- Read SQLite strictly read-only: `sqlite3.connect('file:...?mode=ro', uri=True)`,
  as used for this reconnaissance. The source vault is never written to.
- Validate `content_json` as JSON before insert; an invalid document would
  abort the batch. (All 261 rows parse cleanly today — verified 2026-10-22 —
  but the check belongs in the load, not in an assumption.)

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

This is a **behavioural** change and needs its own regression set (Phase 6).

### 8.1 Call-site inventory — 20 calls in 13 files (verified 2026-10-22)

The plan previously said only "`main_orchestrator.py`". That is wrong: the KB is
read from 13 modules, and five of those reach the tables through **direct SQL**
that no `kb_pg.py` change can intercept.

| File | Call | Legacy filter |
|---|---|---|
| `core/domain_executor.py` | `Read_KB` | table names from `index_map`; sunnah namespaces (broken, below) |
| `reasoning/Islamic_Reasoning/islamic_reasoning.py` | `Read_KB` ×2 | `quran` `""`, `sunnah` `""` |
| `reasoning/Catholic_Reasoning/catholic_reasoning.py` | `Read_KB` | `"catholic"`, `"Christianity/Catholicism/"` |
| `reasoning/Anglican_Reasoning/anglican_reasoning.py` | `Read_KB` | `"anglican"`, `"Christianity/Anglicanism/"` |
| `reasoning/Cooking_Reasoning/{British,Italian,USA}/…` + `__init__.py` | `Read_KB` ×4 | table + `/Cooking/…` path |
| `reasoning/Facts_Reasoning/facts_reasoning.py` | `Read_Country_KB` ×2, `Read_KB` ×4 | country layer, empty path |
| `reasoning/General_Knowledge_Reasoning/general_reasoning.py` | `Read_KB`, `Read_KB_Text` | `euro_gk` routed to FTS, others empty path |
| `reasoning/Chat_Reasoning/chat_reasoning.py` + `domain_registry.py` | `Read_KB` | table/path map **including `psych_kb`, which does not exist** |
| `reasoning/phases/phase2_retriever.py`, `phase3_executor.py` | `Read_KB_Text("euro_gk")` | FTS |

**Direct SQL that bypasses `kb_pg.py` entirely:**

- `Facts_Reasoning/facts_reasoning.py:223, 320, 464, 470` —
  `SELECT … FROM factbook_countries`
- `utils/fact_extract.py:532` — `SELECT content_json FROM factbook_countries`
- `tools/fetch_british_history_online.py:710, 750` and
  `tools/fetch_gutenberg_history.py:580, 623` — `SELECT … FROM euro_history`
  (offline fetchers, not the request path, but they write to the vault and must
  target the new store if they keep running after cutover)

**Consequence:** cutover cannot be a `kb_pg.py` swap alone. Two mechanisms are
required:

1. **A compatibility shim.** Keep the `Read_KB(table_name, kb_path, …)`
   signature and translate `(legacy_table, path)` → `(topic_id, attribute
   predicates)` inside it. Untouched call sites keep working; call sites move
   to topic codes one at a time, each covered by the regression set.
2. **Legacy views.** One view per old table reproducing its exact column names
   (`legacy_factbook_countries`, `legacy_euro_history`, …). The direct-SQL
   sites are then pointed at the views, or left untouched, without a rewrite.
   The views are also a standing check that no column was lost.

**A live defect this fixes.** `domain_executor.py` routes the Integrated
Islamic query to `Read_KB("sunnah", "bukhari")`, `("sunnah","muslim")`,
`("sunnah","tirmidhi")` and so on, and `Read_KB` turns the second argument into
`kb_path LIKE '%bukhari%'`. But **all 34,177 sunnah rows share exactly one
path**, `/Islam/Sunni/sunnah` — so every one of those filtered calls returns
**zero rows today**. The collections exist only in `source_book`
(`Sahih Muslim` 7,458; `Sahih al-Bukhari` 7,277; `Nasai` 5,768;
`Abu Dawood` 5,276; `Ibn Majah` 4,345; `Tirmidhi` 4,053). Under the new schema
collection is an attribute (and optionally a child topic), so the filter that
currently fails silently becomes expressible. This should be captured in the
Phase 6 regression set as a **fix**, not merely a parity case.

**Separate defect noticed, out of scope but flag it:** `kb_io.py:290`
rewrites retrieved content with `text.replace("The Slave Colony", "South
Africa")`. A hardcoded find-and-replace sits in the KB read path. It is not
part of this migration; it should be tracked and removed on its own.

---

## 9. Phases, each with an acceptance gate

| # | Phase | Deliverable | Acceptance gate |
|---|---|---|---|
| 0 | **Preflight** | verify the existing backups by SHA-256 (two 7.1 GB copies already exist); record a baseline manifest; install `psycopg[binary]` | a verified backup and hash are recorded; manifest matches live counts (12 tables, 1,310,311 rows); `content_json` parses for every row; `psycopg` imports |
| 1 | **Schema** | `chatilm_kb` database; docx DDL + extension applied | all **5 tables and 5 enum types** exist; the `UNIQUE`/`CHECK` constraints are present; a test insert round-trips, and deleting its topic is refused by `RESTRICT` |
| 2 | **Normalisation** | path → canonical map; the 238 Fordham URLs resolved; junk paths flagged | no canonical path begins `https://`; casing collisions folded **without merging rows** (per-table counts still match the manifest); 972 → canonical count recorded |
| 3 | **Mapping (human gate)** | **two** artefacts: 972-row path→topic, and ~50-row topic→dual-mapping | **named reviewer signs off** the Islamic classifications; every topic has **≥ 1** European row and **exactly 1** Islamic row; every leaf that will hold content has a path→topic entry |
| 4 | **Load** | all 12 content tables in `topic_content` | `count(*)` = 1,310,311; per-table parity reproduced exactly; zero NULL `topic_id` **and zero NULL `layer`** |
| 5 | **Verify** | parity + integrity report; the 50-query regression set | every vector 1,536 bytes and passes its `CHECK`; sampled floats identical; **no parent topic carries content**; per-domain top-10 overlap vs SQLite ≥ 9/10; legacy views reproduce every old column |
| 6 | **Cutover** | `kb_pg.py` + compatibility shim + legacy views behind a flag | all 20 call sites are migrated or running through the shim; the five direct-SQL sites read the legacy views; app answers the smoke set from PG with SQLite retained as rollback |

Phase 4 is the one to run **on a copy first** and time — 7.1 GB / 1.31M rows
is large enough that an untested batch size will be discovered the hard way.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Mapping is a scholarly judgement** — wrong Islamic classification ships | Phase 3 human gate; mapping stored as data, trivially correctable without re-loading content |
| **972 → topic collapse loses retrieval precision** (523 GlobalFacts paths → one topic) | attributes (`region`, `country`) are preserved and indexed; the Phase 5 overlap test must catch any regression |
| **7.1 GB load fails midway** | idempotent upsert on `(legacy_table, legacy_id)`; batched; resumable |
| **`kb_path LIKE` call sites break** | Phase 6 behind a flag; SQLite vault untouched and retained |
| **Source vault corrupted** | strictly `mode=ro`; preflight backup; source never written |
| **`factbook_countries` vs `facts_gk` merged by mistake** | `layer` attribute preserves the deliberate Layer 1 / Layer 2 split |
| pgvector absent | not depended on; §11 option |

**Rollback:** entirely non-destructive. The new database is additive; the
SQLite vault keeps working until the cutover flag is flipped, and flipping it
back restores the old path.

---

## 11. Open items — decisions needed before Phases 2–3

1. **The 238 Fordham URL paths.** They hold real history content but no usable
   taxonomy. Options: (a) re-derive the subdomain from each row's `source_book`
   / text, (b) map all to `/History/documents_sources`, (c) exclude from this
   migration and fix in the extraction pipeline first. **Recommend (a) with (b)
   as the fallback for rows that cannot be resolved.**
2. **pgvector.** Not installed. Stay on `BYTEA` + Python scoring (recommended —
   it is what runs today), or install pgvector and move scoring into the
   database. Installing it is a separate, optional phase, not a prerequisite.
3. **Reviewer for §6.3** — needed before Phase 3 can pass its gate.
4. **Cooking's branch.** The docx has no culinary branch. Medicine / Tibb
   (nutrition) is defensible; so is adding a new branch. **Recommend medicine,
   flagged in `rationale` as an extension.**
5. **The "missing" tables.** `shia`, `islamic_sects`, `islamic_gk`,
   `christian_sects`, `christian_gk`, `physics` — six distinct corpora, since
   `islamic_gk` / `islamic_heritage_gk` are one slot. Build them, or retire
   them from the registry? **Recommend retiring them from this migration**: the
   new design does not need one table per corpus, and S2's gap list is not a
   backlog (§3.1).
6. **Arabic normalisation.** NFC-normalise in place (changes stored bytes) or
   in a separate derived column? **Recommend a derived column** — the stored
   original is never overwritten.

*Resolved (revision 2, 2026-10-22): the registry documents were reconciled
against the vault (§3.1) and the plan corrected where it disagreed with them —
`legacy_id` type, content-table count, casing-collision scale, `/History` node
count. The reconciliation found that S1 and S2 omit two real tables and that
`islamic_gk` is double-named.*
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
read-only reconnaissance only (§3 figures came from `mode=ro` connections, and
were re-verified on 2026-10-22 for revisions 2 and 3).

**Phase 0 does not wait on anything.** Backup verification, the baseline
manifest and the `psycopg[binary]` install are decision-independent and can run
now. The decisions in §11 gate **Phase 2 onward**:

1. The **238 malformed Fordham paths** — choose rule (a), (b) or (c). [Phase 2]
2. **pgvector** — stay on `BYTEA` + Python scoring, or install it as its own phase. [Phase 2]
3. **The reviewer** for the §6.3 dual mapping. [Phase 3]
4. Cooking's branch, the six "missing" corpora, and Arabic normalisation
   (§11.4–11.6). [Phase 2]

The stale KB path and this plan's location are **resolved** — see §11.

---

## 13. Audit record — revision 3 (2026-10-22)

Every defect below was found by checking the plan against the live vault and
the real call sites, then fixed in place.

| # | Defect | Fix |
|---|---|---|
| 1 | Mapping tables had no uniqueness, yet the gate demanded "exactly one row in each"; the docx's Rule 2 allows several European branches per topic | `UNIQUE (topic_id, branch)` and `UNIQUE (topic_id)`; gate is ≥ 1 European, exactly 1 Islamic |
| 2 | `topic_relationships` edges had no `ON DELETE` behaviour and allowed a topic to be its own parent | `ON DELETE CASCADE` on both FKs, `CHECK (parent <> child)` |
| 3 | `layer DEFAULT 'CORPUS'` would silently mislabel a row whose adapter forgot to set it — collapsing the Layer 1/2 split | No default; adapters set it explicitly; Phase 4 fails on NULL |
| 4 | Nothing enforced that a vector is 384 float32 | `CHECK (octet_length(vector) = vector_dim * 4)` |
| 5 | No index for the collection filter that the sunnah fix depends on | `(topic_id, source_book)` index |
| 6 | `COPY` into `topic_content` cannot upsert — a re-run would abort on the first conflict | Load to an `UNLOGGED` staging table, then `INSERT … ON CONFLICT` |
| 7 | "Create indexes after the bulk load" contradicted the unique index the upsert needs | Unique index during load; secondary indexes after |
| 8 | Phase 1 gate said 4 enum types; the schema defines 5 | Corrected |
| 9 | Phase 2 row had lost its table pipe (malformed markdown table) | Corrected |
| 10 | §6.2 normalised `content_arabic` in place, contradicting the preservation rule | Derived `content_arabic_norm`; original never rewritten |
| 11 | Junk paths were unhandled: `Meta/CATEGORIES` (1,001 rows) and two prose paths | Added to §6.2; mapped to `GlobalFacts` with `quality_flag` |
| 12 | History topics were double-counted (20 sub-domains × 2 heritage lines) | 20 topics; `heritage` is an attribute |
| 13 | No rule stopped content attaching to a parent topic — a query on `arXiv` would load 1.2M rows (1.8 GB) | Leaf-only rule; Phase 5 asserts no parent carries content |
| 14 | §8 claimed the call sites were in `main_orchestrator.py`; in fact there are **20 calls in 13 files** plus **5 direct-SQL sites** that bypass `kb_pg.py` | Full inventory (§8.1), compatibility shim, legacy views |
| 15 | Phase 3 conflated the 972-row path→topic map with the ~50-row dual mapping | Two artefacts and two gates |
| 16 | The Phase 5 regression set was undefined ("a 50-query set") | Fixed per-domain query file, created before Phase 5 |
| 17 | §6.4 omitted `Sovereign` in `quran` and the hadith authenticity grades in `sunnah` | Added, with the explicit "do not clean" warning |
| 18 | §4 said PostgreSQL 17.25; `psql --version` reports **17.6**. The stale-`CLAUDE.md` bullet was still written as open | Corrected; stale bullet marked resolved |
| 19 | §12 said Phase 0 waits on the open decisions | Corrected — Phase 0 is independent |
| 20 | §11 heading said all decisions were needed "before Phase 2", though the reviewer gate is Phase 3 | Retitled to Phases 2–3 |
| 21 | `heritage` was derived from the topic only — but `History` is a single topic fed by **both** history tables, so all 2,522 rows would have received one heritage | Derived from the source table for history; from the mapping elsewhere |

**Verified rather than changed:** 12 content tables / 1,310,311 rows; 972 distinct
paths; 238 URL paths in 2,338 history rows; 261 casing-collision groups / 54,119
rows; every id non-null and unique (including `quran`'s text ids); every vector
1,536 bytes and non-null; all 261 `content_json` values parse; `psycopg`,
`psycopg2`, `sqlalchemy`, `alembic` and `pgvector` all absent from the pinned
venv; PostgreSQL 17.6 running on :5432 with no `vector` extension.
