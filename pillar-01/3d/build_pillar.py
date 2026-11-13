"""Build a 1.5 x 6 x 1.5 m steel pillar with a wider cap and base."""

import os
import shutil
import zipfile

import bpy
from mathutils import Vector


OUT = os.path.dirname(os.path.abspath(__file__))
TEXTURES = os.path.join(OUT, 'textures')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def textured_material(name, filename):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (0.17, 0.17, 0.17, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = 0.18
    shader.inputs['Roughness'].default_value = 0.85
    image = bpy.data.images.load(os.path.join(TEXTURES, filename), check_existing=True)
    image.pack()
    image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image
    image_node.extension = 'CLIP'
    material.node_tree.links.new(image_node.outputs['Color'], shader.inputs['Base Color'])
    return material


shaft_material = textured_material('Pillar | 2D shaft', 'pillar_shaft.png')
trim_material = textured_material('Pillar | 2D cap and base', 'pillar_trim.png')

vertices = []
faces = []
sections = []


def add_box(width, depth, z_bottom, z_top, region, material_index):
    start = len(vertices)
    x, y = width / 2.0, depth / 2.0
    vertices.extend([
        (-x, -y, z_bottom), (x, -y, z_bottom),
        (x, -y, z_top), (-x, -y, z_top),
        (-x, y, z_bottom), (x, y, z_bottom),
        (x, y, z_top), (-x, y, z_top),
    ])
    box_faces = [
        (0, 1, 2, 3), (5, 4, 7, 6),
        (4, 0, 3, 7), (1, 5, 6, 2),
        (4, 5, 1, 0), (3, 2, 6, 7),
    ]
    for side_index, face in enumerate(box_faces):
        faces.append(tuple(start + index for index in face))
        sections.append((side_index, region, material_index, width, depth, z_bottom, z_top))


add_box(1.5, 1.5, 0.0, 0.8, 'base', 1)    # full-size lower plinth
add_box(1.25, 1.25, 0.8, 3.125, 'shaft_lower', 0)
add_box(1.25, 1.25, 3.125, 5.45, 'shaft_upper', 0)
add_box(1.5, 1.5, 5.45, 6.0, 'cap', 1)  # projecting upper cap

mesh = bpy.data.meshes.new('Pillar 01 mesh')
mesh.from_pydata(vertices, [], faces)
mesh.materials.append(shaft_material)
mesh.materials.append(trim_material)
mesh.update()
pillar = bpy.data.objects.new('Pillar 01 | 1.5 x 6 x 1.5 m', mesh)
bpy.context.collection.objects.link(pillar)

uv = mesh.uv_layers.new(name='Pillar direct atlas UV')
atlas_regions = {
    'shaft_upper': (16, 16, 240, 432),
    'shaft_lower': (272, 16, 496, 432),
    'cap': (16, 16, 496, 192),
    'base': (16, 224, 496, 480),
}
for polygon, (side_index, region, material_index, width, depth, z_bottom, z_top) in zip(mesh.polygons, sections):
    polygon.material_index = material_index
    left, top, right, bottom = atlas_regions[region]
    for loop_index in polygon.loop_indices:
        vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        if side_index in (0, 1):  # front/back
            horizontal = (vertex.x + width / 2.0) / width
            vertical = (vertex.z - z_bottom) / (z_top - z_bottom)
        elif side_index in (2, 3):  # left/right
            horizontal = (vertex.y + depth / 2.0) / depth
            vertical = (vertex.z - z_bottom) / (z_top - z_bottom)
        else:  # horizontal cap/base surfaces
            horizontal = (vertex.x + width / 2.0) / width
            vertical = (vertex.y + depth / 2.0) / depth
        u = (left + 1 + horizontal * (right - left - 2)) / 512.0
        v = (512 - bottom + 1 + vertical * (bottom - top - 2)) / 512.0
        uv.data[loop_index].uv = (u, v)

pillar['dimensions_m'] = 'Width 1.5 | Height 6 | Depth 1.5'
pillar['source_material'] = '../2d/front.png (pillar-specific texture)'
collection = bpy.data.collections.get('Collection')
if collection:
    collection.name = 'PILLAR 01 | steel'

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world.color = (0.075, 0.075, 0.075)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(8, -11, 8))
camera = bpy.context.object
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 7.7
aim(camera, (0, 0, 3))
scene.camera = camera
for name, location, power, size in (
    ('Key', (3, -7, 10), 1450, 7),
    ('Fill', (-5, -3, 6), 850, 6),
    ('Rim', (3, 5, 8), 1200, 6),
):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.shape = 'DISK'
    light.data.size = size
    aim(light, (0, 0, 3))
scene.render.filepath = os.path.join(OUT, 'preview.png')
bpy.ops.render.render(write_still=True)

# Exports include only the pillar mesh.
for obj in list(bpy.data.objects):
    if obj.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(obj, do_unlink=True)
scene.camera = None
bpy.ops.object.select_all(action='DESELECT')
pillar.select_set(True)
bpy.context.view_layer.objects.active = pillar

bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, 'pillar_01.glb'),
    export_format='GLB',
    export_apply=True,
    use_selection=True,
)

fbx_dir = os.path.join(OUT, 'fbx')
fbx_texture_dir = os.path.join(fbx_dir, 'textures')
os.makedirs(fbx_texture_dir, exist_ok=True)
for filename in ('pillar_shaft.png', 'pillar_trim.png'):
    shutil.copy2(os.path.join(TEXTURES, filename), os.path.join(fbx_texture_dir, filename))

fbx_path = os.path.join(fbx_dir, 'pillar_01.fbx')
bpy.ops.export_scene.fbx(
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
with zipfile.ZipFile(os.path.join(OUT, 'pillar_01_fbx.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.write(fbx_path, 'pillar_01.fbx')
    for filename in ('pillar_shaft.png', 'pillar_trim.png'):
        archive.write(os.path.join(fbx_texture_dir, filename), 'textures/' + filename)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'pillar_01.blend'))
