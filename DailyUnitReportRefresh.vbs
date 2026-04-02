Option Explicit
Dim excel, workbook, excelPath, fso, logFile
Dim logPath

' CONFIGURATION
excelPath = "C:\Users\AnnaS\OneDrive\Documents\UnitMembership2025thru20261 1.xlsm"
logPath = "C:\Users\AnnaS\.gemini\antigravity\scratch\refresh_log.txt"

Function LogMessage(msg)
    On Error Resume Next
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set logFile = fso.OpenTextFile(logPath, 8, True)
    logFile.WriteLine Now & " - " & msg
    logFile.Close
    Set fso = Nothing
End Function

LogMessage "SCRIPT STARTED. Cleanup starting..."

On Error Resume Next

' 1. Cleanup
Dim objWMIService, colProcess, objProcess
Set objWMIService = GetObject("winmgmts:{impersonationLevel=impersonate}!\\.\root\cimv2")
Set colProcess = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'excel.exe'")
For Each objProcess in colProcess
    objProcess.Terminate()
Next
Err.Clear
LogMessage "Cleanup finished. Launching Excel..."

' 2. Launch Excel
Set excel = CreateObject("Excel.Application")
excel.Visible = True 
excel.DisplayAlerts = False ' SILENCE ALL POPUPS
excel.AskToUpdateLinks = False ' DO NOT ASK ABOUT LINKS

' 3. Open Workbook
' UpdateLinks=3 (Force Update) or 0 (No Update). Using 0 (False) to ignore the prompt, letting Macro handle refreshes.
On Error Resume Next
Set workbook = excel.Workbooks.Open(excelPath, 0, False) 

If Err.Number <> 0 Then
    LogMessage "ERROR Opening file: " & Err.Description
    WScript.Quit
End If
LogMessage "Workbook Opened. Running Macro 'DailyAutoRefresh'..."

' 4. Run Macro
excel.Run "DailyAutoRefresh"

If Err.Number <> 0 Then
    LogMessage "ERROR Running Macro: " & Err.Description
Else
    LogMessage "Macro triggered successfully. Script ending (Excel handles the rest)."
End If

' 5. Cleanup Objects
Set workbook = Nothing
Set excel = Nothing
