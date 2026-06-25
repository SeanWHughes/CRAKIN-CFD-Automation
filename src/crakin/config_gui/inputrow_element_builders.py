# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 08:18:18 2026

@author: Sean
"""

#%%     IMPORT MODULES

# Standard modules
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Tuple

# Custom modules
import inputrow_blueprints as irBP

#%%     ROW ELEMENT BUILDERS
    
class InputRowElementBuilder:
    """
    This class is used to build every widget within each input row.
    """
    
    def __init__(self, ctx: irBP.BaseInputRowContext, 
                 spec: irBP.BaseInputRowSpec):
        """
        Constructor method for row element builder objects managing the
        layout and row specifications for all elements within the row.
        """
        
        self.ctx = ctx
        self.container = ctx.container
        self.row_ind = ctx.row_ind
        self.base_col_ind = ctx.base_col_ind
        self.spec = spec
        
        # RESOLVE: Prefer context options over spec options if overlap
        self.simple_text = self._resolve_option(
            self.ctx.simple_text,
            self.spec.simple_label_wg_kwargs.get("text")
        )
        self.hover_text = self._resolve_option(
            self.ctx.hover_text,
            self.spec.hover_label_wg_kwargs.get("text")
        )

    def _resolve_option(self, ctx_value, spec_value):
        """
        Context overrides spec.
        """
        return ctx_value if ctx_value is not None else spec_value            

    def _note_modifications(self, widget):
        """
        Marks row as modified in ConfigSetupApp.
        """
    
        # Walk up references safely
        try:
            app = self.container.winfo_toplevel().app_ref
            app.mark_mods(self.ctx.cfg_key)
        except Exception:
            pass
        
    def _adjust_cellsizes(self, input_frame_wg, 
                          row_range: Tuple[int, int] | int, 
                          col_range: Tuple[int, int] | int):
        """
        Private method that adjusts the size of internal rows and columns of
        an input frame to allow each cell to expand to the size of the widget
        within it.
        """
        
        # Adjust cell size in y-axis for every cell in the row
        if isinstance(row_range, tuple):        
            for row_index in range(row_range[0], row_range[1] + 1):
                input_frame_wg.rowconfigure(row_index, weight=1)
        elif isinstance(row_range, int):
            input_frame_wg.rowconfigure(row_range, weight=1)
        else:
            raise ValueError("Row range must be an int or tuple of the min row "
                             "index and max row index")
        
        # Adjust cell size in x-axis for every cell in the column
        if type(col_range) is tuple:
            for col_index in range(col_range[0], col_range[1] + 1):
                input_frame_wg.columnconfigure(col_index, weight=1)
        elif isinstance(col_range, int):
            input_frame_wg.columnconfigure(col_range, weight=1)
        else:
            raise ValueError("Column range must be an int or tuple of the min "
                             "col index and max col index")

    def build_simple_label(self):
        """
        Method used to build a simple input row label for any input row type.
        """

        # I. CONTEXT: Set row and column
        row_ind = self.row_ind
        col_ind = self.base_col_ind     # Default is leftmost column

        # II: BUILD: Build all necessary widgets
        # Build simple input row label
        simple_label_wg = ttk.Label(
            self.container,
            text=self.simple_text,
            **self.spec.simple_label_wg_kwargs
        )
        simple_label_wg.grid(
            row=row_ind,
            column=col_ind,
            **self.spec.simple_label_grid_kwargs
        )

        return simple_label_wg
    
    def build_tooltip_label(self):
        """
        Method used to build a special tooltip label for any input row type.
        The tooltip displays a texbox when the user hovers their cursor over 
        the label widget.
        """
        
        # I. CONTEXT: Set row and column
        row_ind = self.row_ind              
        col_ind = self.base_col_ind + 1     # Default to 2nd leftmost column

        # II: BUILD: Build all necessary widgets
        # Build pin label widget that will activate the tooltip textbox
        pin_label_wg = ttk.Label(
            self.container,
            **self.spec.pin_label_wg_kwargs
        )
        pin_label_wg.grid(
            row=row_ind,
            column=col_ind,
            **self.spec.pin_label_grid_kwargs
        )
        
        # Initialize tooltip container object reference
        tip_toplvl_wg = None

        def _show_tooltip(event=None):
            """
            Private method to start displaying the tooltip when the cursor 
            moves OVER the pin label widget.
            """
    
            # Specify that tip container is from parent method
            nonlocal tip_toplvl_wg
    
            # Build a small container for the tooltip
            tip_toplvl_wg = tk.Toplevel(
                pin_label_wg, 
                **self.spec.tip_toplvl_wg_kwargs
            )
            
            # Remove standard container decor for tooltip
            tip_toplvl_wg.wm_overrideredirect(True)
            
            # Position tooltip box slightly below and to the right of the label widget
            x = pin_label_wg.winfo_rootx() + 20
            y = pin_label_wg.winfo_rooty() + 20
            tip_toplvl_wg.geometry(f"+{x}+{y}")
    
            # Insert the tooltip text as a label within the tooltip container
            hovertxt_label_wg = ttk.Label(
                tip_toplvl_wg,
                text=self.hover_text,
                **self.spec.hover_label_wg_kwargs
            )
            hovertxt_label_wg.pack()
    
        def _hide_tooltip(event=None):
            """
            Private method to stop displaying the tooltip when the cursor 
            moves OFF of the pin label widget.
            """
            
            # Specify that tip container is from parent build_tooltip method
            nonlocal tip_toplvl_wg
            
            # If the tooltip container is open, remove it and reset the tooltip container object ref
            if tip_toplvl_wg:
                tip_toplvl_wg.destroy()
                tip_toplvl_wg = None

        # Display tooltip when cursor hovers over label widget, and remove it when not
        pin_label_wg.bind("<Enter>", _show_tooltip)
        pin_label_wg.bind("<Leave>", _hide_tooltip)

    def build_filepath_UI_widgets(self):
        """
        Method used to build an OS filepath input row with an entry widget
        and a browser button that populates the filepath string into the entry 
        widget.
        """
        
        # I. SPEC GATE: Require a FilepathInputRowSpec for the builder spec
        self.spec.require_spectype(irBP.FilepathInputRowSpec)
        
        # RESOLVE: Prefer context options over spec options if overlap
        self.browse_mode = self._resolve_option(
            self.ctx.browse_mode,
            self.spec.browse_mode
        )
        # Throw an error if invalid browse mode chosen
        if self.browse_mode not in ("file", "folder"):
            raise ValueError(f"browse_mode must be 'file' or 'folder, invalid value: {self.browse_mode}")
        
        # II. CONTEXT: Set row and column
        row_id = self.row_ind
        col_id = self.base_col_ind + 2
        
        # III. UI VARS: Create variables for user-input values
        # Initialize a string variable for UI text
        fp_entry_UIvar = tk.StringVar()
        
        # IV: BUILD: Build all necessary widgets
        # Build input frame to contain all filepath input widgets
        input_frame_wg = ttk.Frame(
            self.container,
            **self.spec.input_frame_wg_kwargs
        )
        input_frame_wg.grid(
            row=row_id,
            column=col_id,
            **self.spec.input_frame_grid_kwargs
        )
        
        # Resize cells according to widget
        self._adjust_cellsizes(
            input_frame_wg, 
            row_range=0, 
            col_range=(self.base_col_ind, col_id)
        )
        
        # Build filepath entry widget
        fp_entry_wg = ttk.Entry(
            input_frame_wg,
            textvariable=fp_entry_UIvar,
            **self.spec.fp_entry_wg_kwargs
        )
        fp_entry_wg.grid(
            row=0,
            column=0,
            **self.spec.fp_entry_grid_kwargs
        )
        
        def _browse_filepaths():
            """ 
            Method for opening a filepath selection dialog and inserts the 
            selected filepath into the specified entry widget.
            """

            # Open OS dialog and store filepath as a string (either a file or folder)
            if self.browse_mode == "file":
                pathstr = filedialog.askopenfilename()
            elif self.browse_mode == "folder":
                pathstr = filedialog.askdirectory()
        
            # Populate the textbox within the GUI only if the user entered a filepath
            if pathstr:
                fp_entry_wg.delete(0, tk.END)     # Delete previous text
                fp_entry_wg.insert(0, pathstr)    # Replace with new text
                
                # Show the end of long paths
                fp_entry_wg.icursor(tk.END)
                fp_entry_wg.xview_moveto(1.0)

        # Build browser button widget
        browse_btn_wg = ttk.Button(
            input_frame_wg,
            command=lambda: _browse_filepaths(),
            **self.spec.browse_btn_wg_kwargs
        )
        browse_btn_wg.grid(
            row=0,
            column=1,
            **self.spec.browse_btn_grid_kwargs
        )
        
        # V TRACE: Attach tracker to UI variable
        fp_entry_UIvar.trace_add("write", lambda *args: self._note_modifications(fp_entry_wg))
        
        # VI OUTPUT: Package all outputs into dicts
        # Package UI variables
        fp_UIvars = {"fp_entry_UIvar": fp_entry_UIvar}
        
        # Package widgets
        fp_wgs = {"fp_entry_wg": fp_entry_wg}
        
        return fp_UIvars, fp_wgs
    
    def build_condition_UI_widgets(self):
        """
        Method used to build a conditional statement and prevents nonsensical
        conditions using combobox and entry widgets.
        """
        
        # I. SPEC GATE: Require a ConditionInputRowSpec for the builder spec
        self.spec.require_spectype(irBP.ConditionInputRowSpec)
        
        # II. CONTEXT: Set row and column
        row_ind = self.row_ind
        col_ind = self.base_col_ind + 2
        
        # III. UI VARS: Create variables for user-input values
        # Initialize a string variables for UI text and selections
        LHS_entry_UIvar = tk.StringVar()
        LHS_cbb_UIvar = tk.StringVar()
        center_entry_UIvar = tk.StringVar()
        RHS_cbb_UIvar = tk.StringVar()
        RHS_entry_UIvar = tk.StringVar()

        # IV: BUILD: Build all necessary widgets     
        # Build input frame to contain all conditional statement input widgets
        input_frame_wg = ttk.Frame(
            self.container,
            **self.spec.input_frame_wg_kwargs
        )
        input_frame_wg.grid(
            row=row_ind,
            column=col_ind,
            **self.spec.input_frame_grid_kwargs
        )
        
        # Define options for boolean (relational) operators
        OPS = ["", "<", "<=", ">", ">=", "==", "!="]
        
        # COL 0: Build entry box for the left-hand side (LHS) value in boolean statement
        LHS_entry_wg = ttk.Entry(
            input_frame_wg,
            textvariable=LHS_entry_UIvar,
            **self.spec.LRHS_entry_wg_kwargs
        )
        LHS_entry_wg.grid(
            row=0, 
            column=0, 
            **self.spec.LRHS_entry_grid_kwargs
        )

        # COL 1: Build option menu on LHS for boolean operators
        LHS_cbb_wg = ttk.Combobox(
            input_frame_wg,
            textvariable=LHS_cbb_UIvar,
            values=OPS,
            state="readonly",
            **self.spec.LRHS_cbb_wg_kwargs
        )
        LHS_cbb_wg.grid(
            row=0, 
            column=1, 
            **self.spec.LRHS_cbb_grid_kwargs
        )

        # COL 2: Build entry box for the center value in boolean statement
        center_entry_wg = ttk.Entry(
            input_frame_wg,
            textvariable=center_entry_UIvar,
            **self.spec.center_entry_wg_kwargs
        )
        center_entry_wg.grid(
            row=0, 
            column=2, 
            **self.spec.center_entry_grid_kwargs
        )

        # COL 3: Build option menu on right-hand side (RHS) for boolean operators
        RHS_cbb_wg = ttk.Combobox(
            input_frame_wg,
            textvariable=RHS_cbb_UIvar,
            values=OPS,
            **self.spec.LRHS_cbb_wg_kwargs
        )
        RHS_cbb_wg.grid(
            row=0, 
            column=3, 
            **self.spec.LRHS_cbb_grid_kwargs
        )
        
        # COL 4: Build entry box for the RHS value in boolean statement
        RHS_entry_wg = ttk.Entry(
            input_frame_wg,
            textvariable=RHS_entry_UIvar,
            **self.spec.LRHS_entry_wg_kwargs
        )
        RHS_entry_wg.grid(
            row=0, 
            column=4, 
            **self.spec.LRHS_entry_grid_kwargs
        )
        
        # Resize cells according to widget
        self._adjust_cellsizes(input_frame_wg, row_range=0, col_range=(0, 4))
        
        # V: TRACE: Attach trackers to UI variables
        LHS_entry_UIvar.trace_add("write", lambda *args: self._note_modifications(input_frame_wg))
        LHS_cbb_UIvar.trace_add("write", lambda *args: self._note_modifications(input_frame_wg))
        center_entry_UIvar.trace_add("write", lambda *args: self._note_modifications(input_frame_wg))
        RHS_cbb_UIvar.trace_add("write", lambda *args: self._note_modifications(input_frame_wg))
        RHS_entry_UIvar.trace_add("write", lambda *args: self._note_modifications(input_frame_wg))
    
        def _update_condition_status():
            """
            Private method used to prevent poorly defined boolean statements
            from being entered by disabling entries.
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
            lhs = LHS_cbb_UIvar.get()
            rhs = RHS_cbb_UIvar.get()
            
            # CHECK FORBIDDEN CONDITIONAL STATEMENTS
            # 1. If LHS op is a one-sided operator disable RHS
            if lhs in eq_rels:
                RHS_entry_wg.config(state="disabled")
                
            # 2. If RHS op is a one-sided operator disable LHS
            elif rhs in eq_rels:
                LHS_entry_wg.config(state="disabled")
                
            # 3. If LHS and RHS ops are both less than center entry
            elif lhs in less_rels and rhs in more_rels:
                LHS_entry_wg.config(state="disabled")
                
            # 4. If LHS and RHS ops are both greater than center entry
            elif lhs in more_rels and rhs in less_rels:
                LHS_entry_wg.config(state="disabled")
                
            # Keep everything normal otherwise
            else:
                LHS_entry_wg.config(state="normal")
                RHS_entry_wg.config(state="normal")

        # Update the status of all entries in the row anytime a relational operator is changed
        LHS_cbb_UIvar.trace_add("write", _update_condition_status)
        RHS_cbb_UIvar.trace_add("write", _update_condition_status)
        
        def _safe_get(widget, UIvar):
            """
            Private function that returns nothing for disabled widgets rather
            than altering the UI variable itself.
            """
            if widget.cget("state") == "disabled":
                return None
            else:
                return UIvar
        
        # VI OUTPUT: Package all outputs into dicts
        # Package UI variables
        cond_UIvars = {
            "LHS_entry_UIvar": _safe_get(LHS_entry_wg, LHS_entry_UIvar),
            "LHS_cbb_UIvar": _safe_get(LHS_cbb_wg, LHS_cbb_UIvar),
            "center_entry_UIvar": _safe_get(center_entry_wg, center_entry_UIvar),
            "RHS_cbb_UIvar": _safe_get(RHS_cbb_wg, RHS_cbb_UIvar),
            "RHS_entry_UIvar": _safe_get(RHS_entry_wg, RHS_entry_UIvar)
        }
        
        # Package widgets
        cond_wgs = {
            "LHS_entry_wg": LHS_entry_wg,
            "LHS_cbb_wg": LHS_cbb_wg,
            "center_entry_wg": center_entry_wg,
            "RHS_cbb_wg": RHS_cbb_wg, 
            "RHS_entry_wg": RHS_entry_wg
        }

        return cond_UIvars, cond_wgs