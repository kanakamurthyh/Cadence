# Open speech corpora where many Indian speakers read the identical text (for a consensus-envelope delivery dataset)

Research date: 2026-10-14. All counts below were checked live on the source pages unless flagged in Gaps. "NC" means non-commercial (OK for a non-commercial hackathon). No ND licence was found among the candidates.

## Q1. Which candidates give a continuous 30–90 s passage read identically by many Indian speakers? (counts per L1)

### Takeaway
The **Speech Accent Archive (GMU)** is the only source found that gives one continuous, identical passage read by many Indian-L1 speakers. It holds 172+ South Asian samples of the same 69-word "Please call Stella" paragraph. Each clip is about 26–35 s, not 70 s, so it sits at the low end of the 30–90 s target. The licence is CC BY-NC-SA 4.0, which allows derivatives but adds NC and share-alike conditions. It is the best fit for this design.

### Cited Findings
- Elicitation paragraph (verbatim): "Please call Stella. Ask her to bring these things with her from the store: Six spoons of fresh snow peas, five thick slabs of blue cheese, and maybe a snack for her brother Bob. We also need a small plastic snake and a big toy frog for the kids. She can scoop these things into three red bags, and we will go meet her Wednesday at the train station." — [GMU How-to](http://accent.gmu.edu/howto/)
- Licence: the site says it is under the "BY-NC-SA 4.0 license from Creative Commons". The copyright line reads "© 2026 • The Speech Accent Archive", by Steven H. Weinberger and Matthew C. Kelley, George Mason University. — [GMU How-to](http://accent.gmu.edu/howto/). One secondary page (DagsHub mirror) says "CC BY-NC-SA 2.0". Treat the primary site's 4.0 as authoritative. — [DagsHub mirror](https://dagshub.com/m-cohn/speech-accent-archive)
- Recording conditions: "Subjects were recorded individually in quiet rooms … approximately 8-10 inches from the microphone", using Sony TC-D5M or Sony minidisc (MDR-70) recorders. Conditions vary across contributors, who must document their device. — [GMU How-to](http://accent.gmu.edu/howto/)
- **Sample counts per Indic/South-Asian L1.** I counted these from the `https://accent.gmu.edu/language/<lang>/` listing pages on 2026-10-14: Hindi 34, Urdu 29, Bengali 24, Nepali 18, Gujarati 17, Telugu 15, Tamil 13, Punjabi 12, Marathi 11, Kannada 9, Malayalam 8, Konkani 4, Oriya 2, Sindhi 1. That is about 197 South Asian samples in total, about 172 excluding Nepali and Urdu. The Hindi 34 / Telugu 15 / Tamil 13 figures match search snippets. — [Hindi list](https://accent.gmu.edu/language/hindi/), [Tamil](https://accent.gmu.edu/language/tamil/), [Telugu](https://accent.gmu.edu/language/telugu/)
  - Caveat: L1 does not equal country. Some Urdu, Bengali and Punjabi speakers are from Pakistan or Bangladesh, and some Indian-L1 speakers grew up abroad. Filter on the birthplace metadata on each sample page. For example, hindi1 is "male, nagpur, maharashtra, india". — [hindi1 sample page](https://accent.gmu.edu/samples/hindi1/)
- Audio: direct MP3 URL pattern `https://accent.gmu.edu/audio/<lang><n>.mp3`. — [hindi1 sample page](https://accent.gmu.edu/samples/hindi1/)
- I downloaded six clips and measured them with ffprobe: all are 44.1 kHz mono MP3 at 128 kbps. Durations: hindi1 26.3 s, hindi5 29.7 s, tamil1 35.2 s, telugu2 30.1 s, bengali3 27.6 s, marathi1 26.5 s. — [hindi1 audio](https://accent.gmu.edu/audio/hindi1.mp3)
- The Svarah authors list Speech Accent Archive as an existing benchmark where Indian speakers are "poorly represented". That is relative to Svarah's goals; in absolute terms it still has more than 170 Indian-subcontinent readings of one passage. — [Svarah paper](https://ar5iv.labs.arxiv.org/html/2305.15760)

### Inferences
- The Stella paragraph is a single fixed text with a ground-truth transcript, so the identical-text grouping is trivial. Grouping by L1 still gives at least 6 speakers per group for Hindi, Bengali, Gujarati, Telugu, Tamil, Punjabi, Marathi, Kannada and Malayalam.
- Clips last about 26–35 s. That meets the ≥30 s target only at the edge, and many clips will be slightly under 30 s. No 60–90 s identical passage exists in this source.
- The MP3 compression (128 kbps) and the mix of older tape and minidisc recordings mean quality is uneven. Screen with SNR checks before building the envelope. Weinberger's elicitation also contains some reading disfluencies, which are good for realism but should be filtered out of the "good readings" set.
- Share-alike means any derived audio (PSOLA-modified flaws) must be redistributed under CC BY-NC-SA 4.0.

### Gaps
- The site's /about and /browse_language.php pages returned 404, so I could not find a bulk-download licence statement separate from the how-to page.
- Not verified: whether a Kaggle mirror ("rtatman/speech-accent-archive", about 2,140 samples per secondary sources) carries the same licence. The Kaggle page did not render.
- No Rainbow Passage or "North Wind and the Sun" corpus with many Indian speakers was found in this pass.

## Q2. L2-ARCTIC (Hindi-L1 speakers reading identical CMU ARCTIC prompts)

### Takeaway
L2-ARCTIC is a clean option for identical sentences, but it has only **4 Hindi-L1 speakers**. Each reads the same ~1,132 ARCTIC sentences, which together make about 1 h per speaker. The licence is CC BY-NC 4.0. It cannot reach 6+ Indian speakers on its own.

### Cited Findings
- Hindi speakers: ASI (M), RRBI (M), SVBI (F), TNI (F). — [L2-ARCTIC page](https://psi.engr.tamu.edu/l2-arctic-corpus/)
- Content: about one hour of read speech per speaker from about 1,132 phonetically balanced CMU ARCTIC prompts. For 150 utterances per speaker, mispronunciation errors are manually annotated. All speakers use the same ARCTIC prompts. — [L2-ARCTIC page](https://psi.engr.tamu.edu/l2-arctic-corpus/)
- Licence: "CC BY-NC 4.0". Download is through a web form (name, email, affiliation), which emails a Google Drive link. — [L2-ARCTIC page](https://psi.engr.tamu.edu/l2-arctic-corpus/)

### Inferences
- The prompt IDs (arctic_a0001 …) are shared across speakers, so grouping is trivial. Each ARCTIC sentence lasts about 2–4 s. Concatenating 10–30 consecutive prompts gives a 30–90 s "pseudo-passage" read by the same 4 speakers. Prosody across sentence boundaries is not natural paragraph reading, though.
- It could be combined with the 20 other non-Indian L2 speakers (Arabic, Mandarin, Korean, Spanish, Vietnamese), plus the original CMU ARCTIC US speakers, if L1 diversity is acceptable. That gives 6+ speakers per prompt, but they are not Indian.

### Gaps
- I did not check the total size or the exact recording setup on the page. Per general knowledge it is 44.1 kHz WAV recorded in a quiet room, but that is unverified here.

## Q3. AI4Bharat Svarah (Indian-accented English)

### Takeaway
Svarah is CC BY 4.0, with 117 speakers and 9.6 h, but it is **not usable for identical-prompt grouping**. The paper says no two participants got the same sentence.

### Cited Findings
- HF id `ai4bharat/Svarah`, licence "CC BY 4.0". It has 9.6 h of audio from 117 speakers in 65 districts and 19 states, covering 19 L1s. It mixes read and spontaneous speech. Size is 1.1 GB in parquet, with a test split only. — [HF card](https://huggingface.co/datasets/ai4bharat/Svarah)
- Read part: "Each participant was asked to read 5 sentences randomly chosen from this collection while ensuring that no two participants got the same sentence". The pool was about 1k sentences across 9 domains, recorded on the Karya Android app (phone). — [Svarah paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/2305.15760)

### Inferences
- Svarah is useful only as an Indian-English accent and ASR sanity-check set, not for building a consensus envelope.

### Gaps
- I did not verify the sample rate or per-utterance durations.

## Q4. IIT Madras IndicTTS (English recorded by Indian native speakers)

### Takeaway
IndicTTS is studio quality and CC BY 4.0. Each language has typically one male and one female speaker who also record English. So it gives only about 2 speakers per language, and at most about 26 Indian-English voices across about 13 languages. I could **not confirm** that the English sentence set is identical across languages. If it is, IndicTTS-English would be the highest-quality identical-text source.

### Cited Findings
- "over 10,000 spoken sentences/utterances each for mono (native language) and English recordings, recorded by both male and female native speakers"; studio recordings; WAV with text. — search snippet of [IITM IndicTTS database page](https://www.iitm.ac.in/donlab/indictts/database). The page itself timed out on two fetch attempts.
- Licence: "voice talents provide consent to release their recordings under CC BY 4.0" (search snippet). The AIKosh mirror lists "Attribution 4.0 International (CC BY- 4.0)", studio quality, about 10 h per speaker set (example: Hindi female mono, 1.81 GB). — [AIKosh Hindi female mono](https://aikosh.indiaai.gov.in/home/datasets/details/hindi_female_mono_indictts_phase3.html)
- The paper on the unified TTS data-collection framework for 22 languages is arXiv:2410.14197, under a CC BY 4.0 paper licence. — [arXiv](https://arxiv.org/abs/2410.14197)

### Inferences
- The brief asked for IndicTTS's custom licence to be quoted. The older IndicTTS download page historically required accepting a custom "IndicTTS database" licence form (registration). The AIKosh re-releases say CC BY 4.0. The custom licence text could not be retrieved, so treat it as unverified.
- If the English sentences are shared, you would get about 2 speakers × 13 L1s reading identical sentences (possibly 26 speakers per prompt). These are short sentences, which would need concatenation.

### Gaps
- Not verified: whether the English text is the same across languages, the exact number of speakers with English recordings, and the verbatim custom licence. The iitm.ac.in page was unreachable twice. Check it manually: https://www.iitm.ac.in/donlab/indictts/database

## Q5. Mozilla Common Voice English, accent "India and South Asia"

### Takeaway
Common Voice is CC0, and the India/South-Asia accent bucket is large: 152,535 clips from 3,011 speakers in v25.0. However, the corpus has about 1.72M sentences for about 2.57M clips, so **most sentences are recorded only about once or twice**, and rarely by multiple Indian-accent speakers. It is a poor source for ≥4 Indian speakers per identical sentence, except for the pre-2019 duplicate-heavy sentence set.

### Cited Findings
- CV Scripted Speech 25.0 English, on Mozilla Data Collective (March 2026): 2,574,404 clips, 3,765.76 h (2,751.56 h validated), 99,724 speakers, 1,720,488 sentences. The "India and South Asia (India, Pakistan, Sri Lanka)" accent has 152,535 clips (5.9%) and 3,011 speakers (3.0%). — [MDC CV 25.0 English](https://prod.datacollective.mozillafoundation.org/datasets/cmndapwry02jnmh07dyo46mot) (search snippet; the page did not resolve in fetch); older release [CV 23.0 English](https://datacollective.mozillafoundation.org/datasets/cmflnuzw52mzok78yz6woemc1)
- Distribution has moved to Mozilla Data Collective, which requires an account and acceptance of terms; the corpus itself is CC0. — [MDC listing](https://datacollective.mozillafoundation.org/datasets/cmflnuzw52mzok78yz6woemc1)
- Duplicates: "A large proportion of the 880 hours of English are duplicate sentences recorded prior to Sentence Collector/Wikipedia import". — [Mozilla Discourse](https://discourse.mozilla.org/t/duplicate-sentences-during-validation/43286); see also [Discourse: multiple samples same text](https://discourse.mozilla.org/t/do-the-common-voice-datasets-contain-multiple-audio-samples-for-the-same-text-in-the-same-language/55215)

### Inferences
- Grouping is easy: `validated.tsv` has a `sentence` column plus `accents` and `client_id`. A groupby on sentence, filtered to Indian-accent speakers, will show quickly whether any early (pre-2019) sentences have ≥4 Indian speakers. Utterances are about 3–6 s, recorded on browsers and phones, so quality is mixed.
- Accent tags are self-reported and include Pakistan and Sri Lanka.

### Gaps
- I found no published per-sentence count of Indian-accent speakers. It must be computed from the TSVs.
- I could not confirm whether HF `mozilla-foundation/common_voice_*` mirrors are still current after the MDC move.

## Q6. Other AI4Bharat / Indic corpora (Kathbath, IndicSUPERB, IndicVoices, Shrutilipi, Vistaar, Lahaja, Nirantar, NPTEL, SPRING-INX), AccentDB, OpenSLR

### Takeaway
**Kathbath/IndicSUPERB explicitly has no repeated sentences.** The others are spontaneous, broadcast or lecture speech, or unverified. **AccentDB** is a small but genuinely parallel Indian-English set: 8 speakers across 4 L1s read the same Harvard sentences in a soundproof booth, under CC BY-NC 4.0. That makes it the second-best English option after the Speech Accent Archive. No OpenSLR Indian-English multi-speaker identical-prompt corpus was found.

### Cited Findings
- Kathbath: 1,684 h of read speech, 12 languages, 1,218 speakers, recorded on the Karya phone app. "Note that each utterance in the data is unique, i.e., a given sentence is only spoken by one speaker and never repeated again in the data." Sentences are 8–15 words from IndicCorp. — [IndicSUPERB paper arXiv:2208.11761](https://arxiv.org/pdf/2208.11761). Licence reported as CC BY-SA 4.0 (search snippet, not confirmed on the HF card) — [HF ai4bharat/Kathbath](https://huggingface.co/datasets/ai4bharat/Kathbath)
- AccentDB core: Bangla (2), Malayalam (3), Odiya (1) and Telugu (2) speakers, 8 in total. They read Harvard sentences: "a minimum of the same 25 sets across all 4 of the non-native accents". "Each set was repeated thrice". Recorded "inside a professionally-designed soundproof booth" with an Audio Technica AT2005USB and a Tascam DR-05. — [AccentDB paper](https://ar5iv.labs.arxiv.org/html/2005.07973)
- AccentDB licence: "CC BY-NC 4.0". accentdb_core is 2.8 GB (6,587 files); extended is 3.9 GB (19,111 files, 9 accents, with native accents compiled from other sources and 2 metropolitan Indian speakers). — [accentdb.org](https://accentdb.org/); also [TFDS accentdb](https://www.tensorflow.org/datasets/catalog/accentdb)
- IndicVoices: 7,348 h of "natural and spontaneous speech" from 16,237 speakers. IndicVoices-R: 1,704 h, 10,496 speakers, 22 languages (TTS-cleaned). — [IndicVoices-R arXiv](https://arxiv.org/pdf/2409.05356); [IndicVoices ACL](https://preview.aclanthology.org/dashboard/2024.findings-acl.639)
- Lahaja: 12.5 h of Hindi read and extempore speech from 132 speakers in 83 districts. — [datasets.ai4bharat.org/lahaja](https://datasets.ai4bharat.org/lahaja); [HF ai4bharat/Lahaja](https://huggingface.co/datasets/ai4bharat/Lahaja)
- Google crowdsourced OpenSLR corpora cover Gujarati, Kannada, Malayalam, Marathi, Tamil and Telugu, each with "at least 2,000 recorded lines from female and male native speakers". No Indian English set was found. — [Google LREC 2020](https://aclanthology.org/2020.lrec-1.800)

### Inferences
- AccentDB's Harvard sentences are about 2–3 s each, and the same 25 sets of 10 sentences are spoken by all 8 speakers, 3 times each. Concatenating one Harvard list (10 sentences) gives about 25–30 s. That yields 8 Indian-English speakers × 3 takes reading identical text in clean booth audio, which is very well suited to a consensus envelope despite the NC licence.
- Combined plan: use the **Speech Accent Archive** (one continuous passage, more than 170 Indian readers) as the primary set, and **AccentDB** plus **L2-ARCTIC Hindi** as clean, sentence-level identical-text sets. Common Voice and IndicTTS are fallbacks after verification.
- Hindi option: Kathbath, IndicVoices and Shrutilipi lack identical prompts. Lahaja's read portion might reuse prompts, but this is unverified.

### Gaps
- Not researched or verified in this pass, because of the tool budget: NPTEL2020 Indian English (lecture speech from YouTube, so likely spontaneous and not identical-text), Nirantar, Shrutilipi (All India Radio news, so broadcast with no repeated prompts per general knowledge), Vistaar (a benchmark aggregator), SPRING-INX (IIT Madras), the "Indic TIMIT" corpus (IIT/IISc), and Microsoft Indian-English corpora. No licence or prompt-sharing facts are claimed for these.
- Not verified: whether Lahaja's read prompts are shared across speakers.
- Not verified: AccentDB sample rate, and whether the HF or TFDS mirror keeps the sentence IDs. File names in the core version reportedly encode speaker and sentence index.
