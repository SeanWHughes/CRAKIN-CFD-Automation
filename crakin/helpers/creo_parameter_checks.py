# -*- coding: utf-8 -*-
"""

Parameter Update Status Checker

This helper function takes in either a single parameter name or a list of 
parameter names and determines for each parameter whether it can (or should) 
be updated, via detecting one of four potential causes for being locked:
    1. relation-driven parameter
    2. measurement-driven parameter
    3. user-locked parameter
    4. unknown reason

    Parameters:
    - par_names: a parameter name or a list of parameter names
    - model_name: the Creo CAD file name

"""

#%%     IMPORT MODULES

import re
import creopyson
import xlwings as xw
from xlwings.utils import col_name
from types import MethodType
from typing import List, Optional

#%%     HELPER FUNCTIONS

def infer_creo_type(par_value):
    
    """ Infers Creo parameter type and returns cleaned parameter value """
    
    if isinstance(par_value, bool):
        return par_value, "boolean"
    elif isinstance(par_value, int):
        return par_value, "integer"
    elif isinstance(par_value, float):
        # Convert integer-like floats
        if par_value.is_integer():
            return int(par_value), "integer"
        else:
            return par_value, "real"
    else:
        return str(par_value), "string"
    
#%%     PARAMETER UPSTATUS

def param_status(client, 
                 par_names=None, 
                 model_name=None
                 ) -> dict:
    
    """
    Parameter Update Status Checker

    This helper function takes in either a single parameter name or a list of 
    parameter names and determines for each parameter whether it can (or should) 
    be updated, via detecting one of four potential causes for being locked:
        1. relation-driven parameter
        2. measurement-driven parameter
        3. user-locked parameter
        4. unknown reason

        Parameters:
        - par_names: a parameter name or a list of parameter names
        - model_name: the Creo CAD file name
    """
    
    # Default model name to the active model
    if model_name is None:
        try:
            model_name = client.get_active()["file"]
        except Exception as exc:
            raise RuntimeError(f"There is no currently active Creo|SON client: \n{exc}")
    
    # If no input was given for par_names, then extract parameters from CAD model
    if par_names is None:
        # Extract list of parameter dictionaries (one dict per parameter)
        par_name_dict = client.parameter_list()
        
        # Loop through parameter dictionaries to extract parameter names into a set
        par_names = {param["name"] for param in par_name_dict}
            
    # Normalize the par_names input to a set of strings for searching
    if isinstance(par_names, str):
        par_names = set(par_names)
    elif isinstance(par_names, (list, set)):
        if not all(isinstance(element, str) for element in par_names):
            raise ValueError(f"Parameter name(s) input list or set contains non-strings: \n{par_names}")        
        elif isinstance(par_names, list):
            par_names = set(par_names)
    else:
        raise ValueError(f"Parameter name(s) input must be a string, list of strings, or set of strings: \n{par_names}")
    
    # Initialize output dictionary with all input parameters unlocked at default
    status_dict = {par: {"type": None,
                         "locked": False,
                         "reason": "default"}
                     for par in par_names}

#%%     CHECK 1: DEFAULT PARAMETER

    
#%%     CHECK 2: RELATION-DRIVEN PARAMETER

    # Extract all relations from the Creo model
    relations = client.relations_get(model_name)    

    # Initialize variables
    multistr = ""
    mult_ind = 0
    rel_dict = {}
    
    # Parse through relations for parameter names
    for line in relations:
    
        # Ignore comments (delimeters /* & */) and strip whitespace
        line_clean = re.sub(r"/\*.*?(?:\*/|$)", "", line, re.IGNORECASE).strip()
        
        # Skip empty lines
        if not line_clean:
            continue
        
        # Concatenate multi-line expressions
        if line_clean.endswith("\\"):
            line_clean = re.sub(r"\\$", "", line_clean, re.IGNORECASE)
            multistr += line_clean
            mult_ind += 1
            continue
        elif mult_ind:
            line_clean = multistr + line_clean
            mult_ind = 0
        else:
            multistr = ""

        # Detect left-hand side (LHS) and right-hand side (RHS) of relation assignment:
        rel_match = re.match(r"^(.*?)\s*=\s*(.*)$", line_clean)
        if rel_match:
            lhs = rel_match.group(1)
            rhs = rel_match.group(2)
            
            # Store LHS and RHS into a dictionary
            rel_dict[lhs] = rhs
        else:
            raise RuntimeError(f"There was an error parsing the LHS and RHS of the following relation: {line_clean}")

        # Check if the LHS matches any input parameter name(s) and lock if so 
        if lhs in par_names:
            status_dict[lhs]["locked"] = True
            status_dict[lhs]["reason"] = "relation_driven"
       
#%%     CHECK 3: MEASUREMENT-DRIVEN PARAMETER
    
    for par in status_dict:
        if status_dict[par]["reason"] == "relation_driven":
            rhs = rel_dict[par]
            
            # Check if there is a measurement on RHS of relation
            meas_match = re.match(r"^.*?:FID_(.*)$", rhs, re.IGNORECASE)
            if meas_match:
                meas_feat = meas_match.group(1)
                
                # Check if there are any matching measurement features in tree and change dict reason accordingly
                if client.feature_list(name=meas_feat):
                    status_dict[par]["reason"] = "measurement_driven"
    
#%%     CHECK 4: USER-LOCKED PARAMETER
    
    
    return status_dict

"""

    
    # CHECK 4: PARAMETER TEST CHANGE
    client.parameter_set(
        name=par_names,
        value=par_value,
        file_=model_name,
        type_=creo_type
    )

    update_status = {
        "locked": False,
        "reason": "updated"
    }"""

def validate_excel_creo_params(client, 
                               excel_par_names: List[str], 
                               model_name: Optional[str] = None, 
                               update_excel: bool = False, 
                               excel_sheet_fp: Optional[str] = None
                               ) -> bool:
    
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