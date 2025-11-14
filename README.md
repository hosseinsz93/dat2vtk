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

The script will:
1. Create (or reuse) `vtk_output/`
2. Convert each `*_nf.dat` file → corresponding `*_nf.vtk`
3. Print a progress table and final summary

## License
No explicit license included; add one if you plan to distribute.
