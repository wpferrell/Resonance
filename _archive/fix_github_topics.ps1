# Fix GitHub repo topics: remove typo 'wotion-detection', add correct topics
# Run from PowerShell on Shadow PC (git credential manager provides the token)
# Usage: .venv\Scripts\Activate.ps1 then .\fix_github_topics.ps1

$owner = "wpferrell"
$repo = "Resonance"

# Get token from git credential store
$cred = git credential fill @("protocol=https", "host=github.com") 2>$null
# If that doesn't work, prompt:
if (-not $env:GITHUB_TOKEN) {
    Write-Host "Enter your GitHub Personal Access Token (needs repo scope):"
    $token = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
    $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
} else {
    $plainToken = $env:GITHUB_TOKEN
}

$headers = @{
    "Accept" = "application/vnd.github.mercy-preview+json"
    "Authorization" = "token $plainToken"
    "Content-Type" = "application/json"
}

$topics = @{
    names = @(
        "affective-computing",
        "ai",
        "conversational-ai",
        "emotion-detection",
        "emotion-recognition",
        "llm",
        "machine-learning",
        "mental-health",
        "nlp",
        "psychology",
        "wellbeing",
        "empathy",
        "dbt",
        "perma",
        "sdt",
        "window-of-tolerance",
        "wise-mind",
        "python"
    )
} | ConvertTo-Json

$url = "https://api.github.com/repos/$owner/$repo/topics"

try {
    $response = Invoke-RestMethod -Uri $url -Method Put -Headers $headers -Body $topics
    Write-Host "SUCCESS. Topics updated:" -ForegroundColor Green
    $response.names | ForEach-Object { Write-Host "  - $_" }
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host "You can also fix this manually on GitHub:"
    Write-Host "  1. Go to https://github.com/wpferrell/Resonance"
    Write-Host "  2. Click the gear icon next to 'About'"
    Write-Host "  3. Remove 'wotion-detection'"
    Write-Host "  4. Add: emotion-detection, psychology, wellbeing, empathy, dbt, perma, sdt, window-of-tolerance, wise-mind"
    Write-Host "  5. Save changes"
}
