Option Explicit

Dim shell
Dim projectDir
Dim pythonwPath
Dim scriptPath
Dim command

Set shell = CreateObject("WScript.Shell")
projectDir = "E:\smartpet_ascii"
pythonwPath = projectDir & "\.venv\Scripts\pythonw.exe"
scriptPath = projectDir & "\gui_app.py"

shell.CurrentDirectory = projectDir
command = """" & pythonwPath & """ """ & scriptPath & """"
shell.Run command, 0, False
