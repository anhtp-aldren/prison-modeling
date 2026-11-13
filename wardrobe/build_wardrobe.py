"""Build a stylized, editable wardrobe from wardrobe-views.png (Blender 5.x)."""

import math
import os
import random
import sys

import bpy
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
CLOSED = '--closed' in sys.argv
OUT = os.path.join(ROOT, 'closed') if CLOSED else ROOT
os.makedirs(OUT, exist_ok=True)
random.seed(19)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

asset = bpy.data.collections.new('Wardrobe | model')
bpy.context.scene.collection.children.link(asset)


def move_to_asset(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    asset.objects.link(obj)
    return obj


def plain(name, color, metallic=0, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def weathered(name, paint, rust, threshold=.65):
    mat = plain(name, paint, .57, .69)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = 8.5
    tex.inputs['Detail'].default_value = 5
    tex.inputs['Roughness'].default_value = .72
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = threshold - .045
    ramp.color_ramp.elements[0].color = (*paint, 1)
    ramp.color_ramp.elements[1].position = threshold + .07
    ramp.color_ramp.elements[1].color = (*rust, 1)
    links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .09
    bump.inputs['Distance'].default_value = .017
    links.new(tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def fabric(name, color):
    mat = plain(name, color, 0, .98)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 42
    noise.inputs['Detail'].default_value = 3
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .23
    ramp.color_ramp.elements[0].color = (*(v*.82 for v in color), 1)
    ramp.color_ramp.elements[1].position = .77
    ramp.color_ramp.elements[1].color = (*(v*1.08 for v in color), 1)
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .075
    bump.inputs['Distance'].default_value = .002
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


if CLOSED:
    blue = weathered('01 | Dark steel panels', (.052, .062, .066), (.12, .13, .13), .68)
    blue_dark = plain('02 | Dark inset steel', (.035, .042, .044), .62, .72)
    steel = weathered('03 | Worn steel edging', (.11, .125, .128), (.18, .19, .19), .73)
    rust = plain('05 | Steel seam', (.082, .093, .098), .65, .72)
else:
    blue = weathered('01 | Scuffed dark steel panels', (.052, .066, .071), (.12, .135, .14), .66)
    blue_dark = weathered('02 | Dark cabinet interior', (.027, .034, .036), (.075, .08, .08), .73)
    steel = weathered('03 | Worn steel edging', (.115, .13, .13), (.18, .19, .19), .72)
    rust = plain('05 | Steel seam', (.075, .085, .088), .65, .72)
recess = plain('06 | Shadowed seams', (.041, .052, .054), .36, .84)
black = plain('07 | Dark iron', (.074, .074, .068), .78, .53)
cloth_gray = fabric('08 | Gray prison uniform fabric', (.13, .14, .14))
cloth_brown = fabric('09 | Faded orange prison uniform fabric', (.31, .115, .036))
cloth_blue = plain('10 | Folded indigo fabric', (.125, .15, .23), .0, .96)
paper = plain('11 | Aged paper', (.38, .32, .215), .0, .94)
ink = plain('12 | Faded newsprint', (.07, .064, .05), .0, 1)
fabric_trim = plain('13 | Uniform seams and patches', (.046, .05, .05), .0, .97)


def bevel(obj, width=.004, segments=2):
    if width:
        mod = obj.modifiers.new('Rounded pressed-metal edge', 'BEVEL')
        mod.width = width
        mod.segments = segments
        obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, xyz, dims, material, edge=.003, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = move_to_asset(bpy.context.object)
    obj.name = name
    if parent:
        obj.parent = parent
    obj.location = xyz
    obj.dimensions = dims
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return bevel(obj, edge)


def cylinder(name, xyz, radius, depth, material, parent=None, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = move_to_asset(bpy.context.object)
    obj.name = name
    if parent:
        obj.parent = parent
    obj.location = xyz
    obj.data.materials.append(material)
    return bevel(obj, .0015, 2)


def tube(name, points, radius, material, parent=None):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for target, coord in zip(spline.points, points):
        target.co = (*coord, 1)
    obj = bpy.data.objects.new(name, curve)
    asset.objects.link(obj)
    if parent:
        obj.parent = parent
    obj.data.materials.append(material)
    return obj


def rivet(name, xyz, axis='Y', parent=None, radius=.007):
    obj = cylinder(name, xyz, radius, .004, steel, parent=parent, vertices=12)
    if axis == 'Y':
        obj.rotation_euler.x = math.pi/2
    elif axis == 'X':
        obj.rotation_euler.y = math.pi/2
    return obj


# Body: the opening is physically empty, so the shelf and hanging clothing show through.
box('Back panel', (0, .269, .93), (.85, .031, 1.52), blue, .01)
for side in (-1, 1):
    box(f'Cabinet side {side:+}', (side*.438, 0, .93), (.034, .545, 1.56), blue, .012)
    box(f'Front vertical rolled edge {side:+}', (side*.441, -.286, .93), (.045, .032, 1.56), steel, .008)
    box(f'Back vertical rolled edge {side:+}', (side*.441, .285, .93), (.045, .025, 1.56), steel, .008)
box('Top lid', (0, 0, 1.723), (.91, .59, .047), blue, .019)
box('Top lid inset', (0, 0, 1.749), (.82, .50, .005), blue_dark, .006)
box('Bottom floor', (0, 0, .145), (.91, .57, .043), blue_dark, .007)
box('Bottom front threshold', (0, -.284, .156), (.86, .035, .036), steel, .004)
box('Top front lintel', (0, -.286, 1.687), (.86, .033, .058), steel, .004)
if CLOSED:
    box('Solid front backing', (0, -.267, .93), (.85, .026, 1.52), blue_dark, .005)
else:
    box('Upper shelf', (0, -.01, 1.338), (.82, .51, .032), blue_dark, .003)
    box('Shelf front lip', (0, -.279, 1.322), (.82, .015, .033), steel, .003)

for x in (-.376, .376):
    for y in (-.224, .224):
        foot = box('Tapered steel foot', (x, y, .058), (.078, .083, .116), blue_dark, .012)
        box('Foot seam', (x, y-.043, .1), (.07, .002, .006), rust, 0)

# Riveted back face and side lift handles.
for x in (-.39, -.195, 0, .195, .39):
    for z in (.198, 1.67):
        rivet('Back rim fastener', (x, .287, z))
for z in (.25, .56, .87, 1.18, 1.5):
    for x in (-.39, .39):
        rivet('Back side fastener', (x, .287, z))
for s in (-1, 1):
    x = s*.475
    box('Side reinforcement plate', (s*.461, .0, .815), (.008, .28, .32), black, .003)
    for y in (-.12, .12):
        for z in (.68, .95):
            rivet('Plate fixing', (s*.468, y, z), axis='X')
    tube('Fold-down side lift handle', [(x, -.13, 1.465), (x+s*.05, -.13, 1.465),
         (x+s*.05, -.13, 1.26), (x+s*.05, .13, 1.26),
         (x+s*.05, .13, 1.465), (x, .13, 1.465)], .008, black)
    for y in (-.13, .13):
        cylinder('Handle pivot pin', (x, y, 1.465), .015, .018, steel)

# Rail and hanging inmate uniforms.
if not CLOSED:
    tube('Clothes rail', [(-.37, .01, 1.235), (.37, .01, 1.235)], .012, steel)


def uniform(label, x, color, y, number):
    ztop = 1.195
    zbot = .655
    verts2d = [(-.126, ztop-.13), (-.077, ztop-.035), (-.03, ztop),
               (.03, ztop), (.077, ztop-.035), (.126, ztop-.13),
               (.089, zbot), (-.091, zbot)]
    verts = [(x+vx, y+vy, vz) for vy in (-.043, .043) for vx, vz in verts2d]
    n = len(verts2d)
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, n*2))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    mesh = bpy.data.meshes.new(label)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(label, mesh)
    asset.objects.link(obj)
    obj.data.materials.append(color)
    bevel(obj, .015, 3)
    for s in (-1, 1):
        sleeve = box(label+' long sleeve', (x+s*.133, y, .889), (.072, .09, .44), color, .024)
        sleeve.rotation_euler.y = s*.065
        box(label+' wrist cuff', (x+s*.143, y-.004, .677), (.076, .095, .027), color, .008)
        box(label+' trouser leg', (x+s*.052, y, .425), (.081, .086, .46), color, .012)
        box(label+' trouser hem', (x+s*.052, y-.002, .197), (.083, .09, .022), color, .005)
        box(label+' side seam', (x+s*.087, y-.048, .428), (.004, .003, .43), fabric_trim, .001)
        box(label+' trouser crease', (x+s*.052, y-.045, .43), (.003, .002, .36), fabric_trim, .001)
        box(label+' sleeve crease', (x+s*.133, y-.048, .88), (.003, .002, .26), fabric_trim, .001)
    box(label+' open collar', (x, y-.046, ztop-.037), (.12, .02, .057), fabric_trim, .009)
    box(label+' front zipper', (x, y-.047, .916), (.006, .005, .43), fabric_trim, .001)
    box(label+' waist seam', (x, y-.05, .662), (.18, .006, .011), fabric_trim, .002)
    box(label+' left chest pocket', (x-.061, y-.05, 1.015), (.072, .006, .067), color, .004)
    box(label+' inmate number patch', (x+.058, y-.052, 1.018), (.077, .006, .043), paper, .002)
    text_data = bpy.data.curves.new(label+' printed inmate number', 'FONT')
    text_data.body = number
    text_data.size = .019
    text_data.extrude = .0001
    text_obj = bpy.data.objects.new(label+' printed inmate number', text_data)
    asset.objects.link(text_obj)
    text_obj.location = (x+.027, y-.057, 1.009)
    text_obj.rotation_euler.x = math.pi/2
    text_data.materials.append(ink)
    tube(label+' hanger', [(x-.08,y,ztop-.025), (x,y,ztop+.015),
         (x+.08,y,ztop-.025)], .004, black)
    tube(label+' hanger hook', [(x,y,ztop+.015), (x,y,ztop+.07),
         (x+.018,y,ztop+.09)], .003, black)


if not CLOSED:
    uniform('Gray prison jumpsuit', -.135, cloth_gray, -.055, '041')
    uniform('Orange prison jumpsuit', .14, cloth_brown, .025, '106')

# Folded bedding on top shelf.
if not CLOSED:
    for i, (x, y, z, dims) in enumerate([(-.075, -.01, 1.393, (.38, .34, .095)),
                                       (.015, .02, 1.473, (.34, .28, .082))]):
        box('Folded indigo blanket '+str(i+1), (x, y, z), dims, cloth_blue, .036)
        tube('Blanket folded piping', [(x-.15,y-.13,z), (x-.18,y,z), (x-.15,y+.13,z)], .004, cloth_gray)

# Door assemblies rotate about their hinges and remain editable as grouped objects.
def door(name, hinge_x, angle, direction, inside):
    pivot = bpy.data.objects.new(name+' | hinge pivot', None)
    asset.objects.link(pivot)
    pivot.location = (hinge_x, -.307, 0)
    pivot.rotation_euler.z = math.radians(angle)
    w = .442 if CLOSED else .414
    cx = direction*w/2
    box(name+' outer pressed sheet', (cx, -.02, .914), (w, .032, 1.465), blue, .009, pivot)
    box(name+' inner enamel sheet', (cx, .000, .915), (w-.035, .004, 1.42), inside, .003, pivot)
    if name == 'Left door':
        box('Left door blue inner stamping', (cx, .005, .91), (w-.095, .003, 1.34), blue, .003, pivot)
        for z in (1.34, 1.40, 1.46, 1.52, .29, .35, .41, .47):
            box('Left door inner vent recess', (cx, .009, z), (.27, .003, .02), recess, .001, pivot)
            box('Left door inner louver', (cx, .016, z+.002), (.265, .010, .012), steel, .002, pivot)
    for local_x in (direction*.012, direction*(w-.012)):
        box(name+' edge stile', (local_x, -.043, .915), (.022, .017, 1.466), steel, .003, pivot)
    for z in (.188, 1.644):
        box(name+' edge rail', (cx, -.043, z), (w-.018, .017, .025), steel, .003, pivot)
    # Raised rectangular stamping with its darker recess.
    box(name+' inset panel', (cx, -.040, .925), (.302, .006, .54), blue_dark, .004, pivot)
    for xx in (cx-.16, cx+.16):
        box(name+' panel vertical molding', (xx, -.056, .925), (.012, .015, .56), steel, .004, pivot)
    for zz in (.645, 1.205):
        box(name+' panel horizontal molding', (cx, -.056, zz), (.33, .015, .013), steel, .004, pivot)
    # Upper and lower vent louvers project slightly from the door.
    for z in (1.33, 1.39, 1.45, 1.51, 1.57, .24, .30, .36, .42, .48):
        slot = box(name+' vent shadow', (cx, -.040, z), (.295, .006, .023), recess, .001, pivot)
        blade = box(name+' louver', (cx, -.056, z+.003), (.29, .014, .012), steel, .002, pivot)
        blade.rotation_euler.x = math.radians(-17)
    # A pair of old notices on the inner face of the left door.
    if name == 'Left door':
        for z, width in ((.91, .115), (1.12, .095)):
            box('Yellowed notice on left door', (cx+.025, .022, z), (width, .002, .17), paper, .001, pivot)
    # Door knob, latch mount and hinge barrels.
    knob_x = direction*(w-.065)
    cylinder(name+' latch escutcheon', (knob_x, -.064, .845), .034, .008, steel, pivot).rotation_euler.x = math.pi/2
    cylinder(name+' round knob', (knob_x, -.084, .845), .020, .028, steel, pivot).rotation_euler.x = math.pi/2
    for z in (.26, .85, 1.52):
        cylinder(name+' hinge barrel', (0, 0, z), .018, .080, black, pivot)
        box(name+' hinge strap', (direction*.045, -.014, z), (.09, .012, .028), steel, .003, pivot)
    return pivot


door('Left door', -.449, 0 if CLOSED else -104, 1, blue_dark)
door('Right door', .449, 0 if CLOSED else 48, -1, blue_dark)

# Keep the previously made closed variant reproducible; the open version has a clear top.
if CLOSED:
    book = box('Black notebook', (.045, .005, 1.787), (.32, .205, .018), black, .003)
    book.rotation_euler.z = math.radians(-17)
    paper_stack = box('Stacked old newspapers', (.08, -.015, 1.811), (.305, .195, .023), paper, .002)
    paper_stack.rotation_euler.z = math.radians(13)
    for i in range(3):
        strip = box('Newspaper ink line', (.015+i*.075, -.044, 1.824), (.05, .12, .0008), ink, 0)
        strip.rotation_euler.z = math.radians(13)
    box('Newspaper masthead', (.045, .047, 1.825), (.23, .025, .0008), ink, 0).rotation_euler.z = math.radians(13)

# Studio backdrop and light rig are outside the asset collection.
ground = plain('Studio ground', (.76, .75, .71), 0, .9)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.01))
floor = bpy.context.object
floor.name = 'Studio floor (render only)'
floor.data.materials.append(ground)

world = bpy.context.scene.world
world.color = (.3, .3, .3)
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.72, .77, .82, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .55


def light(name, location, power, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    direction = Vector((0, 0, .95)) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


light('Large softbox left', (-2.5, -3.5, 4), 480, 3.0)
light('Softbox right', (2.4, -1.8, 2.8), 230, 2.3)
light('Rear edge light', (0, 2.3, 3.1), 390, 2.1)

camera_data = bpy.data.cameras.new('Render camera')
camera = bpy.data.objects.new('Render camera', camera_data)
bpy.context.scene.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera_data.type = 'ORTHO'


def aim_camera(location, target, scale):
    camera.location = location
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.ortho_scale = scale


scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 28
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.render.film_transparent = False

views = [
    ('preview.png', (2.8, -4.2, 2.5), (0, 0, .94), 2.58),
    ('preview_front.png', (0, -5, 1.08), (0, -.02, .94), 2.28),
    ('preview_back.png', (0, 5, 1.09), (0, 0, .94), 2.22),
    ('preview_side.png', (5, 0, 1.1), (0, 0, .94), 2.32),
    ('preview_top.png', (0, -.12, 5), (0, -.12, .93), 2.18),
]

for filename, position, target, scale in views:
    aim_camera(position, target, scale)
    scene.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)

aim_camera((2.8, -4.2, 2.5), (0, 0, .94), 2.58)
scene.render.filepath = '//preview.png'
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.shading.type = 'MATERIAL'
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'wardrobe_closed.blend' if CLOSED else 'wardrobe.blend'))
print('Saved wardrobe model and five preview renders to', OUT)
