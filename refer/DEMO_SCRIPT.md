# 5 minute demo script, written to be read aloud

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

> Everything in a quote block is written to be **spoken**. Short sentences, plain words,
> and pauses where you need to breathe. Read it at normal talking pace and it lands at five
> minutes. Anything in *italics* is a stage direction. Don't read it out.

```
0:00 to 0:20   Intro
0:20 to 1:00   GitHub, the README and the architecture
1:00 to 1:20   Decision trace
1:20 to 1:55   Experiment, including the result that went against us
1:55 to 2:15   Safety and tests
2:15 to 5:00   The live run
```

Each section has a **⚠ What broke here** box. Those are optional, and the timings above
assume you skip them. Use one or two if you have room, or save them for questions.

If you only tell one, tell the payment one. It's the best story in the project.

***

## Before you start (2 minutes, off camera)

**Terminal 1, the engine.** Dashboard, webhook listener and the follow up worker, all on
one port:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; $env:PORT="8555"; .venv\Scripts\python.exe -m app.server
```

**Terminal 2, the tunnel**, so Razorpay can reach this laptop. Leave it open for the whole
demo. Closing it kills the webhook path:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; .\scripts\start_tunnel.ps1
```

**Terminal 3, spare**, for the health check below and anything you need mid demo:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"
```

* [ ] `curl.exe -s localhost:8555/health` shows `followup_hour_seconds: 0.05` and `worker_interval_seconds: 2`.
      If it says `3600` and `60`, the server started before the demo settings, and your
      escalation will take eight days on stage.
* [ ] Run the Experiment benchmark once now, so results are already on screen
* [ ] Reset the board, tick confirm, then **Clear N unpaid**
* [ ] Tabs open: GitHub README, dashboard, your inbox. Phone where you can see it.
* [ ] `demo_customers.csv` ready to drag in

> **Dispatch is live.** Every upload sends a real email. Only use a CSV with your own address.

***

## 0:00 to 0:20 · Intro

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

***

## 0:20 to 1:00 · The README and the architecture

*Open the GitHub README. Scroll to the flow diagram.*

> "One engine handles all four streams. Failed payments, abandoned checkouts, failed
> renewals, and overdue invoices.
>
> The whole thing is one loop, and it's all on this diagram."

*Point at the two boxes at the very top.*

> "Everything starts in one of these two places. Either a webhook comes in from Razorpay,
> because a payment failed or somebody walked away from a checkout. Or a merchant uploads a
> CSV of overdue invoices. Both of them feed into the same pipeline, and after this point the
> engine doesn't care which door you came through."

*Run your cursor down the boxes underneath.*

> "Stage zero checks there's real money to recover here. Stage one asks the question in the
> box, why is this unpaid. Candidate generation asks what's even legal for this kind of case.
> And the safety filter throws out anything that isn't allowed right now, contact budget,
> outage suppression, the escalation ceiling."

*Point at the indigo diamond in the middle.*

> "Everything funnels into this one decision. Whatever survived all of that gets ranked by
> expected value, and the best one wins.
>
> And look at the two arrows coming out of it. The one going left says E V less than or equal
> to zero, and it leads to that amber box, no action. If nothing is worth doing, the engine
> abstains and writes down why. The other arrow is the best action, and that's the path that
> creates a Razorpay payment link and actually sends something."

*Point at the dotted arrow curving back up.*

> "This dotted line is the part I'd most like you to notice. After it sends, it schedules its
> own next look, and that arrow loops straight back up to stage one. It reads the case again and
> decides again, from scratch. Nothing outside the system is driving that."

*Point at the green box on the right, then the red one at the bottom.*

> "There are only two ways out. The green one is money arriving. A signed webhook comes in,
> the case is marked paid, open links get cancelled, and every scheduled follow up stops.
>
> The red one is the stopping rules. When we've done everything we're allowed to do, the case
> leaves as a handoff report for a human, carrying everything we already tried, so nobody
> sends the email we've already sent three times."

*Scroll to the escalation ladder diagram.*

> "And this is how contact gets louder, one step at a time.
>
> Zero is email, and it says ignorable, because it is. You can leave an email unread and
> nothing has happened to you. One is SMS. Two is WhatsApp, which expects a reply. Three
> interrupts you with a phone call. And four, the red one on the end, is a person calling a
> person.
>
> The rule is that it can only ever move one step to the right, from the last contact we know
> actually arrived. Never two, no matter what the model says. So the engine cannot open a
> relationship with a phone call."

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

***

## 1:00 to 1:20 · Decision trace

*Dashboard, then Decision trace.*

> "That diagram, running on one real case. This screen answers one question. Why did it do
> that?
>
> The numbered steps down the left are the same pipeline you just saw. And the colours are
> doing work here."

*Point at step three, the indigo one.*

> "Indigo means the decision was made at this step."

*Point at steps five and seven, the amber ones with the SUPPRESSED tag.*

> "Amber means something was taken away. Step five says four eligible, three suppressed
> before any scoring happened. Step seven names them."

*Point at the Rejected before scoring card on the right.*

> "And there they are. Agent dial, WhatsApp, IVR call, all three rejected, and the reason
> next to each one is escalation ceiling. This customer hasn't earned a phone call yet.
>
> Above it, the answer. The action it chose, and the expected value that won, five thousand
> two hundred and fifty rupees. Every number on this screen is read back from the decision
> that actually ran. Nothing here is scripted."

***

## 1:20 to 1:55 · The experiment

*Experiment tab. Results already on screen.*

> "Five versions of the engine, run over the same batch of cases. Each one isolates a single
> capability, so you can see what each part is actually worth.
>
> Now, the honest part. I wrote a prediction down before running this. I said the machine
> learning model would beat the simple rule based version.
>
> It didn't." *(point at the row)* "That comparison came back inconclusive. The p value is
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
> I fixed it, ran everything again, and the prediction was still wrong. So that's what I'm
> reporting."

***

## 1:55 to 2:15 · Safety and tests

*Safety tab. Point at the green bar across the top.*

> "That bar is counting checks that ran when this page loaded. Not a config file, not a
> document. Three of three passed, three executed, on this page load.
>
> Each row underneath has a green tick, the invariant code, and the actual evidence
> underneath it in monospace. That's the string the check returned, not a description of it.
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

***

## 2:15 to 3:00 · Upload a CSV, and a real email goes out

*Live test tab. Drag in `demo_customers.csv`.*

> "This is a merchant's list of overdue invoices. Six columns.
>
> Notice there's no column for why it's unpaid. A merchant knows what's owed and by whom.
> They don't know why. If I asked them to type in a reason, then my diagnosis would just be
> reading their answer back to them. So the engine works it out itself.
>
> One row in here is broken on purpose. It gets rejected with a reason, not quietly skipped.
> A dropped row is money the merchant thinks is being chased, and nothing is chasing it."

*Point at the cards appearing on the board.*

> "Each row is one customer. The coloured stripe down the left is the status, and the four
> chips in the middle are the escalation ladder from that diagram. Grey means we haven't been
> there. Green means a message was confirmed sent. And the dashed one is what it has decided
> to do next, but hasn't sent yet.
>
> Those counts above the cards are filters. Click needs attention, and you get only the rows
> that need a person."

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

***

## 3:00 to 4:00 · It escalates on its own

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

***

## 4:00 to 4:40 · Payment always wins

*Point at the green PAID row. Then click Open.*

> "That's a real payment. Twenty five thousand rupees, in test mode. Razorpay's webhook came
> into this machine, we verified the signature, and the case closed itself. Marked paid, the
> open link cancelled, and every scheduled follow up stopped.
>
> The case is read again at the moment we send, not when the action was queued. So if money
> arrives, it cancels everything already in flight. Someone who has paid can't be chased by a
> message that was lined up five minutes ago."

*Point at the timeline that opens underneath.*

> "And this is the whole life of that case, in order. Case created. Agent decided. Link
> created. Message sent. Follow up scheduled. Payment received. Case closed.
>
> That's seven lines, and every one of them was written by the engine as it happened. Nobody
> typed that."

**⚠ What broke here** *(20 seconds, the best story you have)*

> "The first time I actually paid this link, the case didn't close.
>
> The webhook arrived. The signature checked out. It was recorded. And the case just sat
> there, still open, with a follow up still scheduled. The engine was about to chase me for
> money I had just paid it.
>
> That got past three hundred and ninety five passing tests.
>
> Razorpay sent a payment event, not a payment link event. And a payment event hides our
> reference somewhere different. We were only looking in one place.
>
> There was a second bug underneath it. The code that cancels the follow up was matching on
> the wrong column, so it updated zero rows, reported success, and nothing checked.
>
> Both fixed. And the test I wrote for it uses the actual data Razorpay sent me, not a made up
> example. A made up example would have had the same wrong assumption baked into it."

***

## 4:40 to 5:00 · Close

> "The one idea underneath all of this. Doing nothing scores exactly zero. So when no action
> is worth taking, the engine contacts nobody. That's deliberate. It's the difference between
> a recovery system and a harassment system.
>
> The numbers in the experiment come from a simulation, and I've labelled them that way
> everywhere. What's real is the loop. A real payment link, a real email, a real webhook, and
> a real case closing itself.
>
> Thank you."

***

## If something goes wrong

Each of these has an answer that turns it into a point. Say it, then keep moving.

**The email doesn't arrive.**
> "SMTP is a live dependency. The dispatch log shows it was sent, with the provider's ID."

*Then show the timeline.*

**No escalation shows up.**
Check `/health`. If it says 3600, the clock isn't compressed.
> "This one is running at real world timing, so the next review is scheduled rather than
> immediate."

*Then point at the scheduled next review on the card.*

**WhatsApp shows FAILED.** Use it, don't hide it.
> "That's Twilio actually refusing. It's a paid feature on their side. The engine records
> the failure, and it does not move up the ladder, because a rung only lights up when a
> message was confirmed sent."

**The SMS wording looks odd.**
> "Free Twilio accounts can only send fixed templates, so our payment link isn't in there.
> And the record says exactly that, instead of claiming it worked."

**A payment doesn't close a case.**
Run `scripts/send_test_webhook.py` and show the receiving side works on its own.

**Somebody asks, is that your model deciding, on the trace tab.**
> "No, and the screen says so. That one uses base rates. The live path uses the trained
> model. I checked all seven scenarios and it picks the identical action every time, because
> the safety rules had already narrowed it down."

***

## Three lines worth landing

1. **"Doing nothing scores exactly zero, so when nothing is worth sending, it sends nothing."**
2. **"A lit rung means a message actually arrived. A failed send earns nothing."**
3. **"I wrote the prediction down first, it turned out wrong, and I'm reporting it."**

## Don't say

* Any percentage uplift from the AI. Your own experiment showed there isn't one.
* That the 13.6 million figure is real money. It's a simulation, and the README says so.
* That WhatsApp is working. It's built, and it's blocked by the provider.
