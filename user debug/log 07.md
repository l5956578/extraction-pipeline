odd-numbered pages lost their full text, noticed in chapter 2

---

page 38 trash soup for old table attempt under Figure 06

---

page 41

this page has a couple issues. 

1. it is an exception to the rule where `if the callout is not in the top-left corner then the callout element's text goes at the bottom` The reason it is an exception and should be placed in-line is because the elements directly before and after are NOT multi-column.

After you implement this fix here, understanding how the prose elements before and after the callout span the full page, I want to invoke Grok Vision (agent-in-the-loop) to QA your output and fail it and or pass it. If it fails you will continue working on the code. I do not want you to stop coding to give me a partial update until Grok Vision understands. If that means you must take a full page PNG snapshot and make it available to the Grok Vision agent, then so be it. This should be instituted as a skill. I don't need to QA things, if I explain clearly what I want, as I have here. This information should be made available to the Grok Vision agent in-the-loop, when it is invoked so that it has the necessary context of what the page is, what I expect, and the process we are following: you code → it QA's until your code satisfies the requirement. We will use this going forward to lower the person-in-the-QA-loop churn and user general fatigue. 

2. Also give it access to all other requirements in case it wants to identify where that page has issues. For example you know that prose elements should exist in their own block and not be merged into other prose element blocks. You providing a comprehensive set of rules and put them in a file and point the QA agent skill to it. I think this is a much-needed addition to our workflow for bug reporting where we ensure Grok Vision Agent's intelligence is used instead of burdening the user for easy misses in the output compared to the PNG you'll make of the page.

A grok agent, for example should also notice, though it is a bit hard to articulate that this block of prose in the output:

The illustrative descriptors are one source for the development of standards appropriate to the context concerned; they are not in themselves offered as standards. They are a basis for reflection, discussion and further action. The aim is to open new possibilities, not to pre-empt decisions. The CEFR itself makes this point very clearly, stating that the descriptors are presented as recommendations and are not in any way mandatory. As a user, you are invited to use the scaling system and associated descriptors critically. The Modern Languages Section of the Council of Europe will be glad to receive a report of your experience in putting them into use. Please note also that scales are provided not only for a global proficiency, but for many of the parameters of language proficiency detailed in Chapters 4 and 5. This makes it possible to specify differentiated profiles for particular learners or groups of learners (CEFR 2001, Notes for the user: xiii-xiv).

Based on the Agent's intelligent view of the PNG should be:

The illustrative descriptors are one source for the development of standards appropriate to the context concerned; they are not in themselves offered as standards. They are a basis for reflection, discussion and further action. The aim is to open new possibilities, not to pre-empt decisions. The CEFR itself makes this point very clearly, stating that the descriptors are presented as recommendations and are not in any way mandatory. 

As a user, you are invited to use the scaling system and associated descriptors critically. The Modern Languages Section of the Council of Europe will be glad to receive a report of your experience in putting them into use. Please note also that scales are provided not only for a global proficiency, but for many of the parameters of language proficiency detailed in Chapters 4 and 5. This makes it possible to specify differentiated profiles for particular learners or groups of learners (CEFR 2001, Notes for the user: xiii-xiv).

We don't need the user's eyes on this kind of thing. Only break the coding → Grok QA cycle when it is evident (after 4 attempts) that the Grok Agent has reported an issue that requires user input to resolve. But as this is a PDF where we are extracting text and ensuring it matches when in markdown format, this should be rare. The protocol after bug fixes, is to describe the issue, where the issue exists, number of attempts to resolve, and how it was resolved.

Anything missing?

---

page 42 callout lost all its formatting, why?

Defining curriculum aims from a needs profile Step 1: Select the descriptor scales that are relevant to the needs of the group of learners concerned (see Figures 6 and 7). Clearly this is best undertaken in consultation with stakeholders, including teachers and, in the case of adult learners, the learners themselves. Stakeholders can also be asked what other communicative activities are relevant. Step 2: Determine with the stakeholders, for each relevant descriptor scale, the level that the learners should reach. Step 3: Collate the descriptors for the target level(s) from all the relevant scales into a list. This provides the very first draft of a set of communicative aims. Step 4: Refine the list, possibly in discussion with the stakeholders.

---

page 43 callout failed again, it is at the top and should not be put inline, spans the whole page and therefore can remain at the top. It also lost it's formatting. Systemic issue must be investigated.

---

page 43, when you moved the callout to the bottom (bug, see above) you lost prose for the first paragraph of text:

course. In such a case, descriptors from particular scales are selected, adapted to the local context and added to an existing curricular document.

should be:

Very often, CEFR descriptors are referred to for inspiration in adapting or making explicit the aims of an existing course. In such a case, descriptors from particular scales are selected, adapted to the local context and added to an existing curricular document.

Plus this:

2. Descriptors of aspects of proficiency related to particular competences, which are located in Chapter 5. 
   
   The former are very suitable for teacher- or self-assessment with regard to real-world tasks. Such teacher- or self- assessments are made on the basis of a detailed picture of the learner’s language ability built up during the course concerned. They are attractive because they can help to focus both learners and teachers on an action-oriented approach. (CEFR 2001 Section 9.2.2) 

The latter, descriptors of aspects of competences (CEFR 2001 Chapter 5), can be a useful source for developing assessment criteria for how well...

Was botched:

2.	 Descriptors of aspects of proficiency related to particular competences, which are located in Chapter 5. The former are very suitable for teacher or self-assessment with regard to real-world tasks. Such teacher or self-assessments are made on the basis of a detailed picture of the learner’s language ability built up during the course concerned. They are attractive because they can help to focus both learners and teachers on an action-oriented approach. (CEFR 2001 Section 9.2.2) The latter, descriptors of aspects of competences (CEFR 2001 Chapter 5), can be a useful source for developing assessment criteria for how well

This is another example where the QA agent skill will help since it should be able to easily identify the wrong placement of the callout, plus the formatting being botched based on the PNG it has access to, plus the ability to describe what's wrong. It should not force it's own opinion on how to code. It should only describe, not prescribe, standing in for the user as a QA agent. I want a clean skill that doesn't break the system obviously.

---

page 70 trash soup after figure 13. I mentioned this earlier but apparently it wasn't integrated correctly. Why? Also on page 90. FFS why do I report issues that you refuse to do anything about!? I reported this in log 05 or 06 maybe mentioning that when you apply the chunk 2 fixes to the rest of the document there would likely be soup trash you need to clean up but you didn't.



Notes, messages Conversation and forms

Obtaining goods and services

Interviewing and being interviewed

Using telecommunications

The other scales then follow:

Online conversation Turntaking and discussion

Asking for clarification



---

page 94 tells me that there is a systemic issue where earlier broken artifacts (in this case table title output) ended up in the name of the artifact id name, and the header text, for example below `cfiiceps` is wrong in several places. All table IDs need to be reviewed and corrected. 

<!-- db:id=scale_relaying_cfiiceps_information type=descriptor_scale product_tier=context pages=94-95 -->
### Relaying cfiiceps information | scale_relaying_cfiiceps_information

| Level | Relaying specific information in speech or sign | Relaying specific information in writing |
|-------|--------------------------------------------------|------------------------------------------|
| C2 | No descriptors available; see C1 | No descriptors available; see B2 |
| C1 | Can explain (in Language B) the relevance of specific information found in a particular section of a long, complex text (in Language A). | No descriptors available; see B2 |
| B2 | Can relay (in Language B) which presentations given (in Language A) at a conference, or which articles in a book (in Language A) are particularly relevant for a specific purpose. | Can relay in writing (in Language B) which presentations at a conference (given in Language A) were relevant, pointing out which would be worth detailed consideration.<br>Can relay in writing (in Language B) the relevant point(s) contained in propositionally complex but well-structured texts (in Language A) within their fields of professional, academic and personal interest.<br>Can relay in writing (in Language B) the relevant point(s) contained in an article (in Language A) from an academic or professional journal. |
| | Can relay (in Language B) the main point(s) contained in formal correspondence and/or reports (in Language A) on general subjects and on subjects related to their fields of interest. | Can relay in a written report (in Language B) relevant decisions that were taken in a meeting (in Language A).<br>Can relay in writing (in Language B) the significant point(s) contained in formal correspondence (in Language A). |
| B1 | Can relay (in Language B) the content of public announcements and messages delivered clearly at normal speed (in Language A).<br>Can relay (in Language B) the contents of detailed instructions or directions, provided these are clearly articulated (in Language A).<br>Can relay (in Language B) specific information given in straightforward informational texts (e.g. leaflets, brochure entries, notices and letters or e-mails) (in Language A). | Can relay in writing (in Language B) specific information points contained in texts delivered (in Language A) on familiar subjects (e.g. calls, announcements and instructions).<br>Can relay in writing (in Language B) specific, relevant information contained in straightforward informational texts (in Language A) on familiar subjects.<br>Can relay in writing (in Language B) specific information given in a straightforward recorded message (left in Language A), provided the topics concerned are familiar and the delivery is slow and clear. |
| A2 | Can relay (in Language B) the point made in a clear announcement (in Language A) concerning familiar everyday subjects, though they may have to simplify the message and search for words/signs.<br>Can relay (in Language B) specific, relevant information contained in short, simple texts, labels and notices (in Language A) on familiar subjects. | Can relay in writing (in Language B) specific information contained in short simple informational texts (in Language A), provided the texts concern concrete, familiar subjects and are composed in simple everyday language. |
| | Can relay (in Language B) the point made in short, clear, simple messages, instructions and announcements, provided these are expressed slowly and clearly in simple language (in Language A).<br>Can relay (in Language B) in a simple way a series of short, simple instructions, provided the original (in Language A) is clearly and slowly articulated. | Can list (in Language B) the main points of short, clear, simple messages and announcements (given in Language A), provided they are clearly and slowly articulated.<br>Can list (in Language B) specific information contained in simple texts (in Language A) on everyday subjects of immediate interest or need. |
| A1 | Can relay (in Language B) simple, predictable information about times and places given in short, simple statements (delivered in Language A). | Can list (in Language B) names, numbers, prices and very simple information of immediate interest in oral texts (in Language A), provided the articulation is very slow and clear, with repetition. |
| Pre-A1 | Can relay (in Language B) simple instructions about places and times (given in Language A), provided these are repeated very slowly and clearly.<br>Can relay (in Language B) very basic information (e.g. numbers and prices) from short, simple, illustrated texts (in Language A). | Can list (in Language B) names, numbers, prices and very simple information from texts (in Language A) that are of immediate interest, that are composed in very simple language and contain illustrations. |
<!-- el:end id=scale_relaying_cfiiceps_information -->

---

my md reader needs a blank row between the element and id info and the table to render the table correctly

<!-- el:start type=artifact id=scale_cte_smargaid_shparg_ni_atad_explaining page=97 -->
| Level | Explaining data in speech or sign | Explaining data in writing | <-- this never renders as columns and rows, just the pipe symbols

Add a row after scales/table element and id info...

---


