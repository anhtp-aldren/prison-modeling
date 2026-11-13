# Main gate

Blender model based on the four orthographic reference views in `../2d`.

- `main_gate.blend` — editable Blender scene with exactly three mesh objects: `Main Frame`, `Left Leaf`, and `Right Leaf`.
- `main_gate.glb` — portable glTF binary export.
- `preview.png` — rendered three-quarter view.
- `preview_front.png` and `preview_side.png` — orthographic checks against the reference views.
- `build_gate.py` — procedural source used to build the scene and exports.
- `textures/` — authored base color, packed metallic/roughness, normal, and source roughness maps. The frame maps are derived from the top and bottom trim in `../../wall-01/3d/fbx_mobile/textures/front_mobile.jpg`. The used maps are packed into the `.blend` and embedded in the `.glb`.
- `make_textures.py` — regenerates the texture maps with Pillow.

The materials use restrained charcoal and warm steel tones, sparse rust marks, fine scratches, and low strength normal maps to match the reference without broad mottled noise.
The structural `Main Frame` uses the wall trim texture; the door leaves and black upper panel keep their own finishes.

The `.blend` opens in **Material Preview** so the texture maps are visible. If a newly imported GLB appears flat in Blender, switch its viewport from **Solid** to **Material Preview** using the sphere icons at the top right of the 3D Viewport.

The model is approximately 9.7 m wide, 11.1 m tall including the upper lamps, and 1.7 m deep. Its front faces negative Y. One large X spans the paired leaves. The lower doorway is open behind the leaves, and each leaf has its origin at its outer hinge edge. Each leaf has a vertical grab handle at its inner edge on both faces. The lower pillars stop at the door top, with wider top and bottom caps; a reveal and horizontal rail connect them to the upper board. The model includes plank seams, hazard paint, rivets, hinges, and upper lamps. The center lock and side lamps have been removed.

Rebuild with Blender 5.x:

```powershell
python make_textures.py
blender --background --python build_gate.py
```
