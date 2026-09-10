# AI & Automation Internship Learning Portal

Static learning portal containing the generated Week 1, Week 2 and Week 3 HTML books.

## Files

- `index.html` — landing page
- `week-1.html` — Week 1 learning book
- `week-2.html` — Week 2 learning book
- `week-3.html` — Week 3 n8n learning book, drills, FlowGuard and HR Intake
- `week-3-materials.zip` — Week 3 Markdown, local mock API/tests and workflow examples
- `week-3-assets/workflows/` — individual downloadable workflow JSON files
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
