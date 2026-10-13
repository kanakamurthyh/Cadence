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
