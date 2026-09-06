# AI & Automation Internship Learning Portal

Static learning portal containing the generated Week 1 and Week 2 HTML books.

## Files

- `index.html` — landing page
- `week-1.html` — Week 1 learning book
- `week-2.html` — Week 2 learning book
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
