# -*- coding: utf-8 -*-
"""

A large set of classes, methods, and functions used by setup_config.py to 
customize the config.json setup GUI.

NAMING CONVENTIONS:
In this code, all tkinter widgets (i.e. tk and ttk) are instantiated with an 
object name as follows: "{purpose}_{widget type}_wg. The "_wg" stands for 
"widget" or sometimes "_wgs" is used for a list of widgets. This reduces how
succinct the program is, but greatly improves readability for future 
customization. Similarly, custom class objects are always instantiated with an 
object name that ends in "_obj" for clarity. 

Finally, all tkinter widgets require a container for the widget to be placed
within ("container" is used here but these are also often referred to as
"parent", "owner", or "context"). Potential containers include: 
    
    tk.Tk(), tk.Frame(), tk.TopLevel(), tk.LabelFrame(), tk.Canvas(), 
    tk.PanedWindow(), etc.             

Each of these containers can safely be passed as the first argument for most 
tkinter widgets. The simplest of these containers is the tk.Tk() window (i.e. 
the "main window" or "root"). Windows are a special class of container because
they represent a window (or "tab") that is displayed on your PC and can be
minimized, expanded, etc. For this reason, unlike other containers, a window 
cannot be placed within another window. Therefore, in this code, the "window" 
argument is always reserved for the main window and no other containers. 
Conversely, "container" may refer to any container, including a window. 
Multiple windows can technically be created; however, this code is for a
single-window GUI application, and so the only real window used in this code
should be the main window.

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
    
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config_json_dict = json.load(f)
    
        for section, fields in self.arch.items():
    
            section_data = self.config_json_dict.get(section, {})
    
            for field in fields:
    
                field_val = section_data.get(field, None)
    
                # ---------------- NORMAL ENTRY ----------------
                if field in self.entries_dict and field_val is not None:
    
                    widget = self.entries_dict[field]
                    self._set_widget_value(widget, field_val)
    
                # ---------------- DYNAMIC ENTRY ----------------
                elif field in self.dynamic_entries and field_val:
    
                    dyn_list = self.dynamic_entries[field]
    
                    # Clear existing dynamic rows if needed
                    dyn_list.dynamic_entries_dict.clear()
    
                    for item in field_val:
    
                        if isinstance(item, dict):
    
                            dyn_list.append_row_list(config_values=item.get("main_fp", ""))
    
                            # You would also restore condition here if needed
                            # (depends on your EntryRow implementation)
    
                        elif isinstance(item, str):
    
                            dyn_list.append_row_list(config_values=item)
    
    def _set_widget_value(self, widget, value):
        """
        Safely sets a value into a Tkinter widget (Entry, StringVar, etc.)
        """
    
        if value is None:
            value = ""
    
        # StringVar
        if isinstance(widget, tk.StringVar):
            widget.set(value)
            return
    
        # Entry / ttk.Entry
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.delete(0, tk.END)
            widget.insert(0, value)
            return
    
        # fallback for anything with .set()
        if hasattr(widget, "set"):
            try:
                widget.set(value)
            except Exception:
                pass
            return
    
        # fallback for anything with .delete/.insert but not recognized type
        try:
            widget.delete(0, tk.END)
            widget.insert(0, value)
        except Exception:
            pass
    
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
    
    def save_config(self, container):
        """
        Save all entries (normal and dynamic) to config.json with sections.
        Dynamic entries are saved as JSON lists.
        """
        
        self.config_json_dict = {}
    
        # Loop through sections
        for section, fields in self.arch.items():
            self.config_json_dict[section] = {}
        
            for field in fields:
                print(section, field)
                
                # normal entry
                if field in self.entries_dict:

                    self.config_json_dict[section][field] = self._extract_widget_value(
                        self.entries_dict[field]
                    )
                    
                # dynamic entry
                elif field in self.dynamic_entries:

                    dyn_list = self.dynamic_entries[field]
    
                    values = []
                    for item in dyn_list.dynamic_entries_dict:
    
                        values.append({
                            "main_fp": self._extract_widget_value(item["main_fp"]),
                            "condition": (
                                self._extract_widget_value(item["condition"])
                                if item["condition"] else None
                            )
                        })
    
                    self.config_json_dict[section][field] = values
    
                else:
                    self.config_json_dict[section][field] = ""
    
        # Write JSON to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config_json_dict, f, indent=4)
    
        if container:
            messagebox.showinfo(
                "Configuration Saved",
                f"Configuration successfully saved to {self.config_path}"
            )
            
            # Close parent window (always the highest window in container hierarchy)
            container.winfo_toplevel().destroy()
    
    def _extract_widget_value(self, widget):
        """
        Private method to safely extract the value from a widget, StringVar, or nested dict.
        """
        if isinstance(widget, ttk.Entry):
            return widget.get()
        if isinstance(widget, tk.Entry):
            return widget.get()
        if isinstance(widget, tuple):
            return self._extract_widget_value(widget[1])
        if isinstance(widget, tk.StringVar):
            return widget.get()
        
        if isinstance(widget, dict):
            # Recursively extract values from dict
            return {k: self._extract_widget_value(subwidget) for k, subwidget in widget.items()}
        if isinstance(widget, list):
            return [self._extract_widget_value(item) for item in widget]
        elif hasattr(widget, "get"):
            # fallback for other Tk widgets
            try:
                return widget.get()
            except TypeError:
                return str(widget)
        else:        
            return str(widget)

#%%     GUI MAIN WINDOW CLASSES

class GUIBootstrap:
    """
    This class is used to create the main window for the GUI and applying styling.
    """
    
    def __init__(self, GUIwidth=1000, GUIheight=800, 
                 title="Configure Parameter Optimization Study", 
                 global_font="Segoe UI"):
        """
        Constructor method used to initialize the main window of the GUI.
        """
        
        # Create the main window for the GUI
        self.window = tk.Tk()
        self.width = GUIwidth
        self.height = GUIheight
        self.window.geometry(f"{GUIwidth}x{GUIheight}")
        
        self.window.grid_columnconfigure(2, weight=0)
        
        # Add GUI title
        self.window.title(title)
        
        # Automatically apply styling to the GUI
        self.global_font = global_font
        self._apply_styles()
        
        # Make GUI window expandable
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Make GUI window scrollable
        scroll_obj = ScrollableFrame(self.window)
        scroll_obj.grid(row=0, column=0, sticky="nsew")
        
        # Define the scrollable frame variable
        self.scroll_frame = scroll_obj.inner_frame_wg

    def _apply_styles(self):
        """
        Private method for applying ttk styling to the GUI. You can customize 
        the styling here by altering the style.configure(...) statements below.
        """
        
        # Define ttk style object
        style = ttk.Style(self.window)
        
        # Attempt to asign global theme as vista for Windows machines, otherwise use clam
        try:
            style.theme_use("vista")
        except tk.TclError:
            style.theme_use("clam")

        # Extract global font
        gfont = self.global_font

        # Label widget styles
        style.configure(
            "Default.TLabel",
            font=(gfont, 12),
            foreground="#4F81BD"
        )
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
        
        # Entry widget styles
        style.configure(
            "Default.TEntry",
            padding=4,
        )
        
        # Button widget styles
        style.configure(
            "Default.TButton",
            padding=5,
            foreground="#2E5C8A",
        )
        style.configure(
            "AddRow.TButton",
            padding=5,
            foreground="#2E5C8A",
        )
        style.configure(
            "Browse.TButton",
            padding=(8, 4),
            foreground="#2E5C8A",
        )
        style.configure(
            "SmallBrowse.TButton",
            padding=(2, 1),
            foreground="#2E5C8A"
        )
        style.configure(
            "Save.TButton",
            font=(gfont, 12, "bold"),
            foreground="#3CB371",
            padding=10
        )
        
        self.window.grid_columnconfigure(2, weight=0)

class ScrollableFrame(ttk.Frame):
    """
    This class is used to create a scrollable frame using the main window
    of the GUI.
    """
    
    def __init__(self, window, *args, **kwargs):
        """
        Constructor method used to initialize a scrollable frame widget.
        """
        
        # Inherit ttk.Frame class to instantiate ScrollableFrame (self) as a frame within the main window
        super().__init__(window, *args, **kwargs)

        # Allow scrollable frame to be expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Construct a canvas within scrollable frame to use as a viewport (displays a section of the much larger inner frame)
        self.viewport_canvas_wg = tk.Canvas(self, highlightthickness=0)
        self.viewport_canvas_wg.grid(row=0, column=0, sticky="nsew")

        # Construct vertical scrollbar on right of the scrollable frame
        self.scrollbar_wg = ttk.Scrollbar(self, orient="vertical", command=self.viewport_canvas_wg.yview)
        self.scrollbar_wg.grid(row=0, column=1, sticky="ns")
        
        # Associate the viewport canvas with the scrollbar / mouse scrolling
        self.viewport_canvas_wg.configure(yscrollcommand=self.scrollbar_wg.set)

        # Construct the full inner frame that contains all widgets
        self.inner_frame_wg = ttk.Frame(self.viewport_canvas_wg)
        self.canvas_window = self.viewport_canvas_wg.create_window((0, 0), window=self.inner_frame_wg, anchor="nw")

        # Make inner frame resize properly
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

    def __init__(self, container, config_app_obj, btn_wg_kwargs=None, 
                 btn_grid_kwargs=None):
        """
        Constructor method used to initialize a save button widget.
        """
        
        # Parent container
        self.container = container
        
        # Config object
        self.config_app_obj = config_app_obj
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        self.btn_wg_kwargs = btn_wg_kwargs or {}
        self.btn_grid_kwargs = btn_grid_kwargs or {}
        
        # Set default widget options for save button widget
        self.btn_wg_kwargs.setdefault("text", "Save Configuration")
        self.btn_wg_kwargs.setdefault("style", "Save.TButton")
        
        # Set default grid options for save button widget
        self.btn_grid_kwargs.setdefault("columnspan", 1)
        self.btn_grid_kwargs.setdefault("pady", 30)
        
    def build_save_btn(self):
        """
        Method for placing the save button within the parent container (i.e. a
        window or frame.
        """
        
        # Create save button widget
        self.save_btn_wg = ttk.Button(
            self.container,
            command=lambda: self.config_app_obj.save_config(self.container),
            **self.btn_wg_kwargs
        )
        
        # Position save button widget
        self.save_btn_wg.grid(**self.btn_grid_kwargs)

#%%     GUI ROW ELEMENT CLASSES

class FPBrowser:
    """
    This class is used to create an OS filepath browser button that autofills
    entry textboxes with the selected filepath.
    """
    
    def __init__(self, container, fp_entry_wg, browse_mode, btn_wg_kwargs=None, 
                 btn_grid_kwargs=None):
        """
        Constructor method used to initialize new filepath browser instances.
        """
        
        # Parent container
        self.container = container
        
        # Entry row widget
        self.fp_entry_wg = fp_entry_wg
        
        # Browser mode (file or folder)
        self.browse_mode = browse_mode
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        self.btn_wg_kwargs = btn_wg_kwargs or {}
        self.btn_grid_kwargs = btn_grid_kwargs or {}
        
        # Set default widget options for browser button widget
        self.btn_wg_kwargs.setdefault("text", "Browse")
        self.btn_wg_kwargs.setdefault("style", "Browse.TButton")
        
        # Set default grid options for browser button widget
        btn_grid_kwargs.setdefault("row", fp_entry_wg.grid_info()["row"])
        btn_grid_kwargs.setdefault("column", fp_entry_wg.grid_info()["column"] + 1)
        btn_grid_kwargs.setdefault("padx", 5)
        btn_grid_kwargs.setdefault("pady", 4)
    
    def _browse_filepaths(self):
        """ 
        Method for opening a FILE selection dialog and inserts the 
        selected filepath into the specified textbox widget.
        """

        # Open OS dialog and store filepath as a string (either a file or folder)
        if self.browse_mode == "file":
            pathstr = filedialog.askopenfilename()
        elif self.browse_mode == "folder":
            pathstr = filedialog.askdirectory()
        else:
            raise ValueError("ERROR: mode is neither \"file\" nor \"folder\": {self.browse_mode}")
    
        # Populate the textbox within the GUI only if the user entered a filepath
        if pathstr:
            self.fp_entry_wg.delete(0, tk.END)     # Delete previous text
            self.fp_entry_wg.insert(0, pathstr)    # Replace with new text
            
            # Show the end of long paths
            self.fp_entry_wg.icursor(tk.END)
            self.fp_entry_wg.xview_moveto(1.0)
            
    def build_browse_btn(self):
        
        # Create button widget
        browse_btn_wg = ttk.Button(
            self.container,
            command=lambda: self._browse_filepaths(),
            **self.btn_wg_kwargs
        )

        # Position button widget
        browse_btn_wg.grid(**self.btn_grid_kwargs)
       
class ToolTip:
    """
    This class is used to transform a normal tkinter label widget into a 
    special tooltip label widget that displays a texbox when the user hovers
    their cursor over the normal label.
    """
    
    def __init__(self, pin_label_wg, hover_label_wg_kwargs, 
                 toplvl_wg_kwargs=None):
        """
        Constructor method used to initialize new tooltip object instances 
        and bind display events to the widget.
        """
        
        # The label widget that activates the tooltip            
        self.pin_label_wg = pin_label_wg   
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        self.hover_label_wg_kwargs = hover_label_wg_kwargs
        self.toplvl_wg_kwargs = toplvl_wg_kwargs or {}
        
        # The tooltip container object reference
        self.tip_container = None   

        # Set default widget options for hover label widget
        self.hover_label_wg_kwargs.setdefault("style", "ToolTip.TLabel")
        self.hover_label_wg_kwargs.setdefault("justify", "left")
        self.hover_label_wg_kwargs.setdefault("wraplength", 350)
        self.hover_label_wg_kwargs.setdefault("padding", 6)

        # Display tooltip when cursor hovers over label widget, and remove it when not
        pin_label_wg.bind("<Enter>", self._show_tooltip)
        pin_label_wg.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event=None):
        """
        Private method to stop displaying the tooltip when an event occurs.  
        In the tooltip class constructor the event is defined as the cursor 
        moving INTO the pin label widget.
        """

        # Check that another tooltip container isn't already being displayed (i.e. prevent duplicate containers)
        if self.tip_container:
            return

        # Create a small container for the tooltip
        self.tip_container = tk.Toplevel(
            self.pin_label_wg, 
            **self.toplvl_wg_kwargs
        )
        
        # Remove standard container decor for tooltip (title, min/max buttons, etc.)
        self.tip_container.wm_overrideredirect(True)
        
        # Position tooltip box slightly below and to the right of the label widget
        x = self.pin_label_wg.winfo_rootx() + 20
        y = self.pin_label_wg.winfo_rooty() + 20
        self.tip_container.geometry(f"+{x}+{y}")

        # Insert the tooltip text as a label within the tooltip container
        hovertxt_label_wg = ttk.Label(
            self.tip_container,
            **self.hover_label_wg_kwargs
        )
        hovertxt_label_wg.pack()

    def _hide_tooltip(self, event=None):
        """
        Private method to stop displaying the tooltip when an event occurs.  
        In the tooltip class constructor the event is defined as the cursor 
        moving OUT OF the pin label widget.
        """
        
        # If the tooltip container is open, remove it and reset the tooltip container object ref
        if self.tip_container:
            self.tip_container.destroy()
            self.tip_container = None
            
class EntryRowLabel:
    def __init__(self, container, label_wg_kwargs, label_grid_kwargs):
        """
        Constructor method for entry row labels (i.e. any label that is used
        to describe an entry row built from the EntryRow class)
        """
        
        # Parent container
        self.container = container
        
        # Keyword arguments
        self.label_wg_kwargs = label_wg_kwargs
        self.label_grid_kwargs = label_grid_kwargs
        
        # Set default widget options for entry row label widget
        self.label_wg_kwargs.setdefault("style", "Default.TLabel")
        self.label_wg_kwargs.setdefault("anchor", "e")
        
        # Set default grid options for entry row label widget
        self.label_grid_kwargs.setdefault("padx", 5)
        self.label_grid_kwargs.setdefault("pady", 5)

    def build_normal_label(self):
        """
        Method for creating a normal entry row label
        """
        
        self.label_grid_kwargs.setdefault("sticky", "e")
    
        row_label_wg = ttk.Label(
            self.container, 
            **self.label_wg_kwargs
        )
        
        row_label_wg.grid(**self.label_grid_kwargs)
    
    def build_tooltip_label(self, hover_label_wg_kwargs=None, 
                            toplvl_wg_kwargs=None):
        """
        Method for creating a tooltip entry row label
        """
        
        # Set default widget options for pin label widget
        self.label_wg_kwargs["text"] = "ⓘ"
        self.label_wg_kwargs["style"] = "ToolTip.TLabel"
        self.label_wg_kwargs["cursor"] = "hand2"
           
        # Set default grid options for pin label widget
        self.label_grid_kwargs["sticky"] = "w"

        # Create pin label widget that will activate the tooltip
        pin_label_wg = ttk.Label(
            self.container,
            **self.label_wg_kwargs
        )
        
        # Position pin label widget
        pin_label_wg.grid(**self.label_grid_kwargs)
        
        # Turn help icon into a hoverable, detailed description for what text to enter in textbox
        ToolTip(pin_label_wg, hover_label_wg_kwargs, toplvl_wg_kwargs)

#%%     GUI ROW ENTRY CLASSES

class EntryRow:
    """
    This class is used to create any row containing one or more user-input 
    entry widgets. Various types of user-inputs are allowed via the methods 
    below.
    """
    
    def __init__(self, container, field_var, row_ind, base_col_ind=0, 
                 show_label=True, config_value=None, norm_label_kwargs=None, 
                 tooltip_label_kwargs=None, entry_kwargs=None, 
                 browse_btn_kwargs=None):
        """
        Constructor method used to initialize new entry row object instances.
        """
        
        # Parent container
        self.container = container
        
        # Associated key-value pair within the config.json file
        self.field_var = field_var
        self.config_value = config_value
        
        # Row index for the entire entry row plus optional base column
        self.row_ind = row_ind
        self.base_col_ind = base_col_ind
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        self.norm_label_wg_kwargs = (norm_label_kwargs or {}).get("widget", {})
        self.norm_label_grid_kwargs = (norm_label_kwargs or {}).get("grid", {})
        self.pin_label_wg_kwargs = (tooltip_label_kwargs or {}).get("widget", {})
        self.pin_label_grid_kwargs = (tooltip_label_kwargs or {}).get("grid", {})
        self.hover_label_wg_kwargs = (tooltip_label_kwargs or {}).get("hover_label", {})
        self.toplvl_wg_kwargs = (tooltip_label_kwargs or {}).get("toplevel", {})
        self.entry_wg_kwargs = (entry_kwargs or {}).get("widget", {})
        self.entry_grid_kwargs = (entry_kwargs or {}).get("grid", {})
        self.browse_btn_wg_kwargs = (browse_btn_kwargs or {}).get("widget", {})
        self.browse_btn_grid_kwargs = (browse_btn_kwargs or {}).get("grid", {})
     
        # If entry row should have labels
        self.show_label = show_label
        
        # Override erroneous kwarg row definitions to force all widgets into same row
        self.entry_grid_kwargs["row"] = self.row_ind
        self.norm_label_grid_kwargs["row"] = self.row_ind
        self.pin_label_grid_kwargs["row"] = self.row_ind
        self.browse_btn_grid_kwargs["row"] = self.row_ind
        
        # Set default widget options for normal button widget
        self.entry_wg_kwargs.setdefault("width", 90)
        
        # DEFAULTS
        
        offset = -2 if not self.show_label else 0
        
        # Place each widget in adjacent columns by default (can be overriden by kwargs)
        self.norm_label_grid_kwargs.setdefault("column", self.base_col_ind)
        self.pin_label_grid_kwargs.setdefault("column", self.base_col_ind + 1)
        self.entry_wg_kwargs.setdefault("style", "Default.TEntry")
        self.entry_grid_kwargs.setdefault("column", self.base_col_ind + 2 + offset)
        self.browse_btn_grid_kwargs.setdefault("column", self.base_col_ind + 3 + offset)
        

        # All entry rows must have labels if specified
        # I: Create normal label
        if self.show_label:
            norm_label_obj = EntryRowLabel(
                self.container,
                self.norm_label_wg_kwargs,
                self.norm_label_grid_kwargs
            )
            norm_label_obj.build_normal_label()
        
        # II: Create tooltip label
        if self.show_label:
            tooltip_label_obj = EntryRowLabel(
                self.container,
                self.pin_label_wg_kwargs,
                self.pin_label_grid_kwargs
            )
            tooltip_label_obj.build_tooltip_label(
                self.hover_label_wg_kwargs,
                self.toplvl_wg_kwargs
            )

    def build_fp_row(self, browse_mode):
        """
        Method for defining an entry row for OS filepaths.
        """

        # DEFAULTS
        self.entry_grid_kwargs.setdefault("padx", (5, 10))
        self.entry_grid_kwargs.setdefault("padx", 4)
        self.entry_grid_kwargs.setdefault("sticky", "ew")
        
        # III: Create textbox entry 
        fp_entry_wg = ttk.Entry(
            self.container, 
            **self.entry_wg_kwargs
        )
        fp_entry_wg.grid(**self.entry_grid_kwargs)
        
        # Pre-fill entry with previous value from config.json file if it exists
        if self.config_value:
            fp_entry_wg.insert(0, self.config_value)
            
            # Show the end of long paths
            fp_entry_wg.icursor(tk.END)
            fp_entry_wg.xview_moveto(1.0)
        
        # IV: Instantiate filepath browser button object
        browser_obj = FPBrowser(
            self.container, 
            fp_entry_wg, 
            browse_mode,
            self.browse_btn_wg_kwargs,
            self.browse_btn_grid_kwargs
        )
        browser_obj.build_browse_btn()
        
        return fp_entry_wg
    
    def build_cond_row(self, LRHS_entry_kwargs=None, LRHS_cbb_kwargs=None, 
                       center_entry_kwargs=None):
        """
        Method for defining an entry row for a boolean condition
        """
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        LRHS_entry_wg_kwargs = (LRHS_entry_kwargs or {}).get("widget", {})
        LRHS_entry_grid_kwargs = (LRHS_entry_kwargs or {}).get("grid", {})
        LRHS_cbb_wg_kwargs = (LRHS_cbb_kwargs or {}).get("widget", {})
        LRHS_cbb_grid_kwargs = (LRHS_cbb_kwargs or {}).get("grid", {})
        center_entry_wg_kwargs = (center_entry_kwargs or {}).get("widget", {})
        center_entry_grid_kwargs = (center_entry_kwargs or {}).get("grid", {})
        
        # DEFAULTS
        # Entire condition row
        self.entry_grid_kwargs.setdefault("padx", 20)
        self.entry_grid_kwargs.setdefault("sticky", "w")
        
        # Get rid of any potential erroneous specifications
        for spec in ("row", "column"):
            LRHS_entry_grid_kwargs.pop(spec, None)
            LRHS_cbb_grid_kwargs.pop(spec, None)
            center_entry_grid_kwargs.pop(spec, None)
        for spec in ("values", "state", "textvariable"):
            LRHS_cbb_wg_kwargs.pop(spec, None)
        
        # LHS and RHS entry widgets
        LRHS_entry_wg_kwargs.setdefault("width", 8)
        LRHS_entry_grid_kwargs.setdefault("padx", 2)
        
        # Center entry widget
        center_entry_wg_kwargs.setdefault("width", 25)
        center_entry_grid_kwargs.setdefault("padx", 5)
        
        # LHS and RHS combobox widget
        LRHS_cbb_wg_kwargs.setdefault("width", 3)
        LRHS_cbb_wg_kwargs.setdefault("justify", "center")
        LRHS_cbb_grid_kwargs.setdefault("padx", 2)

    
        # III: Create a frame to allow the conditional statement input columns 
        # to fit side-by-side within a single parent container column
        cond_frame_wg = ttk.Frame(self.container)
        cond_frame_wg.grid(**self.entry_grid_kwargs)
        
        # Define options for boolean (relational) operators
        OPS = ["", "<", "<=", ">", ">=", "==", "!="]
        
        # Initialize local column and row for conditional row frame
        cond_row = 0
        cond_col = 0
        
        # COL 0: Create entry box for the left-hand side (LHS) value in boolean statement
        LHS_entry_wg = ttk.Entry(cond_frame_wg, **LRHS_entry_wg_kwargs)
        LHS_entry_wg.grid(row=cond_row, column=cond_col, **LRHS_entry_grid_kwargs)
        cond_col += 1

        # COL 1: Create option menu on LHS for boolean operators
        LHS_op = tk.StringVar()         # Text variable is recognized as a string
        LHS_cbb_wg = ttk.Combobox(       # Option box defines allowable strings,
            cond_frame_wg,              # the user must select one to assign
            textvariable=LHS_op,        # as the value for the entry variable
            values=OPS,
            state="readonly",
            **LRHS_cbb_wg_kwargs
        )
        LHS_cbb_wg.grid(row=cond_row, column=cond_col, **LRHS_cbb_grid_kwargs)
        cond_col += 1

        # COL 2: Create entry box for the center value in boolean statement
        # (for a simple boolean this is often just the parameter name (e.g. it would be "param" for 3 < param < 5))
        center_entry_wg = ttk.Entry(cond_frame_wg, **center_entry_wg_kwargs)
        center_entry_wg.grid(row=cond_row, column=cond_col, **center_entry_grid_kwargs)
        cond_col += 1

        # COL 3: Create option menu on right-hand side (RHS) for boolean operators
        RHS_op = tk.StringVar()         # Text variable is recognized as a string
        RHS_cbb_wg = ttk.Combobox(       # Option box defines allowable strings, 
            cond_frame_wg,              # the user must select one to assign   
            textvariable=RHS_op,        # as the value for the entry variable
            values=OPS,
            **LRHS_cbb_wg_kwargs
        )
        RHS_cbb_wg.grid(row=cond_row, column=cond_col, **LRHS_cbb_grid_kwargs)
        cond_col += 1
        
        # COL 4: Create entry box for the RHS value in boolean statement
        RHS_entry_wg = ttk.Entry(cond_frame_wg, **LRHS_entry_wg_kwargs)
        RHS_entry_wg.grid(row=cond_row, column=cond_col, **LRHS_entry_grid_kwargs)
    
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
        raw_condition_dict = {                          # Object type...
            "LHS_entry_wg": LHS_entry_wg,               # ttk.Entry()
            "LHS_cbb_wg": LHS_cbb_wg,                     # ttk.Combobox()
            "center_entry_wg": center_entry_wg,         # ttk.Entry()
            "RHS_cbb_wg": RHS_cbb_wg,                     # ttk.Combobox()
            "RHS_entry_wg": RHS_entry_wg                # ttk.Entry()
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
                    cond_dict["LHS_cbb_wg"] = raw_condition_dict["LHS_cbb_wg"].get()
                if key == "RHS_entry_wg":
                    cond_dict["RHS_cbb_wg"] = raw_condition_dict["RHS_cbb_wg"].get()

        return cond_dict

class DynamicRowList:
    """
    This class is used to create a row entry that can be dynamically expanded 
    by the user via buttons to include multiple internal sub-rows.
    """
    
    def __init__(self, main_rowentry_obj, show_label=True, browse_mode="File", 
                 conditional=True, config_values=None, add_btn_wg_kwargs=None,
                 add_btn_grid_kwargs=None):
        """
        Constructor method used to initialize a dynamic row list object.
        """
        
        # Initialize entry list
        self.dynamic_entries_dict = []
        self.main_rowentry_obj = main_rowentry_obj
        
        # Browse mode and label options
        self.browse_mode = browse_mode
        self.show_label = show_label

        # Extract container from row entry object
        self.container = main_rowentry_obj.container
        self.field_var = main_rowentry_obj.field_var

        # Dynamic Row List Variables
        self.conditional = conditional
        
        # Keyword arguments (and convert any immutable defaults kwargs to empty dicts)
        self.add_btn_wg_kwargs = add_btn_wg_kwargs or {}
        self.add_btn_grid_kwargs = add_btn_grid_kwargs or {}
        
        # DEFAULTS
        self.add_btn_wg_kwargs.setdefault("text", "Add Entry Row")
        self.add_btn_wg_kwargs.setdefault("style", "AddRow.TButton")
        self.add_btn_grid_kwargs.setdefault("pady", 5)

        # Create main filepath row within outer container
        self.main_entry_wg = main_rowentry_obj.build_fp_row(self.browse_mode)
        
        # Extract grid info from the entry row widget
        self.cont_row = self.main_entry_wg.grid_info()["row"]
        self.cont_col = self.main_entry_wg.grid_info()["column"]
        self.cont_colspan = self.main_entry_wg.grid_info().get("columnspan", 1)
    
        # Construct internal dynamic row frame for all potential subsequent rows
        self.dyn_frame_wg = ttk.Frame(self.container)
        self.dyn_frame_wg.grid(
            row=self.cont_row + 1, 
            column=self.cont_col, 
            columnspan=self.cont_colspan, 
            sticky=""
        )
        
        # Initialize internal frame row counter
        self.frame_row = 0
        self.frame_col = 2

        # Instantiate dynamic "add row" button within the frame
        self.add_btn_wg = ttk.Button(
            self.dyn_frame_wg,
            command=self.append_row_list,
            **self.add_btn_wg_kwargs   
        )
        self.add_btn_wg.grid(
            row=self.frame_row + 1, 
            column=self.frame_col,
            **self.add_btn_grid_kwargs 
        )
 
    def append_row_list(self):
        """
        Method for adding a new entry row to the dynamic row list.
        """

        # ---------- (1) FILEPATH ROW -----------
        # Create an additional filepath entry row in the internal frame
        
        # I: Instantiate entry row object
        fp_row_obj = EntryRow(
            container=self.dyn_frame_wg,
            field_var=self.field_var,
            row_ind=self.frame_row,
            base_col_ind=self.frame_col,
            show_label=self.show_label,
            config_value="",
            entry_kwargs = {"widget": {"width": 70}},
            browse_btn_kwargs = {"widget": {"style": "SmallBrowse.TButton"}}
        )

        # II: Construct filepath row
        fp_entry_wg = fp_row_obj.build_fp_row(self.browse_mode)
        
        # III: Increment frame row index
        self.frame_row += 1
        # ---------------------------------------

        # ---------- (2) CONDITION ROW ----------
        # Create an additional condition entry row in the internal frame
        
        # Only place row if specified
        if self.conditional:

            # I: Instantiate entry row object
            cond_row_obj = EntryRow(
                container=self.dyn_frame_wg,
                field_var=self.field_var,
                row_ind=self.frame_row,
                base_col_ind=self.frame_col,
                show_label=self.show_label,
                config_value=""
            )

            # II: Construct condition row and extract cond
            cond_dict = cond_row_obj.build_cond_row()
            
            # III: Increment frame row index
            self.frame_row += 1
        # ---------------------------------------
            
        # Store all entry widgets within the widget list
        self.dynamic_entries_dict.append({
            "main_fp": fp_entry_wg,
            "condition": cond_dict if self.conditional else None
        })
        
        # Reposition add entry button
        self.add_btn_wg.grid(
            row=self.frame_row + 1, 
            **self.add_btn_grid_kwargs
        )

        return self.dynamic_entries_dict