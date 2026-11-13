import bpy
import math
import os
import tempfile
from mathutils import Vector

LOWPOLY = os.environ.get('MAIN_GATE_LOWPOLY') == '1'
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
out = os.path.normpath(os.path.join(SOURCE_DIR, '..', 'lowpoly')) if LOWPOLY else SOURCE_DIR
os.makedirs(out, exist_ok=True)
asset_name = 'main_gate_lowpoly' if LOWPOLY else 'main_gate'

# Procedural, editable prop scene. Dimensions in meters; front faces -Y.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
CURRENT_PART = 'Main Frame'

def tag(obj):
    obj['gate_part'] = CURRENT_PART
    if CURRENT_PART == 'Main Frame' and obj.type == 'MESH' and obj.data.materials:
        if obj.data.materials[0] in (steel, edge):
            obj.data.materials[0] = wall_trim
    return obj

def mat(name, color, metallic=0.0, roughness=0.5, emission=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[0], 1)
        p.inputs['Emission Strength'].default_value = emission[1]
    return m

steel = mat('01 | Oxidized gunmetal', (0.105,0.105,0.10), .78, .34)
edge = mat('02 | Worn steel edges', (.22,.205,.18), .82, .28)
dark = mat('03 | Recesses and shadow', (.018,.022,.023), .25, .72)
wood = mat('04 | Dark charcoal door plates', (.055,.06,.058), .35, .56)
rust = mat('05 | Oxide highlights', (.24,.105,.035), .35, .64)
yellow = mat('06 | Hazard ochre', (.83,.43,.045), .28, .48)
glass = mat('07 | Warm lamp glass', (1.0,.70,.34), .12, .22, ((1.0,.48,.16), 2.4))
wall_trim = mat('08 | Wall top/bottom trim', (.24,.22,.20), .25, .80)

# UV image maps survive the GLB export. Keep the source PNGs beside the blend.
texture_dir=os.path.join(out,'textures')
def add_texture_maps(material, style):
    nodes=material.node_tree.nodes; links=material.node_tree.links
    principled=nodes.get('Principled BSDF')
    def image_node(suffix, non_color=False):
        node=nodes.new('ShaderNodeTexImage')
        node.label=f'{style} {suffix}'
        node.image=bpy.data.images.load(os.path.join(texture_dir,f'{style}_{suffix}.png'),check_existing=True)
        node.extension='REPEAT'
        if non_color: node.image.colorspace_settings.name='Non-Color'
        return node
    base=image_node('basecolor'); links.new(base.outputs['Color'],principled.inputs['Base Color'])
    if LOWPOLY:
        metal,rough={'steel':(.78,.69),'edge':(.82,.68),'door':(.36,.72),'panel':(0,.80),'yellow':(.27,.70),'wall_trim':(.25,.80)}[style]
        principled.inputs['Metallic'].default_value=metal
        principled.inputs['Roughness'].default_value=rough
    else:
        orm=image_node('orm',True)
        channels=nodes.new('ShaderNodeSeparateColor'); channels.mode='RGB'
        links.new(orm.outputs['Color'],channels.inputs['Color'])
        links.new(channels.outputs['Green'],principled.inputs['Roughness'])
        links.new(channels.outputs['Blue'],principled.inputs['Metallic'])
        normal_tex=image_node('normal',True)
        normal=nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value={'steel':.08,'edge':.07,'door':.06,'panel':.02,'yellow':.07,'wall_trim':.015}[style]
        links.new(normal_tex.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],principled.inputs['Normal'])
    if style=='panel' and principled.inputs.get('Specular IOR Level'):
        principled.inputs['Specular IOR Level'].default_value=.30

for material,style in ((steel,'steel'),(edge,'edge'),(wood,'door'),(dark,'panel'),(yellow,'yellow'),(wall_trim,'wall_trim')):
    add_texture_maps(material,style)

def bevel(obj, amount=.04, seg=2):
    if LOWPOLY:
        major_parts=('Lower pillar body','Lower pillar bottom cap','Lower pillar top cap',
                     'Massive head beam','Upper board backing','Upper panel frame rail',
                     'Upper panel jamb','Door leaf |','Door perimeter stile',
                     'Door perimeter crossbar','Door opening jamb','Door opening head',
                     'Door threshold')
        if not obj.name.startswith(major_parts): return obj
        amount*=.55
        seg=1
    if amount:
        mod=obj.modifiers.new('Soft battered edges','BEVEL'); mod.width=amount; mod.segments=seg
        mod2=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return obj

def box(name, loc, scale, material, bev=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material); return tag(bevel(o,bev))

def sphere(name, loc, radius, material, scale=None):
    if LOWPOLY and any(word in name.lower() for word in ('rivet','pin','screw','bolt')):
        return None
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8 if LOWPOLY else 12, ring_count=4 if LOWPOLY else 8, radius=radius, location=loc)
    o=bpy.context.object; o.name=name
    if scale: o.scale=scale
    o.data.materials.append(material); bpy.ops.object.shade_smooth(); return tag(o)

def cyl(name, loc, radius, depth, material, axis='Y', vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=min(vertices,6) if LOWPOLY else vertices, radius=radius, depth=depth, location=loc)
    o=bpy.context.object; o.name=name
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    elif axis=='X': o.rotation_euler[1]=math.pi/2
    o.data.materials.append(material); return tag(bevel(o,.018,2))

def rod(name, a, b, radius, material, vertices=12):
    mid=(Vector(a)+Vector(b))/2; delta=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=min(vertices,6) if LOWPOLY else vertices, radius=radius, depth=delta.length, location=mid)
    o=bpy.context.object; o.name=name; o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    o.data.materials.append(material); return tag(bevel(o,.015,2))

W=9.0; H=9.2; YF=-1.15; YB=1.15
# Structural opening around the moving lower leaves.
for x in (-3.78,3.78):
    box('Door opening jamb',(x,0,2.83),(.36,2.4,5.62),steel,.055)
box('Door opening head',(0,0,5.50),(8.15,2.4,.37),steel,.05)
box('Door threshold',(0,0,.11),(8.15,2.4,.21),steel,.04)
for x in (-4.18,4.18):
    # The jamb body ends at the door top. Its top and bottom caps are wider.
    box('Lower pillar body',(x,0,2.73),(.95,2.55,5.45),edge,.07)
    box('Lower pillar bottom cap',(x,0,.55),(1.32,3.25,1.08),edge,.07)
    box('Lower pillar top cap',(x,0,5.22),(1.32,3.25,.72),edge,.07)
# Board, narrow reveal, and the junction rail resting on the lower pillars.
box('Upper board backing',(0,0,7.36),(9.58,2.38,3.02),edge,.065)
box('Board-to-door recessed reveal',(0,0,5.71),(9.58,2.20,.22),dark,.025)
box('Door-to-board junction beam',(0,0,5.52),(8.20,2.50,.40),steel,.045)
box('Massive head beam',(0,0,8.52),(9.58,2.5,.72),edge,.08)
box('Header front rail',(0,YF-.12,5.52),(8.05,.30,.40),edge,.045)
box('Header rear rail',(0,YB+.12,5.52),(8.05,.30,.40),edge,.045)

# Upper dark armored viewing/sign panel, framed on both faces.
box('Upper panel solid core',(0,0,7.0),(8.45,2.5,2.02),dark,.08)
for face in (-1,1):
    y=face*1.33; outside=face*1.47
    box('Upper inset black panel',(0,y,7.0),(8.45,.12,2.0),dark,.12)
    # continuous frame made from rails and posts
    for x in (-4.25,4.25): box('Upper panel jamb',(x,outside,7.0),(.22,.24,2.45),edge,.04)
    for z in (5.82,8.18): box('Upper panel frame rail',(0,outside,z),(8.65,.24,.22),edge,.04)

# Paired lower doors with inset faces, frames, plank seams and X-braces.
for side in (-1,1):
    CURRENT_PART='Left Leaf' if side<0 else 'Right Leaf'
    box('Solid door core',(side*1.72,0,2.82),(3.42,2.25,5.3),wood,.045)
for face in (-1,1):
    y=face*1.22; fy=face*1.36
    for side in (-1,1):
        CURRENT_PART='Left Leaf' if side<0 else 'Right Leaf'
        cx=side*1.72
        box('Door leaf | left' if side<0 else 'Door leaf | right',(cx,y,2.82),(3.42,.22,5.3),wood,.055)
        # perimeter stiles and rails
        for dx in (-1.58,1.58): box('Door perimeter stile',(cx+dx,fy,2.82),(.16,.18,5.12),edge,.025)
        for z in (.33,5.30): box('Door perimeter crossbar',(cx,fy,z),(3.28,.18,.16),edge,.025)
        # narrow recessed vertical board seams
        for dx in (-1.25,-.82,-.39,.04,.47,.90,1.33):
            box('Vertical plank seam',(cx+dx,face*1.345,2.82),(.025,.035,4.72),dark,.006)
        # The two leaves together form one full X.
        if side<0:
            rod('Upper-left to center brace',(-3.14,fy,5.18),(-.08,fy,2.83),.105,steel)
            rod('Lower-left to center brace',(-3.14,fy,.48),(-.08,fy,2.83),.105,steel)
        else:
            rod('Center to lower-right brace',(.08,fy,2.83),(3.14,fy,.48),.105,steel)
            rod('Center to upper-right brace',(.08,fy,2.83),(3.14,fy,5.18),.105,steel)
        box('Door waist reinforcement',(cx,face*1.46,2.72),(3.22,.18,.23),edge,.035)
        # Safety stripe panels, alternating ochre and dark steel slashes.
        box('Hazard stripe backing',(cx,face*1.39,.72),(2.88,.035,.42),yellow,.015)
        for i in range(7):
            xx=cx-1.34+i*.43
            # narrow diagonal dark cuts; slight rotation gives painted industrial stripe rhythm
            q=box('Hazard stripe | black slash',(xx,face*1.42,.72),(.19,.035,.46),dark,.005)
            q.rotation_euler[1]=math.radians(27)
        # A vertical grab handle at each leaf's inner edge, accessible on both faces.
        hx=-.30 if side<0 else .30
        box('Handle mounting plate',(hx,face*1.56,2.83),(.19,.11,1.10),steel,.025)
        for hz in (2.46,3.20):
            rod('Handle stand-off',(hx,face*1.62,hz),(hx,face*1.88,hz),.055,edge)
            sphere('Handle plate bolt',(hx,face*1.64,hz),.045,edge,(1,.45,1))
        rod('Vertical door grab handle',(hx,face*1.88,2.39),(hx,face*1.88,3.27),.075,edge)
CURRENT_PART='Main Frame'

# Rivet lines on face and back, distributed across armor, frame, and doors.
for face in (-1,1):
    y=face*1.51
    for x in [(-4.15+i*.46) for i in range(19)]:
        sphere('Domed perimeter rivet',(x,face*1.33,8.52),.075,edge,(1,.42,1))
        sphere('Door frame rivet',(x,face*1.48,5.53),.065,edge,(1,.42,1))
    for x in (-4.18,4.18):
        for dx in (-.33,.33):
            for z in (1.35,2.15,3.0,4.0,4.75):
                sphere('Pillar body rivet',(x+dx,face*1.31,z),.068,edge,(1,.42,1))
            for z in (.28,.86,5.05,5.42):
                sphere('Pillar cap rivet',(x+dx,face*1.66,z),.074,edge,(1,.42,1))
    for cx in (-1.72,1.72):
        CURRENT_PART='Left Leaf' if cx<0 else 'Right Leaf'
        for dx in (-1.47,-.9,0,.9,1.47):
            for z in (.42,1.2,2.72,4.45,5.2):
                sphere('Door fastening rivet',(cx+dx,y,z),.052,edge,(1,.4,1))
    CURRENT_PART='Main Frame'

# Chunky strap hinges along outer door edges, with barrels and knuckles.
for face in (-1,1):
    fy=face*1.57
    for x in (-3.48,3.48):
        CURRENT_PART='Left Leaf' if x<0 else 'Right Leaf'
        for z in (1.0,2.95,4.75):
            box('Hinge leaf',(x,fy,z),(.26,.12,.92),steel,.035)
            cyl('Hinge barrel',(x,face*1.72,z),.125,.72,edge,'Z')
            for dz in (-.25,.25): cyl('Hinge knuckle ring',(x,face*1.72,z+dz),.145,.045,steel,'Z')
            for dz in (-.32,.32): sphere('Hinge pin',(x,face*1.8,z+dz),.052,edge)
CURRENT_PART='Main Frame'

# Warm work lamps over the header on both faces; omitted from the low-poly build.
for face in ((-1,1) if not LOWPOLY else ()):
    f=face
    for x in (-2.35,2.35):
        box('Header lamp mounting plate',(x,f*1.36,8.98),(1.35,.20,.22),steel,.06)
        box('Header lamp housing',(x,f*1.52,9.20),(1.05,.30,.36),edge,.075)
        box('Header luminous diffuser',(x,f*1.69,9.18),(.78,.07,.20),glass,.035)
        for xx in (-.34,-.17,0,.17,.34): rod('Lamp cage grille',(x+xx,f*1.74,9.08),(x+xx,f*1.74,9.28),.018,steel,8)
        for xx in (-.46,.46): sphere('Lamp housing screw',(x+xx,f*1.68,9.20),.04,edge,(1,.4,1))

# Bake the detailed components, set the depth from the side view, and
# join them into exactly three independent mesh objects.
parts={name:[] for name in ('Main Frame','Left Leaf','Right Leaf')}
for obj in list(bpy.data.objects):
    if obj.type!='MESH': continue
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    for mod in list(obj.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
    matrix=obj.matrix_world.copy()
    for vertex in obj.data.vertices:
        point=matrix @ vertex.co
        vertex.co=(point.x,point.y*.46,point.z*1.18)
    obj.matrix_world.identity()
    parts[obj['gate_part']].append(obj)

for name,objects in parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    joined=bpy.context.object; joined.name=name
    bpy.context.scene.cursor.location=((-3.48 if name=='Left Leaf' else 3.48) if name!='Main Frame' else 0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    joined.color=(.2,.2,.2,1)

root=bpy.data.collections.get('Collection')
if root: root.name='MAIN GATE | 3 meshes'
if LOWPOLY:
    counts={o.name:sum(len(poly.vertices)-2 for poly in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'}
    print('LOWPOLY_TRIANGLES',counts,'TOTAL',sum(counts.values()))
tempfile.tempdir=os.path.join(out,'.blender-temp')
os.makedirs(tempfile.tempdir,exist_ok=True)
result=bpy.ops.export_scene.gltf(filepath=os.path.join(out,asset_name+'.glb'), export_format='GLB', export_apply=True)
if 'FINISHED' not in result: raise RuntimeError('GLB texture export failed')

# Temporary studio setup for preview; the saved asset contains only the three meshes.
def aim(obj, target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-19,11.5))
cam=bpy.context.object; cam.name='Presentation Camera'; aim(cam,(0,0,5.2)); cam.data.type='ORTHO'; cam.data.ortho_scale=15.6
scene=bpy.context.scene; scene.camera=cam
for name,loc,power,size in [('Key',(1,-8,14),1900,8),('Fill',(-8,-3,9),1300,7),('Rim',(2,6,12),2200,6)]:
    bpy.ops.object.light_add(type='AREA', location=loc); o=bpy.context.object; o.name=name+' softbox'; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; aim(o,(0,0,4.5))
scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.world.color=(.075,.075,.075)
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'

scene.render.filepath=os.path.join(out,'preview.png')
bpy.ops.render.render(write_still=True)
cam.location=(0,-20,5.5); aim(cam,(0,0,5.5)); cam.data.ortho_scale=12.8
scene.render.filepath=os.path.join(out,'preview_front.png')
bpy.ops.render.render(write_still=True)
cam.location=(20,0,5.5); aim(cam,(0,0,5.5)); cam.data.ortho_scale=12.8
bpy.ops.object.light_add(type='AREA', location=(12,-6,12))
side_light=bpy.context.object; side_light.name='Side preview softbox'; side_light.data.energy=2200; side_light.data.shape='DISK'; side_light.data.size=9; aim(side_light,(0,0,5.5))
scene.render.filepath=os.path.join(out,'preview_side.png')
bpy.ops.render.render(write_still=True)
for obj in list(bpy.data.objects):
    if obj.type in {'CAMERA','LIGHT'}: bpy.data.objects.remove(obj,do_unlink=True)
scene.camera=None
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all()
# Open the asset with its image textures visible in Blender's viewport.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D': area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,asset_name+'.blend'))
try:
    os.rmdir(tempfile.tempdir)
except OSError:
    pass
