@echo off
color 0A
echo ========================================================
echo   Jira -> Monday.com Sync (FIXED DUPLICATES v2.1)
echo   Updated: 2026-01-17
echo ========================================================
echo.
echo [SAFETY PROTOCOLS ACTIVE]
echo  1. ONE-WAY SYNC ONLY (Jira -> Monday)
echo  2. DELETE DISABLED (No items will be removed from Monday)
echo  3. WRITE-BACK DISABLED (Jira will not be modified)
echo.
echo [NEW FEATURES]
echo  - Subtask Lookup (Prevents duplicates)
echo  - Name Preservation (Keeps [KEY] prefix)
echo.
echo Starting Sync Process...
echo.

cd /d "C:\Users\AnnaS\.gemini\antigravity\scratch\jira_monday_sync"
python sync_script.py

echo.
echo ========================================================
echo   Sync Finished.
echo   Please check above for any [RE-SYNC] warnings.
echo ========================================================
pause
