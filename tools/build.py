"""Compatibility entry point for the complete Pols Q build."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
for args in [("generate_skin.py",),("build_assets.py",),("preview.py","--png","--thumbnail"),("build.py",)]:
    subprocess.run([sys.executable,str(root/"scripts"/args[0]),*args[1:]],cwd=root,check=True)
