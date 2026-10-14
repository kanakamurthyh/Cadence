# LibriVox / Internet Archive multi-reader recordings of Indian-authored or India-related texts (and Indian-named readers of the texts we already use)

Method note (applies to everything below): all reader counts, reader IDs, durations and MP3 URLs were pulled on 2026-10-14 straight from the LibriVox JSON API (`https://librivox.org/api/feed/audiobooks?id=<id>&format=json&extended=1`, `...?title=^<prefix>`, `...?author=<lastname>`) and from the AJAX endpoint that backs LibriVox author and reader pages (`https://librivox.org/{author|reader}/get_results?primary_key=<id>&search_category={author|reader}&search_page=N&search_order=alpha&project_type=either`). That endpoint needs the header `X-Requested-With: XMLHttpRequest`. Durations are the API `playtime` in seconds. The MP3 URL pattern is `https://www.archive.org/download/<ia_identifier>/<file>_64kb.mp3`. Replace `_64kb.mp3` with `_128kb.mp3` (in newer items) or with `.ogg` / `_vbr.mp3` per the IA item's file list. LibriVox states on every catalog page that "LibriVox recordings are Public Domain in the USA" ([LibriVox reader page](https://librivox.org/reader/3588)).

**Accent caveat:** the LibriVox forum, where readers introduce themselves, needs a login: anonymous fetches return "The board requires you to be registered and logged in" ([forum thread](https://forum.librivox.org/viewtopic.php?p=937822)). Reader profile pages show only a catalog name, forum name and an optional URL. Wherever these notes say "Indian-named", that is a guess from the name **only**. No accent was confirmed by listening.

## Q1. Which LibriVox projects cover Indian authors with ≥4 readers of the exact same short text?

### Takeaway
Three LibriVox Weekly Poetry projects by Indian authors have 14–17 distinct readers of one identical 1–2 min text:
- Tagore "XVIII" (Fruit-Gathering 18): 16 readers, 58–89 s. This is the best fit.
- Naidu "The Gift of India": 17 readers, 91–131 s. It runs a bit long.
- Tagore "The First Jasmines": 14 readers, 79–116 s.

"Where the Mind is Without Fear" (Gitanjali 35) has only 4 standalone readings, scattered across Short Poetry Collections, plus 1 embedded in the Gitanjali solo/group book. Three of those 4 readers have Indian names.

Items with no multi-reader version:
- **Single reading only:** Palanquin Bearers, Our Casuarina Tree, Kabir.
- **No LibriVox recording found:** "In the Bazaars of Hyderabad", Vivekananda's Chicago 1893 address, Nehru, and a multi-reader Gandhi speech.

### Cited Findings

**A. Tagore, "XVIII" (poem 18 of *Fruit-Gathering*, "No: it is not yours to open buds into blossoms…")**
- LibriVox Weekly Poetry project for 13 Feb 2022, 16 recordings — [LibriVox project](https://librivox.org/xviii-by-rabindranath-tagore/); [IA item xviii_2202.poem_librivox](https://archive.org/details/xviii_2202.poem_librivox)
- The 16 readers (reader_id, seconds):
  - KevinS (13278), 65
  - Lee Ann Howlett (1212), 68
  - Algy Pug (4705), 71
  - Patrick Randall (17124), 74
  - Larry Wilson (8425), 69
  - Bruce Kachuk (8786), 78
  - TriciaG (3157), 64
  - Newgatenovelist (9872), 89
  - Krista Zaleski (16999), 58
  - Matthew McNaughton (16521), 66
  - Greg Giordano (8011), 78
  - Adrian Stephens (13577), 73
  - Kerry Adams (16550), 85
  - David Lawrence (2911), 70
  - Patrick Wallace (6609), 75
  - LeeSalter (15365), 73
  
  Source: [LibriVox API id=17632](https://librivox.org/api/feed/audiobooks?id=17632&format=json&extended=1)
- File pattern: `https://www.archive.org/download/xviii_2202.poem_librivox/xviii_tagore_<initials>_64kb.mp3`. The initials used are ks, lah, alp, pr, lcw, bk, tg, el0, kz, mpm, gg, aps, kla, dl, pjw, ls — [LibriVox API id=17632](https://librivox.org/api/feed/audiobooks?id=17632&format=json&extended=1)
- Text source: Project Gutenberg #6522, *Fruit-Gathering*, section "XVIII". I checked the downloaded text: it begins "No: it is not yours to open buds into blossoms." — [PG 6522](https://www.gutenberg.org/ebooks/6522)
- No Indian-named readers among the 16 — [LibriVox API id=17632](https://librivox.org/api/feed/audiobooks?id=17632&format=json&extended=1)

**B. Sarojini Naidu, "The Gift of India"**
- Weekly Poetry project for 18 Apr 2021, 17 recordings — [LibriVox project](https://librivox.org/the-gift-of-india-by-sarojini-naidu/); [IA item the_gift_of_india_2104.poem_librivox](https://archive.org/details/the_gift_of_india_2104.poem_librivox)
- The 17 readers (reader_id, seconds):
  - altrin (15994), 131
  - Bruce Kachuk (8786), 131
  - Caitlin Buckley (9862), 91
  - David Lawrence (2911), 104
  - Elizabeth (16031), 122
  - Newgatenovelist (9872), 113
  - Ethan Meyer (15919), 109
  - Graham Scott (12484), 107
  - Lloyd Knight (15889), 100
  - Lisa Marie Dolcy (16136), 103
  - LeeSalter (15365), 106
  - Cavaet (14309), 93
  - Mayah (11247), 128
  - PalamonArcite (16134), 109
  - Phil Schempf (8576), 106
  - **Shantanu Santra (16124), 91**
  - TR Love (15829), 120
  
  Source: [LibriVox API id=16574](https://librivox.org/api/feed/audiobooks?id=16574&format=json&extended=1)
- Files: `https://www.archive.org/download/the_gift_of_india_2104.poem_librivox/india_naidu_<initials>_64kb.mp3`, e.g. `india_naidu_ss_64kb.mp3` (Shantanu Santra) — [LibriVox API id=16574](https://librivox.org/api/feed/audiobooks?id=16574&format=json&extended=1)
- Text source listed by LibriVox: a Digital Library of India scan, [archive.org in.ernet.dli.2015.95756](https://archive.org/details/in.ernet.dli.2015.95756/page/n25/mode/2up)
- Shantanu Santra's profile lists 1 section and 1 project (this one); forum name "santras"; no URL — [LibriVox reader 16124](https://librivox.org/reader/16124)
- "altrin" is not Indian-named: the forum name is "ArthurTrinchera" — [LibriVox reader 15994](https://librivox.org/reader/15994)

**C. Tagore, "The First Jasmines" (from *The Crescent Moon*)**
- Weekly Poetry project with 14 recordings — [LibriVox project](https://librivox.org/the-first-jasmines-by-rabindranath-tagore/); [LibriVox API id=9888](https://librivox.org/api/feed/audiobooks?id=9888&format=json&extended=1)
- The 14 readers (reader_id, seconds):
  - Andrew Coleman (2854), 116
  - Algy Pug (4705), 85
  - Bruce Kachuk (8786), 95
  - David Lawrence (2911), 85
  - Newgatenovelist (9872), 97
  - Greg Giordano (8011), 101
  - Ian King (7785), 93
  - J. McDougall (9902), 81
  - Lee Ann Howlett (1212), 79
  - Leonard Wilson (4738), 112
  - Maria Kasper (8051), 99
  - NoelBadrian (6965), 86
  - Peter Yearsley (167), 96
  - Rosslyn Carlyle (9331), 106
  
  Source: [LibriVox API id=9888](https://librivox.org/api/feed/audiobooks?id=9888&format=json&extended=1)
- Files: `firstjasmines_tagore_<initials>_64kb.mp3` — same source
- Text: PG #6520, *The Crescent Moon*, section "THE FIRST JASMINES" ("Ah, these jasmines, these white jasmines!") — [PG 6520](https://www.gutenberg.org/ebooks/6520)
- No Indian-named readers.

**D. Tagore, "Where the Mind is Without Fear" (Gitanjali 35)**

There is no weekly multi-reader project. Separate readings exist in Short Poetry Collections (SPC) — [LibriVox author page Tagore, id 568](https://librivox.org/author/568):
- SPC 090, section 30: **Sowmya** (5693), 72 s — `https://www.archive.org/download/short_poetry_090_librivox/wherethemind_tagore_sr_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-collection-090-by-various/)
- SPC 094, section 36: **Aparna Vishwanatham** (5842), 60 s — `https://www.archive.org/download/short_poetry_094_librivox/wherethemindiswithoutfear_tagore_av_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-094/)
- SPC 125, section 26: dsilber01 (8705), 62 s — `https://www.archive.org/download/shortpoetry125_1310_librivox/spc125_wherethemindiswithoutfear_dss_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-collection-125/)
- SPC 274, section 39: **Leena Manohar** (20633), 67 s — `https://www.archive.org/download/spc274_2604_librivox/spc274_wherethemindiswithoutfear_lm_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-collection-274-by-various/)
- Also inside the group *Gitanjali* recording, "Verses 31 to 40", read by Elli (3885) in a 413 s file. It would have to be cut out by hand. In the Dialect collection, Elli self-labels as "Austrian accent (German)" — [LibriVox API id=3745](https://librivox.org/api/feed/audiobooks?id=3745&format=json&extended=1); [Dialect Vol 1 API id=3445](https://librivox.org/api/feed/audiobooks?id=3445&format=json&extended=1)
- Text: PG #7164 *Gitanjali*, poem "35." ("Where the mind is without fear and the head is held high; …") — [PG 7164](https://www.gutenberg.org/ebooks/7164); the LibriVox project cites [Wikisource Gitanjali](https://en.wikisource.org/wiki/Gitanjali)
- Leena Manohar's profile links to a YouTube channel ([LibriVox reader 20633](https://librivox.org/reader/20633)). The channel's About text mentions "Hidden India" among its topics ([YouTube @LeenaManoharVoice](http://www.youtube.com/@LeenaManoharVoice)). That is weak evidence of an Indian link.
- Sowmya: 1 project; Aparna Vishwanatham: 4 projects. Neither profile has a URL — [reader 5693](https://librivox.org/reader/5693); [reader 5842](https://librivox.org/reader/5842)

**E. Other Tagore and Gitanjali items, all single-reader**
- "Verse 48 from Gitanjali" (dc, 136 s) and Vivekananda's "Song of the Sannyasin" (dc, 328 s), both in SPC 223 — [LibriVox project](https://librivox.org/short-poetry-collection-223-by-various/)
- The *Gitanjali* group book (3745): readers are Neeru Iyer (Introduction, Verses 1–10), Hilara, Elli, lonely trotter, Patti Cunningham, Carl Manchester and Sean Michael Hogan, each reading blocks of 10 verses — [LibriVox API id=3745](https://librivox.org/api/feed/audiobooks?id=3745&format=json&extended=1)

**F. Sarojini Naidu, *The Golden Threshold* (group project, one reader per poem)**
- "Palanquin Bearers" has one reader: Vann Lantz, 57 s — [LibriVox API id=8472](https://librivox.org/api/feed/audiobooks?id=8472&format=json&extended=1)
- Indian-named readers in the book:
  - Zeeshan Reshamwala (9084): Village-Song through Autumn Song
  - Anusha Iyer (9063): Ode to the Nizam, Leili, Indian Dancers, Nightfall in the City of Hyderabad, Street Cries, To India, and others
  - Source: [LibriVox API id=8472](https://librivox.org/api/feed/audiobooks?id=8472&format=json&extended=1)
- Text: PG #680 — [PG 680](https://www.gutenberg.org/ebooks/680)
- Other Naidu poems appear only as single readings in SPCs: Ecstasy, My Dead Dream, Past and Future, The Soul's Prayer (2 readings, SPC 149 and SPC 175), To a Buddha…, To the God of Pain, Transience — [LibriVox author 3569](https://librivox.org/author/3569)
- The LibriVox API returned nothing for "In the Bazaars of Hyderabad" (title or author search) — [LibriVox API](https://librivox.org/api/feed/audiobooks?author=Naidu&format=json)

**G. Toru Dutt, "Our Casuarina Tree"**
- Single reading by Rosslyn Carlyle (9331), 234 s, section 20 of *Ancient Ballads and Legends of Hindustan* — [LibriVox project](https://librivox.org/ancient-ballads-and-legends-of-hindustan-by-toru-dutt/); [IA](https://archive.org/details/ancient_ballads_legends_hindustan_1501_librivox)
- Text: [PG 23245](https://www.gutenberg.org/ebooks/23245)

**H. Vivekananda, Gandhi, Kabir, Aurobindo**
- Vivekananda (author 1306) has only single readings in compilations: "Hold On Yet A While, Brave Heart", "Peace", "Song of the Sannyasin", "The Cup", "The Ideal of a Universal Religion", and Lecture 5 in the 8th Anniversary Collection. **No Chicago 1893 address** — [LibriVox author 1306](https://librivox.org/author/1306)
- Separately, the claim that an audio recording of Vivekananda's 1893 Chicago speech exists has been investigated and rejected — [Wikipedia](https://en.wikipedia.org/wiki/Swami_Vivekananda_at_the_Parliament_of_the_World%27s_Religions); [Belur Math media](https://media.belurmath.org/clarification-on-swami-vivekanandas-voice-recording-swami-suvirananda-video-6719/)
- Gandhi (author 622) has only book-length projects: Freedom's Battle, Guide to Health, Hind Swaraj, Third Class in Indian Railways — [LibriVox author 622](https://librivox.org/author/622)
- Kabir: *Songs of Kabir* is a solo by Algy Pug in 3 long files, plus 2 Hindi readings in Multilingual Short Works 039 and 040 — [LibriVox author 917](https://librivox.org/author/917)
- Aurobindo: 1 single reading ("Love and Death", SPC 254) — [LibriVox author 18599](https://librivox.org/author/18599)
- Nehru: the API returned no author match — [LibriVox API](https://librivox.org/api/feed/audiobooks?author=Nehru&format=json)

**I. India-themed (not Indian-authored) Weekly and Fortnightly projects by Laurence Hope (Adela Nicolson), with Indian-named readers**

All texts come from PG #5125 or #8197 (*India's Love Lyrics* / *The Garden of Kama*) — [LibriVox author 10161](https://librivox.org/author/10161)
- **The Hut**: 12 readers, 49–77 s. Includes Garfield Dsouza (14214) and RajVO (12236) — [project](https://librivox.org/the-hut-by-laurence-hope/); [IA](https://archive.org/details/the_hut_2204.poem_librivox)
- **Among the Rice Fields**: 22 readers, 56–89 s. Includes Asha (14638) and Edmond Aggabao — [project](https://librivox.org/among-the-rice-fields-by-laurence-hope/); [IA](https://archive.org/details/among_the_rice_fields_2008.poem_librivox)
- **Unanswered**: 19 readers, 71–112 s. Includes AfsanaA (17861) — [project](https://librivox.org/unanswered-by-laurence-hope/); [IA](https://archive.org/details/unanswered_2209.poem_librivox)
- **Starlight**: 22 readers, 50–98 s. Includes dc (16764), forum name "dckabir" — [project](https://librivox.org/starlight-by-laurence-hope/); [IA](https://archive.org/details/starlight_2210.poem_librivox)
- **Kashmiri Song** ("Pale hands I loved…"): 15 readers, 59–83 s. No Indian-named readers — [project](https://librivox.org/kashmiri-song-by-laurence-hope/); [IA](https://archive.org/details/kashmiri_song_1508.poem_librivox)
- **The Jungle Flower**: 13 readers, 61–103 s. No Indian-named readers — [project](https://librivox.org/the-jungle-flower-by-laurence-hope/)
- **Kotri, by the River**: 15 readers, but 143–254 s, which is too long. Includes jdsouza27 (14400) and Tasleem Khan (4610) — [project](https://librivox.org/kotri-by-the-river-by-laurence-hope/)
- **Shivratri**: 14 readers, 89–132 s — [project](https://librivox.org/shivratri-the-night-of-shiva-by-laurence-hope/)

**J. Kipling's India poems**
- Only scattered SPC single readings: Gunga Din (SPC 004, 085, 104, 133, 205), Mandalay (SPC 076, 224), The Ballad of East and West (SPC 111, 233), Recessional (SPC 265) — [LibriVox author 144](https://librivox.org/author/144)

### Inferences
- If the goal is ≥6 readers of one exact 30–90 s Indian-authored text, Tagore "XVIII" (16 readers, all ≤89 s) is the top candidate. "The First Jasmines" (14 readers, mostly 79–116 s) comes second. "The Gift of India" (17 readers) runs 91–131 s. Its 2 stanzas could be trimmed to one, but that needs forced alignment.
- None of the big Indian-author weekly projects gives accent diversity: only 1 possibly-Indian reader (Shantanu Santra) appears across those 47 readings.
- "Where the Mind is Without Fear" is the most Indian-accent-rich option: 3 of 4 standalone readers have Indian names. It still falls short of the ≥6-reader consensus target. It could serve as a held-out "Indian reader" probe text if a non-Indian reference envelope is built elsewhere, but with n≈5 the envelope would be thin.
- The Laurence Hope weeklies give India-themed texts with 12–22 readers and short durations. A few have Indian-named readers. The Hut (12 readers, 49–77 s, 2 Indian-named) is the best of these.

### Gaps
- No reader's accent was verified. Forum self-introductions need a login, so a human should listen to each file, or an accent-ID model (for example a CommonAccent ECAPA model) should be run before any reader is counted as "Indian-accented".
- dsilber01's and dc's backgrounds are unknown.

## Q2. Are any readers Indian or Indian-accented? How many?

### Takeaway
I found no Indian accent that a reader has self-declared on LibriVox. Both "Celebration of Dialects and Accents" volumes (35 and 20 self-labelled readers) contain no Indian or South Asian label.

By name only (unverified), these readers look Indian or South Asian:
- **Reads short multi-reader texts that matter here:** RajVO, Leena Manohar, Sowmya, Aparna Vishwanatham, Shantanu Santra, K. H. Atole, Garfield Dsouza.
- **Reads long-form only:** Anusha Iyer, Neeru Iyer, Zeeshan Reshamwala.
- **Possible, in Hope weeklies:** Asha, AfsanaA, jdsouza27, Tasleem Khan.

### Cited Findings
- **Dialect collections, no Indian accent:**
  - *Celebration of Dialects and Accents, Vol 1* is "The North Wind and the Sun", 35 readers, each with a self-described accent label. The labels include Flemish, Irish, Australian, RP, Austrian, Hungarian, Dutch, Chinese (Taiwan), Chinese (Singaporean), French and many US/UK regional accents. None is Indian — [LibriVox API id=3445](https://librivox.org/api/feed/audiobooks?id=3445&format=json&extended=1); [IA dialect_accent_0909_librivox](https://archive.org/details/dialect_accent_0909_librivox)
  - Vol 2 has 20 readers (text source PG #21, Aesop) with US, UK, Australian, German, Austrian, Dutch and Hungarian labels. None is Indian — [LibriVox project](https://librivox.org/celebration-of-dialects-and-accents-vol-2-by-aesop/); [IA](https://archive.org/details/celebration_dialects_accents_vol2_1312_librivox)
- **RajVO (12236):** 141 sections across 113 projects, almost all Weekly or Fortnightly Poetry. No profile URL or bio — [LibriVox reader 12236](https://librivox.org/reader/12236). A web search turned up no biography. The name "Raj" alone is weak evidence.
- **Neeru Iyer (3588):** forum name "neerajanagarajan". The profile URL is neeruscribbles.blogspot.com, which needs a login — [LibriVox reader 3588](https://librivox.org/reader/3588). A Goodreads author page describes a Neeru Iyer as a writer born in Chennai — [Goodreads](https://www.goodreads.com/author/show/13955703?tab=author). I could not confirm this is the same person.
- **Neeru Iyer's weekly poems:** When You Are Old (Yeats; 29 readers, her file 57 s), Snow-Flakes (Longfellow; 21 readers, 60 s), Winter (Shakespeare; 16 readers, 62 s), Lines (Shelley; 14 readers, 78 s), Pillow and Stone (13 readers, 53 s) — [IA when_you_are_old_1001_librivox](https://www.archive.org/details/when_you_are_old_1001_librivox); [IA snow-flakes_0912_librivox](https://www.archive.org/details/snow-flakes_0912_librivox)
- **Anusha Iyer (9063):** profile URL soundcloud.com/anusha-ramasubramoney. 679 sections, mostly collaborative poetry books, no weekly projects — [LibriVox reader 9063](https://librivox.org/reader/9063)
- **Garfield Dsouza (14214):** forum name "quasimoir", 38 projects, about 18 of them Weekly or Fortnightly Poetry (e.g. The Hut, The Broken Oar, Sleep Is Supposed To Be) — [LibriVox reader 14214](https://librivox.org/reader/14214)
- **Tasleem Khan (4610):** forum name "voiceartistmedia", 12 fortnightly or weekly poems, including The Charge of the Light Brigade, A Visit From Saint Nicholas and The Spell of the Yukon — [LibriVox reader 4610](https://librivox.org/reader/4610)
- **K. H. Atole (13800):** forum name "atole", 5 projects, including Kipling "The Winners" (fortnightly) and "If" in SPC 274 — [LibriVox reader 13800](https://librivox.org/reader/13800)
- **dc (16764):** forum name "dckabir", 768 sections across 280 projects. Read Gitanjali 48, Song of the Sannyasin and "If" (SPC 273) — [LibriVox reader 16764](https://librivox.org/reader/16764). The Indian link is speculative; it rests only on the forum name.
- **A non-Indian accent on an Indian text:** Elli, who read Gitanjali 31–40 including "Where the Mind", self-labels as "Austrian accent (German)" — [LibriVox API id=3445](https://librivox.org/api/feed/audiobooks?id=3445&format=json&extended=1)
- **Context from forum search snippets (I could not open the forum):** LibriVox has Indian volunteers, for example from Chennai and New Delhi. One reader is described as "RP with some light Malaysian Indian notes" — [LibriVox forum (login-gated)](https://forum.librivox.org/viewtopic.php?p=937822); [forum](https://forum.librivox.org/viewtopic.php?p=1909216)

### Inferences
- **Strongest bet:** RajVO, because of the sheer volume of weekly poems (roughly 100 Weekly/Fortnightly projects with 7–28 readers each), so every weekly text RajVO read already has a consensus pool. If a listening check confirms an Indian accent, RajVO alone adds one Indian reading to around 100 multi-reader texts at no transcription cost. Examples:
  - The Arrow and the Song: 27 readers, 59 s
  - The Solitary: 24 readers, 63 s
  - The Panther: 23 readers, 67 s
  - Lines on a New-Born Infant: 22 readers, 90 s
  - The Eagle: 21 readers, 37 s
  - A Wish: 21 readers, 74 s
  - Contrasts: 21 readers, 65 s
  - The Lost Lagoon: 21 readers, 68 s
  - To the Fringed Gentian: 21 readers, 77 s
  - Comfort to a Youth: 21 readers, 64 s
  
  Files follow the pattern `<slug>_<author>_raj_64kb.mp3` under each `*.poem_librivox` IA item. Source: [LibriVox reader 12236](https://librivox.org/reader/12236), with project lists and section counts taken from the API.
- **Second tier:** Garfield Dsouza (about 18 weeklies) and Neeru Iyer (5 weeklies, including Yeats "When You Are Old" with 29 readers).

### Gaps
- No accent has been verified. Recommended next step: download one 60 s file per candidate (RajVO, Garfield Dsouza, Neeru Iyer, Leena Manohar, Sowmya, Aparna Vishwanatham, Shantanu Santra, K. H. Atole, Tasleem Khan, dc) and have a human or an accent classifier label them. That step is cheap and decisive.
- A reader could be Indian and still have a non-Indian accent (diaspora), or the reverse. The name heuristic cannot settle this.

## Q3. Do Indian-named readers appear in the texts we already use (Sea Fever, Stopping by Woods, Gettysburg Address, Kipling "If—")?

### Takeaway
Two texts are covered:
- **"If":** 3 Indian-named readings: RajVO in the 28-reader fortnightly project, K. H. Atole in SPC 274 and Leena Manohar in SPC 275.
- **Sea Fever, Stopping by Woods and Gettysburg:** I found no Indian-named reader in any LibriVox instance.

### Cited Findings
- **Kipling "IF", Fortnightly Poetry project, 28 readers:** includes **RajVO (12236), 140 s**, `https://archive.org/download/if_1808.poem_librivox/if_kipling_raj_64kb.mp3`. The other 27 readers are April6090, Angelique G. Campbell, Bruce Kachuk, Beth Thomas, Erin B. Lillis, Ellies, Newgatenovelist, Eva Staes, Fenman, Foon, Garth Burton, Greg Giordano, Graham Scott, Ian King, Kristin G., Larry Wilson, Michael Fassio, Matthew M. Benzing, Mark Ernest, Michele Fry, Nan Dodge, Nemo, Phil Chenevert, Scotty Smith, Tomas Peter, tovarisch and William Allan Jones — [LibriVox API id=13211](https://librivox.org/api/feed/audiobooks?id=13211&format=json&extended=1); [IA](https://archive.org/details/if_1808.poem_librivox)
- **Kipling "If", 2006 weekly, 17 readers:** none Indian-named — [LibriVox API id=188](https://librivox.org/api/feed/audiobooks?id=188&format=json&extended=1)
- **"If" in Short Poetry Collections:**
  - **K. H. Atole (13800), 107 s:** `https://www.archive.org/download/spc274_2604_librivox/spc274_if_kha_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-collection-274-by-various/)
  - **Leena Manohar (20633), 143 s:** `https://www.archive.org/download/spc275_2605_librivox/spc275_if_lm_64kb.mp3` — [LibriVox project](https://librivox.org/short-poetry-collection-275-by-various/)
  - dc (16764), 135 s, SPC 273 — [LibriVox project](https://librivox.org/short-poetry-collection-273-by-various/)
  - Other SPC "If" readers, none Indian-named: SPC 011, 020, 029, 051, 096, 101, 125, 221, 226, 228, 248, 253 and 267 — [LibriVox author 144](https://librivox.org/author/144)
- **Sea Fever:**
  - The weekly project has 24 readers, none Indian-named — [LibriVox API id=1452](https://librivox.org/api/feed/audiobooks?id=1452&format=json&extended=1)
  - 6 extra single readings, also none Indian-named: SPC 070 (JDV), SPC 180 (Winston Tharp), SPC 214 (Adam Saunders), SPC 215 (Caleb Mann), SPC 264 (MexIrishBrian) and Coffee Break 025 (William Allan Jones) — [LibriVox author 722](https://librivox.org/author/722)
- **Stopping by Woods:**
  - The fortnightly project has 23 readers, none Indian-named — [LibriVox API id=13668](https://librivox.org/api/feed/audiobooks?id=13668&format=json&extended=1)
  - Extra readings: SPC 207 (Ethan) and SPC 254 (Yaron Bernstein) — [LibriVox author 338](https://librivox.org/author/338)
- **Gettysburg Address:**
  - The 150th Anniversary collection has 15 readers, none Indian-named — [LibriVox API id=8387](https://librivox.org/api/feed/audiobooks?id=8387&format=json&extended=1)
  - Solo versions 1–4: Shurtagal, John Greenman, Mark F. Smith, Jim Cadwell.
  - In compilations: Short Nonfiction 027 (Daniel Vimont), 048 (Esther Kamas), 076 (MaybeCordelia) and 099 (Al Marzel, under the title "Dedication of the Cemetery at Gettysburg"), plus US Historical Documents (Michael Scherer).
  - That makes **about 24 distinct LibriVox Gettysburg readings** in all, none Indian-named — [LibriVox author 2233](https://librivox.org/author/2233)

### Inferences
- "If" (PG 15529, already transcribed) can take up to 3 possibly-Indian readings against a pool of 28 + 17 + about 15 others, with no new transcription. The catch is length: at 107–143 s these readings run past the 90 s window, so they would need to be cut at a stanza boundary with the same cut applied to every reader.
- The extra Gettysburg readings found in compilations (about 9 beyond the 15-reader collection) and the 6 extra Sea Fever readings enlarge the consensus pools, though not their accent diversity.

### Gaps
- I did not check the "Multilingual"/anniversary collections or Dramatic Readings for more readings of these four texts. Nor did I check whether Indian-named readers read these texts outside LibriVox (e.g. on IA community audio, which may not be CC0).
