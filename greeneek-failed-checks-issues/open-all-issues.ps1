param(
    [switch]$DryRun,
    [string]$Repo = "Mostafa-Taher-git/Greeneek"
)

$ErrorActionPreference = "Stop"
$PayloadsPath = Join-Path $PSScriptRoot "issues-payloads.json"
$Issues = Get-Content -Raw -Encoding UTF8 $PayloadsPath | ConvertFrom-Json

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI ('gh') is required. Install from https://cli.github.com/ and run 'gh auth login'."
}

if (-not $DryRun) {
    gh auth status | Out-Null
}

$ExistingJson = gh api --paginate "repos/$Repo/issues?state=open&per_page=100"
$ExistingTitles = @()
if ($ExistingJson) {
    $ExistingTitles = ($ExistingJson | ConvertFrom-Json) | ForEach-Object { $_.title }
}

Write-Host "Preparing to process $($Issues.Count) issue(s) for $Repo (DryRun=$DryRun)..."

for ($i = 0; $i -lt $Issues.Count; $i++) {
    $Issue = $Issues[$i]
    $Index = $i + 1
    if ($ExistingTitles -contains $Issue.title) {
        Write-Host "[$Index/$($Issues.Count)] SKIP (already open): $($Issue.title)"
        continue
    }

    if ($DryRun) {
        $Labels = ($Issue.labels -join ", ")
        Write-Host "[$Index/$($Issues.Count)] DRY-RUN would create: $($Issue.title) (labels=[$Labels], body=$($Issue.body.Length) chars)"
    } else {
        $JsonBody = $Issue | ConvertTo-Json -Depth 10 -Compress
        $CreatedUrl = $JsonBody | gh api "repos/$Repo/issues" --method POST --input - --jq ".html_url"
        Write-Host "[$Index/$($Issues.Count)] CREATED: $CreatedUrl - $($Issue.title)"
        Start-Sleep -Seconds 1
    }
}

Write-Host "Done."
