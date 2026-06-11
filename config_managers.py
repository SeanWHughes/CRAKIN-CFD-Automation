# -*- coding: utf-8 -*-
"""

A large set of classes, methods, and functions used by setup_config.py to 
customize the config.json setup GUI.

All tkinter widgets (tk and ttk) are instantiated with an object name that
follows this structure "{purpose}_{widget type}_wg with "_wg" standing for 
"widget" or also "_wgs" standing for a list of widgets. This reduces how
succinct the program is, but greatly improves readability for future 
customization. Similarly, custom class objects are always instantiated with an 
object name that ends in "_obj".

"""

#%%     IMPORT MODULES

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import json
import configparser

#%%     CONFIG.JSON SETUP CLASS

class ConfigSetupApp:
    """
    This class is used to package all config.json related variables into a
    single app object to simplify GUI-config.json variable handling.
    """
    
    def __init__(self, config_path, arch):
        """
        Constructor method used to initialize new config object instances using
        the config architecture.
        """

        # Initialize entry dictionaries
        self.entries_dict = {}
        self.dynamic_entries = {}
        
        self.arch = arch
        
        self.config_path = config_path
        self.config_json_dict = {}
    
    def load_config(self):
        """
        Method for loading an existing config.json file.
        """
    
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config_json_dict = json.load(f)
            
        # Load previously saved values
        #if config_values:
        #    for val in config_values:
        #        self.append_row_list(config_value=val)
    
        # Ensure all expected sections/fields exist
        for section, fields in self.arch.items():
            for field in fields:
    
                # Normalize dynamic-entry structures
                field_val = self.config_json_dict[section][field]
    
                if isinstance(field_val, list):
    
                    cleaned = []
    
                    for item in field_val:
    
                        # Preserve conditional entries
                        if isinstance(item, dict):
                            cleaned.append(item)
    
                        # Preserve simple filepath entries
                        elif isinstance(item, str):
                            cleaned.append(item)
    
                    self.config_json_dict[section][field] = cleaned
    
    def init_config(self, work_dir):
        """
        Method for creating a config.json file with the specified sections and 
        fields from the config architecture. Field values are initialized as
        empty strings except for the working directory variable.
        """
        
        self.config_json_dict = {}
    
        for section, fields in self.arch.items():
    
            self.config_json_dict[section] = {}
    
            for field in fields:
    
                if field == "WORK_DIR":
                    self.config_json_dict[section][field] = str(work_dir)
                else:
                    self.config_json_dict[section][field] = ""
    
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_json_dict, f, indent=4)
    
    def config_get(self, section, key):
        """
        Method for extracting an existing key-value pair from the config.json 
        file if available, otherwise returns empty string
        """
        
        try:
            return self.config_json_dict[section][key]
        except KeyError:
            return ""
    
    def save_config(self, mainwin):
        """
        Save all entries (normal and dynamic) to config.json with sections.
        Dynamic entries are saved as JSON lists.
        """
        
        self.config_json_dict = {}
    
        # Loop through sections
        for section, fields in self.arch.items():
            self.config_json_dict[section] = {}
        
            for field in fields:
                print(section)
                print(self.entries_dict[section])
                
                # normal entry
                if section in self.entries_dict and field in self.entries_dict[section]:
                    self.config_json_dict[section][field] = self.extract_widget_value(
                        self.entries_dict[section][field]
                    )
                    
                # dynamic entry
                elif section in self.dynamic_entries and field in self.dynamic_entries[section]:
                    dyn_list = self.dynamic_entries[section][field]
        
                    values = []
                    for item in dyn_list.entries_dict:
        
                        if isinstance(item, dict):
                            values.append({
                                "main": self.extract_widget_value(item["main"]),
                                "condition": self.extract_widget_value(item.get("condition", {}))
                            })
                        else:
                            values.append(self.extract_widget_value(item))
        
                    self.config_json_dict[section][field] = values
        
                else:
                    self.config_json_dict[section][field] = ""
    
        # Write JSON to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_json_dict, f, indent=4)
    
        if mainwin:
            messagebox.showinfo(
                "Configuration Saved",
                f"Configuration successfully saved to {self.config_path}"
            )
            mainwin.destroy()
    
    def extract_widget_value(self, v):
        """
        Private method to safely extract the value from a widget, StringVar, or nested dict.
        """
        
        if isinstance(v, tuple):
            return self.extract_widget_value(v[1])
        if isinstance(v, tk.StringVar):
            return v.get()
        if isinstance(v, ttk.Entry):
            return v.get()
        if isinstance(v, dict):
            # Recursively extract values from dict
            return {k: self.extract_widget_value(subv) for k, subv in v.items()}
        if isinstance(v, list):
            return [self.extract_widget_value(item) for item in v]
        elif hasattr(v, "get"):
            # fallback for other Tk widgets
            try:
                return v.get()
            except TypeError:
                return str(v)
        else:        
            return str(v)

#%%     GUI MAIN WINDOW CLASSES

class GUIBootstrap:
    """
    This class is used to create the main window for the GUI and applying styling.
    """
    
    def __init__(self, GUIwidth=1000, GUIheight=800, title="Configure Parameter Optimization Study", global_font="Segoe UI"):
        """
        Constructor method used to initialize the main window of the GUI.
        """
        
        # Create the main window for the GUI
        self.mainwin = tk.Tk()
        self.width = GUIwidth
        self.height = GUIheight
        self.mainwin.geometry(f"{GUIwidth}x{GUIheight}")
        
        self.mainwin.grid_columnconfigure(2, weight=0)
        
        # Add GUI title
        self.mainwin.title(title)
        
        # Automatically apply styling to the GUI
        self.global_font = global_font
        self._apply_styles()
        
        # Make GUI window expandable
        self.mainwin.grid_rowconfigure(0, weight=1)
        self.mainwin.grid_columnconfigure(0, weight=1)
        
        # Make GUI window scrollable
        scrollable = ScrollableFrame(self.mainwin)
        scrollable.grid(row=0, column=0, sticky="nsew")
        
        # Define the scrollable window variable
        self.scrollwin = scrollable.inner_frame_wg

    def _apply_styles(self):
        """
        Private method for applying ttk styling to the GUI. You can customize 
        the styling here by altering the style.configure(...) statements below.
        """
        
        # Define ttk style object
        style = ttk.Style(self.mainwin)
        
        # Attempt to asign global theme as vista for Windows machines, otherwise use clam
        try:
            style.theme_use("vista")
        except tk.TclError:
            style.theme_use("clam")

        # Extract global font
        gfont = self.global_font

        # Create style settings for all GUI labels
        style.configure(
            "Header.TLabel",
            font=(gfont, 10)
        )
        style.configure(
            "ToolTip.TLabel",
            font=(gfont, 10),
            foreground="#1F3B57",
            background="#EAF3FF",
            bordercolor="#A6C8FF",
            relief="solid",
            padding=1
        )
        style.configure(
            "EntryType.TLabel",
            font=(gfont, 10),
            foreground="#4F7CAC"
        )
        
        # Create style for all GUI text entry boxes
        style.configure(
            "TEntry",
            padding=4
        )
        
        # Create style for all GUI buttons
        style.configure(
            "TButton",
            padding=(8, 4)
        )
        style.configure(
            "SmallBrowse.TButton",
            padding=(2, 1)
        )
        style.configure(
            "Save.TButton",
            font=(gfont, 12, "bold"),
            foreground="#3CB371"
        )
    
        self.mainwin.grid_columnconfigure(2, weight=0)

class ScrollableFrame(ttk.Frame):
    """
    This class is used to transform the GUI into a scrollable window.
    """
    
    def __init__(self, window, *args, **kwargs):
        """
        Constructor method used to initialize a scrollable frame widget.
        """
        
        super().__init__(window, *args, **kwargs)

        # Allow scrollable frame to be expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Construct a canvas to use as a viewport, displaying a section of the much larger inner frame
        self.viewport_canvas_wg = tk.Canvas(self, highlightthickness=0)
        self.viewport_canvas_wg.grid(row=0, column=0, sticky="nsew")

        # Construct vertical scrollbar on right of window
        self.scrollbar_wg = ttk.Scrollbar(self, orient="vertical", command=self.viewport_canvas_wg.yview)
        self.scrollbar_wg.grid(row=0, column=1, sticky="ns")
        self.viewport_canvas_wg.configure(yscrollcommand=self.scrollbar_wg.set)

        # Construct the full inner scrollbar frame that contains all widgets
        self.inner_frame_wg = ttk.Frame(self.viewport_canvas_wg)
        self.canvas_window = self.viewport_canvas_wg.create_window((0, 0), window=self.inner_frame_wg, anchor="nw")

        # Make inner scrollbar frame resize properly
        self.inner_frame_wg.bind("<Configure>", self._on_frame_configure)
        self.viewport_canvas_wg.bind("<Configure>", self._on_canvas_configure)

        # Enable mouse wheel scrolling
        self.viewport_canvas_wg.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        """
        Private method for updating the canvas scroll region to match the size 
        of the inner frame.
        """
        
        # Update scrollregion to fit inner frame
        self.viewport_canvas_wg.configure(scrollregion=self.viewport_canvas_wg.bbox("all"))

    def _on_canvas_configure(self, event):
        """
        Private method for resizing the inner frame to match the width of the 
        canvas widget.
        """
        
        # Inner frame is always same width as canvas
        self.viewport_canvas_wg.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """
        Private method for handling mouse wheel scrolling events for the canvas 
        widget.
        """
        
        self.viewport_canvas_wg.yview_scroll(int(-1*(event.delta/120)), "units")

class SaveButton:
    """
    This class is used to create a standardized Save Configuration button
    that performs the config_save method from ConfigSetupApp.
    """

    def __init__(self, window, config_app_obj):
        """
        Constructor method used to initialize a save button widget.
        """

        # Instantiate save button widget without yet placing it
        self.save_btn_wg = ttk.Button(
            window,
            text="Save Configuration",
            style="Save.TButton",
            command=lambda: config_app_obj.save_config(window)
        )
        
    def place_save_btn(self, window_row, window_col) -> int:
        """
        Method for placing the save button within the window.
        """
        
        # Position save button and place within window
        self.save_btn_wg.grid(
            row=window_row,
            column=window_col,
            columnspan=1,
            pady=30
        )
        
        return window_row + 1

#%%     GUI ROW ELEMENT CLASSES

class FPBrowser:
    """
    This class is used to create an OS filepath browser button that autofills
    entry textboxes with the selected filepath.
    """
    
    def __init__(self, fp_entry_wg):
        """
        Constructor method used to initialize new filepath browser instances.
        """
        
        self.fp_entry_wg = fp_entry_wg
    
    def browse_file(self):
        """ 
        Method for opening a FILE selection dialog and inserts the 
        selected filepath into the specified textbox widget.
        """
        
        # Open OS dialog and store filepath as a string
        pathstr = tk.filedialog.askopenfilename()
        
        # Populate the textbox within the GUI only if the user entered a filepath
        if pathstr:
            self.fp_entry_wg.delete(0, tk.END)     # Delete previous text
            self.fp_entry_wg.insert(0, pathstr)    # Replace with new text
            
            # Show the end of long paths
            self.fp_entry_wg.icursor(tk.END)
            self.fp_entry_wg.xview_moveto(1.0)
    
    def browse_folder(self):
        """ 
        Method for opening a FOLDER selection dialog and inserts the 
        selected filepath into the specified textbox widget.
        """
        
        # Open OS dialog and store filepath as a string
        pathstr = tk.filedialog.askdirectory()
        
        # Populate the textbox within the GUI only if the user entered a filepath
        if pathstr:
            self.fp_entry_wg.delete(0, tk.END)     # Delete previous text
            self.fp_entry_wg.insert(0, pathstr)    # Replace with new text
            
            # Show the end of long paths
            self.fp_entry_wg.icursor(tk.END)
            self.fp_entry_wg.xview_moveto(1.0)
       
class ToolTip:
    """
    This class is used to create a small pop-up tooltip that appears when the 
    user hovers over a widget and disappears when the mouse leaves the widget.
    """
    
    def __init__(self, pin_label_wg, text):
        """
        Constructor method used to initialize new tooltip object instances 
        and bind display events to the widget.
        """
        
        # Store relevant tooltip objects
        self.tip_window = None      # The tooltip window object reference
        self.pin_label_wg = pin_label_wg        # The label widget that activates the tooltip
        self.text = text            # The text to be displayed by the tooltip

        # Display tooltip when cursor hovers over label widget, and remove it when not
        pin_label_wg.bind("<Enter>", self.show_tooltip)
        pin_label_wg.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """
        This method displays the tooltip when the cursor hovers over the label widget object.
        """

        # Check that another tooltip window isn't already being displayed (i.e. prevent duplicate windows)
        if self.tip_window:
            return

        # Create a small window for the tooltip
        self.tip_window = tw = tk.Toplevel(self.pin_label_wg)
        
        # Remove standard window decor for tooltip (title, min/max buttons, etc.)
        tw.wm_overrideredirect(True)
        
        # Position tooltip box slightly below and to the right of the label widget
        x = self.pin_label_wg.winfo_rootx() + 20
        y = self.pin_label_wg.winfo_rooty() + 20
        tw.geometry(f"+{x}+{y}")

        # Insert the tooltip text as a window label
        hovertxt_label_wg = ttk.Label(
            tw,
            text=self.text,
            style="ToolTip.TLabel",
            justify="left",
            wraplength=350,
            padding=6
        )
        hovertxt_label_wg.pack()

    def hide_tooltip(self, event=None):
        """
        This method closes the tooltip display when the cursor is not hovered
        over the widget object.
        """
        
        # If the tooltip window is open, remove it and reset the tooltip window object ref
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None     

#%%     GUI ROW MANAGEMENT CLASSES

class EntryRow:
    """
    This class is used to create any row with a user-input entry. Various types
    of user-input entries are allowed via the methods below.
    """
    
    def __init__(self, window, window_row_ind, field_var, row_label_text, show_label=True, help_text="", config_value=None):
        """
        Constructor method used to initialize new entry row object instances.
        """
        
        self.window = window
        self.row_ind = window_row_ind
        self.row_label_text = row_label_text
        self.show_label = show_label
        self.help_text = help_text
        self.config_value = config_value
        self.field_var = field_var
        
        if self.row_ind is None:
            raise ValueError("Row index is None. Check Row initialization.")

    def fp_row(self, is_file=True, btn_style="TButton"):
        """
        Method for defining an entry row for OS filepaths.
        """
        
        # COL 0-1: Construct label (col 0) and tooltip (col 1)
        if self.show_label:
            self.create_row_labels(label_width=30, label_col=0, tooltip_col=1)
        
        # COL 2: Create textbox entry
        fp_entry_wg = ttk.Entry(self.window, width=90)
        fp_entry_wg.grid(
            row=self.row_ind,
            column=2,
            padx=(5, 10),
            pady=4,
            sticky="ew"
        )
        
        # COL 2: Pre-fill entry with previous value from config.json file if it exists
        if self.config_value:
            fp_entry_wg.insert(0, self.config_value)
            
            # Show the end of long paths
            fp_entry_wg.icursor(tk.END)
            fp_entry_wg.xview_moveto(1.0)
        
        # COL 3: Instantiate filepath browser button object
        browser_obj = FPBrowser(fp_entry_wg)
        
        # COL 3: Construct textbox browse button for file or directory search accordingly
        if is_file:
            # Make button browse OS for files using helper func
            browse_btn_wg = ttk.Button(self.window, text="Browse", command=browser_obj.browse_file, style=btn_style)
        else:
            # Make button browse OS for directories using helper func
            browse_btn_wg = ttk.Button(self.window, text="Browse", command=browser_obj.browse_folder, style=btn_style)

        browse_btn_wg.grid(row=self.row_ind, column=3, padx=5, pady=4)
    
        # COL 4:# Create a label to specify whether a file or directory is required
        if self.show_label:
            type_label_wg = ttk.Label(
                self.window,
                text="File" if is_file else "Directory",
                style="EntryType.TLabel"
            )
            type_label_wg.grid(row=self.row_ind, column=4, padx=5)
        
        return fp_entry_wg
    
    def condition_row(self):
        """
        Method for defining an entry row for a boolean condition
        """

        # COL 0-1: Construct label (col 0) and tooltip (col 1)
        if self.show_label:
            self.create_row_labels(label_width=30, label_col=0, tooltip_col=1) 
         
        # COL 2: Create a frame to allow the conditional statement input columns 
        # to fit side-by-side within a single main window column
        cond_frame_wg = ttk.Frame(self.window)
        cond_frame_wg.grid(row=self.row_ind, column=2, padx=20)
        
        # Define options for boolean (relational) operators
        OPS = ["", "<", "<=", ">", ">=", "==", "!="]
        
        # Initialize local column and row for conditional row frame
        cond_row = 0
        cond_col = 0
        
        # COL 2.0: Create entry box for the left-hand side (LHS) value in boolean statement
        LHS_entry_wg = ttk.Entry(cond_frame_wg, width=8)
        LHS_entry_wg.grid(row=cond_row, column=cond_col, padx=2)
        cond_col += 1

        # COL 2.1: Create option menu on LHS for boolean operators
        LHS_op = tk.StringVar()         # Entry variable is recognized as a string
        LHS_op_wg = ttk.Combobox(       # Option box defines allowable strings,
            cond_frame_wg,              # the user must select one to assign
            textvariable=LHS_op,        # as the value for the entry variable
            values=OPS,
            width=3,
            state="readonly"
        )
        LHS_op_wg.grid(row=cond_row, column=cond_col, padx=2)
        LHS_op_wg.configure(justify="center")
        cond_col += 1

        # COL 2.2: Create entry box for the center value in boolean statement
        # (for a simple boolean this is often just the parameter name (e.g. it would be "param" for 3 < param < 5))
        center_entry_wg = ttk.Entry(cond_frame_wg, width=25)
        center_entry_wg.grid(row=cond_row, column=cond_col, padx=5)
        cond_col += 1

        # COL 2.3: Create option menu on right-hand side (RHS) for boolean operators
        RHS_op = tk.StringVar()         # Entry variable is recognized as a string
        RHS_op_wg = ttk.Combobox(       # Option box defines allowable strings, 
            cond_frame_wg,              # the user must select one to assign   
            textvariable=RHS_op,        # as the value for the entry variable
            values=OPS,
            width=3,
            state="readonly"
        )
        RHS_op_wg.grid(row=cond_row, column=cond_col, padx=2)
        RHS_op_wg.configure(justify="center")
        cond_col += 1
        
        # COL 2.4: Create entry box for the RHS value in boolean statement
        RHS_entry_wg = ttk.Entry(cond_frame_wg, width=8)
        RHS_entry_wg.grid(row=cond_row, column=cond_col, padx=2)
    
        def update_condition_status(*args):
            """
            A short helper function that prevents poorly defined boolean
            statements from being entered by the user by disabling entries.
            """
            
            # Group similar boolean relational operators
            eq_rels = ["==", "!="]
            less_rels = ["<", "<="]
            more_rels = [">", ">="]
            
            # Reset all entry statuses before updating (prevents erroneous double disabling)
            LHS_entry_wg.config(state="normal")
            RHS_entry_wg.config(state="normal")
            center_entry_wg.config(state="normal")
            
            # Extract LHS and RHS operator values
            lhs = LHS_op.get()
            rhs = RHS_op.get()
            
            # If LHS is a one-sided operator disable RHS
            if lhs in eq_rels:
                RHS_entry_wg.config(state="disabled")
                center_entry_wg.config(state="normal")
            # If RHS is a one-sided operator disable LHS
            elif rhs in eq_rels:
                LHS_entry_wg.config(state="disabled")
                center_entry_wg.config(state="normal")
            # If RHS and LHS are functionally the same operator
            elif lhs in less_rels and rhs in more_rels:
                LHS_entry_wg.config(state="disabled")
                center_entry_wg.config(state="normal")
            elif lhs in more_rels and rhs in less_rels:
                LHS_entry_wg.config(state="disabled")
                center_entry_wg.config(state="normal")
            # Keep everything normal if otherwise
            else:
                LHS_entry_wg.config(state="normal")
                RHS_entry_wg.config(state="normal")
                center_entry_wg.config(state="normal")
        
        # Update the status of all entries in the row anytime a relational operator is changed
        LHS_op.trace_add("write", update_condition_status)
        RHS_op.trace_add("write", update_condition_status)
        
        # Construct output dict containing all conditional entry widgets
        raw_condition_dict = {                      # Object type...
            "LHS_entry_wg": LHS_entry_wg,           # tk.Entry()
            "LHS_op": LHS_op,                       # tk.StringVar()
            "center_entry_wg": center_entry_wg,     # tk.Entry()
            "RHS_op": RHS_op,                       # tk.StringVar()
            "RHS_entry_wg": RHS_entry_wg            # tk.Entry()
        }    
        
        # Initialize cleaned condition dictionary
        cond_dict = {}
        
        # Loop through all condition value keys
        for key in ("LHS_entry_wg", "center_entry_wg", "RHS_entry_wg"):
            # Extract entry widget
            widget = raw_condition_dict[key]
            
            # If not disabled, then pass entry widget to cleaned dict
            if widget.cget("state") != "disabled":
                cond_dict[key] = widget.get()
                
                if key == "LHS_entry_wg":
                    cond_dict["LHS_op"] = raw_condition_dict["LHS_op"].get()
                if key == "RHS_entry_wg":
                    cond_dict["RHS_op"] = raw_condition_dict["RHS_op"].get()

        return cond_dict
    
    def create_row_labels(self, label_width, label_col, tooltip_col):
        """
        This helper function creates the label and helper tooltip for a row.
        """
        
        # Create short entry row description label
        row_label_wg = ttk.Label(
            self.window,
            text=self.row_label_text,
            style="Header.TLabel",
            anchor="e",
            width=label_width
        )
        row_label_wg.grid(row=self.row_ind, column=label_col, padx=5, pady=5, sticky="e")
        
        # Create help icon label
        help_label_wg = ttk.Label(
            self.window,
            text="ⓘ",
            style="ToolTip.TLabel",
            cursor="hand2"
        )
        help_label_wg.grid(row=self.row_ind, column=tooltip_col, sticky="w")
        
        # Turn help icon into a hoverable, detailed description for what text to enter in textbox
        ToolTip(help_label_wg, self.help_text)

class DynamicRowList:
    """
    This class is used to create a row entry that can be dynamically expanded 
    by the user via buttons to include multiple internal sub-rows.
    """
    
    def __init__(self, window, window_row_ind, field_var, row_label_text, show_label=True, help_text="", btn_text="Add Another", is_file=True, conditional=False, config_values=None):
        """
        Constructor method used to initialize a dynamic row list object.
        """
        
        # Initialize entry list
        self.dynamic_entries_dict = []
        self.main_entry_wg = None
        self.field_var = field_var
        
        # External window variables
        self.window = window
        self.win_row = window_row_ind
        self.win_col = 2
        self.win_colspan = 1
        self.row_label_text = row_label_text
        self.help_text = help_text
        
        # Dynamic Row List Variables
        self.is_file = is_file
        self.conditional = conditional
        self.btn_text = btn_text
        
        # Instantiate first entry row object directly within parent window
        main_row_obj = EntryRow(
            window=self.window,
            window_row_ind=self.win_row,
            field_var=field_var,
            row_label_text=self.row_label_text,
            show_label=show_label,
            help_text=self.help_text,
            config_value=""
        )

        # Construct filepath row
        self.main_entry_wg = main_row_obj.fp_row(is_file=self.is_file)
        
        # Construct internal dynamic row frame for all potential subsequent rows
        self.frame_wg = ttk.Frame(self.window)
        self.frame_wg.grid(
            row=self.win_row + 1, 
            column=self.win_col, 
            columnspan=self.win_colspan, 
            sticky=""
        )
        
        # Initialize internal row counter
        self.frame_row = 0

        # Instantiate dynamic "add row" button within the frame
        self.add_btn_wg = ttk.Button(
            self.frame_wg,
            text=self.btn_text,
            command=self.append_row_list
        )
        self.add_btn_wg.grid(row=self.frame_row + 1, column=2, pady=5, sticky="")
 
    def append_row_list(self, config_value=""):
        """
        Method for adding a new entry row to the dynamic row list.
        """

        # ---------- (1) FILEPATH ROW -----------
        # Create an additional filepath entry row in the internal frame
        
        # I: Instantiate entry row object
        fp_row_obj = EntryRow(
            window=self.frame_wg,
            window_row_ind=self.frame_row,
            field_var=self.field_var,
            row_label_text="",
            show_label=False,
            help_text="",
            config_value=config_value
        )

        # II: Construct filepath row
        fp_entry_wg = fp_row_obj.fp_row(
            is_file=self.is_file,
            btn_style="SmallBrowse.TButton"
        )
        fp_entry_wg.config(width=70)
        
        # III: Increment frame row index
        self.frame_row += 1
        # ---------------------------------------

        # ---------- (2) CONDITION ROW ----------
        # Create an additional condition entry row in the internal frame
        
        # Only place row if specified
        if self.conditional:

            # I: Instantiate entry row object
            cond_row_obj = EntryRow(
                window=self.frame_wg,
                window_row_ind=self.frame_row,
                field_var=self.field_var,
                row_label_text="",
                show_label=False,
                help_text="",
                config_value=""
            )

            # II: Construct condition row and extract cond
            cond_dict = cond_row_obj.condition_row()
            
            # III: Increment frame row index
            self.frame_row += 1
        # ---------------------------------------
            
        # Store all entry widgets within the widget list
        self.dynamic_entries_dict.append({
            "main": fp_entry_wg,
            "condition": cond_dict if self.conditional else None
        })
        
        # Reposition add entry button
        self.add_btn_wg.grid(row=self.frame_row + 1, column=2, pady=5, sticky="")

        return self.dynamic_entries_dict