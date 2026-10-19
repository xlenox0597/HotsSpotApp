"""
Build script to compile HotSpotManager into a standalone Windows executable.
"""

import os
import shutil
import subprocess
import sys


def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    print("[INFO] Starting PyInstaller build...")

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=HotSpotManager",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--collect-all=customtkinter",
        "--add-data=drivers;drivers",
        "main.py"
    ]

    print("[INFO] Command:", " ".join(pyinstaller_cmd))
    res = subprocess.run(pyinstaller_cmd, cwd=base_dir)

    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

    # Copy drivers folder to dist/HotSpotManager/drivers as well to ensure external accessibility
    target_drivers = os.path.join(dist_dir, "HotSpotManager", "drivers")
    source_drivers = os.path.join(base_dir, "drivers")
    
    if os.path.exists(source_drivers):
        if os.path.exists(target_drivers):
            shutil.rmtree(target_drivers)
        shutil.copytree(source_drivers, target_drivers)
        print(f"[OK] Copied drivers into: {target_drivers}")

    print("\n=======================================================")
    print("[SUCCESS] Build complete! Executable located at:")
    print(os.path.join(dist_dir, "HotSpotManager", "HotSpotManager.exe"))
    print("=======================================================\n")


if __name__ == "__main__":
    build()
