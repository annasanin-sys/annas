' DEBUG TRIGGER - "LOUD MODE"
Option Explicit
Dim excel, workbook, excelPath

' CONFIGURATION
excelPath = "C:\Users\asanina\Desktop\OneDrive - Healthworks Fitness\Accounting Team\Carol\Unit Membership\UnitMembership2025thru2026.xlsm"

MsgBox "Step 1: Script Started. Launching Excel..."

' 1. Launch Excel
Set excel = CreateObject("Excel.Application")
excel.Visible = True

MsgBox "Step 2: Excel Launched. Opening Workbook..."

' 2. Open Workbook
Set workbook = excel.Workbooks.Open(excelPath)

MsgBox "Step 3: Workbook Opened. About to run Macro 'DailyAutoRefresh'..."

' 3. Run Macro with Error Trapping
On Error Resume Next
excel.Run "DailyAutoRefresh"

If Err.Number <> 0 Then
    MsgBox "CRITICAL ERROR: Could not run the macro!" & vbCrLf & _
           "Error Code: " & Err.Number & vbCrLf & _
           "Description: " & Err.Description & vbCrLf & vbCrLf & _
           "POSSIBLE CAUSES:" & vbCrLf & _
           "1. Macros are disabled in Excel Trust Center." & vbCrLf & _
           "2. The macro name is wrong." & vbCrLf & _
           "3. The code was pasted into a Sheet instead of a Module."
Else
    MsgBox "SUCCESS: Macro command was sent to Excel!" & vbCrLf & _
           "Excel should be frozen/waiting now."
End If

' 4. Cleanup
Set workbook = Nothing
Set excel = Nothing
