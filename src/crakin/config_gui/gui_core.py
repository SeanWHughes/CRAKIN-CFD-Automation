# -*- coding: utf-8 -*-
"""

GUI Core

"""

import tkinter as tk
from tkinter import ttk 

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
        
        # Build the main window for the GUI
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

        # Frame widget styles
        style.configure(
            "Input.TFrame",
            # bordercolor="#A6C8FF",
            # relief="solid"
        )

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
            padding=(5,5)
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
        self.btn_grid_kwargs.setdefault("pady", 30)
        
    def build_save_btn(self):
        """
        Method for placing the save button within the parent container (i.e. a
        window or frame.
        """
        
        # Build save button widget
        self.save_btn_wg = ttk.Button(
            self.container,
            command=lambda: self.config_app_obj.save_config(self.container),
            **self.btn_wg_kwargs
        )
        self.save_btn_wg.grid(**self.btn_grid_kwargs)