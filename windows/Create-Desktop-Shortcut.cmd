@echo off
setlocal
set "BUNDLEDESK_ROOT=%~dp0"
powershell.exe -NoProfile -Command "$root=$env:BUNDLEDESK_ROOT; $ws=New-Object -ComObject WScript.Shell; $lnk=$ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Bundle Desk.lnk')); $lnk.TargetPath=Join-Path $root 'Start-BundleDesk.cmd'; $lnk.WorkingDirectory=$root; $lnk.IconLocation=(Join-Path $root 'BundleDesk.ico'); $lnk.Save()"
if errorlevel 1 (
  echo Could not create the desktop shortcut. Use Start-BundleDesk.cmd directly.
) else (
  echo Desktop shortcut created. Keep the extracted folder in its current location.
)
pause
endlocal
