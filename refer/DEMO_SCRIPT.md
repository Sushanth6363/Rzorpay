# 5 minute demo script

**Unified Recovery Engine · Razorpay AI Buildathon 2026 · Track 3**

> Quote blocks are what you say. *Italics* are stage directions, don't read them.

```
0:00   Intro
0:20   Architecture             90 seconds on the diagram, the one slow section
1:50   Decision trace           five points
2:10   Experiment               five points
2:35   Safety                   five points
2:55   Live test                the demo itself
4:40   Close
```

**If it is on the screen, do not read it out.** Point at it, and say the one thing the
screen cannot say for itself.

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
* Run the Experiment benchmark now, so results are already on screen. Takes about 80
  seconds at the default 200 events, seeds 21 to 40. Don't shrink it, the smaller run is
  underpowered and shows inconclusive.
* Clear the board
* Open: GitHub README, dashboard, your inbox. Phone visible.
* `demo_customers.csv` ready to drag

> **Dispatch is live.** Only use a CSV with your own address.

***

## 0:00 · Intro

> "Hi, I'm Sushanth. This is the Unified Recovery Engine, for Track 3.
>
> Every business loses money it has already earned. Failed payments, abandoned checkouts,
> overdue invoices. Most systems chase all of it the same way. Mine decides, case by case,
> whether to chase at all."

***

## 0:20 · Architecture · 90 seconds

*GitHub README, the flow diagram. This is the slow section. Everything after it moves
faster, so take the full ninety seconds here.*

*Point at the top two boxes.*

> "Two ways in. A Razorpay webhook when a payment fails, or a merchant's CSV of overdue
> invoices. Same engine underneath, either door."

*Run your cursor down the stack of boxes.*

> "Eight stages, and the order is the point. Validate there is real money at risk. Diagnose
> why it is unpaid. Generate only what this stream is allowed to do. Then the safety filter
> drops whatever is not allowed right now, before anything is scored."

*Point at the indigo diamond.*

> "Here is the decision. Every survivor is scored on one question. How much more likely is
> this customer to pay if I do this, instead of nothing.
>
> Doing nothing scores exactly zero, so it is a real candidate. When it wins, the engine
> contacts nobody. That is the amber path."

*Point at the dotted arrow looping back up.*

> "It then schedules its own next look, and a worker brings the case back round."

*Point at the green box, then the red one.*

> "Two ways out. The money arrives, or the stopping rules hand it to a person."

*Scroll to the ladder diagram.*

> "And contact gets louder one step at a time, only ever one step above the last message we
> know arrived."

*Gesture at the whole page.*

> "Built on Razorpay links and signed webhooks, Twilio for SMS and voice, SMTP, ngrok,
> CatBoost, and SQLite as the shared memory that makes this one engine, not five scripts."

***

## 1:50 · Decision trace · five points

*Decision trace tab.*

> "This tab answers one question. Why did the engine do that. It is here because a recovery
> system that cannot show its reasoning is just a mailer with extra steps.
>
> One. That whole diagram, on one real case.
>
> Two. Amber means something was removed there.
>
> Three. Four eligible, three suppressed before any scoring.
>
> Four. That card names each one and why.
>
> Five. Change the scenario, the trace changes."

*Switch the dropdown to the overdue invoice.*

> "Different stream, so no retry is even offered. Nothing failed, nothing to repeat."

***

## 2:10 · Experiment · five points

*Experiment tab, results already on screen.*

> "This tab is where I try to disprove my own engine. Each version is missing one
> capability, so every feature has to earn its place or be dropped.
>
> One. Five versions of the engine, one identical batch.
>
> Two. I predicted the model would beat the simple rule.
>
> Three. It didn't. p value nought point nine six. The safety rules narrow the choices so
> far that scoring barely matters.
>
> Four. It wins here instead. Eleven percent fewer messages, no measurable loss of recovery.
>
> Five. That one was not pre-registered, and the panel title says so."

***

## 2:35 · Safety · five points

*Safety tab.*

> "This tab runs the safety rules in front of you instead of listing them. It is here
> because every one of these could be claimed on a slide, and a claim is not a check.
>
> One. These ran when the page loaded.
>
> Two. Each prints its own evidence. A check, not a checklist.
>
> Three. The six below have no ticks. This page did not run them.
>
> Four. Five hundred and fifty one tests.
>
> Five. And it reproduces on a fresh clone."

***

## 2:55 · Live test · the demo

*Live test tab. Everything before this was setup.*

> "This tab is the engine actually running. A merchant drops in their unpaid customers, and
> it decides case by case and really sends. Everything so far was me explaining it. This is
> it working."

*Drag in `demo_customers.csv`.*

> "A merchant's overdue invoices. Notice there is no column for why it is unpaid. They know
> what is owed, not why. If they typed a reason in, my diagnosis would just be reading their
> answer back.
>
> One row is broken on purpose. Rejected with a reason, not skipped."

*Point at the cards.*

> "Every case, its own decision. The chips are that ladder. Grey untouched, green confirmed
> sent."

*Switch to your inbox.*

> "And that email is real. It left seconds ago."

*Back to the board. Wait ten seconds, refresh. Again.*

> "Nothing out here triggered that. It scheduled its own next look and the worker woke it
> up. That is the loop from the diagram.
>
> The timing is not configured anywhere. It comes from the diagnosis, the channel, and how
> many times we have already tried. A gateway glitch retries in four hours. An overdue
> invoice waits eight days, because emailing a finance team daily just gets you blocked.
> Only the unit is compressed here. Every ratio is exact."

*Point at a rung lighting up.*

> "A failed send earns nothing, so the ladder does not move."

*Point at the green PAID row, then click Open.*

> "And a real payment. Twenty five thousand rupees. Razorpay's webhook hit this machine, we
> checked the signature, and the case closed itself. Links cancelled, follow ups stopped.
>
> Every line on that timeline was written by the engine as it happened."

***

## 4:40 · Close

> "Doing nothing scores exactly zero, so when no action is worth taking, it contacts nobody.
> That is the difference between a recovery system and a harassment system.
>
> The numbers are simulated. The loop is real. Thank you."

***

## Optional, only if you have time

Real bugs from this project. Your strongest material, and they cost time.
**Have one ready, not all five.**

**The best one.** *(after the payment closes the case)*

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
> graded in a world that didn't exist. I fixed it, ran it again, and the prediction was
> still wrong. So I went looking for the metric the engine is actually built for, found it
> wins there, and put it below the one that failed rather than above it."

**The ledger one.** *(after Safety)*

> "The contact ledger was recording the simulator's result instead of what actually
> happened. Rows said a contact succeeded nine milliseconds after it was created, before the
> email had even been sent."

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
> "Free Twilio accounts only send fixed templates, so our link isn't in there. And the
> record says exactly that instead of claiming it worked."

**A payment doesn't close a case.** Run `scripts/send_test_webhook.py` and show the
receiving side works on its own.

**"Is that your model deciding?" on the trace tab.**
> "No, and the screen says so. That one uses base rates, the live path uses the trained
> model. I checked all seven scenarios and it picks the identical action every time."

***

## Four lines worth landing

1. **"Doing nothing scores exactly zero, so when nothing is worth sending, it sends nothing."**
2. **"Green means a message actually arrived. A failed send earns nothing."**
3. **"I wrote the prediction down first, it turned out wrong, and I'm reporting it."**
4. **"Eleven percent fewer messages, and no measurable loss of recovery."**

## Don't say

* Any percentage uplift from the AI. Your own experiment showed there isn't one.
* That the contact efficiency result was pre-registered. It was not, and the panel says so.
* That the 13.6 million figure is real money. It's a simulation.
* That WhatsApp is working. It's built, and blocked by the provider.
