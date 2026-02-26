param(
    [string]$Repo = "https://github.com/phreakin/cannabis.git",
    [string]$Branch = "main",
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

function Require-Cmd {
    param([Parameter(Mandatory=$true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "Missing required command: $Name. Install it and try again." -ForegroundColor Red
        throw "Missing required command: $Name"
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)][string]$Args,
        [switch]$Fatal
    )

    $tmpOut = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()

    try {
        $p = Start-Process -FilePath "git" `
      -ArgumentList $Args `
      -NoNewWindow `
      -Wait `
      -PassThru `
      -RedirectStandardOutput $tmpOut `
      -RedirectStandardError $tmpErr

        $exit = $p.ExitCode

        $stdout = @()
        $stderr = @()

        if (Test-Path $tmpOut) { $stdout = Get-Content -Path $tmpOut -ErrorAction SilentlyContinue }
        if (Test-Path $tmpErr) { $stderr = Get-Content -Path $tmpErr -ErrorAction SilentlyContinue }

        # Print line-by-line with smart coloring:
        # - fatal/error -> Red
        # - warning -> Yellow
        # - normal output -> Gray on success, Red on failure
        $baseColor = if ($exit -eq 0) { 'Gray' } else { 'Red' }

        foreach ($line in ($stdout + $stderr)) {
            $t = "$line"
            if ($t.Trim().Length -eq 0) { continue }

            $lc = $t.ToLowerInvariant()
            if ($lc.StartsWith("fatal:") -or $lc.StartsWith("error:")) {
                Write-Host $t -ForegroundColor Red
            }
            elseif ($lc.StartsWith("warning:")) {
                Write-Host $t -ForegroundColor Yellow
            }
            else {
                Write-Host $t -ForegroundColor $baseColor
            }
        }

        if ($exit -ne 0 -and $Fatal) {
            throw "git $Args failed (exit code $exit)"
        }

        return $exit
    }
    finally {
        Remove-Item $tmpOut, $tmpErr -ErrorAction SilentlyContinue
    }
}

Write-Host "Preparing GitHub repo: $Repo (branch: $Branch)" -ForegroundColor Cyan

Require-Cmd git

# --- Ensure we're in a repo root (or init it) ---
if (-not (Test-Path ".git")) {
    Write-Host "No .git found, initializing new repository..." -ForegroundColor Yellow
    Invoke-Git -Args "init" -Fatal | Out-Null
} else {
    Write-Host "Git repository detected." -ForegroundColor Green
}

# --- Ensure .gitignore exists ---
$gitignorePath = ".gitignore"
if (-not (Test-Path $gitignorePath)) {
    Write-Host "No .gitignore found, creating one..." -ForegroundColor Yellow
    @"
# --- JetBrains / IntelliJ / PyCharm ---
.idea/
*.iws
out/
.idea_modules/
atlassian-ide-plugin.xml
com_crashlytics_export_strings.xml
crashlytics.properties
crashlytics-build.properties
fabric.properties

# --- CMake ---
cmake-build-*/

# --- Logs / temp ---
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*
*.pid
*.seed
*.pid.lock

# --- Node / JS deps & build output ---
node_modules/
jspm_packages/
web_modules/
bower_components/
build/Release/
coverage/
.nyc_output/
.cache/
.parcel-cache/
.grunt/
.next/
.nuxt/
dist/
.vuepress/dist/
.temp/
.docusaurus/
.serverless/
.fusebox/
.dynamodb/
.tern-port
.vscode-test

# Yarn v2+ / PnP
.yarn/cache/
.yarn/unplugged/
.yarn/build-state.yml
.yarn/install-state.gz
.pnp.*

# --- Env files (secrets) ---
.env
.env.*
!.env.example

# --- Python ---
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
venv/
env/
ENV/

# Packaging / builds
build/
dist/
develop-eggs/
eggs/
.eggs/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Test / coverage
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Django / Flask / misc
local_settings.py
db.sqlite3
db.sqlite3-journal
instance/
.webassets-cache/
.scrapy
docs/_build/
.ipynb_checkpoints/
profile_default/
ipython_config.py
target/
site/

# Type checkers
.mypy_cache/
.dmypy.json
.pyre/
.pytype/

# PHP / Composer
/vendor/
"@ | Set-Content -Encoding UTF8 $gitignorePath
    Write-Host "Created .gitignore" -ForegroundColor Green
} else {
    Write-Host ".gitignore exists." -ForegroundColor Green
}

# --- Ensure README exists ---
$readmePath = "README.md"
if (-not (Test-Path $readmePath)) {
    Write-Host "No README.md found, creating a template..." -ForegroundColor Yellow
    $projectName = Split-Path -Leaf (Get-Location)
    @"
# $projectName

## What this is
Describe the purpose of this repository in 1–2 sentences.

## Setup
### Prerequisites
- Git
- (add runtime requirements here)

### Install
\`\`\`bash
# example
# npm install
# composer install
\`\`\`

## Usage
\`\`\`bash
# example
# npm run dev
\`\`\`

## Notes
- Add anything important (env vars, deployment notes, etc).
"@ | Set-Content -Encoding UTF8 $readmePath
    Write-Host "Created README.md" -ForegroundColor Green
} else {
    Write-Host "README.md exists." -ForegroundColor Green
}

# --- Normalize branch name ---
Write-Host "Ensuring branch is named: $Branch" -ForegroundColor Cyan
Invoke-Git -Args "branch -M $Branch" -Fatal | Out-Null

# --- Set/repair remote origin ---
Write-Host "Ensuring remote origin is set to: $Repo" -ForegroundColor Cyan
$existingOrigin = ""
try { $existingOrigin = (git remote get-url origin 2>$null) } catch { $existingOrigin = "" }

if ([string]::IsNullOrWhiteSpace($existingOrigin)) {
    Write-Host "No origin found. Adding origin..." -ForegroundColor Yellow
    Invoke-Git -Args "remote add origin $Repo" -Fatal | Out-Null
} elseif ($existingOrigin -ne $Repo) {
    Write-Host "Origin differs. Updating origin..." -ForegroundColor Yellow
    Invoke-Git -Args "remote set-url origin $Repo" -Fatal | Out-Null
} else {
    Write-Host "Origin already set correctly." -ForegroundColor Green
}

# --- Show status ---
Write-Host "`n--- git status ---" -ForegroundColor Cyan
git status

# --- Stage changes ---
Write-Host "`n--- staging changes ---" -ForegroundColor Cyan
Invoke-Git -Args "add -A" -Fatal | Out-Null
Write-Host "Staging complete." -ForegroundColor Green

# --- Commit message default ---
if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $CommitMessage = "Update $ts"
    Write-Host "Commit message: $CommitMessage" -ForegroundColor Yellow
} else {
    Write-Host "Commit message: $CommitMessage" -ForegroundColor Green
}

# --- Commit if anything staged ---
Write-Host "`n--- committing ---" -ForegroundColor Cyan
$staged = git diff --cached --name-only
if ($staged) {
    Invoke-Git -Args "commit -m `"$CommitMessage`"" -Fatal | Out-Null
    Write-Host "Commit successful." -ForegroundColor Green
} else {
    Write-Host "No staged changes to commit." -ForegroundColor Yellow
}

# --- Pull ---
Write-Host "`n--- pulling ---" -ForegroundColor Cyan
try {
    Invoke-Git -Args "pull origin $Branch --allow-unrelated-histories" -Fatal | Out-Null
    Write-Host "Pull successful." -ForegroundColor Green
} catch {
    Write-Host "Pull failed. If there are conflicts:" -ForegroundColor Red
    Write-Host "  1) Resolve the conflicted files" -ForegroundColor Yellow
    Write-Host "  2) git add -A" -ForegroundColor Yellow
    Write-Host "  3) git commit -m `"Resolve merge conflicts`"" -ForegroundColor Yellow
    Write-Host "  4) git push" -ForegroundColor Yellow
    throw
}

# --- Push ---
Write-Host "`n--- pushing ---" -ForegroundColor Cyan
Invoke-Git -Args "push -u origin $Branch" -Fatal | Out-Null
Write-Host "Push successful." -ForegroundColor Green

Write-Host "`nDone. Synced with: $Repo ($Branch)" -ForegroundColor Green