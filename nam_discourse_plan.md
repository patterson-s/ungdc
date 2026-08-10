# NAM Discourse — Multi-Agent Text Analysis System

A build plan for Claude Code. The goal is a system that, **given a corpus of UN General Debate speeches already labelled with a NAM (Non-Aligned Movement) flag**, discovers whether there is a *distinctive* NAM discourse — allowing for uneven boundaries, uneven adoption across states, and change over time.

This is **boundary work**: abductive, hermeneutic, iterative. It is *not* a classification task. Read the "Framing and non-goals" section before writing any code; it constrains the whole design.

---

## 1. Context for the implementing agent

- **Existing infrastructure**: PostgreSQL is already running. The speech corpus already exists (or will be loaded) with a NAM flag, year, and country. The system *reads* the corpus; it does not produce the labels.
- **Architecture standard**: follow a three-layer separation — raw ingestion → derivative production → exploration. The shared substrate (the database) is the centre of the design. Agents are functions that read and write the substrate and leave a trail; they do not talk peer-to-peer.
- **Control flow is deterministic Python, not LLM routing.** The orchestrator decides what runs next. Agents only produce content; they never decide the next step. This is for auditability — a human must be able to drop in at any point and resituate themselves.
- **Every claim is grounded in a verifiable verbatim.** An annotation without an exact-substring quote is rejected. This is the primary defence against hallucinated evidence.

Suggested stack: Python 3.11+, `psycopg`/`psycopg2` for Postgres, Anthropic API via a thin model-agnostic client (so a second provider can be swapped in). No heavy orchestration framework — a plain explicit loop is preferred over LangGraph here, because control flow must be readable.

---

## 2. Framing and non-goals

The unit of analysis is "distinctive discourse," and we deliberately do **not** commit in advance to *which level* of discourse carries the distinction. It could be lexical (words), phraseological (recurring formulae), rhetorical moves, thematic frames, or positionality. The level is a **result**, not an input. Agents tag everything by level; the contrast step reveals which level actually discriminates.

Non-goals — enforce these as design constraints:

1. **Do not build a classifier.** The NAM label is given. Do not train, fine-tune, or prompt a model to *predict* the label. The task is to characterise, not to predict.
2. **No ungrounded claims.** Reject any annotation whose stored span text does not exactly match the source slice. No "close paraphrase" stands in for a quote.
3. **The skeptic is not optional.** Its objections must be *resolved* in the journal, never silently dropped.
4. **The null result is a finding.** Weak distinctiveness, or distinctiveness only in some periods or for some states, is a publishable outcome. Do not bias the system toward confirming that a NAM discourse exists.
5. **Do not let the system substitute for interpretive writing.** The pilot's definition of done includes a human-written interpretive memo. If standing up the orchestration takes longer than hand-coding one year, that is the signal to stop building and start reading.

The dominant failure mode of LLM coders is manufacturing coherence everywhere (apophenia) and inventing quotes. The verbatim check, the skeptic role, and inter-coder reliability all exist to counter this.

---

## 3. The shared substrate (data model)

Implement in `db/schema.sql`. All meaningful state lives here; the only legitimate private state is an agent's reasoning draft *before* it deposits a grounded annotation.

```sql
-- RAW LAYER ---------------------------------------------------------------
-- Assumed to exist or be loaded. The system reads, never relabels.
CREATE TABLE speeches (
    speech_id     TEXT PRIMARY KEY,
    year          INT  NOT NULL,
    country_iso   TEXT NOT NULL,
    nam_flag      BOOLEAN NOT NULL,
    speaker       TEXT,
    body          TEXT NOT NULL,           -- full speech text, exact
    source_meta   JSONB DEFAULT '{}'::jsonb
);

-- Covariates for matched control sampling (RA2). If absent, RA2 must flag it.
CREATE TABLE country_metadata (
    country_iso        TEXT PRIMARY KEY,
    region             TEXT,
    development_tier   TEXT,                -- e.g. low/lower-mid/upper-mid/high
    independence_year  INT,
    notes              JSONB DEFAULT '{}'::jsonb
);

-- DERIVATIVE LAYER --------------------------------------------------------
CREATE TABLE grid_versions (
    version_id   SERIAL PRIMARY KEY,
    parent_id    INT REFERENCES grid_versions(version_id),
    created_at   TIMESTAMPTZ DEFAULT now(),
    rationale    TEXT NOT NULL,            -- why this version exists
    frozen       BOOLEAN DEFAULT FALSE
);

-- The living typology. Codes belong to a version; changes create new rows.
CREATE TABLE codes (
    code_id      SERIAL PRIMARY KEY,
    version_id   INT REFERENCES grid_versions(version_id),
    label        TEXT NOT NULL,
    definition   TEXT NOT NULL,
    level        TEXT NOT NULL CHECK (level IN
                  ('lexical','phraseological','rhetorical_move',
                   'thematic_frame','positionality')),
    status       TEXT NOT NULL DEFAULT 'candidate'
                  CHECK (status IN ('candidate','active','retired','merged')),
    exemplars    JSONB DEFAULT '[]'::jsonb -- [{speech_id, char_start, char_end, quote}]
);

-- Every applied code, grounded in a verified span.
CREATE TABLE annotations (
    annotation_id   SERIAL PRIMARY KEY,
    speech_id       TEXT REFERENCES speeches(speech_id),
    code_id         INT  REFERENCES codes(code_id),
    grid_version    INT  REFERENCES grid_versions(version_id),
    level           TEXT NOT NULL,
    char_start      INT  NOT NULL,
    char_end        INT  NOT NULL,
    span_text       TEXT NOT NULL,         -- MUST equal body[char_start:char_end]
    distinctiveness TEXT CHECK (distinctiveness IN
                      ('characteristic','shared','peripheral')),  -- set by RA2
    agent           TEXT NOT NULL,         -- which agent / instance
    model           TEXT NOT NULL,         -- provenance
    prompt_version  TEXT NOT NULL,         -- provenance
    confidence      REAL,
    batch_id        INT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE temporal_signatures (
    code_id     INT REFERENCES codes(code_id),
    signature   TEXT CHECK (signature IN
                  ('founding','event_peak','durable_core','cyclical','drift')),
    evidence    JSONB,                     -- spans across years
    set_by      TEXT,                      -- RA3
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- EXPLORATION LAYER -------------------------------------------------------
CREATE TABLE batches (
    batch_id        SERIAL PRIMARY KEY,
    year            INT NOT NULL,
    sample_method   TEXT,
    speech_ids      JSONB,                 -- NAM speeches in this batch
    control_ids     JSONB,                 -- matched non-NAM controls
    grid_version_in INT REFERENCES grid_versions(version_id),
    grid_version_out INT REFERENCES grid_versions(version_id),
    status          TEXT DEFAULT 'open',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE decisions (              -- the journal: append-only
    decision_id   SERIAL PRIMARY KEY,
    batch_id      INT REFERENCES batches(batch_id),
    type          TEXT CHECK (type IN
                    ('typology_change','arbitration','escalation','freeze')),
    summary       TEXT NOT NULL,
    evidence      JSONB,                   -- verbatims
    interpretations JSONB,                 -- competing readings considered
    resolution    TEXT,
    decided_by    TEXT,                    -- 'coordinator' or 'human'
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE questions (              -- escalation queue to the human
    question_id   SERIAL PRIMARY KEY,
    batch_id      INT REFERENCES batches(batch_id),
    status        TEXT DEFAULT 'open' CHECK (status IN ('open','answered')),
    question      TEXT NOT NULL,
    context_spans JSONB,                   -- 2-3 verbatims
    interpretations JSONB,                 -- competing readings
    recommendation TEXT,                   -- coordinator's suggested resolution
    human_answer  TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    answered_at   TIMESTAMPTZ
);
```

Append-only tables (`decisions`, `annotations`, `grid_versions`) are the audit trail. Never update-in-place; create new rows. The trail is what lets a human resituate.

---

## 4. The agents (instruction sheets)

Each agent is a prompt template plus a strict I/O contract. Store prompts in `src/nam/agents/prompts/` as versioned files (the `prompt_version` recorded on every annotation must point to one). Agents return structured JSON; the orchestrator validates, verifies spans, and persists. An agent that returns an unparseable or unverifiable result is retried once, then escalated as a question.

### RA1 — Inductive coder
- Input: a batch of NAM speeches + the current grid (codes with definitions and exemplars).
- Job: read the batch in small lots (≈5 speeches), propose new codes or apply existing ones, **tag every observation with its level**, and ground each in an exact span (`char_start`, `char_end`, `quote`). Reflect on fit after each lot and revise proposed codes before the next lot.
- Output: proposed code deltas + annotations. It does **not** decide the level that matters; it labels all levels it sees.
- Run two independent instances per batch for inter-coder reliability (see §6).

### RA2 — Boundary tester
- Input: RA1's codes + the same batch + **matched non-NAM controls** (see §5).
- Job: for each code, decide whether it is `characteristic` (concentrated in NAM speeches), `shared` (appears widely in matched controls — therefore not distinctive), or `peripheral` (rare/marginal). Ground decisions in verbatims from both NAM and control speeches.
- Output: distinctiveness labels written onto annotations; notes on overlap.

### Skeptic — Adversary
- Input: the candidate distinctive codes + their evidence.
- Job: attack each distinctiveness claim. Standard objections to test: "this is just UN-era boilerplate," "this is a regional effect, not NAM," "the exemplars come from only 2-3 states," "this is a Global-South or young-state effect confounded with NAM." Each objection cites evidence.
- Output: objections, each tied to a specific code, that the coordinator must resolve or escalate. Objections are never deleted, only resolved in the journal.

### RA3 — Diachronic analyst
- Input: committed grids and annotations across adjacent years.
- Job: assign each code a temporal signature — `founding`, `event_peak`, `durable_core`, `cyclical`, `drift`. Watch specifically for the same term whose *meaning* shifts over time (e.g. "sovereignty" 1965 vs 2005) — the label persists, the discourse changes. May propose retiring temporally isolated codes or merging drifting ones.
- Runs at a slower cadence than RA1/RA2 (across years, not within a batch). RA3 is the main driver of typology revision, so the loop's feedback edge runs mostly through it.

### Coordinator — Orchestrator-assistant
- Input: outputs of RA1, RA2, skeptic.
- Job: reconcile RA1/RA2 disagreements and skeptic objections; produce a grid delta; write journal entries; and **escalate hard cases to the human** as compact packets (the question + 2-3 verbatims + competing interpretations + a recommendation). It does not arbitrate the hardest cases alone — it escalates.
- Note: the coordinator produces *content* (arbitrations, deltas, packets). The deterministic orchestrator (code, not LLM) still controls execution order.

---

## 5. Matched control sampling (the technical crux for RA2)

A plain "NAM vs all non-NAM" contrast is invalid because NAM membership is confounded with region, era (decolonisation, Cold War), development tier, and recent independence. A trait that looks "NAM-distinctive" may only be "Global South" or "1970s" or "newly independent."

Implement in `src/nam/sampling.py`:
- For each NAM speech in a batch, draw non-NAM controls **matched on the same year**, comparable region and development tier, and similar independence cohort, using `country_metadata`.
- Include **hard cases**: states non-aligned *de facto* but not members, and pivot states.
- If `country_metadata` is missing or sparse, RA2 must raise a question rather than silently contrasting against an unmatched pool.

---

## 6. Inter-coder reliability

Run each batch through two independent RA1 instances. Compute agreement on which codes were applied to which spans (a simple overlap/agreement metric is sufficient to start — exact code-on-span agreement, plus a looser code-presence agreement). Surface disagreements: they mark exactly where the typology is under-specified, and they become candidate questions for the human. Store the reliability number per batch.

---

## 7. Orchestration loop

Implement in `src/nam/orchestrator.py` as an explicit, deterministic sequence. One within-year iteration:

1. `sample_batch(year)` → batch (NAM speeches + matched controls).
2. `inductive_code(batch, current_grid)` ×2 instances → proposed codes + annotations (level-tagged, span-verified).
3. `reliability(batch)` → agreement metric; flag disagreements.
4. `boundary_test(batch, controls, codes)` → distinctiveness labels.
5. `skeptic_challenge(codes, evidence)` → objections.
6. `coordinator_arbitrate(...)` → resolutions, grid delta, escalated questions.
7. `commit_grid(delta)` → new `grid_version` + `decisions` entries.
8. Periodically: `diachronic_pass(year, year±1)` → temporal signatures; may propose retire/merge.

Between every step: validate output, verify spans (`src/nam/verbatim.py` — reject if `span_text != body[char_start:char_end]`), persist, log provenance (`model`, `prompt_version`).

Convergence / freeze (`src/nam/convergence.py`): stop iterating when grid churn (codes added/changed/retired per batch) falls below a threshold over N consecutive batches **and** skeptic objections are being resolved rather than accumulating. Expose a manual `freeze` command. Do not let the loop run indefinitely.

---

## 8. Human-in-the-loop

The `questions` queue is the only vertical link. Everything else is lateral (agents ↔ substrate). Provide a CLI so the human can drop in:

```
run-batch     --year YYYY        # run one iteration
questions     list               # open escalations
questions     answer ID "..."    # resolve one
grid          show [--version V]
grid          diff V1 V2         # what changed and why
report        --year YYYY        # generate interpretive memo scaffold
reliability   --batch ID
freeze        --reason "..."
```

`grid diff` and the journal together must let a human resituate in a couple of minutes.

---

## 9. Suggested project layout

```
nam_discourse/
  README.md
  pyproject.toml
  config.yaml              # db dsn, model(s), thresholds (churn, N, confidence)
  db/
    schema.sql
    migrations/
  src/nam/
    db.py                  # connection + repositories (one per table group)
    llm.py                 # thin, model-agnostic client; logs model+prompt_version
    verbatim.py            # exact-span verification (hard gate)
    sampling.py            # batch + matched controls
    reliability.py
    convergence.py
    report.py              # interpretive memo scaffold generator
    orchestrator.py        # the deterministic loop
    cli.py
    agents/
      inductive.py
      boundary.py
      skeptic.py
      diachronic.py
      coordinator.py
      prompts/             # versioned prompt templates (instruction sheets)
  reports/                 # generated memo scaffolds
  tests/
```

Model configuration: allow a cheaper model for bulk inductive passes and a stronger one for arbitration and the skeptic, or a single strong model — keep it configurable. Use low temperature for coding passes. Record `model` and `prompt_version` on every annotation.

---

## 10. Pilot scope and definition of done

Start with **one dense year** — a decolonisation/NAM peak (e.g. 1973 or 1979; make it a parameter). 20-40 NAM speeches plus matched controls.

The pilot is done when the system has produced:
- a filled database (raw read, derivative + exploration populated);
- a versioned grid of **level-tagged** codes with distinctiveness labels;
- a decision journal capturing typology changes and arbitrations;
- a question queue with the genuinely hard cases escalated;
- an inter-coder reliability number for each batch;
- a generated interpretive memo scaffold.

Two acceptance tests:
1. The human can open the journal + questions and resituate themselves in a few minutes.
2. The memo scaffold is good enough that writing the interpretation is faster than starting from the raw speeches.

If building the orchestration is taking longer than it would take to hand-code one year, stop and hand-code the year — the system is meant to absorb maintenance debt, not to replace the interpretive work.

---

## 11. Build order

1. `schema.sql` + `db.py` repositories. Confirm the corpus loads and spans can be sliced exactly.
2. `verbatim.py` and `llm.py` (the two gates everything depends on).
3. `sampling.py` (batch + matched controls); confirm `country_metadata` coverage, flag gaps.
4. RA1 inductive coder + reliability (two-instance run) on one batch.
5. RA2 boundary tester.
6. Skeptic + coordinator + journal/questions writing + CLI for questions.
7. `orchestrator.py` wiring steps 1-7 of the loop; convergence/freeze.
8. RA3 diachronic pass across two years.
9. `report.py` memo scaffold.

Ship and test each stage on the pilot year before moving on.
