@echo off
REM Daily Claude Conversation Extraction
REM Run this via Task Scheduler

cd /d "C:\Users\Josh\Projects\claude-conversation-extractor-plugin\scripts"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "daily-extract.ps1"
