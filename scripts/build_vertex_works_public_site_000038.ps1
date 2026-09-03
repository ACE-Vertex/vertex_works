#requires -Version 7.0
param(
    [string] $WorksRoot = "G:\Vertex_Project\Development\vertex_works",
    [string] $VertexStudioRoot = "G:\Vertex_Project\Development\vertex_studio_ai",
    [string] $HostName = "vertex.a-portal.net",
    [string] $Route = "vertex-works",
    [switch] $SkipGitPush
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ============================================================
# VERTEX WORKS PUBLIC SITE BUILDER 000041
#
# Existing Vertex Hub builder already owns:
#   G:\Vertex_Project\Development\vertex_studio_ai\VertexHub\site
# as the public site root for vertex.a-portal.net.
#
# Therefore this builder does NOT query IIS at all.
# It deploys under the already-established Vertex Hub public root.
# ============================================================

$sourceRoot = Join-Path $WorksRoot "site\vertex-works-public"
$scriptRoot = Join-Path $WorksRoot "scripts"
$backupRoot = Join-Path $WorksRoot "site\_deployment_backups\vertex-works"

$hubRoot = Join-Path $VertexStudioRoot "VertexHub"
$hubDefaultSiteRoot = Join-Path $hubRoot "site"
$hubDeploymentManifest = Join-Path $hubRoot "deployment.json"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Test-PathUnder {
    param(
        [Parameter(Mandatory)][string] $Candidate,
        [Parameter(Mandatory)][string] $Parent
    )
    $candidateFull = [System.IO.Path]::GetFullPath($Candidate).TrimEnd('\') + '\'
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    return $candidateFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Resolve-HubPublicRoot {
    if (Test-Path $hubDeploymentManifest) {
        try {
            $manifest = Get-Content $hubDeploymentManifest -Raw -Encoding UTF8 | ConvertFrom-Json
            $candidate = [string]$manifest.physicalPath
            if ($candidate -and (Test-PathUnder -Candidate $candidate -Parent $VertexStudioRoot)) {
                Write-Host "Hub Root      : deployment.json" -ForegroundColor DarkGray
                return [Environment]::ExpandEnvironmentVariables($candidate)
            }
            Write-Warning "deployment.json physicalPath was missing or outside vertex_studio_ai; using canonical fallback."
        }
        catch {
            Write-Warning "Could not read VertexHub deployment.json; using canonical fallback."
        }
    }

    Write-Host "Hub Root      : canonical fallback" -ForegroundColor DarkGray
    return $hubDefaultSiteRoot
}

function Invoke-GitClosure {
    param(
        [Parameter(Mandatory)][string] $RepoRoot,
        [Parameter(Mandatory)][string[]] $Paths,
        [Parameter(Mandatory)][string] $Message,
        [switch] $NoPush
    )

    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Write-Warning "Git closure skipped: git not found"
        return
    }

    $inside = (& git -C $RepoRoot rev-parse --is-inside-work-tree 2>$null)
    if ($LASTEXITCODE -ne 0 -or $inside -ne "true") {
        Write-Warning "Git closure skipped: $RepoRoot is not a Git work tree"
        return
    }

    $existingPaths = @()
    foreach ($p in $Paths) {
        $existingPaths += $p
    }

    $changed = & git -C $RepoRoot status --porcelain -- @existingPaths
    if (-not $changed) {
        Write-Host "GIT COMMIT    : no owned changes in $RepoRoot"
        return
    }

    & git -C $RepoRoot add -- @existingPaths
    if ($LASTEXITCODE -ne 0) { throw "git add failed in $RepoRoot" }

    & git -C $RepoRoot commit --only -m $Message -- @existingPaths
    if ($LASTEXITCODE -ne 0) { throw "git commit failed in $RepoRoot" }

    $branch = (& git -C $RepoRoot branch --show-current).Trim()
    Write-Host "GIT COMMIT    : PASS $RepoRoot ($branch)" -ForegroundColor Green

    if ($NoPush) {
        Write-Host "GIT PUSH      : SKIPPED by -SkipGitPush"
        return
    }

    $origin = (& git -C $RepoRoot remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $origin) {
        Write-Warning "GIT PUSH skipped: origin unavailable in $RepoRoot"
        return
    }

    & git -C $RepoRoot push origin $branch
    if ($LASTEXITCODE -ne 0) { throw "git push failed in $RepoRoot" }
    Write-Host "GIT PUSH      : PASS origin/$branch" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host " VERTEX WORKS PUBLIC SITE BUILDER 000041" -ForegroundColor DarkYellow
Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host ""

if (-not (Test-Path $sourceRoot)) {
    throw "Canonical site source missing: $sourceRoot"
}
if (-not (Test-Path $hubRoot)) {
    throw "Vertex Hub root missing: $hubRoot"
}

$hubSiteRoot = Resolve-HubPublicRoot
New-Item -ItemType Directory -Force -Path $hubSiteRoot | Out-Null

if (-not (Test-PathUnder -Candidate $hubSiteRoot -Parent $VertexStudioRoot)) {
    throw "Resolved Hub public root is outside vertex_studio_ai: $hubSiteRoot"
}

$deployRoot = Join-Path $hubSiteRoot $Route

Write-Host "Host          : $HostName"
Write-Host "Hub Site Root : $hubSiteRoot"
Write-Host "Deploy Route  : /$Route"
Write-Host "Deploy Path   : $deployRoot"

# ------------------------------------------------------------
# 1. BACKUP EXISTING DEPLOYMENT
# ------------------------------------------------------------

New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

if ((Test-Path $deployRoot) -and
    ((Get-ChildItem $deployRoot -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)) {
    $backupPath = Join-Path $backupRoot $timestamp
    New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
    Copy-Item (Join-Path $deployRoot "*") $backupPath -Recurse -Force
    Write-Host "Backup        : $backupPath" -ForegroundColor DarkGray
}
else {
    Write-Host "Backup        : skipped (no previous deployment)" -ForegroundColor DarkGray
}

# ------------------------------------------------------------
# 2. PRESERVE RUNTIME COUNTER DATA
# ------------------------------------------------------------

$runtimeBackup = $null
$runtimeData = Join-Path $deployRoot "data"
if (Test-Path $runtimeData) {
    $runtimeBackup = Join-Path $env:TEMP "vertex-works-counter-$timestamp"
    Copy-Item $runtimeData $runtimeBackup -Recurse -Force
}

# ------------------------------------------------------------
# 3. DEPLOY INTO EXISTING VERTEX HUB PUBLIC ROOT
# ------------------------------------------------------------

if (Test-Path $deployRoot) {
    Remove-Item $deployRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $deployRoot | Out-Null
Copy-Item (Join-Path $sourceRoot "*") $deployRoot -Recurse -Force

if ($runtimeBackup -and (Test-Path $runtimeBackup)) {
    Remove-Item (Join-Path $deployRoot "data") -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item $runtimeBackup (Join-Path $deployRoot "data") -Recurse -Force
    Remove-Item $runtimeBackup -Recurse -Force -ErrorAction SilentlyContinue
}

# ------------------------------------------------------------
# 4. COUNTER WRITE PERMISSION
# No IIS administration API required.
# ------------------------------------------------------------

$dataPath = Join-Path $deployRoot "data"
New-Item -ItemType Directory -Force -Path $dataPath | Out-Null

try {
    $acl = Get-Acl $dataPath
    $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
        "IIS_IUSRS",
        "Modify",
        "ContainerInherit,ObjectInherit",
        "None",
        "Allow"
    )
    $acl.SetAccessRule($rule)
    Set-Acl -Path $dataPath -AclObject $acl
    Write-Host "Counter ACL   : MODIFY -> IIS_IUSRS" -ForegroundColor Green
}
catch {
    Write-Warning "Could not grant IIS_IUSRS Modify permission automatically: $($_.Exception.Message)"
}

# ------------------------------------------------------------
# 5. VERIFY SOURCE + DEPLOYED COPY
# ------------------------------------------------------------

$verifier = Join-Path $scriptRoot "verify_vertex_works_public_site_000038.py"
if (-not (Test-Path $verifier)) {
    throw "Verifier missing: $verifier"
}

& python $verifier --source-root $sourceRoot --deploy-root $deployRoot
if ($LASTEXITCODE -ne 0) {
    throw "Vertex Works public site source/deploy verifier failed"
}

# ------------------------------------------------------------
# 6. PUBLIC HTTP CHECK
# ------------------------------------------------------------

$url = "https://$HostName/$Route/"
try {
    $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 20 -UseBasicParsing
    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
        Write-Host "HTTP CHECK     : PASS ($($response.StatusCode)) $url" -ForegroundColor Green
    }
    else {
        Write-Warning "HTTP CHECK returned status $($response.StatusCode): $url"
    }
}
catch {
    Write-Warning "HTTP CHECK unavailable: $($_.Exception.Message)"
}

# ------------------------------------------------------------
# 7. GIT CLOSURE
# Commit/push only paths owned by this task.
# ------------------------------------------------------------

$worksPaths = @(
    "site/vertex-works-public",
    "scripts/build_vertex_works_public_site_000038.ps1",
    "scripts/verify_vertex_works_public_site_000038.py",
    "scripts/run_vertex_works_public_site_000039.py",
    "scripts/run_vertex_works_public_site_000040.py",
    "scripts/run_vertex_works_public_site_000041.py",
    "docs/VERTEX_WORKS_PUBLIC_SITE_000038.md",
    "docs/VERTEX_WORKS_PUBLIC_SITE_RUNNER_HOTFIX_000039.md",
    "docs/VERTEX_WORKS_PUBLIC_SITE_IIS_DISCOVERY_HOTFIX_000040.md",
    "docs/VERTEX_WORKS_PUBLIC_SITE_HUB_ROOT_HOTFIX_000041.md"
)

Invoke-GitClosure `
    -RepoRoot $WorksRoot `
    -Paths $worksPaths `
    -Message "feat(web): publish Vertex Works public site" `
    -NoPush:$SkipGitPush

$hubRelative = "VertexHub/site/$Route"
Invoke-GitClosure `
    -RepoRoot $VertexStudioRoot `
    -Paths @($hubRelative) `
    -Message "feat(hub): publish Vertex Works public route" `
    -NoPush:$SkipGitPush

Write-Host ""
Write-Host "VERTEX_WORKS_PUBLIC_SITE_000041=PASS" -ForegroundColor Green
Write-Host "URL=$url"
Write-Host "SOURCE=$sourceRoot"
Write-Host "DEPLOY=$deployRoot"
