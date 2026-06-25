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

    def __init__(self, arch):
        """
        Constructor method used to initialize new config object instances.
        """

        # Extract config architecture
        self.arch = arch
        
        # Initialize paths
        self.CONFIG_PATH = Path("config.json").resolve()
        self.TOOL_ROOT = self._find_project_wd()

        # Initialize a dictionary cache to store every built input row object during runtime
        self.inputrow_objs = {}

        # Initialize a dictionary to load entire config.json into at runtime
        self._config_cache = {}

        # Initialize a set to register fields that were modified since last load/save
        self._modified_inputrows = set()

        # Internal variable for setting timestamp format
        self._timefmt = "%m-%d-%Y %H:%M:%S"
        
        # Config load flag for modification tracking
        self._loading_config = False
        
        # If config.json file doesn't exist, run initializiation routine
        if not self.CONFIG_PATH.exists():
            self.init_config()
    
    def _find_project_wd(self):
        """
        Private method for trying to find correct project root directory
        """
        
        # If running outside IDE, try to get this file's filepath from __file__ variable
        try:
            MY_FP = Path(__file__).resolve()
        # If running inside IDE, try to get this file's filepath from Python's current working directory    
        except NameError:
            MY_FP = Path.cwd().resolve() / "setup_config.py"

        # Throw a warning if the current file's filepath wasn't found
        if not Path(MY_FP).exists():
            print("WARNING: Could not determine the script location. Please set TOOL_ROOT variable manually.")

        # Establish project root directory via essential root directory contents
        for parent in [MY_FP] + list(MY_FP.parents):
            if (parent / ".git").exists():
                return parent
            elif (parent / "pyproject.toml").exists():
                return parent
        
        # Raise an error if it couldn't find the project root directory
        raise RuntimeError("Couldn't find CRAKIN root directory")
    
    def mark_mods(self, cfg_key):
        """
        Adds a modified inputrow to the internal set.
        """
        
        # Don't mark as modification if loading values from config.json
        if self._loading_config:
            return

        self._modified_inputrows.add(cfg_key)

    def load_config(self):
        """
        Loads all previous values from the config.json file into the GUI
        widgets so that they persist on save if they weren't modified.
        """
        
        # Flag for loading
        self._loading_config = True
        
        # Check if the config.json file exists
        if not Path(self.CONFIG_PATH).exists():
            return
        
        # Load config.json contents into the internal cache
        with open(self.CONFIG_PATH, "r") as f:
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
                    
                            if ui_var is not None and value is not None:
                                ui_var.set(value)
    
        # Unflag for loading
        self._loading_config = False

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
            
            # Initialize the group and field for this InputRow if it hasn't been already by another InputRow
            cfg_push_values.setdefault(group, {})
            cfg_push_values[group].setdefault(field, {})
    
            # Extract modified status
            if IR_key in self._modified_inputrows:
                last_modified = datetime.now().strftime(self._timefmt)
            else:
                last_modified = ir_obj.cfg_last_modified or self._datetime_stamp()
            
            # Initialize this InputRow's values dictionary
            values = {}
            
            # Convert key-value pairs from widgets and UIvars dicts to list of tuples
            widget_items = list(ir_obj.widgets.items())
            UIvar_items = list(ir_obj.UIvars.items())
            
            # Extract values from UI variables
            for i, (UIvar_name, UIvar) in enumerate(UIvar_items):
                
                # Try getting matching widget by naming convention first
                widget_name = UIvar_name.replace("UIvar", "wg")
                widget = ir_obj.widgets.get(widget_name)
                
                # If this fails, match widget by it's dictionary position
                if widget is None and i < len(widget_items):
                    _, widget = widget_items[i]
                    
                    print(f"WARNING: UIvar, {UIvar_name}, couldn't be associated ",
                          "with it's widget by naming convention. Using dictionary ",
                          "position for matching instead; please fix UIvar and ",
                          "widget naming to match codebase style conventions ",
                          "in the future.")
                
                # Get raw UIvar value
                raw_val = UIvar.get()
            
                # Set value to none if widget is disabled
                if widget.cget("state") == "disabled":
                    values[UIvar_name] = None
                # Set value to none if empty string
                elif isinstance(raw_val, str) and raw_val.strip() == "":
                    values[UIvar_name] = None
                # Otherwise use UIvar value
                else:
                    values[UIvar_name] = raw_val
    
            # Add InputRow data to the push values staging dictionary
            cfg_push_values[group][field][rowid] = {
                "PARENT": parent_rowid,
                "ROW_ID": rowid,
                "ROW_TYPE": spectype,
                "VALUES": values,
                "LAST_MODIFIED": last_modified
            }
    
        # After the staging dictionary has been filled, push changes to the config.json
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg_push_values, f, indent=4)
    
        # Clear the internal registry for modified rows
        self._modified_inputrows.clear()
    
        # Confirm to user that save was successful and then close the GUI
        if container:
            messagebox.showinfo(
                "Configuration Saved",
                f"Configuration successfully saved to {self.CONFIG_PATH}"
            )
    
            container.winfo_toplevel().destroy()

    def init_config(self):
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
    
                # Initialize TOOL_ROOT with a default filepath row
                if field == "TOOL_ROOT":
    
                    self.config_json_dict[section][field][str(row_id)] = {
                        "PARENT": None,
                        "ROW_ID": str(row_id),
                        "ROW_TYPE": "filepath",
                        "VALUES": {
                            "fp_entry_UIvar": str(self.TOOL_ROOT)
                        },
                        "LAST_MODIFIED": self._datetime_stamp()
                    }
    
                    row_id += 1
    
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
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