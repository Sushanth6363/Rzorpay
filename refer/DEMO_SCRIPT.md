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
> Every business loses money it has already earned. Failed payments, dropped carts, unpaid
> invoices. Most systems chase all of it the same way. Mine looks at each case and decides
> if it is worth chasing at all."

***

## 0:20 · Architecture · 90 seconds

*GitHub README, the flow diagram. This is the slow section. Everything after it moves
faster, so take the full ninety seconds here.*

*Point at the top two boxes.*

> "Two ways in. Razorpay tells us a payment failed, or a merchant uploads a file of unpaid
> invoices. Same engine underneath, either way."

*Run your cursor down the stack of boxes.*

> "Eight steps, and the order matters. Check the money is really missing. Work out why it
> wasn't paid. List only the actions this kind of case allows. Then throw out anything we
> are not allowed to do right now, before we score anything."

*Point at the indigo diamond.*

> "Here is the decision. Every action left gets one question. How much more likely is this
> customer to pay if I do this, compared to doing nothing.
>
> Doing nothing scores zero. So it is a real choice, and when it wins, we contact nobody.
> That is the orange path."

*Point at the dotted arrow looping back up.*

> "The engine then sets its own reminder to look again, and a background worker brings the
> case back."

*Point at the green box, then the red one.*

> "Two ways out. The money comes in, or we stop and hand it to a person."

*Scroll to the ladder diagram.*

> "And we get louder one step at a time. Never more than one step above the last message we
> know actually reached them."

*Gesture at the whole page.*

> "Built with Razorpay payment links and signed webhooks, Twilio for SMS and calls, email
> over SMTP, ngrok, CatBoost for the model, and one SQLite database that all of it shares.
> That shared memory is what makes this one engine and not five separate scripts."

***

## 1:50 · Decision trace · five points

*Decision trace tab.*

> "This tab answers one question. Why did the engine do that. It is here because a system
> that cannot show its reasoning is just a spam tool.
>
> One. That whole diagram, on one real case.
>
> Two. Orange means something was thrown out at that step.
>
> Three. Four actions were allowed, three were blocked before we scored anything.
>
> Four. That card on the right names each one and why.
>
> Five. Change the case at the top, and the whole thing changes."

*Switch the dropdown to the overdue invoice.*

> "Different kind of case, so a retry is not even on the list. Nothing failed, so there is
> nothing to retry."

***

## 2:10 · Experiment · five points

*Experiment tab, results already on screen.*

> "This tab is where I try to prove my own engine wrong. Each version has one piece taken
> out, so every feature has to show it is worth keeping.
>
> One. Five versions of the engine, over the same set of cases.
>
> Two. I wrote down first that the model would beat the simple rule.
>
> Three. It did not. p value zero point nine six. The safety rules cut the choices down so
> much that the scoring barely matters.
>
> Four. It wins here instead. Eleven percent fewer messages, and no drop in money recovered
> that we can measure.
>
> Five. I did not call that one in advance, and the title of the panel says so."

***

## 2:35 · Safety · five points

*Safety tab.*

> "This tab runs the safety rules in front of you instead of listing them. Anyone can put
> these on a slide. A claim is not a check.
>
> One. These ran when the page loaded.
>
> Two. Each one shows what it actually found.
>
> Three. The six below have no tick, because this page did not run them.
>
> Four. Five hundred and fifty one tests.
>
> Five. And it all runs the same on a fresh copy of the code."

***

## 2:55 · Live test · the demo

*Live test tab. Everything before this was setup.*

> "This tab is the engine really running. A merchant drops in their unpaid customers, it
> decides one by one, and it actually sends. Everything so far was me explaining it. This
> is it working."

*Drag in `demo_customers.csv`.*

> "A merchant's unpaid invoices. Notice there is no column saying why it is unpaid. They
> know what is owed, not why. If they typed a reason in, my diagnosis would just be reading
> their answer back to them.
>
> One row is broken on purpose. It gets rejected with a reason, not quietly dropped."

*Point at the cards.*

> "Every case gets its own decision. Those chips are the ladder. Grey means not used yet,
> green means the message was sent."

*Switch to your inbox.*

> "And that email is real. It went out seconds ago."

*Back to the board. Wait ten seconds, refresh. Again.*

> "I did not touch anything. The engine set its own reminder and the worker picked it up.
> That is the loop from the diagram.
>
> The waiting time is not something I typed in. It comes from why the payment failed, which
> channel we used, and how many times we have already tried. A bank glitch, we try again in
> four hours. An unpaid invoice, we wait eight days, because emailing someone's finance team
> every day just gets you blocked.
>
> I sped the clock up for the demo. The gaps are still in the same proportion."

*Point at a rung lighting up.*

> "A message that fails to send earns nothing, so the ladder does not move up."

*Point at the green PAID row, then click Open.*

> "And a real payment. Twenty five thousand rupees. Razorpay called this laptop, we checked
> the signature, and the case closed itself. Payment links cancelled, reminders stopped.
>
> Every line on that timeline was written by the engine as it happened."

***

## 4:40 · Close

> "Doing nothing scores zero. So when nothing is worth sending, we send nothing. That is the
> difference between a recovery system and a system that just annoys people.
>
> The experiment numbers are simulated. The loop is real. Thank you."

***

## Optional, only if you have time

Real bugs from this project. Your strongest material, and they cost time.
**Have one ready, not all five.**

**The best one.** *(after the payment closes the case)*

> "The first time I really paid this link, the case did not close. The message came in, the
> signature was fine, and the engine was about to chase me for money I had just paid it.
> That got past three hundred and ninety five passing tests.
>
> Razorpay sent a payment event, not a payment link event, and it puts our reference in a
> different place. The test I wrote uses the real data Razorpay sent, not one I made up,
> because a made up one would have had the same wrong assumption in it."

**The experiment one.** *(after the p value)*

> "The model looked like it was losing and I nearly kept tuning it until it won. Instead I
> found a date bug that broke the ladder in every test run. The model was being judged in a
> world that did not exist. I fixed it, ran it again, and my prediction was still wrong. So
> I looked for the thing the engine is actually built for, found it wins there, and put that
> below the result that failed instead of above it."

**The ledger one.** *(after Safety)*

> "The contact log was saving what the simulator imagined instead of what really happened.
> Rows said a message succeeded nine milliseconds after it was created, before the email had
> even gone out."

**The reachability one.** *(after the CSV upload)*

> "A customer with a phone and no email was never contacted at all. Invoices start at the
> email step, nothing checked whether we had an address, so the message never went, so it
> never moved up. It offered the same impossible action forever."

**The Razorpay notify one.** *(after escalation)*

> "Razorpay's links have a notify setting and I had it switched on. So Razorpay was sending
> its own SMS and email on top of mine. Three messages for one decision, and none of them in
> my log."

***

## If something goes wrong

**The email doesn't arrive.**
> "Email is a live dependency. The send log shows it went, with the provider's ID."

**No escalation shows up.** Check `/health`. If it says 3600 the clock isn't sped up.
> "This one is at real world timing, so the next check is scheduled rather than immediate."

**WhatsApp shows FAILED.** Use it.
> "That is Twilio refusing. It is a paid feature. The engine records the failure and does
> not move up the ladder, because a step only turns green when a message really went."

**The SMS wording looks odd.**
> "Free Twilio accounts only send fixed templates, so our link is not in there. And the
> record says exactly that, instead of pretending it worked."

**A payment doesn't close a case.** Run `scripts/send_test_webhook.py` and show the
receiving side works on its own.

**"Is that your model deciding?" on the trace tab.**
> "No, and the screen says so. That one uses base rates, the live path uses the trained
> model. I checked all seven cases and it picks the same action every time."

***

## Four lines worth landing

1. **"Doing nothing scores zero, so when nothing is worth sending, we send nothing."**
2. **"Green means a message really arrived. A failed send earns nothing."**
3. **"I wrote my prediction down first, it turned out wrong, and I am reporting it."**
4. **"Eleven percent fewer messages, and no drop in money recovered."**

## Don't say

* Any percentage uplift from the AI. Your own experiment showed there isn't one.
* That the contact efficiency result was called in advance. It wasn't, and the panel says so.
* That the 13.6 million figure is real money. It's a simulation.
* That WhatsApp is working. It's built, and blocked by the provider.
