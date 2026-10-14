"""The three texts of the benchmark (spec section 8).

T1 is calibration only (thresholds, lambda, severity mapping); T2-T5 are held-out test.
Every text is public domain in the US; every recording's licence is stored per file. T3 is the closing paragraph of the
Gettysburg Address: no recording of the original orator exists, so its envelope
is built from LibriVox readers and teammate takes (see README, deviations).
"""

TEXTS = {
    "T1": {
        "title": "Sea Fever",
        "author": "John Masefield (1902)",
        "role": "calibration",
        "librivox_ids": [1452],
        "text": (
            "I must go down to the seas again, to the lonely sea and the sky, "
            "And all I ask is a tall ship and a star to steer her by, "
            "And the wheel's kick and the wind's song and the white sail's shaking, "
            "And a grey mist on the sea's face, and a grey dawn breaking. "
            "I must go down to the seas again, for the call of the running tide "
            "Is a wild call and a clear call that may not be denied; "
            "And all I ask is a windy day with the white clouds flying, "
            "And the flung spray and the blown spume, and the sea-gulls crying. "
            "I must go down to the seas again, to the vagrant gypsy life, "
            "To the gull's way and the whale's way where the wind's like a whetted knife; "
            "And all I ask is a merry yarn from a laughing fellow-rover, "
            "And quiet sleep and a sweet dream when the long trick's over."
        ),
    },
    "T2": {
        "title": "Stopping by Woods on a Snowy Evening",
        "author": "Robert Frost (1923)",
        "role": "test",
        "librivox_ids": [13668],
        "text": (
            "Whose woods these are I think I know. His house is in the village though; "
            "He will not see me stopping here To watch his woods fill up with snow. "
            "My little horse must think it queer To stop without a farmhouse near "
            "Between the woods and frozen lake The darkest evening of the year. "
            "He gives his harness bells a shake To ask if there is some mistake. "
            "The only other sound's the sweep Of easy wind and downy flake. "
            "The woods are lovely, dark and deep, But I have promises to keep, "
            "And miles to go before I sleep, And miles to go before I sleep."
        ),
    },
    "T3": {
        "title": "Gettysburg Address (closing paragraph)",
        "author": "Abraham Lincoln (1863)",
        "role": "test-oratory",
        "librivox_ids": [8387, 389, 390, 1157, 1293],
        "text": (
            "But, in a larger sense, we can not dedicate, we can not consecrate, "
            "we can not hallow this ground. The brave men, living and dead, who struggled "
            "here, have consecrated it, far above our poor power to add or detract. "
            "The world will little note, nor long remember what we say here, but it can "
            "never forget what they did here. It is for us the living, rather, to be "
            "dedicated here to the unfinished work which they who fought here have thus "
            "far so nobly advanced. It is rather for us to be here dedicated to the great "
            "task remaining before us, that from these honored dead we take increased "
            "devotion to that cause for which they gave the last full measure of devotion, "
            "that we here highly resolve that these dead shall not have died in vain, "
            "that this nation, under God, shall have a new birth of freedom, and that "
            "government of the people, by the people, for the people, shall not perish "
            "from the earth."
        ),
    },
    "T4": {
        "title": "Gettysburg Address (opening paragraph)",
        "author": "Abraham Lincoln (1863)",
        "role": "test-oratory",
        # same 19 LibriVox readings as T3 (different passage): no new download.
        # T3 and T4 share speakers; both are held out, neither touches calibration.
        "reuse_raw": "T3",
        "span_rule": 2,
        "librivox_ids": [],
        "text": (
            "Four score and seven years ago our fathers brought forth on this continent, "
            "a new nation, conceived in Liberty, and dedicated to the proposition that all "
            "men are created equal. Now we are engaged in a great civil war, testing whether "
            "that nation, or any nation so conceived and so dedicated, can long endure. We are "
            "met on a great battle-field of that war. We have come to dedicate a portion of that "
            "field, as a final resting place for those who here gave their lives that that "
            "nation might live. It is altogether fitting and proper that we should do this."
        ),
    },
    "T5": {
        "title": "Day of Infamy address (opening)",
        "author": "Franklin D. Roosevelt (1941)",
        "role": "test-oratory",
        "librivox_ids": [],
        "span_rule": 2,
        # Original orator + one LibriVox reading. The envelope needs >= 4 renditions, so
        # T5 stays out of ladders and evaluation until teammate takes are added to
        # data/raw/T5/ (see docs/human_data_protocol.md).
        "sources": [
            {"id": "fdr_original_1941", "speaker": "Franklin D. Roosevelt (original orator)",
             "url": "https://upload.wikimedia.org/wikipedia/commons/f/fd/Roosevelt_Pearl_Harbor.ogg",
             "page": "https://commons.wikimedia.org/wiki/File:Roosevelt_Pearl_Harbor.ogg",
             "licence": "Public domain (US federal government work; Wikimedia Commons PD, Copyrighted=False)",
             "provenance": "NARA record https://catalog.archives.gov/id/10611614 (recording: John G. Bradley); "
                           "NARA lists the speech as Unrestricted; Commons sha1 90239988a1fc36a44f6531207c918544980bfea0",
             "sha1": "90239988a1fc36a44f6531207c918544980bfea0"},
            {"id": "lv_snf064_04_lcw", "speaker": "LibriVox reader 'lcw' (Short Nonfiction Collection Vol. 064, section 4)",
             "url": "https://archive.org/download/nonfiction064_1904_librivox/snf064_dayofinfamy_roosevelt_lcw_64kb.mp3",
             "page": "https://archive.org/details/nonfiction064_1904_librivox",
             "licence": "Public Domain Mark 1.0 (LibriVox)",
             "provenance": "archive.org item nonfiction064_1904_librivox, file snf064_dayofinfamy_roosevelt_lcw_64kb.mp3"},
        ],
        "text": (
            "Mister Vice President, Mister Speaker, Members of the Senate, and of the House of "
            "Representatives: Yesterday, December seventh, nineteen forty-one, a date which will "
            "live in infamy, the United States of America was suddenly and deliberately attacked "
            "by naval and air forces of the Empire of Japan. The United States was at peace with "
            "that nation and, at the solicitation of Japan, was still in conversation with its "
            "Government and its Emperor looking toward the maintenance of peace in the Pacific."
        ),
    },

    "T6": {
        "title": "If- (first two stanzas)",
        "author": "Rudyard Kipling (1910)",
        # Untouched final test, added 2026-10-14 AFTER the v2 detector was frozen. Built and
        # evaluated once; never used to choose or tune anything.
        "role": "test-final",
        "librivox_ids": [188],
        "span_rule": 2,
        "text": (
            "If you can keep your head when all about you Are losing theirs and blaming it on you, "
            "If you can trust yourself when all men doubt you, But make allowance for their doubting too; "
            "If you can wait and not be tired by waiting, Or being lied about, don't deal in lies, "
            "Or being hated, don't give way to hating, And yet don't look too good, nor talk too wise: "
            "If you can dream, and not make dreams your master; If you can think, and not make thoughts "
            "your aim; If you can meet with Triumph and Disaster And treat those two impostors just the "
            "same; If you can bear to hear the truth you've spoken Twisted by knaves to make a trap for "
            "fools, Or watch the things you gave your life to, broken, And stoop and build 'em up with "
            "worn-out tools:"
        ),
    },

    # T7 and T8 added 2026-10-14 (session 10) AFTER detector v3 was designed; held out,
    # never used for calibration or threshold tuning.
    "T7": {
        "title": "Please call Stella (Speech Accent Archive)",
        "author": "GMU Speech Accent Archive elicitation paragraph",
        "role": "test-indian",
        "librivox_ids": [],
        "span_rule": 2,
        "text": (
            "Please call Stella. Ask her to bring these things with her from the store: "
            "Six spoons of fresh snow peas, five thick slabs of blue cheese, and maybe a snack "
            "for her brother Bob. We also need a small plastic snake and a big toy frog for the "
            "kids. She can scoop these things into three red bags, and we will go meet her "
            "Wednesday at the train station."
        ),
        "sources": [
            {
                "id": "saa_hindi1",
                "url": "https://accent.gmu.edu/audio/hindi1.mp3",
                "page": "https://accent.gmu.edu/samples/hindi1/",
                "speaker": "SAA hindi1 (Hindi L1, born Nagpur, Maharashtra, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/hindi1/",
                "sha1": "06d8877de0cf80c2ac743605c82dc0fe789059b0",
                "meta": {"l1": "hindi", "birthplace": "nagpur, maharashtra, india", "sex": "male", "age": 27, "english_onset_age": 2},
            },
            {
                "id": "saa_hindi2",
                "url": "https://accent.gmu.edu/audio/hindi2.mp3",
                "page": "https://accent.gmu.edu/samples/hindi2/",
                "speaker": "SAA hindi2 (Hindi L1, born Hyderabad, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/hindi2/",
                "sha1": "6452982dbb92256683f7718c40b5b905b615aabe",
                "meta": {"l1": "hindi", "birthplace": "hyderabad, india", "sex": "male", "age": 31, "english_onset_age": 3},
            },
            {
                "id": "saa_bengali6",
                "url": "https://accent.gmu.edu/audio/bengali6.mp3",
                "page": "https://accent.gmu.edu/samples/bengali6/",
                "speaker": "SAA bengali6 (Bengali L1, born Jamshedpur, Jharkhand, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/bengali6/",
                "sha1": "4f84240ec2a8413c22d42de1246a0f136c92a3b0",
                "meta": {"l1": "bengali", "birthplace": "jamshedpur, jharkhand, india", "sex": "male", "age": 29, "english_onset_age": 4},
            },
            {
                "id": "saa_bengali9",
                "url": "https://accent.gmu.edu/audio/bengali9.mp3",
                "page": "https://accent.gmu.edu/samples/bengali9/",
                "speaker": "SAA bengali9 (Bengali L1, born Kolkata, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/bengali9/",
                "sha1": "313499b90fdfa6cc9d7650efb892ecc8f8e00139",
                "meta": {"l1": "bengali", "birthplace": "kolkata, india", "sex": "female", "age": 61, "english_onset_age": 12},
            },
            {
                "id": "saa_telugu1",
                "url": "https://accent.gmu.edu/audio/telugu1.mp3",
                "page": "https://accent.gmu.edu/samples/telugu1/",
                "speaker": "SAA telugu1 (Telugu L1, born Kadapa, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/telugu1/",
                "sha1": "f880839365e0484f4ccf7093ead6f6bf71f7997c",
                "meta": {"l1": "telugu", "birthplace": "kadapa, india", "sex": "male", "age": 31, "english_onset_age": 6},
            },
            {
                "id": "saa_telugu2",
                "url": "https://accent.gmu.edu/audio/telugu2.mp3",
                "page": "https://accent.gmu.edu/samples/telugu2/",
                "speaker": "SAA telugu2 (Telugu L1, born Guntur, Andhra Pradesh, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/telugu2/",
                "sha1": "fc842e7ed9b72b0d94dfbf1f0229a0522ae84c55",
                "meta": {"l1": "telugu", "birthplace": "guntur, andhra pradesh, india", "sex": "male", "age": 18, "english_onset_age": 6},
            },
            {
                "id": "saa_tamil2",
                "url": "https://accent.gmu.edu/audio/tamil2.mp3",
                "page": "https://accent.gmu.edu/samples/tamil2/",
                "speaker": "SAA tamil2 (Tamil L1, born Madras, Tamil Nadu, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/tamil2/",
                "sha1": "c184bd75002d8e815b1fe0f454020f5df2011a03",
                "meta": {"l1": "tamil", "birthplace": "madras, tamil nadu, india", "sex": "female", "age": 35, "english_onset_age": 4},
            },
            {
                "id": "saa_tamil5",
                "url": "https://accent.gmu.edu/audio/tamil5.mp3",
                "page": "https://accent.gmu.edu/samples/tamil5/",
                "speaker": "SAA tamil5 (Tamil L1, born Coimbatore, Tamil Nadu, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/tamil5/",
                "sha1": "b97eb0be43036736fb070f92da1056069a0f3ab1",
                "meta": {"l1": "tamil", "birthplace": "coimbatore, tamil nadu, india", "sex": "female", "age": 36, "english_onset_age": 5},
            },
            {
                "id": "saa_marathi1",
                "url": "https://accent.gmu.edu/audio/marathi1.mp3",
                "page": "https://accent.gmu.edu/samples/marathi1/",
                "speaker": "SAA marathi1 (Marathi L1, born Bombay, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/marathi1/",
                "sha1": "5b255fa2cfe8f8b74bb4d990525fb96f9d94e556",
                "meta": {"l1": "marathi", "birthplace": "bombay, india", "sex": "female", "age": 21, "english_onset_age": 3},
            },
            {
                "id": "saa_marathi2",
                "url": "https://accent.gmu.edu/audio/marathi2.mp3",
                "page": "https://accent.gmu.edu/samples/marathi2/",
                "speaker": "SAA marathi2 (Marathi L1, born Madras, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/marathi2/",
                "sha1": "838cd7add3663371db9d67c331f0b477722881f7",
                "meta": {"l1": "marathi", "birthplace": "madras, india", "sex": "male", "age": 28, "english_onset_age": 10},
            },
            {
                "id": "saa_malayalam1",
                "url": "https://accent.gmu.edu/audio/malayalam1.mp3",
                "page": "https://accent.gmu.edu/samples/malayalam1/",
                "speaker": "SAA malayalam1 (Malayalam L1, born Kerala State, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/malayalam1/",
                "sha1": "fce7cafe68ecd491c728fd3275a8ad222a65b82f",
                "meta": {"l1": "malayalam", "birthplace": "kerala state, india", "sex": "male", "age": 24, "english_onset_age": 5},
            },
            {
                "id": "saa_malayalam2",
                "url": "https://accent.gmu.edu/audio/malayalam2.mp3",
                "page": "https://accent.gmu.edu/samples/malayalam2/",
                "speaker": "SAA malayalam2 (Malayalam L1, born Trivandrum, Kerala, India)",
                "licence": "CC BY-NC-SA 4.0 (Speech Accent Archive, George Mason University; https://accent.gmu.edu/howto/)",
                "provenance": "Speech Accent Archive, Weinberger & Kelley, GMU; speaker page https://accent.gmu.edu/samples/malayalam2/",
                "sha1": "f95a6da139aa2f7e78ccd632dc1ad629fed439eb",
                "meta": {"l1": "malayalam", "birthplace": "trivandrum, kerala, india", "sex": "female", "age": 29, "english_onset_age": 5},
            },
        ],
    },

    "T8": {
        "title": "Fruit-Gathering XVIII",
        "author": "Rabindranath Tagore (1916)",
        "role": "test-indian",
        "librivox_ids": [17632],
        "span_rule": 2,
        "text": (
            "No: it is not yours to open buds into blossoms. "
            "Shake the bud, strike it; it is beyond your power to make it blossom. "
            "Your touch soils it, you tear its petals to pieces and strew them in the dust. "
            "But no colours appear, and no perfume. "
            "Ah! it is not for you to open the bud into a blossom. "
            "He who can open the bud does it so simply. "
            "He gives it a glance, and the life-sap stirs through its veins. "
            "At his breath the flower spreads its wings and flutters in the wind. "
            "Colours flush out like heart-longings, the perfume betrays a sweet secret. "
            "He who can open the bud does it so simply."
        ),
    },
}

MIN_GOOD = 4  # an envelope needs at least this many good renditions (spec section 5)


def test_texts() -> list[str]:
    return [t for t, v in TEXTS.items() if v["role"].startswith("test")]


# How each passage is shown to a reader (line breaks only; scoring uses "text").
DISPLAY = {
    "T1": """I must go down to the seas again, to the lonely sea and the sky,
And all I ask is a tall ship and a star to steer her by,
And the wheel's kick and the wind's song and the white sail's shaking,
And a grey mist on the sea's face, and a grey dawn breaking.

I must go down to the seas again, for the call of the running tide
Is a wild call and a clear call that may not be denied;
And all I ask is a windy day with the white clouds flying,
And the flung spray and the blown spume, and the sea-gulls crying.

I must go down to the seas again, to the vagrant gypsy life,
To the gull's way and the whale's way where the wind's like a whetted knife;
And all I ask is a merry yarn from a laughing fellow-rover,
And quiet sleep and a sweet dream when the long trick's over.""",
    "T2": """Whose woods these are I think I know.
His house is in the village though;
He will not see me stopping here
To watch his woods fill up with snow.

My little horse must think it queer
To stop without a farmhouse near
Between the woods and frozen lake
The darkest evening of the year.

He gives his harness bells a shake
To ask if there is some mistake.
The only other sound's the sweep
Of easy wind and downy flake.

The woods are lovely, dark and deep,
But I have promises to keep,
And miles to go before I sleep,
And miles to go before I sleep.""",
    "T7": (
        "Please call Stella. Ask her to bring these things with her from the store: "
        "Six spoons of fresh snow peas, five thick slabs of blue cheese, and maybe a snack "
        "for her brother Bob. We also need a small plastic snake and a big toy frog for the "
        "kids. She can scoop these things into three red bags, and we will go meet her "
        "Wednesday at the train station."
    ),
    "T8": """No: it is not yours to open buds into blossoms.

Shake the bud, strike it; it is beyond your power to make it blossom.

Your touch soils it, you tear its petals to pieces and strew them in the dust.

But no colours appear, and no perfume.

Ah! it is not for you to open the bud into a blossom.

He who can open the bud does it so simply.

He gives it a glance, and the life-sap stirs through its veins.

At his breath the flower spreads its wings and flutters in the wind.

Colours flush out like heart-longings, the perfume betrays a sweet secret.

He who can open the bud does it so simply.""",
}


def display_text(tid: str) -> str:
    return DISPLAY.get(tid, TEXTS[tid]["text"])


# One-line context shown to a speaker (display only).
CONTEXT = {
    "T3": "Abraham Lincoln, 19 November 1863, at the dedication of the Soldiers' National Cemetery in "
          "Gettysburg, Pennsylvania. The closing paragraph: the call to finish the work, ending in "
          "\"government of the people, by the people, for the people\".",
    "T4": "Abraham Lincoln, 19 November 1863, at the dedication of the Soldiers' National Cemetery in "
          "Gettysburg, Pennsylvania. The opening paragraph: the nation's founding ideals and the purpose "
          "of the day.",
    "T5": "Franklin D. Roosevelt to a joint session of Congress, 8 December 1941, the day after the attack "
          "on Pearl Harbor.",
    "T1": "A lyric poem (1902); a research benchmark used only to calibrate Cadence.",
    "T2": "A lyric poem (1923); a held-out research benchmark.",
    "T6": "A poem written as advice from a father to his son (1910); the untouched final test set.",
}
SPEECHES = ["T3", "T4", "T5"]  # public-speaking exercises; the rest are research benchmarks
