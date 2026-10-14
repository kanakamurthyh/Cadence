# Technical Methods for Automatic Reading-Prosody and Speech-Delivery Assessment (catalogue for Cadence)

Researched 2026-10-14. Scope: commercial APIs, research methods (especially comparison against reference speakers), real-time read-along tracking, localisation of feedback, and datasets. Cadence context: wav2vec2 alignment of a known passage, a per-word "consensus envelope" (pace, pause, pitch, energy) built from several good human readers, and flags on spans outside the envelope.

## 1. Commercial pronunciation/prosody assessment APIs

### Takeaway
Microsoft Azure Pronunciation Assessment is the best-documented commercial reference. It returns word-level `ErrorType` tags (Omission, Insertion, Mispronunciation, UnexpectedBreak, MissingBreak, Monotone) with confidence values that you threshold yourself, which is close to Cadence's "flag spans outside a range" design. Speechace and SpeechSuper expose fluency primitives: WCPM, a pause list with timestamps, and articulation time. ETS SpeechRater and Pearson Versant combine interpretable fluency features (speech rate, articulation rate, mean length of run, pause frequency and duration) in regression models validated against human raters.

### Cited Findings
**Microsoft Azure Pronunciation Assessment** ([docs, updated 2026-07](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment))
- Scripted mode (with `ReferenceText`) is for reading. Unscripted mode (no reference text) is for speaking, and in that mode the speech-to-text model differs from Azure STT. For accurate unscripted text, Microsoft recommends calling STT first and then running a scripted assessment on the result. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- `Granularity`: `Phoneme` returns scores at full-text, word, syllable and phoneme level; `Word`; or `FullText`. The default is Phoneme. With phonemeAlphabet IPA and `nBestPhonemeCount`, it returns candidate spoken phonemes. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- Scores: `AccuracyScore`, `FluencyScore` ("how closely the speech matches a native speaker's use of silent breaks between words"), `CompletenessScore` (ratio of pronounced words to reference words), `ProsodyScore` ("stress, intonation, speaking speed, and rhythm"), and `PronScore`. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- PronScore formula: sort the available scores from low to high as s0..s3.
  - Reading with prosody: 0.4·s0 + 0.2·s1 + 0.2·s2 + 0.2·s3.
  - Reading without prosody: 0.6·s0 + 0.2·s1 + 0.2·s2.
  - Speaking with prosody: 0.6·s0 + 0.2·s1 + 0.2·s2.
  - Speaking without prosody: 0.6·s0 + 0.4·s1.

  The weakest dimension is weighted most heavily. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- Word-level `ErrorType` values are `None`, `Omission`, `Insertion`, `Mispronunciation`, `UnexpectedBreak`, `MissingBreak` and `Monotone`. A word is tagged `Mispronunciation` when its AccuracyScore is below 60. Omission and Insertion need `EnableMiscue=True`. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- Prosody `Feedback` per word contains `Break` (`UnexpectedBreak`/`MissingBreak` with Confidence) and `Intonation` (`Monotone`).
  - Microsoft suggests a threshold of 0.75 on both break confidences, and says you should tune it per scenario.
  - Monotone is detected over the whole utterance and copied to every word.
  - The `Monotone - SyllablePitchDeltaConfidence` fields are "reserved for user-customized monotone detection."

  — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- Limits: prosody assessment is en-US only and needs SDK 1.35.0 or later. Audio longer than 30 s needs continuous mode, and continuous mode does not support `EnableMiscue`; you have to diff against the reference text yourself to get Omission and Insertion. Streaming mode is supported with unlimited recording time. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)

**Speechace**
- Fluency response fields:
  - `word_correct_per_minute`, with 120 WPM cited as the minimum fluent rate.
  - `all_pause_list[]`, pause begin and end times at 10 ms accuracy. Pauses of 500 ms or more count as "medium" and pauses over 1 s as "long."
  - `duration` and `articulation` (speaking time vs pausing and filler time).

  — [Speechace docs](https://api-docs.speechace.com/api-reference/score-text-fluency/handling-fluency-response)
- Read-aloud fluency and pronunciation scores are mapped to IELTS, CEFR, PTE, TOEFL and TOEIC equivalents. — [Speechace fluency scoring](https://api-docs.speechace.com/features/scripted-activities/fluency-scoring)

**SpeechSuper** (from search summary, field schema not verified)
- Returns pronunciation, fluency, completeness and rhythm/speed scores; WCPM and pause count; and advanced features such as syllable stress, liaison, loss of plosion, and rising/falling tone at sentence ends. — [SpeechSuper samples (GitHub)](https://github.com/speechsuper/SpeechSuper-API-Samples)

**ETS SpeechRater**
- Operational since 2006. Feature categories are pronunciation, prosody, vocabulary, grammar, content and discourse, combined with filtering models for nonscorable responses. — [ETS RR-18-10, Chen, Zechner et al. 2018](https://www.ets.org/research/policy_research_reports/publications/report/2018/jyzm.html)
- Fluency features:
  - Speed fluency: speaking rate (words/s over total response time), articulation rate (words/s over articulation time), and mean length of run.
  - Breakdown fluency: pause frequency, pause duration, filled-pause rate, and long-pause frequency normalised by words.
  - Prosody: stress features (occurrence of and distance between stressed phonemes) and interval-based rhythm features over vocalic, consonantal and syllabic intervals.

  — [Hsieh & Zechner, EALTA 2019 slides](https://ealta.eu/conference/2019/Conference%20presentations/EALTA%202019%20Powerpoints/Automated%20assessment%20of%20fluency_Hsieh%20&%20Zechner.pdf); [arXiv 2608.26137](https://arxiv.org/pdf/2608.26137)
- Correlations: a meta-analysis cited in recent work reports speech rate r = .76, mean length of run r = .72 and pause frequency r = −.59 with proficiency. The recent study reports mean length of run ρ = +.75 and pause ratio ρ = −.72. — [arXiv 2608.26137](https://arxiv.org/pdf/2608.26137) (from search snippet)
- TOEFL Junior speaking: form-level human–machine r = .81 vs human–human r = .89. — [ETS report 2015](https://www.ets.org/research/policy_research_reports/publications/report/2015/jufc.html) (from search snippet)

**Pearson Versant**
- The fluency subscore covers rate of speaking, position and length of pauses, rhythm and phrasing. Pearson reports a correlation of about 0.98 with expert human scores, though the figure comes from a Wikipedia/marketing-level source. — [Wikipedia: Versant](https://en.wikipedia.org/wiki/Versant_(language_test))
- Pearson children's oral reading: machine Words Correct vs human r > 0.98 at the response level. — [Cheng, BEA4 workshop](https://www.cs.rochester.edu/~tetreaul/bea4/Cheng-BEA4.pdf) (from search snippet)

### Inferences
- Azure's design (word-level break and monotone flags with tunable confidence thresholds, and a weakest-dimension-weighted overall score) maps directly onto Cadence's envelope flags. Two pieces worth copying: (a) the "MissingBreak at punctuation" and "UnexpectedBreak mid-phrase" taxonomy, and (b) a min-weighted aggregate.
- Speechace's 500 ms / 1 s pause bands are a quick reference-free sanity check alongside the envelope.

### Gaps
- I found no technical detail on ELSA API, Amazon (no first-party pronunciation-assessment API found), iFlytek or Chinese gaokao/zhongkao English oral-test scoring, or Pearson PTE feature lists within this call budget.
- I could not retrieve the SpeechSuper response schema or the exact SpeechRater feature count and correlations from primary documents.

## 2. Research methods: reference-based comparison, GOP, monotony, pause classification

### Takeaway
Cadence's approach has a direct precedent. Project LISTEN (Mostow & Duong) represents each read sentence as a word-level contour (latency, production duration, mean F0, mean intensity per word) and scores a child by the Pearson correlation of that contour with an adult narration of the same sentence. Correlating rather than taking absolute differences cancels out pitch baseline and recording level. Recent work (2026) applies DTW over WavLM features against multiple native templates and averages the scores.

### Cited Findings
**Project LISTEN template models** ([Mostow & Duong, AIED 2009, "Automated Assessment of Oral Reading Prosody"](https://www.scs.cmu.edu/afs/cs.cmu.edu/Web/People/listen2/pdfs/AIED2009-expressiveness-final.pdf))
- Per-word features:
  - latency before the word, production time, and their sum as reading time, each both absolute and normalised per letter;
  - F0 averaged over the ASR-aligned word, from a pitch tracker;
  - mean intensity;
  - pitch variability as the SD of F0, chosen over max−min because it is more robust to outliers.
- The similarity score is the correlation between the child's and the adult's word-level contours, computed separately for each feature. Correlation "factor[s] out differences between adults and children in baseline F0 … individual variations in intensity, and fluctuations in recording conditions."
- Missing values (words given help, or not accepted as read) are excluded from the correlation, and the score is penalised by the proportion of undefined values.
- Scores are averaged per student, weighted by word count. Each feature is also regressed against time to get rate-of-change features, and the model is fit by stepwise linear regression.
- Data: 55 children aged 7–10 with at least 20 sentences each, and a single adult narration per sentence.
- Rubric prediction (n=10 students, 4-point rubric): cross-validated r = 0.902 for expression and volume, 0.768 for smoothness, 0.448 for pace and 0.281 for phrasing. Inter-rater ICC for those dimensions was 0.798, 0.283, 0.721 and 0.681.
- Sentence-level human kappa was only 0.087–0.297. The authors conclude that "a single sentence is insufficient to rate reliably."
- Posttest fluency prediction (cross-validated within-grade r):

  | Model | r |
  |---|---|
  | pretest | 0.809 |
  | latency-only | 0.859 |
  | correlation+latency | 0.872 |
  | correlation+latency+pretest | 0.965 |

- Comprehension posttest: correlation+latency r = 0.763 vs pretest r = 0.738.
- Precursor: Schwanenflugel et al. averaged 34 adults' readings into an "expressive reading profile" (pause durations at sentence ends, commas and mid-phrase "pausal intrusions"; F0 drop at sentence end; F0 at each word's vowel). F0 match and the number of pausal intrusions were the best indicators of prosodic development. — [Mostow & Duong 2009, citing Schwanenflugel et al.](https://www.scs.cmu.edu/afs/cs.cmu.edu/Web/People/listen2/pdfs/AIED2009-expressiveness-final.pdf)
- Journal version: template models (correlation with adult narration) vs generalised text-to-prosody models trained on 4,558 sentences narrated by 11 adults and applied to 85,209 child sentences. Using duration features only, the generalised models predicted fluency and comprehension posttests better (adjusted R² = 0.6, 55 children). — [Duong, Mostow & Sitaram, ACM TSLP 7(4), 2011](https://publications.ri.cmu.edu/two-methods-for-assessing-oral-reading-prosody); [RI CMU summary](https://ri.cmu.edu/publications/mining-data-from-project-listens-reading-tutor-to-analyze-development-of-childrens-oral-reading-prosody)
- Related LISTEN work:
  - "Detecting prosody improvement in oral rereading": same-day rereadings improve more, with recency effects about twice as strong as learning effects. — [RI CMU](https://ri.cmu.edu/?p=122142)
  - "What visual feedback should a reading tutor give children on their oral reading prosody" — [RI CMU](https://ri.cmu.edu/publications/what-visual-feedback-should-a-reading-tutor-give-children-on-their-oral-reading-prosody)
  - Interspeech 2010 paper on adapting a duration synthesis model — [ISCA](https://www.isca-archive.org/interspeech_2010/duong10_interspeech.html)

**DTW against native templates**
- McIntosh, Smit, Saito, Minematsu & Kamper (arXiv, July 2026), "Self-supervised Speech Comparison for L2 Phone, Rhythm, and Intonation Scoring." DTW over WavLM representations against native templates is text-free and works in English and Japanese.
  - Basic DTW "exceeds human agreement on holistic and sentence-level phonetic scoring."
  - The best rhythm metric, built from warping-path statistics, "approaches human-level performance."
  - Intonation (DTW distance plus prosodic residuals plus pitch and intensity features) is "more modest on some tasks."

  — [arXiv 2607.13721](https://arxiv.org/abs/2607.13721)
- Reference-based methods score against every available native template and average the results. — [arXiv 2607.13721 (search snippet)](https://arxiv.org/pdf/2607.13721)
- Earlier CALL intonation work compares F0 contours and breaks at the DTW-mapped syllable level, with trend similarity of F0 and energy contours. It reports a subjective–objective correlation of up to 0.88, and 91.2% vs 88.1% classification accuracy with a native vs a TTS reference. — [search summary of Arias (U. Chile) / Interspeech 2015 ma15c](https://www.isca-archive.org/interspeech_2015/ma15c_interspeech.pdf) (attribution to a specific paper among these not verified)

**GOP / reference-free scoring**
- GOPT (Gong et al., ICASSP 2022) is a transformer over GOP features from a Librispeech-trained ASR. It does multi-task scoring of accuracy, fluency, completeness and prosody at phone, word and utterance level, and was state of the art on speechocean762 at publication. — [arXiv 2205.03432](https://arxiv.org/abs/2205.03432v1)
- On speechocean762, utterance-level fluency and prosody PCCs of roughly 0.75–0.83 are reported across recent models. One GOP-TDNN baseline reports PCC of 0.361 (task level not verified). — [search summary across arXiv 2305.11438, 2406.02859 et al.](https://arxiv.org/pdf/2305.11438)
- Recent GOP variants remove the need for forced alignment, which matters for disfluent or child speech: segmentation-free GOP ([arXiv 2507.16838](https://arxiv.org/pdf/2507.16838)), GOP without phoneme time alignment ([arXiv 2603.25150](https://arxiv.org/pdf/2603.25150)), and CTC-based GOP ([arXiv 2506.02080](https://arxiv.org/pdf/2506.02080)).

**Monotony metrics**
- One patent classifies speech as monotone by clustering pitch values, computing a Pitch Variation Quotient (PVQ = pitch SD / mean) per cluster, and comparing the weighted average to a threshold (0.16 reported), with real-time feedback. — [US11205418B2 "Monotone speech detection"](https://patents.google.com/patent/US11205418)
- Semitone SD of F0 is the standard speaker-normalised pitch-variability measure. — [arXiv 1801.00453 (classroom presentation rating)](https://arxiv.org/pdf/1801.00453)
- Azure flags monotone per utterance, and exposes `SyllablePitchDeltaConfidence` for custom thresholds. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)

**Children's oral reading prosody (non-LISTEN)**
- Bailly et al. (Speech Communication 2022) studied 1,063 readings from 442 French children (over 30 h) with 6,853 scores from 29 raters. They combine linguistic counts per minute (correct words, repetitions, deletions, insertions) with prosodic, sentence-level and chunk-level silence features to predict multidimensional ratings. — [HAL hal-03585934](https://hal.archives-ouvertes.fr/hal-03585934); [PDF](https://lead.ube.fr/wp-content/uploads/2024/07/Bailly_et_al._2022.pdf) (details from search snippet; page blocked on fetch)
- Deep learning for ORF assessment rated on NAEP/MDFS-style scales. — [arXiv 2405.19426](https://arxiv.org/html/2405.19426v2)

### Inferences
- Cadence's envelope (per-word min/max across several readers) is a multi-reference generalisation of LISTEN's template model. Three cheap additions:
  1. A per-sentence contour correlation score per feature (pitch, duration, pause), which is robust to speaker baseline.
  2. A missing-value penalty for words that fail alignment.
  3. Feature values normalised per letter or syllable.
- LISTEN's finding that single-sentence human ratings are unreliable (kappa below 0.3) suggests aggregating over a passage before judging, and treating per-word flags as hints rather than verdicts.
- A semitone-based pitch SD per phrase compared against the readers' range is a defensible monotony flag.

### Gaps
- I did not obtain exact GOPT PCC numbers per aspect.
- I found no dedicated source on emphasis or prominence detection, or on pause classification beyond Azure's break taxonomy, Speechace's duration bands and Schwanenflugel's sentence/comma/mid-phrase categories.

## 3. Real-time read-along tracking

### Takeaway
Production read-along products use on-device ASR constrained by the known text, plus position tracking. Vendors publish design choices (favour recall, encourage the reader) but very few latency or algorithm details. Project LISTEN's published design (ASR tracks position in the text, detects deviations, and time-aligns words and silences) is the best documented one.

### Cited Findings
- Google Read Along (formerly Bolo) uses Assistant speech recognition and TTS on-device. Voice data never leaves the device, so it works offline. The team "optimized for recall, thereby increasing the number of false positives, which results in a user experience that feels more encouraging for children." — [Android Developers Blog, June 2020](https://android-developers.googleblog.com/2020/06/on-device-ML-design-insights.html); [Google blog](https://blog.google/outreach-initiatives/education/early-access-read-along/)
- Project LISTEN Reading Tutor: the ASR listens as the child reads each sentence, tracks the child's position in the text to detect deviations, and identifies the start and end of each word and silence. The tutor responds to hesitations and miscues with spoken and graphical feedback. Text is shown one sentence at a time. — [Mostow & Duong 2009](https://www.scs.cmu.edu/afs/cs.cmu.edu/Web/People/listen2/pdfs/AIED2009-expressiveness-final.pdf)
- Amira Learning is derived from Project LISTEN at CMU. It captures accuracy, rate, prosody and error types through miscue analysis, and tracks miscues, pauses and self-corrections in real time. — [Amira "Science"](https://www.amiralearning.com/how-it-works.html)
- Microsoft Reading Progress / Reading Coach:
  - Auto-detect error types: omission, insertion, mispronunciation, repetition and self-correction.
  - Metrics: Accuracy rate and Correct Words Per Minute.
  - Pronunciation sensitivity can be set to "less" or "more" sensitive.
  - Microsoft notes that detection "may not recognize accents and dialects well."
  - The support page documents no prosody or expression scoring.

  — [Microsoft Support](https://support.microsoft.com/en-us/topic/7617c11c-d685-4cb7-8b75-3917b297c407)
- PromptSmart VoiceTrack, a patented teleprompter, uses on-device speech recognition with no calibration and no internet. Scrolling follows spoken words and pace, waits during pauses, and stops when the speaker goes off-script until they return. — [SpeechTechMag](https://www.speechtechmag.com/Articles/News/Speech-Technology-News/PromptSmart-Launches-Teleprompter-App-with-Voice-Recognition---98763.aspx); [Teleprompter.com voice scrolling](https://www.teleprompter.com/features/voice-scrolling)
- Azure supports streaming pronunciation assessment with pause and resume. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)

### Inferences
- For a hackathon, constrained or streaming CTC alignment of wav2vec2 against the known passage, with a forward-only position pointer, approximates these systems. Following Read Along, it should favour leniency on word acceptance.

### Gaps
- None of the vendors I found publish latency figures, model sizes or tracking algorithms (keyword spotting vs constrained decoding). Microsoft Reading Coach's real-time internals are undocumented.

## 4. Explainability, temporal grounding and playback

### Takeaway
Commercial tools localise feedback to words with timestamps: Azure per-word ErrorType and break feedback, Speechace pause lists at 10 ms, and Reading Progress word-click review tied to audio. I found no documented A/B "you vs model" playback in these sources, although Project LISTEN's tutor plays adult narrations of every sentence.

### Cited Findings
- Azure attaches error types and prosody `Feedback` (Break, Intonation) to each word, with offsets and durations at word, syllable and phoneme level. — [MS Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)
- Speechace pauses have begin and end times accurate to 10 ms. — [Speechace](https://api-docs.speechace.com/api-reference/score-text-fluency/handling-fluency-response)
- Reading Progress lets teachers play a recording and select individual words, with keyboard navigation word by word. — [Microsoft Support](https://support.microsoft.com/en-us/topic/7617c11c-d685-4cb7-8b75-3917b297c407)
- The Reading Tutor has recorded adult narrations for several hundred stories, and LISTEN studied what visual prosody feedback to show children. — [Mostow & Duong 2009](https://www.scs.cmu.edu/afs/cs.cmu.edu/Web/People/listen2/pdfs/AIED2009-expressiveness-final.pdf); [RI CMU visual feedback paper](https://ri.cmu.edu/publications/what-visual-feedback-should-a-reading-tutor-give-children-on-their-oral-reading-prosody)

### Inferences
- Cadence can differentiate itself by playing the user's flagged span next to the same span from the closest reference reader. Word timestamps from alignment make that a simple slice.

### Gaps
- I could not access the findings of the LISTEN visual-feedback paper, and found no vendor documentation of A/B model playback.

## 5. Datasets and benchmarks

### Takeaway
For scoring validation, speechocean762 (with sentence-level fluency and prosody labels) is the standard open benchmark. L2-ARCTIC covers phone-level mispronunciation and MyST covers children's speech. No common open benchmark of multi-reader reference readings with prosody ratings turned up.

### Cited Findings
- speechocean762: 5,000 English sentences (2,500 train and 2,500 test) from Mandarin L1 speakers, 125 per split. Five raters scored phoneme, word and sentence levels, with sentence scores for accuracy, completeness, fluency and prosody. Open source. — [arXiv 2104.01378](https://www.arxiv.org/pdf/2104.01378) (details via search summary)
- L2-ARCTIC: 26,867 utterances from 24 non-native speakers with L1s Hindi, Korean, Mandarin, Spanish, Arabic and Vietnamese. 3,599 utterances carry manual annotations: 14,098 substitutions, 3,420 deletions and 1,092 additions. — [TAMU PSI](https://psi.engr.tamu.edu/l2-arctic-corpus/); [Interspeech 2018](https://www.isca-archive.org/interspeech_2018/zhao18b_interspeech.pdf)
- MyST: about 470 h of conversational English from 1,371 students in grades 3–5 talking with a virtual science tutor, collected 2008–2017. LDC2021S05. It is conversational, not read speech. — [LDC](https://catalog.ldc.upenn.edu/LDC2021S05); [LREC-COLING 2024](https://preview.aclanthology.org/setup/2024.lrec-main.1052)
- French children's oral reading: 1,063 readings from 442 children, with 6,853 ratings from 29 raters. — [Bailly et al. 2022 (HAL)](https://hal.archives-ouvertes.fr/hal-03585934)

### Inferences
- speechocean762's prosody and fluency labels give Cadence an external check. Correlate the envelope-violation rate with human prosody scores, keeping in mind it is non-native, sentence-level data with no multi-reader references.

### Gaps
- I did not verify licensing or availability of the LISTEN narration and child-reading data, or of any children's oral-reading prosody corpus with NAEP or MDFS ratings in English.
