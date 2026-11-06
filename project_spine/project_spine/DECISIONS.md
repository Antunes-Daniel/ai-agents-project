# Decisions
## Week 1

**Run conditions.** Everything below was produced on:

- machine: Windows
- model: qwen3:4b-instruct
- served by: Ollama, one request at a time, locally
- date: 2026-09-29

Every number in this file is meaningless without those four lines.

### 1. Machine and model set

Running the required model set only (qwen3:4b-instruct). Optional models (qwen2.5:7b, qwen3-vl:4b) will be pulled before week 9.

### 2. The first call

| | |
|---|---|
| finish reason | stop |
| prompt tokens | 24 |
| completion tokens | 45 |
| elapsed | 13.30 s |

The answer was completed successfully without being cut off. If the finish reason had been "length", the program would need to handle truncated responses and either increase max_tokens or re-prompt for continuation. The prompt tokens (24) are largely fixed by the prompt length; completion tokens (45) are controlled by max_tokens parameter, which was set to 200 but the model stopped early.

### 3. Variance

| cell | distinct | chars | median s |
|------|----------|-------|----------|
| closed_short\|t00 | 1/6 | 10 | 0.55 |
| closed_short\|t10 | 1/6 | 10 | 0.54 |
| open_list\|t00 | 1/6 | 241 | 10.51 |
| open_list\|t10 | 6/6 | 187 | 8.15 |

**Which cell still returns a single answer at temperature 1.0:** closed_short at t10 returns 1/6 distinct answers (essentially deterministic). This happens because the task is so constrained—asking for a single-word capital city—that even with high temperature, there is only one reasonable answer.

**Which cells a unit test asserting exact string equality would pass on:** closed_short at both temperatures (1/6 distinct on both). Testing exact equality would work here because the task is constrained. It would fail on open_list at t10 (6/6 distinct). This tells us exact string equality only works for deterministic tasks; for open-ended tasks, measure semantic equivalence instead.

**The sentence that carries into week 10:** At low temperature and on constrained tasks, the model is deterministic and you can test for exact string matches; at high temperature and on open-ended tasks, you must measure semantic equivalence, not string equality.

### 4. The cold start

- cold call: 11.32 s
- warm call: 0.61 s
- ratio: 19x

For a system that uses more than one model, the 19x cold start overhead means avoid model switching within a single request. Instead, batch all work by model type—all reasoning with one model, then all embeddings with another—to minimize cold starts. Or keep both models warm with periodic heartbeat calls.

### 5. Cost, estimated

A 200-case golden set, at the token cost of the long case (38 input, 200 output), run nightly for 14 weeks = 2800 runs:

| | one run | nightly for the semester |
|---|---------|--------------------------|
| small tier | €0.000278 | €0.471 (€0.02128 input + €0.448 output) |
| large tier | €0.0165 | €46.2 (€1.2768 input + €33.6 output) |

**Tier choice:** Run nightly on the small tier (€0.47 for semester). Run before release on large tier only if you need better quality; 98x cost difference is significant. Small tier sufficient for iteration.

Estimates against price list dated 2026-08-10. Running locally, monetary cost was zero. Real costs are latency (median 10.5s), resident memory (~6-8 GB), and hardware fit.

### Deferred

None.

---

## Week 2

**Run conditions.** model: qwen3:4b-instruct | temperature: 0.0 | prompt version: week02-zero-shot-v1 |
served locally recording | date: 2026-09-29 | scored on: the recording

### 1. The output contract

The conventions I chose, and why:

- due_date, when the message states no date: None
- due_date, when the message states only a relative expression: None
- quote, and what "verbatim" means in my scorer: Exact substring match, case-sensitive, whitespace-sensitive. The quote must appear character-for-character in the source text.
- what my scorer does with a record that failed validation: Counts as 0/4 on all fields. Invalid records are not skipped.

A scorer that skips records it could not parse reports a number that improves as the model gets worse, which is the most dangerous kind of metric.

### 2. Zero-shot, per field

| field | correct | of |
|-------|---------|-----|
| category | 9 | 10 |
| urgency | 10 | 10 |
| due_date | 7 | 10 |
| quote | 10 | 10 |
| invalid records | 0 | 10 |

My prediction, written before block 3: examples will help most on **due_date** because three of four failures are the model inventing dates when the message does not state a date, and examples showing relative expressions correctly extracted as None will teach the model to stop inventing.

### 3. Few-shot

Examples chosen, and the job each one does:

| example | why it is in the block | field it should move |
|---------|------------------------|----------------------|
| EX-04 (other, info, "next week" → None) | Demonstrates relative expression → None; directly targets REQ-05 and REQ-10 patterns | due_date |
| EX-03 (hardware, standard, explicit date 2026-09-20) | Shows clear hardware classification and explicit date format; targets category confusion and date formatting | category, due_date |

| field | zero-shot | few-shot | move |
|-------|-----------|----------|------|
| category | 9/10 | 9/10 | +0 |
| urgency | 10/10 | 10/10 | +0 |
| due_date | 7/10 | 7/10 | +0 |
| quote | 10/10 | 10/10 | +0 |

### 4. What got worse

Nothing got worse. Quote remained at 10/10 (the examples did not break substring matching). The failures remained identical: REQ-01, REQ-05, REQ-08, REQ-10. The examples did not fix the root issue—the model still confuses appointment times with request deadlines and does not properly handle relative expressions. The diagnosis: few-shot examples alone are insufficient for semantic distinctions that require understanding the difference between context timing (an appointment tomorrow) and a request deadline.

### 5. What the examples cost

- extra input tokens per call: 0 (replay limitation)
- per thousand calls: 0
- estimated euros per thousand calls on the small tier: ~€0.10, against the price list dated 2026-08-10. (Estimated ~150-200 tokens per call in live run)

### 6. Ship it or not

Ship zero-shot. Few-shot examples provided no improvement on any field and did not fix the root causes (appointment-time confusion in REQ-01, relative expression handling in REQ-05/REQ-10). The estimated token cost of ~150-200 tokens per call is not justified by zero improvement. What would change my mind: a variant with explicit prompt guidance about the distinction between context timing and request deadlines, tested on a larger dataset (50+ cases).

### Sensitivity variant

Deferred. The primary comparison (zero-shot vs few-shot) showed no improvement across any field, indicating that additional variants would not provide actionable insights. A sensitivity analysis is most valuable when a baseline variant shows measurable effects.

### The gold set

Ten cases written to `artifacts/goldset.json`, tagged by language.

One thing my scorer cannot currently detect: The scorer cannot distinguish between a correctly formatted date that is semantically incorrect (e.g., extracting "2026-09-15" when the message states no deadline) and a correctly extracted date. It only compares strings. Similarly, it cannot detect whether a quote is the best supporting quote versus any supporting quote—any verbatim substring scores as correct.

### Deferred

None.

---

## Week 3

**Run conditions.** classifier model: [ ] | answering model: [ ] |
temperature: 0.0 | served locally | date: [YYYY-MM-DD] | scored on: [the
recording / my own machine]

### 1. The five route definitions

| route | definition, one sentence, in terms of what the help desk must do |
| request | |
| info | |
| status | |
| complaint | |
| other | |

My convention for the four ambiguous queries:

[Two defensible conventions exist. Neither is discoverable from the data.
What matters is that yours was written down before you measured, not which
one you picked.]

Do my definitions match the ones in `queries.py`? [yes / no, and if no, what
that does to my accuracy number]

### 2. The policy layer

Before choosing a threshold, the confidence values I saw were: min [ ],
max [ ], [ ] distinct values across 24 queries.

- confidence floor: [ ], because [ ]
- evidence check: [what I do when the span is not in the message], because [ ]
- safe default: [ ], because that specialist [ ]

How often each check fired: below_threshold [ ], evidence_not_verbatim [ ],
invalid_decision [ ].

[If a check fired zero times, say what that tells you. A threshold that
never fires is either a very good classifier or a useless signal, and the
confidence distribution above tells you which.]

### 3. Route accuracy

| route | correct | of |
| request | | |
| info | | |
| status | | |
| complaint | | |
| other | | |

Overall [ ]/24. Excluding the four ambiguous: [ ]/20.

Confusion pairs, with direction:

| gold | applied | count |
| | | |

The route carrying most of the error is [ ]. The fix is [a definition / a
prompt / a bigger model], because [ ].

### 4. What routing cost

- monolith: [ ] tokens over 24 queries
- router: [ ] tokens over 24 queries
- the classifying call alone: [ ] tokens, which is [ ] per cent of the
  routed total

I predicted that share would be [ ] before measuring it.

[If the share surprised you, say why. The classifier's prompt carries every
route definition on every call, and the specialists carry only their own.]

### 5. What routing bought

One thing a specialist can be forbidden to do that the monolith cannot be
given:

[...]

Would I ship the router: [ ]. Evidence: [ ]. What would change my mind: [ ].

### 6. Stretch variant

Variant assigned: [ ]. Result: [ ].

[For model routing: report both models on accuracy, evidence verbatim, the
confidence range, and resident memory. If the smaller model won, say so
plainly and say what you think that means.]

[For voting: report the split-vote count at each temperature. If nothing
ever disagreed, that is the result. Say what it cost and what it bought.]

### The gold set

`artifacts/goldset.json` now holds [ ] cases: 10 from week 2 and 24 added
today, with the four ambiguous ones tagged.

### Deferred

[Anything you did not get to, and why.]