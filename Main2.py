import os
from pathlib import Path
from Data_Preparation import process_simulations

# Use absolute path to be safe [cite: 840-844]
script_dir = Path(r"D:\Aakash Deshmukh\Projekt\New folder\at2024")
base_directory = script_dir / 'Simulation Data'
output_directory = script_dir / 'output'
output_directory.mkdir(parents=True, exist_ok=True)
print(output_directory.exists)
# Dataset specifics [cite: 122-123, 852-854]
sim_start = 1
sim_end = 162

# Use 'print' to ensure CSVs are actually saved to the output folder [cite: 863-864]
print_option = 'print' 
time_option = 'deltime'
plot_sim_num = None

print(f"Targeting path: {base_directory}")

# Call the function
# NOTE: If process_simulations is internally flawed, we will need to fix it next.
simulation_dataframes = process_simulations(
    base_directory, 
    output_directory, 
    sim_start, 
    sim_end, 
    print_option, 
    time_option, 
    plot_sim_num
)

print(f"Reconstruction complete. Check: {output_directory}")