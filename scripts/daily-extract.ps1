# Daily Claude Conversation Extraction Workflow
# Scheduled via Windows Task Scheduler to run daily
#
# This script:
# 1. Updates existing conversation extracts with new messages
# 2. Renames any new files with date ranges and frontmatter
# 3. Logs results to a daily log file

param(
    [string]$BackupDir = "C:\Users\Josh\Documents\Mine\Claude Code Conversation Backups\Devices\Work Desktop",
    [string]$LogDir = "C:\Users\Josh\Documents\Mine\Claude Code Conversation Backups\Logs",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$LogFile = Join-Path $LogDir "extract-$(Get-Date -Format 'yyyy-MM-dd').log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "=========================================="
Write-Log "Starting daily conversation extraction"
Write-Log "Backup directory: $BackupDir"
Write-Log "=========================================="

# Step 1: Update existing extracts with new messages
Write-Log "Step 1: Updating existing extracts..."
try {
    $updateArgs = @($ScriptDir, "update-extracts.py", $BackupDir)
    if ($DryRun) {
        Write-Log "(DRY RUN - skipping update)"
    } else {
        $updateResult = & uv run "$ScriptDir\update-extracts.py" $BackupDir 2>&1
        $updateResult | ForEach-Object { Write-Log "  $_" }
    }
    Write-Log "Update step completed"
} catch {
    Write-Log "ERROR in update step: $_"
}

# Step 2: Rename any files that still have default naming (new extracts)
Write-Log "Step 2: Checking for files needing rename..."
try {
    # Only rename files that match the original extraction pattern
    $filesToRename = Get-ChildItem -Path $BackupDir -Filter "claude-conversation-*.md" -File

    if ($filesToRename.Count -gt 0) {
        Write-Log "Found $($filesToRename.Count) files with default names, running rename..."
        if ($DryRun) {
            $renameResult = & uv run "$ScriptDir\rename-extracts.py" $BackupDir --dry-run 2>&1
        } else {
            $renameResult = & uv run "$ScriptDir\rename-extracts.py" $BackupDir 2>&1
        }
        $renameResult | ForEach-Object { Write-Log "  $_" }
    } else {
        Write-Log "No files need renaming"
    }
    Write-Log "Rename step completed"
} catch {
    Write-Log "ERROR in rename step: $_"
}

# Step 3: Summary
Write-Log "=========================================="
$totalFiles = (Get-ChildItem -Path $BackupDir -Filter "*.md" -File).Count
Write-Log "Workflow complete. Total conversation files: $totalFiles"
Write-Log "=========================================="

# Optional: Send email notification on errors
# Uncomment below if you want email alerts
<#
$errors = Select-String -Path $LogFile -Pattern "ERROR" -SimpleMatch
if ($errors) {
    $body = Get-Content $LogFile -Raw
    Send-MailMessage -SmtpServer "mail.eusd.org" -Port 25 `
        -From "automation@eusd.org" -To "josh.stephens@gmail.com" `
        -Subject "Claude Extraction - Errors Detected $(Get-Date -Format 'yyyy-MM-dd')" `
        -Body $body
}
#>
