import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# ===============================================================================
# Function to prepare the Simulation data and combine them in a single Data Frame
# ===============================================================================

def process_simulations(base_dir, output_path, sim_start, sim_end, print_option, time_option, plot_sim_num=None):
    """
    Automated version: Correctly handles SIM_V12-XX zero-padding. 
    """
    # Ensure paths are handled as strings for os.path join
    base_dir = str(base_dir)
    output_path = str(output_path)

    # Note: Dataset requires Parameter_Simulation_01.csv in the base dir [cite: 818]
    param_file_path = os.path.join(base_dir, 'Parameter_Simulation_01.csv')
    
    if not os.path.exists(param_file_path):
        print(f"CRITICAL ERROR: {param_file_path} not found.")
        return []

    param_df = pd.read_csv(param_file_path, delimiter=';', index_col='No.')
    
    parameter_names = [
        "BendDieBendingAngle", "BendDieLateralMovement", "ColletAxialForce",
        "ColletAxialMovement", "MandrelAxialForce", "MandrelAxialMovement",
        "PressureDieAxialForce", "PressureDieAxialMovement", "PressureDieLateralForce",
        "WiperDieAxialForce", "WiperDieLateralForce", "WiperDieLateralMovement"
    ]

    simulations_data = []

    for sim_num in range(sim_start, sim_end + 1):
        # Match zero-padding found on disk: SIM_V12-01 
        folder_name = f"SIM_V12-{str(sim_num).zfill(2)}"
        sim_path = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(sim_path):
            print(f"Skipping {folder_name}: Folder not found at {sim_path}")
            continue

        file_names = [
            f"{folder_name}_bend-die_bending-angle_rad.csv",
            f"{folder_name}_bend-die_lateral-movement.csv",
            f"{folder_name}_collet_axial-force.csv",
            f"{folder_name}_collet_axial-movement.csv",
            f"{folder_name}_mandrel_axial-force.csv",
            f"{folder_name}_mandrel_axial-movement.csv",
            f"{folder_name}_pressure-die_axial-force.csv",
            f"{folder_name}_pressure-die_axial-movement.csv",
            f"{folder_name}_pressure-die_lateral-force.csv",
            f"{folder_name}_wiper-die_axial-force.csv",
            f"{folder_name}_wiper-die_lateral-force.csv",
            f"{folder_name}_wiper-die_lateral-movement.csv"
        ]
        
        temp_data = pd.DataFrame()
        valid_sim = True

        for i, file_name in enumerate(file_names):
            file_path = os.path.join(sim_path, file_name)
            if not os.path.exists(file_path):
                print(f"  Warning: Missing component file {file_name}")
                valid_sim = False
                break
                
            temp_df = pd.read_csv(file_path, delimiter=';', header=None, names=['Time', parameter_names[i]], skiprows=1)
            
            if parameter_names[i] == "BendDieBendingAngle":
                temp_df[parameter_names[i]] = np.rad2deg(temp_df[parameter_names[i]])
            
            if i == 0:
                temp_data['Time'] = temp_df['Time']
            temp_data[parameter_names[i]] = temp_df[parameter_names[i]]

        if not valid_sim:
            continue

        # Add metadata parameters (Diameter, Wall thickness, etc.) [cite: 121, 129]
        for param in param_df.columns:
            temp_data[param] = param_df.loc[sim_num, param]
        
        if time_option == 'deltime':
            temp_data.drop('Time', axis=1, inplace=True)

        simulations_data.append(temp_data)

        if print_option == 'print':
            output_file_path = os.path.join(output_path, f'Simulation_{sim_num}.csv')
            temp_data.to_csv(output_file_path, index=False)
            print(f"  Successfully saved: Simulation_{sim_num}.csv")

    return simulations_data

# ... [Keep plot_data and load_and_plot_geometry as per original script] ...

def load_and_plot_geometry(base_dir, sim_start, sim_end, plot=False, plot_sims=[]):
    geometry_before_dataframes = []
    geometry_after_dataframes = []
    base_dir = str(base_dir)

    for sim_num in range(sim_start, sim_end + 1):
        folder_name = f"SIM_V12-{str(sim_num).zfill(2)}"
        sim_path = os.path.join(base_dir, folder_name)

        file_path_before = os.path.join(sim_path, f"{folder_name}_geometry_before_springback.csv")
        file_path_after = os.path.join(sim_path, f"{folder_name}_geometry_after_springback.csv")

        if not os.path.exists(file_path_before) or not os.path.exists(file_path_after):
            continue

        df_before = pd.read_csv(file_path_before, delimiter=';')
        df_after = pd.read_csv(file_path_after, delimiter=';')

        geometry_before_dataframes.append(df_before)
        geometry_after_dataframes.append(df_after)

    return (geometry_before_dataframes, geometry_after_dataframes)

# =============================================
# Function to Generate Windows (Headless Version)
# =============================================
def generate_windows_from_dfs(machine_dataframes, geometry_before_dfs, geometry_after_dfs, output_directory=None, save_csv=False, method='middle_small'):
    stats_before_springback = []
    stats_after_springback = []

    for index, (machine_df, geo_before_df, geo_after_df) in enumerate(zip(machine_dataframes, geometry_before_dfs, geometry_after_dfs)):
        stats_before = process_geometry(machine_df, geo_before_df, method)
        stats_after = process_geometry(machine_df, geo_after_df, method)

        df_before = pd.DataFrame(stats_before) if stats_before else pd.DataFrame()
        df_after = pd.DataFrame(stats_after) if stats_after else pd.DataFrame()

        if not df_before.empty:
            stats_before_springback.append(df_before)
            if save_csv and output_directory:
                df_before.to_csv(os.path.join(str(output_directory), f'sim_{index+1}_before_springback_stats.csv'), index=False)

        if not df_after.empty:
            stats_after_springback.append(df_after)
            if save_csv and output_directory:
                df_after.to_csv(os.path.join(str(output_directory), f'sim_{index+1}_after_springback_stats.csv'), index=False)

    return (stats_before_springback, stats_after_springback)

def process_geometry(machine_df, geometry_df, method):
    stats = []
    # [cite: 218-219] Mapping methods to window sizes
    methods = {'middle_small': 0.5, 'middle_large': 2, 'middle_extra_large': 3, 'before': 1, 'after': 1}
    window_size = methods.get(method, 0.5)

    for angle in geometry_df['Angle[degree]']:
        lower_bound, upper_bound = calculate_bounds(angle, window_size, method, machine_df)
        mask = (machine_df['BendDieBendingAngle'] >= lower_bound) & (machine_df['BendDieBendingAngle'] <= upper_bound)
        window_df = machine_df[mask]

        if not window_df.empty:
            summary_stats = {
                'Angle[degree]': angle,
                **{f'{col}_min': window_df[col].min() for col in window_df if col != 'BendDieBendingAngle'},
                **{f'{col}_max': window_df[col].max() for col in window_df if col != 'BendDieBendingAngle'},
                **{f'{col}_avg': window_df[col].mean() for col in window_df if col != 'BendDieBendingAngle'}
            }
            stats.append(summary_stats)
    return stats

# ... [Keep calculate_bounds, merge_machine_with_geometry, concatenate_data_frames as is] ...