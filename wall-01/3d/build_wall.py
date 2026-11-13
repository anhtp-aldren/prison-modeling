import bpy
import os
from mathutils import Vector


OUT = os.path.dirname(os.path.abspath(__file__))
TEXTURE = os.path.abspath(os.path.join(OUT, '..', '2d', 'front.png'))

# Clear the default scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


brick = bpy.data.materials.new('Wall | all faces textured')
brick.diffuse_color = (0.28, 0.12, 0.065, 1.0)
brick.use_nodes = True
nodes = brick.node_tree.nodes
links = brick.node_tree.links
shader = nodes.get('Principled BSDF')
image = bpy.data.images.load(TEXTURE, check_existing=True)
image.pack()
image_node = nodes.new('ShaderNodeTexImage')
image_node.image = image
image_node.extension = 'CLIP'
image_node.interpolation = 'Linear'
links.new(image_node.outputs['Color'], shader.inputs['Base Color'])
shader.inputs['Roughness'].default_value = 0.9

# Extrude a stepped side profile. The steel top and bottom project 0.18 m
# beyond the brick on both front and back; total bounds stay 3 x 6 x 1 m.
# (Y, Z) points run around the profile, starting at the front bottom corner.
profile = [
    (-0.5, 0.0), (-0.5, 1.0), (-0.32, 1.0),
    (-0.32, 5.4), (-0.5, 5.4), (-0.5, 6.0),
    (0.5, 6.0), (0.5, 5.4), (0.32, 5.4),
    (0.32, 1.0), (0.5, 1.0), (0.5, 0.0),
]
count = len(profile)
vertices = [(-1.5, y, z) for y, z in profile]
vertices += [(1.5, y, z) for y, z in profile]
faces = []
for index in range(count):
    next_index = (index + 1) % count
    faces.append((index, count + index, count + next_index, next_index))
# Divide the left and right sides at the cap heights so each section gets its
# own UV mapping while the profile remains a single closed wall mesh.
side_sections = [
    (0, 1, 2, 9, 10, 11),  # base
    (2, 3, 8, 9),         # brick
    (3, 4, 5, 6, 7, 8),  # head
]
faces.extend(side_sections)
faces.extend(tuple(count + index for index in reversed(section)) for section in side_sections)
mesh = bpy.data.meshes.new('Wall 01 stepped mesh')
mesh.from_pydata(vertices, [], faces)
mesh.materials.append(brick)
mesh.update()
wall = bpy.data.objects.new('Wall 01 | 3 x 6 x 1 m', mesh)
bpy.context.collection.objects.link(wall)
for polygon in mesh.polygons:
    polygon.material_index = 0

uv_layer = mesh.uv_layers.new(name='Wall all-face UV')


def image_v(z):
    if z <= 1.0:
        return 0.14 * z
    if z <= 5.4:
        return 0.14 + (z - 1.0) / 4.4 * 0.78
    return 0.92 + (z - 5.4) / 0.6 * 0.08


for polygon in mesh.polygons:
    for loop_index in polygon.loop_indices:
        vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        if polygon.index >= count:
            # One metre of side depth uses one metre's worth of brick pixels.
            u = 0.5 + vertex.y / 9.0
            v = image_v(vertex.z)
        elif polygon.index in (0, 2, 4, 6, 8, 10):
            # Front and back use the same centered portrait crop.
            u = 1.0 / 3.0 + (vertex.x + 1.5) / 9.0
            v = image_v(vertex.z)
        else:
            # Textured steel on the top, bottom, and small cap ledges.
            u = 1.0 / 3.0 + (vertex.x + 1.5) / 9.0
            v = (0.93 + (vertex.y + 0.5) * 0.06) if vertex.z > 3.0 else (0.02 + (vertex.y + 0.5) * 0.10)
        uv_layer.data[loop_index].uv = (u, v)
wall['dimensions_m'] = 'Width 3 | Height 6 | Thickness 1'
wall['front_face'] = '-Y'
wall['source_texture'] = os.path.relpath(TEXTURE, OUT)

collection = bpy.data.collections.get('Collection')
if collection:
    collection.name = 'WALL 01 | 3 x 6 x 1 m'

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.world.color = (0.075, 0.075, 0.075)
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(8, -12, 8))
camera = bpy.context.object
camera.name = 'Preview Camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 8.2
aim(camera, (0, 0, 3))
scene.camera = camera

for name, location, power, size in (
    ('Key', (2, -7, 10), 1500, 7),
    ('Fill', (-6, -3, 5), 900, 6),
    ('Rim', (3, 5, 8), 1200, 5),
    ('Back', (-2, 7, 9), 1500, 7),
):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name + ' softbox'
    light.data.energy = power
    light.data.shape = 'DISK'
    light.data.size = size
    aim(light, (0, 0, 3))

scene.render.filepath = os.path.join(OUT, 'preview.png')
bpy.ops.render.render(write_still=True)

camera.location = (0, -12, 3)
aim(camera, (0, 0, 3))
camera.data.ortho_scale = 7.0
scene.render.filepath = os.path.join(OUT, 'preview_front.png')
bpy.ops.render.render(write_still=True)

camera.location = (8, 12, 8)
aim(camera, (0, 0, 3))
camera.data.ortho_scale = 8.2
scene.render.filepath = os.path.join(OUT, 'preview_back.png')
bpy.ops.render.render(write_still=True)

camera.location = (12, 0, 7)
aim(camera, (0, 0, 3))
camera.data.ortho_scale = 8.2
scene.render.filepath = os.path.join(OUT, 'preview_side.png')
bpy.ops.render.render(write_still=True)

# Export the textured model, then remove preview-only objects from the editable
# Blender scene so the .blend opens with just the wall mesh.
result = bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, 'wall_01.glb'),
    export_format='GLB',
    export_apply=True,
)
if 'FINISHED' not in result:
    raise RuntimeError('GLB export failed')

for obj in list(bpy.data.objects):
    if obj.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(obj, do_unlink=True)
scene.camera = None
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
wall.select_set(True)
bpy.context.view_layer.objects.active = wall
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'wall_01.blend'))
