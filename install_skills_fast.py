#!/usr/bin/env python3
"""Fast install skills to all target locations."""

import os
import shutil
from pathlib import Path

# Source directories with skills
SOURCE_DIRS = [
    Path(r"C:\Users\Project Zero\Desktop\skills"),
    Path(r"C:\Projects\Quantum C2\skills"),
    Path(r"C:\Projects\Quantum CLI\skills"),
    Path(r"C:\Projects\Fable Apps\OpenFable\.openfable\skills"),
]

# Target directories
GLOBAL_OC_SKILLS = Path(r"C:\Users\Project Zero\.opencode\skills")
GLOBAL_OF_SKILLS = Path(r"C:\Users\Project Zero\.openfable\skills")

PROJECT_DIRS = [
    Path(r"C:\Projects\Fable Apps\OpenFable"),
    Path(r"C:\Projects\Fable Apps\Z-Fable"),
    Path(r"C:\Projects\Quantum C2"),
    Path(r"C:\Projects\Quantum CLI"),
    Path(r"C:\Projects\FB Dropshipper"),
]


def copy_skill(src: Path, dst_dir: Path):
    """Copy a skill directory to destination."""
    dest = dst_dir / src.name
    if not dest.exists():
        shutil.copytree(src, dest)
    else:
        # Merge: copy files that don't exist
        for item in src.iterdir():
            dest_item = dest / item.name
            if item.is_dir():
                copy_skill(item, dest_item)
            else:
                dest_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_item)


def main():
    # Collect all unique skills from all source directories
    all_skills = {}  # name -> Path
    
    for src_dir in SOURCE_DIRS:
        if not src_dir.exists():
            print(f"SKIP: {src_dir} not found")
            continue
        print(f"Scanning: {src_dir}")
        for item in src_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                if item.name not in all_skills:
                    all_skills[item.name] = item
    
    print(f"\nTotal unique skills: {len(all_skills)}")
    for name in sorted(all_skills.keys()):
        print(f"  - {name}")
    
    # Install to global locations
    print("\nInstalling to global locations...")
    
    GLOBAL_OC_SKILLS.mkdir(parents=True, exist_ok=True)
    for name, src in sorted(all_skills.items()):
        copy_skill(src, GLOBAL_OC_SKILLS)
    print(f"Installed {len(all_skills)} skills to {GLOBAL_OC_SKILLS}")
    
    GLOBAL_OF_SKILLS.mkdir(parents=True, exist_ok=True)
    for name, src in sorted(all_skills.items()):
        copy_skill(src, GLOBAL_OF_SKILLS)
    print(f"Installed {len(all_skills)} skills to {GLOBAL_OF_SKILLS}")
    
    # Install to each project
    for proj_dir in PROJECT_DIRS:
        proj_name = proj_dir.name
        print(f"\nProcessing: {proj_name}")
        
        # OpenCode
        oc_skills = proj_dir / ".opencode" / "skills"
        oc_skills.mkdir(parents=True, exist_ok=True)
        for name, src in sorted(all_skills.items()):
            copy_skill(src, oc_skills)
        
        # OpenFable
        of_dir = proj_dir / ".openfable"
        if of_dir.exists():
            of_skills = of_dir / "skills"
            of_skills.mkdir(parents=True, exist_ok=True)
            for name, src in sorted(all_skills.items()):
                copy_skill(src, of_skills)
    
    print("\n=== INSTALLATION COMPLETE ===")
    print(f"Total skills: {len(all_skills)}")
    for name in sorted(all_skills.keys()):
        print(f"  - {name}")


if __name__ == "__main__":
    main()