# 5-minute demo script — read-aloud version

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

> Everything in a quote block is written to be **spoken**. Short sentences, plain words,
> natural pauses. Read it at normal talking pace and it lands at five minutes.
> Anything in *italics* is a stage direction. Don't read it out.

```
0:00 – 0:20   Intro
0:20 – 1:00   GitHub: the README and the architecture
1:00 – 1:20   Decision trace
1:20 – 1:55   Experiment, including the result that went against us
1:55 – 2:15   Safety and tests
2:15 – 5:00   The live run
```

Each section has a **⚠ What broke here** box. Those are optional, and the timings above
assume you skip them. Use one or two if you have room, or save them for questions.

If you only tell one, tell the payment one. It's the best story in the project.

---

## Before you start (2 minutes, off camera)

**Terminal 1 — the engine.** Dashboard, webhook listener and the follow-up worker, all on
one port:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; $env:PORT="8555"; .venv\Scripts\python.exe -m app.server
```

**Terminal 2 — the tunnel**, so Razorpay can reach this laptop. Leave it open for the whole
demo; closing it kills the webhook path:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; .\scripts\start_tunnel.ps1
```

**Terminal 3 — spare**, for the health check below and anything you need mid-demo:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"
```

- [ ] `curl.exe -s localhost:8555/health` shows `followup_hour_seconds: 0.05` and `worker_interval_seconds: 2`
      — if it says `3600` and `60`, the server started before the demo settings, and your
      escalation will take eight days on stage
- [ ] Run the Experiment benchmark once now, so results are already on screen
- [ ] Reset the board → tick confirm → **Clear N unpaid**
- [ ] Tabs open: GitHub README, dashboard, your inbox. Phone where you can see it.
- [ ] `demo_customers.csv` ready to drag in

> **Dispatch is live.** Every upload sends a real email. Only use a CSV with your own address.

---

## 0:00 – 0:20 · Intro

> "Hi, I'm Sushanth. This is the Unified Recovery Engine, built for Track 3.
>
> Every business loses money it has already earned. A payment fails. Someone abandons a
> checkout. A subscription doesn't renew. An invoice just sits there.
>
> Most systems chase all of that the same way. Retry twice, send an email, then call. The
> rule fires whether it helps or not, and nobody can tell you which rupee it brought back.
>
> I built something that decides, case by case, whether contacting someone is actually worth
> it. And when it isn't, it doesn't."

---

## 0:20 – 1:00 · The README and the architecture

*Open the GitHub README. Scroll to the flow diagram.*

> "One engine handles all four streams. Failed payments, abandoned checkouts, failed
> renewals, overdue invoices.
>
> The whole thing is one loop." *(trace it with your cursor)*
>
> "An event comes in, either from a webhook or from a merchant's CSV. Stage zero checks
> there's real money to recover. Stage one works out why it's unpaid. Then we list the
> actions that are even legal for this kind of case. The safety filter throws out anything
> that isn't allowed right now. Whatever survives gets ranked by expected value, and the best
> one runs.
>
> Then it schedules its own next look and goes quiet. A worker wakes it up later, it re-reads
> the case, and decides again. That keeps going until the money arrives, or a stopping rule
> ends it."

*Scroll to the escalation ladder diagram.*

> "Contact gets louder one step at a time. Email, then SMS, then WhatsApp, then a voice call,
> then a human. And it can only ever go up one rung from the last contact we know actually
> arrived. Never two, no matter what the model says."

*Stay on the README.*

> "Four outside services actually get called here.
>
> Razorpay, for creating and cancelling payment links, and for the signed webhooks coming
> back. Gmail, for the email that reaches the customer. Twilio, for SMS, WhatsApp and voice
> calls. And Meta's WhatsApp API as a second provider, because Twilio's WhatsApp can't be
> tested on a free account.
>
> Everything else is deliberately boring. SQLite. A small Starlette server. Streamlit for
> this dashboard. CatBoost for the scoring. And there's no language model anywhere in the
> decision path. If you're going to chase someone for money, you should be able to explain
> exactly why, from a number."

---

## 1:00 – 1:20 · Decision trace

*Dashboard → Decision trace.*

> "This screen answers one question. Why did it do that?
>
> One case, from the raw event all the way to the action it took. Eight stages, and every
> number here is read back from the decision that actually ran. Nothing is scripted."

*Point at the amber steps.*

> "You can see where things got removed. Three actions were rejected before any scoring
> happened at all. The engine isn't allowed to open a relationship with a phone call."

---

## 1:20 – 1:55 · The experiment

*Experiment tab. Results already on screen.*

> "Five versions of the engine, run over the same batch of cases. Each one isolates a single
> capability, so you can see what each part is actually worth.
>
> Now, the honest part. I wrote a prediction down before running this. I said the machine
> learning model would beat the simple rule-based version.
>
> It didn't." *(point at the row)* "That comparison came back inconclusive. The p-value is
> nought point nine six.
>
> And the reason is more interesting than a win would have been. The safety rules narrow the
> choices down so far that the scoring barely matters. The two scorers disagree on four
> decisions out of a thousand.
>
> The one result that is statistically significant is the engine against doing nothing at
> all. That's where the value actually is.
>
> Every comparison is on this screen, including the four that came back inconclusive. Showing
> only the flattering one is how an honest experiment turns into a marketing chart."

**⚠ What broke here** *(15 seconds)*

> "The model looked like it was losing, and my first instinct was to tune it until it won.
> Instead I went looking for a reason.
>
> There was a bug in how we timestamped contacts. It used the wall clock instead of the
> decision time, and that quietly killed the escalation ladder in every single test run. The
> model was being graded in a world that didn't exist.
>
> I fixed it, re-ran everything, and the prediction was still wrong. So that's what I'm
> reporting."

---

## 1:55 – 2:15 · Safety and tests

*Safety tab.*

> "These checks ran when this page loaded. That's what the count says. A tick here means it
> actually executed, just now.
>
> Underneath, six more are enforced in the architecture and covered by tests. They're listed
> deliberately without ticks, because this page didn't run them. A green tick that isn't
> backed by a real check is exactly what this screen exists to avoid.
>
> Five hundred and twenty three tests. Twenty four architecture decision records. And the
> whole evaluation reproduces exactly on a fresh clone. I cloned it cold this morning and got
> an identical result."

**⚠ What broke here**

> "Two things these tests didn't catch until I went looking.
>
> The contact ledger was recording the simulator's outcome instead of what actually happened.
> A row would say a contact succeeded nine milliseconds after it was created. The email hadn't
> even been sent yet. Dry runs were being recorded as real contacts.
>
> And the test suite was reading my own environment file. So when I turned real sending on for
> a demo, the tests started running with live credentials loaded. One test caught itself.
> Nothing was protecting the rest."

---

## 2:15 – 3:00 · Upload a CSV, and a real email goes out

*Live test tab. Drag in `demo_customers.csv`.*

> "This is a merchant's list of overdue invoices. Six columns.
>
> Notice there's no column for why it's unpaid. A merchant knows what's owed and by whom.
> They don't know why. If I asked them to type in a reason, then my diagnosis would just be
> reading their answer back to them. So the engine works it out itself.
>
> One row in here is broken on purpose. It gets rejected with a reason, not quietly skipped.
> A dropped row is money the merchant thinks is being chased, and nothing is chasing it."

*Switch to your inbox.*

> "That email is real. It went out over SMTP a few seconds ago. The name, the amount and the
> due date all come straight from the row I just uploaded."

**⚠ What broke here**

> "A customer with a valid phone number and no email address was never contacted at all. Not
> once, ever.
>
> Invoices start at the email rung. Nothing checked whether we actually had an email address.
> The send got skipped, so the contact was never confirmed, so the engine was never allowed to
> move up. It offered the same impossible action forever, while the money sat there.
>
> Now a channel we can't reach gets rejected straight away, and it starts at the first rung
> that can actually reach the person."

---

## 3:00 – 4:00 · It escalates on its own

*Back to the board. Wait about ten seconds. Refresh. Then again.*

> "Nothing out here is triggering that. The engine scheduled its own next look, and a
> background worker woke it up.
>
> The timing isn't configured anywhere. It's worked out from the diagnosis, the channel, and
> how many times we've already tried. A gateway glitch gets retried in about four hours. An
> overdue invoice waits about eight days, because emailing a finance team every day just gets
> you blocked.
>
> I've sped the clock up for this demo. One hour becomes a twentieth of a second. Only the
> unit changes. All the ratios stay exactly the same."

*Point at the rungs lighting up.*

> "A lit rung means that message was confirmed sent. If a message fails, it earns nothing. So
> a broken channel can never quietly walk its way up to a phone call."

*(If the voice rung fires, your phone rings. Let it ring.)*

**⚠ What broke here**

> "Razorpay's payment links have a notify setting, and I had it switched on. So Razorpay was
> sending its own SMS and its own email, on top of mine. Three messages for one decision. None
> of them went through my dispatcher, so none of them were in the ledger. The whole escalation
> ladder was being bypassed by messages my own engine couldn't see.
>
> Twilio had a different problem. On a free account it refuses to take the call script inline.
> So the engine now serves its own, from a signed endpoint. It has to be signed, because
> Twilio fetches it without any credentials, and otherwise anyone who guessed a case ID could
> have a customer's name and their debt read out loud."

---

## 4:00 – 4:40 · Payment always wins

*Point at the green PAID row. Then click Open.*

> "That's a real payment. Twenty five thousand rupees, in test mode. Razorpay's webhook came
> into this machine, we verified the signature, and the case closed itself. Marked paid, the
> open link cancelled, and every scheduled follow-up stopped.
>
> The case gets re-read at the moment we send, not when the action was queued. So if money
> arrives, it cancels everything already in flight. Someone who has paid can't be chased by a
> message that was lined up five minutes ago."

*Point at the timeline.*

> "Case created. Agent decided. Link created. Message sent. Follow-up scheduled. Payment
> received. Case closed."

**⚠ What broke here** *(20 seconds — the best story you have)*

> "The first time I actually paid this link, the case didn't close.
>
> The webhook arrived. The signature checked out. It was recorded. And the case just sat
> there, still open, with a follow-up still scheduled. The engine was about to chase me for
> money I had just paid it.
>
> That got past three hundred and ninety five passing tests.
>
> Razorpay sent a payment event, not a payment-link event. And a payment event hides our
> reference somewhere different. We were only looking in one place.
>
> There was a second bug underneath it. The code that cancels the follow-up was matching on
> the wrong column, so it updated zero rows, reported success, and nothing checked.
>
> Both fixed. And the test I wrote for it uses the actual data Razorpay sent me, not a made-up
> example. A made-up example would have had the same wrong assumption baked into it."

---

## 4:40 – 5:00 · Close

> "The one idea underneath all of this. Doing nothing scores exactly zero. So when no action
> is worth taking, the engine contacts nobody. That's deliberate. It's the difference between
> a recovery system and a harassment system.
>
> The numbers in the experiment come from a simulation, and I've labelled them that way
> everywhere. What's real is the loop. A real payment link, a real email, a real webhook, and
> a real case closing itself.
>
> Thank you."

---

## If something goes wrong

| What happens | What to say, then keep moving |
|---|---|
| Email doesn't arrive | "SMTP is a live dependency. The dispatch log shows it was sent, with the provider's ID." Then show the timeline. |
| No escalation shows up | Check `/health`. If it says 3600, say "this is running at real-world timing" and show the scheduled next review instead. |
| WhatsApp shows FAILED | **Use it.** "That's Twilio actually refusing. It's a paid feature. The engine records the failure and doesn't move up the ladder, because a rung only lights up when a message was confirmed sent." |
| SMS wording looks odd | "Free Twilio accounts can only send fixed templates, so the payment link isn't in there. And the record says exactly that, instead of claiming it worked." |
| Payment doesn't close a case | Run `scripts/send_test_webhook.py` and show the receiving side works on its own. |
| "Is that your model deciding?" on the trace tab | "No, and the screen says so. That one uses base rates. The live path uses the trained model. I checked all seven scenarios and it picks the identical action every time, because the safety rules had already narrowed it down." |

---

## Three lines worth landing

1. **"Doing nothing scores exactly zero, so when nothing is worth sending, it sends nothing."**
2. **"A lit rung means a message actually arrived. A failed send earns nothing."**
3. **"I wrote the prediction down first, it turned out wrong, and I'm reporting it."**

## Don't say

- Any percentage uplift from the AI. Your own experiment showed there isn't one.
- That the 13.6 million figure is real money. It's a simulation, and the README says so.
- That WhatsApp is working. It's built, and it's blocked by the provider.
