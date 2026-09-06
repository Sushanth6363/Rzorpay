# 5 minute demo script, written to be read aloud

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

> Quote blocks are what you say. *Italics* are stage directions, don't read them.
> Each section shows its word count so you can check your pace against a clock.
> The whole script is 581 spoken words, which is five minutes at a slow, clear pace.

```
0:00 to 0:25   Intro
0:25 to 1:10   The diagram
1:10 to 1:35   Decision trace
1:35 to 2:20   Experiment
2:20 to 2:45   Safety and tests
2:45 to 3:30   Upload a CSV
3:30 to 4:15   It escalates by itself
4:15 to 4:45   Payment always wins
4:45 to 5:00   Close
```

**Rule for the whole thing: if it is on the screen, do not read it out.** Point at it, and
say the one thing the screen cannot say for itself.

***

## Before you start

**Terminal 1, the engine:**

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; $env:PORT="8555"; .venv\Scripts\python.exe -m app.server
```

**Terminal 2, the tunnel.** Leave it open:

```powershell
cd "C:\Users\Dell\Documents\New folder\Razorpay"; .\scripts\start_tunnel.ps1
```

* `curl.exe -s localhost:8555/health` must show `followup_hour_seconds: 0.05`. If it says
  3600, restart Terminal 1, or escalation takes eight days on stage.
* Run the Experiment benchmark once now, so results are already on screen
* Clear the board
* Open: GitHub README, dashboard, your inbox. Phone visible.
* `demo_customers.csv` ready to drag

> **Dispatch is live.** Only use a CSV with your own address.

***

## 0:00 to 0:25 · Intro *(54 words)*

> "Hi, I'm Sushanth. This is the Unified Recovery Engine, built for Track 3.
>
> Every business loses money it has already earned. Failed payments, abandoned checkouts,
> overdue invoices.
>
> Most systems chase all of it the same way. Mine decides, case by case, whether contacting
> someone is even worth it. And when it isn't, it doesn't."

***

## 0:25 to 1:10 · The diagram *(97 words)*

*README, flow diagram. Point at the top two boxes.*

> "Two ways in. A webhook from Razorpay, or a merchant's CSV of overdue invoices."

*Run your cursor down the next four boxes.*

> "Validate, diagnose, list what's legal, drop what isn't allowed."

*Point at the indigo diamond.*

> "It all funnels here. Highest expected value wins. And if nothing is worth doing, it takes
> that amber path and contacts nobody."

*Point at the dotted arrow looping back up.*

> "Then it schedules its own next look, and this line loops it back. Nothing outside is
> driving that."

*Point at the green box, then the red one.*

> "Two ways out. Money arrives, or the stopping rules hand it to a human."

*Scroll to the ladder diagram.*

> "Contact gets louder one step at a time, and only ever one step from the last message we
> know arrived."

***

## 1:10 to 1:35 · Decision trace *(44 words)*

*Decision trace tab.*

> "That diagram, on one real case."

*Point at the amber steps.*

> "Amber means something was removed. Four actions were eligible, three were suppressed
> before any scoring happened."

*Point at the rejected card on the right.*

> "There they are. Agent dial, WhatsApp, IVR, all rejected for escalation ceiling. Every
> number here comes from the decision that actually ran."

***

## 1:35 to 2:20 · Experiment *(98 words)*

*Experiment tab, results already on screen.*

> "Five versions of the engine over the same batch, each isolating one capability.
>
> Now the honest part. I wrote a prediction down before running this. I said the machine
> learning model would beat the simple rule based version."

*Point at the row.*

> "It didn't. Inconclusive, p value nought point nine six.
>
> And the reason is better than a win. The safety rules narrow the choices so far that
> scoring barely matters. The two scorers disagree on four decisions in a thousand.
>
> The one significant result is the engine against doing nothing. Every comparison is on
> screen, including the four that went nowhere."

***

## 2:20 to 2:45 · Safety and tests *(47 words)*

*Safety tab, point at the green bar.*

> "These ran when the page loaded. Not a document, actual checks, with the evidence each one
> returned underneath it.
>
> The six below have no ticks, because this page didn't run them. Five hundred and twenty
> three tests. And the whole evaluation reproduces exactly on a fresh clone."

***

## 2:45 to 3:30 · Upload a CSV *(71 words)*

*Drag in `demo_customers.csv`.*

> "A merchant's overdue invoices. Notice there's no column for why it's unpaid. They know
> what's owed, not why. If they typed a reason in, my diagnosis would just be reading their
> answer back.
>
> One row is broken on purpose. Rejected with a reason, not quietly skipped."

*Point at the cards.*

> "The chips in the middle are that ladder. Grey is untouched, green is confirmed sent."

*Switch to your inbox.*

> "And that email is real. Sent a few seconds ago."

***

## 3:30 to 4:15 · It escalates by itself *(71 words)*

*Back to the board. Wait ten seconds, refresh. Again.*

> "Nothing out here triggered that. It scheduled its own next look, and a worker woke it up.
>
> The timing isn't configured anywhere. A gateway glitch retries in four hours. An overdue
> invoice waits eight days, because emailing a finance team daily gets you blocked.
>
> I've sped the clock up for this. Only the unit changes, every ratio is exact."

*Point at a rung lighting up.*

> "Green means that message was confirmed sent. A failed send earns nothing."

***

## 4:15 to 4:45 · Payment always wins *(56 words)*

*Point at the green PAID row, then click Open.*

> "A real payment. Twenty five thousand rupees. Razorpay's webhook hit this machine, we
> checked the signature, and the case closed itself. Links cancelled, follow ups stopped.
>
> The case is read again at the moment we send. So money arriving cancels whatever was
> already in flight."

*Point at the timeline.*

> "Every line there was written by the engine as it happened."

***

## 4:45 to 5:00 · Close *(43 words)*

> "The idea underneath all of it. Doing nothing scores exactly zero. So when no action is
> worth taking, it contacts nobody. That's the difference between a recovery system and a
> harassment system.
>
> The experiment numbers are simulated. The loop is real.
>
> Thank you."

***

## Optional, only if you have time

Each of these is a real bug found in this project. They are the strongest material you have,
and they cost time. **Have one ready, not all five.**

**The best one, use this if you use any.** *(after Payment always wins)*

> "The first time I actually paid this link, the case didn't close. The webhook arrived, the
> signature checked out, and the engine was about to chase me for money I'd just paid it.
> That got past three hundred and ninety five passing tests.
>
> Razorpay sent a payment event, not a payment link event, and it hides our reference
> somewhere different. The test I wrote uses the real data Razorpay sent, not a made up
> example, because a made up one would have had the same wrong assumption in it."

**The experiment one.** *(after the p value)*

> "The model looked like it was losing and I nearly tuned it until it won. Instead I found a
> timestamp bug that killed the escalation ladder in every test run. The model was being
> graded in a world that didn't exist. I fixed it, ran it again, and the prediction was still
> wrong."

**The ledger one.** *(after Safety)*

> "The contact ledger was recording the simulator's result instead of what actually happened.
> Rows said a contact succeeded nine milliseconds after it was created, before the email had
> even been sent."

**The reachability one.** *(after the CSV upload)*

> "A customer with a phone and no email was never contacted at all. Invoices start at the
> email rung, nothing checked whether we had an address, so the contact was never confirmed
> and it never moved up. It offered the same impossible action forever."

**The Razorpay notify one.** *(after escalation)*

> "Razorpay's links have a notify setting and I had it on. So Razorpay was sending its own
> SMS and email on top of mine. Three messages for one decision, none of them in my ledger."

***

## If something goes wrong

**The email doesn't arrive.**
> "SMTP is a live dependency. The dispatch log shows it was sent, with the provider's ID."

**No escalation shows up.** Check `/health`. If it says 3600 the clock isn't compressed.
> "This one is at real world timing, so the next review is scheduled rather than immediate."

**WhatsApp shows FAILED.** Use it.
> "That's Twilio refusing. It's a paid feature. The engine records the failure and does not
> move up the ladder, because a rung only lights when a message was confirmed sent."

**The SMS wording looks odd.**
> "Free Twilio accounts only send fixed templates, so our link isn't in there. And the record
> says exactly that instead of claiming it worked."

**A payment doesn't close a case.** Run `scripts/send_test_webhook.py` and show the receiving
side works on its own.

**"Is that your model deciding?" on the trace tab.**
> "No, and the screen says so. That one uses base rates, the live path uses the trained
> model. I checked all seven scenarios and it picks the identical action every time."

***

## Three lines worth landing

1. **"Doing nothing scores exactly zero, so when nothing is worth sending, it sends nothing."**
2. **"Green means a message actually arrived. A failed send earns nothing."**
3. **"I wrote the prediction down first, it turned out wrong, and I'm reporting it."**

## Don't say

* Any percentage uplift from the AI. Your own experiment showed there isn't one.
* That the 13.6 million figure is real money. It's a simulation.
* That WhatsApp is working. It's built, and blocked by the provider.
