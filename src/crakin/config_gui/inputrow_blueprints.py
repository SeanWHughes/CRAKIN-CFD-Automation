# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 17:18:59 2026

@author: Sean
"""

#%%     IMPORT MODULES

# Standard modules
from dataclasses import dataclass, field
from typing import Literal

#%%     ROW CONTEXT DATACLASSES

@dataclass
class BaseInputRowContext:
    """
    Baseline dataclass containing every structural (i.e. non-state) variable 
    that is specific to a single row input (i.e. that row's particular 
    "context" within the config and GUI) such that the same row specifications (via an 
    InputRowSpec object) can be reused for multiple stylistically/functionally 
    identical rows so long as a unique InputRowContext object is supplied to a 
    builder function. InputRowContext objects are often referred to just as
    "ctx" or "context" for short.
    """
    
    # Spatial context
    container: any
    row_ind: int        # via grid kwargs
    base_col_ind: int   # via grid kwargs
    
    # Config.json architectural context
    cfg_group: str
    cfg_field: str
    cfg_rowid: str
    cfg_parent_rowid: str | None = None
    
    # Widget context (optional)
    simple_text: str | None = None
    hover_text: str | None = None
    
    # Initialize a key to package row coordinates within config.json
    cfg_key: tuple = field(init=False)

    def __post_init__(self):
        """
        Post-construction method for row contexts.
        """
        
        self.cfg_key = (self.cfg_group, self.cfg_field, self.cfg_rowid)
        
@dataclass
class FilepathInputRowContext(BaseInputRowContext):
    """
    Context dataclass for filepath input row.
    """
    
    # Widget context (optional)
    browse_mode: Literal["file", "folder"] | None = None
        
    def __post_init__(self):
        """ 
        Post-construction method for filepath input rows.
        """
        
        # Inherit/call the BaseInputRowSpec post-construction method
        super().__post_init__()
        
@dataclass
class ConditionInputRowContext(BaseInputRowContext):
    """
    Context dataclass for condition input row.
    """
    
    def __post_init__(self):
        """ 
        Post-construction method for filepath input rows.
        """
        
        # Inherit/call the BaseInputRowSpec post-construction method
        super().__post_init__()

#%%     INPUT ROW SPECIFICATION DATACLASSES

@dataclass
class BaseInputRowSpec:
    """ 
    Baseline specification dataclass for every type of input row. Every 
    InputRowSpec object ("spec" for short) represents the reusable instructions 
    for how to build a particular type of input row. These instructions are 
    then passed to a builder function as a single object such that many 
    instances can be built using identical instructions.
    """
    
    # Config.json specification
    cfg_spectype: str = None
    
    # Label option
    show_label: bool = True
    
    # Force any mutable defaults to be created for every instance of the class
    simple_label_kwargs: dict = field(default_factory=dict)
    tooltip_label_kwargs: dict = field(default_factory=dict)
    input_frame_kwargs: dict = field(default_factory=dict)
    
    box_ipady: int = 5
    
    def __post_init__(self):
        """ 
        Post-construction method for every type of input rows.
        """
        
        # Prevent BaseInputRowSpec from being instantiated directly
        if type(self) is BaseInputRowSpec:
            raise TypeError("BaseInputRowSpec cannot be instantiated directly. "
                            "You must use a type-specific InputRowSpec object.")

        # I. EXTRACTION: get widget/grid kwarg dicts, default to empty dicts
        # Simple row label
        self.simple_label_wg_kwargs = self.simple_label_kwargs.get("widget", {})
        self.simple_label_grid_kwargs = self.simple_label_kwargs.get("grid", {})
        
        # Tooltip row label
        self.pin_label_wg_kwargs = self.tooltip_label_kwargs.get("widget", {})
        self.pin_label_grid_kwargs = self.tooltip_label_kwargs.get("grid", {})
        self.hover_label_wg_kwargs = self.tooltip_label_kwargs.get("hover_label", {})
        self.tip_toplvl_wg_kwargs = self.tooltip_label_kwargs.get("tip_toplvl", {})
        
        # Frame container for all widgets that take in user inputs for the row
        self.input_frame_wg_kwargs = self.input_frame_kwargs.get("widget", {})
        self.input_frame_grid_kwargs = self.input_frame_kwargs.get("grid", {})
        
        # II. DEFAULTS: assign default keyword arguments
        # Set default widget options for input row label
        self.simple_label_wg_kwargs.setdefault("style", "Default.TLabel")
        self.simple_label_wg_kwargs.setdefault("anchor", "e")

        self.simple_label_grid_kwargs.setdefault("padx", 5)
        self.simple_label_grid_kwargs.setdefault("pady", 5)
        self.simple_label_grid_kwargs.setdefault("sticky", "e")
        
        # Set default widget options for pin label widget
        self.pin_label_wg_kwargs.setdefault("text", "ⓘ")
        self.pin_label_wg_kwargs.setdefault("style", "ToolTip.TLabel")
        self.pin_label_wg_kwargs.setdefault("cursor", "hand2")
        self.pin_label_wg_kwargs.setdefault("anchor", "e")
        
        # Set default grid options for pin label widget
        self.pin_label_grid_kwargs.setdefault("padx", 10)
        self.pin_label_grid_kwargs.setdefault("pady", 10)
        self.pin_label_grid_kwargs.setdefault("sticky", "e")
        
        # Set default widget options for hover label widget
        self.hover_label_wg_kwargs.setdefault("style", "ToolTip.TLabel")
        self.hover_label_wg_kwargs.setdefault("justify", "left")
        self.hover_label_wg_kwargs.setdefault("wraplength", 500)
        self.hover_label_wg_kwargs.setdefault("padding", 6)
        
        # Set default widget options for input frame widget
        self.input_frame_wg_kwargs.setdefault("style", "Input.TFrame")
    
    def _validate_grids(self, grid_list):
        """
        Ensures no grid kwargs contain forbidden spatial keys.
        """
    
        forbidden = {"row", "column"}
    
        for grid in grid_list:
            spatial = set(grid) & forbidden
    
            if spatial:
                raise ValueError(
                    f"{self.__class__.__name__} grid kwargs must not contain {forbidden}. "
                    "Spatial positioning is controlled by the builder."
                )
    
    def require_spectype(self, spec_type):
        """
        Method for checking the type of InputRowSpec object and throwing an
        error if it does not match the input spec type. This method is 
        inherited by all InputRowSpec classes and therefore can be used by 
        builder classes and methods to restrict the type of spec.
        """
        
        if not isinstance(self, spec_type):
            raise TypeError(
                f"This build method requires a InputRowSpec type of "
                f"{spec_type.__name__}, instead got " 
                f"{type(self.rowspec).__name__}"
            ) 

@dataclass
class FilepathInputRowSpec(BaseInputRowSpec):
    """ 
    Specification dataclass for filepath input row. 
    """
    
    # Config.json specification
    cfg_spectype: str = "filepath"
    
    # Force any mutable defaults to be created for every instance of the class 
    fp_entry_kwargs: dict = field(default_factory=dict)
    browse_btn_kwargs: dict = field(default_factory=dict)
    
    # Optional browse model option
    browse_mode: Literal["file", "folder"] = None
    
    def __post_init__(self):
        """ 
        Post-construction method for filepath input rows.
        """
        
        # Inherit/call the BaseInputRowSpec post-construction method
        super().__post_init__()
    
        # I. EXTRACTION: get widget/grid kwarg dicts, default to empty dicts 
        # Filepath text entry
        self.fp_entry_wg_kwargs = self.fp_entry_kwargs.get("widget", {})
        self.fp_entry_grid_kwargs = self.fp_entry_kwargs.get("grid", {})

        # Browse button
        self.browse_btn_wg_kwargs = self.browse_btn_kwargs.get("widget", {})
        self.browse_btn_grid_kwargs = self.browse_btn_kwargs.get("grid", {})
        
        # II. DEFAULTS: assign default keyword arguments
        # Set default widget options for filepath entry widget
        self.fp_entry_wg_kwargs.setdefault("style", "Default.TEntry")
        self.fp_entry_wg_kwargs.setdefault("width", 80)
        
        # Set default grid options for filepath entry widget
        self.fp_entry_grid_kwargs.setdefault("padx", 5)
        self.fp_entry_grid_kwargs.setdefault("sticky", "")

        # Set default widget options for browser button widget
        self.browse_btn_wg_kwargs.setdefault("text", "Browse")
        self.browse_btn_wg_kwargs.setdefault("style", "Browse.TButton")
        
        # Set default grid options for browser button widget
        self.browse_btn_grid_kwargs.setdefault("padx", 5)
        self.browse_btn_grid_kwargs.setdefault("sticky", "")
        
        # III. CLEANUP: remove/override some keyword arguments or throw error
        # Prevent repositioning of internal conditional statement widgets
        gridkwargs = [
            self.fp_entry_grid_kwargs,
            self.browse_btn_grid_kwargs
        ]
        
        self._validate_grids(gridkwargs)
        
@dataclass
class ConditionInputRowSpec(BaseInputRowSpec):   
    """ 
    Specification dataclass for condition input row. 
    """

    # Config.json specification
    cfg_spectype: str = "condition"

    # Force any mutable defaults to be created for every instance of the class 
    center_entry_kwargs: dict = field(default_factory=dict)
    LRHS_cbb_kwargs: dict = field(default_factory=dict)
    LRHS_entry_kwargs: dict = field(default_factory=dict)

    def __post_init__(self):
        """ 
        Post-construction method for condition input rows. 
        """  
        
        # Inherit/call the BaseInputRowSpec post-construction method
        super().__post_init__()
    
        # I. EXTRACTION: get widget/grid kwarg dicts, default to empty dicts 
        # Center text entry
        self.center_entry_wg_kwargs = self.center_entry_kwargs.get("widget", {})    
        self.center_entry_grid_kwargs = self.center_entry_kwargs.get("grid", {})
        
        # LHS and RHS combobox option entry
        self.LRHS_cbb_wg_kwargs = self.LRHS_cbb_kwargs.get("widget", {})
        self.LRHS_cbb_grid_kwargs = self.LRHS_cbb_kwargs.get("grid", {})
        
        # LHS and RHS text entry (symmetrical)
        self.LRHS_entry_wg_kwargs = self.LRHS_entry_kwargs.get("widget", {})        
        self.LRHS_entry_grid_kwargs = self.LRHS_entry_kwargs.get("grid", {})
        
        # II. DEFAULTS: assign default keyword arguments
        self.LRHS_entry_wg_kwargs.setdefault("style", "Default.TEntry")
        self.LRHS_entry_wg_kwargs.setdefault("width", 8)
        self.LRHS_entry_grid_kwargs.setdefault("padx", 2)
        
        self.center_entry_wg_kwargs.setdefault("style", "Default.TEntry")
        self.center_entry_wg_kwargs.setdefault("width", 25)
        self.center_entry_grid_kwargs.setdefault("padx", 5)
        
        self.LRHS_cbb_wg_kwargs.setdefault("width", 3)
        self.LRHS_cbb_wg_kwargs.setdefault("justify", "center")
        self.LRHS_cbb_grid_kwargs.setdefault("padx", 2)
        
        # III. CLEANUP: remove/override some keyword arguments or throw error
        # Prevent repositioning of internal conditional statement widgets
        gridkwargs = [
            self.center_entry_grid_kwargs,
            self.LRHS_cbb_grid_kwargs,
            self.LRHS_entry_grid_kwargs
        ]
        
        self._validate_grids(gridkwargs)
        
        # Prevent comboboxes from allowing anything but the relational operators
        for spec in ("values", "state", "textvariable"):
            self.LRHS_cbb_wg_kwargs.pop(spec, None)