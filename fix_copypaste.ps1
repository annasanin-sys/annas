# 1. Get previous and current dates
$currentDate = Get-Date
$previousDate = (Get-Date).AddMonths(-1)

Write-Host "Current Date: $($currentDate.ToString('yyyy-MM-dd'))"
Write-Host "Previous Month Target: $($previousDate.ToString('yyyy-MM-dd'))"

# 2. Format folder names and date suffixes
$sourceFolderName = $previousDate.ToString("MMMM yyyy") # e.g., "October 2025"
$destinationFolderName = $currentDate.ToString("MMMM yyyy") # e.g., "November 2025"

# Define date suffixes for source and destination files (MM-yy format)
$previousDateSuffixDash = $previousDate.ToString("MM-yy") # e.g., 10-25
$newDateSuffix = $currentDate.ToString("MM-yy") # e.g., 11-25

# 3. Define base paths 
# Verified path root
$rootPath = "C:\Users\AnnaS\OneDrive - Healthworks Fitness\Accounting Team\Anna"

$basePaths = @{
    "CopleyME"      = Join-Path $rootPath "CopleyME"
    "CambridgeME"   = Join-Path $rootPath "CambridgeME"
    "RepublicME"    = Join-Path $rootPath "RepublicME"
    "Gymit BK ME"   = Join-Path $rootPath "Gymit BK ME"
}

# 4. Define file *patterns* for the source files (All use the pattern [LocationNameNoSpaces]-[MM-yy].xlsx)
$sourceFilePatterns = @{
    "CopleyME"      = "CopleyME-$previousDateSuffixDash.xlsx"
    "CambridgeME"   = "CambridgeME-$previousDateSuffixDash.xlsx"
    "RepublicME"    = "RepublicME-$previousDateSuffixDash.xlsx"
    "Gymit BK ME"   = "GymitBKME-$previousDateSuffixDash.xlsx" 
}

# 5. Process each location
foreach ($location in $basePaths.Keys) {
    $basePath = $basePaths[$location]
    
    # Paths
    $sourceFolderPath = Join-Path -Path $basePath -ChildPath $sourceFolderName
    $destinationFolderPath = Join-Path -Path $basePath -ChildPath $destinationFolderName

    Write-Host "Processing $location..."
    Write-Host "  Source Folder: $sourceFolderPath"
    Write-Host "  Dest Folder:   $destinationFolderPath"

    # Look up the correct source file name (e.g., CopleyME-10-25.xlsx)
    $sourceFileName = $sourceFilePatterns[$location]
    $sourceFilePath = Join-Path -Path $sourceFolderPath -ChildPath $sourceFileName
    
    # Ensure destination folder exists
    # Use -Force to prevent errors if the directory already exists
    if (-not (Test-Path -Path $destinationFolderPath)) {
        Write-Host "  Creating destination folder..."
        New-Item -ItemType Directory -Path $destinationFolderPath -Force | Out-Null
    } else {
         Write-Host "  Destination folder already exists." -ForegroundColor Gray
    }

    # --- Destination file name construction (Current month, hyphenated) ---
    # Convert location name for the destination file name (remove spaces, e.g., "Gymit BK ME" -> "GymitBKME")
    $destinationLocationName = $location -replace '\s','' 
    
    # Construct the new file name (e.g., CopleyME-11-25.xlsx)
    $newFileName = "$destinationLocationName" + "-$newDateSuffix.xlsx"
    $destinationFilePath = Join-Path -Path $destinationFolderPath -ChildPath $newFileName

    # Copy and rename
    if (Test-Path -Path $sourceFilePath) {
        if (-not (Test-Path $destinationFilePath)) {
            Copy-Item -Path $sourceFilePath -Destination $destinationFilePath
            Write-Host "  ✅ Copied '$sourceFileName' -> '$newFileName'" -ForegroundColor Green
        } else {
            Write-Warning "  ⚠️ Destination file already exists: $newFileName"
        }
    } else {
        Write-Error "  ❌ Source file not found: '$sourceFilePath'"
    }
    Write-Host ""
}
