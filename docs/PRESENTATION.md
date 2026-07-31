# SentinelX — 5-Minute Presentation Script

A structured run-sheet for pitching SentinelX. Total presentation runtime is ~5 minutes.

Core theme: **Behavioural. Correlated. Explainable.**

---

## 1. Problem — 30 seconds

**Slide title:** The Problem: Attackers Don't Need to Be Known

**Bullets:**
- Signature and IoC matching only catches threats someone has already seen and catalogued
- Zero-days and novel techniques have no signature to match — by definition
- "Living-off-the-land" attacks use legitimate admin tools and valid credentials — nothing to
  flag
- Insider misuse uses real credentials doing real actions — there is no IoC at all
- Result: defenders are structurally *at least one incident behind* the attacker

**Say:**
> "Every major breach you've read about got past antivirus and firewall rules. Not because those
> tools are broken — because they're built to catch what's already known. A zero-day has no
> signature. An attacker using stolen but valid credentials and built-in admin tools leaves
> nothing on a blocklist to trip. If detection depends only on knowing the attack in advance,
> you're always defending against yesterday's threat."

**On screen:** Title slide. A simple visual: a known-bad signature list with a clean checkmark
next to it, and a "living off the land" / "zero-day" / "insider" trio next to a blank, unmatched
signature list — visually showing the gap.

---

## 2. Why existing approaches are insufficient — 30 seconds

**Slide title:** Why Rules and Blocklists Fall Short

**Bullets:**
- Static rules/thresholds are global — they don't know a firewall's "normal" traffic volume is a
  workstation's extreme outlier
- Single-metric alerting (e.g. "CPU > 90%") floods analysts with false positives and gets tuned
  into silence
- No IoC exists for behaviour that is *technically legitimate* but *contextually wrong*
- Alert fatigue is a well-documented reason real incidents get missed in production SOCs

**Say:**
> "Even rule-based anomaly tools usually apply one global threshold to every device — which means
> either it's too sensitive for quiet workstations, or too blind for busy infrastructure like a
> firewall or router. And a single noisy metric triggering an alert is exactly how analysts end up
> ignoring their own alerting. You need detection that understands *this specific device's* normal
> — and that doesn't cry wolf on one twitchy metric."

**On screen:** Two device icons — a workstation and a firewall — with the *same* raw traffic
number under each, one flagged red (wrong for the workstation) and one green (normal for the
firewall), to make the "context matters" point visually immediate.

---

## 3. SentinelX solution — 45 seconds

**Slide title:** SentinelX: Behavioural · Correlated · Explainable

**Bullets:**
- **IoC-independent behavioural detection** — an Isolation Forest learns each host's *own*
  baseline from its own history, then scores new activity against that baseline, not a global
  rule
- **Multi-signal correlation** — risk only escalates once multiple *independent* signal families
  (traffic, DNS, process creation, authentication, destinations, resource use) move together
- **Explainable threat reasoning** — every score traces to concrete evidence: observed value,
  learned baseline, deviation, and each signal's share of the finding
- Three separate, inspectable services — detection, correlation, explanation — not one opaque
  model producing a mystery number

**Say:**
> "SentinelX is built around three ideas, and we want you to remember all three. First:
> behavioural, IoC-independent detection — we learn what's normal *for that specific host* and
> flag deviation from its own history. Second: multi-signal correlation — one unusual metric is
> noise; several independent signals moving together is a real pattern, and that's the only thing
> that escalates risk. Third: explainable reasoning — every number we show you traces back to real
> telemetry evidence. We never output a malware name or a CVE we didn't derive — if the evidence
> isn't there, we don't invent it."

**On screen:** The three-pillar diagram (Behavioural → Correlated → Explainable) as a simple
left-to-right pipeline, ending in "Incident + Evidence." This is the mental model the rest of the
talk hangs on.

---

## 4. Live demo — 90 seconds

**Slide title:** Live Demo: Detecting a Simulated Compromise

**Bullets:**
- Start state: all 5 simulated endpoints — 2 workstations, a firewall, a router, and the demo
  target — reading **Normal**
- One click triggers a controlled, fully reversible compromise simulation (no real exploitation
  of anything, ever)
- Watch the real, live progression: telemetry anomaly → **BEHAVIOURAL ANOMALY DETECTED** →
  **MULTIPLE SIGNALS CORRELATED** → **POSSIBLE SYSTEM COMPROMISE** → **HIGH RISK INCIDENT**
- Open the investigation view: real evidence, real baseline comparison chart, real recommended
  actions
- One click resets everything back to Normal — repeatable on demand

**Say (while doing it):**
> "This is the live system, not slides. Right now every endpoint reads Normal. Watch what happens
> when I click Simulate Compromise on this workstation." *(click; narrate each banner as it
> appears)* "Anomalous telemetry — the model's already scoring it. Behavioural anomaly detected.
> Now multiple independent signals are correlating — that's the noise filter working. Possible
> system compromise... and now a high-risk incident has actually been opened, automatically, with
> deduplication so it doesn't spam duplicate tickets." *(click into the investigation panel)*
> "Here's the evidence behind that number — outbound traffic, DNS volume, process creation, all
> compared against this host's own baseline, in real standard deviations, plus concrete
> recommended actions. Nothing here is fabricated." *(click Reset)* "And it's back to Normal —
> we can run this again right now if you want to see it twice."

**On screen:** The running application, live — Demo Mode view, then the Investigation Panel. Not
a recording; this section only works if it's actually running.

---

## 5. Technical architecture — 45 seconds

**Slide title:** Under the Hood

**Bullets:**
- FastAPI + SQLite backend, React/TypeScript frontend — one deployable stack, no external
  services required
- Per-host z-score normalization feeding a single pooled Isolation Forest (scikit-learn)
- Rule-based correlation layer fuses the ML score with signal breadth and severity into one
  compromise probability
- Deterministic, template-based explanation engine — zero LLM dependency, zero hallucination risk
- 53 automated backend tests plus a documented, verified end-to-end test pass before every
  milestone

**Say:**
> "Architecturally it's deliberately simple: one FastAPI backend, one SQLite database, one React
> frontend. Telemetry gets normalized per host into z-scores, scored by a single Isolation Forest,
> fused by a transparent, documented correlation rule — not another black-box model — and
> explained by a deterministic template engine, so there's no LLM in the loop and nothing it can
> hallucinate. Every one of these pieces is independently tested — 53 automated tests on the
> backend alone."

**On screen:** The architecture diagram from `docs/ARCHITECTURE.md` — UI → API → telemetry
engine / anomaly detection / correlation / explanation / incident management → SQLite.

---

## 6. Innovation — 30 seconds

**Slide title:** What's Actually Different Here

**Bullets:**
- Detection reasons about *behaviour*, not blocklists — structurally catches what IoC tools
  cannot, by design, not by luck
- The correlation gate is a concrete, testable answer to alert fatigue: noise on one metric never
  escalates alone
- Explainability is enforced in code, not a UI afterthought — there is no code path that can
  emit an attribution the evidence doesn't support
- Every score, in every screen, is traceable back to a real telemetry number — full transparency
  by construction

**Say:**
> "The innovation isn't 'we added AI.' It's that the system is built so alert fatigue and false
> attribution are structurally hard to produce. Correlation isn't a display filter — it's gating
> the actual score. Explainability isn't a nice paragraph we generate afterward — the code has no
> way to name a malware family or a CVE it didn't derive from real evidence. That's enforced, and
> it's tested."

**On screen:** A short callout quote or code-adjacent snippet showing the correlation gate
condition and the explanation disclaimer text, to visually back the "enforced, not asserted"
claim.

---

## 7. Impact and scalability — 30 seconds

**Slide title:** Impact & Scalability

**Bullets:**
- Applies anywhere there's telemetry to learn from — enterprise endpoints, network
  infrastructure, and extensible to IoT/OT
- Designed to reduce analyst alert fatigue by requiring correlated, explained evidence before
  anything reaches a human
- Detection, correlation, explanation, and incident management are separate services — each can
  scale or be swapped independently
- Clear, honest path from this prototype to a production pipeline (next section)

**Say:**
> "This approach isn't tied to five simulated hosts — the same per-host baselining and
> correlation logic applies to any fleet with telemetry, from enterprise endpoints to network
> gear to IoT. And because detection, correlation, and explanation are separate services instead
> of one monolith, each layer can scale, or be replaced with a stronger model, independently
> without touching the rest."

**On screen:** A simple "prototype → production" scaling diagram: same pipeline, larger fleet,
real ingestion sources feeding in instead of the synthetic generator.

---

## 8. Future scope — 30 seconds

**Slide title:** Roadmap to Production

**Bullets:**
- Train and formally evaluate against public cybersecurity datasets (e.g. CICIDS2017/2018,
  UNSW-NB15) for a genuine, defensible accuracy benchmark
- Richer endpoint telemetry — process trees, EDR-grade signals, network flow/packet data
- Temporal and sequence models to catch attack *chains* over time, not just single-sample
  deviation
- Online and federated learning, so baselines adapt continuously without centralizing sensitive
  data across organizations
- Direct SIEM/EDR/SOAR integration so incidents and evidence reach the tools a real SOC already
  uses

**Say:**
> "We're intentionally honest that this is a prototype on synthetic data. The roadmap is
> concrete: train and evaluate on public labelled datasets so we can report a real accuracy
> number instead of none; ingest richer real telemetry; add temporal models for multi-step attack
> chains; move to online and federated learning so the baseline keeps improving without
> centralizing anyone's raw data; and integrate directly with the SIEM and EDR tools SOCs already
> run. Thank you — happy to take questions."

**On screen:** Roadmap slide, five items above, ending on a thank-you / contact slide.

---

## Timing summary

| # | Section | Seconds | Cumulative |
|---|---|---|---|
| 1 | Problem | 30 | 0:30 |
| 2 | Why existing approaches fall short | 30 | 1:00 |
| 3 | SentinelX solution | 45 | 1:45 |
| 4 | Live demo | 90 | 3:15 |
| 5 | Technical architecture | 45 | 4:00 |
| 6 | Innovation | 30 | 4:30 |
| 7 | Impact & scalability | 30 | 5:00 |
| 8 | Future scope | 30 | 5:30 |

If your slot is a strict 5:00, cut the demo's reset-and-repeat beat (last ~15s of section 4) and
tighten section 5's opening sentence — those are the two lowest-cost trims.

## Before you present — checklist

- [ ] Backend running (`uvicorn app.main:app --port 8000`) and reachable
- [ ] Frontend running (`npm run dev`) and reachable
- [ ] Environment reset to Normal *before* judges walk up (`POST /api/simulation/reset`, then
      resolve any leftover open incident — see `docs/ARCHITECTURE.md` §14 on why reset alone
      doesn't close incidents)
- [ ] Do a full dry run of the Simulate → Investigate → Reset sequence within the last hour —
      confirm it completes in well under 90 seconds on the actual demo machine/network

## Anticipated Q&A

**"What's your accuracy?"** — We haven't run a formal evaluation against a labelled dataset, so we
don't have a number to give you, and we'd rather say that than make one up. That's the first item
in our roadmap: benchmark against public datasets like CICIDS2017/2018 or UNSW-NB15.

**"Is this real network data?"** — No — synthetic, clearly labelled telemetry, generated with
realistic correlated behaviour (not independent random noise) so the detection pipeline is
exercised honestly. Every API response says so explicitly.

**"Why Isolation Forest and not [X]?"** — It's an established, well-understood unsupervised
method that doesn't require labelled attack data to train, which matches a real deployment where
labelled compromises are rare. We've documented its actual limitation too: with limited
per-host samples, it's weaker on anomalies confined to a single feature — which is exactly why the
correlation layer exists as an independent second check.

**"Does it use an LLM?"** — No, by design. Explanations are generated by a deterministic template
engine grounded in the same computed evidence shown in the evidence panel, so there's no
hallucination risk in the explanation layer.
