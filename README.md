# blender_spritesheet_builder
headless Blender spritesheet builder utility for normal maps and renders for gamedev

##### Requires the PIL library, installed to Blender's bundled Python 

Command line syntax:

##### blender -b -P sheetbuild.py -- `[ANG] [CAP] [RADIUS] [MESH.BLEND]`

ANG : number of angles of the model to capture in the spritesheet

CAP : number of frames to capture in the spritesheet

RADIUS : radius of the mesh in the blend file

MESH.BLEND : name of the blend file where MESH is the name of the mesh of the object to capture, e.g "Spider.blend" for a mesh named "Spider"

### (resized) examples:

![](images/normal_spritesheet_Spider_resize.png)
![](images/render_spritesheet_Spider_resize.png)
