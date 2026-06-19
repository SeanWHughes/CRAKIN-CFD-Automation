# -*- coding: utf-8 -*-
"""



"""

#%%     IMPORT MODULES

# Standard modules
from dataclasses import dataclass, field

# Custom modules
from config_io import ConfigSetupApp
import inputrow_blueprints as irBP
from inputrow_element_builders import InputRowElementBuilder

#%%     INPUT ROW OUTPUT DATACLASS

@dataclass
class InputRow:
    """
    A dataclass containing all of the structural AND runtime state variables 
    associated with a single input row within the GUI to allow for object 
    relationships and to normalize IO.
    """
    
    # Store structural input data
    ctx: irBP.InputRowContext
    spec: irBP.BaseInputRowSpec

    # Store runtime state variable data
    widgets: dict = field(default_factory=dict)
    UIvars: dict = field(default_factory=dict)     # This is essentially the GUI output
    
    # Store config metadata
    cfg_last_modified: str = ""

#%%     INPUT ROW BUILDER CLASSES

class InputRowBuilder:
    """
    This class is used to build user input rows inside the GUI using the 
    options arguments from InputRowSpec objects. Every input row returns an 
    InputRow object that will store the user-selected configuration info from 
    the GUI.
    """
    
    @staticmethod
    def _register_inputrow(ctx: irBP.InputRowContext, spec: irBP.ConditionInputRowSpec, 
                        widgets, UIvars, cfg_app_obj):
        """
        Private method for creating and then registering an InputRow object.
        """
        
        # Create InputRow object
        inputrow_obj = InputRow(
            ctx=ctx,
            spec=spec,
            widgets=widgets,
            UIvars=UIvars
        )
        
        # Package the InputRow key as a tuple
        IR_key = ctx.cfg_key
        
        # Add InputRow object to the config app object's internal storage
        cfg_app_obj.inputrow_objs[IR_key] = inputrow_obj
        
        return inputrow_obj
    
    @staticmethod
    def build_fp_inputrow(ctx: irBP.InputRowContext, spec: irBP.FilepathInputRowSpec, 
                          cfg_app_obj):
        """
        Method for building filepath input rows into the GUI.
        """

        # Require a FilepathInputRowSpec for the builder spec
        spec.require_spectype(irBP.FilepathInputRowSpec)
        
        # Throw an error if invalid browse mode chosen
        if spec.browse_mode not in ("file", "folder"):
            raise ValueError(f"browse_mode must be 'file' or 'folder, invalid value: {spec.browse_mode}")
        
        # Extract filepath config values from config.json
        cfg_pull_values = cfg_app_obj.config_get(ctx.cfg_key) or {}
        
        # Initialize row element builder
        subbuilder = InputRowElementBuilder(ctx, spec)
        
        # Build row header if specified
        if spec.show_label:
            subbuilder.build_simple_label()
            subbuilder.build_tooltip_label()
        
        # Build filepath entry widget and browser button
        fp_UIvars, fp_wgs = subbuilder.build_filepath_UI_widgets(cfg_pull_values)
        
        # Return registered InputRow object
        return InputRowBuilder._register_inputrow(
            ctx=ctx, 
            spec=spec, 
            widgets=fp_wgs, 
            UIvars=fp_UIvars, 
            cfg_app_obj=cfg_app_obj
        )
        
    @staticmethod
    def build_cond_inputrow(ctx: irBP.InputRowContext, 
                            spec: irBP.ConditionInputRowSpec, 
                            cfg_app_obj: ConfigSetupApp):
        """
        Method for building conditional statement input rows into the GUI.
        """
        
        # Require a ConditionInputRowSpec for the builder spec
        spec.require_spectype(irBP.ConditionInputRowSpec)
        
        # Extract condition config values from config.json
        cfg_pull_values = cfg_app_obj.config_get(ctx.cfg_key) or {}
        
        # Initialize row element builder
        subbuilder = InputRowElementBuilder(ctx, spec)
        
        # Build row header if specified
        if spec.show_label:
            subbuilder.build_simple_label()
            subbuilder.build_tooltip_label()
            
        # Build conditional statement entry
        cond_UIvars, cond_wgs = subbuilder.build_condition_UI_widgets(cfg_pull_values)
        
        # Return registered InputRow object
        return InputRowBuilder._register_inputrow(
            ctx=ctx, 
            spec=spec, 
            widgets=cond_wgs, 
            UIvars=cond_UIvars, 
            cfg_app_obj=cfg_app_obj
        )