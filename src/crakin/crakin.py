# -*- coding: utf-8 -*-
"""

CFD DOE Pipeline Main Script

This script will take an Excel file input that specifies combinations of CREO 
parameter par_values and for each combo (design variant) it will change the input 
Creo file's parameters, regenerate and save the variation, optimize mesh 
controls in Excel, then generate the mesh in ANSYS, and finally export the 
mesh.msh file to an output folder named according to the variation. The script 
then repeats this for each design variant until all meshes have been exported.

"""

#%%     IMPORT MODULES

# Standard modules
import creopyson
import pandas as pd
import os
from pathlib import Path
import subprocess
import shutil
import re
import xlwings as xw
from types import MethodType
import sys
import configparser

# DOE CFD Automation Modules
import validate_file_for_OS as val
import creoson_managers as cm
import creo_parameter_checks as cpc

#%%     FILEPATH MANAGEMENT

# Normalize all config.ini filepaths


# (1) Initialize Python config parser and read the config.ini file created by setup_config.py
config = configparser.ConfigParser()
config.read("config.ini")

# (2) Project Directories
WORK_DIR = config["PROJECT"]["WORK_DIR"]
DOE_PROJ_DIR = config["PROJECT"]["DOE_PROJ_DIR"]
OUTPUT_DIR = Path(DOE_PROJ_DIR) / "Generated_Variants"
OF_CASE_DIR_TEMPLATE = config["PROJECT"]["OF_CASE_DIR_TEMPLATE"]

# (3) PTC Creo
CREO_MODEL_FP = config["CREO"]["CREO_MODEL_FP"]
CREO_BATCH_FP = Path(WORK_DIR) / "nitro_proe_remote.bat"
CREOSON_DIR = config["CREO"]["CREOSON_DIR"]
CREOSON_BATCH_FP = Path(CREOSON_DIR) / "creoson_run.bat"

# Check if Creo batch file has been copied to script directory yet
if not Path(CREO_BATCH_FP).exists():
    CREO_EXE_FP = config["CREO"]["CREO_EXE_FP"]
    
    # Get the Creo batch file from the same directory as the executable
    CREO_BIN_DIR = Path(CREO_EXE_FP).resolve().parent
    CREO_OG_BATCH_FP = Path(CREO_BIN_DIR) / "parametric.bat"
    
    if Path(CREO_OG_BATCH_FP).exists():
        shutil.copy2(CREO_OG_BATCH_FP, CREO_BATCH_FP)
    else:
        RuntimeError("Could not find the Creo batch file within the same"\
                     "directory as the parametric.exe file")

# (5) Excel sheets
EXCEL_PAR_INPUT_FP = Path(DOE_PROJ_DIR) / "DOE_parameters_input.xlsx"
EXCEL_MESH_OPT_FP = Path(DOE_PROJ_DIR) / "Mesh_EdgeBias_Optimizer.xlsx"
EXCEL_MESH_VBA_MACRO_FP = Path(DOE_PROJ_DIR) / "SolverMacro.bas"

# (6) ANSYS Workbench
WB_PROJ_FP = config["ANSYS"]["WB_PROJ_FP"]
WB_EXE_FP = config["ANSYS"]["wb_exe_fp"]



# Split file paths into directory and file name
CREO_MODEL_DIR, CREO_MODEL_NAME = os.path.split(CREO_MODEL_FP)

EXCEL_PAR_INPUT_DIR, EXCEL_PAR_INPUT_NAME = os.path.split(EXCEL_PAR_INPUT_FP)
EXCEL_MESH_OPT_DIR, EXCEL_MESH_OPT_NAME = os.path.split(EXCEL_MESH_OPT_FP)

WB_PROJECT_DIR, WB_PROJECT_NAME = os.path.split(WB_PROJ_FP)
WB_EXE_DIR, WB_EXE_NAME = os.path.split(WB_EXE_FP)

# Change working directory
os.chdir(WORK_DIR)

# Check if output directory exists already, otherwise check if valid output directory for OS and create directory if so
if os.path.exists(OUTPUT_DIR):
    pass
elif not val.validate_file_for_OS(OUTPUT_DIR):
    raise ValueError(f"Specified output directory is invalid: {OUTPUT_DIR}")
else:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

#%%     EXCEL PROCESSING

# Read Excel parameter input file to dataframe
param_df = pd.read_excel(EXCEL_PAR_INPUT_FP)

# Define persistent list of parameter names from first column of dataframe
parameter_names = param_df.iloc[1:,0].tolist()

# Open Excel mesh optimization workbook in background
app = xw.App(visible=False)
mesh_book = app.books.open(EXCEL_MESH_OPT_FP)

# Import mesh optimization macro
mac_import = mesh_book.api.VBProject.VBComponents.Import(EXCEL_MESH_VBA_MACRO_FP)

# Parse the VBA code of the macro
mac_code = mac_import.CodeModule
mac_lines = mac_code.Lines(1, mac_code.CountOfLines)

# Search each line for the sub-process definition ("sub") and extract macro name
macro_name = None

for line in mac_lines.splitlines():
    line = line.strip()
    match = re.match(r"Sub\s([^(]+)", line, re.IGNORECASE)
    if match:
        macro_name = match.group(1)
        break
    
if macro_name is None:
    raise ValueError("Could not parse Excel mesh optimization macro name within the VBA code")

print(f"STARTUP 1. Opened Excel Files: \n{EXCEL_PAR_INPUT_NAME} \n{EXCEL_MESH_OPT_NAME}")

#%%     Startup

# Run through Creo|SON startup routine and define client object
client = cm.creoson_startup(CREO_MODEL_FP,
                            CREO_BATCH_FP,
                            CREOSON_BATCH_FP,
                            display_model=True,
                            silent=False)

print("STARTUP 2. Creo CAD file ready for alterations via Creo|SON")

# Check that parameter input sheet matches Creo model parameters
cpc.validate_excel_creo_params(client, parameter_names, True, EXCEL_PAR_INPUT_FP)

#%%     SHUTDOWN TESTING

cm.creoson_shutdown(client,
                    shutdown_creo=True,
                    shutdown_creoson=False,
                    silent=False)

#%%     DESIGN VARIANT LOOP

# Outer Loop: Iterate through each design variant
for col_index, column in enumerate(param_df.columns):
    try: 
        if col_index == 0:
            continue
        
        variant_name = str(column).strip()
        
        # Check if variant name is valid
        if val.validate_file_for_OS(variant_name):
            print(f"\n===== GENERATING VARIANT {col_index + 1}/{len(param_df.columns)}: {variant_name} =====")
        else:
            raise ValueError(f"Invalid variant name {variant_name}")
        
        # Initialize empty parameter dictionary for value, type, & update status
        variant_parameters = {}
    
        #%%     PART 1: CREO PARAMETER UPDATE
    
        # Inner Loop 1: Iterate through each CAD parameter (Excel-->Creo update)
        for row_index, row in param_df.iterrows():
    
            # Find current parameter value & name
            par_name = parameter_names[row_index]
            par_value = row[column]
    
            # Skip empty Excel cells
            if pd.isna(par_value):
                continue
            
            # Check parameter status (parameter type and whether it can be updated)
            status_dict = cpc.param_upstatus(par_name)
            
            # If parameter value is same as last variant, skip it, otherwise update parameter value dictionary accordingly
            if par_value == variant_parameters[par_name]["value"]:
                continue
            else:
                variant_parameters[par_name] = {
                    "value": par_value,
                    "type": creo_type,
                    "update": update_stat,
                }
    
            # Check if mesh-aid feature suppression is necessary
            # ...TBC...
    
            # Check if parameter exists in Creo file if first time running loop
            if col_index == 1 and (client.feature_param_exists(CREO_MODEL_NAME, par_name) != True):
                raise ValueError(f"Missing Creo parameter: {par_name}")
    
            # Update parameter value in Creo model accordingly
            try:
                client.parameter_set(
                    name=par_name,
                    value=par_value,
                    file_=CREO_MODEL_NAME,
                    type_=creo_type
                )
            except Exception as exc:
                raise RuntimeError(f"Failed setting parameter {par_name}: \n{exc}")
        # ---------------------------------------------------------------------
    
        # Regenerate CREO model and save variant for ANSYS import
        try:
            client.file_regenerate(file_=CREO_MODEL_NAME)
            print("CREO Model Regenerated")
            
            client.file_save
            print("CREO model saved")
        except Exception as exc:
            raise RuntimeError(f"FAILED {variant_name}: \n{exc}")
        
        #%%     PART 2: OPENFOAM CASE DIRECTORY PREPARATION
    
        # Create OpenFOAM case directory for variant
        variant_case_dir = os.path.join(
            OUTPUT_DIR,
            variant_name
        )
        
        # Remove existing directory if it exists
        if os.path.exists(variant_case_dir):
            shutil.rmtree(variant_case_dir)
        
        # Copy template case
        shutil.copytree(
            OF_CASE_DIR_TEMPLATE,
            variant_case_dir
        )
        
        # Filepath for parameter summary text file
        par_txt_fp = os.path.join(
            variant_case_dir,
            "parameters.txt"
        )
    
        # Populate parameter summary text file with parameter names & values
        with open(par_txt_fp, "w") as par_txt_file:
            par_txt_file.write(f"Variant Name: {variant_name}\n")
            par_txt_file.write("=" * 50 + "\n\n")

            for par_name, par_value in variant_parameters.items():
                par_txt_file.write(f"{par_name} = {par_value}\n")
        
        print(f"Created OpenFOAM case directory: {variant_case_dir}")
        
        #%%     PART 3: MESH CONTROLS OPTIMIZATION
        
        # In Excel mesh optimization file, find Creo parameter export sheet & clear previous parameters
        input_sheet = mesh_book.sheets["Creo Input"]
        input_sheet.range(f"D2:D{2+len(variant_parameters)}").clear_contents()
    
        # Write each parameter value for the current variant into Creo Input sheet
        for par_ind, par_value in enumerate(variant_parameters.values()):
            input_sheet.range(f"D{3 + par_ind}").value = par_value
    
        # Execute the imported VBA macro (if your macro has args, input them in second set of parentheses)
        mesh_book.macro(macro_name)()
    
        # Find Output sheet
        msh_ctrl_df = pd.read_excel(EXCEL_MESH_OPT_FP, sheet_name="WB Output")
        
        variant_mesh_controls = {}
        
        # Inner Loop 2: Iterate through each output mesh control --------------
        for msh_index, row in msh_ctrl_df.iterrows():
            
            # Find mesh control name and value
            msh_ctrl_name = row[0]
            msh_ctrl_value = row[1]
            
            # Skip empty Excel cells
            if pd.isna(msh_ctrl_value):
                continue
        
            # Update mesh control dictionary
            variant_mesh_controls[msh_ctrl_name] = msh_ctrl_value
        # ---------------------------------------------------------------------
        
        print(f"Mesh optimization completed for '{variant_name}'.")
    
        # Save Excel workbook
        mesh_book.save()
        
        #%%     PART 4: ANSYS UPDATE
    
        # Call ANSYS Workbench
        print("Launching Workbench automation...")
        command = [
            WB_EXE_FP,
            "-B",
            "-R",
            WB_SCRIPT_FP,
            "-F",
            WB_PROJ_FP
        ]
    
        # Pass variant name as environment variable
        env = os.environ.copy()
        env["VARIANT_NAME"] = variant_name
        env["OUTPUT_DIR"] = OUTPUT_DIR
        
        # Export mesh control values into ansys
        
    
        # Run ANSYS automation subprocess and throw error if fail
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ANSYS automation failed:\n{result.stderr}")
        print(f"Completed Workbench processing for {variant_name}")
        
    # Continue to next variant if current variant failed somewhere
    except Exception as exc:
        print(f"FAILED {variant_name}: \n{exc}")
        continue
    
#%%     SHUT-DOWN ROUTINE

# Close Excel mesh optimization workbook
mesh_book.save()
mesh_book.close()
app.quit()

# Close Creo and disconnect from Creo|SON
client.stop_creo()
client.disconnect()

print("\n========== ! ALL VARIANTS COMPLETED ! ==========")
