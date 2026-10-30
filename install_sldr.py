#!/usr/bin/env python3
"""
Install SLDR Autonomous Software Factory skill to all target directories.
"""

import shutil
from pathlib import Path

SOURCE = Path(r"C:\Users\Project Zero\.opencode\skills\sldr-autonomous-factory")

TARGETS = [
    Path(r"C:\Users\Project Zero\.openfable\skills\sldr-autonomous-factory"),
    Path(r"C:\Projects\Fable Apps\OpenFable\.opencode\skills\sldr-autonomous-factory"),
    Path(r"C:\Projects\Fable Apps\Z-Fable\.opencode\skills\sldr-autonomous-factory"),
    Path(r"C:\Projects\Quantum C2\.opencode\skills\sldr-autonomous-factory"),
    Path(r"C:\Projects\Quantum CLI\.opencode\skills\sldr-autonomous-factory"),
    Path(r"C:\Projects\FB Dropshipper\.opencode\skills\sldr-autonomous-factory"),
]


def copy_skill(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  [OK] {dst}")


def main():
    print("Installing SLDR Autonomous Software Factory skill...")
    print(f"Source: {SOURCE}")
    print()
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_skill(SOURCE, target)
    print()
    print("SLDR skill installed to all target directories.")
    print()
    print("Usage in any project:")
    print("  cd <project>")
    print("  python .opencode/skills/sldr-autonomous-factory/auto_command.py init")
    print("  python .opencode/skills/sldr-autonomous-factory/auto_command.py <requirements>")


if __name__ == "__main__":
    main()