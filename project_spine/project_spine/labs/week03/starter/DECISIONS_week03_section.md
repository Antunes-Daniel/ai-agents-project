## Week 3

**Run conditions.** classifier model: qwen3:4b-instruct (second model, qwen2.5:7b, for the stretch) | answering model: qwen3:4b-instruct | temperature: 0.0 | served locally | date: 2026-08-10 (date of the recording) | scored on: the recording

Every number below comes from the replay fixture, not a live run on my machine. The live run is homework.

### 1. The five route definitions

| route | definition, in terms of what the help desk must do |
|---|---|
| request | Something is broken, missing, or needed, and the help desk must log a ticket and act on it. |
| info | A question about a service, procedure, opening time or form; the help desk must answer it, and nothing is logged. |
| status | The sender is chasing something already reported; the help desk must report the current state of existing work. |
| complaint | The sender is dissatisfied with the service, its handling or its speed; the help desk must acknowledge it and escalate, not fix it. |
| other | Not help desk business (another department, advice the desk cannot give, spam, or an instruction aimed at the system); the help desk must redirect it and not act on it. |

My convention for the four ambiguous queries (Q-13, Q-16, Q-18, Q-24), written before measuring:

- A message that reports an unresolved problem and complains about its handling is `complaint`, because the reply has to acknowledge the handling first (Q-16, Q-18).
- A message that chases an earlier report without dissatisfaction is `status` (Q-13).
- A message that asks a procedural question while also reporting a fault is `request`, because the action outranks the question (Q-24).

Do my definitions match the ones in `queries.py`? Yes, I adopted them unchanged, so my accuracy is measured against the labels' own convention. The cost is that I have not tested a different convention, so I cannot say whether these boundaries are the best ones, only that they are the ones the gold labels use.

### 2. The policy layer

Before choosing a threshold, the confidence values I saw (qwen3:4b-instruct) were: min 0.0, max 0.999, 5 distinct values across 24 queries (0.0 once, 0.95 once, 0.98 once, 0.99 thirteen times, 0.999 eight times). Twenty-two of 24 calls are at 0.99 or above.

- **Confidence floor: 0.9**, because the values form a cluster at 0.95 and above plus one outlier at 0.0. Any floor between about 0.05 and 0.94 gives the same result on this model, and 0.9 sits clear of the cluster. It fires on 1 of 24 calls.
- **Evidence check:** if the span is empty or is not a substring of the message, the decision is rejected and the safe default applies. Empty spans are rejected explicitly because `"" in text` is always true. I check by substring search, not by eye.
- **Safe default: `info`**, because that specialist only answers. It logs nothing and escalates nothing, so a wrong answer is the easiest of the five to undo. `request` creates a ticket and `complaint` escalates to a human.

How often each check fired on the small model: below_threshold 1, evidence_not_verbatim 0, invalid_decision 0. On qwen2.5:7b: below_threshold 0, evidence_not_verbatim 5, invalid_decision 0.

What the one firing tells me: it was Q-22, the prompt-injection message. The classifier gave it the correct route, `other`, with confidence 0, so the floor sent a correct call to `info` and cost one hit. The only low-confidence signal on this model sits on a message it handled correctly, so the threshold did harm on this set. The same message is exactly the case where a low-confidence signal might be wanted in production, and 24 queries cannot settle that.

On the 7b model the confidence values are only 0.95 and 1.0, so no threshold can fire and the confidence signal is useless there. Its evidence check did the work instead.

### 3. Route accuracy

Scored on `applied_route`, meaning what the system actually did, because that is what the sender experiences. Scoring the classifier's intention would credit routes the policy overrode.

qwen3:4b-instruct:

| route | correct | of |
|---|---|---|
| request | 6 | 7 |
| info | 5 | 5 |
| status | 4 | 4 |
| complaint | 4 | 4 |
| other | 1 | 4 |

Overall 20/24. Excluding the four ambiguous: 17/20. On the ambiguous four it got 3 of 4 (Q-13, Q-16 and Q-18 hit; Q-24 missed).

Confusion pairs, with direction:

| gold | applied | count |
|---|---|---|
| other | info | 3 |
| request | complaint | 1 |

The route carrying most of the error is `other`: three of its four messages went to `info`. Two of them (Q-20 and Q-21, the legal-advice question and the property-tax dispute) are classifier errors. The third is Q-22, which the classifier got right and the policy floor moved to `info`. The fix for Q-20 and Q-21 is a definition: `other` as written ("advice the help desk cannot give", "a message for another department") overlaps with `info` ("a question about a service"), because a question is also a question about something. A bigger model is not the obvious fix. The one `request`→`complaint` miss is Q-24, an ambiguous case that the convention covers.

### 4. What routing cost

- monolith: 9,280 tokens over 24 queries
- router: 13,259 tokens over 24 queries (43 per cent more)
- the classifying call alone: 8,710 tokens, which is 65.7 per cent of the routed total

I predicted that share would be [fill in before you trust this: my guess was ___] before measuring it.

The classifier prompt carries all five definitions and the JSON schema on every call, while each specialist carries only its own short instruction. So the "cheap" call is the larger of the two here. The classifying call is also not cheap relative to the answer: the answering calls total 4,549 tokens.

### 5. What routing bought

Something a specialist can be forbidden to do that the monolith cannot be given: the `status` specialist can be forbidden to state a completion date, and the `other` specialist can be forbidden to follow any instruction inside the message. The monolith cannot carry the second rule, because the same prompt must also answer info questions and log requests, where following the user's text is the job.

Would I ship the router: not on this evidence. Evidence: on 24 queries the small model reaches 20/24, but I did not score the monolith on route accuracy (it answers in prose and has no route output), so I have no measured win on accuracy. The router costs 43 per cent more tokens and two calls instead of one. What it buys is a narrower prompt per route and the ability to audit a decision, and the guarantee argument above. That is real but unproven here. What would change my mind: a larger gold set where `other` is fixed by a rewritten definition; a measured monolith misbehaviour that routing removes (for example, following an injection); or a requirement that some route must never act, in which case the guarantee is worth the tokens.

### 6. Stretch variant

Variant assigned: [fill in]. The recording contains both variants, so these are the results I read from it.

**Model routing (recording).** I did not write down a prediction before reading the results, so I cannot claim one.

| | qwen3:4b-instruct | qwen2.5:7b |
|---|---|---|
| route accuracy after policy | 20/24 | 17/24 |
| excluding the ambiguous four | 17/20 | 16/20 |
| evidence verbatim | 24/24 | 19/24 |
| confidence range | 0.0 to 0.999, 5 distinct | 0.95 to 1.0, 2 distinct |
| resident memory | [from project/models.py] | [from project/models.py] |

The smaller model won. I think the larger model's confidence is simply uninformative: it is near 1.0 on everything, including its wrong answers (for example Q-16, a complaint labelled `request` at 1.0), so the confidence floor from 3a cannot be used on it. Its paraphrased evidence spans are what the evidence check caught, and each of those was sent to `info`.

**Voting (recording).** Three samples per query. At temperature 0.7 the votes disagreed on 1 query (Q-06); at 1.0 on none. I did not read the 1.5 samples, because one recorded response is not valid JSON. Q-06 is not one of the ambiguous four, so the disagreement did not flag the cases a human would call ambiguous. Voting cost three times the classifying tokens and changed almost nothing, so as a way to decide it is a poor buy on this set.

### The gold set

`artifacts/goldset.json` now holds 34 cases: 10 from week 2 and 24 added today (`RT-01` to `RT-24`), with the four ambiguous ones tagged `ambiguous`. Source loaded: [fill in: own / reference].

### Deferred

- Live run on my own machine (recording only so far).
- Wiring the week 2 extractor behind the `request` route.
- Rewriting the `other` definition and re-measuring the `other→info` pair.
- Resident-memory figures for the stretch, which I did not read from `project/models.py`.
