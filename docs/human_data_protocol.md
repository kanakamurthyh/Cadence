# Human data protocol

Collect the data in this order. **The order matters:** a ranking can change which reading
the T1 ladders are built from, and listening responses are tied to that ladder version.

| Step | Who | Output | Verify with |
|---|---|---|---|
| 0. Envelope takes for T5 | ≥ 2 teammates, ideally 4, 1 rehearsed take each | `data/raw/T5/team_<name>_take1.wav` plus a consent form | `cadence fetch && cadence refs` |
| 1. Rank readers | 3 raters × 6 texts, 102 readings: T1 24, T2 23, T3 19, T4 19, T5 2 + team, T6 15. Most important: **T1** (sets calibration), then **T4/T3** (the speeches) | `data/rankings/T1.csv` … `T6.csv` | `cadence status` |
| 2. Rebuild refs and ladders | You | `selection.json` method = human ranking; ladders re-rendered | `cadence status` |
| 3. Listening test | 5 listeners × 36 trials | `data/listening/responses.csv` | `cadence status` |
| 4. Teammate takes and annotations | Readers; 2 annotators | `data/takes/…`, `data/annotations/…` | `cadence natural` |
| 5. Re-run the benchmark and compare | You | `results/results.md`, `results/comparison.md` | `cadence compare` |

Start the human-study pages with `uv run cadence human`. They open at `http://localhost:7861`
on this Mac and at `http://<this Mac's LAN IP>:7861` for teammates on the same network.

## 0. Envelope takes for T5 (FDR "Day of Infamy" opening)

T5 has only two public-domain renditions: FDR's original and one LibriVox reading. An envelope
needs at least 4, so T5 has no ladders or results until teammates add theirs.

1. Each teammate signs `data/consent/CONSENT_FORM.md` and saves it as `data/consent/<name>.pdf`.
2. Rehearse the passage, then record **one best-effort take**: a strong, deliberate delivery,
   not a flawed one.
   - Print the passage with `uv run python -c "from cadence.data.texts import TEXTS; print(TEXTS['T5']['text'])"`.
   - Use a quiet room, 30 cm from the microphone, and leave 1–2 s of silence at both ends.
3. Save the take as `data/raw/T5/team_<name>_take1.wav` (m4a and mp3 also work).
4. Run `uv run cadence fetch && uv run cadence refs`. The takes join T5's ranking. Once T5 has
   ≥ 4 good renditions, `uv run cadence ladders` builds its ladders.

These takes are reference candidates. They must not also be submitted as natural-flaw takes
(step 4); `cadence natural` rejects identical files.

## 1. Reader ranking (3 raters)

1. Open the **Rank readers** tab, type your name, and pick **T1** in the Text dropdown.
2. Play every reader's first 20 s. Score each one from 1 (weak) to 10 (excellent delivery).
   - Judge **delivery only**: pace, pauses, pitch variety, emphasis, volume, fluency.
   - Ignore accent, microphone quality and voice type.
3. Every slider starts at 5, and an untouched slider is saved as 5. Move every slider.
4. Click **Save my scores**, then repeat for **T2**, **T3**, **T4** and **T5**.
   - T3 and T4 are two passages of the same 19 Gettysburg readings; rate each passage on its own.
   - For T5, rate after step 0, so the teammate takes are included.

Rater rules:
- Rate alone, without discussing scores with the other raters.
- Use the same spelling of your name for every text.
- To change your scores, save again. Your latest scores replace the earlier ones.

**Stored data:**
- Raw scores are appended to `data/rankings/<T>_ratings.csv` as `rater,id,rating`.
- Ranks are recomputed into `data/rankings/<T>.csv` as `id,<rater1>,<rater2>,<rater3>`.
- `cadence refs` reads this file: it sorts readers by mean rank and takes the top 6 as the good set.

## 2. Rebuild after ranking

```bash
uv run cadence refs      # re-selects the good set (recordings are cached, takes seconds)
uv run cadence ladders   # re-renders only the clips whose source reading or spans changed
uv run cadence status    # check: method = human ranking, ladders consistent
```

## 3. Listening test (5 listeners, ~15 min each)

Use headphones in a quiet room.

1. Open the **Listening test** tab, type your name, and click **Start / resume**.
2. For each trial, play **clean** and then **test**. Rate how much worse the test clip
   sounds: 0 = no difference, 4 = much worse.
3. Click **Save and next**. There are 36 trials.
4. If you get interrupted, enter the same name and click **Start / resume**. The test
   continues where you stopped.

Trial order is randomized per listener. 6 of the 36 trials are clean-vs-clean checks.

**Stored data:**
- Responses are appended to `data/listening/responses.csv` as
  `listener,clip,type,level,rating,source,time`.
- Only rows whose `source` matches the current T1 ladders are used.
- `cadence evaluate` fits the T1 severity map to the perceived ratings (0–4), and reports the
  lowest audible level and the Spearman correlations.

## 4. Teammate takes and annotations

**Recording.**
- Each teammate reads each text twice, naturally, with no deliberate flaws, as
  `data/takes/<T>/<speaker>_<T>_take<n>.<wav|m4a|mp3|flac>`. Example: `priya_T2_take1.m4a`.
- Read the canonical text exactly. Print it with `uv run python -c "from cadence.data.texts import TEXTS; print(TEXTS['T2']['text'])"`.
- If a take changes any words, put the words actually read in `data/takes/<T>/<take_id>.txt`.
- Record in a quiet room, phone or laptop microphone, 30 cm away.
- Start recording a second or two before speaking. Anything before or after the text is
  trimmed automatically.

**Annotating.** Two annotators, each working alone and **before seeing any Cadence output**.

1. In Audacity, open the take and add a label track.
2. Mark each delivery flaw as a span label: select the span, press Ctrl/Cmd+B, and type the type.
   - Types: `pace`, `missing_pause`, `misplaced_pause`, `monotone`, `missed_emphasis`, `volume_fade`.
   - Point labels are rejected.
   - For a pause flaw, select the silence itself (misplaced) or the two words around the
     boundary (missing).
3. Export with **File → Export → Export Labels** to `data/annotations/<annotator>/<take_id>.txt`.
4. A take with no flaws still needs an **empty** label file. It means "listened, found no flaw".

Check with `uv run cadence natural`. It lists missing files and format errors, then evaluates:
- Cadence against each annotator (Matching Score, time F1);
- annotator against annotator (the ceiling, with mean IoU);
- flags no annotator marked, per minute.

Teammate takes are **test data only**. They never enter calibration or the good set.

## 5. Re-run and compare

```bash
uv run cadence evaluate                 # T1-only calibration, T2/T3 held out (unchanged rule)
uv run python scripts/robustness.py
uv run python scripts/make_demo.py
uv run python scripts/rerun_check.py --store   # params changed, so refresh the stored hashes
uv run cadence compare                  # baseline (results/baseline_2026-10-13) vs now
```
