[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location -LiteralPath $projectRoot
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is not installed or not in PATH.' }
    $remoteUrl = git remote get-url origin
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read origin remote.' }
    if ($remoteUrl -notmatch '^(https://github\.com/|git@github\.com:)wen-yan-chen/desertification-control(?:\.git)?/?$') {
        throw 'Origin is not the expected Practice2 repository. No files changed.'
    }
    $branchName = git branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branchName -ne 'main') { throw 'Switch to main after preserving your work; this script only synchronizes main.' }
    $pendingChanges = @(git status --porcelain)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect working tree.' }
    if ($pendingChanges.Count -gt 0) { throw 'Working tree has local changes or untracked files. Commit or preserve them before synchronizing.' }
    git fetch origin
    if ($LASTEXITCODE -ne 0) { throw 'Fetch failed; no local files overwritten.' }
    $aheadCount = git rev-list --count origin/main..HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect origin/main.' }
    if ([int]$aheadCount -gt 0) { throw 'Local main has unpushed commits. Review and merge remote changes manually before pushing.' }
    git merge --ff-only origin/main
    if ($LASTEXITCODE -ne 0) { throw 'Fast-forward update failed. Resolve divergence manually.' }
    $currentCommit = git rev-parse --short HEAD
    Write-Host "Synchronized main at $currentCommit. Other computers must synchronize separately."
} finally {
    Pop-Location
}
