# AI & Automation Internship Learning Portal

Static portal containing the Book 00–08 textbook collection, the original five-week learning path, embedded visual notes, reusable scripts and delivery templates, two full reference projects, a guided end-to-end project and quick-reference atlases.

## Files

- `index.html` — landing page
- `book-00.html` / `book-00-materials.zip` — Developer Toolkit and command-line foundation
- `week-1.html` — Week 1 learning book
- `week-2.html` — Week 2 learning book
- `week-2-materials.zip` — Week 2 Markdown, drills and API Sentinel starter
- `week-3.html` — Week 3 n8n learning book, drills, FlowGuard and HR Intake
- `week-3-materials.zip` — Week 3 Markdown, local mock API/tests and workflow examples
- `week-3-assets/workflows/` — individual downloadable workflow JSON files
- `week-4.html` — Week 4 LLM and AI integration book
- `week-4-materials.zip` — Week 4 source lessons, mock AI lab, tests and synthetic PDF fixtures
- `week-4-assets/` — individual source and fixture downloads linked from the book
- `vercel.json` — clean static deployment configuration
- `week-5.html` — Git, Docker, clean code, durable workers, documentation and capstones
- `week-5-materials.zip` — source lessons, local capstone/tests, Compose and ReleaseGuard starter
- `week-5-assets/` — individual source and workflow downloads linked from the book
- `book-06.html` / `book-06-materials.zip` — System Design & Delivery Playbook
- `book-07.html` / `book-07-materials.zip` — intake-to-handoff textbook, reusable templates and two filled examples
- `book-08.html` / `book-08-materials.zip` — practical script library plus Reliable Intake & Review and Daily Operations Report full projects
- `book-08-assets/` — individually viewable source files linked from Book 08
- `project-01.html` / `project-01-materials.zip` — Resume Evidence Assistant Lite guided build, synthetic fixtures, hints, acceptance matrix and delivery rubric
- `command-atlas.html` — searchable command reference
- `debugging-atlas.html` — symptom-to-layer debugging reference
- `technical-glossary.html` — Thai/English engineering vocabulary
- `reference-atlases.zip` — Markdown source of all three reference pages

## Preview locally

Opening `index.html` directly is sufficient. Alternatively:

```powershell
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Deploy through GitHub and Vercel

1. Create an empty GitHub repository without README, gitignore or license.
2. Initialize Git in this folder and push the `main` branch.
3. Import the repository in Vercel.
4. Keep Framework Preset as `Other` and leave Build Command empty.
5. Use the repository root as the Root Directory and deploy.

The generated Week HTML files should be refreshed from their source folders whenever the Markdown curriculum changes.

Week 3's mock API is **local-only**. This portal hosts the book and downloadable source, not a live API or n8n instance. Workflow examples contain synthetic data and no credentials. Read Verification in the Week 3 book for the exact test coverage and limitations.

Week 4 also runs with a local-only mock provider by default. The optional paid-provider example is not enabled by the portal or the lab API. Read the Week 4 Verification section: mock regression results are not real-model accuracy, and DOCX parser tests do not certify a rendered DOCX sample.

Week 5 provides local-only synthetic Transaction and HR capstones. The portal does not run their API, worker, database or n8n. Reference tests and native process checks are separate from the deliberately failing ReleaseGuard starter. Docker Compose configuration has been checked, but container runtime verification remains pending; see Verification in the book.

Project 01 is a build-it-yourself exercise rather than a completed implementation. It uses synthetic resume text and a deterministic Mock AI; it must not be represented as a production hiring, ranking or rejection system.
