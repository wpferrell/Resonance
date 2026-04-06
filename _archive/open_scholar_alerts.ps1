# Opens the Scholar Alerts setup page in Chrome
# Run once from PowerShell — then click each of the 12 alert buttons on the page

$alertsPage = "C:\Users\Shadow\Documents\Resonance_Scholar_Alerts.html"

if (Test-Path $alertsPage) {
    Start-Process $alertsPage
    Write-Host "Scholar Alerts page opened in browser."
    Write-Host "Click each of the 12 buttons to set up Google Scholar alerts."
    Write-Host "This takes about 2 minutes total."
} else {
    Write-Host "ERROR: Scholar Alerts page not found at $alertsPage"
    Write-Host "The file may have been moved. Check the Resonance root folder."
}
