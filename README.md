# Brep-Tetrahedral-Mesh
___
This is a demo AddIn for Fusion 360 used to create brep bodies from tetrahedral meshes. This serves as a way to extract information from mesh files output by computational meshing tools for use in Boundary Representation modeling.
___
This AddIn adds two features to the Design Environment: 

* **Default Edge Joint** - This feature defines two bodies, and edge and a node. The 'edge body' is used as a template to be copied and resized between every node. The 'node body' will be copied to every node. As such, this AddIn can make use of custom geometry applied to each body.
* **Mesh Body** - This feature prompts the user to select their desired edge and node bodies, a .ele mesh file, and a .node mesh file. For the purposes of this demo, these files were generated from .stl files using [WIAS TetGen](https://wias-berlin.de/software/index.jsp?id=TetGen&lang=1). The output of this feature is a single BRep Body that corresponds to the input mesh. Creating hundreds or thousands of copies of arbitrary BRep Bodies and joining into a single body is very computationally expensive, so completing this feature may take some time.
___
### Example 1 - Truncated Icosahedron:
The input files for this example may be found in 'Form Example/3D-Files.zip'. The relevant mesh files were created with the command 'tetgen.exe -pqAa ExampleInput.stl'.
![Input Body](https://raw.githubusercontent.com/v-whitetail/brep-tetrahedral-mesh/master/Truncated%20Icosahedron%20Example/example-input.jpg)
**Input Body**
![Output Body](https://raw.githubusercontent.com/v-whitetail/brep-tetrahedral-mesh/master/Truncated%20Icosahedron%20Example/example-output.jpg)
**Output Body**
___
### Example 2 - NURBS Form:
The input files for this example may be found in 'Truncated Icosahedron Example/3D-Files.zip'. The relevant mesh files were created with the command 'tetgen.exe -pqAa ExampleInput.stl'.
![Input Body](https://raw.githubusercontent.com/v-whitetail/brep-tetrahedral-mesh/master/Form%20Example/example-input.jpg)
**Input Body**
![Output Body](https://raw.githubusercontent.com/v-whitetail/brep-tetrahedral-mesh/master/Form%20Example/example-output.jpg)
**Output Body**
