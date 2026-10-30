#!/usr/bin/env python3
"""
Install all Skills/Plugins/Extensions/MCPs/Custom Commands/Workflows/templates
to OpenCode Desktop, OpenCode, and OpenFable globally and per-project.
"""

import os
import shutil
import json
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DESKTOP_ROOT = Path(r"C:\Users\Project Zero\Desktop")
PROJECTS_ROOT = Path(r"C:\Projects")

GLOBAL_OC_DIR = Path(r"C:\Users\Project Zero\.opencode")
GLOBAL_OC_SKILLS = GLOBAL_OC_DIR / "skills"

GLOBAL_OF_DIR = Path(r"C:\Users\Project Zero\.openfable")
GLOBAL_OF_SKILLS = GLOBAL_OF_DIR / "skills"

PROJECT_DIRS = [
    Path(r"C:\Projects\Fable Apps\OpenFable"),
    Path(r"C:\Projects\Fable Apps\Z-Fable"),
    Path(r"C:\Projects\Quantum C2"),
    Path(r"C:\Projects\Quantum CLI"),
    Path(r"C:\Projects\FB Dropshipper"),
]


def copy_recursive(src: Path, dst: Path):
    """Recursively copy directory contents."""
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dst_item = dst / item.name
        if item.is_dir():
            copy_recursive(item, dst_item)
        else:
            shutil.copy2(item, dst_item)


def copy_skill(src_skill_dir: Path, dest_skills_dir: Path):
    """Copy a single skill directory to destination."""
    skill_name = src_skill_dir.name
    dest_skill_dir = dest_skills_dir / skill_name
    dest_skill_dir.mkdir(parents=True, exist_ok=True)
    copy_recursive(src_skill_dir, dest_skill_dir)
    print(f"  [OK] {skill_name}")


def discover_skills(search_root: Path, label: str) -> dict:
    """Discover all skill directories under search_root."""
    skills = {}
    if not search_root.exists():
        print(f"  [SKIP] Path not found: {search_root}")
        return skills
    
    print(f"Scanning {label}: {search_root}")
    for dir_path in search_root.rglob("*"):
        if dir_path.is_dir():
            skill_file = dir_path / "SKILL.md"
            if skill_file.exists():
                skill_name = dir_path.name
                if skill_name not in skills:
                    skills[skill_name] = dir_path
    
    return skills


def main():
    print("=" * 80)
    print("SKILLS INSTALLATION SCRIPT")
    print("=" * 80)
    
    # Step 1: Discover all skills
    print("\nSTEP 1: Discovering all skills...")
    all_skills = {}
    
    # Desktop skills
    desktop_skills = DESKTOP_ROOT / "skills"
    all_skills.update(discover_skills(desktop_skills, "Desktop/skills"))
    
    # Projects skills directories
    for proj_dir in PROJECTS_ROOT.rglob("skills"):
        if proj_dir.is_dir():
            all_skills.update(discover_skills(proj_dir, f"Projects/{proj_dir.parent.name}/skills"))
    
    print(f"\nTotal unique skills discovered: {len(all_skills)}")
    for name in sorted(all_skills.keys()):
        print(f"  - {name}")
    
    # Step 2: Create global directories
    print("\nSTEP 2: Creating global directories...")
    GLOBAL_OC_SKILLS.mkdir(parents=True, exist_ok=True)
    print(f"  Created: {GLOBAL_OC_SKILLS}")
    
    GLOBAL_OF_SKILLS.mkdir(parents=True, exist_ok=True)
    print(f"  Created: {GLOBAL_OF_SKILLS}")
    
    # Step 3: Install to global locations
    print("\nSTEP 3: Installing skills to global locations...")
    
    for skill_name, skill_dir in sorted(all_skills.items()):
        copy_skill(skill_dir, GLOBAL_OC_SKILLS)
    print(f"  Installed {len(all_skills)} skills to OpenCode global: {GLOBAL_OC_SKILLS}")
    
    for skill_name, skill_dir in sorted(all_skills.items()):
        copy_skill(skill_dir, GLOBAL_OF_SKILLS)
    print(f"  Installed {len(all_skills)} skills to OpenFable global: {GLOBAL_OF_SKILLS}")
    
    # Step 4: Install to each project
    print("\nSTEP 4: Installing skills to each project...")
    
    for proj_dir in PROJECT_DIRS:
        proj_name = proj_dir.name
        print(f"\nProcessing project: {proj_name}")
        
        # OpenCode directory
        proj_oc_dir = proj_dir / ".opencode"
        if not proj_oc_dir.exists():
            proj_oc_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {proj_oc_dir}")
        
        proj_oc_skills = proj_oc_dir / "skills"
        proj_oc_skills.mkdir(parents=True, exist_ok=True)
        
        for skill_name, skill_dir in sorted(all_skills.items()):
            copy_skill(skill_dir, proj_oc_skills)
        
        # OpenFable directory
        proj_of_dir = proj_dir / ".openfable"
        if proj_of_dir.exists():
            proj_of_skills = proj_of_dir / "skills"
            proj_of_skills.mkdir(parents=True, exist_ok=True)
            
            for skill_name, skill_dir in sorted(all_skills.items()):
                copy_skill(skill_dir, proj_of_skills)
    
    # Step 5: Ensure .opencode directories exist
    print("\nSTEP 5: Ensuring .opencode directories exist...")
    
    for proj_dir in PROJECT_DIRS:
        proj_name = proj_dir.name
        proj_oc_dir = proj_dir / ".opencode"
        if not proj_oc_dir.exists():
            proj_oc_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created .opencode in {proj_name}")
        
        proj_oc_skills = proj_oc_dir / "skills"
        if not proj_oc_skills.exists():
            proj_oc_skills.mkdir(parents=True, exist_ok=True)
            print(f"  Created skills dir in {proj_name}/.opencode")
        
        if len(all_skills) > 0:
            for skill_name, skill_dir in sorted(all_skills.items()):
                copy_skill(skill_dir, proj_oc_skills)
    
    # Step 6: Ensure .openfable directories exist
    print("\nSTEP 6: Ensuring .openfable directories exist...")
    
    for proj_dir in PROJECT_DIRS:
        proj_name = proj_dir.name
        proj_of_dir = proj_dir / ".openfable"
        if not proj_of_dir.exists():
            proj_of_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created .openfable in {proj_name}")
        
        proj_of_skills = proj_of_dir / "skills"
        if not proj_of_skills.exists():
            proj_of_skills.mkdir(parents=True, exist_ok=True)
        
        if len(all_skills) > 0:
            for skill_name, skill_dir in sorted(all_skills.items()):
                copy_skill(skill_dir, proj_of_skills)
    
    # Step 7: Ensure global .opencode config exists
    print("\nSTEP 7: Ensuring OpenCode config exists...")
    global_oc_config = GLOBAL_OC_DIR / "config.json"
    if not global_oc_config.exists():
        config = {
            "secrets": {},
            "skills": [],
            "mcp": {},
            "providers": []
        }
        with open(global_oc_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  Created: {global_oc_config}")
    else:
        print(f"  Exists: {global_oc_config}")
    
    # Step 8: Ensure global OpenFable config exists
    print("\nSTEP 8: Ensuring OpenFable config exists...")
    global_of_config = GLOBAL_OF_DIR / "openfable.jsonc"
    if not global_of_config.exists():
        config = {
            "$schema": "https://opencode.ai/config.json",
            "provider": {},
            "permission": {},
            "mcp": {}
        }
        with open(global_of_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  Created: {global_of_config}")
    else:
        print(f"  Exists: {global_of_config}")
    
    # Step 9: Summary
    print("\n" + "=" * 80)
    print("INSTALLATION COMPLETE")
    print("=" * 80)
    print(f"\nTotal skills discovered: {len(all_skills)}")
    print()
    print("Skills installed to:")
    print(f"  - Global OpenCode:  {GLOBAL_OC_SKILLS}")
    print(f"  - Global OpenFable: {GLOBAL_OF_SKILLS}")
    print()
    for proj_dir in PROJECT_DIRS:
        proj_name = proj_dir.name
        print(f"  - {proj_name}/.opencode/skills")
        print(f"  - {proj_name}/.openfable/skills")
    print()
    print("Skills installed:")
    for name in sorted(all_skills.keys()):
        print(f"  - {name}")
    print()
    print("To use skills in OpenCode, type: /skills")
    print("To use skills in OpenFable, use the skills panel in the UI")
    print("=" * 80)


if __name__ == "__main__":
    main()