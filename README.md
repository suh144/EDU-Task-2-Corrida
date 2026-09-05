Product Requirements Document
Tradie in trAIning
Motto: "The AI Whisperer for the AI Worshipper"

Team: Edu Track2 Corrida — Maneesh (Team Lead), Suha, Daria Event: MentorME Futura Remix Hackathon — Brisbane, September 2026 Track: Track 2 — Education and Student Success Submission deadline: 2:30pm Sunday, 6 September 2026

1. Problem Statement
Students frequently paste assignment questions directly into generic AI tools and receive instant, ready-made answers. This produces two problems:

De-skilling — students don't build genuine understanding of the material because they never attempt the reasoning themselves.
Academic integrity risk — many assessments explicitly prohibit using AI to generate answers, leaving students without a safe, sanctioned way to use AI for study support.
Who experiences this: University students (demonstrated with QUT students, using real unit material) across any discipline, at any stage of a course.

Why it matters: Employers increasingly expect graduates who can think critically and apply knowledge, not just produce AI-generated outputs. A tool that builds genuine understanding — rather than bypassing it — directly supports both learning outcomes and future employability.

2. Target User
A university student working through their own course material (lecture slides, readings, notes, assignments) who wants to actually understand the content — not just get an answer — either because they choose to, or because their assessment doesn't permit AI-generated answers.

Demo persona: One QUT student, one specific unit's real material, used as the live walkthrough example.

3. Proposed Solution
A web app where a student uploads their own course material. Instead of answering questions directly, the tool:

Reads and previews the material — showing the topics it covers and a suggested number of study checkpoints
Lets the student adjust the number of checkpoints and optionally focus on a specific topic
Breaks the material into checkpoints, each with:
A guiding question (not yes/no)
An optional hint
Brief feedback on the student's attempt
A full explanation, revealed only after the student has had a go
Everything is grounded strictly in the student's own uploaded material — not a generic AI answer pulled from elsewhere
Core value proposition: an AI study companion that makes students do the "reps" instead of skipping straight to the answer — safe to use even where AI-generated answers for assessments aren't allowed.

4. MVP Scope (what we are building this weekend)
Feature	Status
Upload course material (PDF, DOCX, PPTX, TXT, images)	✅ Build
Text extraction from documents	✅ Build
Image/diagram analysis via vision-capable AI	✅ Build
Outline preview (topics + suggested checkpoint count) before starting	✅ Build
Adjustable checkpoint count (student choice, 3–15)	✅ Build
Optional topic focus	✅ Build
Guided question → hint → feedback → reveal explanation flow	✅ Build
Resilient error handling (auto-retry, graceful failure messages)	✅ Build
Demo safety net (preloaded backup checkpoints in case live API fails)	✅ Build
Basic accessibility touches (clear labelling, plain language)	🟡 Stretch, time-permitting
Light rewards/progress indicator	🟡 Stretch, time-permitting
5. Explicitly Out of Scope (Future Development)
These were discussed by the team but are deliberately not built for this hackathon submission — they appear in our pitch as future roadmap items, not the working prototype:

Multi-source scaffolding with ranked, external reputable sources (minimum 5, ranked for accuracy) — would require web search integration and a source-credibility system; a substantial second feature set on its own.
Employer-facing real-time employability dashboard — a second application with a second user type (employer login, skills analytics, real-time tracking). Scoped as a clear next-stage product, not an MVP feature.
Full gamification system (points, badges, sounds) — nice-to-have, not core to proving the concept.
Automated fact-checking / self-correction layer — the current design already reduces this risk by grounding checkpoints strictly in the student's own uploaded material, rather than open-ended AI recall; a dedicated verification layer is a future enhancement, not core to the MVP.
6. Technology Overview
Frontend/App framework: Streamlit (Python) — chosen for fast build time, built-in file upload, and natural handling of step-by-step state via session_state.
AI model: Anthropic Claude (Sonnet) via the Anthropic API — used for:
Generating the topic outline and suggested checkpoint count
Generating checkpoint questions, hints, and explanations
Describing image-based material (diagrams, hand-drawn notes, scanned pages) via vision capability
Giving brief feedback on student answers
Document parsing: pdfplumber (PDF), python-docx (Word), python-pptx (PowerPoint), native text decoding (TXT)
Resilience: automatic retry with backoff on API connection errors/rate limits; graceful error messages instead of crashes; a manual "backup checkpoints" fallback for live demo safety
Deployment: local server (streamlit run app.py) — no cloud hosting required for this prototype
Known technical limitations (stated openly, not hidden):

One file processed per session in this prototype; combining multiple files is a reasonable next step
Image analysis quality depends on clarity of the photo/scan
No user accounts/login — acceptable for a hackathon demo, would need authentication for real deployment
Checkpoint quality depends on how well-structured the source material is
7. Implementation Plan
Who could use this: QUT (or any university) learning support services, individual course coordinators, or student support/success teams, as a supplementary study tool alongside existing LMS content.
What would be required to adopt it: hosting infrastructure beyond a local server, integration with institutional learning management systems (optional), an ongoing AI API budget, and a review process to confirm it meets institutional academic integrity and data privacy policies.
Key risks: reliance on third-party AI API availability and cost at scale; need for clear policy on how "AI-assisted study support" is distinguished from "AI-generated assessment answers" in university academic integrity guidelines.
Next steps: pilot with a small group of students in one unit, gather structured feedback, then evaluate multi-file support and the future-development features above.
8. Impact Measurement
Planned/possible indicators of success:

Qualitative feedback from hackathon cohort testing (informal, pre-pitch): did the guided approach feel clearer than a direct AI answer?
Checkpoint completion rate (did students finish the guided session, or drop off?)
Self-reported confidence before vs. after a guided session on a topic
(For a real deployment) reduced reliance on direct AI-answer tools for assessments, and instructor-reported understanding/engagement improvements
9. Responsible AI & Accessibility Considerations
Privacy: the tool only processes material the student themselves uploads; no other personal or employment data is collected in this prototype.
Transparency: all guidance is explicitly grounded in the uploaded material, not external or invented content.
Human oversight: the tool guides and hints; it does not make high-stakes decisions about the student without their own engagement and judgement.
Accessibility: intended to work regardless of the student's cultural/language background, digital confidence, or prior education level; plain-language design is a stated goal.
10. Team & Roles
Person	Primary responsibility
Maneesh (Team Lead)	Technical build, AI prompt logic, implementation
Suha	Data/source-accuracy logic, testing, impact metrics
Daria	Business narrative, pitch deck, demo script, accessibility/ethics considerations
(3-person team covering all judged areas: problem understanding, technical build, data/AI thinking, business communication, and final pitch.)

11. Submission Checklist
[ ] Problem statement
[ ] Proposed solution
[ ] Working prototype / proof of concept
[ ] Technology overview
[ ] Implementation plan
[ ] Impact measurement
[ ] Pitch slides (PDF or PPTX)
[ ] Demo video/live walkthrough
