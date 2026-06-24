### CONFIG GUI:
The config\_gui directory contains a large set of classes, methods, and functions
used to customize the config.json setup and integration within the config GUI.

### STRUCTURE:
Briefly, the structure of the entire config\_gui codebase is as follows:

    InputRowSpec -> InputRowElementBuilder -> InputRowBuilder ->  
    PolyInputRowSpec -> PolyInputRowBuilder

The gui\_core.py is used to setup the GUI window and any of the more complex
non-input row elements of the GUI. The config\_io.py is used to communicate info
between the frontend and backend (config.json).

### NAMING CONVENTIONS:

In this code, all tkinter widgets (i.e. tk and ttk) are instantiated with an
object name as follows: `{purpose}_{widget type}_wg`. The `_wg` stands for
"widget" or sometimes `_wgs` is used for a list or dict of widgets. Similarly,
widget options are specified through `{purpose}_{widget type}_wg_kwargs`, while
grid options are specified through `{purpose}_{widget type}_grid_kwargs`.
Additionally, custom class objects are often instantiated with an object name
that ends in `_obj`. This reduces how succinct the program is, but greatly
improves clarity for future customization. 

### CONTAINERS:

All tkinter widgets require a container for the widget to be placed within
("container" is used here but these are also often referred to as "parent",
"owner", or "context"). Potential containers include: 
    
    tk.Tk(), tk.Frame(), tk.TopLevel(), tk.LabelFrame(), tk.Canvas(), 
    tk.PanedWindow(), etc.             

Each of these containers can safely be passed as the first argument for most
tkinter widgets. The simplest of these containers is the `tk.Tk()` window (i.e.
the "main window" or "root"). Windows are a special class of container because
they represent a window (or "tab") that is displayed on your PC and can be
minimized, expanded, etc. For this reason, unlike other containers, a window
cannot be placed within another window. Therefore, in this code, the "window"
argument is always reserved for the main window and no other containers.
Conversely, "container" may refer to any container, including a window. Multiple
windows can technically be created; however, this code is for a single-window
GUI application, and so the only real window used in this code should be the
main window.

### INPUT ROW BLUEPRINTS:

The code for the config GUI reflects the structure of the GUI itself. The basic
unit of the GUI is an "input row", which is just a standardized multi-column row
that allows for some type of user input. These input rows are built using two
dataclass objects ("blueprints"): 

1. **Input Row Specification:** (i.e the `InputRowSpec` or "spec" for short). 
   This is used to detail the style and settings of a particular input row using
   keyword arguments such that it can be applied to many input rows, regardless
   of where they are built within the GUI.

2. **Input Row Context:** (i.e. the `InputRowContext` or "ctx" for short). 
   This is used to detail the position of the input row within the GUI as well
	as the position and relationship of the input row within the config.json
	file. It also details any of the widget keyword arguments that must be
	specific to each individual instance of that input row type. This allows for
	the "individual row" values to be separate from the more general "row style"
	of the spec classes. As such, a unique context must be supplied for every
	input row.

### INPUT ROW BUILDERS:

Input rows are built using three files within the config\_gui directory. 

The lowest level builders are within inputrow\_element\_builders.py, which
contains all of the custom methods used to build all of the widgets for a
particular input row. Every input row must contain some widgets that transfer a
user-input (UI) value into the config.json. All of the UI-connected widgets are
built within an input frame to keep them organized within the GUI. Other
standard input row elements that do not contain UI are also programmed here
(e.g. input row labels), each of which has its own column within the GUI.

Above this level, there are then input row builders within inputrow\_builders.py,
which contains static methods used to build an entire input row. An input row
builder will call each of the required element builders for that particular
input row type to then construct it within the GUI. Additionally, each input row
builder will call an InputRow dataclass to instantiate an object representing
the row that was just built and storing important information about that input
row within the object. This object is then automatically registered with a
config app to coordinate transferring of user-inputs into the config.json file.

Finally, there are poly-row builders within poly\_inputrow\_builders.py, which
organize and connect multiple input rows together within the config.gui and then
reflect this backend connection with a frontend visual connection on the GUI.
The dataclasses detailing the specifications for a poly-row builder can be found
in poly\_inputrow\_blueprints.py.

### CONFIG INPUT-OUTPUT:

The config\_io.py file contains a class for a config app that initializes the
config.json file, manages all of the gui outputs, and then converts these into
inputs for the config.json file. The InputRow object cache and the config
architecture are the two main dictionaries that dictate the config setup through
the app. 

The InputRow object cache is created automatically as the user builds the GUI
via the input row builders.

Conversely, the config architecture must be written by the user directly at the
start of the launch\_config\_gui.py file. This architecture file essentially
dictates "what" you intend on populating the config.json file with. In the
default case provided within this code, it is primarily filepaths for the
various software and project files used by the automation pipeline. However,
this config can be easily extended or modified to include other software
filepaths. 

Additionally, the config can be modified to allow for different types of inputs
entirely so long as the code for a new input row is added to the codebase. For
example, for a new input row type of "Name", these codebase changes include:

1. A '{Name}InputRowContext' dataclass within inputrow\_blueprints.py
2. A `{Name}InputRowSpec` dataclass within inputrow\_blueprints.py
3. A `build_{name}_UI_widgets` method within the `InputRowElementBuilder` class
   inside inputrow\_element\_builders.py.
4. A `build_{name}_inputrow` static method within the `InputRowBuilder` class
   inside inputrow\_builders.py
5. Adding the `build_{name}_inputrow` method to the `IR_BUILDERS` list within the
   `BasePolyInputRowSpec` dataclass inside poly\_inputrow\_blueprints.py (this
   ensures that all poly input row builders can recognize your new input row
   type and build it).

An analagous procedure is required to add any new poly input row methods as
well.