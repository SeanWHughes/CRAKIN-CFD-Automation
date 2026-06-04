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

#%%     INITIALIZATION

def param_upstatus(client, 
                   par_names=None, 
                   model_name=None) -> dict:
    
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
            raise ValueError(f"ERROR: Parameter name(s) input list or set contains non-strings: \n{par_names}")        
        elif isinstance(par_names, list):
            par_names = set(par_names)
    else:
        raise ValueError(f"ERROR: Parameter name(s) input must be a string, list of strings, or set of strings: \n{par_names}")
    
    # Initialize output dictionary with all input parameters unlocked at default
    upstatus_dict = {par: {"locked": False,
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
            upstatus_dict[lhs]["locked"] = True
            upstatus_dict[lhs]["reason"] = "relation_driven"
       
#%%     CHECK 3: MEASUREMENT-DRIVEN PARAMETER
    
    for par in upstatus_dict:
        if upstatus_dict[par]["reason"] == "relation_driven":
            rhs = rel_dict[par]
            
            # Check if there is a measurement on RHS of relation
            meas_match = re.match(r"^.*?:FID_(.*)$", rhs, re.IGNORECASE)
            if meas_match:
                meas_feat = meas_match.group(1)
                
                # Check if there are any matching measurement features in tree and change dict reason accordingly
                if client.feature_list(name=meas_feat):
                    upstatus_dict[par]["reason"] = "measurement_driven"
    
#%%     CHECK 4: USER-LOCKED PARAMETER
    
    
    return upstatus_dict

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
