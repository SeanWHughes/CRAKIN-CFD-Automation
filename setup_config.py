# -*- coding: utf-8 -*-
"""

User Configuration Setup Routine

This file creates a simple GUI for users to configure the main pipeline script.

To add more fields to the GUI simply add a help_text and add_row line to the 
main GUI construction section, then add a par["eg"] statement to the
save_config function so that user-inputs are saved for the program. Extract any
filepaths as you normally would to use elsewhere in the codebase.

"""

#%%     IMPORT MODULES

import tkinter as tk
from tkinter import filedialog, messagebox
import sys

from pathlib import Path
import configparser

#%%     HELPER FUNCTIONS

def browse_file(entry):
    """ 
    This helper function opens a FILE selection dialog and inserts the 
    selected filepath into the specified textbox widget.
    """
    
    # Open OS dialog and store filepath as a string
    pathstr = tk.filedialog.askopenfilename()
    
    # Populate the textbox within the GUI only if the user entered a filepath
    if pathstr:
        entry.delete(0, tk.END)     # Delete previous text
        entry.insert(0, pathstr)    # Replace with new text

def browse_folder(entry):
    """ 
    This helper function opens a FOLDER selection dialog and inserts the 
    selected filepath into the specified textbox widget.
    """
    
    # Open OS dialog and store filepath as a string
    pathstr = tk.filedialog.askdirectory()
    
    # Populate the textbox within the GUI only if the user entered a filepath
    if pathstr:
        entry.delete(0, tk.END)     # Delete previous text
        entry.insert(0, pathstr)    # Replace with new text
       
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
        label = tk.Label(tw, text=self.text, justify="left", 
                         background="#FFF6CF", relief="solid", 
                         borderwidth=1, wraplength=350, padx=5, pady=3)
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

def add_row(window, entry_dict, label, help_text, row, config_value="", is_file=True) -> int:
    """ 
    This helper function adds a single textbox row in the GUI for the user 
    to enter a new file or directory filepath, it then adds to the row index
    and returns the row number for the next textbox.
    """
    
    # Create label for the textbox on leftmost side of GUI row (col 0)
    rowlabel = tk.Label(window, text=label, anchor="w", width=30)
    rowlabel.grid(row=row, column=0, padx=5, pady=5, sticky="w")

    # Create label for help icon (col 1)
    help_label = tk.Label(window, text="[?]", fg="blue", cursor="hand2")
    help_label.grid(row=row, column=1, sticky="w")
    
    # Create hoverable tooltip description for what text to enter in textbox
    ToolTip(help_label, help_text)

    # Create textbox entry to the right of the label (col 2)
    entry = tk.Entry(window, width=70)
    entry.grid(row=row, column=2, padx=5)
    
    # Pre-fill filepath with previous value if config.ini file exists
    if config_value:
        entry.insert(0, config_value)

    # Create textbox browse button for file or directory search accordingly (col 3)
    if is_file:
        # Make button browse OS for files using helper func
        btn = tk.Button(window, text="Browse", command=lambda: browse_file(entry))
    else:
        # Make button browse OS for directories using helper func
        btn = tk.Button(window, text="Browse", command=lambda: browse_folder(entry))
    
    btn.grid(row=row, column=3, padx=5)
    
    # Create a label to specify whether a file or directory is required (col 4)
    type_label = tk.Label(window, text="File" if is_file else "Directory", width=10, fg="blue")
    type_label.grid(row=row, column=4, padx=5)

    # Add current row's user-input text into the entries dictionary
    entries[label] = entry
    
    # Add to row counter
    return row + 1

def config_get(config, section, key):
    "Tries to extract config key-value pair, otherwise returns empty string"
    try:
        return config[section][key]
    except KeyError:
        return ""

def save_config(entries, config_obj, config_path_obj, window):
    """
    This helper function saves the user-input filepaths to a config.ini file
    that can be parsed by the main script pipeline.
    """

    # Assign key value pairs to config object for filepaths from the entries dict
    config_obj["PROJECT"] = {
        "DOE_PROJ_DIR": entries["DOE Project Directory"].get(),
        "OF_CASE_DIR_TEMPLATE": entries["OpenFOAM Case Directory Template"].get()}

    config_obj["CREO"] = {
        "CREO_MODEL_FP": entries["Creo Parametric CAD Model File"].get(),
        "CREO_EXE_FP": entries["Creo Parametric Executable"].get(),
        "CREOSON_DIR": entries["CreoSON Directory"].get()}

    config_obj["ANSYS"] = {
        "WB_PROJ_FP": entries["ANSYS Workbench Project"].get(),
        "WB_EXE_FP": entries["ANSYS Workbench Executable"].get()}

    missing = []

    # Check for missing fields within the config object
    for section in config_obj:
        for key, value in config_obj[section].items():
            if not value.strip():
                missing.append(f"{section}:{key}")
                
    # Create an error popup if the user tries to save without filling all fields
    if missing:
        tk.messagebox.showerror("Missing Fields",
                                "Please fill in all fields:\n\n" + 
                                "\n".join(missing))
        return

    # Write config object contents to a config.ini file
    with open(config_path_obj, "w") as f:
        config.write(f)

    # Save confirmation message
    tk.messagebox.showinfo("Success",
                           f"Configuration saved to:\n{config_path_obj.resolve()}")
    
    # Close GUI after user clicks OK
    mainwin.destroy()

#%%     GUI CONSTRUCTION

# Try to find correct working directory
try:
    # If running outside IDE, try to get working directory from script location
    SCRIPT_FP = Path(__file__).resolve()
    WORK_DIR = SCRIPT_FP.parent
except:
    # If running inside IDE, try to assign current working directory from default
    WORK_DIR = Path.cwd()
    SCRIPT_FP = WORK_DIR / "setup_config.py"

if not Path(SCRIPT_FP).exists():
    sys.exit("Error: Could not determine the script location because the __file__ "
             "variable is not available. This typically occurs when running scripts"
             " inside an IDE. Please set WORK_DIR variable manually.")

# Assign working directory as a variable for the config.ini

# Try to find config.ini file and load it if it exists
config = configparser.ConfigParser()
config_path = Path("config.ini")

if config_path.exists():
    config.read(config_path)



# Construct main window object that will display the GUI
mainwin = tk.Tk()

# Specify dimensions of the main window object
mwin_w = 840
mwin_h = 450
mainwin.geometry(f"{mwin_w}x{mwin_h}")

# Label the main window with title and a short description
mainwin.title("DOE CFD Automation - Setup Configuration")
ltxt = "Populate the fields below with the absolute filepaths for your "\
       "CFD setup (manually or using the browser dialogs)."
label = tk.Label(mainwin, text=ltxt, font=("Arial", 10))
label.grid(row=0, column=0, columnspan=4, pady=20)

# Initialize dictionary for user-input values in textboxes
entries = {}

# Initialize row index
row = 1

# Create a row for each required user-input filepath, including textbox, tooltip, and descriptions 
key = "PROJECT"
help_text = "The directory where the script will store the parameter input sheet, "\
            "mesh optimization sheet, VBA macros, and all generated variant meshes."
row = add_row(mainwin, entries, "DOE Project Directory", help_text, row, 
              config_value=config_get(config, key, "DOE_PROJ_DIR"), is_file=False)

help_text = "The OpenFOAM case directory that will be copied and used for "\
            "every geometry variant generated by the script. The directory should "\
            "include everything necessary for your particular OpenFOAM case "\
            "setup except the mesh file. \n\n(Note: This script assumes that case"\
            " setup is otherwise identical for all generated variants)"
row = add_row(mainwin, entries, "OpenFOAM Case Directory Template", help_text, row, 
              config_value=config_get(config, key, "OF_CASE_DIR_TEMPLATE"), is_file=False)

key = "CREO"
help_text = "The filepath for the Creo Parametric CAD file. This is the CAD "\
            "that the mesh will be generated from and then input into the simulations."\
            "\n\n(Note: This file should not include the part version. The script"\
            " will automatically try to remove the version number but you can "\
            "also just remove the numbered portion of the file extension "\
            "yourself to be sure: e.g. my_part.prt.23 --> my_part.prt)"
row = add_row(mainwin, entries, "Creo Parametric CAD Model File", help_text, row, 
              config_value=config_get(config, key, "CREO_MODEL_FP"))

help_text = "The filepath for the \"parametric.exe\" file."
row = add_row(mainwin, entries, "Creo Parametric Executable", help_text, row,
              config_value=config_get(config, key, "CREO_EXE_FP"))

help_text = "The CreoSON directory containing the CreoSON application and all"\
            " supporting files. \n\n(e.g. C:\Program Files\CreosonServerWithSetup-3.0.1-win64)"
row = add_row(mainwin, entries, "CreoSON Directory", help_text, row, 
              config_value=config_get(config, key, "CREOSON_DIR"), is_file=False)

key = "ANSYS"
help_text = "The filepath for the .wbpj file being used to mesh the geometry."\
            "\n\n(Note: This Workbench project must be connected to the PTC Creo"\
            " CAD file using the CAD Associative Interface prior to running "\
            "the script)"    
row = add_row(mainwin, entries, "ANSYS Workbench Project", help_text, row, 
              config_value=config_get(config, key, "WB_PROJ_FP"))

help_text = "The filepath for the Workbench \"RunWB2.exe\" file."
row = add_row(mainwin, entries, "ANSYS Workbench Executable", help_text, row,
              config_value=config_get(config, key, "WB_EXE_FP"))

# Construct save button to save user-inputs into the entries dict
save_btn = tk.Button(mainwin, text="Save Configuration",
                     command=lambda: save_config(entries, config, config_path, mainwin),
                     bg="green", fg="white", height=2, width=25)
save_btn.grid(row=row, column=2, columnspan=1, pady=20)

# Add instructions for executable files
ltxt = "Note: For executables, the filepath should be for the actual "\
       "executable file, not the shortcut that is often used to launch the "\
       "software from Desktop. If you don't know where to find the real "\
       "executable, go to the shortcut and right-click > Properties > Target "\
       "will reveal the absolute filepath to input here. Additionally, you "\
       "must ensure that this is the correct version of the software you want"\
       " to run if you have multiple versions installed on your PC."
label = tk.Label(mainwin, text=ltxt, justify="left", font=("Arial", 8), wraplength=mwin_w-50)
label.grid(row=row+1, column=0, columnspan=5)

# Display GUI main window
mainwin.mainloop()

#%%     NORMALIZE CONFIG INPUTS


