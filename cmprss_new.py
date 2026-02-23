#!/usr/bin/env python3
import csv
import numpy as np
import pandas as pd
from pathlib import Path

# Automation range for at2024 dataset
PROCESS_IDS = range(1, 163)
quant = 100
numChannels = 20

# Directory Setup
script_dir = Path(__file__).resolve().parent
input_dir = script_dir / "output"
output_js_dir = script_dir / "website_data" 
output_js_dir.mkdir(exist_ok=True)

for process in PROCESS_IDS:
    proc_id = str(process)
    input_file = input_dir / f"Simulation_{proc_id}.csv"
    
    if not input_file.exists():
        print(f"Skipping {proc_id}: File not found.")
        continue

    print(f"Compressing Process {proc_id}...")

    with open(input_file) as f:
        reader = csv.reader(f, delimiter=',')
        adata = list(reader)

    # Sensors structure: 20 channels x length of data
    sensors = np.zeros([numChannels, len(adata)-1]) 
    
    # Fill existing columns from CSV into the 20-channel schema
    for i, row in enumerate(adata[1:]):
        for channel_idx in range(len(row)):
            if channel_idx < numChannels:
                try:
                    sensors[channel_idx][i] = float(row[channel_idx])
                except (ValueError, IndexError):
                    sensors[channel_idx][i] = 0

    # Calculate Min/Max for normalization spans
    m = np.zeros([numChannels, 2])
    for c in range(numChannels):
        m[c][0] = np.amin(sensors[c])
        m[c][1] = np.amax(sensors[c])

    # Grouping indices for Torque vs Distance/Angle
    torque_indices = [0, 1, 2, 6, 7, 12, 13, 14, 18]
    dist_indices = [3, 4, 5, 8, 9, 11, 15, 16, 17, 19]

    tmin = np.amin([m[idx][0] for idx in torque_indices])
    tspan = np.amax([m[idx][1] for idx in torque_indices]) - tmin
    
    dmin = np.amin([m[idx][0] for idx in dist_indices])
    dspan = np.amax([m[idx][1] for idx in dist_indices]) - dmin

    # Normalization Loop
    for i in range(sensors.shape[1]):
        for channel in range(numChannels):
            if channel in torque_indices:
                span, minimum = tspan, tmin
            elif channel in dist_indices:
                span, minimum = dspan, dmin
            else:
                span = m[channel][1] - m[channel][0]
                minimum = m[channel][0]

            if span == 0:
                val = 0
            else:
                val = int(quant * ((sensors[channel][i] - minimum) / span - 0.5))

            # Vertical track separation offsets
            if channel < 3: val += 450
            elif channel < 6: val += 400
            elif channel < 10: val += 300
            elif channel < 12: val += 220
            elif channel < 18: val += 100
            
            sensors[channel][i] = val

    # Write the JS file
    js_filename = output_js_dir / f"dta{proc_id}.js"
    with open(js_filename, "w") as f:
        sensor_names = [
            "bendDieLatT","bendDieRotT","bendDieVerT","bendDieLatM","bendDieRotA","bendDieVerM",
            "colletAxT","colletRotT","colletAxMov","colletRotMov",
            "mandrelAxLoad","mandrelAxMov",
            "pressAxT","pressLatT","pressLeftAxT","pressAxMov","pressLatMov","pressLeftAxMov",
            "clampLatT","clampLatMov"
        ]
        for idx, name in enumerate(sensor_names):
            clean_data = [str(int(x)) for x in sensors[idx]]
            f.write(f"var {name}=[{','.join(clean_data)}];\n")
        
        # Dynamic Metadata Footer
        # Index 12=Diameter, 13=Wall, 14=Mandrel, 15=Collet Boost, 16=Clearance
        diam = adata[1][12]
        wall = adata[1][13]
        
        if int(proc_id) < 89:
            attr1 = f"Mandrel: {adata[1][14]}"
            attr2 = f"Collet Boost: {adata[1][15]}"
        else:
            # For 89+, original website highlights Clearance
            attr1 = f"Clearance: {adata[1][16]} mm"
            attr2 = f"Collet Boost: {adata[1][15]}"

        f.write(f"var info='Process ID: {proc_id}<br/>D: {diam}mm | W: {wall}mm<br/>{attr1}<br/>{attr2}';")

print("All processes compressed successfully.")