#Davin Jimeno
#Blender v2.81.16
#Blender 3D to spritesheet/normals headless util

bl_info = {
    "name": "3D_2_Spritesheet",
    "author": "Davin Jimeno",
    "version": (1, 0),
    "blender": (2, 81, 16),
    "location": "",#"View3D > Add > Mesh > New Object",
    "description": "pack a 3D model",
    "warning": "requires PIL library",
    "wiki_url": "",
    "category": "Create Images",
}

import bpy, sys, shutil, math, os, time, argparse
from bpy.app.handlers import persistent
from PIL import Image

#do not flush ram after loading a new file
@persistent
def load_handler(dummy):
	print("Load Handler:", bpy.data.filepath)

def main():
	
	argv = sys.argv
	if "--" not in argv:
		argv = []
	else:
		argv = argv[argv.index("--") + 1:]

	usage_text = (
		"Usage: blender -b -P sheetbuilder.py -- [ANGLES] [FRAMES] [RADIUS] [MESH.BLEND]"
	)	
		
	#initiate load handler	
	bpy.app.handlers.load_post.append(load_handler)

	#take in values
	ang = int(argv[0]) # number of angles
	cap = int(argv[1]) # number of animation frame captures
	radius = float(argv[2]) # radius of model
	model_file = argv[3]

	#defaults
	cam_d = math.radians(30) # camera depression
	cam_rad = radius + 5 #camera distance
	height = cam_rad * math.tan(math.pi/2 - cam_d)
	cur_cap = 1 # current capture frame
	cur_ang = 0 # current angle
	max_cap_anim = 25 #number of frams in anim

	#operate on temp file
	temp_name_file = "temp_" + model_file
	shutil.copyfile(model_file, temp_name_file)
	
	#make temp output folders
	try:
		core_name = os.path.splitext(model_file)[0]
		#print(core_name)
		top_fold_name = "output_" + core_name + "_" + time.strftime("%Y%m%d-%H%M%S")
		#toplevel
		os.mkdir(top_fold_name)
		#renders
		rend_fold_name = top_fold_name + '/' + "renders_" + core_name
		os.mkdir(rend_fold_name)
		#normals
		norm_fold_name = top_fold_name + '/' + "normals_" + core_name
		os.mkdir(norm_fold_name)
	except FileExistsError:
		print("Output directory creation conflict")
		sys.exit(1)

	#locations
	camloc = (cam_rad, 0, height)
	shtloc = (-camloc[0], camloc[1], -camloc[2])
	#euler rotations
	camrot = (cam_d, 0, math.pi/2)
	shtrot = (camrot[1], -camrot[0], math.pi)

	#open the temp file
	bpy.ops.wm.open_mainfile(filepath=temp_name_file)
	scene = bpy.context.scene

	#access model and light
	model = scene.objects[core_name]
	light = scene.objects[0]
	
	#create camera and settings
	cam_data = bpy.data.cameras.new("RndrCamData") # returns bpy.types.Camera(ID)
	cam_data.type = 'ORTHO'
	cam_data.ortho_scale = radius*2
	cam_ob = bpy.data.objects.new(name="RndrCam", object_data=cam_data)
	scene.collection.objects.link(cam_ob)
	scene.camera = cam_ob
	cam_ob.location = camloc
	cam_ob.rotation_euler = camrot
	print("built render cam")
	#render settings
	scene.render.resolution_y = 1040
	scene.render.resolution_x = 1040
	
	#make normal map baking sheet
	sht_data = bpy.data.meshes.new("BakeShtData") #returns bpy.types.BlendDataMeshes
	sht_verts = [(-radius,radius,0),(-radius,-radius,0),(radius,-radius,0),(radius,radius,0)] 
	sht_edges = [[0,1],[1,2],[2,3],[3,0]]
	sht_faces = [(0,1,2,3)]
	sht_data.from_pydata(sht_verts,sht_edges,sht_faces)
	sht_ob = bpy.data.objects.new(name="BakeSht", object_data=sht_data)
	scene.collection.objects.link(sht_ob)
	sht_ob.location = shtloc
	sht_ob.rotation_euler = shtrot
	

	#SHADER RENDER
	
	#prepare shader render settings

	#hide sheet during render
	sht_ob.hide_render = True
	
	#print("moved camera to", camloc, "	with rotation: ", camrot)
	
	#Eevee
	scene.render.engine = 'BLENDER_EEVEE'
	scene.frame_current = cur_cap

	#save as pixels as we go
	rend_names = []
	#loop for ANG and CAP
	while cur_ang < ang:
		while cur_cap < max_cap_anim:
			cur_rend_name = 'render_' + 'ang_' + str(cur_ang) + 'cap_' + str(cur_cap) + '_' + core_name
			print("current name: ", cur_rend_name)
			cur_path = rend_fold_name + '/' + cur_rend_name
			rend_names.append(cur_path + '.png')
			scene.render.filepath = cur_path
			scene.render.image_settings.file_format = 'PNG'
			bpy.ops.render.render(write_still = 1)
			print("rendered image:    ", cur_path)
			cur_cap += int(max_cap_anim / cap)	
			scene.frame_current = cur_cap
		
		cur_ang += 1
		cur_cap = 1
		scene.frame_current = cur_cap
		#move camera
		print("x: ", camloc[0])
		camloc = (
			math.cos((math.pi*2) * (cur_ang/ang)) * cam_rad,
			math.sin((math.pi*2) * (cur_ang/ang)) * cam_rad, 
			camloc[2]
			)	
		print("mov to : ", camloc)
		cam_ob.location = camloc
			
		#rotate camera
		camrot = (
			camrot[0],
			camrot[1],
			math.pi*2 * (cur_ang/ang) + math.pi/2
			)
		cam_ob.rotation_euler = camrot
		print("moved camera to", camloc, "	with rotation: ", camrot)
		
	#reset counters
	cur_ang = 0
	cur_cap = 1
	scene.frame_current = cur_cap
	###############################################################
	#NORMAL RENDER
	#setup for normal mapping
	scene.render.engine = 'CYCLES'
	scene.cycles.bake_type = 'NORMAL'
	#add UVs
	sht_data.uv_layers.new(name='ShtUV')

	#material data
	sht_ob.hide_render = False
	sht_mat = bpy.data.materials.new('shtmat')
	sht_ob.data.materials.append(sht_mat)
	sht_mat.use_nodes = True
	sht_mat.node_tree.nodes.new(type="ShaderNodeTexImage")
 	
	#context override
	print("Current context: ", bpy.context.copy())
	norm_ovr = bpy.context.copy()
	norm_ovr['selected_objects'] = [sht_ob, model]
	norm_ovr['active_object'] = sht_ob
	print("Overridden context: ", norm_ovr)
	bpy.ops.image.new(name='normals')
	norm_img = bpy.data.images['normals']
	norm_img.file_format = 'PNG'
	sht_mat.node_tree.nodes['Image Texture'].image = norm_img
	norm_ovr['edit_image'] = norm_img
	norm_ovr['scene'].frame_set(cur_cap)
	norm_names = []
	#loop for ANG and CAP
	while cur_ang < ang:
		while cur_cap < max_cap_anim:
			cur_rend_name = 'normal_' + 'ang_' + str(cur_ang) + 'cap_' + str(cur_cap) + '_' + core_name + '.png'
			print("current name: ", cur_rend_name)
			cur_path = norm_fold_name + '/' + cur_rend_name
			norm_names.append(cur_path)
			#bake operator
			bpy.ops.object.bake(norm_ovr,
						save_mode='INTERNAL',
						use_selected_to_active=True,
						cage_extrusion=(radius*20),
						type='NORMAL',
						use_clear=True)

			print("baked file:     ", cur_path)

			norm_ovr['edit_image'] = norm_img
			bpy.ops.image.save_as(norm_ovr, filepath=cur_path)
			#bpy.data.images.remove(norm_img)
			cur_cap += int(max_cap_anim / cap)	
			norm_ovr['scene'].frame_set(cur_cap)

			print("current scene: ", scene.frame_current)	

		cur_ang += 1
		cur_cap = 1
		norm_ovr['scene'].frame_set(cur_cap)

		#move sheet
		print("x: ", shtloc[0])
		shtloc = (
			math.cos((math.pi*2) * (cur_ang/ang) + math.pi) * cam_rad,
			math.sin((math.pi*2) * (cur_ang/ang) + math.pi) * cam_rad, 
			shtloc[2]
			)	
		print("mov to : ", shtloc)
		sht_ob.location = shtloc
			
		#rotate sheet
		shtrot = (
			shtrot[0],
			shtrot[1],
			math.pi*2 * (cur_ang/ang) - math.pi
			)
		sht_ob.rotation_euler = shtrot
		print("moved sheet to", shtloc, "	with rotation: ", shtrot)
	
	#loop through folders and build spritesheets
	rend_images = [Image.open(x) for x in rend_names]
	norm_images = [Image.open(x) for x in norm_names]

	total_width = cap*scene.render.resolution_x
	total_height = ang*scene.render.resolution_y

	rend_sprites = Image.new('RGBA', (total_width, total_height))
	norm_sprites = Image.new('RGBA', (total_width, total_height), (128,255,255, 0))
	x_offset = 0
	y_offset = 0
	for im in rend_images:
		if x_offset >= total_width:
			x_offset = 0;
			y_offset += int(total_height/ang)
		rend_sprites.paste(im, (x_offset, y_offset))
		x_offset += int(total_width/cap)
	rend_sprites.save(rend_fold_name +'/render_spritesheet_' + core_name + '.png')
	
	x_offset = 0
	y_offset = 0
	for im in norm_images:
		if x_offset >= total_width:
			y_offset += int(total_height/ang)
			x_offset = 0;
		norm_sprites.paste(im, (x_offset, y_offset))
		x_offset += int(total_height/ang)
	norm_sprites.save(norm_fold_name + '/normal_spritesheet_' + core_name + '.png')
	print("Spritesheets done")	
if __name__ == '__main__':
	main()
