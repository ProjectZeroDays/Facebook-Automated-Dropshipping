# ============================================================================
# FBM Ops - Skills Installation Script
# Installs all Skills/Plugins/Extensions/MCPs/Custom Commands/Workflows/templates
# into OpenCode Desktop, OpenCode, and OpenFable globally and per-project
# ============================================================================

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURATION
# ============================================================================
$desktopRoot = "C:\Users\Project Zero\Desktop"
$projectsRoot = "C:\Projects"

$globalOpenCodeDir = "C:\Users\Project Zero\.opencode"
$globalOpenCodeSkills = "$globalOpenCodeDir\skills"

$globalOpenFableDir = "C:\Users\Project Zero\.openfable"
$globalOpenFableSkills = "$globalOpenFableDir\skills"

# Target project directories
$projectDirs = @(
    "C:\Projects\Fable Apps\OpenFable",
    "C:\Projects\Fable Apps\Z-Fable",
    "C:\Projects\Quantum C2",
    "C:\Projects\Quantum CLI",
    "C:\Projects\FB Dropshipper"
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$msg)
    Write-Host ""
    Write-Host "="*80
    Write-Host "  $msg"
    Write-Host "="*80
}

function Copy-Recurse {
    param([string]$Source, [string]$Dest)
    if (-not (Test-Path $Source)) { return }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force | Out-Null }
    Get-ChildItem -Path $Source -Recurse | ForEach-Object {
        $relPath = $_.FullName.Substring($Source.Length).TrimStart('\')
        $destPath = Join-Path $Dest $relPath
        if ($_.PSIsContainer) {
            if (-not (Test-Path $destPath)) { New-Item -ItemType Directory -Path $destPath | Out-Null }
        } else {
            Copy-Item -Path $_.FullName -Destination $destPath -Force
        }
    }
}

function Copy-Skill {
    param([string]$SourceSkillDir, [string]$DestSkillsDir)
    $skillName = Split-Path $SourceSkillDir -Leaf
    $destSkillDir = Join-Path $DestSkillsDir $skillName
    if (-not (Test-Path $destSkillDir)) { New-Item -ItemType Directory -Path $destSkillDir -Force | Out-Null }
    Copy-Recurse -Source $SourceSkillDir -Dest $destSkillDir
    Write-Host "  [OK] $skillName"
}

# ============================================================================
# STEP 1: COLLECT ALL SKILLS FROM ALL SOURCES
# ============================================================================

Write-Header "STEP 1: Discovering all skills across C:\Projects\ and Desktop"

$allSkills = @{}  # HashTable: skillName -> sourceDir

function Discover-Skills {
    param([string]$searchRoot, [string]$label)
    Write-Host "Scanning $label: $searchRoot"
    if (-not (Test-Path $searchRoot)) {
        Write-Host "  [SKIP] Path not found: $searchRoot"
        return
    }
    
    # Look for directories containing SKILL.md or .md files that look like skills
    Get-ChildItem -Path $searchRoot -Recurse -Directory | ForEach-Object {
        $dir = $_.FullName
        $skillFile = Join-Path $dir "SKILL.md"
        if (Test-Path $skillFile) {
            $skillName = Split-Path $dir -Leaf
            if (-not $allSkills.ContainsKey($skillName)) {
                $allSkills[$skillName] = $dir
            }
        }
    }
}

# Search Desktop skills
Discover-Skills -searchRoot "C:\Users\Project Zero\Desktop\skills" -label "Desktop/skills"
# Search Projects for skills directories
Get-ChildItem -Path "C:\Projects" -Recurse -Directory -Filter "skills" | ForEach-Object {
    Discover-Skills -searchRoot $_.FullName -label "Projects/skills"
}

Write-Host "Found $($allSkills.Count) unique skills"

# ============================================================================
# STEP 2: CREATE GLOBAL DIRECTORIES
# ============================================================================

Write-Header "STEP 2: Creating global directories"

if (-not (Test-Path $globalOpenCodeSkills)) {
    New-Item -ItemType Directory -Path $globalOpenCodeSkills -Force | Out-Null
    Write-Host "Created: $globalOpenCodeSkills"
} else {
    Write-Host "Exists: $globalOpenCodeSkills"
}

if (-not (Test-Path $globalOpenFableSkills)) {
    New-Item -ItemType Directory -Path $globalOpenFableSkills -Force | Out-Null
    Write-Host "Created: $globalOpenFableSkills"
} else {
    Write-Host "Exists: $globalOpenFableSkills"
}

# ============================================================================
# STEP 3: INSTALL SKILLS TO GLOBAL LOCATIONS
# ============================================================================

Write-Header "STEP 3: Installing skills to global locations"

foreach ($skillName in $allSkills.Keys) {
    Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $globalOpenCodeSkills
}
Write-Host "Installed $($allSkills.Count) skills to OpenCode global: $globalOpenCodeSkills"

foreach ($skillName in $allSkills.Keys) {
    Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $globalOpenFableSkills
}
Write-Host "Installed $($allSkills.Count) skills to OpenFable global: $globalOpenFableSkills"

# ============================================================================
# STEP 4: INSTALL TO EACH PROJECT
# ============================================================================

Write-Header "STEP 4: Installing skills to each project"

foreach ($projDir in $projectDirs) {
    $projName = Split-Path $projDir -Leaf
    Write-Host "Processing project: $projName"
    
    # Check for .opencode directory
    $projOcDir = Join-Path $projDir ".opencode"
    if (-not (Test-Path $projOcDir)) {
        New-Item -ItemType Directory -Path $projOcDir -Force | Out-Null
        Write-Host "  Created: $projOcDir"
    }
    
    $projOcSkills = Join-Path $projOcDir "skills"
    if (-not (Test-Path $projOcSkills)) {
        New-Item -ItemType Directory -Path $projOcSkills -Force | Out-Null
    }
    
    # Copy all skills
    foreach ($skillName in $allSkills.Keys) {
        Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $projOcSkills
    }
    
    # Check for .openfable directory
    $projOfDir = Join-Path $projDir ".openfable"
    if (Test-Path $projOfDir) {
        $projOfSkills = Join-Path $projOfDir "skills"
        if (-not (Test-Path $projOfSkills)) {
            New-Item -ItemType Directory -Path $projOfSkills -Force | Out-Null
        }
        foreach ($skillName in $allSkills.Keys) {
            Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $projOfSkills
        }
    }
}

# ============================================================================
# STEP 5: CREATE .opencode DIRECTORIES WHERE MISSING
# ============================================================================

Write-Header "STEP 5: Ensuring .opencode directories exist in all projects"

foreach ($projDir in $projectDirs) {
    $projName = Split-Path $projDir -Leaf
    $projOcDir = Join-Path $projDir ".opencode"
    if (-not (Test-Path $projOcDir)) {
        New-Item -ItemType Directory -Path $projOcDir -Force | Out-Null
        Write-Host "Created .opencode in $projName"
    }
    
    $projOcSkills = Join-Path $projOcDir "skills"
    if (-not (Test-Path $projOcSkills)) {
        New-Item -ItemType Directory -Path $projOcSkills -Force | Out-Null
        Write-Host "Created skills dir in $projName/.opencode"
    }
    
    # Copy skills if any exist
    if ($allSkills.Count -gt 0) {
        foreach ($skillName in $allSkills.Keys) {
            Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $projOcSkills
        }
    }
}

# ============================================================================
# STEP 6: CREATE .openfable DIRECTORIES WHERE MISSING
# ============================================================================

Write-Header "STEP 6: Ensuring .openfable directories exist in all projects"

foreach ($projDir in $projectDirs) {
    $projName = Split-Path $projDir -Leaf
    $projOfDir = Join-Path $projDir ".openfable"
    if (-not (Test-Path $projOfDir)) {
        New-Item -ItemType Directory -Path $projOfDir -Force | Out-Null
        Write-Host "Created .openfable in $projName"
    }
    
    $projOfSkills = Join-Path $projOfDir "skills"
    if (-not (Test-Path $projOfSkills)) {
        New-Item -ItemType Directory -Path $projOfSkills -Force | Out-Null
    }
    
    if ($allSkills.Count -gt 0) {
        foreach ($skillName in $allSkills.Keys) {
            Copy-Skill -SourceSkillDir $allSkills[$skillName] -DestSkillsDir $projOfSkills
        }
    }
}

# ============================================================================
# STEP 7: CREATE GLOBAL OPENCODE CONFIG IF MISSING
# ============================================================================

Write-Header "STEP 7: Ensuring OpenCode config exists"

$globalOcConfig = Join-Path $globalOpenCodeDir "config.json"
if (-not (Test-Path $globalOcConfig)) {
    $config = @{
        "secrets" = @{}
        "skills" = @()
        "mcp" = @{}
        "providers" = @()
    } | ConvertTo-Json -Depth 10
    $config | Out-File -FilePath $globalOcConfig -Encoding UTF8
    Write-Host "Created: $globalOcConfig"
} else {
    Write-Host "Exists: $globalOcConfig"
}

# ============================================================================
# STEP 8: CREATE GLOBAL OPENFABLE CONFIG IF MISSING
# ============================================================================

Write-Header "STEP 8: Ensuring OpenFable config exists"

$globalOfConfig = Join-Path $globalOpenFableDir "openfable.jsonc"
if (-not (Test-Path $globalOfConfig)) {
    $config = @{
        "$schema" = "https://opencode.ai/config.json"
        "provider" = @{}
        "permission" = @{}
        "mcp" = @{}
    } | ConvertTo-Json -Depth 10
    $config | Out-File -FilePath $globalOfConfig -Encoding UTF8
    Write-Host "Created: $globalOfConfig"
} else {
    Write-Host "Exists: $globalOfConfig"
}

# ============================================================================
# STEP 9: SUMMARY
# ============================================================================

Write-Header "STEP 9: INSTALLATION COMPLETE"

Write-Host ""
Write-Host "============================================================================"
Write-Host "  INSTALLATION SUMMARY"
Write-Host "============================================================================"
Write-Host "Total skills discovered: $($allSkills.Count)"
Write-Host ""
Write-Host "Skills installed to:"
Write-Host "  - Global OpenCode:  $globalOpenCodeSkills"
Write-Host "  - Global OpenFable: $globalOpenFableSkills"
Write-Host ""
foreach ($projDir in $projectDirs) {
    $projName = Split-Path $projDir -Leaf
    Write-Host "  - $projName/.opencode/skills"
    Write-Host "  - $projName/.openfable/skills"
}
Write-Host ""
Write-Host "Skills available:"
$allSkills.Keys | Sort-Object | ForEach-Object { Write-Host "  - $_" }
Write-Host ""
Write-Host "To use skills in OpenCode, type: /skills"
Write-Host "To use skills in OpenFable, use the skills panel in the UI"
Write-Host "============================================================================"
