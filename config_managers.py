# -*- coding: utf-8 -*-
"""

A large set of classes, methods, and functions used by setup_config.py to 
customize the config.ini setup GUI.

"""

#%%     IMPORT MODULES

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import configparser

#%%     CONFIG.INI SETUP CLASS

class ConfigSetupApp:
    """
    This class is used to package all config.ini related variables into a
    single app object to simplify GUI-config.ini variable handling.
    """
    
    def __init__(self, config_path, arch):
        """
        Constructor method used to initialize new config object instances using
        the config architecture.
        """

        self.entries = {}
        self.arch = arch
        
        self.config = configparser.ConfigParser()
        self.config_path = config_path

    def init_config(self, work_dir):
        """
        Method for creating a config.ini file with the specified sections and 
        fields from the config architecture. Field values are initialized as
        empty strings except for the working directory variable.
        """
    
        for section, fields in self.arch.items():
            self.config[section] = {
                field: str(work_dir) if field == "WORK_DIR" else ""
                for field in fields
            }
        
        if not any("WORK_DIR" in fields for fields in self.arch.values()):
            raise ValueError('ERROR: Config architecture is missing required "WORK_DIR" entry.')
            
        with open(self.config_path, "w") as f:
            self.config.write(f)
    
    def config_get(self, section, key):
        """
        Method for extracting an existing key-value pair from the config.ini 
        file if available, otherwise returns empty string
        """
        
        try:
            return self.config[section][key]
        except KeyError:
            return ""
    
    def save_config(self, mainwin):
        """
        Method for saving the user-input filepaths from the GUI into the 
        config.ini file that is eventually parsed by the main script pipeline.
        """

        for section, fields in self.arch.items():
            self.config[section] = {}
    
            for field_var in fields:
                widget = self.entries[field_var]
                self.config[section][field_var] = widget.get().strip()
    
        missing = []
    
        # Check for missing fields within the config object
        for section in self.config:
            for key, value in self.config[section].items():
                if not value.strip():
                    missing.append(f"{section}:{key}")
                    
        # Create an error popup if the user tries to save without filling all fields
        if missing:
            tk.messagebox.showerror("Missing Fields",
                                    "Please fill in all fields:\n\n" + 
                                    "\n".join(missing))
            return
    
        # Write config object contents to a config.ini file
        with open(self.config_path, "w") as f:
            self.config.write(f)
    
        # Save confirmation message
        tk.messagebox.showinfo("Success", f"Configuration saved to:\n{self.config_path.resolve()}")
        
        # Close GUI after user clicks OK
        mainwin.destroy()

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
        self.apply_styles()
        
        # Make GUI window expandable
        self.mainwin.grid_rowconfigure(0, weight=1)
        self.mainwin.grid_columnconfigure(0, weight=1)
        
        # Make GUI window scrollable
        scrollable = ScrollableFrame(self.mainwin)
        scrollable.grid(row=0, column=0, sticky="nsew")
        
        # Define the scrollable window variable
        self.scrollwin = scrollable.inner

    def apply_styles(self):
        """
        Method for applying ttk styling to the GUI. You can customize the
        styling by altering the style.configure(...) statements below.
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
            "Save.TButton",
            font=(gfont, 12, "bold"),
            foreground="#3CB371"
        )
    
        self.mainwin.grid_columnconfigure(2, weight=0)

class ScrollableFrame(ttk.Frame):
    """
    This class is used to transform the GUI into a scrollable window.
    """
    
    def __init__(self, parent, *args, **kwargs):
        """
        Constructor method used to initialize a scrollable frame widget.
        """
        
        super().__init__(parent, *args, **kwargs)

        # Allow scrollable frame to be expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Construct a canvas to hold inner frame
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # --- vertical scrollbar on right ---
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # --- inner frame for widgets ---
        self.inner = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # --- make inner frame resize properly ---
        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # --- mouse wheel scrolling ---
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        """
        Method for updating the canvas scroll region to match the size of the inner frame.
        """
        
        # Update scrollregion to fit inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """
        Method for resizing the inner frame to match the width of the canvas widget.
        """
        
        # Inner frame is always same width as canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """
        Method for handling mouse wheel scrolling events for the canvas widget.
        """
        
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class SaveButton:
    """
    This class is used to create a standardized Save Configuration button
    that performs the config_save method from ConfigSetupApp.
    """

    def __init__(self, window, config_app):
        """
        Constructor method used to initialize a save button widget.
        """

        # Instantiate save button object without yet placing it
        self.button = ttk.Button(
            window,
            text="Save Configuration",
            style="Save.TButton",
            command=lambda: config_app.save_config(window)
        )
        
    def place_save_btn(self, window_row, window_col) -> int:
        """
        Method for placing the save button within the window.
        """
        
        # Position save button and place within window
        self.button.grid(
            row=window_row,
            column=window_col,
            columnspan=1,
            pady=30
        )
        
        return window_row + 1

#%%     GUI ROW ELEMENT CLASSES

class Browser:
    """
    This class is used to create an OS filepath browser button that autofills
    entry textboxes with the selected filepath.
    """
    
    def __init__(self, entry):
        """
        Constructor method used to initialize new browser instances.
        """
        
        self.entry = entry
    
    def browse_file(self):
        """ 
        This helper function opens a FILE selection dialog and inserts the 
        selected filepath into the specified textbox widget.
        """
        
        # Open OS dialog and store filepath as a string
        pathstr = tk.filedialog.askopenfilename()
        
        # Populate the textbox within the GUI only if the user entered a filepath
        if pathstr:
            self.entry.delete(0, tk.END)     # Delete previous text
            self.entry.insert(0, pathstr)    # Replace with new text
            
            # Show the end of long paths
            self.entry.icursor(tk.END)
            self.entry.xview_moveto(1.0)
    
    def browse_folder(self):
        """ 
        This helper function opens a FOLDER selection dialog and inserts the 
        selected filepath into the specified textbox widget.
        """
        
        # Open OS dialog and store filepath as a string
        pathstr = tk.filedialog.askdirectory()
        
        # Populate the textbox within the GUI only if the user entered a filepath
        if pathstr:
            self.entry.delete(0, tk.END)     # Delete previous text
            self.entry.insert(0, pathstr)    # Replace with new text
            
            # Show the end of long paths
            self.entry.icursor(tk.END)
            self.entry.xview_moveto(1.0)
       
class ToolTip:
    """
    This class is used to create a small pop-up tooltip that appears when the 
    user hovers over a widget and disappears when the mouse leaves the widget.
    """
    
    def __init__(self, widget, text):
        """
        Constructor method used to initialize new tooltip object instances 
        and bind display events to the widget.
        """
        
        # Store relevant tooltip objects
        self.tip_window = None      # The tooltip window object reference
        self.widget = widget        # The widget that activates the tooltip
        self.text = text            # The text to be displayed by the tooltip

        # Display tooltip when cursor hovers over widget, and remove it when not
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """
        This method displays the tooltip when the cursor hovers over the widget object.
        """

        # Check that another tooltip window isn't already being displayed (i.e. prevent duplicate windows)
        if self.tip_window:
            return

        # Create a small window for the tooltip
        self.tip_window = tw = tk.Toplevel(self.widget)
        
        # Remove standard window decor for tooltip (title, min/max buttons, etc.)
        tw.wm_overrideredirect(True)
        
        # Position tooltip box slightly below and to the right of the widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        tw.geometry(f"+{x}+{y}")

        # Insert the tooltip text as a window label
        label = ttk.Label(
            tw,
            text=self.text,
            style="ToolTip.TLabel",
            justify="left",
            wraplength=350,
            padding=6
        )
        label.pack()

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
    
    def __init__(self, window, window_row_ind, row_label, show_label=True, help_text="", config_value=""):
        """
        Constructor method used to initialize new entry row object instances.
        """
        
        self.window = window
        self.row_ind = window_row_ind
        self.row_label = row_label
        self.show_label = show_label
        self.help_text = help_text
        self.config_value = config_value
        
        if self.row_ind is None:
            raise ValueError("Row index is None. Check Row initialization.")

    def fp_row(self, is_file=True):
        """
        Method for defining an entry row for OS filepaths.
        """
        
        # COL 0-1: Construct label (col 0) and tooltip (col 1)
        if self.show_label:
            self.row_labels(label_width=30, label_col=0, tooltip_col=1)
        
        # COL 2: Create textbox entry
        entry = ttk.Entry(self.window, width=70)
        entry.grid(
            row=self.row_ind,
            column=2,
            padx=(5, 10),
            pady=4,
            sticky="ew"
        )
        
        # COL 2: Pre-fill entry with previous value from config.ini file if it exists
        if self.config_value:
            entry.insert(0, self.config_value)
            
            # Show the end of long paths
            entry.icursor(tk.END)
            entry.xview_moveto(1.0)
        
        # COL 3: Instantiate browser button object
        browser = Browser(entry)
        
        # COL 3: Construct textbox browse button for file or directory search accordingly
        if is_file:
            # Make button browse OS for files using helper func
            btn = ttk.Button(self.window, text="Browse", command=browser.browse_file)
        else:
            # Make button browse OS for directories using helper func
            btn = ttk.Button(self.window, text="Browse", command=browser.browse_folder)

        btn.grid(row=self.row_ind, column=3, padx=5, pady=4)
    
        # COL 4:# Create a label to specify whether a file or directory is required
        if self.show_label:
            type_label = ttk.Label(
                self.window,
                text="File" if is_file else "Directory",
                style="EntryType.TLabel"
            )
            type_label.grid(row=self.row_ind, column=4, padx=5)
        
        return entry
    
    def condition_row(self):
        """
        Method for defining an entry row for a boolean condition
        """

        # COL 0-1: Construct label (col 0) and tooltip (col 1)
        if self.show_label:
            self.row_labels(label_width=30, label_col=0, tooltip_col=1) 
         
        # COL 2: Create a frame to allow the conditional statement input columns 
        # to fit side-by-side within a single main window column
        cond_frame = ttk.Frame(self.window)
        cond_frame.grid(row=self.row_ind, column=2, padx=20)
        
        # Define options for boolean (relational) operators
        OPS = ["", "<", "<=", ">", ">=", "==", "!="]
        
        # Initialize local column and row for conditional row frame
        cond_row = 0
        cond_col = 0
        
        # COL 2.0: Create entry box for the left-hand side (LHS) value in boolean statement
        LHS_value = ttk.Entry(cond_frame, width=8)
        LHS_value.grid(row=cond_row, column=cond_col, padx=2)
        cond_col += 1

        # COL 2.1: Create option menu on LHS for boolean operators
        LHS_op = tk.StringVar()       # Entry variable is recognized as a string
        LHS_op_box = ttk.Combobox(    # Option box defines allowable strings,
            cond_frame,               # the user must select one to assign
            textvariable=LHS_op,      # as the value for the entry variable
            values=OPS,
            width=3,
            state="readonly"
        )
        LHS_op_box.grid(row=cond_row, column=cond_col, padx=2)
        LHS_op_box.configure(justify="center")
        cond_col += 1

        # COL 2.2: Create entry box for the center value in boolean statement
        # (for a simple boolean this is often just the parameter name (e.g. it would be "param" for 3 < param < 5))
        center_value = ttk.Entry(cond_frame, width=25)
        center_value.grid(row=cond_row, column=cond_col, padx=5)
        cond_col += 1

        # COL 2.3: Create option menu on right-hand side (RHS) for boolean operators
        RHS_op = tk.StringVar()       # Entry variable is recognized as a string
        RHS_op_box = ttk.Combobox(    # Option box defines allowable strings, 
            cond_frame,               # the user must select one to assign   
            textvariable=RHS_op,      # as the value for the entry variable
            values=OPS,
            width=3,
            state="readonly"
        )
        RHS_op_box.grid(row=cond_row, column=cond_col, padx=2)
        RHS_op_box.configure(justify="center")
        cond_col += 1
        
        # COL 2.4: Create entry box for the RHS value in boolean statement
        RHS_value = ttk.Entry(cond_frame, width=8)
        RHS_value.grid(row=cond_row, column=cond_col, padx=2)
    
        
        def update_entries(*args):
            """
            A short helper function that disables the opposite sides entry 
            variable if a single-sided boolean operator is used (== or !=).
            """
            if LHS_op.get() in ["==", "!="]:
                RHS_value.config(state="disabled")
                center_value.config(state="normal")
            elif RHS_op.get() in ["==", "!="]:
                LHS_value.config(state="disabled")
                center_value.config(state="normal")
            else:
                LHS_value.config(state="normal")
                RHS_value.config(state="normal")
                center_value.config(state="normal")
        
        LHS_op.trace_add("write", update_entries)
        RHS_op.trace_add("write", update_entries)

        # Return a dictionary containing all the conditional entry widgets
        return {"LHS_value": LHS_value,
                "LHS_op": LHS_op,
                "center_value": center_value,
                "RHS_op": RHS_op,
                "RHS_value": RHS_value}

    def add_basic_row(self, entries=None, is_file=True) -> int:
        """ 
        This helper function adds a single textbox row in the GUI for the user 
        to enter a new file or directory filepath, it then adds to the row index
        and returns the row number for the next textbox.
        """
        
        entry = self.fp_row(is_file)
    
        # Add current row's user-input text into the entries dictionary
        entries[self.row_label] = entry
        
        return self.row_ind + 1
    
    def row_labels(self, label_width, label_col, tooltip_col):
        """
        This helper function creates the label and helper tooltip for a row.
        """
        
        # Create label for the textbox on leftmost side of GUI row (col 0)
        rowlabel = ttk.Label(
            self.window,
            text=self.row_label,
            style="Header.TLabel",
            anchor="e",
            width=label_width
        )
        rowlabel.grid(row=self.row_ind, column=label_col, padx=5, pady=5, sticky="e")
        
        # Create label for help icon (col 1)
        help_label = ttk.Label(
            self.window,
            text="ⓘ",
            style="ToolTip.TLabel",
            cursor="hand2"
        )
        help_label.grid(row=self.row_ind, column=tooltip_col, sticky="w")
        
        # Create hoverable tooltip description for what text to enter in textbox
        ToolTip(help_label, self.help_text)

class DynamicRowList:
    """
    This class is used to create a row entry that can be dynamically expanded 
    by the user via buttons to include multiple internal sub-rows (which are 
    defined by the EntryRow class)
    """
    
    def __init__(self, frame, row_template, add_button, is_file=True, conditional=False):
        """
        Constructor method used to initialize a dynamic row list object.
        """
        
        self.entries = []
        
        # Dynamic row frame
        self.frame = frame
        self.frame_row = 0
        
        # Variables extracted from first row of the list (which is used as the template for all additional rows in the list to duplicate)
        self.row_template = row_template
        self.row_label = self.row_template.row_label
        self.help_text = self.row_template.help_text
        
        self.is_file = is_file
        self.conditional = conditional
        
        self.add_button = add_button
 
    def append_row_list(self):
        """
        Method for adding a new entry row to the dynamic row list.
        """
        
        if self.frame_row != 0:
            entry_label = "..."
            entry_width = 65
        else:
            entry_label = self.row_label
            entry_width = 70
        
        row_obj = EntryRow(window=self.frame,
                           window_row_ind=self.frame_row,
                           row_label=entry_label,
                           show_label=True,
                           help_text=self.help_text,
                           config_value="")
        
        entry = row_obj.fp_row(is_file=self.is_file)
        entry.config(width=entry_width)
    
        self.entries.append(entry)
        
        self.frame_row += 1
        
        if self.conditional and self.frame_row != 1:
            cond_row_obj = EntryRow(window=self.frame,
                               window_row_ind=self.frame_row,
                               row_label=entry_label,
                               show_label=True,
                               help_text="",
                               config_value="")
            cond_entries = cond_row_obj.condition_row()
            
            self.entries.append(cond_entries)
            self.frame_row += 1
        
        if self.add_button:
            self.add_button.grid(row=self.frame_row+1, column=2, pady=5)
    
        return entry