from pathlib import Path
import re

MD = Path("output/cefr-companion-2020/CEFR_Companion_Volume.md")
md = MD.read_text(encoding="utf-8")

repls = [
    (
        "Can understand with ease virtually Has no difficulty with any kind of spoken/signers language, whether live or broadcast, delivered at fast native natural speed.",
        "Has no difficulty with any kind of spoken/signed language, whether live or broadcast, delivered at fast natural speed.",
    ),
    (
        "Can understand and interpret critically virtually all forms of the written language types of written/signed texts including abstract, structurally complex, or highly colloquial literary and non-literary writings.",
        "Can understand and interpret critically virtually all forms of written/signed texts including abstract, structurally complex, or highly colloquial literary and non-literary writings.",
    ),
    (
        "speakers/signers of the target language native speakers quite possible",
        "speakers/signers of the target language quite possible",
    ),
    (
        "users of the target language native speakers without",
        "users of the target language without",
    ),
    (
        "another native proficient speaker/signer",
        "another proficient speaker/signer",
    ),
    (
        "another native proficient speaker.",
        "another proficient speaker.",
    ),
    (
        "at no disadvantage to native speakers other participants.",
        "at no disadvantage to other participants.",
    ),
    (
        "at no disadvantage to native speakers. other participants.",
        "at no disadvantage to other participants.",
    ),
    (
        "native speakers/signers of the target language native speakers",
        "speakers/signers of the target language",
    ),
    (
        "Understanding conversation between other native people",
        "Understanding conversation between other people",
    ),
    (
        "Listening Understanding as a member of a live audience",
        "Understanding as a member of a live audience",
    ),
    (
        "Understanding a native speaker an interlocutor",
        "Understanding an interlocutor",
    ),
    (
        "non-standard less familiar variety accent or dialect",
        "less familiar accent or dialect",
    ),
    (
        "native proficient speakers/signers of the target language",
        "proficient speakers/signers of the target language",
    ),
    (
        "Spoken Fluency",
        "Spoken fluency",
    ),
]

for a, b in repls:
    c = md.count(a)
    if c:
        md = md.replace(a, b)
        print(f"{c}x: {a[:50]}...")

MD.write_text(md, encoding="utf-8")
print("virtually Has", "virtually Has" in md)
print("written language types", "written language types" in md)
