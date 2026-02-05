# Global Claude Rules Installation Script (Windows)
# PowerShell script for installing global Claude Code rules system

param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Version
)

# Version information
$ScriptVersion = "1.0.0"

if ($Version) {
    Write-Host "Global Claude Rules Installer v$ScriptVersion" -ForegroundColor Cyan
    exit 0
}

# Script directory
$ScriptDir = Split-Path -Parent $PSScriptRoot
$ScriptDir = Join-Path $ScriptDir ""

# Target directories
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$HooksDir = Join-Path $ClaudeDir "hooks\moai"

# Template variables
$CurrentDate = Get-Date -Format "yyyy-MM-dd"
$Version = "1.4"

function Print-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $Text.PadLeft(60 + $Text.Length / 2) -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

function Print-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Print-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Text)
    Write-Host "ℹ $Text" -ForegroundColor Cyan
}

function Render-Template {
    param(
        [string]$Content,
        [hashtable]$Variables
    )

    $result = $Content
    foreach ($key in $Variables.Keys) {
        $placeholder = "{{${key}}}"
        $result = $result.Replace($placeholder, $Variables[$key])
    }
    return $result
}

function Test-ExistingInstallation {
    $result = @{
        MemoryMd = (Test-Path (Join-Path $ClaudeDir "memory.md"))
        HookFile = (Test-Path (Join-Path $HooksDir "session_start__show_project_info.py"))
        GuideFile = (Test-Path (Join-Path $ClaudeDir "GLOBAL_RULES_GUIDE.md"))
    }
    return $result
}

function Install-MemoryMd {
    $sourceFile = Join-Path $ScriptDir "templates\memory.md"
    $targetFile = Join-Path $ClaudeDir "memory.md"

    if (-not (Test-Path $sourceFile)) {
        Print-Error "Source file not found: $sourceFile"
        return $false
    }

    # Check if exists
    if (Test-Path $targetFile) {
        Print-Warning "Existing file: $targetFile"
        if (-not $Force) {
            $response = Read-Host "  Overwrite $targetFile? [y/N]"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Print-Info "Skipping memory.md"
                return $true
            }
        }
    }

    # Read and render template
    $content = Get-Content $sourceFile -Raw -Encoding UTF8
    $variables = @{
        DATE = $CurrentDate
        VERSION = $Version
        USER_HOME = $env:USERPROFILE
    }
    $rendered = Render-Template -Content $content -Variables $variables

    if ($DryRun) {
        Print-Info "[DRY RUN] Would write: $targetFile"
        Print-Info "[DRY RUN] Size: $($rendered.Length) bytes"
        return $true
    }

    # Create directory if needed
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null

    # Write file with UTF-8 encoding
    [System.IO.File]::WriteAllText($targetFile, $rendered, [System.Text.UTF8Encoding]::new($false))
    Print-Success "Installed: $targetFile"
    return $true
}

function Install-HookFile {
    $sourceFile = Join-Path $ScriptDir "templates\session_start__show_project_info.py"
    $targetFile = Join-Path $HooksDir "session_start__show_project_info.py"

    if (-not (Test-Path $sourceFile)) {
        Print-Error "Source file not found: $sourceFile"
        return $false
    }

    # Create hooks directory
    New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null

    # Check if exists
    if (Test-Path $targetFile) {
        Print-Warning "Existing file: $targetFile"
        if (-not $Force) {
            $response = Read-Host "  Overwrite $targetFile? [y/N]"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Print-Info "Skipping hook file"
                return $true
            }
        }
    }

    if ($DryRun) {
        Print-Info "[DRY RUN] Would copy: $sourceFile -> $targetFile"
        return $true
    }

    # Copy file
    Copy-Item -Path $sourceFile -Destination $targetFile -Force
    Print-Success "Installed: $targetFile"
    return $true
}

function Install-GuideFile {
    $sourceFile = Join-Path $ScriptDir "templates\GLOBAL_RULES_GUIDE.md"
    $targetFile = Join-Path $ClaudeDir "GLOBAL_RULES_GUIDE.md"

    if (-not (Test-Path $sourceFile)) {
        Print-Warning "Source file not found: $sourceFile (optional)"
        return $true
    }

    # Check if exists
    if (Test-Path $targetFile) {
        Print-Warning "Existing file: $targetFile"
        if (-not $Force) {
            $response = Read-Host "  Overwrite $targetFile? [y/N]"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Print-Info "Skipping guide file"
                return $true
            }
        }
    }

    # Read and render template
    $content = Get-Content $sourceFile -Raw -Encoding UTF8
    $variables = @{
        DATE = $CurrentDate
        VERSION = $Version
    }
    $rendered = Render-Template -Content $content -Variables $variables

    if ($DryRun) {
        Print-Info "[DRY RUN] Would write: $targetFile"
        return $true
    }

    # Write file with UTF-8 encoding
    [System.IO.File]::WriteAllText($targetFile, $rendered, [System.Text.UTF8Encoding]::new($false))
    Print-Success "Installed: $targetFile"
    return $true
}

function Print-Summary {
    Print-Header "Installation Summary"

    Write-Host "  Claude Config Dir: $ClaudeDir"
    Write-Host "  Hooks Dir:         $HooksDir"
    Write-Host "  Memory File:       $(Join-Path $ClaudeDir 'memory.md')"
    Write-Host "  Guide File:        $(Join-Path $ClaudeDir 'GLOBAL_RULES_GUIDE.md')"
    Write-Host "  Hook File:         $(Join-Path $HooksDir 'session_start__show_project_info.py')"
    Write-Host ""

    # Verify installation
    $memoryExists = Test-Path (Join-Path $ClaudeDir "memory.md")
    $hookExists = Test-Path (Join-Path $HooksDir "session_start__show_project_info.py")

    if ($memoryExists -and $hookExists) {
        Print-Success "Installation completed successfully!"
        Write-Host ""
        Print-Info "Environment Variables (optional):"
        Write-Host "  setx GLOBAL_CLAUDE_MEMORY $(Join-Path $ClaudeDir 'memory.md')" -ForegroundColor Gray
        Write-Host "  setx GLOBAL_CLAUDE_GUIDE $(Join-Path $ClaudeDir 'GLOBAL_RULES_GUIDE.md')" -ForegroundColor Gray
        Write-Host ""
        Print-Info "To verify installation, start a new Claude Code session."
    } else {
        Print-Error "Installation incomplete!"
        if (-not $memoryExists) {
            Print-Error "  - memory.md not installed"
        }
        if (-not $hookExists) {
            Print-Error "  - Hook file not installed"
        }
    }
}

# Main execution
Print-Header "Global Claude Rules Installation (Windows)"

Print-Info "Script Directory: $ScriptDir"
Print-Info "Target Directory: $ClaudeDir"
Write-Host ""

# Check existing installation
$existing = Test-ExistingInstallation
if ($existing.Values -contains $true) {
    Print-Warning "Existing installation found:"
    if ($existing.MemoryMd) {
        Write-Host "  - $(Join-Path $ClaudeDir 'memory.md')" -ForegroundColor Gray
    }
    if ($existing.HookFile) {
        Write-Host "  - $(Join-Path $HooksDir 'session_start__show_project_info.py')" -ForegroundColor Gray
    }
    if ($existing.GuideFile) {
        Write-Host "  - $(Join-Path $ClaudeDir 'GLOBAL_RULES_GUIDE.md')" -ForegroundColor Gray
    }
    Write-Host ""
}

# Dry run mode
if ($DryRun) {
    Print-Warning "DRY RUN MODE - No files will be modified"
    Write-Host ""
}

# Install files
$success = $true
$success = $success -and (Install-MemoryMd)
$success = $success -and (Install-HookFile)
$success = $success -and (Install-GuideFile)

# Print summary
if (-not $DryRun) {
    Print-Summary
} else {
    Print-Header "Dry Run Summary"
    Print-Info "No files were modified. Run without -DryRun to install."
}

exit (if ($success) { 0 } else { 1 })
