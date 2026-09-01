# 6. Choose Yours

Five good options. Here's how to pick the one that's actually right for **you**.

---

## Six questions

### 1. How much time do you really have?

Not how many days remain — how many days you'll genuinely spend building.

| Your answer | What it means |
|---|---|
| **6 days or fewer** | **#1 Reconciliation** or **#5 Chaperone**. Both have real versions in ~4 days |
| **8-10 days** | Anything except #2's full version |
| **More than 10 days** | #2 becomes viable — but read Q2 first |

**Reserve two days for the writeup and video regardless.** That's not padding. You cannot edit after
submitting, and a brilliant project with a rushed video is a rushed submission.

### 2. Have you built an agent loop before?

Meaning: an LLM that calls tools, decides, acts, and handles its own failures — with structured
outputs, not free text.

**If no, add two days to every estimate** and avoid #2. Its time simulation is a project inside a
project. #1 is the gentlest introduction: most of the work is ordinary code, and the LLM only
handles the hard leftovers.

### 3. What are you actually good at?

| You're strongest at | Pick |
|---|---|
| Data modelling, clean pipelines, careful logic | **#1 Reconciliation** |
| ML and evaluation design | **#2 Recovery** — the holdout is the interesting bit |
| Product thinking, workflows, writing | **#3 Invoices** |
| Systems thinking, spotting non-obvious structure | **#4 Freeze monitor** |
| Interfaces, LLM prompting, demos | **#5 Chaperone** |

### 4. Would you rather be *safe* or *memorable*?

There's a real trade-off.

**Safe:** #1. Best data, least crowded, and the panel conversation is about engineering.

**Memorable:** #4. The insight — *Razorpay legally cannot warn merchants, but merchants can watch
themselves* — is the kind of thing an interviewer repeats to a colleague. It's also the one most
likely to be misread as helping merchants dodge risk controls.

**#3 sits between:** almost nobody else is there, so you'll be noticed by scarcity rather than by
drama.

### 5. How do you handle being challenged?

The panel will push on your weakest number.

- **#1** — "How do you know a proposed match is correct?" A precision/coverage curve answers it.
- **#2** — "Isn't this what Butter and Revaly do?" You need Revaly's name ready and the headroom
  veto as your answer.
- **#3** — "Isn't this just harassment automation?" Guardrails must be visible in the demo.
- **#4** — "Are you helping merchants game our risk controls?" Needs a confident, prepared answer.
- **#5** — "Isn't this just a prompt?" You need the adversarial test set.

**If you'd rather be tested on engineering, pick #1. If you enjoy defending a position, #4 is more fun.**

### 6. Do you want to bet on our weakest assumption?

Our product list for Razorpay is a **blog post from 12 March 2026** — five months old, from a
product that explicitly plans to add third-party agents. Their live page wouldn't load for us.

**#3 and #4 depend on that being accurate.** If Razorpay shipped a refund agent or a freeze monitor
since March, both lose their central claim.

**#1, #2 and #5 don't care** — their positions rest on things that don't change.

---

## If you want to be told what to do

**Build #1, the Reconciliation Exception Resolver.**

It wins on data, on competition, on schedule, and on robustness. It's the only one of the five whose
claim to be different survives every uncertainty we identified. And the design idea — *propose with
confidence, never assert certainty* — comes from the real reason Razorpay hasn't built it, which is
the kind of thing that makes an interviewer sit up.

Then make these three choices:

1. **Report accuracy, not just coverage.** Publish the precision/coverage curve.
2. **End the demo on a failure.** Walk through one exception it couldn't resolve. Track 4's bar
   asks for exactly this, and almost nobody will do it.
3. **Say what a global tool can't do.** *"Ledge reconciles amounts across US rails. Nothing reasons
   about a line carrying MDR, GST on that MDR, a TDS deduction and a UTR — which is every Indian
   merchant's line."*

---

## Things that are true whichever you pick

**Name the incumbent before the judge does.** Every one of these has a company selling something
similar. Saying *"HighRadius does X; here's what they don't do"* reads as command of the space.
Being told it reads as homework not done.

**Never claim Razorpay's numbers as proof of anything.** Their published performance figures have no
methodology behind them. Cite them as priorities.

**Include the exceptions file.** Every bar asks for honest failure reporting. It's the cheapest way
to look serious and the thing most people will skip.

**Freeze the repo before recording.** Tag it. Make the video match the code exactly.

**Prepare five answers:**
- What's your accuracy at the threshold you shipped?
- Show me the trace for one specific case
- Why doesn't Razorpay's existing product solve this?
- What breaks at 10x volume?
- Which of your numbers do you trust least?

That last one is a trap, and honesty is the correct play. Everyone else will pretend they're all solid.

---

## A closing thought

The research says the field is large but mostly not clearing the bar. **One repo in eight** that used
the language of measurement actually had measurements behind it.

You don't need the cleverest idea. You need a real problem, an honest number, and a visible failure.

Three of the five here are things nobody in the applicant pool is building. Pick one, build it
properly, and be honest about its limits — that alone puts you in a small minority.

---

**Reference:** [Glossary →](07-glossary.md)
