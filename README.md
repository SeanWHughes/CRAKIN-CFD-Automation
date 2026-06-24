# CRA:KIN | CFD Resource Administrator for Academics: Keep It Nimble

Hey! What's crackin'?  

CRA:KIN is an automation tool to help researchers efficiently perform massive computational fluid dynamics (CFD) parameter optimization projects (or any other format of CFD design of experiments (DOE) work). It is designed to provide a simple, user-friendly interface and require minimal coding knowledge to successfully use for your CFD project. Oftentimes, CFD geometry optimization problems can explode in complexity, and researchers must spend hours of their time doing repetitious work in numerous software packages to generating their dataset. CRA:KIN, just like the mythical aquatic creature, will wrap itself around each one of these critical softwares and power through your CFD project.

This tool was originally developed to optimize a novel microfluidic ECMO oxygenator in the BRITE Lab at Nemours Children's Hospital. 

It functions via connecting PTC Creo® Parametric --> ANSYS Fluent® --> OpenFOAM along with Excel sheets throughout the whole pipeline. The decision to base the CRA:KIN architecture on these software was entirely for their notable accessibility to researchers (i.e. entirely free or low-cost). In the future, I hope to expand CRA:KIN to allow for integration with other commonly used intelligent parametric CAD software (e.g. SOLIDWORKS®) and especially, expand it for use with a viable opensource meshing software. 

The codebase uses a config GUI to adapt the tool to your specific PC's software locations. Then, it uses a handful of key Excel spreadsheets that the user pre-configures according to their particular case setup to manage the DOE or parameter optimization pipeline.
