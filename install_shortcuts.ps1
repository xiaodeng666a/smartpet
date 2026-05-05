$ErrorActionPreference = "Stop"

$projectDir = "E:\smartpet_ascii"
$launchScript = Join-Path $projectDir "launch_pet.vbs"
$exePath = Join-Path $projectDir "dist\AnyaPet\AnyaPet.exe"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$startupPath = [Environment]::GetFolderPath("Startup")
$iconPath = Join-Path $projectDir "assets\app_icon.ico"
$shortcutName = [string]::Concat(
    [char]0x963F,
    [char]0x5C3C,
    [char]0x4E9A,
    [char]0x684C,
    [char]0x5BA0,
    ".lnk"
)
$legacyShortcutName = "AnyaPet.lnk"

function New-Shortcut {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ShortcutPath
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    if (Test-Path $exePath) {
        $shortcut.TargetPath = $exePath
        $shortcut.Arguments = ""
    }
    else {
        $shortcut.TargetPath = "$env:SystemRoot\System32\wscript.exe"
        $shortcut.Arguments = "`"$launchScript`""
    }
    $shortcut.WorkingDirectory = $projectDir
    if (Test-Path $iconPath) {
        $shortcut.IconLocation = "$iconPath,0"
    }
    else {
        $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
    }
    $shortcut.Save()
}

Remove-Item -LiteralPath (Join-Path $desktopPath $legacyShortcutName) -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $startupPath $legacyShortcutName) -ErrorAction SilentlyContinue

New-Shortcut -ShortcutPath (Join-Path $desktopPath $shortcutName)
New-Shortcut -ShortcutPath (Join-Path $startupPath $shortcutName)

Start-Process -FilePath "$env:SystemRoot\System32\ie4uinit.exe" -ArgumentList "-show" -WindowStyle Hidden

Write-Host "Shortcuts created."
