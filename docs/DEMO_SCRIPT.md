# Demo Script

A **1:45 recorded demo** for slide 6 of [`PITCH_DECK.md`](PITCH_DECK.md). The rubric strongly recommends a recording over a live demo. Thomas drives the app, Krish records and narrates (or narrates live over the video).

Every click below uses the real labels in the app. The "Is this a scam?" step needs PR #17 merged and deployed.

## Before recording

1. Open **https://secondlook-lpl.vercel.app** in Chrome at 1440×900, zoom 110%. Close other tabs and turn off notifications.
2. Check the top bar says **Live API**, not "Mock data".
3. Press **Reset demo**. The fraud queue should show 4 cases: Eleanor, Walter, Janet, Robert.
4. **Warm up:** submit one withdrawal as Marcus Bell, then press **Reset demo** again. The first AI call after a quiet period is the slowest.
5. In the demo account dropdown, each option ends in "(scam)" or "(normal)". Pick it quickly so the open list isn't on screen long, or cut it in editing.
6. Record with Xbox Game Bar (**Win + Alt + R**) or OBS. Record the whole run, then **cut the waiting** (scoring takes about 7 seconds and Juno answers take about 10) so the final video is about 1:45.
7. Watch the finished file on the presentation laptop, with sound, before Saturday.

## The script

Timings are for the final, edited video.

### 0:00 – 0:20 · The call (client, before any money moves)

**Click:** **View as: Client** → tab **Is this a scam? Ask Juno**. Demo client: **Margaret Ellis, 78**. Tap the example **"Bank security" call**.

**On screen:** Juno answers with a red **This looks like a scam** and **Bank impersonation**: it's safe to hang up, never move money to a "safe account", and call the number on the statement.

**Say:**
> "Margaret gets a call from 'bank security'. Before doing anything, she can ask Juno, our AI. Juno says it's a scam, in plain English, and tells her it's safe to hang up. And the firm now remembers she asked."

### 0:20 – 0:45 · The withdrawal (client)

**Click:** tab **Withdraw funds**. Demo account: **Margaret Ellis · $180,000 to CoinVault Exchange**. Press **Submit withdrawal**. *(Cut the wait.)*

**On screen:** "Reviewing your request…" steps, then **We paused this withdrawal to protect you**.

**Say:**
> "But scammers are persuasive, and they call back. Later she tries to wire $180,000 to a crypto exchange she added that morning. In about 7 seconds, Second Look pauses it. Nothing has left her account."

**Click:** **Yes, it was me**.

**Say:**
> "She confirms it was her, because she really did it. The hold stays in place anyway."

### 0:45 – 1:20 · The investigation (fraud team)

**Click:** **View as: Fraud team** → click **Margaret Ellis** in the case queue.

**On screen, point at each in order:**
1. **Risk score** about 95, **HIGH RISK**, and **Hold ends in** shows a short 2-business-day review hold (the countdown includes any weekend), not a long freeze
2. **Signals:** rule checks (new payee, added today, entire balance, senior client, first crypto) and, separately, what **Juno found** (the "safe account" script)
3. **Juno case memo**, citing **FINRA Rule 2165**
4. Scroll to **What the firm already knew**: her check, **Asked Juno in the app · Juno: likely scam**, and her earlier calls asking about wires to "a crypto account"
5. **Who was alerted:** Margaret, her advisor, her daughter Susan, the fraud team

**Say:**
> "The fraud team sees the whole story. Rules catch the obvious signals; Juno reads the rest, including that Margaret already asked about this exact scam. The memo cites the FINRA rule, and her daughter has already been alerted."

### 1:20 – 1:35 · Ask Juno, then decide (fraud team)

**Click:** in **Ask Juno**, tap **What should I verify before releasing?** *(Cut the wait.)*

**On screen:** Juno's answer, built only from this case, and logged.

**Click:** **Extend hold**.

**On screen:** **Hold ends in** jumps to 15 business days: "Extended to 15 business days, FINRA Rule 2165's limit for clients 65+".

**Say:**
> "Investigators can question Juno, and every question is logged. Only the fraud team can decide. This isn't like Margaret, so they extend the hold to the 15 business days FINRA Rule 2165 allows, and the $180,000 stays with her."

### 1:35 – 1:45 · No false alarms (client)

**Click:** **View as: Client** → **Withdraw funds** → demo account **Marcus Bell · $600** → **Submit withdrawal**. *(Cut the wait.)*

**On screen:** **Your withdrawal is on its way**.

**Say:**
> "And a normal $600 transfer goes straight through. Second Look only steps in when it matters."

## Optional cuts, if a judge asks or there's time

**Scammer isolation (Harold, 20 s).** As the client, submit **Harold Brooks · $95,000**. In the fraud view, **Who was alerted** shows his nephew Kevin as **not alerted: may be involved**.
> "Here the scammer is the joint owner. Juno spots it, and he's never told."

**Advisor view (15 s).** **View as: Advisor** → Margaret's banner → **Notes for the Fraud team**: type "Called Margaret on the number on file. A 'bank security officer' told her to move everything." → **Save note**. The fraud view shows the note within 4 seconds.
> "The advisor adds what they know, but can't release the hold."

**No advisor (Dorothy, 25 s).** Submit **Dorothy Nguyen · $25,000**. On the held screen, **Start the 1-minute scam check** and answer **Yes, someone called me**.
> "Clients without an advisor get a short scam check from Juno instead."

**Every case state (10 s).** In the fraud queue, click through Eleanor (escalated), Walter (held), Janet (extended), and Robert (released with a written reason).

## If something goes wrong live

| Problem | Do this |
|---|---|
| Submit takes over 20 seconds | Keep talking. The app switches to a faster model at 12 s and finishes within 22 s |
| Score shows "?" and "manual review" | Say: "The AI failed, so the withdrawal stays held for a person. That's the fail-safe." Then continue |
| "Juno is unavailable" | Skip Ask Juno and go straight to **Extend hold** |
| The page or network fails | Switch to the recorded video |
| Old cases left on screen | **Reset demo** |
