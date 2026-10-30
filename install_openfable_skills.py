#!/usr/bin/env python3
"""Install skills to OpenFable .openfable/skills dirs for missing projects."""
import shutil
from pathlib import Path

SRC = Path(r"C:\Users\Project Zero\.openfable\skills")
TARGETS = [
    Path(r"C:\Projects\Fable Apps\Z-Fable\.openfable\skills"),
    Path(r"C:\Projects\Quantum C2\.openfable\skills"),
    Path(r"C:\Projects\FB Dropshipper\.openfable\skills"),
]

def copy_skill(src, dst_dir):
    dest = dst_dir / src.name
    if not dest.exists():
        shutil.copytree(src, dest)
    else:
        for item in src.iterdir():
            dest_item = dest / item.name
            if item.is_dir():
                copy_skill(item, dest_item)
            else:
                dest_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_item)

def main():
    skills = [d for d in SRC.iterdir() if d.is_dir()]
    print(f"Source skills: {len(skills)}")
    for t in TARGETS:
        t.mkdir(parents=True, exist_ok=True)
        for s in skills:
            copy_skill(s, t)
        print(f"Installed {len(skills)} skills to {t}")

if __name__ == "__main__":
    main()