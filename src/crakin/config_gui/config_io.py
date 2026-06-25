# -*- coding: utf-8 -*-
"""

Config.json Input/Output Application

Contains all of the functions necessary to extract values from the config.json
file and saving values to it.

"""

from datetime import datetime
from pathlib import Path
import json
from tkinter import messagebox

class ConfigSetupApp:
    """
    This class is used to package all config.json related variables into a
    single app object to simplify GUI-config.json variable handling.
    """

    def __init__(self, config_path, arch):
        """
        Constructor method used to initialize new config object instances.
        """

        # Extract inputs
        self.config_path = config_path
        self.arch = arch

        # Initialize a dictionary cache to store every built input row object during runtime
        self.inputrow_objs = {}

        # Initialize a dictionary to load entire config.json into at runtime
        self._config_cache = {}

        # Initialize a set to register fields that were modified since last load/save
        self._modified_inputrows = set()

        # Internal variable for setting timestamp format
        self._timefmt = "%m-%d-%Y %H:%M:%S"
        
    def mark_mods(self, cfg_key):
        """
        Adds a modified inputrow to the internal set.
        """
        
        self._modified_inputrows.add(cfg_key)

    def load_config(self):

        # Check if the config.json file exists
        if not Path(self.config_path).exists():
            return
        
        # Load config.json contents into the internal cache
        with open(self.config_path, "r") as f:
            self._config_cache = json.load(f)
        
        # Loop through every unique row ID within the config cache
        for group, fields in self._config_cache.items():
            for field, rows in fields.items():
                for rowid, rowdata in rows.items():
    
                    # Extract values and last modified timestamp from cache
                    values = rowdata.get("VALUES", {})
                    last_modified = rowdata.get("LAST_MODIFIED", "")
    
                    # Check for the config cache row within the inputrow object dictionary
                    IR_key = (group, field, rowid)
    
                    # Check if inputrow exists in build dictionary
                    if IR_key in self.inputrow_objs:
                        ir_obj = self.inputrow_objs[IR_key]
                        
                        # Update last_modified
                        ir_obj.cfg_last_modified = last_modified
                        
                        # Update UIvars values
                        for key, value in values.items():
                            ui_var = ir_obj.UIvars.get(key)
                    
                            if ui_var is not None:
                                ui_var.set(value)
    
        # Clear the internal registry for modified rows 
        self._modified_inputrows.clear()

    def save_config(self, container):
    
        # Initialize a dictionary for staging new values to push to config.json
        cfg_push_values = {}

        # Loop through every inputrow that was built and added to the config app
        for ir_obj in self.inputrow_objs.values():
    
            # Extract context
            group = ir_obj.ctx.cfg_group
            field = ir_obj.ctx.cfg_field
            rowid = ir_obj.ctx.cfg_rowid
            parent_rowid = ir_obj.ctx.cfg_parent_rowid
            IR_key = ir_obj.ctx.cfg_key
            
            # Extract spec type
            spectype = ir_obj.spec.cfg_spectype
            
            # Initialize the current InputRow's groups and fields as empty dicts
            cfg_push_values.setdefault(group, {})
            cfg_push_values[group].setdefault(field, {})
    
            # Extract modified status
            if IR_key in self._modified_inputrows:
                last_modified = datetime.now().strftime(self._timefmt)
            else:
                last_modified = ir_obj.cfg_last_modified
            
            # Initialize a UIvars values dictionary
            values = {}
            
            # Extract values from UI variables
            for UIvar, value in ir_obj.UIvars.items():
                values[UIvar] = value.get()
    
            # Add InputRow data to the push values staging dictionary
            cfg_push_values[group][field][rowid] = {
                "PARENT": parent_rowid,
                "ROW_ID": rowid,
                "ROW_TYPE": spectype,
                "VALUES": values,
                "LAST_MODIFIED": last_modified
            }
    
        # After the staging dictionary has been filled, push changes to the config.json
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(cfg_push_values, f, indent=4)
    
        # Clear the internal registry for modified rows
        self._modified_inputrows.clear()
    
        # Confirm to user that save was successful and then close the GUI
        if container:
            messagebox.showinfo(
                "Configuration Saved",
                f"Configuration successfully saved to {self.config_path}"
            )
    
            container.winfo_toplevel().destroy()

    def init_config(self, work_dir):
        """
        Method for creating a config.json file with the specified sections and
        fields from the config architecture. Field values are initialized as
        empty strings except for the working directory variable.
        """
    
        self.config_json_dict = {}
    
        row_id = 1
    
        for section, fields in self.arch.items():
    
            self.config_json_dict[section] = {}
    
            for field in fields:
    
                # Create empty row container for this field
                self.config_json_dict[section][field] = {}
    
                # Initialize WORK_DIR with a default filepath row
                if field == "WORK_DIR":
    
                    self.config_json_dict[section][field][str(row_id)] = {
                        "PARENT": None,
                        "ROW_ID": str(row_id),
                        "ROW_TYPE": "filepath",
                        "VALUES": {
                            "fp_entry_UIvar": str(work_dir)
                        },
                        "LAST_MODIFIED": self._datetime_stamp()
                    }
    
                    row_id += 1
    
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_json_dict, f, indent=4)

    def config_get(self, cfg_key):
        """
        Extract the config data for a particular row.
        """
        
        cfg_group_data = self._config_cache.get(cfg_key[0], {})
        cfg_field_data = cfg_group_data.get(cfg_key[1], {})
        cfg_row_data = cfg_field_data.get(cfg_key[2], {})
    
        return cfg_row_data

    def _datetime_stamp(self):
        return datetime.now().strftime("%m-%d-%Y %H:%M:%S")