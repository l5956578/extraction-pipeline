# User round-3 — URLs, callouts, headers, tables

Source: user chat review (through Appendix 3 / self-assessment).

**URL note:** This is a **sanitization** defect class (footnote/punctuation glued into the URL token), not an Obsidian-only render quirk.

## URL sanitize
p28: SANITIZE 'http://www.coe.int/en/web/common-european-framework-reference-languages/referenc' → '<http://www.coe.int/en/web/common-european-framework-reference-languages/referen'
p29: SANITIZE 'https://rm.coe.int/1680667a2d),23' → '<https://rm.coe.int/1680667a2d>),23'
p44: SANITIZE 'https://rm.coe.int/1680697848)”,34' → '<https://rm.coe.int/1680697848>)”,34'
p44: SANITIZE 'https://transformingfsl.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC605_Res' → '<https://transformingfsl.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC605_Re'
PATTERN RLDs \(<?(https?://www\.coe\.int/en/web/common-eur… x1
PATTERN to the CEFR \(<?(https://rm\.coe\.int/1680667a2d)>… x1
PATTERN \(<?(https://rm\.coe\.int/1680697848)>?\)”?,?\s*34… x1
PATTERN \(<?(https://transformingfsl\.ca/wp-content/upload… x1
PATTERN Common European framework and \(<?(https://rm\.coe… x1
PATTERN \(<?(https://rm\.coe\.int/168073ff31)>?\)”\.?\s*19… x1
PATTERN \(<?(https://www\.coe\.int/en/web/common-european-… x1
PATTERN Executive summar \(<?(http://www\.oecd\.org/pisa/3… x1
paren_fn normalize x21
## Callouts
p29 callout: chapter list as separate lines (removed wrong relex URL soup)
p31 callout: 2 paragraphs (was 5 single-sentence lines)
p37 callout: bold header + 2 paragraphs (was 8 lines)
## Headers
header p118/119 strategies explain + Linking: 1 fix(es)
header p121 strategies simplify + Amplifying: 1 fix(es)
general bold header scan touches: 5
## Table 175
p175: 3-column user-band table (Proficient/Independent/Basic + blank continuation rows)
## Self-assessment mediation 180-181
p177: mediation self-assessment = ONE table with columns text|concepts|communication (removed duplicate second table)
## Residual URL issues after fix
p13: https://rm.coe.int/16806ae621>);5
p13: https://rm.coe.int/16806af387>);6
p13: https://rm.coe.int/16802fc1c4>);7
p13: http://www.coe.int/en/web/lang-migrants/officials-texts-and-guidelines>);8
p13: http://www.coe.int/t/dg4/autobiography/default_en.asp>);9
p13: https://go.coe.int/mWYUH>).10
p22: https://www.coe.int/en/web/common-european-framework-reference-languages/bank-of-supplementary-descr
p24: https://rm.coe.int/168073ff31>).19
p28: http://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions
p29: https://rm.coe.int/1680667a2d>).23
p29: https://rm.coe.int/1680667a2b>).24
p29: https://relang.ecml.at>).26
p31: http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx>).27
p44: https://rm.coe.int/1680697848>).34
p44: https://transformingfsl.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC605_Research_Guide_English_
p44: http://www.ecml.at/CEFRqualitymatrix>).36
p44: http://www.helsinki.fi/project/ceftrain/index.php.35.html>).37
p45: https://rm.coe.int/168069ce6e>).38
p45: https://www.eaquals.org/our-expertise/cefr/our-work-practical-resources-for-language-teaching/>).39
p45: http://www.ecml.at/ECML-Programme/Programme2016-2019/SignLanguageInstruction/tabid/1856/Default.aspx
p102: https://petra-education.eu/>).44

# URL catalog (post-sanitize scan)

| Page | Form | Snippet |
|-----:|------|---------|
| 13 | `https://rm.coe.int/16806ae621>);5` **RESIDUAL?** | …ercultural education** (<https://rm.coe.int/16806ae621>);5 - **A handbook… |
| 13 | `https://rm.coe.int/16806af387>);6` **RESIDUAL?** | …sion in all subjects** (<https://rm.coe.int/16806af387>);6 - “From lingui… |
| 13 | `https://rm.coe.int/16802fc1c4>);7` **RESIDUAL?** | …on policies in Europe” (<https://rm.coe.int/16802fc1c4>);7  Others are av… |
| 13 | `http://www.coe.int/en/web/lang-migrants/officials-texts-and-guidelines>);8` **RESIDUAL?** | …tion of adult migrants (<http://www.coe.int/en/web/lang-migrants/officials-texts-and-guidelines>);8 … |
| 13 | `http://www.coe.int/t/dg4/autobiography/default_en.asp>);9` **RESIDUAL?** | …tercultural encounters (<http://www.coe.int/t/dg4/autobiography/default_en.asp>);9 - **Reference … |
| 13 | `https://go.coe.int/mWYUH>).10` **RESIDUAL?** | …r democratic culture** (<https://go.coe.int/mWYUH>).10  However, rega… |
| 13 | `https://rm.coe.int/16806ae621.` | …Strasbourg, available at https://rm.coe.int/16806ae621. 6. Beacco J.-C… |
| 13 | `https://rm.coe.int/16806af387.` | …Strasbourg, available at https://rm.coe.int/16806af387. 7. Beacco J.-C… |
| 13 | `https://rm.coe.int/16802fc1c4.` | …Strasbourg, available at https://rm.coe.int/16802fc1c4. 8. www.coe.int… |
| 13 | `https://go.coe.int/mWYUH,` | …Strasbourg, available at https://go.coe.int/mWYUH, accessed 6 Mar… |
| 14 | `http://www.ecml.at/ECML-Programme/Programme2012-2015/ProSign/tabid/1752/Default.aspx)` | …ering PRO-Sign project. (http://www.ecml.at/ECML-Programme/Programme2012-2015/ProSign/tabid/1752/Def… |
| 14 | `https://go.coe.int/mWYUH` | … Bertrand Vittecoq  11.  https://go.coe.int/mWYUH  - Consultants… |
| 21 | `https://rm.coe.int/1680459f97.` | … Cambridge, available at https://rm.coe.int/1680459f97.  *Introduction… |
| 22 | `https://www.coe.int/en/web/common-european-framework-reference-languages/bank-of-supplemen` **RESIDUAL?** | …nt for young learners, (<https://www.coe.int/en/web/common-european-framework-reference-languages/ba… |
| 22 | `https://rm.coe.int/16808b1688.` | … of Europe, available at https://rm.coe.int/16808b1688. 18.  Goodier T… |
| 22 | `https://rm.coe.int/16808b1689.` | … of Europe, available at https://rm.coe.int/16808b1689.  *Page **22** … |
| 24 | `https://rm.coe.int/168073ff31>).19` **RESIDUAL?** | …mediation for the CEFR (<https://rm.coe.int/168073ff31>).19  **Table 2 – S… |
| 24 | `https://rm.coe.int/168073ff31.` | …Strasbourg, available at https://rm.coe.int/168073ff31.  *Page **24** … |
| 25 | `https://rm.coe.int/16806ae621)` | …tercultural education** (https://rm.coe.int/16806ae621) (Beacco et al.… |
| 25 | `https://go.coe.int/mWYUH)` | …or democratic culture** (https://go.coe.int/mWYUH) (Council of Eu… |
| 25 | `https://rm.coe.int/16807367ee.` | …Strasbourg, available at https://rm.coe.int/16807367ee. <!-- el:end id… |
| 27 | `https://rm.coe.int/16806ae621)` | …tercultural education** (https://rm.coe.int/16806ae621) (Beacco et al.… |
| 27 | `https://search.coe.int/cm/Pages/result_details.aspx?ObjectId=09000016805d2fb1.` | …lingualism, available at https://search.coe.int/cm/Pages/result_details.aspx?ObjectId=09000016805d2f… |
| 28 | `http://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-de` **RESIDUAL?** | …el Descriptions – RLDs (<http://www.coe.int/en/web/common-european-framework-reference-languages/ref… |
| 28 | `https://rm.coe.int/16806ae621)` | …intercultural education (https://rm.coe.int/16806ae621) (Beacco et al.… |
| 29 | `https://rm.coe.int/1680667a2d>).23` **RESIDUAL?** | …aminations to the CEFR (<https://rm.coe.int/1680667a2d>).23 now accompanie… |
| 29 | `https://rm.coe.int/1680667a2b>).24` **RESIDUAL?** | …elopment and examining (<https://rm.coe.int/1680667a2b>).24 The Council of… |
| 29 | `https://www.ecml.at/Portals/1/documents/ECML-resources/2011_10_10_relex._E_web.pdf?ver=201` | …ent (CEFR) – Highlights (https://www.ecml.at/Portals/1/documents/ECML-resources/2011_10_10_relex._E_… |
| 29 | `https://relang.ecml.at>).26` **RESIDUAL?** | … its RELANG initiative (<https://relang.ecml.at>).26  However, it i… |
| 29 | `https://rm.coe.int/1680667a2d.` | …Strasbourg, available at https://rm.coe.int/1680667a2d. 24.  ALTE (201… |
| 29 | `https://rm.coe.int/1680667a2b.` | …Strasbourg, available at https://rm.coe.int/1680667a2b. 25.  Noijons J… |
| 29 | `https://relang.ecml.at/.` | …k of Reference (RELANG): https://relang.ecml.at/.  *Key aspects … |
| 30 | `https://rm.coe.int/168069d29b)` | …LURICULTURAL COMPETENCE (https://rm.coe.int/168069d29b)  The CEFR dist… |
| 30 | `https://rm.coe.int/168069d29b).` | …luricultural competence (https://rm.coe.int/168069d29b). > > These two … |
| 31 | `https://rm.coe.int/168069d29b)”.` | …luricultural competence (https://rm.coe.int/168069d29b)”. This is becaus… |
| 31 | `https://rm.coe.int/16806ae621)` | …tercultural education** (https://rm.coe.int/16806ae621) (Beacco et al.… |
| 31 | `http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx>).27` **RESIDUAL?** | …cultures (FREPA/CARAP) (<http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx>).27  #… |
| 31 | `http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx.` | …p031_s3 page=31 --> 27.  http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx. <!-- e… |
| 32 | `https://rm.coe.int/16806ae621)**` | …intercultural education (https://rm.coe.int/16806ae621)** (Beacco et al.… |
| 32 | `http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf.` | …Strasbourg, available at http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf.  … |
| 34 | `https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/` | … mediation for the CEFR (https://rm.coe.int/common-european-framework-of-reference-for-languages-lea… |
| 41 | `https://rm.coe.int/1680459f97#page=36),` | …d CEFR 2001 Section 3.7 (https://rm.coe.int/1680459f97#page=36), “How to read t… |
| 41 | `https://rm.coe.int/1680459f97#page=38)` | …p. 36), and Section 3.8 (https://rm.coe.int/1680459f97#page=38) (p. 37), “How … |
| 44 | `http://www.ecml.at/Thematicareas/CEFRandELP/Resources/tabid/2971/language/en-GB/Default.as` | …rough the ECML website. (http://www.ecml.at/Thematicareas/CEFRandELP/Resources/tabid/2971/language/e… |
| 44 | `https://rm.coe.int/1680697848>).34` **RESIDUAL?** | …nt – A Guide for Users (<https://rm.coe.int/1680697848>).34 available in E… |
| 44 | `https://transformingfsl.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC605_Research_Guid` **RESIDUAL?** | …d: a research pathway” (<https://transformingfsl.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC60… |
| 44 | `http://www.ecml.at/CEFRqualitymatrix>).36` **RESIDUAL?** | …ce matrix for CEFR use (<http://www.ecml.at/CEFRqualitymatrix>).36 (CEFR QualiMat… |
| 44 | `http://www.helsinki.fi/project/ceftrain/index.php.35.html>).37` **RESIDUAL?** | … in Teacher Training). (<http://www.helsinki.fi/project/ceftrain/index.php.35.html>).37 <!-- el:end … |
| 44 | `https://rm.coe.int/1680697848.` | …Strasbourg, available at https://rm.coe.int/1680697848. 35.  Piccardo … |
| 45 | `https://rm.coe.int/168069ce6e>).38` **RESIDUAL?** | …ework and portfolios** (<https://rm.coe.int/168069ce6e>).38 available in E… |
| 45 | `https://www.eaquals.org/our-expertise/cefr/our-work-practical-resources-for-language-teach` **RESIDUAL?** | …for language teaching” (<https://www.eaquals.org/our-expertise/cefr/our-work-practical-resources-for… |
| 45 | `https://rm.coe.int/16806ae621)**(Beacco` | …intercultural education (https://rm.coe.int/16806ae621)**(Beacco et al. 2016a),… |
| 45 | `http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf)**` | …nd teaching in the CEFR (http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf)**… |
| 45 | `http://www.ecml.at/ECML-Programme/Programme2016-2019/SignLanguageInstruction/tabid/1856/De` **RESIDUAL?** | … Language Instruction. (<http://www.ecml.at/ECML-Programme/Programme2016-2019/SignLanguageInstructio… |
| 45 | `https://rm.coe.int/168069ce6e.` | …Strasbourg, available at https://rm.coe.int/168069ce6e. 39.  Equals “P… |
| 90 | `https://rm.coe.int/168073ff31)` | …mediation for the CEFR” (https://rm.coe.int/168073ff31) (North and Pic… |
| 90 | `https://rm.coe.int/16807367ee)` | …n functions of schools” (https://rm.coe.int/16807367ee) (Coste and Cav… |
| 102 | `https://petra-education.eu/>).44` **RESIDUAL?** | … in the PETRA project. (<https://petra-education.eu/>).44 On the other h… |
| 102 | `https://petra-education.eu/.` | …=prose_p102_s0 -->  44.  https://petra-education.eu/.  *Page **102**… |
| 108 | `https://rm.coe.int/168069d29b),` | …luricultural competence (https://rm.coe.int/168069d29b), distinctions a… |
| 124 | `http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx)` | … languages and cultures (http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx) (FREPA… |
| 133 | `https://rm.coe.int/168073fff9.` | … of Europe, available at https://rm.coe.int/168073fff9. <!-- el:end id… |
| 243 | `https://rm.coe.int/phonological-scale-revision-process-report-cefr/168073fff9)` | …s an existing CEFR 2001 (https://rm.coe.int/phonological-scale-revision-process-report-cefr/168073ff… |
| 245 | `https://rm.coe.int/education-mobility-otherness-the-mediation-functions-of-schools/1680736` | …on functions of schools (https://rm.coe.int/education-mobility-otherness-the-mediation-functions-of-… |
| 245 | `https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/` | …mediation for the CEFR” (https://rm.coe.int/common-european-framework-of-reference-for-languages-lea… |
| 246 | `https://rm.coe.int/168069d29b)` | …luricultural competence (https://rm.coe.int/168069d29b) linked to CEFR… |
| 247 | `https://rm.coe.int/1680667a2d)` | …ment (CEFR) – A Manual” (https://rm.coe.int/1680667a2d) (Council of Eu… |
| 248 | `https://rm.coe.int/168069d29b)**` | …LURICULTURAL COMPETENCE (https://rm.coe.int/168069d29b)**  Finally, an e… |
| 252 | `https://moodle4teachers.org/enrol/index.php?id=90.` | … and Daniela Cuccurullo, https://moodle4teachers.org/enrol/index.php?id=90. 54.  The Counc… |
| 254 | `https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/` | …mediation for the CEFR” (https://rm.coe.int/common-european-framework-of-reference-for-languages-lea… |
| 254 | `https://rm.coe.int/phonological-scale-revision-process-report-cefr/168073fff9)` | …evision Process Report” (https://rm.coe.int/phonological-scale-revision-process-report-cefr/168073ff… |
| 269 | `http://www.coe.int/en/web/common-european-framework-reference-languages),` | …workreference-languages (http://www.coe.int/en/web/common-european-framework-reference-languages), a… |
| 269 | `https://rm.coe.int/16808ce258,` | …Strasbourg, available at https://rm.coe.int/16808ce258, accessed 9 Sep… |
| 269 | `http://www.cambridgeenglish.org/images/business-english-certificates-handbook-for-teachers` | …ndbook-for-teachers.pdf (http://www.cambridgeenglish.org/images/business-english-certificates-handbo… |
| 269 | `http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx)` | … Languages and Cultures (http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx) **, av… |
| 269 | `http://carap.ecml.at,` | …t.aspx) **, available at http://carap.ecml.at, accessed 9 Sep… |
| 269 | `http://events.cambridgeenglish.org/alte-2014/docs/presentations/alte2014-masashi-negishi.p` | …2011: for an update, see http://events.cambridgeenglish.org/alte-2014/docs/presentations/alte2014-ma… |
| 270 | `http://www.coe.int/en/web/common-european-framework-reference-languages/bank-of-supplement` | …pplementary-descriptors (http://www.coe.int/en/web/common-european-framework-reference-languages/ban… |
| 270 | `http://digitalcollections.sit.edu/cgi/viewcontent.cgi?article=1001&context=worldlearning_p` | …g Publications, Paper 1, http://digitalcollections.sit.edu/cgi/viewcontent.cgi?article=1001&context=… |
| 270 | `https://rm.coe.int/16802f727b,` | …Strasbourg, available at https://rm.coe.int/16802f727b, accessed 9 Sep… |
| 271 | `http://www.govtilr.org/skills/ILRscale1.htm)` | …ble at www.govtilr.org, (http://www.govtilr.org/skills/ILRscale1.htm) accessed 9 Sep… |
| 271 | `http://www.unesco.org/shs/diversities/vol13/issue2/art2)` | …ties/vol13/issue2/art2, (http://www.unesco.org/shs/diversities/vol13/issue2/art2) accessed 9 Sep… |
| 271 | `http://archive.ecml.at/mtp2/publications/B1_ICCinTE_E_internet.pdf,` | …bourg/Graz, available at http://archive.ecml.at/mtp2/publications/B1_ICCinTE_E_internet.pdf, accesse… |
| 271 | `https://rm.coe.int/16806ae621)` | …intercultural education (https://rm.coe.int/16806ae621) **, Language P… |
| 271 | `https://rm.coe.int/16805a1e55,` | …Strasbourg, available at https://rm.coe.int/16805a1e55, accessed 9 Sep… |
| 271 | `http://www.miriadi.net/en/printpdf/book/export/html/746),` | …df/book/export/html/746 (http://www.miriadi.net/en/printpdf/book/export/html/746), accessed 9 Sep… |
| 271 | `https://www.convenor.com/uploads/2/3/4/8/23485882/method.pdf),` | …/8/23485882/method. pdf (https://www.convenor.com/uploads/2/3/4/8/23485882/method.pdf), accessed 9 S… |
| 271 | `https://rm.coe.int/16808ce20c,` | … pp. 11-49, available at https://rm.coe.int/16808ce20c, accessed 9 Sep… |
| 272 | `https://rm.coe.int/168070eb85,` | …pe, Lisbon, available at https://rm.coe.int/168070eb85, accessed 9 Sep… |
| 272 | `http://www.oecd.org/pisa/35070367.pdf>),` | …es. Executive summary” (<http://www.oecd.org/pisa/35070367.pdf>), Organisation f… |
| 272 | `http://tuningacademy.org/?lang=en,` | …ogrammes**, available at http://tuningacademy.org/?lang=en, accessed 9 Sep… |
| 272 | `http://tuningacademy.org/?lang=en,` | …petences**, available at http://tuningacademy.org/?lang=en, accessed 9 Sep… |
| 272 | `http://tuningacademy.org/?lang=en,` | …petences**, available at http://tuningacademy.org/?lang=en, accessed 9 Sep… |
| 273 | `https://rm.coe.int/1680667a2b,` | …Strasbourg, available at https://rm.coe.int/1680667a2b, accessed 9 Sep… |
| 273 | `https://rm.coe.int/16806ccc07,` | …Strasbourg, available at https://rm.coe.int/16806ccc07, accessed 10 De… |
| 273 | `https://rm.coe.int/16806ae621,` | …Strasbourg, available at https://rm.coe.int/16806ae621, accessed 9 Sep… |
| 273 | `https://rm.coe.int/16806af387,` | …Strasbourg, available at https://rm.coe.int/16806af387, accessed 9 Sep… |
| 273 | `https://rm.coe.int/16802fc1c4,` | … of Europe, available at https://rm.coe.int/16802fc1c4, accessed 9 Sep… |
| 273 | `https://rm.coe.int/16807367ee,` | …Strasbourg, available at https://rm.coe.int/16807367ee, accessed 9 Sep… |
| 273 | `https://search.coe.int/cm/` | …lingualism, available at https://search.coe.int/cm/ Pages/result_d… |
| 273 | `https://rm.coe.int/1680459f97,` | … Cambridge, available at https://rm.coe.int/1680459f97, accessed 9 Sep… |
| 273 | `https://rm.coe.int/1680667a2d,` | …Strasbourg, available at https://rm.coe.int/1680667a2d, accessed 9 Sep… |
| 273 | `https://go.coe.int/mWYUH,` | …Strasbourg, available at https://go.coe.int/mWYUH, accessed 17 Ap… |
| 274 | `http://www.eaquals.org/our-expertise/cefr/our-work-practical-resources-for-language-teachi` | …-for-language-teaching/ (http://www.eaquals.org/our-expertise/cefr/our-work-practical-resources-for-… |
| 274 | `http://europass.cedefop.europa.eu/,` | …ber 2019.  Europass: see http://europass.cedefop.europa.eu/, accessed 9 Sep… |
| 274 | `http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx,` | …Cultures**, available at http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx, access… |
| 274 | `https://rm.coe.int/16808b1688,` | … of Europe, available at https://rm.coe.int/16808b1688, accessed 9 Sep… |
| 274 | `https://rm.coe.int/16808b1689,` | … of Europe, available at https://rm.coe.int/16808b1689, accessed 9 Sep… |
| 274 | `https://rm.coe.int/168069ce6e,` | …Strasbourg, available at https://rm.coe.int/168069ce6e, accessed 9 Sep… |
| 274 | `https://pjp-eu.coe.int/en/web/youthpartnership/icd-guidelines,` | …/education, available at https://pjp-eu.coe.int/en/web/youthpartnership/icd-guidelines, accessed 9 S… |
| 274 | `https://rm.coe.int/168073ff31,` | …Strasbourg, available at https://rm.coe.int/168073ff31, accessed 9 Sep… |
| 274 | `https://petra-education.eu/,` | …-E Network: available at https://petra-education.eu/, accessed 9 Sep… |
| 274 | `http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf,` | …Strasbourg, available at http://ecep.ecml.at/Portals/26/training-kit/files/2011_08_29_ECEP_EN.pdf, a… |
| 274 | `https://transformingfsl.ca/en/resources/?pagenum=2,` | …ces Canada, available at https://transformingfsl.ca/en/resources/?pagenum=2, accessed 9 Sep… |
| 274 | `https://rm.coe.int/168073fff9,` | … of Europe, available at https://rm.coe.int/168073fff9, accessed 9 Sep… |
| 274 | `https://relang.ecml.at/,` | …e (RELANG): available at https://relang.ecml.at/, accessed 9 Sep… |
| 274 | `https://moodle4teachers.org/enrol/index.php?id=90,` | …Cuccurullo, available at https://moodle4teachers.org/enrol/index.php?id=90, accessed 9 Sep… |
| 274 | `https://rm.coe.int/1680697848,` | …Strasbourg, available at https://rm.coe.int/1680697848, accessed 9 Sep… |
| 275 | `http://www.libeurop.be` | …E-mail: info@libeurop.eu http://www.libeurop.be Jean De Lannoy… |
| 275 | `http://www.jean-de-lannoy.be` | …n.de.lannoy@dl-servi.com http://www.jean-de-lannoy.be  **CANADA** Re… |
| 275 | `http://www.renoufbooks.com` | …der.dept@renoufbooks.com http://www.renoufbooks.com  **CROATIA/CRO… |
| 275 | `http://www.suweco.cz` | …E-mail: import@suweco.cz http://www.suweco.cz  **DENMARK/DAN… |
| 275 | `http://www.gad.dk` | …E-mail: reception@gad.dk http://www.gad.dk  **FINLAND/FIN… |
| 275 | `http://www.akateeminen.com` | …katilaus@akateeminen.com http://www.akateeminen.com  **FRANCE** Pl… |
| 275 | `http://book.coe.int` | …mail: publishing@coe.int http://book.coe.int Librairie Kléb… |
| 275 | `http://www.librairie-kleber.com` | …librairie-kleber@coe.int http://www.librairie-kleber.com  **NORWAY/NORV… |
| 275 | `http://www.akademika.no` | …il: support@akademika.no http://www.akademika.no  **POLAND/POLO… |
| 275 | `http://www.arspolona.com.pl` | …spolona@arspolona.com.pl http://www.arspolona.com.pl  **PORTUGAL** … |
| 275 | `http://www.vesmirbooks.ru` | …l: orders@vesmirbooks.ru http://www.vesmirbooks.ru  **SWITZERLAND… |
| 275 | `http://www.tsoshop.co.uk` | …book.enquiries@tso.co.uk http://www.tsoshop.co.uk UNITED STATES … |
| 275 | `http://www.manhattanpublishing.com` | …@manhattanpublishing.com http://www.manhattanpublishing.com Council of Eur… |
| 275 | `http://book.coe.int` | …shing@coe.int – Website: http://book.coe.int  <!-- el:end i… |
| 278 | `http://book.coe.int**` | …in the member states.  **http://book.coe.int** ISBN 978-92-87… |