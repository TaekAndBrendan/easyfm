import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {'packages': ['PyQt5', 'gffutils', 'pyfastx']}

# base='Win32GUI' should be used only for Windows GUI app
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name = 'easyfm',
    version = '1.0.1',
    description = 'easyfm(easy file manipulation) is a lightweight suite of software tools for working with Next Generation Sequencing datasets (e.g. fastq, fasta, gff, and gtf) on desktops and laptops.',
    options = {'build_exe': build_exe_options},
    executables = [Executable('easyfm.py', base=base)]
)
