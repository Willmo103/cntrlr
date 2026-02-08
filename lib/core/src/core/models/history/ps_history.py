# Placeholder for Powershell Hostory model
# Actual implementation will go here
# TODO Create a PS module to log to the server for each command executed with the following schema:
# {
#    "working_directory": str,
#    "command": str,
#    "timestamp": datetime,
#    "user": str,
#    "session_id": str
#    "exit_code": int
# }
#
# Example Ppoweshell command to log to the server:
# Invoke-RestMethod -Uri "http://<server_address>/api/ps_history"/log -Method Post -Body (ConvertTo-Json @{
#     working_directory = (Get-Location).Path
#     command = $command
#     timestamp = (Get-Date).ToString("o")
#     user = $env:USERNAME
#     session_id = $env:SESSION_ID
#     exit_code = $LASTEXITCODE
# }
# -ContentType "application/json"
# The server will then store this information in the ps_history table for auditing and analysis.

# SET AN ENV VAR TO ENABLE PS HISTORY LOGGING
# $env:PS_HISTORY_LOGGING_ENABLED = "true"
# SET A VAR TO THE SQLITE_CACHE_DATABASE PATH
# $env:PS_HISTORY_LOGGING_DB_PATH = "~\.ps_history.db"
# Example Profile Script Addition:
# $global:OriginalPrompt = $function:prompt
# function prompt {
#     $command = (Get-History -Count 1).CommandLine
#     $logEntry = @{
#         working_directory = (Get-Location).Path
#         command = $command
#         timestamp = (Get-Date).ToString("o")
#         user = $env:USERNAME
#         session_id = $env:SESSION_ID
#         exit_code = $LASTEXITCODE
#     }
#     # Cache to the database file:
#     $entryJson = $logEntry | ConvertTo-Json
#     $dbPath = $env:PS_HISTORY_LOGGING_DB_PATH
#    if (-not (Test-Path $dbPath)) {
#         # Create the SQLite database and table if it doesn't exist
#         $createTableCmd = "CREATE TABLE IF NOT EXISTS ps_history (id INTEGER PRIMARY KEY AUTOINCREMENT, working_directory TEXT, command TEXT, timestamp TEXT, user TEXT, session_id TEXT, exit_code INTEGER)"
#         sqlite-utils $dbPath "ps_history" --execute "$createTableCmd"
#     }
#     Invoke-RestMethod -Uri "http://<server_address>/api/ps_history/log" -Method Post -Body (ConvertTo-Json $logEntry) -ContentType "application/json"
#     & $global:OriginalPrompt
# }

from asyncio import subprocess
import os, json
from sqlite_utils import Database
from pathlib import Path

DB_PATH = os.getenv("PS_HISTORY_LOGGING_DB_PATH", str(Path.home() / ".ps_history.db"))
POWERSHELL_PROFILE_PATH = subprocess.run(["powershell", "-NoProfile", "-Command", "$profile"], capture_output=True, text=True).stdout.strip()
