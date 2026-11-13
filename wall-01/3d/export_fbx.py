"""Export the saved Wall 01 Blender model as a portable FBX package."""

import os
import shutil
import zipfile

import bpy


root = os.path.dirname(os.path.abspath(__file__))
source_texture = os.path.abspath(os.path.join(root, '..', '2d', 'front.png'))
package_dir = os.path.join(root, 'fbx')
texture_dir = os.path.join(package_dir, 'textures')
os.makedirs(texture_dir, exist_ok=True)

texture_copy = os.path.join(texture_dir, 'front.png')
shutil.copy2(source_texture, texture_copy)

wall = bpy.data.objects['Wall 01 | 3 x 6 x 1 m']
image = bpy.data.images['front.png']
image.filepath = texture_copy

bpy.ops.object.select_all(action='DESELECT')
wall.select_set(True)
bpy.context.view_layer.objects.active = wall

fbx_path = os.path.join(package_dir, 'wall_01.fbx')
result = bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    object_types={'MESH'},
    path_mode='COPY',
    embed_textures=True,
    apply_unit_scale=True,
    global_scale=1.0,
    axis_forward='-Z',
    axis_up='Y',
)
if 'FINISHED' not in result:
    raise RuntimeError('FBX export failed')

zip_path = os.path.join(root, 'wall_01_fbx.zip')
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(fbx_path, 'wall_01.fbx')
    archive.write(texture_copy, 'textures/front.png')

# Mobile package: half-size image in each direction. The existing UVs use the
# same image aspect ratio, so no mesh or UV changes are needed. JPEG is widely
# supported by FBX importers and keeps the texture payload small.
mobile_dir = os.path.join(root, 'fbx_mobile')
mobile_texture_dir = os.path.join(mobile_dir, 'textures')
os.makedirs(mobile_texture_dir, exist_ok=True)
mobile_texture_path = os.path.join(mobile_texture_dir, 'front_mobile.jpg')

scaled_image = bpy.data.images.load(source_texture, check_existing=False)
scaled_image.scale(768, 512)
bpy.context.scene.render.image_settings.file_format = 'JPEG'
bpy.context.scene.render.image_settings.quality = 82
scaled_image.save_render(mobile_texture_path, scene=bpy.context.scene)

mobile_image = bpy.data.images.load(mobile_texture_path, check_existing=False)
for material in wall.data.materials:
    if material and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image == image:
                node.image = mobile_image

mobile_fbx_path = os.path.join(mobile_dir, 'wall_01_mobile.fbx')
result = bpy.ops.export_scene.fbx(
    filepath=mobile_fbx_path,
    use_selection=True,
    object_types={'MESH'},
    path_mode='COPY',
    embed_textures=True,
    apply_unit_scale=True,
    global_scale=1.0,
    axis_forward='-Z',
    axis_up='Y',
)
if 'FINISHED' not in result:
    raise RuntimeError('Mobile FBX export failed')

mobile_zip_path = os.path.join(root, 'wall_01_mobile_fbx.zip')
with zipfile.ZipFile(mobile_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(mobile_fbx_path, 'wall_01_mobile.fbx')
    archive.write(mobile_texture_path, 'textures/front_mobile.jpg')

print('FBX:', fbx_path)
print('TEXTURE:', texture_copy)
print('PACKAGE:', zip_path)
print('MOBILE FBX:', mobile_fbx_path)
print('MOBILE TEXTURE:', mobile_texture_path)
print('MOBILE PACKAGE:', mobile_zip_path)
