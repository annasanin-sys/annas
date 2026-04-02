' DEBUG TRIGGER - "LOUD MODE" (VERSION 2)
Option Explicit
Dim excel, workbook, excelPath, macroName

' CONFIGURATION
excelPath = "C:\Users\asanina\Desktop\OneDrive - Healthworks Fitness\Accounting Team\Carol\Unit Membership\UnitMembership2025thru2026.xlsm"

' We use the fully qualified name: 'WorkbookName.xlsm'!MacroName
macroName = "'UnitMembership2025thru2026.xlsm'!DailyAutoRefresh"

MsgBox "Step 1: Script Started. Launching Excel..."

' 1. Launch Excel
Set excel = CreateObject("Excel.Application")
excel.Visible = True

MsgBox "Step 2: Excel Launched. Opening Workbook..."

' 2. Open Workbook
Set workbook = excel.Workbooks.Open(excelPath)

MsgBox "Step 3: Workbook Opened. Attempting to run: " & macroName

' 3. Run Macro with Error Trapping
On Error Resume Next
excel.Run macroName

If Err.Number <> 0 Then
    MsgBox "STILL FAILING (Error " & Err.Number & "): " & Err.Description & vbCrLf & vbCrLf & _
           "CHECK THIS:" & vbCrLf & _
           "1. Open Excel manually." & vbCrLf & _
           "2. Press Alt+F11." & vbCrLf & _
           "3. Look at the code. Does it say 'Private Sub DailyAutoRefresh'?" & vbCrLf & _
           "   (It MUST say just 'Sub' or 'Public Sub')."
Else
    MsgBox "SUCCESS! The fully qualified name worked."
End If

' 4. Cleanup
Set workbook = Nothing
Set excel = Nothing
