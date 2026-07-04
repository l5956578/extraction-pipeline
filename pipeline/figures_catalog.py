"""Authoritative text-diagram content for all 20 CEFR figures."""

from __future__ import annotations

FIGURE_CONTENT: dict[str, dict] = {}


def _entry(fid: str, header: str, body: str, render_as: str) -> None:
    FIGURE_CONTENT[fid] = {
        "id": fid,
        "header": header,
        "body": body.strip(),
        "render_as": render_as,
    }


_entry(
    "figure_01_structure_cefr_descriptive_scheme",
    "Figure 1 – The structure of the CEFR descriptive scheme",
    """
```text
Overall language proficiency
├── General competences
│   ├── Savoir
│   ├── Savoir-faire
│   ├── Savoir-être
│   └── Savoir apprendre
├── Communicative language competences
│   ├── Linguistic
│   ├── Sociolinguistic
│   └── Pragmatic
├── Communicative language activities
│   ├── Reception
│   ├── Production
│   ├── Interaction
│   └── Mediation
└── Communicative language strategies
    ├── Reception
    ├── Production
    ├── Interaction
    └── Mediation
```
""",
    "text_diagram",
)

# Figures 2–10 are PNG assets (see metadata/figures_registry.json).
# Profile level data for radar charts: metadata/figure_06_profile_data.json

_entry(
    "figure_11_reception_activities_strategies",
    "Figure 11 – Reception activities and strategies",
    """
```text
Reception
├── Reception activities
│   ├── Oral comprehension
│   │   ├── Overall oral comprehension
│   │   ├── Understanding conversation between other people
│   │   ├── Understanding as a member of a live audience
│   │   ├── Understanding announcements and instructions
│   │   └── Understanding audio (or signed) media and recordings
│   ├── Audio-visual comprehension
│   │   └── Watching TV, film and video
│   └── Reading comprehension
│       ├── Overall reading comprehension
│       ├── Reading correspondence
│       ├── Reading for orientation
│       ├── Reading for information and argument
│       ├── Reading instructions
│       └── Reading as a leisure activity
└── Reception strategies
    └── Identifying cues and inferring
```
""",
    "text_diagram",
)

_entry(
    "figure_12_production_activities_strategies",
    "Figure 12 – Production activities and strategies",
    """
```text
Production
├── Production activities
│   ├── Oral production
│   │   ├── Overall oral production
│   │   ├── Sustained monologue: describing experience
│   │   ├── Sustained monologue: giving information
│   │   ├── Sustained monologue: putting a case
│   │   ├── Public announcements
│   │   └── Addressing audiences
│   └── Written production
│       ├── Overall written production
│       ├── Creative writing
│       └── Reports and essays
└── Production strategies
    ├── Planning
    ├── Compensating
    └── Monitoring and repair
```
""",
    "text_diagram",
)

_entry(
    "figure_13_interaction_activities_strategies",
    "Figure 13 – Interaction activities and strategies",
    """
```text
Interaction
├── Interaction activities
│   ├── Oral interaction
│   │   ├── Overall oral interaction
│   │   ├── Understanding an interlocutor
│   │   ├── Conversation
│   │   ├── Informal discussion
│   │   ├── Formal discussion
│   │   ├── Goal-oriented co-operation
│   │   ├── Obtaining goods and services
│   │   ├── Information exchange
│   │   ├── Interviewing and being interviewed
│   │   └── Using telecommunications
│   ├── Written interaction
│   │   ├── Overall written interaction
│   │   ├── Correspondence
│   │   └── Notes, messages and forms
│   └── Online interaction
│       ├── Online conversation and discussion
│       └── Goal-oriented online transactions and collaboration
└── Interaction strategies
    ├── Turntaking
    ├── Co-operating
    └── Asking for clarification
```
""",
    "text_diagram",
)

_entry(
    "figure_14_mediation_activities_strategies",
    "Figure 14 – Mediation activities and strategies",
    """
```text
Mediation
├── Mediation activities
│   ├── Mediating a text
│   │   ├── Relaying specific information
│   │   ├── Explaining data
│   │   ├── Processing text
│   │   ├── Translating a written text
│   │   ├── Note-taking
│   │   ├── Expressing a personal response to creative texts
│   │   └── Analysis and criticism of creative texts
│   ├── Mediating concepts
│   │   ├── Collaborating in a group
│   │   │   ├── Facilitating collaborative interaction with peers
│   │   │   └── Collaborating to construct meaning
│   │   └── Leading group work
│   │       ├── Managing interaction
│   │       └── Encouraging conceptual talk
│   └── Mediating communication
│       ├── Facilitating pluricultural space
│       ├── Acting as an intermediary
│       └── Facilitating communication in delicate situations and disagreements
└── Mediation strategies
    ├── Strategies to explain a new concept
    │   ├── Linking to previous knowledge
    │   ├── Adapting language
    │   └── Breaking down complicated information
    └── Strategies to simplify a text
        ├── Amplifying a dense text
        └── Streamlining a text
```
""",
    "text_diagram",
)

_entry(
    "figure_15_plurilingual_pluricultural_competence",
    "Figure 15 – Plurilingual and pluricultural competence",
    """
```text
Plurilingual and pluricultural competence
├── Building on pluricultural repertoire
├── Plurilingual comprehension
└── Building on plurilingual repertoire
```
""",
    "text_diagram",
)

_entry(
    "figure_16_communicative_language_competences",
    "Figure 16 – Communicative language competences",
    """
```text
Communicative language competences
├── Linguistic competence
│   ├── General linguistic range
│   ├── Vocabulary range
│   ├── Grammatical accuracy
│   ├── Vocabulary control
│   ├── Phonological control
│   └── Orthographic control
├── Sociolinguistic competence
│   └── Sociolinguistic appropriateness
└── Pragmatic competence
    ├── Flexibility
    ├── Turntaking
    ├── Thematic development
    ├── Coherence and cohesion
    ├── Propositional precision
    └── Fluency
```
""",
    "text_diagram",
)

_entry(
    "figure_17_signing_competences",
    "Figure 17 – Signing competences",
    """
```text
Signing competences
├── Linguistic
│   ├── Sign language repertoire (receptive/productive)
│   └── Diagrammatical accuracy (receptive/productive)
├── Sociolinguistic
│   └── Sociolinguistic appropriateness and cultural repertoire (receptive/productive)
└── Pragmatic
    ├── Sign text structure (receptive/productive)
    ├── Setting and perspectives (receptive/productive)
    ├── Language awareness and interpretation (receptive)
    ├── Presence and effect (productive)
    ├── Processing speed (receptive)
    └── Signing fluency (productive)
```
""",
    "text_diagram",
)

_entry(
    "figure_18_young_learner_project_design",
    "Figure 18 – Development design of Young Learner Project",
    """
```mermaid
flowchart TD
    PW[Preparatory work] --> IC[Initial collation of validated ELP and assessment descriptors]
    IC --> CS[Categorisation of sources]
    CS --> EC1[Expert consultation]
    PW --> DEV[Development]
    DEV --> JC[Judgement of correspondences to 2001 illustrative descriptors]
    JC --> SCR[Steering committee review of collation format]
    SCR --> AD[Addition of extended set descriptors with judgements of relevance]
    DEV --> QV[Qualitative validation]
    QV --> EC2[Expert consultation - peer review]
    EC2 --> RW[Rework / expert workshop]
    QV --> SRD[Separate reference documents for each age group]
    SRD --> FU[Final updates]
    QV --> FIN[Finalisation]
    FIN --> FU
    FU --> OUT[A new collation of descriptors for young learners]
```
""",
    "mermaid",
)

_entry(
    "figure_19_multimethod_research_design",
    "Figure 19 – Multimethod developmental research design",
    """
```mermaid
flowchart TB
    subgraph prep [Preparatory work]
        IC[Initial collection]
        CM[Consultative meeting]
        RV1[Revision]
        EM[Expert meeting]
    end
    subgraph dev [Development]
        MED[Mediation track]
        PLU[Plurilingual track]
        PHO[Phonology track]
    end
    subgraph qual [Qualitative validation]
        WS1[Workshops - 140 workshops, 999 participants]
        RV2[Revision - 60 descriptors dropped]
        OS1[Online survey - 250 responses]
    end
    subgraph quant [Quantitative validation]
        WS2[Workshops - 189 workshops, 1294 responses]
        OS2[Online survey - 3503 responses]
        DA[Data analysis - Rasch scaling and standard-setting]
    end
    subgraph consult [Consultation and Piloting]
        PC[Pre-consultation]
        FC[Formal consultation]
        PIL[Piloting]
        DIS[Dissemination]
    end
    prep --> dev --> qual --> quant --> consult
```
""",
    "mermaid",
)

_entry(
    "figure_20_sign_language_project_phases",
    "Figure 20 – The phases of the sign language project",
    """
```mermaid
flowchart LR
    PW[Preparatory work] --> IT[Identifying text types]
    IT --> IE[Identifying experts for text types]
    IE --> FS[Filming expert signers]
    DEV[Development] --> FD[Formulating descriptors]
    FD --> VD[Validating descriptors with signers]
    VAL[Validating] --> CC[Checking categories]
    CC --> CAL[Calibrating to CEFR levels]
    CAL --> OUT[Sign language descriptors]
    PW --> DEV --> VAL
```
""",
    "mermaid",
)


def figure_block(fid: str) -> str:
    item = FIGURE_CONTENT[fid]
    pages = {
        "figure_01_structure_cefr_descriptive_scheme": "32",
        "figure_02_reception_production_interaction_mediation": "34",
        "figure_03_cefr_common_reference_levels": "36",
        "figure_04_rainbow": "36",
        "figure_05_conventional_six_colours": "36",
        "figure_06_fictional_profile_clil": "38",
        "figure_07_profile_postgraduate_sciences": "39",
        "figure_08_plurilingual_proficiency_fewer_categories": "40",
        "figure_09_overall_proficiency_one_language": "40",
        "figure_10_plurilingual_oral_comprehension": "40",
        "figure_11_reception_activities_strategies": "47",
        "figure_12_production_activities_strategies": "61",
        "figure_13_interaction_activities_strategies": "71",
        "figure_14_mediation_activities_strategies": "90",
        "figure_15_plurilingual_pluricultural_competence": "123",
        "figure_16_communicative_language_competences": "129",
        "figure_17_signing_competences": "144",
        "figure_18_young_learner_project_design": "244",
        "figure_19_multimethod_research_design": "249",
        "figure_20_sign_language_project_phases": "254",
    }
    page = pages.get(fid, "?")
    display = item["header"]
    return (
        f"<!-- db:id={fid} type=figure render_as={item['render_as']} "
        f"product_tier=context pages={page} -->\n"
        f"### {display} | {fid}\n\n"
        f"{item['body']}\n"
    )