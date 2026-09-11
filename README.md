# AI & Automation Internship Learning Portal

Static learning portal containing the generated Week 1 through Week 4 HTML books.

## Files

- `index.html` — landing page
- `week-1.html` — Week 1 learning book
- `week-2.html` — Week 2 learning book
- `week-3.html` — Week 3 n8n learning book, drills, FlowGuard and HR Intake
- `week-3-materials.zip` — Week 3 Markdown, local mock API/tests and workflow examples
- `week-3-assets/workflows/` — individual downloadable workflow JSON files
- `week-4.html` — Week 4 LLM and AI integration book
- `week-4-materials.zip` — Week 4 source lessons, mock AI lab, tests and synthetic PDF fixtures
- `week-4-assets/` — individual source and fixture downloads linked from the book
- `vercel.json` — clean static deployment configuration

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
