# -*- coding: utf-8 -*-
"""

ANSYS Parameter Update Mesh Generator Subprocess

This subprocess is executed by creo_ansys_parametric_mesh_link.py to update
the ANSYS WB mesh for a particular design variant and then export it.

"""

#%%     INITIALIZATION

import os

variant_name = os.environ["VARIANT_NAME"]
output_dir = os.environ["OUTPUT_DIR"]

mesh_output = os.path.join(
    output_dir,
    variant_name + ".msh"
)

print("Processing:", variant_name)

# Get systems
system1 = GetSystem(Name="Fluid Flow")
geometry = system1.GetContainer(ComponentName="Geometry")
mesh = system1.GetContainer(ComponentName="Mesh")

#%%     UPDATE MESH

# Update geometry
geometry.Refresh()
geometry.Update(AllDependencies=True)

print("Geometry updated from Creo")

# Update Mesh
mesh.Edit()
mesh.SendCommand(
    Command="""
mesh.GenerateMesh()
"""
)

mesh.Exit()

print("Mesh regenerated")

#%%     EXPORT MESH

setup = system1.GetContainer(ComponentName="Setup")
setup.Edit()
setup.SendCommand(
    Command='''
file/write-mesh "{}"
'''.format(mesh_output.replace("\\", "/"))
)

setup.Exit()

print(f"Mesh exported : {variant_name}")