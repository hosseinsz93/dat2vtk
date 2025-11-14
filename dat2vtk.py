import numpy as np
import re
import os
import glob

def read_tecplot_file(filename):
    """Read any Tecplot FEBLOCK format file (surface, line, nacelle)"""
    print(f"  Reading: {os.path.basename(filename)}")
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find variables
    var_match = re.search(r'Variables?\s*=\s*([^\r\n]+)', content, re.IGNORECASE)
    if not var_match:
        raise ValueError("No VARIABLES found")
    
    var_names = [v.strip().strip('"') for v in var_match.group(1).split(',')]
    
    # Find zone info
    zone_match = re.search(r'ZONE\s+([^\r\n]+)', content, re.IGNORECASE)
    if not zone_match:
        raise ValueError("No ZONE found")
    
    zone_line = zone_match.group(1)
    
    # Extract N and E
    n_match = re.search(r'(?:NODES|N)\s*=\s*(\d+)', zone_line, re.IGNORECASE)
    e_match = re.search(r'(?:ELEMENTS|E)\s*=\s*(\d+)', zone_line, re.IGNORECASE)
    
    if not n_match or not e_match:
        raise ValueError("Could not find N and E in zone line")
    
    num_nodes = int(n_match.group(1))
    num_elements = int(e_match.group(1))
    
    # Determine zone type (FELINESEG, FETRIANGLE, etc.)
    zonetype_match = re.search(r'ZONETYPE\s*=\s*(\w+)', zone_line, re.IGNORECASE)
    et_match = re.search(r'ET\s*=\s*(\w+)', zone_line, re.IGNORECASE)
    
    if zonetype_match:
        zonetype = zonetype_match.group(1).upper()
    elif et_match:
        zonetype = 'FE' + et_match.group(1).upper()
    else:
        zonetype = 'UNKNOWN'
    
    # Determine nodes per element
    if 'LINESEG' in zonetype:
        nodes_per_element = 2
        vtk_cell_type = 3  # VTK_LINE
    elif 'TRIANGLE' in zonetype:
        nodes_per_element = 3
        vtk_cell_type = 5  # VTK_TRIANGLE
    elif 'QUAD' in zonetype:
        nodes_per_element = 4
        vtk_cell_type = 9  # VTK_QUAD
    else:
        raise ValueError(f"Unsupported zone type: {zonetype}")
    
    # Parse VARLOCATION
    varloc_match = re.search(r'VARLOCATION\s*=\s*\(([^)]+)\)', zone_line, re.IGNORECASE)
    nodal_indices = []
    cell_indices = []
    
    if varloc_match:
        loc_str = varloc_match.group(1)
        # Parse [1-3]=NODAL,[4-12]=CELLCENTERED
        for match in re.finditer(r'\[(\d+)-(\d+)\]\s*=\s*(\w+)', loc_str, re.IGNORECASE):
            start, end, loc_type = int(match.group(1)), int(match.group(2)), match.group(3).upper()
            for i in range(start, end + 1):
                if loc_type == 'NODAL':
                    nodal_indices.append(i - 1)
                else:
                    cell_indices.append(i - 1)
    else:
        # Default: all variables are nodal
        nodal_indices = list(range(len(var_names)))
    
    # Find data start position (after zone header)
    data_start = zone_match.end()
    next_newline = content.find('\n', data_start)
    if next_newline != -1:
        # Skip any optional lines (like STRANDID, SOLUTIONTIME)
        next_line_start = next_newline + 1
        next_line_end = content.find('\n', next_line_start)
        if next_line_end != -1:
            next_line = content[next_line_start:next_line_end].strip()
            if 'STRANDID' in next_line.upper() or 'SOLUTIONTIME' in next_line.upper():
                data_start = next_line_end + 1
            else:
                data_start = next_line_start
        else:
            data_start = next_line_start
    
    data_section = content[data_start:]
    
    # Extract all numbers
    all_numbers = []
    for line in data_section.split('\n'):
        tokens = line.strip().split()
        for token in tokens:
            if re.match(r'^-?[\d.E+e-]+$', token):
                try:
                    all_numbers.append(float(token))
                except:
                    pass
    
    data = np.array(all_numbers)
    
    # Parse data blocks
    nodal_data = {}
    cell_data = {}
    pos = 0
    
    # Nodal variables first
    for idx in nodal_indices:
        var_name = var_names[idx]
        nodal_data[var_name] = data[pos:pos + num_nodes]
        pos += num_nodes
    
    # Cell variables
    for idx in cell_indices:
        var_name = var_names[idx]
        cell_data[var_name] = data[pos:pos + num_elements]
        pos += num_elements
    
    # Connectivity
    expected_conn_size = num_elements * nodes_per_element
    connectivity = data[pos:pos + expected_conn_size].astype(int)
    
    return {
        'num_nodes': num_nodes,
        'num_elements': num_elements,
        'nodal_data': nodal_data,
        'cell_data': cell_data,
        'connectivity': connectivity,
        'vtk_cell_type': vtk_cell_type,
        'nodes_per_element': nodes_per_element
    }

def write_vtk_file(filename, data):
    """Write data to VTK format"""
    num_nodes = data['num_nodes']
    num_elements = data['num_elements']
    nodal = data['nodal_data']
    cell = data['cell_data']
    conn = data['connectivity']
    vtk_cell_type = data['vtk_cell_type']
    nodes_per_element = data['nodes_per_element']
    
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write("Converted from Tecplot\n")
        f.write("ASCII\n")
        f.write("DATASET UNSTRUCTURED_GRID\n")
        
        # Points
        f.write(f"POINTS {num_nodes} float\n")
        x = nodal.get('x', nodal.get('X', np.zeros(num_nodes)))
        y = nodal.get('y', nodal.get('Y', np.zeros(num_nodes)))
        z = nodal.get('z', nodal.get('Z', np.zeros(num_nodes)))
        for i in range(num_nodes):
            f.write(f"{x[i]:.6f} {y[i]:.6f} {z[i]:.6f}\n")
        
        # Cells
        conn_size_per_cell = nodes_per_element + 1
        f.write(f"\nCELLS {num_elements} {num_elements * conn_size_per_cell}\n")
        for i in range(num_elements):
            indices = conn[i*nodes_per_element:(i+1)*nodes_per_element]
            # Convert from 1-based (Tecplot) to 0-based (VTK)
            indices_str = ' '.join(str(idx - 1) for idx in indices)
            f.write(f"{nodes_per_element} {indices_str}\n")
        
        # Cell types
        f.write(f"\nCELL_TYPES {num_elements}\n")
        for _ in range(num_elements):
            f.write(f"{vtk_cell_type}\n")
        
        # Point data (nodal variables except x, y, z)
        nodal_vars = {k: v for k, v in nodal.items() if k.lower() not in ['x', 'y', 'z']}
        if nodal_vars:
            f.write(f"\nPOINT_DATA {num_nodes}\n")
            for var_name, values in nodal_vars.items():
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', var_name)
                f.write(f"SCALARS {safe_name} float 1\n")
                f.write("LOOKUP_TABLE default\n")
                for val in values:
                    f.write(f"{val:.6f}\n")
        
        # Cell data
        if cell:
            f.write(f"\nCELL_DATA {num_elements}\n")
            for var_name, values in cell.items():
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', var_name)
                f.write(f"SCALARS {safe_name} float 1\n")
                f.write("LOOKUP_TABLE default\n")
                for val in values:
                    f.write(f"{val:.6f}\n")

def main():
    """Convert all .dat files to VTK"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create output directory
    output_dir = os.path.join(script_dir, 'vtk_output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .dat files recursively
    dat_files = []
    for root, dirs, files in os.walk(script_dir):
        # Skip the output directory
        if 'vtk_output' in root:
            continue
        for file in files:
            if file.endswith('_nf.dat'):
                dat_files.append(os.path.join(root, file))
    
    if not dat_files:
        print("No .dat files found!")
        return
    
    print(f"Found {len(dat_files)} files to convert\n")
    print("="*60)
    
    success_count = 0
    fail_count = 0
    
    for dat_file in sorted(dat_files):
        basename = os.path.basename(dat_file)
        vtk_filename = basename.replace('_nf.dat', '_nf.vtk')
        vtk_path = os.path.join(output_dir, vtk_filename)
        
        try:
            data = read_tecplot_file(dat_file)
            write_vtk_file(vtk_path, data)
            
            # Determine file type for reporting
            if 'line' in basename.lower():
                file_type = 'line'
            elif 'surface' in basename.lower():
                file_type = 'surface'
            elif 'nacelle' in basename.lower():
                file_type = 'nacelle'
            else:
                file_type = 'other'
            
            nodal_vars = len([k for k in data['nodal_data'].keys() if k.lower() not in ['x', 'y', 'z']])
            cell_vars = len(data['cell_data'])
            
            print(f"✓ {basename:40s} → {vtk_filename:40s}")
            print(f"  Type: {file_type:8s}  Points: {data['num_nodes']:6d}  Cells: {data['num_elements']:6d}  Fields: {nodal_vars}+{cell_vars}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ {basename}: {str(e)}")
            fail_count += 1
    
    print("\n" + "="*60)
    print(f"Conversion complete!")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Output directory: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    main()
