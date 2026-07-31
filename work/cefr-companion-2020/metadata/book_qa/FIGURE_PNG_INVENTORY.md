# Figure PNG inventory (companion job assets/figures)

Generated: 2026-07-30T18:36:59

## Classification

### Reused from before this recent redesign window (existed ~2026-07-29)
These predate the last 1–2 days of companion Vision/MD finalize + figure-18–20 PNG work.

| File | Notes |
|------|-------|
| `figure_02_reception_production_interaction_mediation.png` | pre-existing pipeline/figure inject (~1785369363.7955377) |
| `figure_03_cefr_common_reference_levels.png` | pre-existing pipeline/figure inject (~1785369363.8397102) |
| `figure_04_rainbow.png` | pre-existing pipeline/figure inject (~1785369363.8722541) |
| `figure_05_conventional_six_colours.png` | pre-existing pipeline/figure inject (~1785369363.8895288) |
| `figure_06_fictional_profile_clil.png` | pre-existing pipeline/figure inject (~1785369364.0148778) |
| `figure_07_profile_postgraduate_sciences.png` | pre-existing pipeline/figure inject (~1785369364.142222) |
| `figure_08_plurilingual_proficiency_fewer_categories.png` | pre-existing pipeline/figure inject (~1785369364.2290554) |
| `figure_09_overall_proficiency_one_language.png` | pre-existing pipeline/figure inject (~1785369364.2728872) |

### Created / rewritten in the last ~1–2 days (2026-07-30)
Created when replacing mermaid for Figs 18–20; **re-cropped again** 2026-07-30 evening to exclude figure titles and surrounding prose (user QA).

| File | Role |
|------|------|
| `figure_18_young_learner_project_design.png` | Fig 18 diagram-only (PDF crop; caption excluded) |
| `figure_18_young_learner_project_design_fullpage.png` | Full page 244 render (reference) |
| `figure_19_multimethod_research_design.png` | Fig 19 diagram-only (PDF crop; caption excluded) |
| `figure_19_multimethod_research_design_fullpage.png` | Full page 249 render (reference) |
| `figure_20_sign_language_project_phases.png` | Fig 20 diagram-only (PDF crop; caption excluded) |
| `figure_20_sign_language_project_phases_fullpage.png` | Full page 254 render (reference) |

### Not created this window
No other figure assets under `assets/figures/` were newly authored for companion testing of source.pdf / regression beyond the list above.

## Rule
Figure PNG crops must contain **diagram only** — not the PDF “Figure N – …” caption and not adjacent body prose. Captions live in the MD `### Figure N` heading + alt text.

## 2026-07-31 follow-up — Figure 19 top borders

User: Fig 19 crop was missing the top outer borders of **Preparatory work** and **Consultation & Piloting**.

Fix: re-render from PDF with higher clip top, then trim only the caption band. Final asset includes both top section frames; PDF “Figure 19 – …” title stays out of the PNG (caption remains MD heading only).

