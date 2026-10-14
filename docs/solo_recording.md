# Solo recording session (about 15 minutes) and a 1-person listening pilot

For when teammates are not available. Everything here is **real human data from one person** and must be
reported that way: "1 reader; flaw labels are the instructions given before recording, not a listener's
judgement; label times from the same forced aligner Cadence uses; no second annotator."

## A. Five takes of T3 (Gettysburg, closing paragraph)

1. Start the app (`uv run cadence web`), open http://localhost:8000 in Chrome, go to **Practice**,
   choose **Gettysburg Address (closing paragraph)** and switch to **Test** mode (no hints).
2. For each take below: press record, read the **whole** passage, stop, then press **Save this recording**.
   Rename the saved file to the take id and move it to `Cadence-v3/data/takes/T3/`
   (e.g. `solo_T3_take2.webm`). Read every other part of the passage normally.

| Take | What to do differently | Words |
|---|---|---|
| `solo_T3_take1` | Nothing: your best natural reading | — |
| `solo_T3_take2` | **Rush** this sentence, clearly faster than the rest | "It is rather for us to be here dedicated to the great task remaining before us" |
| `solo_T3_take3` | Say this line **flat**, on one pitch | "that this nation, under God, shall have a new birth of freedom" |
| `solo_T3_take4` | **Don't pause** at this full stop; run straight on | "…what they did here. It is for us the living" |
| `solo_T3_take5` | Let your voice **fade** to almost a whisper | "shall not perish from the earth" |

Do not change the plan after recording (it is fixed in `data/takes/instructed_plan.json`).
The recordings stay on this computer (ignored by Git).

3. Then run:

```bash
uv run python scripts/instructed_labels.py   # labels from the plan, timed by alignment
uv run cadence natural                        # Cadence vs the instructed labels → results/natural.json
```

`cadence natural` will note "need 2 independent annotators": expected for a solo session.

## B. Listening pilot (about 20 minutes, n = 1)

`uv run cadence human` → http://localhost:7861 → Listening test. Report it as a 1-listener pilot only.
