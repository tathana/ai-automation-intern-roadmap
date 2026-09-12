param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath
)

$ErrorActionPreference = "Stop"

$resolvedParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $TargetPath))
$resolvedTarget = [System.IO.Path]::GetFullPath($TargetPath)

if ([string]::IsNullOrWhiteSpace((Split-Path -Leaf $resolvedTarget))) {
    throw "TargetPath must name a dedicated new lab directory."
}

if ($resolvedTarget -eq [System.IO.Path]::GetPathRoot($resolvedTarget)) {
    throw "Refusing to use a drive root as the lab target."
}

if (Test-Path -LiteralPath $resolvedTarget) {
    throw "Target already exists. Choose a new empty lab path: $resolvedTarget"
}

New-Item -ItemType Directory -Path $resolvedTarget | Out-Null

$remote = Join-Path $resolvedTarget "remote.git"
$seed = Join-Path $resolvedTarget "seed"
$alice = Join-Path $resolvedTarget "alice"
$bob = Join-Path $resolvedTarget "bob"

git init --bare $remote | Out-Null
git clone $remote $seed | Out-Null

Push-Location $seed
try {
    git config user.name "Lab Setup"
    git config user.email "lab@example.invalid"

    @'
APP_NAME = "Resume Helper"
MAX_FILES = 10

def build_summary(candidate_name: str) -> str:
    return f"Candidate: {candidate_name}"
'@ | Set-Content -LiteralPath "app.py" -Encoding UTF8

    @'
from app import build_summary, MAX_FILES

assert build_summary("Ada") == "Candidate: Ada"
assert MAX_FILES > 0
print("checks passed")
'@ | Set-Content -LiteralPath "check_app.py" -Encoding UTF8

    @'
# Git Rescue Lab

Run `python check_app.py` to verify behavior.
'@ | Set-Content -LiteralPath "README.md" -Encoding UTF8

    @'
__pycache__/
*.pyc
.env
*.log
'@ | Set-Content -LiteralPath ".gitignore" -Encoding UTF8

    @'
API_TOKEN=replace_me
'@ | Set-Content -LiteralPath ".env.example" -Encoding UTF8

    git add app.py check_app.py README.md .gitignore .env.example
    git commit -m "chore: establish rescue lab baseline" | Out-Null
    git branch -M main
    git push -u origin main | Out-Null
    git --git-dir=$remote symbolic-ref HEAD refs/heads/main

    git switch -c feature/resume-summary | Out-Null
    @'
APP_NAME = "Resume Helper"
MAX_FILES = 10

def normalize_candidate_name(value: str) -> str:
    return value.strip()

def build_summary(candidate_name: str) -> str:
    name = normalize_candidate_name(candidate_name)
    return f"Resume summary for: {name}"
'@ | Set-Content -LiteralPath "app.py" -Encoding UTF8
    git add app.py
    git commit -m "feat: normalize candidate summary input" | Out-Null
    git push -u origin feature/resume-summary | Out-Null

    git switch main | Out-Null
    @'
APP_NAME = "Resume Helper"
MAX_FILES = -1

def build_summary(candidate_name: str) -> str:
    return f"Candidate: {candidate_name}"
'@ | Set-Content -LiteralPath "app.py" -Encoding UTF8
    git add app.py
    git commit -m "feat: allow unlimited resume batches" | Out-Null
    git push origin main | Out-Null

    git switch -c recovery/important-notes | Out-Null
    @'
# Recovery Notes

Preserve input normalization and require a positive batch limit.
'@ | Set-Content -LiteralPath "RECOVERY_NOTES.md" -Encoding UTF8
    git add RECOVERY_NOTES.md
    git commit -m "docs: record validation requirements" | Out-Null
    git switch main | Out-Null
    git branch -D recovery/important-notes | Out-Null
}
finally {
    Pop-Location
}

git clone $remote $alice | Out-Null
git clone $remote $bob | Out-Null

Push-Location $alice
try {
    git config user.name "Alice Learner"
    git config user.email "alice@example.invalid"

    git switch -c recovery/local-important-notes | Out-Null
    @'
# Local Recovery Notes

The final merge must preserve input normalization and a positive batch limit.
'@ | Set-Content -LiteralPath "LOCAL_RECOVERY_NOTES.md" -Encoding UTF8
    git add LOCAL_RECOVERY_NOTES.md
    git commit -m "docs: capture local rescue requirements" | Out-Null
    git switch main | Out-Null
    git branch -D recovery/local-important-notes | Out-Null

    @'
API_TOKEN=training-placeholder-never-commit
'@ | Set-Content -LiteralPath ".env" -Encoding UTF8

    @'
temporary debug output
'@ | Set-Content -LiteralPath "debug.log" -Encoding UTF8

    Add-Content -LiteralPath "app.py" -Value "`n# TODO: add evidence validation"
    Add-Content -LiteralPath "README.md" -Value "`n## Local development`nUse synthetic resumes only."
    git add app.py
    Add-Content -LiteralPath "app.py" -Value "# TODO: add structured audit output"
}
finally {
    Pop-Location
}

Push-Location $bob
try {
    git config user.name "Bob Teammate"
    git config user.email "bob@example.invalid"
    Add-Content -LiteralPath "README.md" -Value "`n## Team note`nAlways run checks before review."
    git add README.md
    git commit -m "docs: add team verification note" | Out-Null
    git push origin main | Out-Null
}
finally {
    Pop-Location
}

Write-Output "Git Rescue Lab created at: $resolvedTarget"
Write-Output "Start in: $alice"
Write-Output "Read MISSION.md before changing repository state."
