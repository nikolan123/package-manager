import os
import subprocess
from pathlib import Path

cmd = [
    'python',
    '-m', 'PyInstaller',
    'main.py',
    '--name', 'PackageManager',
    '--onefile',
]
subprocess.call(cmd)