# NAM Discourse Pilot — Experiment Log

Status as of 2026-06-18. Read this before resuming. Full architecture spec is at
`../nam_discourse_plan.md`; the JSON-substrate / Cohere adaptation decisions are in this repo's
saved Claude Code plan ("NAM Discourse Pilot — 1965-1975 Test Experiment").

## What this is

A scaled-down test run of the multi-agent system in `nam_discourse_plan.md`: discover whether
UN General Debate speeches by Non-Aligned Movement (NAM) members show a distinctive discourse,
without committing in advance to which level (lexical/phraseological/rhetorical/thematic/
positional) carries it. Scoped to **1965-1975**. Runs on flat JSON/JSONL files, not Postgres —
fully isolated from the live `ungdc_db`/web app in the parent repo.

LLM provider is **Cohere** (`ClientV2`), not Anthropic — `command-a-03-2025` for structured
extraction/labeling tasks, `command-a-reasoning-08-2025` for the Skeptic and Coordinator's
adversarial/arbitration reasoning. `COHERE_API_KEY` must be set; the conda env `ungdc`
(Python 3.12) has the SDK installed and is what was used throughout — the Windows Store
Python 3.8 (`python3` on PATH) cannot build some of Cohere's dependencies, use `python`/`pip`
from the `ungdc` conda env, not `python3`.

## What's done

### 1. NAM membership data (verified, not just sourced)

- `data/nam_membership.json` — every NAM accession 1961/1964/1970/1973 (the cohorts relevant to
  1965-1975), pulled from Wikipedia's "Non-Aligned Movement" article and **cross-checked against
  the actual ISO3 codes present in the corpus** for this window. All resolved cleanly; the corpus
  uses modern ISO3 codes applied retroactively.
- `data/nam_membership_notes.md` — write-up of five known ambiguities, **not yet signed off by
  the PI**:
  1. Chile (CHL) — coded NAM=1 continuously from 1971 despite the Sept 1973 coup ending de facto
     engagement; no formal exit date exists in the source. Current default keeps CHL=1 through 1975.
  2. Argentina (ARG) — joined 1973, a genuinely atypical NAM member; flagged, not a data error.
  3. Yugoslavia / Cyprus — European NAM members, deliberate regional-confound test cases.
  4. YEM vs YMD coding — **spot-checked and verified** against actual speech text: `YEM` speeches
     literally say "the delegation of the Yemen Arab Republic" (North Yemen, NAM since 1961);
     `YMD` (South Yemen, NAM since 1970) confirmed by absence pre-1971 and presence from 1971.
  5. `development_tier` in country_metadata — no clean contemporaneous classification exists for
     1965-1975; built as a coarse, explicitly low-confidence proxy.
- `data/speeches_1965_1975.jsonl` — 1233 speeches, 138 countries, 45.7% NAM-flagged. Spot-checked:
  DZA=NAM throughout, IRN/PAK=non-NAM throughout (both join 1979), BFA flips to NAM exactly in 1973.
- `data/country_metadata.json` — region (from the corpus's own `UN_REGION` column),
  independence_year (filled from general historical knowledge for 20th-century states only),
  development_tier (low-confidence proxy). One corpus data quirk found and patched: Zambia (ZMB)
  is mislabeled `UN_REGION=OTHER` in the source CSV for this period; tier was hand-overridden to
  "low" rather than trusting the bad region label.

Rebuild commands: `python src/build_speeches.py` then `python src/build_country_metadata.py`
(run from `nam_pilot_1965_1975/`).

### 2. Infrastructure gates — built and validated against live Cohere calls

- `src/nam/store.py` — flat-file JSONL repository (append-only writers, scan/filter readers,
  incrementing IDs). Substrate lives in `substrate/`.
- `src/nam/verbatim.py` — exact-span verification. Unit-tested (`tests/test_verbatim.py`, 4/4
  pass) AND validated on real model output (see RA1 smoke test below — it actually caught real
  hallucinated quotes, not just synthetic test cases).
- `src/nam/llm.py` — thin Cohere `ClientV2` wrapper using `response_format` JSON-schema mode.
  Smoke-tested live: returns correctly-typed structured JSON.
- `src/nam/sampling.py` — matched-control sampling (region + development_tier + independence-year
  proximity), always includes hard-case Cold War neutrals (Finland, Austria, Sweden) as controls
  regardless of match score. Run live for 1973: **62 NAM speeches, 65 matched controls**, written
  to `substrate/batches.jsonl` as `batch_id: 1`.
- `src/nam/gridutil.py` — resolves an agent's quoted text to a char span (`body.find` + re-verify),
  and resolves a proposed code label against the current grid (reuse-or-create).
- `src/nam/reliability.py` — inter-coder agreement between two RA1 instances. **Rewritten once
  already** (see finding below) to compare annotated *character spans*, not code-label strings.

### 3. RA1 (inductive coder) — smoke-tested on one real 5-speech lot, two independent instances

Ran live against the first 5 speeches of the 1973 batch (`LBN_28_1973, BHR_28_1973, GAB_28_1973,
OMN_28_1973, SAU_28_1973`), two instances (`RA1-A`, `RA1-B`), `command-a-03-2025`, temp 0.2
(deliberately not 0 — two temp-0 instances would just clone each other and the reliability check
would be meaningless).

**Finding 1 — the verbatim gate works on real hallucinations, not just test cases.** Of 40 raw
annotations across both instances, 7 were rejected because the quoted text was a paraphrase, not
an exact substring of the speech (e.g. RA1-B claimed Oman's speech said "My Government and
delegation welcomes the new Members..." — close in spirit, wrong verbatim). 33 were accepted and
persisted to `substrate/annotations.jsonl` / `substrate/codes.jsonl` (`grid_version: 1`).

**Finding 2 — the first reliability metric was broken, and I fixed it.** Measuring agreement by
exact code-label string match gave 0.0/0.0 — but that's an artifact: with an empty starting grid,
RA1-A and RA1-B each invented their own label vocabulary from scratch (e.g. RA1-A's
`colonialism_and_racial_discrimination` vs RA1-B's `anti_colonialism` — plausibly the same
observation, different label). Rewrote `reliability.py` to measure agreement on the *character
spans* each instance flagged instead. Re-run result: **span_overlap_agreement = 0.097**,
**level_agreement_on_overlap = 0.75 (on 4 overlapping pairs)**.

**Finding 3 — logged the low score as an open question rather than deciding myself.** 0.097 is
well below the configured escalation threshold (`config.yaml: thresholds.reliability_escalate_below
= 0.6`). Per the autonomy framework, this is a Tier-2 escalation: written to
`substrate/questions.jsonl` as `question_id: 1`, **currently open, unanswered**. Two competing
interpretations logged: (a) expected cold-start noise — no shared grid existed yet, agreement
should improve once lot 2+ codes against a populated grid; (b) the 5-speech lot itself may be too
small/heterogeneous (Lebanon, Bahrain, Gabon, Oman, Saudi Arabia have little in common) for two
independent coders to converge on the same salient passages at all. **Not yet resolved.**

## Substrate state right now

- `substrate/grid_versions.jsonl`: 1 row (`version_id: 1`, initial empty grid, not frozen)
- `substrate/codes.jsonl`: codes proposed by RA1-A and RA1-B on the lot-1 smoke test (mix of
  thematic_frame-level codes: Middle East conflict, anti-colonialism, UN critique, etc.)
- `substrate/annotations.jsonl`: 33 verbatim-verified annotations from the lot-1 smoke test
- `substrate/batches.jsonl`: 1 row, the full 1973 NAM+control batch (62+65 speeches)
- `substrate/questions.jsonl`: 1 open question (the reliability finding above)
- `substrate/decisions.jsonl`: empty — no coordinator arbitration has run yet
- `substrate/temporal_signatures.jsonl`: empty — RA3 hasn't run (needs >=2 coded years)

## Not started yet

- RA2 (boundary tester) — characteristic/shared/peripheral distinctiveness labeling
- Skeptic — adversarial objections to distinctiveness claims
- Coordinator — reconciles RA1/RA2/skeptic, writes grid deltas + decisions, escalates hard cases
- `orchestrator.py` — wiring the full deterministic loop + convergence/freeze logic
- `cli.py` — `run-batch`, `questions list/answer`, `grid show/diff`, `report`
- Finishing the rest of the 1973 batch (only 5 of 62 NAM speeches coded so far)
- The 1965-1972 / 1974-1975 sweep, RA3 diachronic pass, `report.py` memo scaffold

## Recommended next steps, in order

1. **Answer `questions.jsonl` #1** (or decide to proceed and let reliability re-settle once a
   real grid exists — your call, not mine).
2. Decide on the Chile/Argentina/Yemen items in `data/nam_membership_notes.md` (or explicitly defer
   them — they don't block anything until RA2 boundary-testing actually touches those countries'
   speeches, which will happen once the full 1973 batch runs, since CHL and ARG are both NAM-flagged
   in 1973).
3. Build RA2 + Skeptic + Coordinator (same pattern as `agents/inductive.py`: a prompt file in
   `agents/prompts/`, a JSON schema, a thin wrapper around `llm.call_json`).
4. Wire `orchestrator.py` and run the **rest** of the 1973 batch (57 more NAM speeches, in lots of
   5, per `config.yaml: batch_size`) before touching any other year.
5. Only after a full human review of 1973's journal + questions, sweep the remaining 10 years.

## Known gotchas for next session

- Use `python`/`pip` (conda env `ungdc`, 3.12), not `python3` (Windows Store stub, 3.8 — cannot
  build Cohere's `tokenizers` dependency from source).
- LLMs cannot reliably report character offsets — always resolve quotes via `gridutil.locate_span`
  (substring search + re-verify), never trust offsets the model invents.
- RA1 temperature is intentionally 0.2, not 0.0, specifically so the two independent instances
  don't degenerate into clones (see Finding 2).
