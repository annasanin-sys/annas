# Configurable Variables
$excelFilePath = "C:\Users\asanina\Desktop\OneDrive - Healthworks Fitness\Accounting Team\Carol\Unit Membership\UnitMembership2025thru2026.xlsx"
$visible = $true # Set to $false to run in background
$delaySeconds = 60 # Seconds to wait for refresh to finish

# Check if file exists
if (-not (Test-Path $excelFilePath)) {
    Write-Error "File not found at path: $excelFilePath"
    exit
}

# Clean Start: Kill zombie processes that might be locking the Mashup Container
try { 
    Stop-Process -Name "excel" -Force -ErrorAction SilentlyContinue 
    Stop-Process -Name "Microsoft.Mashup.Container.Loader" -Force -ErrorAction SilentlyContinue
} catch {}

# --- NATIVE LAUNCH METHOD (No COM) ---
# Starting Excel via COM seems to corrupt the Power Query environment for this specific file.
# We will launch Excel as a standard process, just like double-clicking the file.

Write-Host "Launching Excel as a standard process..."
$excelProcess = Start-Process "excel.exe" -ArgumentList "`"$excelFilePath`"" -PassThru

# Wait for Excel to open and load the file
# We'll wait a bit longer to be safe
Write-Host "Waiting for Excel to launch..."
Start-Sleep -Seconds 15

# UI Automation via WScript.Shell
$wshell = New-Object -ComObject WScript.Shell

# 1. Activate Window
Write-Host "Activating Excel Window..."
$wshell.AppActivate("Excel")
Start-Sleep -Seconds 2

# 2. Refresh All (Ctrl + Alt + F5)
Write-Host "Sending Refresh Command (Ctrl+Alt+F5)..."
$wshell.SendKeys("^%{F5}")
$wshell.SendKeys("^%{F5}") # Send twice to be sure

# 3. Wait for Refresh
$waitMinutes = 2
Write-Host "Waiting $waitMinutes minutes for refresh..."
Start-Sleep -Seconds ($waitMinutes * 60)

# 4. Save (Ctrl + S)
Write-Host "Saving (Ctrl+S)..."
$wshell.AppActivate("Excel") # Ensure focus again
Start-Sleep -Seconds 1
$wshell.SendKeys("^s")
Start-Sleep -Seconds 5 # Wait for save

# 5. Close (Alt + F4)
Write-Host "Closing (Alt+F4)..."
$wshell.SendKeys("%{F4}")
Start-Sleep -Seconds 2

Write-Host "Done!"
