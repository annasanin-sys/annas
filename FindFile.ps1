Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.OpenFileDialog
$f.Title = "Select your data.xlsx file"
$f.Filter = "Excel Files|*.xlsx;*.xlsm"
$f.InitialDirectory = [Environment]::GetFolderPath("Desktop")

if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Host "SELECTED_PATH: $($f.FileName)"
} else {
    Write-Host "CANCELLED"
}
