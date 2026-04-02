Option Explicit
On Error Resume Next 

' 1. KILL ZOMBIES
Dim objWMIService, colProcess, objProcess
Set objWMIService = GetObject("winmgmts:{impersonationLevel=impersonate}!\\.\root\cimv2")
Set colProcess = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'excel.exe'")

If colProcess.Count > 0 Then
    For Each objProcess in colProcess
        objProcess.Terminate()
    Next
    WScript.Sleep 3000
End If

Err.Clear

' 2. LAUNCH EXCEL
Dim excel, workbook, filePath
Set excel = CreateObject("Excel.Application")
excel.Visible = True 
excel.DisplayAlerts = False 
excel.AskToUpdateLinks = False

' 3. PICK FILE
filePath = excel.GetOpenFilename("Excel Files (*.xlsm), *.xlsm")

If filePath = "False" Then 
    excel.Quit
    WScript.Quit
End If

' 4. OPEN & WAIT (5 Minutes)
MsgBox "Launching... Do NOT touch Excel."
Set workbook = excel.Workbooks.Open(filePath, 0, False)

' Wait 5 Minutes
WScript.Sleep 300000 

' 5. ROBUST CLOSE (Ignores errors if Excel crashed/closed already)
On Error Resume Next
workbook.Close True
excel.Quit
On Error GoTo 0

MsgBox "Done. Check the file timestamp."
