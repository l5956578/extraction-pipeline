from pathlib import Path

md_path = Path("output/cefr-companion-2020/CEFR_Companion_Volume.md")
md = md_path.read_text(encoding="utf-8")

p61_para = (
    "The categories for oral production are organised in terms of three macro-functions "
    "(interpersonal, transactional, evaluative), with two more specialised genres: "
    "“Addressing audiences” and “Public announcements”. “Sustained monologue: describing "
    "experience” focuses mainly on descriptions and narratives while “Sustained monologue: "
    "putting a case (e.g. in a debate)” describes the ability to sustain an argument, which "
    "may well be made in a long turn in the context of normal conversation and discussion. "
    "“Sustained monologue: giving information” is a new 2018 scale, created by transferring "
    "certain descriptors from the scale for “Information exchange” that implied monologue "
    "rather than dialogue."
)

if "rather than dialogue" not in md:
    needle = "#### 3.2.1.1. Oral production\n\n\n<!-- el:end id=figure_12"
    if needle in md:
        md = md.replace(
            needle,
            "#### 3.2.1.1. Oral production\n\n" + p61_para + "\n\n<!-- el:end id=figure_12",
            1,
        )
        print("p61 para inserted")
    else:
        # broader
        import re

        md2, n = re.subn(
            r"(#### 3\.2\.1\.1\. Oral production\s*\n)(\s*)(<!-- el:end id=figure_12)",
            r"\1\n" + p61_para + r"\n\n\3",
            md,
            count=1,
        )
        md = md2
        print("p61 regex", n)

p71_block = """### 3.3.1. Interaction activities

#### 3.3.1.1. Oral interaction

Oral interaction is understood to include both spoken interaction and live, face-to-face signing. The scales are once again organised by the three macro-functions “interpersonal”, “transactional” and “evaluative”, with certain specialised genres added on. The scales begin with “Understanding an interlocutor”. “Interlocutor” is a somewhat technical term that means the person with whom one is conversing directly in a dialogue. As mentioned before, the metaphor behind the scales for oral comprehension is that of a series of concentric circles. Here we are at the centre of those circles: the user/learner is actively involved in an interaction with the interlocutor.

The other scales then follow:

- interpersonal: “Conversation”;
- evaluative: “Informal discussion (with friends)”; “Formal discussion (meetings)”, “Goal-oriented collaboration”;
- transactional: “Information exchange”, “Obtaining goods and services”, “Interviewing and being interviewed”, and “Using telecommunications”.
"""

if "Oral interaction is understood" not in md:
    import re

    # Replace thin tail before figure_13 el:end
    md2, n = re.subn(
        r"(```\s*\n)([\s\S]*?)(<!-- el:end id=figure_13_interaction_activities_strategies -->)",
        lambda m: m.group(1)
        + m.group(2).split("### 3.3.1")[0]
        + "\n"
        + p71_block
        + "\n"
        + m.group(3),
        md,
        count=1,
    )
    if n:
        md = md2
        print("p71 restored via regex")
    else:
        print("p71 pattern fail")

md_path.write_text(md, encoding="utf-8")
md = md_path.read_text(encoding="utf-8")
print("dialogue", "rather than dialogue" in md)
print("oral", "Oral interaction is understood" in md)
