import sys

from cx_Freeze import Executable, setup

base = None
#if sys.platform == "win32":
#base = "Win32GUI"

options = {
    "build_exe": {
        "includes": ["tkinter", "os", "xmind2anki", "anki_connect", "ui",
                     "xmind_parser", "main", "typing", "warnings", "shutil", "time"],
        "include_files": ["cvtmode"]
    }
}

executables = [Executable("main.py", base=base)]

setup(
    name="Xmind2Anki PRO",
    version="0.2",
    description="This app implements a simple tool to convert XMind files to Anki cards with Anki Connect",
    options=options,
    executables=executables,
)
