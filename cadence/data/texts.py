"""The three texts of the benchmark (spec section 8).

T1 is calibration only (thresholds, lambda, severity mapping); T2 and T3 are test.
All three are public domain in the US. T3 is the closing paragraph of the
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
}
