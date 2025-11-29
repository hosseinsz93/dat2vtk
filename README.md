# dat2vtk

Convert Tecplot FEBLOCK (`*_nf.dat`) files to VTK (ASCII, Unstructured Grid). This script converts VFS-Geophysics Tecplot outputs so they can be visualized in ParaView.

## Requirements
- Python 3.8+
- `numpy` (`pip install numpy`)

## Usage
From the directory containing `dat2vtk.py`:

```powershell
python .\dat2vtk.py
```

### Change the input directory (and other options)

Change the input directory using `--input-dir` (or `-i`). You can also change the output directory (`--output-dir` or `-o`) and filename pattern (`--pattern` or `-p`).

Examples (PowerShell):

```powershell
# Use a specific input directory
python .\dat2vtk.py -i C:\path\to\my\dat_files

# Use a different output directory
python .\dat2vtk.py -i C:\path\to\my\dat_files -o C:\path\to\my\vtk_output

# Match a different pattern (all .dat files)
python .\dat2vtk.py -i C:\path\to\my\dat_files -p "*.dat"
```

The script will:
1. Create (or reuse) `vtk_output/`
2. Convert each `*_nf.dat` file → corresponding `*_nf.vtk`
3. Print a progress table and final summary

## License
No explicit license included; add one if you plan to distribute.
