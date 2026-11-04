# Part A (SQL) — Run of show · 35 minutes

**Team 1 · Fri 13 Nov 2026 · D302 · 16:30–17:05** (Part B, Relational Algebra, takes 17:05–17:30)

Hybrid session: in-room plus live stream. Per the course policy one team member relays the
online chat and one supports online lab participants — those are **roles R and S** below.

## Roles — assign these by name before Friday

| Role | Who | Does what |
|---|---|---|
| **D** Driver | | Runs the clock, gives every instruction, owns the shared screen. The only voice giving tasks. |
| **F** Floor | | Walks the room. Does **not** answer "what's the query?" — asks "what does `WHERE` see at that point?" Reports to D every 3 min: *"roughly N% are through Task k."* |
| **R** Relay | | Watches chat, reads online questions aloud. Posts every command and every checkpoint answer into chat as D says it. |
| **S** Support | | Breakout room for online students who are stuck or whose setup failed. Keeps them on Tasks 1–3 if Task 4 is impossible for them. |
| **Q** Quizmaster | | Runs the live quiz, reads the result bars, drives the 2-minute debrief. |

**Everyone on the team has run the whole lab end to end on their own laptop, and one person
outside the team has dry-run it** (course requirement, T−7 days).

---

## Timeline

| Clock | Min | What | Who |
|---|---|---|---|
| 16:30 | 2 | **Framing + setup triage** | D |
| 16:32 | 8 | **Live quiz** (8 Q) + debrief of the 2 worst | Q |
| 16:40 | 5 | **Task 1** — clause pipeline | D, F |
| 16:45 | 7 | **Task 2** — joins change the grain | D, F |
| 16:52 | 8 | **Task 3** — the query that lies | D, F |
| 17:00 | 5 | **Task 4a–4c** — run the benchmark, read the matrix | D, F |
| 17:05 | — | **Hand over to Part B** | D → RA lead |

**Task 4d–4f and the extension are take-home.** Say this at 16:30 so nobody paces for it.
If you are ahead at 17:00, do 4d live — it is the best five minutes in the lab.

---

## 16:30 · Framing (2 min) — D

Say this, more or less verbatim. It sets up the whole hour:

> "You all wrote SQL in COMP3030, so we are not going to teach you `SELECT`. Today SQL is a
> **measuring instrument**. You will run the *same query text* on the *same data* in two
> engines and get a **~35–80× difference one way and a ~90–200× difference the other way**. By
> 17:05 you will be able to say exactly why — and that is this week's lecture, in your
> hands rather than on a slide."

Then, in one breath:
- Handout + starter code are on Canvas (released T−48 h).
- Tasks 1–3 are autograded, Task 4 is prose and is where the marks are.
- Submission Sunday 23:59.
- **Setup triage:** "Who did *not* get the `WEEK1-SETUP` line to print?" Hands up → F pairs
  each of them with a neighbour who did, **now**, in 30 seconds. Do not debug a laptop in
  front of 40 people. Online equivalents go to S.

## 16:32 · Quiz (8 min) — Q

Eight questions, 45 s each. See `quiz/quiz.md` for items, keys and debrief notes.

- Announce: **not graded**, it is a diagnostic.
- Show the result bar **before** revealing the key.
- Pick the most popular wrong answer and ask **one** student who chose it to explain their
  reasoning. Their sentence is the misconception in the room. Thank them; do not correct
  them mid-sentence.
- **Debrief only the two worst-scoring questions.** Hard stop at 16:40.
- Q3 and Q8 are *planted*: do not resolve them. Say "hold that — Task 3 and Task 4 are
  exactly this." F should hear students referring back to them later; that is the design
  working.

> **Timebox discipline.** The quiz is the most over-runnable item in the lab. Q holds a
> visible timer. If the debrief is going well at 16:40, **still stop** — the misconceptions
> get resolved by the tasks, which is more durable than by your explanation.

## 16:40 · Task 1 (5 min) — D

- D reads the task aloud once, then **stops talking**. No worked example on screen.
- F circulates. The two things you will see: the date predicate in `HAVING`, and `SUM`
  instead of `AVG` for `avg_disc`.
- **Checkpoint:** "Hands up when your first row is `A | F | 147790`." When ~70% of hands are
  up, move. Do not wait for 100% — the autograder catches the rest at home.
- 30-second debrief: just Q1.1, `WHERE` vs `HAVING`, and the clause pipeline on screen.

## 16:45 · Task 2 (7 min) — D

- Give **5 minutes** for the main query, then **2 minutes** on Q2.3, the grain trap.
- F watches for: `GROUP BY c_custkey` alone (fails in DuckDB — good, let it fail), and a
  missing tie-break.
- **Run Q2.3 on the shared screen yourself** if the room is slow: add the `lineitem` join
  live and let them watch `total_value` jump ~4×. The gasp is the point.
- Debrief sentence to land: **"a join changes the grain, and every aggregate downstream is
  computed at whatever grain reaches it."**

## 16:52 · Task 3 (8 min) — D

This is the lab's centrepiece. Protect its eight minutes.

- **(a) 1 min.** Everyone runs the given query. Ask for the number. The room says **0**.
  Let the silence sit. Then: *"Nothing is broken. Both engines are correct. The standard
  requires this."*
- **(b) 3 min.** They diagnose. F's prompt, if asked: *"What is `150 <> NULL`?"* — and
  nothing more.
- **(c) 3 min.** Three repairs. Most teams get `NOT EXISTS` fastest.
- **(d) 1 min, whole room.** "Which would you ship?" Push past "it's faster" to
  **robust by construction vs robust by vigilance**. This is the sentence they should
  remember in five years.
- **(e)** Read it out, ask them to hold the answer, **hand it to the RA lead.** Do not
  answer it — Part B opens on it.

> If the room is 3+ minutes behind here, cut Task 4 to **4a only** (run the harness, read
> the matrix aloud, assign 4b–4f as take-home). Keep Task 3 whole. See the cut order in
> `solutions/SOLUTION-KEY.md`.

## 17:00 · Task 4a–4c (5 min) — D

- Everyone: `python starter/bench.py`. ~15 s to run.
- **Make them write a prediction in the *Guess* column before the numbers appear** — 20
  seconds, out loud as a show of hands: "who thinks SQLite wins P1?"
- Put the reference matrix on screen next to a student's. Point at the two directions:
  **~35× and ~55× DuckDB on the two scans, ~200× and ~90× SQLite on the two point lookups.**
  Say out loud that these ratios move between machines and between runs — the harness
  prints its own variance, and the handout asks for an order of magnitude, not a number.
- Land one sentence only, and leave the rest as take-home:
  > **"Neither engine is faster. Each is faster at the shape of work it was built for —
  > and 'the shape of work' means which rows and which columns you touch."**
- Flag 4d in one line to bait the take-home: *"S2 is S1 plus a WHERE clause, so it does
  less work, and in SQLite it is three times slower. The plan tells you why. Go find it."*

## 17:05 · Handover — D → RA lead

Say exactly this, then sit down:

> "Same database, no new setup. Task 3 showed you SQL returning 0 where the honest answer
> was 149,960, because of NULL and three-valued logic. Relational algebra has neither. Over
> to [name], who will show you the algebra that **can't** make that mistake — and that your
> query plans in Task 4 were secretly written in."

---

## Failure modes, and what to do in the moment

| Symptom | Do this |
|---|---|
| **Many students have no data** (didn't do setup) | Pair them. Tasks 1–3 need one laptop per pair. Only Task 4 needs their own. Have **one USB stick** with `data/` on it and your DuckDB wheels — 170 MB, faster than classroom wifi. |
| `pip install duckdb` fails in the room | Do not debug. Pair them. Afterwards, point at the pre-built `data/` on the stick. |
| Laptop too slow / <4 GB RAM | `python setup/build_data.py --sf 0.01` still shows every effect, with smaller ratios. Tell them to say so in their write-up. |
| **Timings are wildly noisy** | Expected — someone has 40 Chrome tabs open. Say it: this is why we report medians and compare ratios. Noise is a lesson, not a problem. |
| `SQLite/DuckDB` ratio is much smaller than ours | Usually a cold cache on first run, or a laptop on battery with aggressive power saving. Re-run `bench.py`; the warm-up handles the first, "plug in" handles the second. |
| A student says *"so DuckDB is just better"* | **Best moment in the lab.** Put P1 on screen: 0.004 ms vs 0.65 ms. Ask them to re-state the claim. |
| A student has already seen TPC-H | Send them to the extension E3 (break the optimiser) immediately. |
| Someone finishes everything by 17:00 | E2 (build a column store in SQLite) — they will get ~4.5× and still be 8× off DuckDB. Have them report that to the room in 30 s. |
| Running >4 min late at 16:52 | Cut Task 4 to 4a. **Never** cut Task 3. |
| Running early | Do 4d live. It is the strongest content in the package. |

## Equipment checklist (D)

- [ ] Shared screen mirrors **a real terminal**, not slides — font ≥ 18 pt
- [ ] Quiz open and tested, room code on screen from 16:30
- [ ] `bench.py` reference output on a slide, ready to show at 17:03
- [ ] USB stick: prebuilt `data/` + DuckDB wheels for Win/mac/Linux
- [ ] Visible countdown timer the whole room can see
- [ ] Canvas thread "Week 1 lab — setup check" skimmed Thursday night, so you already know
      how many will arrive without data

## Immediately after (T+1 week deliverable)

Collect for the one-page reflection required by the course:
- % who had working setup on arrival (from the Canvas thread vs. the hands-up count)
- Per-question quiz score bars (export from the quiz tool)
- Which task overran, and by how much
- Autograder pass rates per task — the single best signal of where the handout was unclear
- The two questions students asked most often that the handout *should* have pre-empted
