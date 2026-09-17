export const FALLBACK_MAP = {
  "_comment": "SINGLE SOURCE OF TRUTH for Bangla Braille character mappings.",
  "_standard": "Bangladesh National Braille Code",
  "_warning": "All 50 letters are encoded. ঋ (id=6) and ৎ (id=46) are two-cell characters (prefix dot-5 then the main cell). The device vibrates cell 1, pauses, then collects the learner's answer for cell 2 only. ঋ still collides with র on cell-2 alone — see _notes.collision_ri_ra.",
  "_notes": {
    "verification_sources": "11 vowels verified from braille_img/; 38 consonants+modifiers verified from Wikipedia:Bengali_Braille (Bangladesh standard, retrieved 2026-09-17). ঋ and ৎ additionally confirmed as two-cell from Bangladesh standard.",
    "two_cell_encoding": "Characters with a 'cells' field are multi-cell. cells[0] is the prefix (vibrated first on the device, displayed as context in the web app). cells[1] / 'dots' is the answer cell that the learner presses. Scoring always uses 'dots' (cells[-1]).",
    "collision_ri_ra": "ঋ (id=6) and র (id=37) share the same second-cell pattern [1,2,3,5]. With the two-cell prompt the prefix dot-5 distinguishes them during the teaching phase. The learner still only presses [1,2,3,5] for both — ambiguity remains at input time but is resolved by context (the audio names the character). Consider a two-button submit protocol in a future hardware revision.",
    "not_in_map": "ঌ (obsolete vowel) is not attested in Bangladesh Braille and is excluded from the map. ক্ষ (dots 1,2,3,4,5) and জ্ঞ (dots 1,5,6) are present in Bangladesh standard but not in the 50-character learnable set."
  },
  "standard": "Bangladesh_National_Braille_Code",
  "verified": false,
  "dot_layout": {
    "_comment": "Braille cell dot numbering. Column-major, the international standard.",
    "1": "top-left",
    "2": "middle-left",
    "3": "bottom-left",
    "4": "top-right",
    "5": "middle-right",
    "6": "bottom-right"
  },
  "letters": [
    {
      "id": 0,
      "char": "অ",
      "name": "a",
      "roman": "o",
      "category": "vowel",
      "dots": [
        1
      ],
      "audio": "0001.mp3",
      "verified": true,
      "source": "braille_img/ao.webp"
    },
    {
      "id": 1,
      "char": "আ",
      "name": "aa",
      "roman": "a",
      "category": "vowel",
      "dots": [
        3,
        4,
        5
      ],
      "audio": "0002.mp3",
      "verified": true,
      "source": "braille_img/aa.webp"
    },
    {
      "id": 2,
      "char": "ই",
      "name": "i",
      "roman": "i",
      "category": "vowel",
      "dots": [
        2,
        4
      ],
      "audio": "0003.mp3",
      "verified": true,
      "source": "braille_img/ei.webp"
    },
    {
      "id": 3,
      "char": "ঈ",
      "name": "ii",
      "roman": "ee",
      "category": "vowel",
      "dots": [
        3,
        5
      ],
      "audio": "0004.mp3",
      "verified": true,
      "source": "braille_img/eiii.webp"
    },
    {
      "id": 4,
      "char": "উ",
      "name": "u",
      "roman": "u",
      "category": "vowel",
      "dots": [
        1,
        3,
        6
      ],
      "audio": "0005.mp3",
      "verified": true,
      "source": "braille_img/uu.webp"
    },
    {
      "id": 5,
      "char": "ঊ",
      "name": "uu",
      "roman": "oo",
      "category": "vowel",
      "dots": [
        1,
        2,
        5,
        6
      ],
      "audio": "0006.mp3",
      "verified": true,
      "source": "braille_img/uuuu.webp"
    },
    {
      "id": 6,
      "char": "ঋ",
      "name": "ri",
      "roman": "ri",
      "category": "vowel",
      "dots": [
        1,
        2,
        3,
        5
      ],
      "cells": [
        [
          5
        ],
        [
          1,
          2,
          3,
          5
        ]
      ],
      "audio": "0007.mp3",
      "verified": true,
      "source": "braille_img/ri.webp + Wikipedia:Bengali_Braille",
      "_note": "Two-cell: device vibrates prefix [5] then the learner presses [1,2,3,5]. Collides with র (id=37) on the second cell — distinguished by the prefix vibration and audio. See _notes.collision_ri_ra."
    },
    {
      "id": 7,
      "char": "এ",
      "name": "e",
      "roman": "e",
      "category": "vowel",
      "dots": [
        1,
        5
      ],
      "audio": "0008.mp3",
      "verified": true,
      "source": "braille_img/e.webp"
    },
    {
      "id": 8,
      "char": "ঐ",
      "name": "oi",
      "roman": "oi",
      "category": "vowel",
      "dots": [
        3,
        4
      ],
      "audio": "0009.mp3",
      "verified": true,
      "source": "braille_img/oi.webp"
    },
    {
      "id": 9,
      "char": "ও",
      "name": "o",
      "roman": "o",
      "category": "vowel",
      "dots": [
        1,
        3,
        5
      ],
      "audio": "0010.mp3",
      "verified": true,
      "source": "braille_img/o.webp"
    },
    {
      "id": 10,
      "char": "ঔ",
      "name": "ou",
      "roman": "ou",
      "category": "vowel",
      "dots": [
        2,
        4,
        6
      ],
      "audio": "0011.mp3",
      "verified": true,
      "source": "braille_img/ou.webp"
    },
    {
      "id": 11,
      "char": "ক",
      "name": "ka",
      "roman": "ka",
      "category": "consonant",
      "dots": [
        1,
        3
      ],
      "audio": "0012.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 12,
      "char": "খ",
      "name": "kha",
      "roman": "kha",
      "category": "consonant",
      "dots": [
        1,
        3,
        4,
        6
      ],
      "audio": "0013.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 13,
      "char": "গ",
      "name": "ga",
      "roman": "ga",
      "category": "consonant",
      "dots": [
        1,
        2,
        4,
        5
      ],
      "audio": "0014.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 14,
      "char": "ঘ",
      "name": "gha",
      "roman": "gha",
      "category": "consonant",
      "dots": [
        1,
        2,
        6
      ],
      "audio": "0015.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 15,
      "char": "ঙ",
      "name": "uma",
      "roman": "nga",
      "category": "consonant",
      "dots": [
        3,
        4,
        6
      ],
      "audio": "0016.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 16,
      "char": "চ",
      "name": "cha",
      "roman": "cha",
      "category": "consonant",
      "dots": [
        1,
        4
      ],
      "audio": "0017.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 17,
      "char": "ছ",
      "name": "chha",
      "roman": "chha",
      "category": "consonant",
      "dots": [
        1,
        6
      ],
      "audio": "0018.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 18,
      "char": "জ",
      "name": "ja",
      "roman": "ja",
      "category": "consonant",
      "dots": [
        2,
        4,
        5
      ],
      "audio": "0019.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 19,
      "char": "ঝ",
      "name": "jha",
      "roman": "jha",
      "category": "consonant",
      "dots": [
        1,
        3,
        5,
        6
      ],
      "audio": "0020.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 20,
      "char": "ঞ",
      "name": "nia",
      "roman": "nya",
      "category": "consonant",
      "dots": [
        2,
        5
      ],
      "audio": "0021.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 21,
      "char": "ট",
      "name": "tta",
      "roman": "ta",
      "category": "consonant",
      "dots": [
        2,
        3,
        4,
        5,
        6
      ],
      "audio": "0022.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 22,
      "char": "ঠ",
      "name": "ttha",
      "roman": "tha",
      "category": "consonant",
      "dots": [
        2,
        4,
        5,
        6
      ],
      "audio": "0023.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 23,
      "char": "ড",
      "name": "dda",
      "roman": "da",
      "category": "consonant",
      "dots": [
        1,
        2,
        4,
        6
      ],
      "audio": "0024.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 24,
      "char": "ঢ",
      "name": "ddha",
      "roman": "dha",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        4,
        5,
        6
      ],
      "audio": "0025.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 25,
      "char": "ণ",
      "name": "nna",
      "roman": "na",
      "category": "consonant",
      "dots": [
        3,
        4,
        5,
        6
      ],
      "audio": "0026.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 26,
      "char": "ত",
      "name": "ta",
      "roman": "ta",
      "category": "consonant",
      "dots": [
        2,
        3,
        4,
        5
      ],
      "audio": "0027.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 27,
      "char": "থ",
      "name": "tha",
      "roman": "tha",
      "category": "consonant",
      "dots": [
        1,
        4,
        5,
        6
      ],
      "audio": "0028.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 28,
      "char": "দ",
      "name": "da",
      "roman": "da",
      "category": "consonant",
      "dots": [
        1,
        4,
        5
      ],
      "audio": "0029.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 29,
      "char": "ধ",
      "name": "dha",
      "roman": "dha",
      "category": "consonant",
      "dots": [
        2,
        3,
        4,
        6
      ],
      "audio": "0030.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 30,
      "char": "ন",
      "name": "na",
      "roman": "na",
      "category": "consonant",
      "dots": [
        1,
        3,
        4,
        5
      ],
      "audio": "0031.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 31,
      "char": "প",
      "name": "pa",
      "roman": "pa",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        4
      ],
      "audio": "0032.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 32,
      "char": "ফ",
      "name": "pha",
      "roman": "pha",
      "category": "consonant",
      "dots": [
        2,
        3,
        5
      ],
      "audio": "0033.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 33,
      "char": "ব",
      "name": "ba",
      "roman": "ba",
      "category": "consonant",
      "dots": [
        1,
        2
      ],
      "audio": "0034.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 34,
      "char": "ভ",
      "name": "bha",
      "roman": "bha",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        6
      ],
      "audio": "0035.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 35,
      "char": "ম",
      "name": "ma",
      "roman": "ma",
      "category": "consonant",
      "dots": [
        1,
        3,
        4
      ],
      "audio": "0036.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 36,
      "char": "য",
      "name": "ya",
      "roman": "ja",
      "category": "consonant",
      "dots": [
        1,
        3,
        4,
        5,
        6
      ],
      "audio": "0037.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 37,
      "char": "র",
      "name": "ra",
      "roman": "ra",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        5
      ],
      "audio": "0038.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille",
      "_note": "Correct per Bangladesh standard. Collides with ঋ (id=6) which uses the same single-cell value. See _notes.collision_ri_ra."
    },
    {
      "id": 38,
      "char": "ল",
      "name": "la",
      "roman": "la",
      "category": "consonant",
      "dots": [
        1,
        2,
        3
      ],
      "audio": "0039.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 39,
      "char": "শ",
      "name": "sha",
      "roman": "sha",
      "category": "consonant",
      "dots": [
        1,
        4,
        6
      ],
      "audio": "0040.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 40,
      "char": "ষ",
      "name": "ssa",
      "roman": "sha",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        4,
        6
      ],
      "audio": "0041.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 41,
      "char": "স",
      "name": "sa",
      "roman": "sa",
      "category": "consonant",
      "dots": [
        2,
        3,
        4
      ],
      "audio": "0042.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 42,
      "char": "হ",
      "name": "ha",
      "roman": "ha",
      "category": "consonant",
      "dots": [
        1,
        2,
        5
      ],
      "audio": "0043.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 43,
      "char": "ড়",
      "name": "rra",
      "roman": "ra",
      "category": "consonant",
      "dots": [
        1,
        2,
        4,
        5,
        6
      ],
      "audio": "0044.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 44,
      "char": "ঢ়",
      "name": "rha",
      "roman": "rha",
      "category": "consonant",
      "dots": [
        1,
        2,
        3,
        5,
        6
      ],
      "audio": "0045.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 45,
      "char": "য়",
      "name": "yya",
      "roman": "ya",
      "category": "consonant",
      "dots": [
        2,
        6
      ],
      "audio": "0046.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 46,
      "char": "ৎ",
      "name": "khanda_ta",
      "roman": "t",
      "category": "consonant",
      "dots": [
        2,
        3,
        4,
        5
      ],
      "cells": [
        [
          5
        ],
        [
          2,
          3,
          4,
          5
        ]
      ],
      "audio": "0047.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille",
      "_note": "Two-cell: device vibrates prefix [5] then the learner presses [2,3,4,5]. Second cell collides with ত (id=26) — distinguished by the prefix vibration and audio."
    },
    {
      "id": 47,
      "char": "ং",
      "name": "anushar",
      "roman": "ng",
      "category": "consonant",
      "dots": [
        5,
        6
      ],
      "audio": "0048.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 48,
      "char": "ঃ",
      "name": "bisharga",
      "roman": "h",
      "category": "consonant",
      "dots": [
        6
      ],
      "audio": "0049.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    },
    {
      "id": 49,
      "char": "ঁ",
      "name": "chandrabindu",
      "roman": "n",
      "category": "consonant",
      "dots": [
        3
      ],
      "audio": "0050.mp3",
      "verified": true,
      "source": "Wikipedia:Bengali_Braille"
    }
  ],
  "verified_count": 50
};
