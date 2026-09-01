# 3. How We Investigated — and What We Got Wrong

You should know how this research was done, because that tells you which parts to lean on and which
to treat carefully.

---

## The method

Fourteen stages, each one ending in a checkpoint that asked: *what would prove this conclusion
wrong?*

Three large automated research runs went out to read the web — roughly **320 separate research
agents**, reading Razorpay's site, RBI and NPCI documents, news, developer docs, GitHub and
merchant review sites.

The important design choice: findings weren't just collected, they were **attacked**. Each factual
claim was handed to three independent checkers whose job was to *refute* it. A claim needed to
survive to be kept.

**In the second run, 19 of 25 tested claims were killed.**

That ratio is the useful signal. The process was much better at destroying bad claims than
confirming good ones — which is exactly what you want when the alternative is walking into a panel
with a confident wrong number.

---

## Four things we believed and had to reverse

### 1. We invented a regulation that doesn't exist

We'd written that Razorpay pays merchants in 2 days while RBI requires 1 day — a compliance gap.
It sounded solid. We even had Razorpay's own blog saying the T+1 rule existed.

So a checker pulled the actual RBI Master Direction, all **44,787 characters of it**, and searched
the full text.

**Zero matches** for "T+1", "one working day", or even "working day". The rule says settlement
timing is whatever the contract says, as long as it's fair and clearly stated. The older rule that
did contain timelines had been formally repealed.

There was no gap. We'd built a finding on a rule that didn't exist.

**And the twist:** Razorpay's own blog states the T+1 requirement, citing penalties. Their marketing
content is wrong about the regulation it names. Which is a useful thing to know about how much
weight their published claims can carry.

### 2. We trusted their numbers too easily

Razorpay's Vulcan launch claims an 8-10% improvement in payment success, 8x more fraud caught, 40%
more shoppers seeing their preferred UPI app.

We'd been quoting these as evidence. Then a journalist's write-up surfaced: they had asked Razorpay
directly for the baseline, the sample size and the time period behind those numbers.

**Razorpay didn't provide any of it.** The article states plainly that these are the company's own
beta results with no published methodology.

We now label every Razorpay performance number as *marketing*. It's good evidence of **what they
care about**. It is not evidence that anything is **solved**.

There's a smaller tell too: they claimed "up to 10% success rate increase" for a routing product in
January 2024, and "8-10%" for Vulcan in August 2026. Either the gain is being counted twice, or one
claim is recycled.

### 3. We called two ideas novel that companies already sell

We'd been recommending a recovery agent whose clever bit was timing retries using decline codes.

Then we searched properly. A company called **Revaly** already ships a retry engine that
*"analyses decline codes and issuer behaviour to time retries intelligently."* Our differentiator,
sold commercially, today.

Same story for promise-to-pay tracking. **HighRadius runs 15 AI collections agents and already
auto-creates promise-to-pay entries.**

Neither idea died — but their *novelty claim* did, and we rewrote both.

### 4. Our own filters hid data from us

Midway through, we asked ourselves whether we'd actually read everything. We checked.

**Sixteen of 120 research findings had never been displayed** — a keyword filter had silently
skipped them. Six mattered. One was a quote from Razorpay's own MD that we'd declared didn't exist.

We went back and read all of them.

---

## What survived

The findings we're most confident in are the ones anchored to something physical — a published
schema, a documented threshold, a government portal — rather than to someone's description:

- Razorpay's settlement report has 11 named fields, published
- Razorpay's error codes and their causes are published, with a downloadable table of recommended actions
- Chargebacks above 1% trigger a freeze — Razorpay's own published number
- Merchants spend 20-40 hours a month reconciling — Razorpay's own figure
- SBI's ~70% mandate failure rate — reported by press, still current a year on
- ₹20,979 crore of unresolved MSME payment claims — a government portal
- Disputes **cannot** be created in Razorpay's test environment — checked in their docs directly

That last one killed several otherwise-attractive ideas, which is why it's worth trusting.

---

## What we still don't know

**The big one: Razorpay's current product list.**

Their Agent Studio page is built so the content loads *after* the page does, which means our tools
got an empty page every time — across three separate research runs.

So the seven-agent list we're working from comes from a **blog post dated 12 March 2026**. Five
months old. And that post says third-party developers will be able to publish agents to it.

**If that list has grown, two of our five recommendations lose their main claim.** We flag this
everywhere it matters, and it is the cheapest remaining thing anyone could check.

Also still unknown: whether refunds actually fail often (no rate exists anywhere), what fraction of
settlement lines fail to match, and how many failed payments would have recovered on their own
without help.

---

## What this means for you

Three practical things.

**Don't quote Razorpay's performance numbers as proof.** Cite them as evidence of priorities.

**Prefer facts anchored to published artefacts** — a schema, a threshold, a portal. They survive
scrutiny; descriptions don't.

**Being able to say "here's what I'm unsure about" is a strength in the panel.** The strongest
answer to *"which number do you trust least?"* is a real one. That question rewards honesty and
punishes rehearsal.

---

**Next:** [How 20 problems became 5 →](04-the-funnel.md)
