import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# 'packages': ['os'] is used as example only
# build_exe_options = {'packages': ['PyQt5', 'Biopython', 'gffutils', 'pyfastx'], 'include_files': ['images', 'settings.ini', 'arialbd.ttf']}},}
build_exe_options = {'packages': ['PyQt5', 'gffutils', 'pyfastx']}

# base='Win32GUI' should be used only for Windows GUI app
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name = 'easyfm',
    version = '0.1',
    description = 'This is easyfm version 0.7',
    options = {'build_exe': build_exe_options},
    executables = [Executable('easyfm.py', base=base)]
)
