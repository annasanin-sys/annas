$path = "C:\Users\AnnaS\OneDrive - Healthworks Fitness\Accounting Team\Anna\RepublicME\January 2026"
Write-Host "Checking path: $path"
$exists = Test-Path -Path $path
Write-Host "Test-Path result: $exists"

if ($exists) {
    Write-Host "Path exists. Attributes:"
    (Get-Item $path).Attributes
} else {
    Write-Host "Path does NOT exist according to Test-Path."
    Write-Host "Trying New-Item -Force..."
    try {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "New-Item -Force succeeded."
    } catch {
        Write-Error "New-Item failed: $_"
    }
}
