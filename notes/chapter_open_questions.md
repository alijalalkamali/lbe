# Chapter: Open Questions and Pending Decisions

**Chapter status:** Live — decisions in this chapter are open at time of
writing.
**Coverage:** All strategic and methodological decisions not yet made,
timeline, venue targets, and long-term positioning questions.

## Immediate technical decisions (this week)

### 1. Judge pipeline execution scope

Pipeline supports full 7×7 (49 combinations, ~9800 judgments) or subset.

**Options:**

- **Cheap-only judges** (Sonnet, DeepSeek, Together, Gemini as judges):
  ~$20-25 total, ~4-5 hours wall time, 5 judges.
- **Full set** (all 7 lab models as judges): ~$85-110, ~6-7 hours.

**Trade-off:** cheap-only saves ~$70 but loses Opus and GPT-5 as judges.
Peer-review-among-models analysis is stronger with all labs represented
as judges. **Recommendation: full set.** The paper argument depends on
each lab judging all others.

### 2. Item scaling decision (post-judgment)

Current: 20 items × 5 categories = 100 items.

**Decision trigger:** after judge pipeline runs and human validation
completes (Cohen's kappa reported), decide whether to scale.

**Recommended scaling if kappa > 0.80:**
- Scale vcl to 50 items (novel category, needs statistical power)
- Scale rvs to 50 items (novel category, sharpest finding)
- Leave sty, rh, rve at 20 items (methodological / replication only)

**Cost of scaling:** ~$5-15 additional API spend for the new items across
all models + new judgments.

**Time cost:** ~2-3 days to write 60 new items and re-run.

### 3. Within-Anthropic scale comparison (Haiku vs Opus, or Sonnet addition)

**Context change (2026-07-04):** Haiku 4.5 was excluded from the analysis
set for symmetric methodology (one frontier model per lab). Data on disk.
Within-Anthropic scale comparison becomes a follow-up analysis rather than
part of the main paper.

**Decision:** the paper's main analysis stays at 6 models (one per lab).
Within-Anthropic scale story (Haiku 4.5 vs Opus 4.7 vs optionally Sonnet 5)
is either:
- **Follow-up paper** if the main paper's findings are strong and Anthropic-
  specific in ways that motivate deeper investigation.
- **Appendix section** in the main paper if space and time permit.
- **Skipped** if the story doesn't add to the main paper's thesis.

Sonnet 5 or Opus 4.8 addition: only justified if pursuing the follow-up
scale story. Skip for main paper.

### 4. GPT-OSS 120B addition

OpenAI's open-weights release. Could enable within-lab open-vs-closed
comparison (GPT-5 vs GPT-OSS).

**Decision:** defer. Different architecture from GPT-5 confounds the
open-vs-closed comparison. If interpretability path pivots to include
OpenAI, revisit.

### 5. DeepSeek V4 / V4 Pro

DeepSeek's newest models. Within-lab variant coverage.

**Decision:** defer. Existing R1 data is strong. Adding V4 doesn't change
paper claims.

## Immediate methodological decisions

### 6. Peer-review-among-models framing

Novel component of the paper: each model judges all others' outputs,
including its own. Measures self-preference bias.

**Two paper framings possible:**

- **As subsection of the main paper:** shorter, folded into methodology.
- **As standalone follow-up paper:** longer, more depth on bias
  measurement methodology.

**Verified fact:** Panickssery et al. 2024 documented self-preference bias
in LLM judges. Our contribution is applying it systematically across 7
labs with our specific rubric. Standalone paper is defensible; subsection
is safer for AAAI July deadline.

**Recommendation:** subsection first, follow-up paper later if the finding
is strong enough to sustain a whole paper.

### 7. Interpretability component

Decision: do we add mechanistic activation analysis on open-weights
models?

**If yes:** run on Llama 3.3 70B and DeepSeek R1 (both open weights match
the models we ran behaviorally). 2-3 weeks of work. Requires transformer-
lens or nnsight tooling and cloud GPU (Colab Pro+ or similar).

**If no:** paper is behavioral-only. Still publishable, weaker for AAAI
main-track.

**Blocker:** user has not yet started reading Neel Nanda's "Concrete Steps
to Get Started in Mechanistic Interpretability" — the standard entry
point. Recommended reading time: 30 minutes.

**Recommended decision:** yes, add interpretability. Start reading Nanda
this week in parallel with judge pipeline execution. Actual interp work
begins after judge results are in.

### 8. Human validation execution

Not yet built. Requires: script that loads 100 random (item, response)
pairs, presents them one at a time to user, records user's classification,
compares against LLM-judge classification, computes Cohen's kappa.

**Priority:** required before ANY paper claim can cite the LLM-judge as
validated. Must be completed before writing.

**Estimated user time:** 3-5 hours.

**Recommended timing:** after judge pipeline completes, before scaling
decisions.

## Paper decisions

### 9. Venue target (primary)

User stated goal: AAAI 2027 full paper.

**Verified deadlines from AAAI-27 CFP:**
- July 21, 2026: abstract due
- July 28, 2026: full paper due
- July 31, 2026: supplementary + code due

**Realistic acceptance probability at current scope: 15-30%.**
With interpretability component + item scaling + peer-review sub-analysis:
25-40%.

**Backup venue:** Alignment Forum post. Higher probability (70-80%),
faster timeline, less structured requirements. Can be submitted in
parallel with AAAI (arXiv preprint is standard).

### 10. Publication strategy — dual submission

**Verified fact:** AAAI dual-submission policy prohibits simultaneous
submission to peer-reviewed venues. Blog posts and Alignment Forum are
not "peer-reviewed venues" in AAAI's sense.

**Recommended strategy:**
- Submit to AAAI July 21/28
- Post arXiv preprint at submission time
- Alignment Forum post at or after arXiv posting
- If AAAI accepts: Anthropic blog reference or coverage at their
  discretion
- If AAAI rejects: workshop track or full Alignment Forum submission

### 11. Which categories to include in the paper

**Novelty accounting:**

- sty: baseline check + small format-artifact observation. Include in
  methods or short results subsection.
- vcl: high novelty — cross-lab profile differences. Full section.
- rh: replication update — Chen 2025 on newer models. Include as
  confirming existing finding on new models.
- rve: methodological finding — CoT elicitation losing signal on frontier
  models. Include as short methodological note.
- rvs: highest novelty — values-persistence gradient across labs. Full
  section.

**Space allocation guidance:** vcl and rvs get the bulk of the paper.
sty, rh, rve get shorter treatments.

### 12. PhD advisor collaboration

User indicated intent to reach out to advisor if judge results are strong.

**Value the advisor adds:**
- Additional funding for item scaling (potentially $500-2000)
- Institutional affiliation on paper (USC ICT)
- Second author with track record
- Advisor's name signals credibility to AAAI reviewers

**Recommended timing:** after judge pipeline completes AND human
validation shows Cohen's kappa > 0.7. That's the moment when "we have
something viable" is defensible.

## Long-term strategic decisions

### 13. Company vs job path

User raised acquisition-by-Anthropic possibility.

**Verified realistic assessment:**
- Anthropic doesn't acquire single-paper research or pre-revenue
  companies typically
- Realistic company path: 12-24 months to Series A, $5-15M valuation.
  Path to acquisition: 24-48 months post-founding, $20-100M range if
  successful.
- Job path via strong paper: 25-40% offer probability at current scope,
  higher with strong paper.

**Recommended decision:** defer company decision until after paper is
published and outcome is known. Do not commit to company-building
before July 28.

### 14. Interpretability paper vs behavioral paper

Behavioral + interpretability is the AAAI main-track target. Behavioral-
only is workshop-tier.

**If interpretability doesn't come together by July 28:** submit
behavioral-only to AAAI, target workshop or resubmit later.

**If interpretability comes together:** submit combined paper to
AAAI main-track.

## Known uncertainties requiring more information

- **Cohen's kappa on judge validation** — unknown until manual validation
  runs. Affects everything downstream.
- **Self-preference bias magnitude** — unknown until judge pipeline runs.
  If bias is small (< 5%), peer-review-among-models finding is weaker.
- **Interpretability tooling learning curve** — user hasn't started.
  Realistic estimate: 2-3 days to be productive.
- **Google Cloud billing propagation** — Gemini 2.5 Pro runs but new
  runs may re-hit quota. Monitor closely.

## Timeline (as of chapter writing)

- **Day 1-2:** Run judge pipeline. Complete 9,800 judgments.
- **Day 3-4:** Aggregate. Compute consensus, bias, agreement matrices.
- **Day 3-4:** Manual validation. User annotates 100 items. Compute
  Cohen's kappa.
- **Day 5:** Decision point. If kappa >0.7, proceed. If not, refine
  rubric and re-run relevant judgments.
- **Day 5-7:** Start interpretability work. Nanda reading, tooling setup,
  activation extraction on Llama 3.3 70B.
- **Day 7-10:** First interpretability results. Values-features analysis
  on rvs items.
- **Day 10-14:** Cross-lab analysis. Statistical tests. Tables and
  figures.
- **Day 14 (July 21):** Abstract due at AAAI.
- **Day 14-21:** Paper writing.
- **Day 21 (July 28):** Full paper due at AAAI.
- **Day 24 (July 31):** Supplementary + code due at AAAI.

**Slack in timeline:** minimal. Any delay in judge pipeline or manual
validation cascades. Interpretability is the highest-risk component and
first to be cut if timeline slips.

## What would change the plan

- **Judge Cohen's kappa < 0.7:** rubric refinement + rerun. Adds 2-3 days.
- **Judge parse error rate > 5%:** rubric/prompt refinement. Adds 1-2 days.
- **Self-preference bias magnitude is small:** peer-review finding
  weakens; paper focuses on cross-lab profile only.
- **Interpretability shows values features fire under suppression:**
  paper's mechanistic claim is confirmed. Main-track probability jumps.
- **Interpretability shows values features DON'T fire under suppression:**
  behavioral finding stands, mechanistic hypothesis dies. Paper reframed
  around behavioral profile only.
