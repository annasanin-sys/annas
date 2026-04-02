# --- CONFIGURATION ---
$ExcelPath = "C:\Users\AnnaS\Downloads\data.xlsx"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open($ExcelPath, $null, $true) # ReadOnly

Write-Host "`n--- COLUMN HEADERS ---" -ForegroundColor Cyan

foreach ($sh in $wb.Sheets) {
    if ($sh.Name -in "g", "hw") {
        Write-Host "`nSHEET: [$($sh.Name)]" -ForegroundColor Yellow
        # Get first row values
        $headerRange = $sh.UsedRange.Rows.Item(1)
        $headers = $headerRange.Value2
        
        # Output as a comma-separated list
        if ($headers -is [Array]) {
            # Flatten array just in case
            $flatHeaders = $headers | % { $_ } | Where-Object { $_ -ne $null }
            Write-Host ($flatHeaders -join ", ")
        } else {
             Write-Host "Single Column: $headers"
        }
    }
}

$wb.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
Write-Host "`nDone."
