# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 09:27:58 2026

@author: Sean
"""

#%%     IMPORT MODULES

# Standard modules
import tkinter as tk
from tkinter import ttk 

# Custom modules
import inputrow_blueprints as irBP
import poly_inputrow_blueprints as pirBP

#%%     POLY INPUT ROW BUILDERS

class DynamicInputRowBuilder:
    """
    Dynamically builds GUI rows from InputRowSpec objects in a row-type 
    agnostic way.
    """

    def __init__(self, polyspec: pirBP.DynamicPolyInputRowSpec):
        
        # Initialize PolyInputRowSpec object
        self.polyspec = polyspec
        
        # Initialize a counter for every dynamic input row added
        self.inputrow_count = 0

        # Build a frame to build dynamic entries within
        self.dyn_frame_wg = ttk.Frame(
            polyspec.p_container,
            **polyspec.dyn_frame_wg_kwargs
        )
        self.dyn_frame_wg.grid(
            row=polyspec.p_row_ind + 1,
            column=polyspec.p_base_col_ind + 2,
            **polyspec.dyn_frame_grid_kwargs
        )
        
        # Internal row counter inside dynamic frame
        self.frame_row = 0
        
        # Build a frame to build "add row" buttons within dynamic frame
        self.btn_frame_wg = ttk.Frame(
            self.dyn_frame_wg,
            **polyspec.btn_frame_wg_kwargs
        )
        self.btn_frame_wg.grid(
            row=self.frame_row + 1,
            column=0,
            **polyspec.btn_frame_grid_kwargs
        )
        
        # Force first column to be an adjustable spacer
        self.btn_frame_wg.grid_columnconfigure(0, weight=1)
        
        # Initialize button variables
        btn_col = 1
        self.add_btn_wgs = {}
        
        # Build an add row button for each spec type
        for spec in polyspec.specs:
            # Build add row button
            self.add_btn_wgs[type(spec)] = ttk.Button(
                self.btn_frame_wg,
                text=f"Add {spec.cfg_spectype} row",
                command=lambda spec=spec: self.append_row(spec),
                **polyspec.add_btn_wg_kwargs
            )
            self.add_btn_wgs[type(spec)].grid( 
                row=0,
                column=btn_col,
                **polyspec.add_btn_grid_kwargs
            )
            
            # Prevent column from expanding
            self.btn_frame_wg.grid_columnconfigure(btn_col, weight=0)
            
            # Increment button column
            btn_col += 1
            
        # Force last column to be an adjustable spacer
        self.btn_frame_wg.grid_columnconfigure(btn_col, weight=1)

    def append_row(self, spec):
        """
        Method for adding a new row based on a spec type.
        """
        
        # Get polyspec from builder
        polyspec = self.polyspec
        
        # Increment dynamic input row counter
        self.inputrow_count += 1
        
        # Define rowids
        cfg_parent_rowid = polyspec.p_cfg_rowid
        cfg_rowid = f"{cfg_parent_rowid}.{self.inputrow_count}"

        # Initialize context for the row to be appended
        dyn_ctx = irBP.InputRowContext(
            container=self.dyn_frame_wg,
            row_ind=self.frame_row,
            base_col_ind=polyspec.p_base_col_ind,
            cfg_group=polyspec.p_cfg_group,
            cfg_field=polyspec.p_cfg_field,
            cfg_rowid=cfg_rowid,
            cfg_parent_rowid=cfg_parent_rowid
        )
        
        # Determine the builder function for the input spec
        builder_func = polyspec.IR_BUILDERS.get(type(spec))
        
        # Build the input row
        builder_func(
            ctx=dyn_ctx, 
            spec=spec, 
            cfg_app_obj=polyspec.cfg_app_obj
        )

        # Increment row position
        self.frame_row += 1
        
        # Reposition button frame down a row
        self.btn_frame_wg.grid_configure(row=self.frame_row)