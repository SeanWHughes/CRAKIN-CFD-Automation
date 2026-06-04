# -*- coding: utf-8 -*-
"""

Validate Excel and Creo Parameter Agreement Function

This helper function takes a list of parameter names from an Excel input sheet
and then checks if these parameters are the same as the input Creo model or 
the current active model via the Creo|SON client. The user is given the option
to update the Excel input sheet according to the Creo model's actual parameters
if desired.

    Parameters:
    - client: Creo|SON client
    - excel_par_names: list of parameter name strings from Excel
    - model_name: Creo model name (optional)
    - update_excel: if True, auto-update Excel sheet (optional)
    - excel_sheet_fp: excel input sheet filepath (required if update_excel=True)

"""

#%%     IMPORT MODULES

import creopyson
import xlwings as xw
from xlwings.utils import col_name
from types import MethodType
from typing import List, Optional

#%%     INITIALIZE

def validate_excel_creo_params(client, 
                               excel_par_names: List[str], 
                               model_name: Optional[str] = None, 
                               update_excel: bool = False, 
                               excel_sheet_fp: Optional[str] = None
                               ) -> bool:
    
    # Allow client as object for new function
    creopyson.Client.validate_excel_creo_params = validate_excel_creo_params
    
    # Default model name to the current active model
    if model_name is None:
        try:
            model_name = client.get_active()["file"]
        except Exception as exc:
            print(f"There was an error getting an active Creo|SON Creo model, attempting startup: \n{exc}")
            creoson_startup()
    else:
        if not client.exists(model_name):
            raise RuntimeError("The input Creo model is not open.")
        elif not client.is_active(model_name):
            ""
            
    # Convert list of excel input parameter names into a set
    excel_param_names = {str(name) for name in excel_par_names}
    
    # Extract parameter data from Creo as list of dictionaries
    creo_params_raw = client.feature_list_params(file_=model_name)
    
    # Store parameter names as a set (for lookup), as a list (for order), and as a dictionary (for mapping values)
    creo_param_names = {p["name"] for p in creo_params_raw}
    creo_param_order = [p["name"] for p in creo_params_raw]
    creo_param_values = {p["name"]: p["value"] for p in creo_params_raw}

    #%%     MISMATCH DETECTION

    # Find mismatches between Creo and Excel parameter name dictionaries
    missing_in_creo = excel_param_names - creo_param_names
    missing_in_excel = creo_param_names - excel_param_names
    
    # If there are mismatches
    if missing_in_creo or missing_in_excel:
        # Initialize empty list of mismatches
        mismatches = []

        # Tabulate mismatches for output
        if missing_in_creo:
            mismatches.append(f"Parameters in Excel but NOT in Creo: {sorted(missing_in_creo)}")
        if missing_in_excel:
            mismatches.append(f"Parameters in Creo but NOT in Excel: {sorted(missing_in_excel)}")
        if mismatches:
            print("PARAMETER MISMATCHES FOUND:\n" + "\n".join(mismatches))
    
    # Exit if no updates to Excel are intended OR there are no mismatches detected
    if not update_excel:
        return not mismatches
    # Converse: Continue function execution if updates to Excel are intended AND mismatches are detected
    
    # Ask user whether to synchronize or not
    while True:
        user_input = input("\nDo you want to update the Excel input sheet parameter names to match Creo parameter names? \n(WARNING: parameters that don't exist in Creo will be wiped from Excel input sheet, including all variant values) [y/n]: ")
        user_input = user_input.strip().lower()
        
        if user_input in {"y", "n"}:
            break
        print("Invalid input. Please enter 'y' or 'n'")
    
    # If user decides not to fix mismatches for this particular instance, then exit
    if user_input == "n":
        print("No changes made to Excel sheet.")
        return False
    
    #%%     MISMATCH REMEDIATION ["y"]
    
    # Check that Excel input sheet filepath was input
    if excel_sheet_fp is None:
        raise ValueError("Excel input sheet filepath must be provided to update")
    print("\nUpdating Excel sheet with Creo parameters...")

    # Open Excel parameter input workbook in background
    app = xw.App(visible=True)
    input_wb = app.books.open(excel_sheet_fp)
    input_sheet = input_wb.sheets[0]

    # Detect existing data dimensions in input sheet based on used cells
    filled = input_sheet.used_range
    num_col = filled.last_cell.column
    num_row = filled.last_cell.row
    
    """num_col = input_sheet.range('A1').end('right').column
    num_row = input_sheet.range('A1').end('down').row"""
    
    if not filled:
        raise ValueError("Excel sheet is completely empty")    

    # Define empty dictionary for looking up existing excel parameter values by name
    existing_data = {}
    
    if num_row >= 2:
        # Store existing parameter names as a list to preserve order, even if only one parameter
        ex_names = input_sheet.range(f"A2:A{num_row}").options(ndim=1).value
        
        # Store existing parameter values as a list of lists, even if only one variant
        if num_col >= 2:
            ex_values = input_sheet.range(f"B2:{col_name(num_col)}{num_row}").options(ndim=2).value
        else:
            ex_values = [[] for _ in range(num_row - 1)]    # List of empty lists
        
        # Convert Excel parameter values into a list of lists for each parameter
        for row_ind, name in enumerate(ex_names):
            if name is None:
                continue
            row_values = ex_values[row_ind] if row_ind < len(ex_values) else []
            existing_data[str(name)] = row_values
        
    # Clear Excel sheet entirely from row 2, col 2 onward
    input_sheet.range(f"A2:{col_name(num_col)}{num_row}").clear_contents()
        
    # Write Creo parameters in order, preserving existing variant values where possible
    for row_ind, creo_name in enumerate(creo_param_order):
        # Fill in parameter name in Excel input sheet from Creo
        input_sheet.range(f"A{2 + row_ind}").value = creo_name
        
        # Check dictionary for list of old values if they exist for this parameter, else fill all variants with current Creo value
        final_values = existing_data.get(
            creo_name, 
            [creo_param_values[creo_name]] * (num_col - 1))     # Create list of identical values with length equal to number of variants
        
        # Write each variant value in columns B onwards
        for col_ind, val in enumerate(final_values, start=2):
            input_sheet.range(f"{col_name(col_ind)}{2 + row_ind}").value = val

    # Save and close Excel 
    input_wb.save()
    input_wb.close()
    app.quit()

    print("Excel successfully synchronized with Creo parameters.")

    return True